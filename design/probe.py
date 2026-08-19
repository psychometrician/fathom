"""An executable version of design/probe-sketch.md, for testing the sketch.

THIS IS AN EXPERIMENT, NOT A PACKAGE. It exists to answer one question — does a
domain-blind probe cope with documents that have strong domain conventions? — and
it lives in design/ rather than in any package layout because Phase 2 has not been
earned. Read design/probe-sketch.md first; this is that page, mechanised.

    uv run design/probe.py <file.json>

It knows nothing about npm, Jupyter, npm lockfiles, GeoJSON or anything else, on
purpose. See README.md, "A diverse corpus and a domain-blind tool."
"""
import json
import re
import sys
from collections import Counter, defaultdict

KEYED_MIN = 20  # a fallback threshold, used only where the sibling test cannot run
KIND_MAX = 24   # most kinds a split may propose; see discriminator(). Gap: 20 vs 37
VOCAB_GROWTH = 0.02  # keys per copy below which classify() declines. Gap: 0.007 vs 0.030
SHOW = 40       # how many record shapes and keyed sites to print; see report()


# ── health ───────────────────────────────────────────────────────────────────

BOMS = [(b"\x00\x00\xfe\xff", "utf-32-be"), (b"\xff\xfe\x00\x00", "utf-32-le"),
        (b"\xef\xbb\xbf", "utf-8"), (b"\xfe\xff", "utf-16-be"), (b"\xff\xfe", "utf-16-le")]


MAX_RECORDS = 20_000  # the sampling contract's cap; see _read_ndjson


def health(path, max_records=MAX_RECORDS):
    raw = open(path, "rb").read()
    out = {"bytes": len(raw)}

    # Gzip is not a curiosity, it is how JSON at scale actually ships: GH Archive,
    # warehouse exports, log rotation, anything off S3. `04-gharchive` was
    # unreadable purely for want of these three lines.
    if raw[:2] == b"\x1f\x8b":
        import gzip
        out["compressed"] = "gzip"
        out["packed_bytes"] = len(raw)
        raw = gzip.decompress(raw)
        out["bytes"] = len(raw)

    # ENCODING. A UTF-16 document with a BOM is valid JSON in the wrong clothes,
    # and reporting it as "not a format I recognise" is the NDJSON mistake again.
    enc = next(((b, e) for b, e in BOMS if raw.startswith(b)), None)
    out["bom"] = enc[1] if enc else None
    try:
        txt = raw.decode(enc[1] if enc else "utf-8")
        txt = txt.lstrip("﻿")
        out["bad_bytes"] = 0
    except UnicodeDecodeError:
        # Strict first, so ill-formed bytes are reported instead of being
        # silently replaced by U+FFFD. A lone surrogate used to pass as clean.
        txt = raw.decode(enc[1] if enc else "utf-8", errors="replace").lstrip("﻿")
        out["bad_bytes"] = txt.count("�")

    dupes, negzero = [], []
    def hook(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen:
                dupes.append(k)
            seen.add(k)
        return dict(pairs)

    # parse_int and parse_float receive the ORIGINAL token text, which is the
    # only place the sign of zero still exists: json.loads("-0") returns int 0.
    def num(s, f):
        v = f(s)
        if v == 0 and s.lstrip().startswith("-"):
            negzero.append(s)
        return v
    kw = dict(object_pairs_hook=hook,
              parse_int=lambda s: num(s, int), parse_float=lambda s: num(s, float))

    try:
        doc = json.loads(txt, **kw)
        out["format"] = "JSON"
    except json.JSONDecodeError as e:
        # Split on \n and NOTHING ELSE. str.splitlines() also breaks on U+2028,
        # U+2029, \v, \f and NEL, and three GitHub payloads in `04-gharchive`
        # carry a literal U+2028 in user-written text — so three valid records
        # became six fragments and the probe reported six unreadable lines that
        # it had created. NDJSON is delimited by \n. A diagnostic that accurately
        # reports damage it caused itself is worse than one that says nothing.
        lines = [l.rstrip("\r") for l in txt.split("\n")]
        lines = [l for l in lines if l.strip()]
        # MOST of a sample, not all of it. Requiring every one of the first 50 to
        # parse meant a three-line file with one bad line was not NDJSON at all,
        # so the format was lost over a single broken record — which is the very
        # case the format most needs reporting for.
        sample = lines[:50]
        if len(lines) > 1 and sum(_parses(l) for l in sample) >= max(2, len(sample) * 0.6):
            # NDJSON, and it stays NDJSON even if a later line is broken. The
            # first version detected it, hit a bad line, and forgot — reporting
            # "unrecognised" for a file whose format it had already identified.
            doc, bad = [], []
            read = lines[:max_records]
            for i, l in enumerate(read, 1):
                try:
                    doc.append(json.loads(l, **kw))
                except json.JSONDecodeError as le:
                    bad.append((i, str(le)))
            out.update(format="NDJSON", records=len(doc), bad_lines=bad,
                       lines=len(lines), sampled=len(lines) > len(read))
            return _damage(out, doc, dupes, negzero)
        stripped = _strip_jsonc(txt)
        if stripped != txt:
            try:
                doc = json.loads(stripped, **kw)
                out["format"] = "JSONC"
                return _damage(out, doc, dupes, negzero)
            except json.JSONDecodeError:
                pass
        out.update(format=None, error=str(e), **_why_unreadable(txt))
        return out, None
    return _damage(out, doc, dupes, negzero)


def _why_unreadable(txt):
    """Empty, chopped off, or genuinely not JSON — three different answers.

    The first version tested only the last character, so a document truncated
    just after a `]` was reported as unrecognisable rather than chopped off.
    Depth at end-of-input is the honest test: something is still open.
    """
    if not txt.strip():
        return {"empty": True, "truncated": False}
    depth, instr, esc = 0, False, False
    for ch in txt:
        if esc:
            esc = False
        elif instr:
            if ch == "\\":
                esc = True
            elif ch == '"':
                instr = False
        elif ch == '"':
            instr = True
        elif ch in "[{":
            depth += 1
        elif ch in "]}":
            depth -= 1
    return {"empty": False, "truncated": depth > 0 or instr}


# Strings are matched first so a // inside one survives; anything else that
# looks like a comment is removed, then trailing commas.
_JSONC = re.compile(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*.*?\*/', re.S)


def _strip_jsonc(txt):
    out = _JSONC.sub(lambda m: m.group(0) if m.group(0)[:1] == '"' else "", txt)
    return re.sub(r",(\s*[}\]])", r"\1", out)


def _damage(out, doc, dupes, negzero=()):
    """The silent half: it parsed, and something was lost anyway."""
    out["dupes"] = len(dupes)
    out["negzero"] = len(negzero)
    # Counted on PARSED values. The first version regexed the raw text and fired
    # ten times on a notebook by matching the string "NaN" inside legitimate R
    # output. A health check that cries wolf is worse than none.
    out["nonfinite"] = sum(1 for v in _scalars(doc)
                           if isinstance(v, float) and (v != v or v in (float("inf"), float("-inf"))))
    out["bigints"] = sum(1 for v in _scalars(doc)
                         if isinstance(v, int) and not isinstance(v, bool)
                         and abs(v) > 2 ** 53)
    out["encoded"] = sum(1 for v in _scalars(doc)
                         if isinstance(v, str) and _encoded_doc(v))
    return out, doc


def _encoded_doc(s):
    """True if `s` holds an encoded JSON DOCUMENT, not merely parseable text.

    **Repaired 2026-08-09 after `11-jupyter-notebook`, which reported 17 and
    every one was a false positive.** Advent of Code day 18 is *Snailfish*, whose
    puzzle input IS nested integer lists, printed as cell output; `[376.0,
    490.543]` is a Python `repr`. All 17 parse as JSON and start with a bracket,
    so the old test was right by its own definition and wrong about the world —
    nothing upstream had encoded anything.

    **A document is an object, or an array containing one.** A bare array of
    scalars is data that happens to be bracketed. Both cases in `test/` decode
    to objects and are unaffected.

    The other half of that file's finding is NOT fixed here and is not a defect:
    its 17 base64 PNGs are invisible to this check, because base64 neither
    parses nor starts with a bracket. They are encoded *payloads*, not encoded
    JSON, and widening the check to catch them would be a different feature.
    """
    s = s.strip()
    if s[:1] not in "{[":
        return False
    try:
        v = json.loads(s)
    except (ValueError, RecursionError):
        return False
    return isinstance(v, dict) or (
        isinstance(v, list) and any(isinstance(x, dict) for x in v))


def _parses(s):
    try:
        json.loads(s)
        return True
    except Exception:
        return False


def _looks_truncated(txt):
    t = txt.rstrip()
    return bool(t) and t[-1] not in "}]"


def _scalars(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _scalars(v)
    elif isinstance(o, list):
        for v in o:
            yield from _scalars(v)
    else:
        yield o


# ── structure ────────────────────────────────────────────────────────────────

def fold_set(doc):
    """The set of container paths whose keys are data, and the walk that proves it.

    **It is a fixed point, not a single pass.** The first version decided by key
    count on each instance, so `peerDependenciesMeta` — one to five keys per copy
    but about thirty across copies — never folded and the output grew with the
    data. Data-ness is a property of the aggregate, and the aggregate only
    becomes visible once the container above it has folded. So: walk, fold
    whatever now looks like data, walk again, until nothing new folds.

    **Split out of `containers()` on 2026-08-18 for DEFECT 36, and the split is
    the repair.** `where` was deciding the same question with a weaker test —
    `classify([node])`, one container at a time — because the set this returns
    was locked inside `containers()`, which hands back the walk rather than the
    set. Two walks answering *are these keys data* two different ways is the
    defect; one of them asking the other is the fix.

    **`design/coverage.py` kept its own copy of this loop for the same reason**
    and the comment there says why: an instrument that recomputes the fold
    silently measures a probe that never ran. It calls this now, and so does
    `design/where.py`. **The set is the thing to share, not the loop.**
    """
    big = set()
    for _ in range(20):  # converges in a few; bounded so nothing pathological hangs
        got = _walk(doc, big)
        new = {p for p, objs in got[0].items() if p not in big and folds(p, objs)}
        if not new:
            return big, got
        big |= new
    return big, _walk(doc, big)


def containers(doc):
    """Every dict, grouped by the path of its container, with data keys folded.

    Keys judged to be data collapse to <key>, so 288 sibling objects are
    described once rather than 288 times. That fold is what makes the output
    proportional to the structure instead of to the data.

    The fixed point that decides it is `fold_set()` above; this returns only the
    walk, which is every caller here wants and was the reason the set had no way
    out of this function until defect 36 needed it.
    """
    return fold_set(doc)[1]


def folds(p, objs):
    """Should this site's keys collapse to `<key>`? One definition, two callers.

    Keys the probe calls **data** always fold; that is operation 2 and it is
    unchanged. A **saturated** site — one whose whole vocabulary would fit in a
    field list, so the probe declines to say — folds only when its members are
    RECORDS, and that condition was measured rather than chosen.

    **Folding a collection of records still describes them**, under `<key>`.
    **Folding a collection of scalars erases the only names those leaves will
    ever have**, because a scalar has no fields to describe underneath it.
    `13-package-lock`'s `engines` holds **1,058 strings** under five keys, and
    an earlier draft of this repair folded it and put **6.5% of that document
    beyond naming**; `20-homebrew-formulae`'s `variations` holds **5,295
    objects** and loses nothing. The predicate is the one the keyed-collection
    branch of `classify()` already uses, not a new one.

    **And a site that is ALREADY a collection's member does not fold again.** A
    `<key>` step means the fold has placed a name here, and what a name
    addresses is a record — so the keys below it are that record's fields. This
    is defect 22's own diagnosis applied one level up: *the platform is the
    data, the keys inside it are the fields.* Across the corpus every
    `<key>`-terminated object site holds a record, which is not a coincidence.
    Without this clause `$.paths.<key>` folds `get`, `post` and `delete` into
    `<key>` on `09-stripe-openapi`, taking that file's keys-as-data 47 → 46 and
    its polymorphic 49 → 47. **That trade is measured and it is not made here**
    — it takes Stripe's unnamed from 15.8% to 7.8%, which is a real gain and a
    separate argument. A defect repair changes what the defect names.
    """
    v = classify(objs)[0]
    if v == "data":
        return True
    if v != "saturated" or p.endswith("<key>"):
        return False
    vals = [x for o in objs if o for x in o.values()]
    return bool(vals) and all(isinstance(x, dict) for x in vals)


JSON_TYPE = {"NoneType": "null", "str": "text", "list": "array", "dict": "object",
             "int": "number", "float": "number", "bool": "boolean"}


def varies(counter):
    """The distinct shapes a field takes, ignoring differences that mean nothing.

    An empty array says nothing about its nesting depth, so `array` beside
    `array[1]` is one shape and not two. Without this every optional list in
    every document reads as polymorphic: the comment thread reported `children`
    as `array[1]` ×165 and `array` ×171, which is 165 parents and 171 leaves, not
    a field changing type.
    """
    ts = set(counter)
    if "array" in ts and any(t.startswith("array[") for t in ts):
        ts.discard("array")
    return ts


def shape(v):
    """The type of a value, and for arrays how deeply they nest.

    Added 2026-08-09 after the held-out run on `03-natural-earth`. GeoJSON's
    `coordinates` is `[[[x,y]]]` for a Polygon and `[[[[x,y]]]]` for a
    MultiPolygon — same name, same JSON type, different nesting — and 49% of that
    file's records differ there while the probe reported one shape and zero
    polymorphic fields. Type alone cannot see it.

    An EMPTY array reports plain `array`: its depth is unknown, and inventing one
    would manufacture a difference between `[]` and `[1,2]` that nobody means.
    Only the first element is followed, so an array ragged past position 0 is
    still missed — a known limit, not a solved problem.
    """
    if isinstance(v, list):
        n, x = 0, v
        while isinstance(x, list):
            if not x:
                return "array"
            n, x = n + 1, x[0]
        # The ELEMENT type, added 2026-08-09 after DuckDB found what this
        # function could not. `05-fhir-bundle` has `AllergyIntolerance.category`
        # = ["environment"] on 9 resources and `Observation.category` =
        # [{"coding": …}] on 257, and both returned `array[1]` — nesting depth
        # is not what an array holds. DuckDB, which must unify element types to
        # build a column, stored that field as raw JSON and so reported it; jq
        # and ijson miss it identically because neither compares an array with
        # an array.
        #
        # This was the FOURTH proxy-instead-of-property defect and the sharpest,
        # because `shape()` was itself written to fix the third: comparing types
        # alone could not see `03-natural-earth`'s polymorphism hiding in array
        # depth. Depth alone cannot see this. Both halves are now reported, and
        # natural-earth still reads `array[3] number` against `array[4] number`.
        return f"array[{n}] {JSON_TYPE.get(type(x).__name__, type(x).__name__)}"
    return JSON_TYPE.get(type(v).__name__, type(v).__name__)


def fold_recursion(inst, arrs, types):
    """Fold self-similar nesting into one entry.

    A comment thread has ONE record shape that contains itself. Describing it
    once per level is O(depth) for a structure whose entire point is that it
    repeats — the first version printed the same thirteen fields twelve times
    with a path ending in `children[].children[].children[]`, and priced the
    thread at 25 rows when it holds 336 comments, because it saw only the top
    level. That is the O(data) failure arriving through a third door.

    A path is a recursive repeat of an ancestor when it extends that ancestor by
    at least one FIELD step and carries the same key set. The field step matters:
    `funding` and `funding[]` share a key set and one string-prefixes the other,
    but that is a field which is sometimes an object and sometimes an array of
    that object — polymorphism, not self-containment. Without the `.` test,
    package-lock was reported as recursive depth 2, and it is not recursive at all.

    **Key-set equality is not identity, and the held-out run on `05-fhir-bundle`
    proved it twice.** FHIR builds everything out of a handful of reusable element
    types: `Money` is `{value, currency}` and `Reference` is `{reference,
    display}`, and both appear all over the tree at unrelated places. So
    `Claim.total` is `{value, currency}` and `total[].amount` is `{value,
    currency}`, the two got merged, and a document containing **no recursion at
    all** was reported as `RECURSIVE, 2 levels` at 54 + 54 = 108 copies. The same
    happened to `location` at 108 + 48 = 156.

    **The missing condition is reachability: you have to be able to GET there by
    following a field the ancestor actually has.** A comment thread recurses
    because a comment has a `children` field and the deeper comments are under it.
    A `total` does not contain a `total` — the step into `amount` leaves the shape
    behind and lands on something that merely looks the same. So the first field
    step of the descent must be a key of the ancestor.

    That is the third time an instrument here measured a cheap proxy instead of
    the property: depth by splitting a dotted string said 9 for a document of
    depth 6, polymorphism by comparing types at a path missed `03-natural-earth`,
    and recursion by key-set equality fires on documents that have none.
    """
    keyset = {p: frozenset(k for o in objs for k in o)
              for p, objs in inst.items() if any(objs)}

    def first_step(suffix):
        """The first FIELD name of a descent, ignoring any `[]` hops.

        Written out rather than compressed into one expression, because the
        compressed version silently returned the empty string for a suffix like
        `[].x[]` and that reads as "no such key" — a wrong answer arriving as a
        plausible one, which is the failure mode this whole function is being
        repaired for.
        """
        while suffix.startswith("[]"):
            suffix = suffix[2:]
        if suffix.startswith("."):
            suffix = suffix[1:]
        return suffix.split(".")[0].removesuffix("[]")

    def descends(p, a):
        if p == a or not p.startswith(a):
            return False
        suffix = p[len(a):]
        if "." not in suffix:
            return False
        # Reachability: you have to get there by following a field the ancestor
        # carries. `.children[]` off a comment qualifies; `[].amount` off a
        # `{value, currency}` does not, because a total has no `amount`.
        return first_step(suffix) in keyset.get(a, ())

    canon = {}
    for p in sorted(keyset, key=len):
        canon[p] = next((a for a in sorted(set(canon.values()), key=len)
                         if descends(p, a) and keyset.get(a) == keyset[p]),
                        p)

    merged, levels = defaultdict(list), Counter()
    for p, objs in inst.items():
        c = canon.get(p, p)
        merged[c].extend(objs)
        if c != p:
            levels[c] += 1

    marrs = defaultdict(list)
    for p, lists in arrs.items():
        # Only rewrite when the canonical really is an array path. A thread whose
        # root shares its comments' shape canonicalises to "$", and "$"[:-2] is
        # the empty string, which produced a row candidate called "an item of ".
        c = canon.get(p + "[]")
        marrs[c[:-2] if c and c.endswith("[]") else p].extend(lists)

    # Types have to fold too, or polymorphism inside a recursive structure is
    # invisible: `points` is a number on the story and null on all 335 comments,
    # but no single unfolded path ever sees both. Fourth time this has bitten —
    # anything not computed on the fold reports the wrong thing.
    mtypes = defaultdict(Counter)
    for tp, c in types.items():
        holder, _, field = tp.rpartition(".")
        mtypes[f"{canon.get(holder, holder)}.{field}"].update(c)
    return merged, marrs, levels, mtypes


def filled(o):
    """The keys of `o` that actually carry a value.

    A key present with a `null` is a hole, and this function exists because the
    probe used to disagree with itself about that. `price()` measures holes with
    `pandas.isna()`, so a null counts; `emptiness()` measured key presence, so it
    did not. On `07-graphql-introspection` the two reported **52% and 0% about
    the same table**, and the one that decides whether to split was the blind one.

    That is the fifth proxy-instead-of-property defect: raggedness measured by
    whether a key is there rather than by whether there is a value. GraphQL says
    "this is a SCALAR, not an OBJECT" by nulling the irrelevant keys, never by
    omitting them, so a document whose 108 records are six genuinely different
    kinds looked perfectly uniform.
    """
    return frozenset(k for k, v in o.items() if v is not None)


def variation(objs):
    """How much a set of records disagrees about the SHAPE of their values.

    The fraction of fields whose value shape is not the same in every record.
    `emptiness()` asks which keys are filled; this asks what the filled ones
    hold, and `10-wikidata` is the document that made the difference matter:
    every `datavalue` is `{type, value}` with both keys filled, so it is 0%
    empty and has one key-set, and `value` is `text` on 512 records and `object`
    on 1,210. **A perfect split existed and the operation was measuring the one
    thing this document does not suffer from.**

    **Goes through `varies()`, repaired 2026-08-09 after `11-jupyter-notebook`.**
    It did not, and so counted an EMPTY array as a different type from a full
    one. `cell_type` is the cleanest two-way discriminator in the corpus —
    markdown goes to 0% — and the split was refused because the code group
    "varied" at 40% on `outputs ['array', 'array[1] object']` and `source
    ['array', 'array[1] text']`. That group's real emptiness is 0.0015.

    **`varies()` already existed and already said so** — *"`array` beside
    `array[1]` is one shape and not two"* — and it was applied in the report and
    in `axes.py` but not in the guard. The accumulator below was named `varies`,
    which shadowed the function, and that is most likely how the gap survived
    review: the fix could not be called from the place that needed it because
    the name was already taken. It is now `n`.

    Two correct repairs composed into this: `a316ac68…` gave `shape()` the array
    element type (DuckDB found that bug) and `c7b4aef4…` made `variation()`
    load-bearing for the first time. Neither had been run against the other.
    """
    fields = set().union(*[filled(o) for o in objs])
    if not fields:
        return 0.0
    n = sum(1 for f in fields
            if len(varies(Counter(shape(o[f]) for o in objs
                                  if o.get(f) is not None))) > 1)
    return n / len(fields)


def disorder(objs):
    """What a split is trying to reduce: holes plus disagreement about shape."""
    return max(emptiness(objs), variation(objs))


def weighted(groups, measure):
    """`measure` across groups, weighted by rows. Reporting only — NOT a guard.

    Tried as the pricing rule on 2026-08-09 and rejected by measurement: it took
    `09-stripe-openapi` from 5 splits to 22 and revived two false positives the
    worst-group rule had correctly killed. It stays here because it is the honest
    number to PRINT — a reader meets the big table — while the decision to split
    is still made on the worst group.
    """
    n = sum(len(g) for g in groups)
    return sum(len(g) * measure(g) for g in groups) / n if n else 0.0


def emptiness(objs):
    """What fraction of a folded table's cells would be empty.

    Counts a null as a hole, which is what `price()` has always done and what
    this function did not until 2026-08-09.
    """
    # The columns are the ones this group actually FILLS, not the ones it merely
    # carries. A GraphQL SCALAR type has all eight introspection keys present and
    # five of them null in every single record; nobody building a table of scalars
    # keeps five all-null columns. Measuring against key presence scored that
    # group 70% empty and killed the split that would have produced it.
    cols = set().union(*[filled(o) for o in objs])
    if not cols:
        return 0.0
    return 1 - sum(len(filled(o) & cols) for o in objs) / (len(objs) * len(cols))


def discriminator(objs):
    """A field whose value says which KIND of record this is. `(field, groups)`.

    Added 2026-08-09, forced by the held-out run on `05-fhir-bundle`. One `entry`
    array there holds 564 resources of 20 different resourceTypes, and folding
    them into one shape gives **97 fields, 87% empty, and exactly two fields
    present in all of them**. Folding within each resourceType instead gives 20
    tables, worst 22% empty and eleven of them completely full.

    **The fold was never wrong. Its scope was.** "Sibling instances" was doing
    unexamined work — siblings by position in the document are not siblings by
    kind — and the document said so in the fold's own output, because 42 distinct
    key-sets over 564 instances is the tool reporting that it merged things which
    are not the same. Nothing read that number.

    A discriminator has to earn all four of these, and each one is a false
    positive that appeared while fitting this:

      present in every instance    `status` covers 534 of 564 FHIR resources and
                                   is a state, not a kind. A field that is
                                   sometimes absent cannot partition everything.
      a scalar value               partitioning on an object means nothing.
      few distinct values          `id` is present in all 564 and has 564 values.
                                   An identifier is not a kind. The ceiling is
                                   a fifth of the instances.
      the split has to PAY         it must at least halve the average number of
                                   key-sets per group, or this is just slicing a
                                   regular table and calling it an insight.
      and it has to pay in HOLES   the worst group must be at most half as empty
                                   as the fold was. This is the operation's own
                                   definition rather than a tuned threshold: the
                                   entire reason to split is that the folded
                                   table is mostly holes, so a split that leaves
                                   the holes has not done the thing.

    **That last rule was added because the first version fired twice on file 05
    where it should not have.** `identifier[].system` scored 44% empty down to 31%
    and `item[].sequence` scored 49% down to 46% — the second being an *ordinal
    position*, 1, 2, 3, …, which is the opposite of a kind. Counting key-sets said
    both had improved. Counting holes says neither had.

    **`sequence` is worth watching rather than special-casing.** An integer field
    whose values are a contiguous run is a position and can never be a kind, and a
    rule could say so. It is not written because the holes test already excludes
    it here, and a rule fitted to one file that earns nothing is how a probe stops
    being an instrument. If an ordinal ever passes the holes test, write it then.

    **The limit, stated because it is load-bearing**: the discriminator must live
    INSIDE the record. `04-gharchive`'s payloads differ by event type, but `type`
    sits on the parent event and not on the payload, so nothing here finds it.
    That is the obvious next case and it is not solved.
    """
    objs = [o for o in objs if o]
    if len(objs) < 10:
        return None
    # Distinct FILLED key-sets, not distinct key-sets. See filled().
    # THERE HAS TO BE SOMETHING WORTH FIXING. Pricing by type variation
    # reopened the near-identifier hole the docstring below already warned
    # about: `04-gharchive` split on `client_id`, six opaque values over 61
    # records, because any high-cardinality field trivially makes small
    # homogeneous groups.
    #
    # Records-per-kind does NOT separate that from a real split — the genuine
    # `type` splits on `09-stripe-openapi` run 5 to 10 records per kind and
    # `client_id` is 10. What separates them is how much disorder was there to
    # begin with: `client_id` 8%, against 87% (fhir), 62-68% (stripe), 50%
    # (wikidata, natural-earth), 45% (graphql), 23% (hn thread).
    #
    # **0.2 is fitted, and the gap it sits in is 8% against 23% — the whole
    # evidence for it.** A table that is 8% disordered does not need splitting
    # into six, and saying so costs three real but marginal Stripe splits.
    if disorder(objs) < 0.2:
        return None

    shapes = len({filled(o) for o in objs})
    # More than one key-set, OR any disagreement about value shape. The second
    # half is what `10-wikidata` needed: one key-set, 0% empty, and `value` text
    # on 512 records and object on 1,210.
    #
    # **Was `shapes < 3` until 2026-08-09.** Repairing `variation()` to go
    # through `varies()` cost `02-hn-thread` its split — story 1, comment 335,
    # both 0% disordered, clearing the halving rule 0.0 against 0.115 — because
    # hn has two filled key-sets and had been clearing this gate only on the
    # artifact `varies()` exists to discount: `children` as `array` x171 against
    # `array[1] object` x165, which is 171 leaves and 165 parents.
    #
    # A correct split was being found for a wrong reason. The threshold of three
    # was justified nowhere in writing, and this is a CHEAP PRE-FILTER, not a
    # pricing rule: the 0.2 disorder floor above and the halving rule below are
    # what decide whether a split pays. A document with exactly two kinds is the
    # most ordinary polymorphic document there is, and three was excluding it.
    #
    # One key-set with no shape disagreement still returns None, because then
    # the records genuinely are uniform and there is nothing to partition.
    if shapes < 2 and variation(objs) == 0:
        return None
    everywhere = set.intersection(*[set(o) for o in objs])
    best = None
    for f in sorted(everywhere):
        vals = [o[f] for o in objs]
        if not all(isinstance(v, (str, int, bool)) and not isinstance(v, float)
                   for v in vals):
            continue
        distinct = len(set(vals))
        # TWO CEILINGS, and the second was added 2026-08-09 after
        # `13-package-lock` split `funding` into 37 groups on `url`, a sponsor
        # link. `url` was the ONLY candidate — it is the one field present in
        # every instance, because `type` is on 52 of 282 — and it cleared every
        # guard there was.
        #
        # **The obvious fix was tried first and MEASURED WRONG.** Cardinality
        # relative to record count looks like the separator on five points and
        # is not: across all 27 splits the corpus makes, `url` is 13.1% and sits
        # INSIDE the good range — `07-graphql-introspection`'s `kind` is 13.8%
        # and `09-stripe-openapi`'s `type` is 18.8%. No ratio threshold divides
        # them. Records-per-kind was already rejected the same way on
        # `04-gharchive`.
        #
        # The one axis where it is an outlier is the absolute count. Every
        # genuine split in the corpus proposes 2 to 20 kinds; this proposes 37.
        # **The gap is 20 against 37 and that gap is the whole evidence**, the
        # same shape of argument as the 0.2 disorder floor's 8%-against-23%.
        #
        # And the justification is the probe's purpose rather than the data's
        # structure: **one command that leaves you oriented.** A partition into
        # 37 tables is not a description, it is a shredding, and the report
        # already shows six groups and counts the rest. 24 leaves headroom above
        # `05-fhir-bundle`'s 20, which is the largest genuine split seen.
        if not 2 <= distinct <= min(KIND_MAX, max(2, len(objs) // 5)):
            continue
        groups = defaultdict(list)
        for o, v in zip(objs, vals):
            groups[v].append(o)
        mean_shapes = sum(len({filled(o) for o in g})
                          for g in groups.values()) / len(groups)
        if mean_shapes > shapes / 2 and variation(objs) == 0:
            continue
        # WORST GROUP, not a row-weighted mean. Weighting was tried on
        # 2026-08-09 and rejected by measurement: it took `09-stripe-openapi`
        # from 5 splits to 22, resurrected `05-fhir-bundle`'s `identifier[].system`
        # false positive, and split `07-graphql-introspection` on `name`, which is
        # an identifier. A big clean group must not buy a small filthy one.
        worst = max(disorder(g) for g in groups.values())
        if worst > disorder(objs) / 2:
            continue
        # Prefer the field that leaves the least raggedness behind, not the one
        # that makes the most groups — otherwise a near-identifier always wins by
        # cutting every group down to one instance.
        score = (mean_shapes, worst, distinct)
        if best is None or score < best[0]:
            best = (score, f, dict(groups))
    return None if best is None else (best[1], best[2])


def packed(objs):
    """Fields at one record shape that are LISTS PACKED INTO TEXT — defect 26.

    `25-usgs-quakes` writes three of them:

        types    ,nearby-cities,origin,phase-data,
        ids      ,nc75415572,
        sources  ,nc,

    and `an item of features 10,885 rows x 30 cols` hands a reader a `types`
    column that is really a list. **That is the list-column problem in a
    disguise that passes as text**, and the probe calls it text because it IS
    text.

    **The rule is the one defect 26's own entry proposed and never measured:
    a field wrapped in the same non-alphanumeric character at both ends, AND at
    least one SIBLING field wrapped in that same character.** One field alone is
    never enough — `,nc,` and `04-gharchive`'s `:hash:` are structurally
    identical, and no single value can separate them. What resolves it is the
    document: siblings sharing a wrapping character is a convention, one field
    doing it is a coincidence.

    **Measured over all 29 documents before this shipped: 3 matched, 3 true, 0
    false.** The two rules measured on 2026-08-10 both fail — the strict one
    catches `types` and misses `ids` and `sources`; the relaxed one takes all
    three and **386 false**, every CSS vendor prefix on
    `29-mdn-browser-compat`. `FINDINGS.md` 2026-08-15.

    It reports and changes no number, per *report, never repair* — like
    defect 18's sentinel, and for the same reason: a packed list is the
    document's problem, not the probe's.
    """
    wrap = {}
    for field in {k for o in objs if isinstance(o, dict) for k in o}:
        vals = [o[field] for o in objs
                if isinstance(o, dict) and o.get(field) is not None]
        if not vals or not all(isinstance(v, str) and len(v) >= 3 for v in vals):
            continue
        chars = {v[0] for v in vals if v[0] == v[-1] and not v[0].isalnum()
                 and not v[0].isspace()}
        if len(chars) == 1 and all(v[0] == v[-1] for v in vals):
            wrap[field] = next(iter(chars))
    shared = Counter(wrap.values())
    hits = sorted(f for f, c in wrap.items() if shared[c] > 1)
    return hits, (wrap[hits[0]] if hits else None)


def positional(arrs):
    """Arrays of scalars whose length never varies, grouped by that length.

    Added 2026-08-09, forced by the cold run on `06-espn-qbr`. That document
    stores a table column-wise: `$.categories[0]` holds `labels`, `names`,
    `displayNames` and `descriptions`, four arrays of length 10, and each aligns
    by position with the ten values in every `athletes[].categories[].totals`.
    **`labels` is the column names for the entire document and the probe never
    mentioned it once in 44 lines**, because its holder is a single-copy object
    and the folding loop skips anything with fewer than two instances.

    **This is a targeted fix and not a general one, which matters.** The defect is
    that the fold cannot see single-copy objects, and printing all of them would
    have added seventeen lines of noise to `01-npm-registry` alone. What is
    repaired here is the specific harm: a structure whose parts are related by
    POSITION rather than by nesting, which no amount of folding will ever reveal
    because folding describes shapes and this is an alignment between them.

    A path qualifies only if every instance of it is the same length, because
    that constancy is the entire signal. Ordinary scalar arrays — npm's
    `keywords`, HN's `kids` — vary per record and drop out.
    """
    fixed = {}
    for p, lists in arrs.items():
        lens = {len(l) for l in lists if l is not None}
        if len(lens) != 1:
            continue
        n = lens.pop()
        if n < 3:
            continue
        if any(isinstance(v, (dict, list)) for l in lists for v in l):
            continue
        fixed[p] = (n, lists)

    # THE PARENT IS THE TABLE, and requiring that is what `09-stripe-openapi`
    # forced. The first version asked only for two paths sharing a length of at
    # least three, and on a 7.6 MB document with thousands of small arrays it
    # reported "22 paths hold arrays of exactly 3" — unrelated JSON Schema
    # `required` and `enum` lists, scattered across 22 different parents, with
    # several `enum`s then marked as the names.
    #
    # **Length 3 across 22 parents is a coincidence. Length 336 across 5 paths in
    # ONE parent is a table.** A document that stores a table in columns keeps
    # the columns together, so a parent qualifies only when it holds at least two
    # constant-length scalar arrays and **all of its constant-length scalar
    # arrays agree on that length** — the parent is wholly a table, or it is not
    # one. `08-open-meteo`'s `$.hourly` holds five of 336 and nothing else;
    # `06-espn-qbr`'s two parents hold four of 10 and two of 10.
    by_parent = defaultdict(list)
    for p, (n, lists) in fixed.items():
        by_parent[p.rpartition(".")[0]].append((p, n, lists))

    groups = defaultdict(list)
    for parent, entries in by_parent.items():
        if len(entries) < 2:
            continue
        lens = {n for _, n, _ in entries}
        if len(lens) != 1:
            continue
        n = lens.pop()
        for p, _, lists in entries:
            groups[n].append((p, lists))
    return {n: sorted(ps) for n, ps in groups.items() if len(ps) > 1}


def looks_like_names(lists):
    """One instance, all strings, all distinct, all short. A header row.

    **This test is necessary and nowhere near sufficient, and `08-open-meteo`
    proved it in the worst possible way.** A column of 336 ISO timestamps is one
    instance of distinct strings under forty characters, so the probe marked
    `$.hourly.time` as the header and printed *"to name the others, zip them in
    order against time"* — advice that yields a table rather than an error. The
    caller must apply `names_are_keys()` first; this is only the value test.
    """
    return (len(lists) == 1 and lists[0]
            and all(isinstance(v, str) and 0 < len(v) <= 40 for v in lists[0])
            and len(set(lists[0])) == len(lists[0]))


def names_are_keys(paths):
    """Do all the aligned arrays sit under ONE parent? Then the names are keys.

    Added 2026-08-09 after `08-open-meteo`, and it separates the two documents
    that share a shape and not a risk.

      `08-open-meteo`   $.hourly.time, .temperature_2m, .wind_speed_10m, …
                        FIVE arrays, ONE parent. They are the columns of one
                        table and their names are the KEYS. There is no header
                        row, nothing to choose, and nothing to mis-join.

      `06-espn-qbr`     $.categories[].labels, .names, .displayNames  and
                        $.athletes[].categories[].totals, .ranks
                        TWO parents. The names live in a metadata subtree and
                        the values in a record subtree, related only by
                        position — and `glossary` holds the same ten names in a
                        different order, so the obvious join reports TQBR = -7.4
                        for the league's best quarterback.

    **One parent means safe; more than one means a choice, and a choice is where
    the decoy lives.** The old code printed the same warning for both, which made
    it the finding on one file and noise on the other.
    """
    return len({p.rpartition(".")[0] for p in paths}) == 1


def _walk(doc, big):
    """Also records the types each field takes, so question 5 can be answered.

    Collected on the FOLDED path, so a field inside 288 sibling objects is one
    entry rather than 288 — the same reason everything else here folds.
    """
    inst, arrs = defaultdict(list), defaultdict(list)
    types = defaultdict(Counter)
    def go(o, p):
        if isinstance(o, dict):
            inst[p].append(o)
            for k, v in o.items():
                kp = f"{p}.<key>" if p in big else f"{p}.{k}"
                types[kp][shape(v)] += 1
                go(v, kp)
        elif isinstance(o, list):
            arrs[p].append(o)
            for v in o:
                go(v, p + "[]")
    go(doc, "$")
    return inst, arrs, types


def classify(objs):
    """Are this container's keys data, or field names? Returns (verdict, why).

    Two signals, and NEITHER works alone — measured across npm, a package-lock
    and a notebook, 2026-08-08:

      sibling overlap   how much sibling copies share their key sets. Low means
                        data. Alone it calls `outputs[]` (0.38) and
                        `packages.<key>` (0.32) data, and they are ragged records.
      type homogeneity  do the VALUES under one object share a type. Alone it
                        calls `author{name, email}` data, and it is a record.

    Conjoined they got 11 of 12 hand-labelled cases right. The one miss names the
    real boundary: `data{text/html, text/plain}` is data-as-keys with a closed,
    stable vocabulary, so it is structurally a record and no structural signal can
    see it. Same as `dist-tags{latest, next}`. Those are reported undecided.
    """
    objs = [o for o in objs if o]
    if not objs:
        return "empty", ""
    n = sum(len(o) for o in objs) / len(objs)
    hom = sum(Counter(type(v).__name__ for v in o.values()).most_common(1)[0][1] / len(o)
              for o in objs) / len(objs)

    # A COLLECTION KEYED BY NAME. Added 2026-08-09, forced by the held-out run
    # on `12-agent-trace`, where `snapshot.trackedFileBackups` is keyed by FILE
    # PATH and was called structural.
    #
    # **The sibling test assumes a data vocabulary CHANGES between copies, and a
    # stable one breaks it.** Nineteen snapshots of the same tracked files share
    # their paths, so overlap measured **0.66** where data is supposed to be
    # below 0.5, and the keys were reported as field names. Sibling overlap
    # cannot see a keyed collection whose membership is fixed.
    #
    # What it missed is not subtle: **563 values, every one an object, and
    # exactly ONE key-set among them.** That is a table addressed by name.
    # Nobody writes a record type with twenty-plus fields whose values are all
    # objects of identical shape — the shared shape is what makes them rows.
    #
    # It costs the probe nothing on the other eleven files, measured: every
    # keys-as-data grade in the corpus is unchanged. It is deliberately strict —
    # ONE key-set, not "few" — because a looser version is fitted rather than
    # structural, and the corpus has no case yet that asks for looser.
    vals = [v for o in objs for v in o.values()]
    if n >= KEYED_MIN and vals and all(isinstance(v, dict) for v in vals):
        if len({frozenset(v) for v in vals}) == 1:
            return "data", (f"{len(vals):,} values, all one shape, "
                            f"{int(n)} keys per copy — a collection, not a record")

    if len(objs) > 1:
        allk = Counter()
        for o in objs:
            allk.update(o.keys())
        ov = sum(allk.values()) / (len(allk) * len(objs))
        if ov < 0.5 and hom >= 0.9:
            # DECLINE TO CLAIM when the vocabulary is saturated. Added
            # 2026-08-09 after `13-package-lock` reported `engines` as data —
            # its entire key vocabulary over 1,050 objects is `node` 1048,
            # `npm` 6, `bare` 2, `iojs` 1, `yarn` 1.
            #
            # **This does NOT detect closed vocabularies, and the docstring
            # above is right that no structural signal can.** Three candidates
            # were measured across all 59 data-classified sites in the corpus
            # and all three failed to separate:
            #
            #   vocabulary size     `engines` is 5; Stripe has legitimate data
            #                       sites at 3, 4 and 5.
            #   modal key frequency `engines` is 99.8%; `devDependencies`,
            #                       `scripts` and `permissions` are all 100%.
            #   records per kind    already rejected the same way on gharchive.
            #
            # What this does instead is **stop over-claiming**. The single-copy
            # branch below already answers "undecided" for exactly this shape,
            # and that asymmetry was the finding: with one copy the probe admits
            # it cannot tell, with a thousand it stated the wrong answer.
            #
            # The measure is whether the vocabulary GROWS as copies accumulate.
            # An open vocabulary has a long tail — npm's `scripts` carries
            # `lint:fix` twice — and a closed one saturates. Sorted across the
            # corpus, the two lowest sites are `engines` at 0.005 and Stripe's
            # `paths.<key>` at 0.007, whose vocabulary is `post, get, delete`.
            # **Both are HTTP-method-shaped closed vocabularies and both were
            # being called data.** The next site up is `scripts` at 0.030, which
            # is genuinely data. **The gap is 0.007 against 0.030 and that gap
            # is the whole evidence for 0.02**, the same shape of argument as
            # the 0.2 disorder floor and the 24-kind cap.
            #
            # **THE VERDICT IS A REPORTING DECISION AND WAS ALSO A STRUCTURAL
            # ONE, which is defect 22.** `containers()` folds whatever this
            # function calls "data", so returning "undecided" here did not only
            # stop the probe naming these keys — it stopped their siblings
            # folding. On `20-homebrew-formulae` that turned `$[].variations`
            # into THIRTEEN unfolded platform sites, each with too few copies
            # for this very guard to fire on, and each then reported as data.
            # The guard manufactured the false positives it exists to prevent.
            #
            # So the branch has its own verdict. It still means *I decline to
            # call these keys data*; it no longer means *do not fold*. Measured
            # on 20 documents: eighteen are byte-identical and `SPLIT ON` counts
            # are unchanged on all twenty.
            if len(allk) / len(objs) < VOCAB_GROWTH:
                return "saturated", (f"{len(allk)} keys over {len(objs)} copies "
                                     f"— too few to tell data from a field list")
            return "data", f"{len(objs)} copies share few keys ({ov:.2f}), values one type"
        if ov < 0.5:
            return "structural", f"{len(objs)} ragged copies ({ov:.2f}), values differ ({hom:.2f})"
        return "structural", f"{len(objs)} copies share their keys ({ov:.2f})"
    # DEFECT 31, repaired 2026-08-12, and it is a CONSISTENCY fix rather than a
    # new rule. The docstring above says the two signals are sibling overlap and
    # type homogeneity, and that **neither works alone**. The multi-copy branch
    # demands both — `ov < 0.5 and hom >= 0.9`. This branch has no siblings to
    # measure overlap against, and it was demanding neither: enough keys was the
    # whole test.
    #
    # `27-grafana-dashboard` ran cold and its ROOT is a fixed schema —
    # `annotations`, `editable`, `panels`, `templating`, `title`, `uid`,
    # `version` — 25 field names called data on the strength of there being 25
    # of them.
    #
    # **`hom` is already computed at the top of this function, for every object,
    # single copies included.** The repair is to apply the test the other branch
    # applies, at the same threshold, to a number already in hand.
    #
    # Measured over the eleven corpus sites that reach this branch: **ten score
    # exactly 1.0000** — npm's `versions`, `users` and `time`, stripe's
    # `schemas` and `paths`, wikidata's `aliases` and `claims`, package-lock's
    # `packages` and `devDependencies`, movie-ratings — **and the eleventh
    # scores 0.2400.** That gap is not a threshold anybody chose; 0.9 was
    # already here.
    #
    # **The cost of the miss was not cosmetic.** `containers()` folds whatever
    # this function calls data, so the misclassification pooled five unrelated
    # root arrays — `__inputs`, `__requires`, `links`, `panels`, `tags` — into
    # one path, and `candidates()` prices only pools that are wholly objects. A
    # single string in `tags` then made the document's 31 panels unpriceable.
    # DEFECT 32, repaired 2026-08-12, replacing defect 31's `hom >= 0.9` — which
    # was mine, was too strict, and `28-home-assistant-i18n` was held out to find
    # out. It refused five message groups a reader would call keyed collections:
    # `$.ui.panel.profile` at 0.64, `lovelace.cards.energy` at 0.71,
    # `config.<key>.account` at 0.74, `config.<key>.http` at 0.77,
    # `page-onboarding.restore` at 0.87.
    #
    # **`hom` IS THE WRONG MEASURE HERE AND THE CORPUS NOW PROVES IT.** Across
    # 47 single-copy sites in 28 entries, the ones that must be ACCEPTED run
    # 0.6364 to 1.0000 continuously and the one that must be REFUSED sits at
    # 0.2400. There is no natural cut in that — any threshold would be a
    # constant fitted to the single gap one document happens to leave.
    #
    # **And it is the wrong measure for a reason, not by accident.** `hom`
    # averages a modal fraction over objects: with a thousand copies that is a
    # statistic, with ONE copy it only says what fraction of this one object's
    # values happen to share a type. A 33-key catalogue with twelve sub-groups
    # scores 0.64 and a 33-key catalogue with two scores 0.94, and they are the
    # same kind of thing.
    #
    # **The COUNT of distinct value types does not have that sensitivity, and it
    # separates categorically.** Over the same 47 sites: forty-six have ONE or
    # TWO, and `27-grafana-dashboard`'s root — a real schema of 25 fields — has
    # SIX. The gap is four whole categories rather than a decimal.
    #
    # The rule it expresses is statable, which is what makes it a rule: **a
    # keyed collection's values are one kind of thing, or a leaf and a group.**
    # A message is a string or a nested catalogue; a version is an object. A
    # RECORD is what has numbers and booleans and arrays and strings at once.
    #
    # **Nulls are excluded because a null is not a type** — the same reason
    # `variation()` gives. No corpus site currently has one here, so it costs
    # nothing measured and protects the case where a catalogue has a hole.
    #
    # > **This leaves the two branches measuring different things, and defect 31
    # > was about them measuring the same thing.** The asymmetry is deliberate
    # > now rather than accidental: with siblings there is an overlap to measure
    # > and a ratio over many objects means something; with one object there is
    # > neither.
    if n > KEYED_MIN:
        kinds = {type(v).__name__ for v in objs[0].values() if v is not None}
        if len(kinds) <= 2:
            return "data", f"one copy, {int(n)} keys — not a field list"
        return "structural", (f"one copy, {int(n)} keys, {len(kinds)} value "
                              f"types — a field list")
    return "undecided", f"one copy, {int(n)} keys — nothing separates it from a record"


# ── what one row could be, and what each would cost ──────────────────────────

def _above_marker(p):
    """A path ending in the fold's marker, named in the language a reader types.

    DEFECT 28, repaired 2026-08-12. `_walk` replaces a container's key with
    `<key>` when its keys are data, so a path can END in the marker and the
    label came out as `an item of <key>` — correct inside the fold, and a name
    nobody can type. The menu's contract is that anything `fathom()` names,
    `rows()` can take.

    **`<key>` is the fold's spelling of `*` and nothing else.** `design/rows.py`
    defines `*` as *every child — object values and array elements alike* and
    requires that *the key at every `*` is data and must survive into the
    table*, which is the definition of the site the marker marks. So the
    translation invents no notation: it writes an internal marker in the
    external language, and `$.entities.Q30.aliases.<key>` becomes `aliases.*`.

    **THE BARE NAME ONE LEVEL UP WAS TRIED FIRST AND IT DELETES THE LINE.**
    `aliases` is itself a keys-as-data site, so `an entry of aliases` is already
    in the menu and already in `seen`; naming this one `aliases` too collided
    and dropped it. **That trades an untypeable candidate for a missing one**,
    which is worse — and the two units are genuinely different: an ENTRY of
    aliases is one row per language, an ITEM of `aliases.*` is one row per
    alias. The `.*` is not decoration. It is the step through the keys, and a
    reader who cannot see it cannot write the extraction.

    **The larger half of this defect is a COLLISION, not a spelling.** `<key>`
    is the same string at every keyed site, so `seen` treated four unrelated
    sites on `10-wikidata` as one name and printed only the first — `aliases`,
    707 items — while `claims` at 1,724, its `qualifiers` at 1,271 and their
    `snaks` at 1,413 were dropped without a word. **A placeholder that is not
    typeable is also not distinct**, and the second failure is the one a reader
    had no way to notice.

    One `.*` per marker, because a path can end in a run of them and each is a
    step.

    **DEFECT 30, repaired 2026-08-12, and it was this function's own bug.** The
    first version returned `$` when the marker run reaches the root — a document
    whose ROOT keys are data — and both callers skip on `$`. The docstring said
    *"no corpus file is one, so this line is untested"*, and `27-grafana-dashboard`
    ran cold the same day and was one: its 25 top-level keys are data, so the
    line that printed before defect 28's repair stopped printing after it.
    **That is exactly the trade this function was written to avoid**, described
    two paragraphs up and then committed one paragraph down.

    **The root case needs no new rule; it is this rule with an empty base.** A
    name followed by one `.*` per marker becomes, when there is no name, one `*`
    per marker: `*`, then `*.*`. `design/rows.py` already defines a bare `*` as
    every child of the document and `design/parity.py` already tests it, so the
    label is typeable by a path language that predates the defect.
    """
    segs = [s.rstrip("[]") for s in p.split(".")]
    stars = 0
    while segs and segs[-1] == "<key>":
        segs.pop()
        stars += 1
    if not stars:
        # The callers only ask about a path whose last segment IS the marker.
        return "$"
    if not segs or segs[-1] == "$":
        return ".".join(["*"] * stars)
    return segs[-1] + ".*" * stars


def _rows_path(p):
    """A probe path as `design/rows.py` would write it, segment by segment.

    The probe writes `types[]` for an array's elements and `<key>` where a
    container's keys are data. `rows.py` writes one thing for both: `*` is
    *every child — object values and array elements alike*. So `types[]` is
    `types.*` and `<key>` is `*`, and a path printed this way is one a reader
    can type.
    """
    out = []
    for seg in p.split(".")[1:]:          # `$` is the document, not a segment
        star = seg.endswith("[]")
        name = seg[:-2] if star else seg
        out.append("*" if name == "<key>" else name)
        if star:
            out.append("*")
    return out


def _recursion_labels(paths, rec):
    """`a node at any depth`, qualified ONLY where the depth alone collides.

    DEFECT 29, repaired 2026-08-12. The label was the depth and nothing else, so
    `07-graphql-introspection` printed `a node at any depth (4 levels)` three
    times and `09-stripe-openapi` printed `(2 levels)` six times. **Seven
    candidates across the corpus could not be selected**, and on stripe the
    unreachable set included the document's largest table at 2,542 x 393 — the
    first line answered for all six.

    **Naming the shape does NOT fix it, which is why this is a path.** Measured:
    graphql's four recursive shapes are all called `type` and three of stripe's
    are called `items`. The bare name collides exactly where the depth does.

    **The qualifier is the shortest suffix that separates it from its rivals**,
    and only shapes that actually collide get one — `02-hn-thread`'s single
    recursion keeps the plain label, and 24 of 26 corpus reports are untouched.
    Minimality is what keeps this readable: on graphql it is `fields.*.type`,
    not the 44-character path.

    **A limit, stated rather than hidden**: two distinct probe paths can render
    to the same `rows.py` path — `$.a[]` and `$.a.<key>` are both `a.*` — and
    then no suffix separates them and the label stays ambiguous. Nothing in the
    corpus does this; the fallback is the full rendered path.
    """
    base = {p: f"a node at any depth ({rec[p] + 1} levels)" for p in paths}
    clashes = Counter(base.values())
    rendered = {p: _rows_path(p) for p in paths}
    out = {}
    for p in paths:
        if clashes[base[p]] == 1:
            out[p] = base[p]
            continue
        rivals = [q for q in paths if base[q] == base[p]]
        segs = rendered[p]
        suffix = ".".join(segs)
        for k in range(1, len(segs) + 1):
            here = ".".join(segs[-k:])
            if sum(1 for q in rivals if ".".join(rendered[q][-k:]) == here) == 1:
                suffix = here
                break
        out[p] = f"a node at any depth in {suffix} ({rec[p] + 1} levels)"
    return out


def candidates(doc, inst, arrs, rec):
    """Row shapes, computed on the FOLD rather than on the data.

    The first version of this recursed into raw values and emitted one candidate
    per version, producing 1,239 lines on a 786 KB file — reproducing the exact
    O(data) failure the probe exists to prevent. **The fold is not a display
    step.** Anything computed from raw values rather than from the folded
    structure will be proportional to the data no matter what it prints.
    """
    import pandas as pd
    out = []

    def price(records, label, more=None):
        if not records:
            return
        try:
            t = pd.json_normalize(records)
        except Exception:
            return
        if t.empty:
            return
        holes = t.isna().sum().sum() / (t.shape[0] * t.shape[1])
        # astype(str) because a column of lists is unhashable and nunique dies
        worst = max(((t[c].astype(str).nunique() or 1), c) for c in t.columns)
        dup = len(t) / worst[0]
        # DOES THIS TABLE WANT SPLITTING? Added 2026-08-09 after `12-agent-trace`
        # printed `SPLIT ON type — 10 kinds, 69% empty folded, 6% after` and
        # then, twenty lines later, offered `a record 1,953 rows x 319 cols 93%
        # empty` as the row candidate without reference to the split it had just
        # made. Same program, same fold, two numbers, no join — the third time
        # evidence sat on screen unconnected, after `07-graphql-introspection`
        # and `10-wikidata`.
        #
        # The honest answer to "what is one row" on a document of ten kinds is
        # TEN answers, and the operation that produces them has already run.
        out.append((label, t.shape[0], t.shape[1], holes,
                    (worst[1], dup) if dup > 2 else None,
                    discriminator(records), more))

    # A top-level array is the whole point of NDJSON, and the array loop below
    # skips "$", so it has to be named here or the format with the most obvious
    # row shape in the world would offer none.
    if isinstance(doc, list):
        if doc and all(isinstance(i, dict) for i in doc):
            price(doc, "a record")
        else:
            out.append(("a record", len(doc), 1, None, None, None, None))
    else:
        out.append(("the whole document", 1, len(doc), None, None, None, None))

    # A recursive shape's row count is the whole tree, not the top level. Priced
    # off the pooled records, because the array loop below sees only the outermost
    # array and would say 25 rows for a 336-node thread.
    labels = _recursion_labels([p for p in sorted(inst) if rec.get(p)], rec)
    for p, objs in sorted(inst.items()):
        if rec.get(p):
            price(objs, labels[p])

    # DEFECT 39, repaired 2026-08-18. **Defect 34's repair went to the ARRAY
    # loop below and this one never got it.** The diagnosis there is this loop's
    # verbatim: `seen` keeps the first path in sorted order for a name and drops
    # the rest silently, so the printed count is the count of ONE path while a
    # reader reads it as the count of the word.
    #
    # It did not need a second document — it had five. **50 of 161 keyed
    # candidate names hide a second path and 38 drop the BIGGER one**, across
    # `09-stripe-openapi`, `20-homebrew-formulae`, `28-home-assistant-i18n`,
    # `29-mdn-browser-compat` and `30-aws-redshift-pricing`. Entry 30 printed
    # `an entry of priceDimensions — 1,643 rows` where the document holds 4,505.
    # `uv run design/candidate-twins.py`.
    #
    # **The repair is defect 34's, not a new one**: the count stays and the page
    # says what it left out. Naming both paths was measured and rejected there
    # for the array loop and the same argument holds here.
    #
    # `classify` is asked ONCE per site and the result carried, because it is
    # the expensive call in this function and the pre-pass would otherwise
    # double it.
    keyed = []
    for q, qobjs in sorted(inst.items()):
        if q == "$" or classify(qobjs)[0] != "data":
            continue
        qname = q.split(".")[-1]
        if qname == "<key>":
            qname = _above_marker(q)
        if qname == "$":
            continue
        keyed.append((q, qname, [v for o in qobjs for v in o.values()]))

    # **A TWIN IS ANY KEYED SITE OF THAT NAME, not only one whose values are
    # records, and the difference is 10 modifiers against 51.** Restricting it
    # to record-valued sites is what the modifier's plumbing happens to make
    # easy — `more` rides through `price()`, and the scalar branch below builds
    # its tuple by hand — and it is not what the defect is. `20-homebrew-formulae`
    # prints `an entry of uses_from_macos[] — 84` while another keyed site of
    # that name holds 943; the reader is misled whether or not those values are
    # dicts.
    #
    # **The obvious worry does not arise: it never compares unlike things.**
    # All 305 twin relationships this widening adds are scalar-to-scalar, and
    # the corpus holds ZERO where a record-valued candidate has a scalar twin.
    # **So the mixed-kind branch is unreachable here and therefore untested** —
    # defect 30's lesson stated in advance rather than after, and the reason
    # this widening invents no same-kind rule to guard something no document
    # can currently exercise.
    keyed_by_name = defaultdict(list)
    for q, qname, qvals in keyed:
        if qvals:
            keyed_by_name[qname].append((q, len(qvals)))

    seen = set()
    for p, name, vals in keyed:
        if name in seen:
            continue
        seen.add(name)          # an empty site still CLAIMS the name, as before
        if not vals:
            continue
        twins = [(q, n) for q, n in keyed_by_name[name] if q != p]
        more = None
        if twins:
            more = (sum(n for _, n in twins), len(twins),
                    ".".join(_rows_path(twins[0][0])))
        if all(isinstance(v, dict) for v in vals):
            price(vals, f"an entry of {name}", more)
        else:
            out.append((f"an entry of {name}", len(vals), 2, None, None, None, more))

    # DEFECT 34, repaired 2026-08-13. `seen` keeps the FIRST path in sorted
    # order for a name and drops the rest silently, so the printed count is the
    # count of ONE path while the reader reads it as the count of the word.
    #
    # On `27-grafana-dashboard` the menu said `an item of panels — 31` and the
    # dashboard has 132; it said `an item of targets — 225` and there are 269.
    # **The two came from OPPOSITE levels by lexicographic accident** —
    # `$.panels` sorts before `$.panels[].panels` so the outer won, and
    # `$.panels[].panels[].targets` sorts before `$.panels[].targets` so the
    # inner did. `04-gharchive` is worse: `an item of labels — 5` where the
    # document holds 1,944.
    #
    # **NAMING BOTH WAS MEASURED AND REJECTED.** It adds 22 candidates to
    # `09-stripe-openapi` at 180-character `anyOf` paths holding four items
    # each, and 122 paths for one name on `29-mdn-browser-compat`. The menu
    # would be noise.
    #
    # What is wrong is not that one path is chosen — it is that the number
    # reads as complete. So the count stays and the page SAYS what it left out,
    # which is the same repair defect 33 made and the same one the field-list
    # and keyed-site caps already make. **41 lines across the whole corpus.**
    by_name = defaultdict(list)
    for q, qlists in sorted(arrs.items()):
        qstem = q.rstrip("[]")
        qname = qstem.split(".")[-1]
        if qname == "<key>":
            qname = _above_marker(qstem)
        qitems = [i for l in qlists for i in l]
        if qitems and all(isinstance(i, dict) for i in qitems):
            by_name[qname].append((q, len(qitems)))

    # DEFECT 39, SECOND FACET, repaired 2026-08-18. **`seen` used to be shared
    # with the keyed loop above**, which runs first — so an array site whose
    # bare name a keyed site had already claimed was skipped entirely and no
    # candidate was offered for it at all. **16 of them on
    # `29-mdn-browser-compat`**, including `chrome` at 120 items and `edge` at
    # 126.
    #
    # **The two loops emit DIFFERENT labels** — `an entry of X` against
    # `an item of X` — so nothing could ever have collided, and the shared set
    # was suppressing candidates it had no reason to. It reads as deliberate
    # and is not: the array loop was written second and reused the name in
    # scope.
    # DEFECT 41, repaired 2026-08-19. **The claim used to sit ABOVE the record
    # test**, so the first path in sorted order took the name whether or not it
    # produced anything, and a later path that would have produced a table was
    # never reached. This is defect 39's second facet one loop down: a name
    # claimed by a site that yields no candidate.
    #
    # **The worst instance is the corpus's polymorphism specimen.**
    # `12-agent-trace` holds `$[].attachment.content` — 66 arrays, every one
    # EMPTY — which sorts before `message` and claimed `content`. So
    # `$[].message.content`, **1,363 records over 11 fields**, was never
    # offered, and the report described in its body the one table its menu could
    # not name. Three smaller instances on `29-mdn-browser-compat`.
    #
    # **The repair is monotone and that is the property to check rather than
    # trust**: a name whose first path emits claims it exactly as before, so the
    # only thing that can change is a name that printed NOTHING now printing
    # something. Nothing is removed, renamed or renumbered.
    #
    # **The twin rule below is deliberately NOT widened, and that was measured.**
    # Defect 39 widened the keyed loop's rule because a twin there is any keyed
    # site; doing the same here buys 2 modifiers and adds 35 relationships, ALL
    # of them mixed — a record-valued candidate gaining a non-record twin, 30 of
    # them bigger than the printed count. The keyed loop emits scalar candidates
    # and this one never does, so the same widening relates like to like there
    # and unlike to unlike here. **The two loops run different rules on purpose.**
    # `uv run design/array-twins.py`.
    seen_arrays = set()
    for p, lists in sorted(arrs.items()):
        stem = p.rstrip("[]")
        name = stem.split(".")[-1]
        if name == "<key>":
            name = _above_marker(stem)
        if name in seen_arrays or name == "$":
            continue
        items = [i for l in lists for i in l]
        if not items or not all(isinstance(i, dict) for i in items):
            continue
        seen_arrays.add(name)
        twins = [(q, n) for q, n in by_name[name] if q != p]
        more = None
        if twins:
            more = (sum(n for _, n in twins), len(twins),
                    ".".join(_rows_path(twins[0][0].rstrip("[]"))))
        price(items, f"an item of {name}", more)

    # DEFECT 27, repaired 2026-08-11. The probe DETECTED positional alignment,
    # printed it, and then offered no way to ask for it. On `06-espn-qbr` the
    # four arrays under `$.categories[]` are a 10 x 4 table the menu never
    # mentioned — while `an item of glossary`, the alphabetically sorted decoy
    # the section above warns against joining, WAS offered. `08-open-meteo` is
    # the worse case: its entire menu was one line, `the whole document`, and
    # the 336 x 5 table that IS the document was absent.
    #
    # ONE CANDIDATE PER PARENT, not one per length group, because THE PARENT IS
    # THE TABLE is the rule `positional()` already enforces. File 06's group of
    # six paths spans two parents holding 1 and 28 instances, so a single 10 x 6
    # candidate would name a table that cannot be built without the very join
    # the section above forbids — same length is not same order.
    #
    # NAMED BY PATH, and the bare name was tried first. Both of file 06's
    # parents end in `categories` and `an item of categories` is already in the
    # menu, so every bare-name scheme either collides or drops the one table the
    # defect names. The path is printed directly above in this same notation. A
    # candidate a reader cannot type is defect 28, and fixing 27 by creating
    # another 28 is not a fix.
    #
    # ROWS POOL ACROSS INSTANCES, like every other candidate here: `an item of
    # categories` says 28 for 28 parents of one item each. The instance count is
    # the largest any of the parent's columns has — a column missing from some
    # instances is a hole in the table, not fewer rows, which is how the rest of
    # this function already treats an absent field. Both corpus files with
    # alignment have columns that agree exactly, so the max is a rule for the
    # document that has not arrived rather than one fitted to these two.
    #
    # NOT PRICED THROUGH `price()`. Emptiness is zero by construction — the
    # columns are equal-length scalar arrays — and there are no records to find
    # a discriminator in. Materialising the table to learn that would contradict
    # the rule this function opens with.
    for n, ps in sorted(positional(arrs).items()):
        by_parent = defaultdict(list)
        for p, lists in ps:
            by_parent[p.rpartition(".")[0]].append(lists)
        for parent, cols in sorted(by_parent.items()):
            out.append((f"a position in {parent}", n * max(len(c) for c in cols),
                        len(cols), None, None, None, None))
    return out


# ── render ───────────────────────────────────────────────────────────────────

def _fields(label, items, width=92):
    """A record shape's field list, in full, wrapped under its label.

    Wrapping rather than truncating is the whole of defect 20's repair. Output
    stays proportional to the STRUCTURE — a shape with 97 fields costs 97 names
    however many million records carry them — which is the property being
    defended, and it is not the property the eight-name cap was defending.

    The 17-character indent is load-bearing and not cosmetic: `coverage.py`
    reads this report as a set of claims, and a continuation line has to be
    distinguishable from a new shape header (4 spaces) or a `SPLIT ON` (6).
    """
    for out in _field_lines(label, items, width):
        print(out)


def _field_lines(label, items, width=92):
    """`_fields`, rendered rather than printed, so its SIZE can be compared.

    Split out for defect 25: the back-reference that replaces a duplicate field
    list is only worth printing when it is shorter than the list, and that is a
    measurement rather than a guess.
    """
    if not items:
        return [f"      {label:<11}(none)"]
    lines, line = [], ""
    for it in items:
        if line and len(line) + 1 + len(it) > width:
            lines.append(line)
            line = it
        else:
            line = f"{line} {it}" if line else it
    lines.append(line)
    return ([f"      {label:<11}{lines[0]}"] +
            [f"      {'':<11}{extra}" for extra in lines[1:]])


def main(path):
    h, doc = health(path)
    print(f"\n> fathom({path.split('/')[-1]!r})\n")

    b = h["bytes"]
    size = f"{b} bytes" if b < 1024 else \
           (f"{b/1024:.0f} KB" if b < 2**20 else f"{b/2**20:.1f} MB")

    if h["format"] is None:
        what = ("empty" if h.get("empty") else
                "chopped off" if h.get("truncated") else "not a format I recognise")
        print(f"  {size} · {what}")
        print(f"  {h['error']}")
        return
    bad = h.get("bad_lines") or []
    said = {"JSON": "valid JSON · read whole file",
            "NDJSON": f"NDJSON, {h.get('records', 0):,} of {h.get('lines', 0):,} "
                      "records read · not one JSON document, and not broken",
            "JSONC": "JSONC, comments and trailing commas · "
                     "not valid JSON, and not broken"}[h["format"]]
    if h.get("compressed"):
        said = (f"{h['packed_bytes']/2**20:.1f} MB of {h['compressed']}, "
                f"unpacked to {size} · ") + said
        size = f"{h['bytes']/2**20:.1f} MB"
    flags = [f"{h['dupes']} duplicate keys" if h["dupes"] else "no duplicate keys",
             f"{h['nonfinite']} NaN/Infinity" if h["nonfinite"] else "no NaN or Infinity",
             f"{h['bigints']} ints past 2^53" if h["bigints"] else "no ints past 2^53"]
    for k, msg in (("negzero", "negative zeros, sign lost on parse"),
                   ("bad_bytes", "bytes that are not valid UTF-8"),
                   ("encoded", "values that are themselves encoded JSON")):
        if h.get(k):
            flags.append(f"{h[k]} {msg}")
    enc = f" · {h['bom']} BOM" if h.get("bom") else ""
    print(f"  {size} · {said}{enc}")
    print("  " + " · ".join(flags))
    if bad:
        # Coverage honesty: say what could not be read, and where.
        print(f"  {len(bad)} line{'s' if len(bad) > 1 else ''} could not be read, "
              f"first at line {bad[0][0]} — everything below describes the rest")
    if h.get("sampled"):
        # The sampling contract. The probe must never let a reader believe a
        # description covers a document it only sampled. It says how much it
        # read, and everything downstream is scoped to that and nothing more.
        print(f"  SAMPLE: the first {h['records']:,} of {h['lines']:,} records. "
              f"Everything below describes those and cannot speak for the rest.")

    inst, arrs, types = containers(doc)
    inst, arrs, rec, types = fold_recursion(inst, arrs, types)
    keyed, undecided, saturated = [], [], []
    for p, objs in sorted(inst.items()):
        verdict, why = classify(objs)
        if verdict == "data":
            keyed.append((p, sum(len(o) for o in objs) // max(len(objs), 1), why))
        elif verdict == "undecided" and p != "$":
            undecided.append(p)
        elif verdict == "saturated" and p != "$":
            # The count classify() reasoned about, not the raw one — it drops
            # empty objects first, so sorting on len(objs) here ordered the list
            # by a number the line beside it does not print.
            saturated.append((p, sum(1 for o in objs if o), why.split(" — ")[0]))

    print("\n  KEYS THAT ARE DATA")
    # Biggest first and capped. `09-stripe-openapi` has 47 sites whose paths run
    # past 180 characters, and an unordered list of 47 is not a description.
    for p, n, why in sorted(keyed, key=lambda k: -k[1])[:SHOW]:
        print(f"    {p[:110]:<40} {{{n} keys}}   {why}")
    if len(keyed) > SHOW:
        rest = sorted(keyed, key=lambda k: -k[1])[SHOW:]
        print(f"    … and {len(rest)} more keyed sites, the largest {rest[0][1]} keys")
    if undecided:
        # Itemising every undecided case with its reasoning drowned the output on
        # the first run. An honest "I cannot tell" has to be summarised or it
        # becomes noise, which is itself a finding. See design/probe-sketch.md.
        # Capped. This line was written for `01-npm-registry`'s 17 short paths
        # and on `09-stripe-openapi` it became ONE line carrying 152 paths of
        # ~180 characters each — a wall of text that a line count does not show
        # and a reader cannot use. The failure it was invented to prevent,
        # arriving through its own fix.
        head = [u for u in undecided[:8]]
        print(f"    could not call {len(undecided)} small single-copy objects, "
              f"shortest first:")
        for u in sorted(head, key=len):
            print(f"      {u[:96]}")
        if len(undecided) > len(head):
            print(f"      … and {len(undecided) - len(head)} more")
    if saturated:
        # DEFECT 23: this used to be folded into the line above, which said
        # "small single-copy objects" about `$[].bottle.stable.files` and its
        # 8,531 copies. The label was written when `undecided` had one cause;
        # the saturation branch gave it a second and the sentence was never
        # revisited. **A right verdict with a lie attached sends a reader to
        # look at single-copy objects that are not the problem**, so the two
        # causes are now counted and named separately.
        print(f"    could not call {len(saturated)} "
              f"{'site' if len(saturated) == 1 else 'sites'} whose whole key "
              f"vocabulary would fit in a field list, most copies first:")
        for p, n, why in sorted(saturated, key=lambda s: -s[1])[:8]:
            print(f"      {p[:60]:<60} {why}")
        if len(saturated) > 8:
            print(f"      … and {len(saturated) - 8} more")

    print("\n  RECORD SHAPES, FOLDED")
    # MOST COPIES FIRST, AND CAPPED, and both halves matter. The order was
    # alphabetical, so on any large document the single most important shape sat
    # wherever its path happened to sort. The cap is because
    # `09-stripe-openapi` has 327 shapes — 223 of them under ten copies — and
    # produced a 943-line description, which is not proportional to anything a
    # reader can hold.
    #
    # It bites only where the problem is: six of the nine corpus files have 19
    # shapes or fewer and are untouched. What is dropped is SAID, with the size
    # of the largest thing dropped, because a silent cap reads as completeness.
    shown = [(p, [o for o in objs if o]) for p, objs in inst.items()]
    shown = [(p, o) for p, o in shown if len(o) >= 2 and classify(o)[0] != "data"]
    # A SHAPE THAT SPLITS IS NEVER DROPPED. Sorting by copies alone cost four of
    # `09-stripe-openapi`'s five splits to the cap on the first attempt, which is
    # a display limit hiding the most important thing the probe has to say.
    splits = {p: discriminator(o) for p, o in shown}
    shown.sort(key=lambda kv: (splits.get(kv[0]) is None, -len(kv[1])))
    dropped = shown[SHOW:]
    # ONE SHAPE IS DESCRIBED ONCE — defect 25, found by `23-cratesio-summary`.
    #
    # A record type reached through several containers was printed once per
    # container. crates.io's summary has ELEVEN object sites and FIVE distinct
    # key-sets: the 23-field crate record arrives under `new_crates`,
    # `most_downloaded`, `most_recently_downloaded` and `just_updated`, and its
    # `links` does the same, so 32 of 49 lines said something already said.
    # Corpus-wide it was **83 of 324 printed shapes**.
    #
    # `fold_recursion()` already knows identical key-sets are one shape, and
    # merges them when one is REACHABLE from the other — that guard is defect
    # 1's repair and is not touched here. Siblings are not recursion.
    #
    # **The test is deliberately exact: same `always` names, same `sometimes`
    # names AND the same counts**, so the block replaced would have been
    # byte-identical and nothing a reader could have learned is lost. A looser
    # test keyed on names alone collapses ten more sites across the corpus and
    # would drop their per-site `sometimes` counts, which are real. 83 of 93 for
    # no information at all is the better trade, and it was measured before it
    # was chosen.
    #
    # **This does NOT relieve the shape cap and that half of the defect stays
    # open.** A collapsed shape still occupies one of `SHOW`'s slots, so the
    # naming cost `design/coverage.py` attributes to the cap is unchanged.
    seen = {}
    for p, objs in shown[:SHOW]:
        c = Counter()
        for o in objs:
            c.update(o.keys())
        always = sorted(k for k, v in c.items() if v == len(objs))
        some = sorted(((v, k) for k, v in c.items() if v < len(objs)), reverse=True)
        shapes = len({frozenset(o.keys()) for o in objs})
        deep = f" · RECURSIVE, {rec[p] + 1} levels" if rec.get(p) else ""
        print(f"    {p}   {len(objs)} copies · {len(c)} fields · "
              f"{shapes} distinct key-set{'s' if shapes > 1 else ''}{deep}")
        # EVERY FIELD, WRAPPED, because a field list IS the structure and
        # truncating it truncates the answer. Repaired 2026-08-10 as defect 20,
        # found by `design/coverage.py`.
        #
        # The `sometimes` line used to stop after eight names. Measured, that hid
        # **207 field names across the corpus** — `05-fhir-bundle` 87,
        # `14-nyc-311` 27, `10-wikidata` 25, `01-npm-registry` 23 — and on
        # nyc-311 it left **27 of 48 fields** out of a 20,000-record description,
        # which is 39.4% of that document's field occurrences.
        #
        # **The asymmetry was the worst part**: the cap fell on `sometimes` and
        # never on `always`, so what it dropped was precisely the RAGGED fields,
        # which are the property this project exists to describe.
        #
        # **This does not undo defect 8**, and the measurement is why. That entry
        # capped a 943-line report on `09-stripe-openapi`, and the cap doing that
        # work is `SHOW`, on the number of SHAPES — Stripe has 366 shapes and its
        # widest holds 16 fields, so it loses only 12 names here. The two caps
        # were doing different jobs and only one of them was earning its keep.
        # `always (none)` is a fact — nothing is universal here. `sometimes
        # (none)` is noise, because the header's `1 distinct key-set` has
        # already said it, so the line is omitted exactly as it was before
        # defect 20's repair. Preserved deliberately: the first version of that
        # fix printed it and added 60 empty lines across the corpus.
        block = _field_lines("always", always)
        if some:
            block += _field_lines("sometimes", [f"{k}({v})" for v, k in some])
        sig = (tuple(always), tuple(some))
        ref = seen.get(sig)
        back = f"      same shape as {ref[:96]}" if ref else ""
        # SAY IT ONCE, UNLESS SAYING WHERE COSTS MORE THAN SAYING IT AGAIN.
        # Measured: collapsing unconditionally made SIX of the eleven affected
        # files LARGER, because a three-field list is cheaper than a reference to
        # a fifty-character path — `05-fhir-bundle` grew 452 bytes. The two
        # criteria agree anyway, which is why this is a rule and not a hack: the
        # value of the back-reference is that a reader cannot eyeball two
        # 23-field lists as identical, and that value rises with the same length
        # the saving does.
        if ref and len(back) + 1 < sum(len(b) + 1 for b in block):
            print(back)
        else:
            seen.setdefault(sig, p)
            for out in block:
                print(out)

        # Defect 26, printed where a reader meets the fields rather than as
        # its own section: the shape above just listed `types` among 26 names
        # with nothing saying it is a list.
        packs, wrapper = packed(objs)
        if packs:
            print(f"      └─ {', '.join(packs)} "
                  f"{'are lists' if len(packs) > 1 else 'is a list'} packed into "
                  f"text — {wrapper!r} wraps every value and "
                  f"{len(packs)} fields here share it")

        found = splits.get(p)
        if found:
            # The fold reporting that it should not have folded. Printed right
            # under the shape it is contradicting, because the reader has to see
            # the 97-field 87%-empty version to understand why 20 tables is the
            # answer rather than a complication.
            field, groups = found
            # Say which disorder the split removes. `05-fhir-bundle`'s is holes;
            # `10-wikidata`'s is 0% empty and entirely disagreement about the
            # shape of a value, and reporting that as "0% empty folded, 0% worst
            # split" told the reader nothing about why it was worth doing.
            gs = list(groups.values())
            if variation(objs) > emptiness(objs):
                what = (f"{variation(objs):.0%} of fields disagree on shape, "
                        f"{weighted(gs, variation):.0%} after")
            else:
                what = (f"{emptiness(objs):.0%} empty folded, "
                        f"{weighted(gs, emptiness):.0%} after")
            print(f"      SPLIT ON   {field} — {len(groups)} kinds, "
                  f"not one shape. {what}")
            for v, g in sorted(groups.items(), key=lambda kv: -len(kv[1]))[:6]:
                # Columns the group FILLS, so the count and the percentage next
                # to it are measuring the same table.
                cols = len(set().union(*[filled(o) for o in g]))
                print(f"        {str(v)[:28]:<30} {len(g):>5} x {cols:>3} cols   "
                      f"{emptiness(g):.0%} empty")
            if len(groups) > 6:
                rest = sorted(groups.values(), key=len)[:-6]
                print(f"        … {len(groups) - 6} more, "
                      f"{sum(len(g) for g in rest)} instances")

    if dropped:
        print(f"    … and {len(dropped)} more record shapes, the largest "
              f"{len(dropped[0][1])} copies. Ordered by copies, so what is above "
              f"is the biggest of them.")

    # A null is not a type, repaired 2026-08-09 after `11-jupyter-notebook`.
    # The probe printed `execution_count  number x131, null x1` under FIELDS
    # THAT CHANGE TYPE for one unexecuted cell in 272, while `axes.py` graded
    # the same file polymorphic 0 and ragged-by-null 1. `axes.py` was right —
    # `README.md` split those axes apart on 2026-08-08 because they are
    # orthogonal — and it already carried this exact rule. Two instruments in
    # one repository disagreeing about one field is defect 5's shape again.
    poly = {p: c for p, c in types.items()
            if len({t for t in varies(c) if t != "null"}) > 1}
    if poly:
        print("\n  FIELDS THAT CHANGE TYPE")
        # DEFECT 33, repaired 2026-08-12, and this section was the only one of
        # the four without a cap. `29-mdn-browser-compat` has 1,336 fields that
        # change type, so it printed 1,444 lines of a 1,962-line report — 74% of
        # the page, and a description larger than 24 of the 29 corpus documents
        # in their entirety.
        #
        # **The argument against it is already written above the keyed-site cap**:
        # *"an unordered list of 47 is not a description."* 1,336 is not one
        # either, and the inconsistency was the whole defect — three sections cap
        # and name what they dropped, the fourth did neither.
        #
        # **It is proportional to STRUCTURE and that is not a defence.** 1,336
        # polymorphic fields is a structural fact, so `README.md`'s claim held
        # literally while the report became the thing a reader wanted to avoid.
        #
        # MOST VALUES FIRST, like every other cap here, and what is dropped is
        # SAID with the size of the largest — because a silent cap reads as
        # completeness, which is defect 20's lesson kept rather than relearned.
        ordered = sorted(poly.items(), key=lambda x: -sum(x[1].values()))
        for p, c in ordered[:SHOW]:
            spread = ", ".join(f"{t} x{n:,}" for t, n in c.most_common())
            print(f"    {p:<44} {spread}")
            # A field can look polymorphic only because the fold merged records
            # of different kinds. On `05-fhir-bundle` all three reported
            # polymorphisms were this: `Encounter.type` is always an array and
            # `Claim.type` is always an object, and neither resource has a field
            # that changes type. Saying "changes type" and "split into 20 kinds"
            # in one report without connecting them leaves the reader to notice.
            holder, _, field = p.rpartition(".")
            found = discriminator(inst.get(holder, []))
            if found and all(
                    len(varies(Counter(shape(o[field]) for o in g if field in o))) <= 1
                    for g in found[1].values()):
                print(f"    {'':<44} └─ not really: one type within each "
                      f"{found[0]}. An artifact of folding {len(found[1])} kinds.")
                continue
            # MISSINGNESS WEARING A VALUE. Added 2026-08-09 after
            # `16-movie-ratings`, where `Gross: "unknown"` and `Tomato Score:
            # "unkown"` stand in for absent values. 17 of 159 present cells are
            # sentinels, so the probe printed `54% empty` where the truth is 58%,
            # and every emptiness measure counts a key with a value as filled.
            #
            # **Five structural detectors were measured before this one and all
            # five failed**, across every field of every corpus file: modal value
            # in a mostly-distinct column (the three real sentinels sit mid-pack
            # among 108 candidates — version constraints, SNOMED codes, dates);
            # a value recurring across unrelated fields (silent on this very file
            # and 2,557 false candidates on `14-nyc-311`); plus vocabulary size,
            # modal key frequency and records-per-kind, rejected earlier today.
            #
            # What works is the narrowest reading: **a field that is a NUMBER on
            # some records and one of very FEW strings on others.** Across all
            # sixteen corpus files exactly two fields match, and both are this
            # bug, each with a single distinct string. Zero false positives.
            #
            # **Re-measured 2026-08-15 over all 29: still exactly two, still
            # both on `16-movie-ratings`, still zero false.** The evidence
            # behind this detector has nearly doubled since it was written and
            # the answer has not moved — which is worth recording, because the
            # relaxed rule for defect 26 was called complete on 25 documents and
            # produces 386 false positives on the 29th.
            #
            # **There is no counterexample in the corpus, so `<= 3` is a guess
            # with headroom rather than a fitted constant, and it is written here
            # rather than as a named threshold so nobody mistakes it for one.**
            # It reports and changes no number: `README.md` says report, never
            # repair, and a sentinel is the document's problem, not the probe's.
            vals = [o[field] for o in inst.get(holder, [])
                    if isinstance(o, dict) and o.get(field) is not None]
            nums = [v for v in vals
                    if isinstance(v, (int, float)) and not isinstance(v, bool)]
            txts = sorted({v for v in vals if isinstance(v, str)})
            if nums and txts and len(txts) <= 3:
                shown = ", ".join(repr(t) for t in txts)
                print(f"    {'':<44} └─ {shown} where a number was expected — "
                      f"missing, written as a value. Not counted as empty.")
        if len(ordered) > SHOW:
            rest = ordered[SHOW:]
            print(f"    … and {len(rest):,} more fields that change type, "
                  f"the largest {sum(rest[0][1].values()):,} values")

    aligned = positional(arrs)
    if aligned:
        print("\n  ALIGNED BY POSITION, NOT BY NESTING")
        for n, ps in sorted(aligned.items()):
            # A header row is only possible when the arrays are split across
            # parents. When they all share one, their names ARE the keys and
            # anything that merely looks like a header is a data column — which
            # is how a timestamp column got announced as the names on file 08.
            one_parent = names_are_keys([p for p, _ in ps])
            names = [] if one_parent else [p for p, lists in ps
                                           if looks_like_names(lists)]
            print(f"    {len(ps)} paths hold arrays of exactly {n} — "
                  f"same length everywhere, so probably one table stored in columns")
            for p, lists in ps:
                tag = "   <- the names" if p in names else ""
                sample = ", ".join(str(v) for v in lists[0][:4])
                print(f"      {p:<46} {sample[:38]}{tag}")
            if names:
                # The whole point. A reader who cannot see this joins against
                # whatever names the fold DID surface, and on file 06 that was an
                # alphabetically sorted decoy of the same length.
                #
                # All candidates are listed rather than one being chosen. File 06
                # offers three — `labels`, `names`, `displayNames` — and they are
                # three spellings of the same header, so picking one would be
                # arbitrary dressed as an answer.
                print(f"      to name the others, zip them in order against "
                      + " or ".join(p.rpartition('.')[2] for p in names))
                print(f"      NOT against another array of {n} found elsewhere: "
                      f"same length is not same order")
            elif one_parent:
                # Said explicitly, because "no header row" and "the names are
                # right here" are different facts and the reader needs the
                # second one. This is also the safe case, and saying so is what
                # stops the ESPN warning from being printed where it is noise.
                parent = ps[0][0].rpartition(".")[0]
                print(f"      the names are the keys of {parent} — nothing to "
                      f"join and nothing to mis-join")

    print(f"\n  {_depth(doc)} levels deep · {len(_paths(doc)):,} distinct paths")

    # **The menu says what it is FOR, added 2026-08-15 for the menu-label
    # defect.** The page printed one list and the vocabulary read it two ways:
    # `rows("an entry of dependencies")` works from anywhere, `into("dependencies")`
    # refuses at the root, and nothing said which a label was. 242 of 324 named
    # candidates — 75% — are not navigable IN ONE STEP FROM THE ROOT, so the
    # common case was the broken one. **The qualifier matters**: `navigable()`
    # runs `--at <name>` once from the root, so it measures typeable-as-it-stands
    # and not reachable-at-all — `10-wikidata` scores 0 and
    # `into("entities") → into("aliases")` works. The repair is unaffected: a
    # label a reader has just been shown and cannot type is the defect either
    # way. `FINDINGS.md` 2026-08-15.
    #
    # **Three recorded repairs were refuted by measurement and this fourth was
    # not among them.** Printing the path costs width on every line and overflows
    # `WIDTH` on 15 of 29 documents; letting `into()` take a label cannot be
    # specified, 99 labels naming two or more folded paths; separating the two
    # lists is a no-op on 9 of 29 and reorders the menu on the other 20.
    # **This costs one clause on a header that already exists, on every document,
    # and moves nothing.** `design/vocabulary.md`, `FINDINGS.md` 2026-08-15.
    print("\n  ONE ROW COULD BE — give any of these to rows()")
    for label, rows, cols, holes, dup, split, more in candidates(doc, inst, arrs, rec):
        bits = f"{rows:>7,} rows"
        if cols:
            bits += f" x {cols:>4} cols"
        if holes is not None and holes > 0.1:
            bits += f"   {holes:.0%} empty"
        if dup:
            bits += f"   {dup[0]} repeated {dup[1]:.0f}x"
        print(f"    {label:<34}{bits}")
        # The join, added 2026-08-09. A candidate whose records carry a
        # discriminator is not one table, and the probe knew that before it
        # printed the line above.
        if split:
            field, groups = split
            top = sorted(groups.items(), key=lambda kv: -len(kv[1]))
            names = ", ".join(f"{str(v)[:18]} {len(g):,}" for v, g in top[:4])
            extra = f", +{len(top) - 4} more" if len(top) > 4 else ""
            print(f"      └─ or {len(groups)} tables, split on {field} — "
                  f"{weighted(list(groups.values()), emptiness):.0%} empty: "
                  f"{names}{extra}")
        # DEFECT 34. The count above is one path's; say what it leaves out.
        if more:
            n, k, where = more
            at = where if k == 1 else f"{k} other paths"
            print(f"      └─ {n:,} more at {at} — not counted above")
    print()


def _depth(o):
    if isinstance(o, dict) and o:
        return 1 + max(_depth(v) for v in o.values())
    if isinstance(o, list) and o:
        return 1 + max(_depth(v) for v in o)
    return 0


def _paths(o, p="", acc=None):
    acc = set() if acc is None else acc
    if p:
        acc.add(p)
    if isinstance(o, dict):
        for k, v in o.items():
            _paths(v, f"{p}.{k}", acc)
    elif isinstance(o, list):
        for v in o:
            _paths(v, p + "[]", acc)
    return acc


if __name__ == "__main__":
    main(sys.argv[1])
