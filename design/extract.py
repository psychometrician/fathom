"""The extract half, scored across the whole corpus.

    uv run design/extract.py          # exits non-zero if a row count is wrong

**The asymmetry this closes.** `design/probe.py` has nineteen cold runs and a
defect list to show for them. The extract half had four words and a handful of
demonstrations, and `VERDICT.md` names that as the last of the three conditions
that would earn Phase 2:

> the five proposed words **made to run** on all corpus files, since surviving
> the deletion test on paper is the cheap half.

This runs `rows()` on every corpus entry against **the answer that entry's
`NOTES.md` recorded for question 3**, which is the same discipline
`unnest_auto` was scored under — 7 of 11 — rather than a fresh judgement made
while looking at the output.

**It also measures the two open `rows.py` defects across the whole corpus** for
the first time. Both were found on single files:

  list-columns   god's spec refuses nested data as a value, so any column
                 holding a list or a dict is an extract that cannot flow onward.
                 Found on 06 and 07, seen since on 11 and 13.
  the transpose  `08-open-meteo` stores a table column-wise and `rows()` has no
                 operator for it. Recorded as EXPECTED-FAIL rather than silently
                 skipped, because a known limit that stops being counted stops
                 being a limit.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rows import rows

ROOT = Path(__file__).parent.parent

# (entry, path, rows the entry's NOTES.md recorded for question 3, note)
CASES = [
    ("01-npm-registry", "versions.*", 288, ""),
    ("02-hn-thread", "children**", 335, "recursive, any depth"),
    ("03-natural-earth", "features.*", 241, ""),
    ("04-gharchive", "*", 20000, "sampled at MAX_RECORDS"),
    ("05-fhir-bundle", "entry.*.resource", 564, ""),
    ("06-espn-qbr", "athletes.*", 28, "the tutorial's own answer"),
    ("07-graphql-introspection", "data.__schema.types.*", 108, ""),
    ("08-open-meteo", "hourly.*", 336, "EXPECTED FAIL: needs a transpose"),
    ("09-stripe-openapi", "components.schemas.*", 1440, ""),
    ("10-wikidata", "entities.Q30.claims.*", 469, ""),
    ("11-jupyter-notebook", "cells.*", 272, ""),
    ("12-agent-trace", "*", 1953, ""),
    ("13-package-lock", "packages.*", 1657, ""),
    ("14-nyc-311", "*", 20000, ""),
    ("15-github-issues", "*", 100, ""),
    ("16-movie-ratings", "*.*", 38, "two spellings, see first_present"),
    ("17-openlibrary", "docs.*", 200, ""),
    ("18-openfda-events", "results.*", 100, ""),
    ("19-chicago-salaries", "*", 5000, ""),
]


def load(entry):
    d = ROOT / "corpus" / entry
    for name in ("source.json", "source.jsonl", "source.json.gz"):
        p = d / name
        if not p.exists():
            continue
        raw = p.read_bytes()
        if raw[:2] == b"\x1f\x8b":
            import gzip
            raw = gzip.decompress(raw)
        txt = raw.decode("utf-8", errors="replace")
        try:
            return json.loads(txt)
        except json.JSONDecodeError:
            lines = [l for l in txt.split("\n") if l.strip()]
            return [json.loads(l) for l in lines[:20000]]
    return None


def main():
    print(f"\n  rows() against the answer each NOTES.md recorded, "
          f"{len(CASES)} corpus files\n")
    print(f"    {'entry':<26}{'path':<24}{'got':>7} {'want':>7}   "
          f"{'list-cols':>9}")
    wrong, listcols, expected_fail = 0, 0, 0
    for entry, path, want, note in CASES:
        doc = load(entry)
        if doc is None:
            print(f"    {entry:<26}{path:<24}{'':>7} {'':>7}   no source")
            continue
        cols, out = rows(doc, path)
        got = len(out)
        # god's spec refuses nested data as a value: any column holding a list
        # or a dict is an extract that cannot flow onward into god.
        nested = sorted({k for r in out for k, v in r.items()
                         if isinstance(v, (list, dict))})
        ok = got == want
        if not ok and note.startswith("EXPECTED FAIL"):
            expected_fail += 1
            mark = "expected fail"
        elif ok:
            mark = "ok"
        else:
            wrong += 1
            mark = "WRONG"
        listcols += bool(nested)
        nest = f"{len(nested)}" if nested else "-"
        print(f"    {entry:<26}{path:<24}{got:>7,} {want:>7,}   {nest:>9}   {mark}")

    n = len(CASES)
    print(f"\n  {n - wrong - expected_fail} of {n} row counts correct, "
          f"{expected_fail} expected fail, {wrong} wrong")
    print(f"  {listcols} of {n} produce at least one list-column, "
          f"which god's spec refuses\n")
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
