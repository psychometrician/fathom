"""pandas — Jupyter notebook, Norvig Advent-2021, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
  measured      2026-08-10
  run           cd corpus/11-jupyter-notebook/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   NO                  PARTLY
   2 how deep                                     -  -                   CANNOT
   3 what is one record                           6  YES                 PARTLY
   4 always present vs sometimes                  3  YES                 YES
   5 does any field change type                   4  YES                 PARTLY
   6 are any object keys data                     3  YES                 CANNOT
   7 how many records                             2  YES                 YES
   8 three named fields to a table                4  YES                 yes
   9 a field missing from some rows               4  YES                 yes
  10 flatten the deepest array                    5  YES                 yes
  11 find every path matching something           -  -                   CANNOT
  12 flattest honest table                        6  YES                 PARTLY
  13 needed the shape in advance?                     YES for everything past Q1
  14 survives the next file unchanged?                no — `outputs` column
  15 readable a week later?                           yes
  16 lines, and how much is ceremony?                 ~45, little ceremony
"""
import json
import sys
from importlib.metadata import version

import pandas as pd

print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")
doc = json.load(open("../source.json"))

# ── 1. what is in here ───────────────────────────────────────────────────────
# json_normalize on the root descends objects and stops at the first array, so
# `cells` — the entire document — arrives as one opaque cell. This is the same
# failure recorded on 07-graphql-introspection: a small answer that says nothing.
root = pd.json_normalize(doc)
print(f"\n1. json_normalize(root): {root.shape[0]} row x {root.shape[1]} cols")
print(f"   {list(root.columns)}")
print(f"   the whole description: {len(str(list(root.columns)))} chars, and the")
print("   272 cells are one cell of it. Everything below needs `cells` named by")
print("   hand, so Q1 is answered by knowing the answer.")

cells = pd.json_normalize(doc["cells"])
print(f"\n   json_normalize(cells): {cells.shape[0]} x {cells.shape[1]}  "
      f"{list(cells.columns)}")

# ── 2. how deep ──────────────────────────────────────────────────────────────
print("\n2. CANNOT. A data frame has no depth, and json_normalize flattens")
print("   whatever it descends into dotted names — the nesting it did not")
print("   descend (every array) is invisible. The true depth is 7.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. fraction of the 272 cells where each field is not null:")
for k, v in (cells.notna().sum() / len(cells)).sort_values(ascending=False).items():
    print(f"     {k:18} {v:.0%}")
print("   `execution_count` reads 48%, and that is TWO facts pandas merges into")
print("   one: 140 markdown cells do not have the field, and 1 code cell has it")
print("   as null. NaN cannot tell absent from null, so Q4 and Q5 collapse.")

# ── 5. does any field change type ────────────────────────────────────────────
print("\n5. PARTLY. dtypes are the answer pandas gives:")
print("   " + "; ".join(f"{c}={cells[c].dtype}" for c in cells.columns))
print("   `execution_count` is float64 because 1 of 132 is null — an int column")
print("   promoted by a single missing value. `source` and `outputs` are object,")
print("   which is pandas for 'a Python object' and says nothing at all.")

# ── 6. are any object keys data ──────────────────────────────────────────────
print("\n6. CANNOT, and it is worse than silence. The mime types `text/plain`")
print("   and `image/png` key the `data` objects, and json_normalize turns them")
print("   into COLUMNS — `data.text/plain`, `data.image/png` — so keys that are")
print("   data become field names with no way to say so.")

# ── 3, 7. what is one record, and how many ───────────────────────────────────
# MEASURED, and it is the sharpest thing this file found. The obvious call
# RAISES, and `errors="ignore"` does not help because that argument governs
# `meta` and not `record_path`.
try:
    pd.json_normalize(doc["cells"], record_path="outputs",
                      meta=["cell_type"], errors="ignore")
    raise SystemExit("expected a KeyError and did not get one")
except KeyError as e:
    print(f"\n3. record_path='outputs' RAISES: {str(e)[:68]}…")
    print("   140 markdown cells have no `outputs`, and pandas requires the")
    print("   record path on EVERY element. `errors='ignore'` governs `meta`,")
    print("   not `record_path`, so the ragged case has no flag at all — the")
    print("   140 rows must be filtered out by hand, which means knowing they")
    print("   are there. Q3's deeper answer is unreachable without Q4's answer.")

code = [c for c in doc["cells"] if c["cell_type"] == "code"]
outs = pd.json_normalize(code, record_path="outputs", meta=["cell_type"])
print(f"\n   three defensible records, and pandas prices two of them:")
print(f"     the whole document      1 row x {root.shape[1]} cols")
print(f"     a cell                {len(cells)} rows x {cells.shape[1]} cols   "
      f"{100 * cells.isna().mean().mean():.0f}% empty")
print(f"     an output             {len(outs)} rows x {outs.shape[1]} cols   "
      f"{100 * outs.isna().mean().mean():.0f}% empty")
print("   The output row costs all 140 markdown cells, and that cost is paid by")
print("   the hand-written filter above rather than by pandas — which is the")
print("   better failure. It refused rather than quietly returning 107 rows.")
print(f"\n7. {len(cells)} cells, {len(outs)} outputs.")

# ── 8. three named fields ────────────────────────────────────────────────────
t = cells[["cell_type", "execution_count"]].copy()
t["lines"] = cells["source"].map(len)
print(f"\n8. three fields, one row per cell:\n{t.head(3).to_string(index=False)}")

# ── 9. a field missing from some records ─────────────────────────────────────
print(f"\n9. execution_count is absent on all 140 markdown cells and kept:")
print(f"   {int(t['execution_count'].isna().sum())} of {len(t)} rows are NaN, "
      f"{int(t['cell_type'].eq('markdown').sum())} of them markdown.")
print("   Kept for free — pandas never drops a row for a missing key — but the")
print("   140 structural absences and the 1 real null are the same NaN.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
deep = pd.json_normalize(code, record_path="outputs")
lines = deep[["output_type", "data.text/plain"]].dropna(
    subset=["data.text/plain"]).explode("data.text/plain")
print(f"\n10. outputs flattened: {len(deep)} rows. text/plain exploded to lines: "
      f"{len(lines)} rows")
print("   Three hand-typed paths deep — filter to code, record_path, explode —")
print("   and the column name `data.text/plain` has a dot and a slash in it,")
print("   so it cannot be reached with attribute access.")

# ── 11. every path whose value matches ───────────────────────────────────────
print("\n11. CANNOT. pandas has no whole-document path search. `.str.contains`")
print("   works on one column at a time, and the columns holding text here are")
print("   list-columns, so even that needs an explode first.")

# ── 12. flattest honest table ────────────────────────────────────────────────
flat = pd.json_normalize(code, record_path="outputs",
                         meta=["cell_type", "execution_count"],
                         meta_prefix="cell.", errors="ignore")
print(f"\n12. flattest: {flat.shape[0]} x {flat.shape[1]}   "
      f"{100 * flat.isna().mean().mean():.0f}% empty")
print("   WHAT IS LOST: all 140 markdown cells, because they have no `outputs`")
print("   to be a record of; `source`, still a list in a cell; and the 17")
print("   base64 PNGs, which are 79% of the file's bytes sitting in one column.")
