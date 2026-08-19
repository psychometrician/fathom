"""`where()` — every path whose value matches.

    uv run design/where.py <file> <predicate>
    uv run design/where.py corpus/01-npm-registry/source.json url

**Experiment, not a package**, same status as the other four. Fourth of five
proposed words to execute, and the one that answers `QUESTIONS.md` question 11:

> **Find every path whose value matches something**, such as an email or a URL.

`design/vocabulary.md`'s deletion test says removing it makes question 11
unanswerable on every corpus file, which is the cleanest survival of the five.

WHAT IT RETURNS, AND WHY NOT A LIST OF PATHS
--------------------------------------------
The naive answer is every matching path, and on `01-npm-registry` that is
thousands of them — **the O(data) failure this project exists to name, committed
by fathom's own word.** So `where()` folds: it reports the SHAPE of the paths
that matched, with a count, exactly as the probe folds record shapes.

    versions.<key>.dist.tarball        288 matched

not

    versions.1.0.0.dist.tarball
    versions.1.0.1.dist.tarball        … 286 more

**A word that answers a question by printing the data has not answered it.**
"""
import json
import re
import sys

from probe import fold_set

EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
URL = re.compile(r"^(https?|git\+https?|ftp)://", re.I)
ISO = re.compile(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2})?")

PREDICATES = {
    "url": lambda v: isinstance(v, str) and bool(URL.match(v)),
    "email": lambda v: isinstance(v, str) and bool(EMAIL.match(v)),
    "date": lambda v: isinstance(v, str) and bool(ISO.match(v)),
    "empty": lambda v: v is None or v == "" or v == [] or v == {},
}


def where(doc, predicate):
    """`{folded path: count}` for every path whose value matches.

    The fold replaces a container's key with `<key>` when its siblings are many,
    which is `probe.py`'s keys-as-data idea reused: a path that differs only by
    which version or which movie it named is one path, not 288.

    A CALLABLE is accepted as well as a name, and that is the oracle's contract
    rather than the port's: the CLI can only be handed a string.

    **An unknown NAME has always been refused here, and until 2026-08-14 it was
    refused by accident** — `.get(predicate, predicate)` fell back to the string
    itself, which then failed at `test(value)` with `'str' object is not
    callable`. The refusal was right and unreadable, and it is stated now so
    that `test/parity.py` can assert the two halves refuse TOGETHER. The port
    did not refuse at all; see `Test::parse` in `fathom-core/src/extract.rs`.
    """
    if isinstance(predicate, str):
        if predicate not in PREDICATES:
            raise ValueError(f"no test called {predicate!r} — the tests are "
                             + ", ".join(PREDICATES))
        test = PREDICATES[predicate]
    else:
        test = predicate
    hits = {}

    big = fold_set(doc)[0]

    def walk(node, parts, ip):
        # A CONTAINER IS TESTED TOO, and until 2026-08-10 it was not. The test
        # used to be the `else` of the descent, so a dict or a list was recursed
        # into and never offered to the predicate — which made two of `empty`'s
        # four clauses, `v == []` and `v == {}`, unreachable code that reads as
        # working. `where(empty)` on `{a: [], b: {}, c: null, d: ""}` returned
        # `c` and `d` and called the document two-thirds empty.
        #
        # **Found by writing the word in R**, which is what `design/parity.py`
        # exists for: the R port had to state the predicate from scratch, and the
        # clause that could never fire in Python was the one that had to be
        # explained. Nothing recorded in `vocabulary.md` moves — `url` and
        # `email` never match a container — and `07-graphql-introspection` goes
        # from 3,007 empties to the true count.
        if test(node):
            p = ".".join(parts) or "."
            hits[p] = hits.get(p, 0) + 1
        if isinstance(node, dict):
            # WHICH KEYS ARE DATA is `probe.py`'s question and it is already
            # answered there. The first version of this used `len(node) > 5`,
            # which folded the document's own top level and produced
            # `<key>.<key>.<key>.url` — unreadable, and wrong about what is
            # data. Reusing the probe keeps one answer in one place, the way
            # `variation()` was repaired by routing it through `varies()`.
            #
            # **DEFECT 36, repaired 2026-08-18: ask the FOLD, not `classify`.**
            # This used to call `classify([node])` — ONE container, which always
            # takes the single-copy branch and so decides on `KEYED_MIN` alone.
            # That is a strictly weaker test than the one `containers()` already
            # runs, and on `29-mdn-browser-compat` it under-folds badly: the
            # 1,090 `api` interfaces hold a median of FIVE method names, so none
            # reach twenty, every method name became a literal path segment, and
            # `where url` named **11,320 paths for 35,392 values**. The report
            # folds that same site correctly and always did — `$.api.<key>` and
            # `$.api.<key>.<key>` are both in the fold set. **Two walks were
            # answering *are these keys data* two different ways.**
            #
            # **The repair adds no rule and moves no threshold.** `fold_set()`
            # is the fixed point `containers()` has always used; the two walks
            # simply stop disagreeing. The old comment here argued that handing
            # `classify` the node's VALUES as siblings would break npm — still
            # true, and not what this does. The fold set asks about a
            # container's own COPIES, pooled by folded path: a third question.
            #
            # > **The old comment also claimed this over-folded npm to
            # > `versions.<key>.<key>.url`, and that was measured FALSE on
            # > 2026-08-18.** A version object has **17 keys and four value
            # > types**, so the single-copy branch returned `undecided` and
            # > never folded it — the claim was stale, and `where url` on npm is
            # > byte-identical before and after this repair. It is recorded
            # > rather than deleted because it was believed for four days and
            # > shaped the comment above it.
            many = ip in big
            for k, v in node.items():
                walk(v, parts + ["<key>" if many else k],
                     f"{ip}.<key>" if many else f"{ip}.{k}")
        elif isinstance(node, list):
            for v in node:
                walk(v, parts + ["[]"], ip + "[]")

    walk(doc, [], "$")
    return hits


if __name__ == "__main__":
    src, pred = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "url")
    with open(src, "rb") as fh:
        raw = fh.read()
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
    txt = raw.decode("utf-8", errors="replace")
    try:
        doc = json.loads(txt)
    except json.JSONDecodeError:
        doc = [json.loads(l) for l in txt.split("\n") if l.strip()]

    hits = where(doc, pred)
    total = sum(hits.values())
    print(f"\n  where({pred})\n")
    for p, n in sorted(hits.items(), key=lambda kv: -kv[1])[:14]:
        print(f"    {p[:60]:<62} {n:>7,}")
    if len(hits) > 14:
        print(f"    … and {len(hits) - 14} more shapes")
    print(f"\n  {total:,} values matched, at {len(hits)} distinct path shapes\n")
