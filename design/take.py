"""`take()` — build only the columns you asked for.

    uv run design/take.py <file> <path> <field> [<field> …]
    uv run design/take.py corpus/01-npm-registry/source.json 'versions.*' \\
        version author.name dist.tarball

**Experiment, not a package**, same status as `probe.py`, `rows.py` and
`first_present.py`. Third of five proposed words to execute.

WHY THIS WORD IS THE ONE THAT NEARLY FAILED
-------------------------------------------
`design/vocabulary.md` runs the deletion test and `take` is the only word that
does not clearly survive it:

> If `rows()` returns every column, then selecting three of them is god's `pick`,
> and `take` is a word fathom does not need — the seam is a data frame and
> selection lives downstream.

**What saves it is cost, and `VERDICT.md` records that the claim is untested.**
This file exists to test it. The argument is that
`rows("versions.*")` is 288 x 140 and 60% empty, so materialising 140 columns to
keep 3 is waste — *"it is not even efficient to make every json
rectangularized"*.

`take` is also the word `tidyr::hoist` already is, which
`corpus/06-espn-qbr/r/try-tidyr.R` records as shipped prior art.

IT SELECTS BY PATH, NOT BY KEY, AND THAT IS THE DIFFERENCE FROM `rows(take=)`
-----------------------------------------------------------------------------
`rows()` already has a `take=` parameter and it is a **name filter** — `if take
is None or k in take` — so it can keep `version` and cannot reach
`author.name`. That is why this is a separate word rather than an argument, and
it is also why `first_present` cannot yet compose into `rows()`: the same filter
cannot express a priority order either. See open defect 3.
"""
import json
import sys
import time

import pandas as pd

from rows import match, parse


def take(records, *paths):
    """One row per record, one column per path. Nothing else is built.

    Columns are named by the path's last segment, disambiguated on collision the
    way `rows()` disambiguates its key columns.
    """
    names, seen = [], {}
    for p in paths:
        n = parse(p)[-1]
        seen[n] = seen.get(n, 0) + 1
        names.append(n if seen[n] == 1 else f"{n}{seen[n]}")

    out = []
    for r in records:
        row = {}
        for name, p in zip(names, paths):
            hit = next((v for _k, v in match(r, parse(p))), None)
            row[name] = hit
        out.append(row)
    return names, out


def _widen(records):
    """What you get without `take`, at BOTH the readings people actually use.

    **These are two different numbers and `design/vocabulary.md` quoted one
    without saying which**, which is why this returns both. Measured on
    `01-npm-registry`'s 288 versions:

        every top-level key         288 x  40,  43% empty
        pandas.json_normalize       288 x 140,  60% empty

    Both are honest. The second is the one vocabulary.md's cost argument cites,
    and it is the right one to cite, because **flattening with
    `json_normalize` is the move the argument is about** — it is what somebody
    reaching for "just make it a table" actually types.
    """
    shallow = []
    for r in records:
        for k in r:
            if k not in shallow:
                shallow.append(k)
    flat = pd.json_normalize(records)
    return (shallow, [{k: r.get(k) for k in shallow} for r in records],
            list(flat.columns), flat)


if __name__ == "__main__":
    src, path, fields = sys.argv[1], sys.argv[2], sys.argv[3:]
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

    sh_cols, sh, fl_cols, fl = _widen(records)
    sh_holes = sum(1 for r in sh for c in sh_cols if r[c] is None)
    fl_holes = fl.isna().sum().sum()

    t0 = time.perf_counter()
    cols, narrow = take(records, *fields)
    t_take = time.perf_counter() - t0

    n = len(records)
    print(f"\n  take({', '.join(fields)})")
    print(f"  over {n:,} records reached by {path!r}\n")
    print(f"    every top-level key    {n:>7,} x {len(sh_cols):>4} cols   "
          f"{sh_holes / (n * len(sh_cols)):>4.0%} empty   {n * len(sh_cols):>9,} cells")
    print(f"    json_normalize         {n:>7,} x {len(fl_cols):>4} cols   "
          f"{fl_holes / (n * len(fl_cols)):>4.0%} empty   {n * len(fl_cols):>9,} cells")
    print(f"    with take              {n:>7,} x {len(cols):>4} cols   "
          f"{'':>4}         {n * len(cols):>9,} cells   {t_take * 1000:.1f} ms")
    saved = 1 - (n * len(cols)) / (n * len(fl_cols))
    print(f"\n  {saved:.1%} of json_normalize's cells never built. columns: {cols}")
    print(f"  first row: {narrow[0]}\n")
