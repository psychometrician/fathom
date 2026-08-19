"""jmespath — Jupyter notebook, Norvig Advent-2021, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
  measured      2026-08-10
  run           cd corpus/11-jupyter-notebook/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   PARTLY              PARTLY
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  -   -                   CANNOT
   6 are any object keys data                    3   YES                 CANNOT
   7 how many records                            2   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              5   YES                 DANGEROUS
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       4   YES                 PARTLY
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no, and it will not say so
  15 readable a week later?                          yes, the syntax is compact
  16 lines, and how much is ceremony?                ~35, no ceremony at all
"""
import json
import sys
from importlib.metadata import version

import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))

# ── 1. what is in here ───────────────────────────────────────────────────────
print(f"\n1. root keys: {jmespath.search('keys(@)', doc)}")
print(f"   keys(cells[0]): {jmespath.search('keys(cells[0])', doc)}")
print(f"   keys(cells[1]): {jmespath.search('keys(cells[1])', doc)}")
print("   PARTLY: `keys()` works one object at a time, so the union across 272")
print("   cells has to be assembled by the caller. Cell 0 and cell 1 differ,")
print("   and only luck put a markdown and a code cell next to each other.")

# ── 2, 3, 5. what jmespath does not do ───────────────────────────────────────
print("\n2. CANNOT. No depth verb, and no recursive descent to build one from.")
print("\n3. CANNOT. jmespath selects; it does not propose or price row shapes.")
print("\n5. CANNOT. No verb reports the type of a field across records. The one")
print("   type fact in this document — execution_count null on 1 of 132 — is")
print("   invisible, and `type()` works on a single value at a time.")

# ── 6. are any object keys data ──────────────────────────────────────────────
print("\n6. CANNOT. `keys(cells[].outputs[].data | [0])` lists the mime types and")
print("   presents them exactly as `cell_type` is presented. A key that is data")
print("   and a key that is a field name are the same thing to jmespath.")
print("   The `cells[].outputs[]` flatten is needed because `cells[3]` is a")
print("   markdown cell and `keys(null)` is a TypeError — the one place")
print("   jmespath raises instead of returning None, and it raises on the")
print("   describe question rather than on the extract ones.")
print(f"   {jmespath.search('keys(cells[].outputs[].data | [0])', doc)}")

# ── 7. how many records ──────────────────────────────────────────────────────
print(f"\n7. cells: {jmespath.search('length(cells)', doc)}   "
      f"outputs: {len(jmespath.search('cells[].outputs[]', doc))}")
print("   `cells[].outputs[]` flattens and SKIPS the 140 markdown cells with no")
print("   complaint, which is right here and is the same silence as Q9 below.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. PARTLY — a projection counts what is there, once you name it:")
for f in ("cell_type", "source", "metadata", "execution_count", "outputs"):
    n = len(jmespath.search(f"cells[].{f}", doc) or [])
    print(f"     {f:18} {n:>4} of 272")
print("   `execution_count` reads 131. The projection drops both the 140")
print("   absences and the 1 explicit null, so the two collapse — and unlike")
print("   pandas there is not even a NaN left to notice.")

# ── 8. three named fields ────────────────────────────────────────────────────
rows = jmespath.search(
    "cells[].{type: cell_type, n: execution_count, lines: length(source)}", doc)
print(f"\n8. three fields, one row per cell: {len(rows)} rows")
for r in rows[:3]:
    print(f"     {r}")

# ── 9. a field missing from some records ─────────────────────────────────────
# The multiselect-hash KEEPS the row and sets the absent field to None, which is
# the behaviour Q9 asks for and jmespath gets right without being asked.
kept = sum(1 for r in rows if r["n"] is None)
print(f"\n9. {kept} of {len(rows)} rows have n=None, and all 272 rows survive.")
print("   Correct. But the same silence is dangerous one question over:")
print(f"     cells[0].outputs      -> {jmespath.search('cells[0].outputs', doc)!r}")
print(f"     cells[0].nosuchfield  -> {jmespath.search('cells[0].nosuchfield', doc)!r}")
print("   A field that is absent and a field that was never in the format are")
print("   both None. On a document nobody has seen, every path is a guess and")
print("   jmespath never says which guesses were wrong.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
lines = jmespath.search('cells[].outputs[].data."text/plain"[]', doc)
print(f"\n10. text/plain exploded to lines: {len(lines)} rows")
print('   `"text/plain"` must be quoted — the slash is not a bare identifier —')
print("   and three `[]` flattens do the whole descent in one expression.")

# ── 11. every path whose value matches ───────────────────────────────────────
print("\n11. CANNOT. jmespath has no recursive descent operator at all — there")
print("   is no `..` — so a search over unknown paths cannot be expressed.")

# ── 12. flattest honest table ────────────────────────────────────────────────
flat = jmespath.search(
    "cells[].{type: cell_type, kinds: outputs[].output_type}", doc)
print(f"\n12. flattest: {len(flat)} cells, each with a `kinds` LIST.")
print("   jmespath cannot join a parent onto its children — there is no verb")
print("   that carries `cell_type` down onto each output — so the table stays")
print("   nested. WHAT IS LOST: the pairing, and the 17 base64 PNGs (79% of")
print("   the file) which any honest flat table has to drop or carry whole.")
