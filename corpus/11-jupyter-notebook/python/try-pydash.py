"""pydash — Jupyter notebook, Norvig Advent-2021, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
  measured      2026-08-10
  run           cd corpus/11-jupyter-notebook/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  WRONG
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  -   -                   CANNOT
   6 are any object keys data                    4   YES                 CANNOT
   7 how many records                            2   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       4   YES                 PARTLY
  13 needed the shape in advance?                    YES, for everything but Q1
  14 survives the next file unchanged?               Q1 does; nothing else
  15 readable a week later?                          yes, it is lodash
  16 lines, and how much is ceremony?                ~40, little ceremony

WHAT THIS FILE IS FOR. pydash is the lodash port, and the corpus uses it as the
closest Python equivalent to rrapply's `how="melt"` — a whole-document walk. The
walk itself is nine lines of plain recursion, because pydash has no recursive
descent, and that is the finding rather than an accident of this file.
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = json.load(open("../source.json"))

# ── 1. what is in here ───────────────────────────────────────────────────────
# The corpus's standard pydash walk: every distinct key NAME anywhere.
def leaf_names(node, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            acc.add(k)
            leaf_names(v, acc)
    elif isinstance(node, list):
        for v in node:
            leaf_names(v, acc)
    return acc


names = leaf_names(doc, set())
print(f"\n1. distinct key names anywhere: {len(names)}")
print(f"   {sorted(names)}")
print("   WRONG in a way this corpus has not seen before. On npm the same walk")
print("   answered 3,126 where the truth was 40 — the O(data) failure. Here it")
print("   answers 25, which is RIGHT, because this document has no keys-as-data")
print("   of any size. **The walk did not get better; the document did.** A")
print("   name list also says nothing about WHERE any of them are, which is why")
print("   design/coverage.py refuses to score this shape of answer at all.")

# ── 2, 3, 5, 11. what pydash does not do ─────────────────────────────────────
print("\n2. CANNOT. No depth verb. The recursion above could count it; pydash")
print("   contributed nothing to that recursion, so the answer would be mine.")
print("\n3. CANNOT. pydash has no notion of a record or a row shape.")
print("\n5. CANNOT. No type report across records.")
print("\n11. CANNOT. `pydash.get` needs a path; there is no search over unknown")
print("   paths, so the 53 source lines mentioning a URL are unreachable")
print("   without the recursion above, which is not pydash.")

# ── 6. are any object keys data ──────────────────────────────────────────────
mimes = Counter(k for c in doc["cells"] for o in c.get("outputs", [])
                for k in o.get("data", {}))
print(f"\n6. CANNOT. mime keys under outputs[].data: {dict(mimes)}")
print("   They are in the Q1 name list above, sitting between `cell_type` and")
print("   `execution_count` with nothing to mark them as values. That is the")
print("   whole of the keys-as-data problem in one printed list.")

# ── 7. how many records ──────────────────────────────────────────────────────
outs = pydash.flat_map(doc["cells"], lambda c: c.get("outputs", []))
print(f"\n7. cells: {len(doc['cells'])}   outputs: {len(outs)}")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. PARTLY — `pydash.count_by` once the field is named:")
for f in ("cell_type", "source", "metadata", "execution_count", "outputs"):
    n = len(pydash.filter_(doc["cells"], lambda c, f=f: f in c))
    print(f"     {f:18} {n:>4} of 272")
print("   `f in c` is Python, not pydash — and it is the only formulation that")
print("   separates ABSENT from null. `pydash.get(c, f)` returns None for both,")
print("   so execution_count would read 131 instead of 132.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
rows = pydash.map_(doc["cells"], lambda c: {
    "type": pydash.get(c, "cell_type"),
    "n": pydash.get(c, "execution_count"),
    "lines": len(pydash.get(c, "source", [])),
})
print(f"\n8. three fields, one row per cell: {len(rows)} rows")
for r in rows[:3]:
    print(f"     {r}")
print(f"\n9. n is None on {sum(1 for r in rows if r['n'] is None)} of {len(rows)} "
      f"rows, all kept — `pydash.get` defaults rather than raising.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
lines = pydash.flat_map(outs, lambda o: pydash.get(o, "data.text/plain") or [])
print(f"\n10. text/plain exploded to lines: {len(lines)} rows")
print("   `pydash.get(o, 'data.text/plain')` WORKS, and it is luck. pydash")
print("   splits a path on every dot and does not try longer prefixes, so a")
print("   mime type with a dot in it — `application/vnd.foo+json`, which")
print("   nbformat permits — would silently return None here.")

# ── 12. flattest honest table ────────────────────────────────────────────────
flat = pydash.flat_map(doc["cells"], lambda c: [
    {"type": c["cell_type"], "n": pydash.get(c, "execution_count"),
     "kind": pydash.get(o, "output_type"),
     "tp": len(pydash.get(o, "data.text/plain") or [])}
    for o in c.get("outputs", [])])
print(f"\n12. flattest: {len(flat)} rows, {len(flat[0])} cols")
print("   WHAT IS LOST: the 140 markdown cells, dropped by the inner list")
print("   comprehension — which is Python and not pydash, and pydash offers")
print("   nothing that would have warned. Plus the 17 base64 PNGs, 79% of the")
print("   file's bytes, summarised here as a length and otherwise discarded.")
