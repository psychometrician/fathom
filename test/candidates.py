"""Does every row shape the menu NAMES resolve to the table it PROMISED?

    uv run test/candidates.py         # exits non-zero on any mismatch

**This is the test the sentences run of 2026-08-11 asked for and could not
perform.** That run parsed each document's `ONE ROW COULD BE` menu and asked a
PROTOTYPE whether `rows(<label>)` reproduced the promised count. It got **147 of
197**, and the 37 misses were all one thing: the prototype re-derived the
candidate set from the name — *every container called this, anywhere* — while
the probe's rule comes from its FOLD, which knows which occurrences a candidate
covers. `an item of contributors` collected 1,596 where 7 was wanted;
`an entry of properties` collected 23 where 6,714 was wanted. **Wrong in both
directions, which is the signature of a second engine guessing.**

So `rows()` was built ON the fold instead: `price::candidates_full()` keeps what
each candidate was priced FROM, and `price::table()` rebuilds exactly that. This
harness checks the promise end to end, **through the printed page** rather than
around it — it reads the label out of the report the way a reader would, and
types it back. A label that cannot survive that round trip is defect 28's
failure mode, and parsing the menu is the only way to catch it.

Shaped like the other scorers: one line per group, non-zero exit on failure.
"""

import json
import re
from collections import Counter
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).parent
ROOT = HERE.parent
BINARY = ROOT / "target" / "release" / "fathom"

# `    {label:<34}{rows:>7,} rows` and an optional ` x {cols:>4} cols`. The
# label is taken non-greedily up to the count, which is safe even for a field
# whose name ends in a digit — `temperature_2m` — because the digits have to be
# followed by the literal " rows".
CANDIDATE = re.compile(
    r"^ {4}(?P<label>.*?)\s*(?P<rows>\d[\d,]*) rows(?: x\s*(?P<cols>\d[\d,]*) cols)?"
)


def menu(report):
    """The candidates a document names, read out of its own printed page."""
    out, inside = [], False
    for line in report.splitlines():
        # PREFIX, not equality: the header gained `— give any of these to rows()`
        # on 2026-08-15, and an exact match would have found no menu at all and
        # scored every document as having no candidates — a pass, silently.
        if line.strip().startswith("ONE ROW COULD BE"):
            inside = True
            continue
        if not inside:
            continue
        if line.startswith("      "):
            continue  # a `└─ or N tables, split on …` modifier, not a candidate
        m = CANDIDATE.match(line)
        if m:
            out.append((
                m.group("label"),
                int(m.group("rows").replace(",", "")),
                int(m.group("cols").replace(",", "")) if m.group("cols") else None,
            ))
    return out


SIZE_CAP = 200 * 2**20

#: Documents skipped for size, filled in by `documents()` and REPORTED.
#: **A silent cap reads as coverage.** `CLAUDE.md` states the rule — if a check
#: bounds what it looks at, it says what it left out — and this one did not:
#: `26-gharchive-scale` is 912 MB and was dropped without a word, so the run
#: printed "28 documents perfect" while 29 exist. That is the same repair
#: defects 33 and 34 made to the report: the count stays and the page says what
#: it left out.
SKIPPED = []


def documents():
    for entry in sorted((ROOT / "corpus").iterdir()):
        if not entry.is_dir():
            continue
        for name in ("source.json", "source.jsonl"):
            src = entry / name
            if src.exists():
                if src.stat().st_size <= SIZE_CAP:
                    yield entry.name, src
                else:
                    SKIPPED.append((entry.name, src.stat().st_size))
                break


def main():
    if not BINARY.exists():
        print(f"  no binary at {BINARY} — run `cargo build --release`")
        return 1

    total = matched = 0
    failures, unreachable, perfect, docs = [], [], [], 0
    for entry, src in documents():
        docs += 1
        report = subprocess.run(
            [str(BINARY), "probe", str(src)], capture_output=True, text=True).stdout
        listed = menu(report)
        # **The page and the JSON must agree on how many candidates there are.**
        # Without this the harness has a silent failure mode that nearly fired
        # on 2026-08-15: the menu header changed, `menu()` matched it by
        # equality, found nothing, and every document scored 0 of 0 — which is a
        # PASS. An anchor that can stop matching needs something to check it
        # against, and the binary already publishes the same list as data.
        # Measured on all 29 documents the day this was added: the two counts
        # agree everywhere, so any disagreement is the page-parse breaking.
        js = subprocess.run([str(BINARY), "structure", str(src)],
                            capture_output=True, text=True)
        if js.returncode == 0:
            n = len(json.loads(js.stdout)["candidates"])
            if n != len(listed):
                failures.append((entry, "menu parse", f"{n} in structure",
                                 f"{len(listed)} read off the page"))
        # DEFECT 29. A label the menu prints TWICE cannot select anything: the
        # first one answers for all of them. Counted apart from a mismatch,
        # because it is a known open defect in the REPORT rather than a
        # disagreement between the menu and the table, and a check that fails
        # forever on something already written down is a check people learn to
        # ignore. Any OTHER mismatch still fails the run.
        seen = Counter(label for label, _, _ in listed)
        good = 0
        for label, want_rows, want_cols in listed:
            total += 1
            done = subprocess.run(
                [str(BINARY), "rows", str(src), "--candidate", label],
                capture_output=True, text=True)
            got = None
            if done.returncode == 0:
                bits = done.stdout.strip().split(" ", 2)
                got = (int(bits[0]), int(bits[1]))
            # A candidate the report prints without a column count claims
            # nothing about columns, so nothing is checked.
            if got and got[0] == want_rows and (want_cols is None or got[1] == want_cols):
                matched += 1
                good += 1
            elif seen[label] > 1:
                unreachable.append((entry, label, seen[label], want_rows))
            else:
                failures.append((
                    entry, label,
                    f"{want_rows} x {want_cols if want_cols is not None else '-'}",
                    f"{got[0]} x {got[1]}" if got else "UNRESOLVED"))
        if listed and good == len(listed):
            perfect.append(entry)

    print("\nCANDIDATES: every row shape the menu names, resolved and rebuilt")
    print(f"  {matched} of {total} reproduce the promised shape, "
          f"across {docs} documents")
    print(f"  {len(perfect)} documents perfect")
    for name, size in SKIPPED:
        print(f"  not run: {name} at {size/2**20:,.0f} MB — over the {SIZE_CAP//2**20} MB cap")
    if unreachable:
        print(f"\n  DEFECT 29, open: {len(unreachable)} candidates cannot be "
              f"selected because the menu prints their label more than once")
        for entry, label, times, rows in unreachable:
            print(f"    {entry:<24} {label!r} x{times} — the one promising "
                  f"{rows:,} rows is not reachable")
    if failures:
        print()
        for entry, label, want, got in failures:
            print(f"  {entry:<24} {label:<38} promised {want:<12} got {got}")
        print(f"\n  {len(failures)} MISMATCHES")
        return 1
    print("\n  no mismatches" + (" beyond defect 29" if unreachable else ""))
    return 0


if __name__ == "__main__":
    sys.exit(main())
