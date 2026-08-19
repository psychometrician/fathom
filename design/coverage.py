"""COVERAGE: is a small description small because it FOLDED, or because it DISCARDED?

    uv run design/coverage.py                     # every corpus entry, the probe
    uv run design/coverage.py <file> [<file> …]
    uv run design/coverage.py --tool polars       # or --tool pandas

`VERDICT.md` measures every describer in this project by **size** — 61% of npm,
172% of Stripe, a slope of 52x input against 1.9x description. Size is half a
measurement, and the corpus has now caught one tool being small for the wrong
reason **four separate times**:

    03-natural-earth   json_schema picks one nesting level, silently
    05-fhir-bundle     names 64% of the top-level key union, silently
    07-graphql         flattens an unbounded recursion to a bound
    10-wikidata        types `datavalue.value` as an object for all 4,401 snaks
                       when 1,352 hold a plain STRING

That last one is why this file measures types rather than key names. On
`10-wikidata` `json_schema` covers **100% of the key names** and is wrong about
**31% of the records**, so a key-name instrument would have passed it. `VERDICT.md`
item 22a records this and says the coverage instrument does not exist. It does now.

**The measurement.** One ground truth for every tool: walk the document and count
every object field occurrence as `(path, type)`. Array indices fold to `[]`
because no describer numbers them. Nothing else folds — a tool that folds keys is
credited for the fold by matching a *pattern*, so folding is rewarded and not
assumed.

Every occurrence lands in exactly one of four buckets, and they sum to the
document:

    typed right    the description names this path and admits this type
    TYPED WRONG    it names the path and asserts types that exclude what is here
    named, untyped it names the path and says nothing about the type
    unnamed        it does not mention this path at all

**The middle two are different failures and collapsing them would lose the
distinction this project already treats as load-bearing.** `VERDICT.md` on the
closed-vocabulary limit: *"with one copy the probe admits it cannot tell; with a
thousand it states the wrong answer."* Silence costs a reader a lookup. A wrong
assertion costs them a bug they will not go looking for.

**A stated charity, so nobody reads more into a number than is in it.** The
probe's own keys-as-data judgment is used to fold the paths its patterns are
matched against, because operation 2 is not what is under test here and a
disagreement about the fold would swamp the thing that is. If the probe folds
something it should not have, this instrument credits it. The denominator is the
unfolded occurrence count either way, so the four buckets remain comparable
across tools that fold and tools that do not.

**Why three tools and not one.** `polars` is the calibration: it makes exactly
one wrong claim in 310,579 occurrences and it is the 122-Polygon promotion
`VERDICT.md` already records, which is how "the probe states no wrong type"
becomes a measurement rather than a blunt instrument. `pandas` is the case the
size statistic cannot see at all — on `03-natural-earth` its whole description is
`['type', 'features']`, **twenty characters covering nothing**, and by size alone
that is the best answer any tool in this project gives to a 4 MB document.

**What this cannot see.** A description that names a path and types it correctly
still says nothing here about whether it named the *right* path, priced the right
row, or led anyone anywhere useful. Coverage is a floor on honesty, not a measure
of help.
"""
import json
import os
import re
import subprocess
import sys
from collections import Counter

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)

import probe  # FROZEN at 981a45f0…. Imported and never modified; see CLAUDE.md.


# ── the ground truth ─────────────────────────────────────────────────────────

def truth(doc, big=frozenset()):
    """Every object field, once per occurrence, under two names.

    Returns Counter[(concrete, folded, type)]. `concrete` keeps every key as it
    is written and is what a tool that does not fold must match. `folded`
    collapses the keys at the sites in `big` to `<key>`, and is what a tool that
    folds is matched against. **The two differ only in name — the count is the
    same**, which is what keeps the denominator identical across tools.

    Array indices collapse to `[]` in both, because no describer in the
    comparison numbers them and grading one as though it should would measure
    nothing but that convention.
    """
    acc = Counter()

    def go(o, cp, fp):
        if isinstance(o, dict):
            for k, v in o.items():
                ck = f"{cp}.{k}"
                fk = f"{fp}.<key>" if fp in big else f"{fp}.{k}"
                acc[(ck, fk, probe.shape(v))] += 1
                go(v, ck, fk)
        elif isinstance(o, list):
            for v in o:
                go(v, cp + "[]", fp + "[]")

    go(doc, "$", "$")
    return acc


def fold_sites(doc):
    """The probe's own keys-as-data verdict, asked rather than recomputed.

    **This used to repeat `containers()`'s fixed point here**, because that
    function returns the walk and not the set and `probe.py` is frozen — a
    freeze is not a thing to break for tidiness. **Defect 36's repair broke it
    for a reason instead**, on 2026-08-18: `where` needed the same set, and two
    copies of a fixed point was already one too many. `probe.fold_set()` is now
    the one definition and this asks it.

    The duplication was never harmless. The comment it replaces said an
    instrument that recomputes the fold silently measures a probe that never
    ran, and that is exactly what `where` was doing at the time — with a
    different test, which is what defect 36 turned out to be.
    """
    return probe.fold_set(doc)[0]


def recursion_fold(doc, big):
    """Where the probe's RECURSIVE fold sends a container path.

    **Without this the instrument reports a false miss the size of the
    document.** `02-hn-thread` first scored 99.7% unnamed, because a comment
    thread's deep paths — `$.children[].children[].children[].author` — are
    described once, at the top, as one shape that contains itself thirteen levels
    down. That is operation 1 working exactly as intended, and a grader that
    cannot see it is measuring its own blindness.

    `fold_recursion()` computes this map and returns the merged walk rather than
    the map, so it is reconstructed from what it does return: a container is
    canonical when it survives into the merged walk, and one that did not was
    folded onto its **shortest** ancestor-prefix carrying the same key set, which
    is the ancestor that function's own `sorted(..., key=len)` selects.
    """
    inst, arrs, types = probe._walk(doc, big)
    merged, _, _, _ = probe.fold_recursion(inst, arrs, types)
    keyset = {p: frozenset(k for o in objs for k in o)
              for p, objs in inst.items() if any(objs)}
    canon = {}
    for p in keyset:
        if p in merged:
            continue
        canon[p] = next((a for a in sorted(merged, key=len)
                         if p.startswith(a) and keyset.get(a) == keyset[p]), p)
    return canon


# ── reading a description as claims ──────────────────────────────────────────
#
# A claim is a path pattern and the types it asserts. `None` means the path was
# NAMED AND NOT TYPED, which is a different answer from an absent path and is
# scored differently.

TYPE_TOK = r"(?:null|text|number|boolean|object|array|array\[\d+\] \w+)"
SHAPE_HDR = re.compile(r"^    (\S.*?)   \d[\d,]* copies · ")
POLY_ROW = re.compile(rf"^ +(\S.*?) +({TYPE_TOK} x[\d,]+(?:, {TYPE_TOK} x[\d,]+)*)$")
COUNTED = re.compile(r"(\S(?:[^()]*\S)?)\(\d[\d,]*\)")
KEYED_ROW = re.compile(r"^    (\S.*?) +\{\d[\d,]* keys\}   ")
# A wrapped field list, continued. `probe._fields()` indents continuations by
# exactly 17, which no other line in the report uses — a shape header is 4, a
# `SPLIT ON` is 6, a split group is 8. Added with defect 20's repair; without it
# this instrument would score only the first line of every field list and report
# the repair as having made things worse.
CONT_ROW = re.compile(r"^ {17}(\S.*)$")
ALIGNED_ROW = re.compile(r"^      (\$.+?)  +\S")
SPLIT_ROW = re.compile(r"^      SPLIT ON   (\S.*?) — \d+ kinds,")

SECTIONS = ("KEYS THAT ARE DATA", "RECORD SHAPES, FOLDED", "FIELDS THAT CHANGE TYPE",
            "ALIGNED BY POSITION, NOT BY NESTING", "ONE ROW COULD BE")

#: Which of `SECTIONS` were actually matched anywhere in the run.
#:
#: **An anchor that can stop matching needs something to check it against.** On
#: 2026-08-15 the `ONE ROW COULD BE` header gained a clause and this file matched
#: it by equality; the section would simply have stopped being recognised and its
#: names scored as unnamed — which reads as the probe getting WORSE rather than
#: as the instrument breaking. A section that is never seen on any of 29
#: documents is not a document property, it is a broken anchor, and `main()`
#: says so.
SEEN = set()


def _names(rest, known):
    """Split a space-joined field list, given the names that actually occur.

    **The probe's `always` line is ambiguous and this is not a hypothetical.**
    It prints `' '.join(always)`, so `Popcorn Score Rating` is three names or two
    and the format cannot say which — `16-movie-ratings` has exactly this. The
    reader resolves it by knowing the document, so this does too: longest known
    name first, falling back to a bare token when nothing matches.
    """
    out, i, rest = [], 0, rest.strip()
    order = sorted(known, key=len, reverse=True)
    while i < len(rest):
        if rest[i] == " ":
            i += 1
            continue
        for name in order:
            if rest.startswith(name, i) and (
                    i + len(name) == len(rest) or rest[i + len(name)] == " "):
                out.append(name)
                i += len(name)
                break
        else:
            j = rest.find(" ", i)
            j = len(rest) if j < 0 else j
            out.append(rest[i:j])
            i = j
    return [o for o in out if o not in ("(none)", "…")]


def probe_claims(text, fields_at):
    """Read `design/probe.py`'s PRINTED report as claims.

    The printed text is parsed rather than the probe's internals re-run, because
    **the printed text is the description a person is actually handed** — the
    `SHOW` cap, the eight-field `sometimes` truncation and the dropped-shapes
    line included. A claim set rebuilt from internals would score a description
    nobody ever sees, which is the same error as scoring a model on its training
    set.

    `fields_at` maps a folded container path to the field names really under it.
    It disambiguates the space-joined lists, and re-attaches the keyed-site paths
    the report cuts at 110 characters; it mints no claim of its own.

    **A keyed site counts as naming its keys.** `$.users {2,648 keys}` tells a
    reader those keys are values and how many there are, so their absence from
    any record shape is not a miss. It says nothing about their type, so they land
    in `named, untyped` and not in `typed right`.

    **The `could not call N small single-copy objects` list is deliberately NOT
    read as a claim.** It names a container and describes nothing inside it, which
    is `VERDICT.md` item 21 — the fold skips anything appearing once. Crediting
    those paths would hide the defect this instrument should be able to see.
    """
    claims, shown, section, at, listing = {}, set(), None, None, None
    # `same shape as $.other` is a CLAIM, and reading it is not minting one.
    # Defect 25's repair prints it in place of a field list that would have been
    # byte-identical, so the names are still stated — once, at the path the
    # reference points to. **An instrument that scored it as silence would report
    # `23-cratesio-summary` at 66.9% unnamed for a description that lost
    # nothing**, and the whole point of parsing the printed text is to score what
    # a reader is handed. A reader is handed the reference.
    #
    # The reference always points BACKWARDS — the first site to carry a shape
    # defines it — so one forward pass resolves every one of them.
    minted = {}

    def field_list(rest, counted):
        rest = " ".join(COUNTED.findall(rest)) if counted else rest
        for name in _names(rest, fields_at.get(at, ())):
            claims.setdefault(f"{at}.{name}", None)
            minted.setdefault(at, []).append(name)

    for line in text.splitlines():
        s = line.strip()
        if not s:
            continue
        # Matched by PREFIX since 2026-08-15, when `ONE ROW COULD BE` gained
        # `— give any of these to rows()`. Exact membership would have stopped
        # recognising the section and scored its names as unnamed, which reads
        # as the probe getting worse rather than as the instrument breaking.
        if (hit := next((k for k in SECTIONS if s.startswith(k)), None)):
            section, at = hit, None
            SEEN.add(hit)
            continue
        if section == "ALIGNED BY POSITION, NOT BY NESTING":
            # `08-open-meteo` has an EMPTY `RECORD SHAPES` block and names five
            # of its nineteen fields only here. Scoring the report without this
            # section would have credited the probe with naming nothing at all on
            # that document, which is a claim about the instrument and not about
            # the probe.
            m = ALIGNED_ROW.match(line)
            if m:
                claims.setdefault(m.group(1), None)
            continue
        if section == "KEYS THAT ARE DATA":
            m = KEYED_ROW.match(line)
            if m:
                site = m.group(1)
                # Cut at 110 characters by the report, so match it back to the
                # real paths rather than scoring a truncation as a miss.
                hit = ([site] if site in fields_at else
                       [p for p in fields_at if p.startswith(site)])
                for p in hit:
                    claims.setdefault(f"{p}.<key>", None)
            continue
        if section == "RECORD SHAPES, FOLDED":
            m = CONT_ROW.match(line)
            if m and listing and at:
                field_list(m.group(1), listing == "sometimes")
                continue
            listing = None
            m = SHAPE_HDR.match(line)
            if m:
                at = m.group(1)
                claims.setdefault(at, None)
                shown.add(at)
                continue
            m = SPLIT_ROW.match(line)
            if m and at:
                claims.setdefault(f"{at}.{m.group(1)}", None)
                continue
            if at and s.startswith("same shape as "):
                ref = s[len("same shape as "):]
                for name in minted.get(ref, ()):
                    claims.setdefault(f"{at}.{name}", None)
                    minted.setdefault(at, []).append(name)
                continue
            if at and (s.startswith("always ") or s.startswith("sometimes ")):
                listing = "sometimes" if s.startswith("sometimes") else "always"
                _, _, rest = s.partition(" ")
                field_list(rest, listing == "sometimes")
                continue
        if section == "FIELDS THAT CHANGE TYPE" and "└─" not in line:
            m = POLY_ROW.match(line)
            if m:
                # A typed claim OVERRIDES an untyped one: the field was named in
                # a record shape without a type and named here with one.
                claims[m.group(1)] = {t.rsplit(" x", 1)[0]
                                      for t in m.group(2).split(", ")}
    return claims, shown


# ── attributing the misses ───────────────────────────────────────────────────
#
# `29.8% unnamed` is a number a reader can do nothing with. Defect 20 claims the
# cause is the eight-field `sometimes` cap, and that claim was made from ONE file.
# These are the three ways a field can fail to be named, they are separable from
# the report itself, and they want different repairs — so a number that lumps
# them together would send a repair at the wrong one.

CAUSES = ("sometimes cap", "shape cap", "single-copy", "other")


def cause(container, shown, copies):
    """Why is a field under this container not in the description?

    **`the sometimes cap`** — its container IS a printed record shape, so the
    shape was described and the field was truncated out of it. Defect 20, and the
    truncation falls on `sometimes` and never on `always`, so what it drops is
    exactly the ragged fields.

    **`the shape cap`** — the container has two or more copies and is a record
    shape that `SHOW = 40` dropped. Defect 8's other edge: the report says how
    many shapes it dropped, and this says what that cost.

    **`single-copy`** — the container appears ONCE, so the fold skipped it
    entirely. `VERDICT.md` item 21, open since file 06, and the reason it cannot
    simply be fixed by printing single-copy objects is that `01-npm-registry` has
    seventeen of them.
    """
    if container in shown:
        return "sometimes cap"
    if copies >= 2:
        return "shape cap"
    return "single-copy" if copies == 1 else "other"


# polars is the second tool because its failure is already on the record and
# this instrument should rediscover it without being told: on 03-natural-earth
# it promotes all 122 Polygons to the MultiPolygon's nesting depth so that one
# type covers both. That is a wrong assertion, not a silence, and nothing in
# VERDICT.md currently distinguishes those.

def polars_claims(path):
    """A polars inferred schema, as claims. Every path it names, it types."""
    import polars as pl

    def dtype(t):
        """The probe's own type vocabulary for a polars dtype, and the element."""
        n = 0
        while isinstance(t, (pl.List, pl.Array)):
            n, t = n + 1, t.inner
        if n:
            inner = ("object" if isinstance(t, pl.Struct) else
                     "array" if isinstance(t, (pl.List, pl.Array)) else
                     "null" if t == pl.Null else
                     "boolean" if t == pl.Boolean else
                     "text" if t == pl.String else "number")
            return f"array[{n}] {inner}", t
        if isinstance(t, pl.Struct):
            return "object", t
        return ("null" if t == pl.Null else "boolean" if t == pl.Boolean else
                "text" if t == pl.String else "number"), t

    claims = {}
    size = [0]

    def walk(t, at):
        name, inner = dtype(t)
        claims[at] = {name}
        if isinstance(inner, pl.Struct):
            # `array[3] object` collapses three levels of list into one token;
            # re-expand them so the struct's fields sit where the ground truth
            # walk puts them.
            m = re.match(r"array\[(\d+)\]", name)
            under = at + "[]" * int(m.group(1)) if m else at
            for f in inner.fields:
                walk(f.dtype, f"{under}.{f.name}")

    df = pl.read_json(path)
    with open(path, "rb") as fh:
        top = "$[]" if json.load(fh).__class__ is list else "$"
    for f in df.schema.items():
        walk(f[1], f"{top}.{f[0]}")
    # polars' OWN printed schema, not a reconstruction of it, so the size column
    # compares two things a person would actually be handed.
    size[0] = len(str(df.schema))
    return claims, size[0]


# pandas is the third tool because `VERDICT.md` predicts its answer here and the
# prediction is unusually specific: on `07-graphql-introspection` json_normalize
# "describes a 143 KB document in 157 characters that say nothing", and that
# document *"is not the O(data) failure; it is the opposite one, and arguably
# worse, because a small wrong answer reads as a small right answer."* This is
# the instrument's chance to put a number on "arguably worse".

def pandas_claims(path):
    """`pandas.json_normalize`'s flattened columns, as claims.

    **The `object` dtype is read as NAMED, UNTYPED and not as an assertion.**
    It covers `str`, `list` and `dict` alike, so calling it a type claim would
    manufacture wrong answers pandas never gave — the same charity `satisfies()`
    extends to nullability. Only `int64`, `float64` and `bool` commit to
    anything, and only those are scored as commitments.

    Size is `len(str(list(df.columns)))`, which is the measure
    `corpus/07-graphql-introspection/python/try-pandas.py` already used, so the
    number here and the 157 characters in `VERDICT.md` are the same statistic.
    """
    import pandas as pd

    with open(path, "rb") as fh:
        doc = json.load(fh)
    top = "$[]" if isinstance(doc, list) else "$"
    df = pd.json_normalize(doc)
    commits = {"int64": "number", "float64": "number", "bool": "boolean"}
    claims = {}
    for col, dt in df.dtypes.items():
        t = commits.get(str(dt))
        claims[f"{top}.{col}"] = {t} if t else None
    return claims, len(str(list(df.columns)))


# ijson is the fourth tool, and it inverts pandas. Its description is the
# corpus's largest — 172% of `09-stripe-openapi`, bigger than the document — and
# it is the STREAMING parser, the one tool that never builds the document and
# used 81 MB where polars used 694. `VERDICT.md` records that paradox already:
# **the tool that wins the scale axis loses the description axis hardest.** What
# it has never had is the other half — whether all those characters cover
# anything.

IJSON_EV = {"string": "text", "boolean": "boolean", "null": "null",
            "number": "number", "integer": "number", "double": "number",
            "start_map": "object", "start_array": "array"}


def ijson_claims(path):
    """ijson's distinct prefixes, as claims — and it TYPES them, unlike pandas.

    A prefix writes an array element as the literal segment `item`, so
    `features.item.properties` is `$.features[].properties`.

    **A segment-wise rewrite is not enough, and `05-fhir-bundle` proves it: FHIR
    has a real field called `item`.** Rewriting every `item` segment scored that
    file at 38.1% unnamed, which would have read as a finding about ijson and was
    a bug in this adapter. A substring replace is worse still — `items` is a real
    Stripe field and `"$.a.items".replace(".item", "[]")` gives `$.a[]s`.

    So the disambiguation comes from the EVENT STREAM rather than the string: a
    segment is an array element only when the prefix above it saw `start_array`,
    which ijson always emits before the elements arrive.

    > **The ambiguity is real for a READER even though it is resolvable here.**
    > ijson's public interface is that dotted prefix, and a person handed the
    > listing cannot tell FHIR's `item` field from an array element. That is the
    > same defect `corpus/01-npm-registry/python/try-ijson.py` already records
    > about npm's version-number keys, arriving through a second door.

    Size is `len(str(sorted(prefixes)))`, the expression
    `corpus/09-stripe-openapi/python/try-ijson.py` uses. **It is not identical to
    that file's number** — 174% against 172% on Stripe — because this counts
    container prefixes too, which it must, since it claims a type for them.
    """
    import ijson

    claims, arrays = {}, set()
    with open(path, "rb") as fh:
        for prefix, event, _value in ijson.parse(fh):
            if event == "start_array":
                arrays.add(prefix)
            t = IJSON_EV.get(event)
            if t is None:  # map_key, end_map, end_array carry no type
                continue
            out, acc = [], ""
            for s in (prefix.split(".") if prefix else []):
                out.append("[]" if s == "item" and acc in arrays else s)
                acc = f"{acc}.{s}" if acc else s
            p = ".".join(["$"] + out).replace(".[]", "[]")
            claims.setdefault(p, set()).add(t)
    return claims, len(str(sorted(claims)))


# `pydash` is DELIBERATELY ABSENT, and the absence is the finding rather than a
# gap. Its answer to "what is in here" is `leaf_names()` — a set of bare KEY
# NAMES, 3,126 of them on npm — and a name is not a claim about a path. Scoring
# it here would mean matching a name against any path ending in it, which would
# hand it near-total coverage for an answer that **locates nothing**. That is
# precisely the proxy-instead-of-the-property mistake this repository has made
# five times. The honest statement is the one this comment makes: pydash names
# 3,126 things and says where none of them are, so it has no coverage to measure.

ADAPTERS = {"polars": polars_claims, "pandas": pandas_claims,
            "ijson": ijson_claims}


# ── scoring ──────────────────────────────────────────────────────────────────

BUCKETS = ("typed right", "TYPED WRONG", "named, untyped", "unnamed")


def satisfies(types, t):
    """Does an asserted type set admit an observed value? Two normalisations,
    and **this repository already made both of them** — applying a third
    definition here would be the sixth time two instruments in one project
    disagreed about one field.

    **A null is not a type.** `README.md` splits ragged-by-null from polymorphic
    because they are orthogonal, `axes.py` carries the rule, and `probe.py`
    applies it — `VERDICT.md` defect 11 is precisely this mistake, made once
    already. A describer saying `text` where the document holds `null` is silent
    about nullability, not wrong about the type, and every type system in the
    comparison makes its columns nullable by construction.

    **An empty array says nothing about its nesting.** `probe.varies()`: *"`array`
    beside `array[1]` is one shape and not two"*. Only the BARE `array` is
    bridged — `array[3] number` against `array[4] number` stays a contradiction,
    because that is `03-natural-earth`'s real polymorphism and the whole reason
    `shape()` learned depth.
    """
    if t == "null" or t in types:
        return True
    if t == "array":
        return any(x.startswith("array[") for x in types)
    return t.startswith("array[") and "array" in types


def score(counts, claims, key):
    """Put every occurrence in exactly one bucket. `key` picks concrete/folded."""
    got = Counter()
    misses, wrong = Counter(), Counter()
    for (concrete, folded, t), n in counts.items():
        p = folded if key == "folded" else concrete
        if p not in claims:
            got["unnamed"] += n
            misses[p] += n
        elif claims[p] is None:
            got["named, untyped"] += n
        elif satisfies(claims[p], t):
            got["typed right"] += n
        else:
            got["TYPED WRONG"] += n
            wrong[(p, t)] += n
    return got, misses, wrong


# ── where the printed report comes from ──────────────────────────────────────
#
# **Measured 2026-08-15, and it is the whole reason this instrument stopped
# finishing.** `uv run design/probe.py corpus/29-mdn-browser-compat/source.json`
# takes **75.4 s** of that document's 120 s. Interpreter startup is **0.03 s**,
# so the cost is the probe's own computation in Python and not the subprocess —
# calling `probe.main()` in-process would have saved nothing.
#
# `fathom probe` prints the same bytes. That is not an assumption: `test/parity.py`
# checks the rendered page byte for byte over 79 documents and is run every
# session, so a divergence fails loudly there before it could quietly change a
# number here.
#
# **The engine is NAMED in the output.** An instrument that silently swapped the
# oracle for the port would be measuring something other than what its header
# says, which is the mistake this file's own docstring is about.
ENGINE = "binary"          # 'binary' | 'oracle', set by main()
BIN = os.path.join(ROOT, "target", "release", "fathom")


def engine_in_use():
    """'binary' only if it was asked for AND exists; otherwise the oracle."""
    return "binary" if ENGINE == "binary" and os.path.isfile(BIN) else "oracle"


def probe_report(path):
    """The probe's printed page, from whichever engine `main()` selected."""
    if engine_in_use() == "binary":
        return subprocess.run([BIN, "probe", path],
                              capture_output=True, text=True, cwd=ROOT).stdout
    return subprocess.run(["uv", "run", os.path.join(HERE, "probe.py"), path],
                          capture_output=True, text=True, cwd=ROOT).stdout


def describe(path, tool="probe", show=6):
    h, doc = probe.health(path)
    if doc is None:
        print(f"  {os.path.relpath(path, ROOT):<44} unreadable: {h.get('error')}")
        return None

    if tool == "probe":
        big = fold_sites(doc)
        canon = recursion_fold(doc, big)
        counts = Counter()
        for (c, f, t), n in truth(doc, big).items():
            hp, _, name = f.rpartition(".")
            counts[(c, f"{canon.get(hp, hp)}.{name}", t)] += n
        fields_at = {}
        for (_c, folded, _t) in counts:
            at, _, name = folded.rpartition(".")
            fields_at.setdefault(at, set()).add(name)
        text = probe_report(path)
        claims, shown = probe_claims(text, fields_at)
        size = len(text)
        got, misses, wrong = score(counts, claims, "folded")
        # How many copies the fold saw of each container, so a miss can be
        # attributed rather than merely counted.
        i0, a0, t0 = probe._walk(doc, big)
        merged = probe.fold_recursion(i0, a0, t0)[0]
        why = Counter()
        for p, n in misses.items():
            container = p.rpartition(".")[0]
            why[cause(container, shown, len(merged.get(container, ())))] += n
    else:
        counts = truth(doc)
        try:
            claims, size = ADAPTERS[tool](path)
        except Exception as e:  # a refusal is data; see CLAUDE.md on "cannot"
            print(f"  {os.path.relpath(path, ROOT):<44} "
                  f"{tool} declined: {str(e).splitlines()[0][:60]}")
            return None
        got, misses, wrong = score(counts, claims, "concrete")
        why = Counter()

    total = sum(got.values())
    pairs = len({(f if tool == "probe" else c, t) for c, f, t in counts})
    row = {"file": os.path.basename(os.path.dirname(path)), "total": total,
           "pairs": pairs, "claims": len(claims), "chars": size,
           "bytes": h["bytes"], **{b: got[b] for b in BUCKETS}}
    row["misses"], row["wrong"], row["why"] = misses, wrong, why
    return row


def table(rows, of=None):
    """Size beside coverage, which is the whole point — `VERDICT.md` measures
    the first and had no instrument for the second, so a describer could be small
    because it folded or small because it discarded and the table could not say
    which."""
    print(f"\n  {'':<22} {'fields':>9} {'descr':>7} {'typed':>7} {'TYPED':>7} "
          f"{'named,':>7} {'':>8}")
    print(f"  {'':<22} {'seen':>9} {'/file':>7} {'right':>7} {'WRONG':>7} "
          f"{'untyped':>7} {'unnamed':>8}")
    for r in rows:
        print(f"  {r['file']:<22} {r['total']:>9,} "
              f"{100 * r['chars'] / max(r['bytes'], 1):>6.1f}% "
              + " ".join(f"{100 * r[b] / max(r['total'], 1):>6.1f}%"
                         for b in BUCKETS))
    tot = sum(r["total"] for r in rows)
    # `ALL 26 FILES` was printed while three entries were being skipped in
    # silence. The denominator goes in the label so the total cannot read as
    # complete when it is not.
    label = (f"ALL {len(rows)} FILES" if of in (None, len(rows))
             else f"{len(rows)} OF {of} FILES")
    print(f"  {label:<22} {tot:>9,} "
          f"{100 * sum(r['chars'] for r in rows) / max(sum(r['bytes'] for r in rows), 1):>6.1f}% "
          + " ".join(f"{100 * sum(r[b] for r in rows) / max(tot, 1):>6.1f}%"
                     for b in BUCKETS))


# A corpus entry's document, in the order the entry itself prefers. **Three of
# the 29 have no `source.json`** — `04-gharchive` and `26-gharchive-scale` ship
# gzip, `12-agent-trace` ships NDJSON — and globbing for `source.json` alone
# dropped all three in silence while `table()` printed `ALL 26 FILES`, which
# reads as all files. `probe.health()` handles both formats, so two of the three
# simply run; the third is a real bound and is NAMED.
SOURCES = ("source.json", "source.json.gz", "source.jsonl")

# `26-gharchive-scale` is 117.6 MB of gzip that unpacks to 869.8 MB. The probe
# samples it to 20,000 records, so the parse is bounded — but the READ is not,
# and `FINDINGS.md` 2026-08-15 measured that read at 3.4 s for the binary alone.
# Whether it is affordable is measured rather than assumed; see `main()`.
BIG_MB = 100


def corpus_documents():
    """Every entry's document, and the ones deliberately not run, with reasons."""
    d = os.path.join(ROOT, "corpus")
    paths, skipped = [], []
    for e in sorted(os.listdir(d)):
        if not os.path.isdir(os.path.join(d, e)):
            continue
        found = next((os.path.join(d, e, s) for s in SOURCES
                      if os.path.isfile(os.path.join(d, e, s))), None)
        if found is None:
            skipped.append((e, "no source document in the entry"))
            continue
        mb = os.path.getsize(found) / 2**20
        if mb > BIG_MB:
            skipped.append((e, f"{mb:,.0f} MB on disk — over the {BIG_MB} MB cap"))
            continue
        paths.append(found)
    return paths, skipped


def main(argv):
    global ENGINE
    # The oracle is slower by two orders of magnitude and is kept reachable, so
    # a reader who distrusts the port can spend the ten minutes deliberately.
    # Parsed BEFORE `--tool` so that either order works.
    if "--oracle" in argv:
        ENGINE, argv = "oracle", [a for a in argv if a != "--oracle"]
    tool = "probe"
    if argv[:1] == ["--tool"]:
        tool, argv = argv[1], argv[2:]
    skipped = []
    whole_corpus = not argv
    if argv:
        paths = argv
    else:
        paths, skipped = corpus_documents()

    said = ("design/probe.py, the oracle" if engine_in_use() == "oracle"
            else "target/release/fathom, byte-identical to the oracle per test/parity.py")
    print(f"\n  coverage of {tool}'s description, by field occurrence")
    if tool == "probe":
        print(f"  claims read from {said}")
    print()
    rows = [r for r in (describe(p, tool) for p in paths) if r]
    if not rows:
        return 1
    table(rows, of=len(paths) + len(skipped))

    # **Named, not dropped.** `test/candidates.py` was repaired for exactly this
    # on 2026-08-14 — a bounded run that reads as a complete one — and this file
    # had the same defect at the same time.
    for name, why in skipped:
        print(f"    not run: {name} — {why}")

    # **Only over the WHOLE corpus.** `FIELDS THAT CHANGE TYPE` and
    # `ALIGNED BY POSITION` are absent from most single documents and that is
    # the document, not the anchor. Absent from all 29 is the anchor.
    if tool == "probe" and whole_corpus:
        missed = [s for s in SECTIONS if s not in SEEN]
        if missed:
            print(f"\n    ANCHOR BROKEN: never matched on any of {len(rows)} "
                  f"documents — {', '.join(missed)}")
            print("    A section absent from every document is this file's "
                  "constant going stale, not the probe's output changing.")
            return 1

    if any(r["why"] for r in rows):
        # Attribution, because "29.8% unnamed" is a number nobody can act on and
        # the three causes want three different repairs.
        print("\n  WHY THE UNNAMED ARE UNNAMED\n")
        tot = sum(r["total"] for r in rows)
        print(f"    {'':<22} " + " ".join(f"{c:>14}" for c in CAUSES))
        for r in sorted(rows, key=lambda r: -r["unnamed"])[:8]:
            if not r["why"]:
                continue
            print(f"    {r['file']:<22} "
                  + " ".join(f"{100 * r['why'][c] / max(r['total'], 1):>13.1f}%"
                             for c in CAUSES))
        n_all = len(paths) + len(skipped)
        lbl = (f"ALL {len(rows)} FILES" if n_all == len(rows)
               else f"{len(rows)} OF {n_all} FILES")
        print(f"    {lbl:<22} "
              + " ".join(f"{100 * sum(r['why'][c] for r in rows) / max(tot, 1):>13.1f}%"
                         for c in CAUSES))

    print("\n  WHERE THE MISSES ARE, worst first\n")
    for r in sorted(rows, key=lambda r: -(r["TYPED WRONG"] + r["unnamed"]))[:6]:
        if not (r["misses"] or r["wrong"]):
            continue
        print(f"    {r['file']}")
        for (p, t), n in r["wrong"].most_common(3):
            print(f"      WRONG   {p[:74]:<76} {t} x{n:,}")
        for p, n in r["misses"].most_common(3):
            print(f"      unnamed {p[:74]:<76} x{n:,}")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
