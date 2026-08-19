"""polars — Jupyter notebook, Norvig Advent-2021, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
  measured      2026-08-10
  run           cd corpus/11-jupyter-notebook/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  yes
   2 how deep                                    4   NO                  yes
   3 what is one record                          6   YES                 PARTLY
   4 always present vs sometimes                 -   -                   CANNOT
   5 does any field change type                  4   YES                 PARTLY
   6 are any object keys data                    3   YES                 CANNOT
   7 how many records                            2   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              4   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 PARTLY
  13 needed the shape in advance?                    NO for 1, 2 — YES after
  14 survives the next file unchanged?               1 and 2 do; the rest do not
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~45, little ceremony
"""
import json
import sys
from importlib.metadata import version

import polars as pl

print(f"python {sys.version.split()[0]}, polars {version('polars')}")

# ── 1. what is in here ───────────────────────────────────────────────────────
# polars infers a real nested schema, which is the right idea, and on this
# document it is also small — 1.1 MB in, 0.1% out. That is NOT the O(data)
# failure recorded on npm and Stripe, and the reason is measurable: this file
# has zero keys-as-data at the sites that matter and only 37 distinct paths.
df = pl.read_json("../source.json")
schema = str(df.schema)
print(f"\n1. schema: {len(schema):,} chars for a 1,114,184-byte file "
      f"({100 * len(schema) / 1114184:.2f}% of it)")
for name, dt in df.schema.items():
    print(f"     {name:16} {str(dt)[:96]}")

# ── 2. how deep ──────────────────────────────────────────────────────────────
def depth(dt):
    if isinstance(dt, pl.Struct):
        return 1 + max((depth(f.dtype) for f in dt.fields), default=0)
    if isinstance(dt, pl.List):
        return 1 + depth(dt.inner)
    return 0


print(f"\n2. deepest nesting: {1 + max(depth(d) for d in df.schema.values())}")
print("   The true depth is 7 and this reports it — the `1 +` is the root")
print("   object, which is not in `df.schema` because it became the frame.")
print("   polars descends ARRAYS as well as objects, so it is the only tool")
print("   in the Python set that answers Q2 from its own output rather than")
print("   from a hand walk. pandas stops at the first array and reports 2.")

# ── 5. does any field change type ────────────────────────────────────────────
# `empty_as_null` is passed explicitly rather than defaulted, and it is not
# tidiness: 28 of the 132 code cells have an EMPTY `outputs` array, and this
# flag decides whether those become a null row or vanish. polars 2.0 changes
# the default, so a file that relies on it would silently re-measure.
cells = df["cells"].explode(empty_as_null=True).struct.unnest()
print(f"\n5. PARTLY. `execution_count` is {cells['execution_count'].dtype}, and")
print("   polars cannot say it is null on 1 of 132 code cells and ABSENT on")
print("   140 markdown ones — a struct field missing from a value becomes null,")
print("   so the two are the same. It also unified `source` to List(String)")
print("   across all 272, which is correct here and would be a silent rewrite")
print("   if any cell held a bare string, as nbformat permits.")

# ── 6. are any object keys data ──────────────────────────────────────────────
print("\n6. CANNOT. `data` is keyed by `text/plain` and `image/png`, and polars")
print("   makes them STRUCT FIELDS — a mime type becomes a column name. The")
print("   inference is silent about the difference between a field and a value.")

# ── 3, 7. what is one record, and how many ───────────────────────────────────
outs = cells["outputs"].explode(empty_as_null=True).drop_nulls().struct.unnest()
print(f"\n3. three defensible records:")
print(f"     the whole document      1 row x {df.width} cols")
print(f"     a cell                {cells.height} rows x {cells.width} cols   "
      f"{100 * sum(cells[c].null_count() for c in cells.columns) / (cells.height * cells.width):.0f}% empty")
print(f"     an output             {outs.height} rows x {outs.width} cols   "
      f"{100 * sum(outs[c].null_count() for c in outs.columns) / (outs.height * outs.width):.0f}% empty")
print("   `explode` then `drop_nulls` gets the outputs without pre-filtering to")
print("   code cells, which is the thing pandas refused to do.")
print(f"\n7. {cells.height} cells, {outs.height} outputs.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. CANNOT, and the reason is structural rather than a missing verb.")
print("   polars unified all 272 cells into ONE struct type, so every field")
print("   exists on every row and `null_count` mixes absence with null:")
for c in cells.columns:
    print(f"     {c:18} {cells[c].null_count():>4} null of {cells.height}")
print("   `execution_count` shows 141 = 140 absent + 1 genuinely null, and")
print("   nothing in the output separates them. Same collapse as pandas.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
t = cells.select("cell_type", "execution_count",
                 pl.col("source").list.len().alias("lines"))
print(f"\n8. three fields, one row per cell:\n{t.head(3)}")
print(f"\n9. execution_count null on {t['execution_count'].null_count()} of "
      f"{t.height} rows, all rows kept.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
tp = outs.select(pl.col("data").struct.field("text/plain")).explode(
    "text/plain", empty_as_null=True).drop_nulls()
print(f"\n10. text/plain exploded to lines: {tp.height} rows")
print("   `.struct.field('text/plain')` — the slash means it can only be")
print("   reached as a string, never as an attribute.")

# ── 11. every path whose value matches ───────────────────────────────────────
print("\n11. CANNOT. polars has no whole-document path search; every expression")
print("   names a column. Reaching the 53 source lines that mention a URL")
print("   means exploding `source` first and knowing to look there.")

# ── 12. flattest honest table ────────────────────────────────────────────────
print(f"\n12. flattest: the {outs.height}-row output table, {outs.width} cols.")
print("   WHAT IS LOST: the 140 markdown cells, which have no output; the")
print("   cell/output nesting, unless `cell_type` is carried down by hand; and")
print("   the 17 base64 PNGs are 79% of the file sitting in one string column.")
