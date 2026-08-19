"""DuckDB — Jupyter notebook, Norvig Advent-2021, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
  measured      2026-08-10
  run           cd corpus/11-jupyter-notebook/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  yes
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          6   YES                 PARTLY
   4 always present vs sometimes                 -   -                   CANNOT
   5 does any field change type                  5   YES                 PARTLY
   6 are any object keys data                    4   YES                 CANNOT
   7 how many records                            2   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 PARTLY
  13 needed the shape in advance?                    NO for 1 — YES after
  14 survives the next file unchanged?               1 does; the SQL does not
  15 readable a week later?                          yes, it is SQL
  16 lines, and how much is ceremony?                ~45, some SQL ceremony
"""
import sys
from importlib.metadata import version

import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")
con = duckdb.connect()
SRC = "read_json_auto('../source.json', maximum_object_size=100000000)"

# ── 1. what is in here ───────────────────────────────────────────────────────
# DESCRIBE returns four tidy rows. On 01-npm-registry the same call hid a
# 378,036-character type inside one cell; here the whole schema is small,
# because this document has 37 distinct paths and no keys-as-data of any size.
d = con.sql(f"DESCRIBE SELECT * FROM {SRC}").df()
total = sum(len(str(t)) for t in d["column_type"])
print(f"\n1. DESCRIBE: {len(d)} rows, all type cells together {total:,} chars "
      f"({100 * total / 1114184:.2f}% of the file)")
for c, t in zip(d["column_name"], d["column_type"]):
    print(f"     {c:16} {str(t)[:92]}")

# ── 2. how deep ──────────────────────────────────────────────────────────────
print("\n2. CANNOT directly. The depth is inside that type string and DuckDB")
print("   offers no verb for it — counting STRUCT( and [] in a text blob is")
print("   parsing the answer out of a printout, not asking a question.")

# ── 5. does any field change type ────────────────────────────────────────────
# DuckDB must unify element types to build a column, which is exactly why it
# found the array-element bug on 05-fhir-bundle that shape() could not see.
print("\n5. PARTLY, and the mechanism is worth stating. DuckDB unifies to build")
t = con.sql(f"SELECT typeof(cells[1].execution_count) a, "
            f"typeof(cells[1].source) b, "
            f"typeof(cells[1].outputs) c FROM {SRC}").fetchone()
print(f"   a column, so it reports ONE type per field: execution_count={t[0]}, "
      f"source={t[1]},")
print(f"   outputs={str(t[2])[:56]}…")
print("   The 1 null execution_count and the 140 absent ones are both NULL in")
print("   a BIGINT column. Unification is what makes DuckDB good at Q5 across")
print("   heterogeneous records and blind to it within one column.")

# ── 6. are any object keys data ──────────────────────────────────────────────
print("\n6. CANNOT. `data` is keyed by mime type and DuckDB makes it a STRUCT,")
print("   so `text/plain` and `image/png` become field names needing double")
print("   quotes to reference. A key that is data is indistinguishable from a")
print("   field, and the quoting is the only hint anything is unusual.")

# ── 3, 7. what is one record, and how many ───────────────────────────────────
n = con.sql(f"SELECT len(cells) FROM {SRC}").fetchone()[0]
no = con.sql(f"SELECT sum(len(c.outputs)) FROM {SRC}, "
             f"unnest(cells) t(c)").fetchone()[0]
print(f"\n3. three defensible records:")
print(f"     the whole document      1 row x {len(d)} cols")
print(f"     a cell                {n} rows x 5 cols")
print(f"     an output             {int(no)} rows x 6 cols")
print("   `unnest` gets from one to the next and needs the field named. There")
print("   is no verb that proposes the candidates.")
print(f"\n7. {n} cells, {int(no)} outputs.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. CANNOT. Same unification: every cell is one STRUCT type, so every")
print("   field exists on every row. A markdown cell's missing `outputs` and a")
print("   code cell's empty `outputs` are both readable as NULL/[] and nothing")
print("   in the schema records that 140 rows never had the field.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
q = con.sql(f"""
    SELECT c.cell_type, c.execution_count, len(c.source) AS lines
    FROM {SRC}, unnest(cells) t(c) LIMIT 3""").df()
print(f"\n8. three fields, one row per cell:\n{q.to_string(index=False)}")
miss = con.sql(f"""
    SELECT count(*) FROM {SRC}, unnest(cells) t(c)
    WHERE c.execution_count IS NULL""").fetchone()[0]
print(f"\n9. execution_count NULL on {miss} of {n} rows, all rows kept.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
tp = con.sql(f"""
    SELECT count(*) FROM {SRC}, unnest(cells) t(c),
    unnest(c.outputs) u(o), unnest(o.data."text/plain") v(line)""").fetchone()[0]
print(f"\n10. text/plain exploded to lines: {tp} rows")
print('   Three nested `unnest`es and a double-quoted "text/plain". DuckDB is')
print("   the only tool here that flattens all three levels in one statement.")

# ── 11. every path whose value matches ───────────────────────────────────────
print("\n11. CANNOT. There is no path search over an arbitrary document; every")
print("   column must be named. The 53 source lines mentioning a URL are")
print("   reachable only by unnesting `source` and knowing to look.")

# ── 12. flattest honest table ────────────────────────────────────────────────
flat = con.sql(f"""
    SELECT c.cell_type, c.execution_count, o.output_type, o.name,
           len(o.data."text/plain") AS tp_lines
    FROM {SRC}, unnest(cells) t(c), unnest(c.outputs) u(o)""").df()
print(f"\n12. flattest: {flat.shape[0]} x {flat.shape[1]}, "
      f"{100 * flat.isna().mean().mean():.0f}% empty")
print("   WHAT IS LOST: the 140 markdown cells, dropped by the inner unnest")
print("   with no warning; `source`, still a list; and the 17 base64 PNGs,")
print("   79% of the file's bytes, which no flat table wants.")
