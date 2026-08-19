"""`first_present()` — the first of these paths that is actually there.

    uv run design/first_present.py <file> <path> <spelling> [<spelling> …]
    uv run design/first_present.py corpus/16-movie-ratings/source.json \\
        '*.*' Rating rating

**Experiment, not a package**, same status as `probe.py` and `rows.py`. It is the
second of five proposed words to execute, and the first since `rows()`.

WHY IT IS ITS OWN FILE
----------------------
`design/rows.py` has been frozen at `109cf022…` for **fifteen cold runs**, files
05 through 19, and has never been repaired. That is an asset: every corpus file
since 05 is a genuine held-out run for it. **Adding a word is not a repair**, so
this lives beside it and `rows.py` is imported unmodified — its hash does not
move and the streak survives.

**This does NOT close open defect 3.** That defect is that `rows()` cannot ask
for the field rather than the spelling, and `rows()`'s `take=` is a name filter
(`if take is None or k in take`) which cannot express a priority order. Wiring
`first_present` into `rows()` is a separate change with its own evidence, and
doing it in the same step would have meant unfreezing `rows.py` to ship an
unproven word.

WHAT COUNTS AS PRESENT
----------------------
`README.md` names the word so both halves carry something people get wrong:

> *`first` says the arguments are a priority order rather than a set, and
> `present` says the only value skipped is a missing one, so a zero comes back.*

So the test is **presence, not truthiness**. A `0`, an empty string and an empty
list are all values and are returned. Only an absent path and an explicit `null`
are skipped, which is exactly `probe.filled()`'s definition and keeps the see
half and the extract half agreeing about what "empty" means — a thing this
project has already had to repair three times.

**It does not skip sentinels.** `16-movie-ratings` writes missingness as the
string `"unknown"`, and `first_present` returns it. The policy is *report, never
repair*: the probe reports the sentinel, and silently stepping over it here would
destroy the evidence that something upstream is broken.
"""
import json
import sys

from rows import match, parse

MISSING = object()


def first_present(node, *paths, default=None):
    """The value at the first of `paths` that is there. `default` if none are.

    Paths are `rows.py`'s notation, unchanged — one notation for the project, so
    a person who learned `rows("versions.*")` already knows how to spell these.
    """
    for p in paths:
        for _keys, val in match(node, parse(p)):
            if val is not None:
                return val
    return default


def collapse(records, *paths, default=None):
    """`first_present` over many records. Returns the values and a tally.

    The tally is the point on a corpus file: it says which spelling actually
    supplied each row, which is the number that shows the word did something.
    """
    vals, who = [], {}
    for r in records:
        hit = default
        src = None
        for p in paths:
            for _keys, val in match(r, parse(p)):
                if val is not None:
                    hit, src = val, p
                    break
            if src:
                break
        vals.append(hit)
        who[src] = who.get(src, 0) + 1
    return vals, who


if __name__ == "__main__":
    src, path, spellings = sys.argv[1], sys.argv[2], sys.argv[3:]
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

    records = [v for _k, v in match(doc, parse(path)) if isinstance(v, dict)]
    vals, who = collapse(records, *spellings)
    got = sum(1 for v in vals if v is not None)

    print(f"\n  first_present({', '.join(spellings)})")
    print(f"  over {len(records):,} records reached by {path!r}\n")
    for p in spellings:
        n = who.get(p, 0)
        print(f"    {p:<28} supplied {n:>6,}")
    if who.get(None):
        print(f"    {'(none of them)':<28} {who[None]:>15,}")
    print(f"\n  {got:,} of {len(records):,} rows filled "
          f"({got / len(records):.0%}) from {len(spellings)} spellings")
    print(f"  first three: {vals[:3]}\n")
