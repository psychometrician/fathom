"""glom — Jupyter notebook, Norvig Advent-2021, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
  measured      2026-08-10
  run           cd corpus/11-jupyter-notebook/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   CANNOT
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 5   YES                 PARTLY
   5 does any field change type                  4   YES                 PARTLY
   6 are any object keys data                    -   -                   CANNOT
   7 how many records                            3   YES                 YES
   8 three named fields to a table               5   YES                 yes
   9 a field missing from some rows              5   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 PARTLY
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no — every spec is a path
  15 readable a week later?                          yes, specs read as data
  16 lines, and how much is ceremony?                ~40, almost no ceremony
"""
import json
import sys
from importlib.metadata import version

from glom import Coalesce, Flatten, PathAccessError, glom

print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = json.load(open("../source.json"))

# ── 1, 2, 3, 6. what glom does not do ────────────────────────────────────────
print("\n1. CANNOT. glom is an EXTRACTOR: every spec names a path the caller")
print("   already knows. It has no verb that describes a document, so Q1, Q2,")
print("   Q3 and Q6 are all outside it. That is a design choice rather than a")
print("   gap — but it means glom cannot start you on an unseen file.")

# ── 7. how many records ──────────────────────────────────────────────────────
# `Coalesce(..., default=[])` on EVERY step that touches `outputs`, because a
# markdown cell has no such key and glom raises rather than skipping. That is the
# right behaviour and it means the ragged case must be named in the spec.
allout = glom(doc, ("cells", [Coalesce("outputs", default=[])], Flatten()))
print(f"\n7. cells: {len(doc['cells'])}   outputs: {len(allout)}")

# ── 8. three named fields ────────────────────────────────────────────────────
spec = ("cells", [{
    "type": "cell_type",
    "n": Coalesce("execution_count", default=None),
    "lines": ("source", len),
}])
rows = glom(doc, spec)
print(f"\n8. three fields, one row per cell: {len(rows)} rows")
for r in rows[:3]:
    print(f"     {r}")

# ── 9. a field missing from some records ─────────────────────────────────────
# `Coalesce(..., default=None)` is the whole answer and it is one word. Without
# it the spec raises on the first markdown cell, which is the correct behaviour
# and the opposite of jmespath's silent None.
missing = sum(1 for r in rows if r["n"] is None)
print(f"\n9. execution_count absent-or-null on {missing} of {len(rows)} rows, "
      f"all kept.")
try:
    glom(doc, ("cells", ["execution_count"]))
    print("   expected a PathAccessError and did not get one")
except PathAccessError as e:
    print(f"   WITHOUT Coalesce it RAISES and names the key: {str(e)[:58]}…")
print("   That is the safety margin VERDICT.md credits glom with: a wrong or")
print("   absent path is an error with a name, not a None you carry onward.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. PARTLY — glom can TEST a field once you name it, not enumerate:")
for f in ("cell_type", "source", "metadata", "execution_count", "outputs"):
    have = sum(1 for c in doc["cells"]
               if glom(c, Coalesce(f, default=None)) is not None)
    print(f"     {f:18} {have:>4} of {len(doc['cells'])}")
print("   The field names came from reading the file, not from glom. And note")
print("   `execution_count` reads 131, not 132: Coalesce's default cannot tell")
print("   the 1 null from the 140 absent, so this counts NON-NULL, not present.")

# ── 5. does any field change type ────────────────────────────────────────────
kinds = {}
for c in doc["cells"]:
    kinds.setdefault(type(glom(c, Coalesce("execution_count",
                                           default=None))).__name__, 0)
print(f"\n5. PARTLY. types seen at cells[].execution_count: {sorted(kinds)}")
print("   glom has no type report; this is a Python loop with glom used as the")
print("   accessor. `NoneType` here is the 140 absences and the 1 null merged,")
print("   which is the same collapse pandas and polars make.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
lines = glom(doc, ("cells", [Coalesce("outputs", default=[])], Flatten(),
                   [Coalesce("data.text/plain", default=[])], Flatten()))
print(f"\n10. text/plain exploded to lines: {len(lines)} rows")
print("   `data.text/plain` works as a dotted spec because glom splits on the")
print("   dot and `text/plain` has none — a key with a dot in it would need")
print("   Path('data', 'text/plain'), which this document happens not to need.")

# ── 11. every path whose value matches ───────────────────────────────────────
print("\n11. CANNOT. glom has no recursive search over unknown paths. Its whole")
print("   contract is that you supply the path, so 'find every path where…' is")
print("   the one question its design excludes.")

# ── 12. flattest honest table ────────────────────────────────────────────────
flat = glom(doc, ("cells", [{
    "type": "cell_type",
    "outs": (Coalesce("outputs", default=[]), [{
        "kind": "output_type",
        "tp": Coalesce("data.text/plain", default=None),
    }]),
}]))
n = sum(len(r["outs"]) for r in flat)
print(f"\n12. flattest: {n} output rows under {len(flat)} cells, nested one")
print("   level because glom builds the shape you write and will not join.")
print("   WHAT IS LOST: nothing yet — but it is not a TABLE, it is a list of")
print("   dicts holding lists, and turning it rectangular is plain Python.")
print("   glom got the extraction exactly right and stopped short of the shape.")
