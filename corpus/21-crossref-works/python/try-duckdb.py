"""DuckDB — Crossref works, 1,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
  measured      2026-08-11
  run           cd corpus/21-crossref-works/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                            14   YES                 PARTLY — two views
   2 how deep                                    4   NO                  PARTLY
   3 what is one record                         20   YES                 THE SPLIT, correctly
   4 always present vs sometimes                 6   NO                  yes — 40, 0 nulls
   5 does any field change type                  6   YES                 confirms, cannot find
   6 are any object keys data                    8   YES                 counts, no verdict
   7 how many records                            1   NO                  yes, both numbers
   8 three named fields to a table               4   YES                 yes, all quoted
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   6   YES                 yes — 18,155
  11 find every path matching something          4   YES                 PARTLY
  12 flattest honest table                       3   NO                  TWO ANSWERS
  13 needed the shape in advance?                    YES — the records are at
                                                     $.message.items and read_json_auto
                                                     stops at the envelope
  14 survives the next file unchanged?               Q3/Q4 yes, every $-path no
  15 readable a week later?                          the Q3 CTE, no
  16 lines, and how much is ceremony?                ~150, mostly SQL

  ══════════════════════════════════════════════════════════════════════════════
  DUCKDB IS THE ONLY TOOL HERE THAT CAN PRICE THE SPLIT BOTH WAYS, AND IT HAS NO
  VERB THAT CHOOSES TO.
  ══════════════════════════════════════════════════════════════════════════════

  Computed with `json_keys` so the column set is recomputed PER GROUP:

      worst 0.2629, weighted 0.2073, unsplit 0.4454

  Those are jq's numbers to four decimal places, and they are the probe's own
  internal figures — a third independent computation of the quantity defect 24
  turns on. pandas and polars, pricing the same split over a FIXED column set,
  get weighted 44.3% and 44.5%, equal to the unsplit figure by arithmetic.

  DuckDB can do it only by leaving the relational world: `json_keys` is a JSON
  scalar function, not a table operation. Build a real table and the column set
  is fixed and the split becomes invisible again. THE TOOL CONTAINS BOTH
  ANSWERS AND NOTHING IN IT PREFERS ONE.

  IT DISAGREES WITH ITSELF ON QUESTION 1 TOO. `read_json_auto` on the file gives
  the 4-column ENVELOPE, one row; pointed at `$.message.items` it gives 1,000
  records with 57 keys. Two views, two answers, and the first is not an error.

  20 OF 57 FIELD NAMES CONTAIN A HYPHEN, which is SQL's minus sign, so every one
  needs double quotes. Entry 20 hit the same wall over `desc`, a reserved word;
  here it is the grammar itself rather than one unlucky name.
"""
import time
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
con = duckdb.connect()

print("\nQ0  DuckDB parses or refuses; no duplicate-key or big-int report. CANNOT.")

# ── Q1. The wrapper problem, in SQL. ─────────────────────────────────────────
t = time.time()
con.execute(f"CREATE VIEW env AS SELECT * FROM read_json_auto('{RAW}')")
envcols = con.execute("DESCRIBE env").fetchall()
print(f"\nQ1  read_json_auto on the FILE gives {len(envcols)} columns:")
for n, ty, *_ in envcols:
    print(f"    {n:18} {ty[:70]}")
print("    THE ENVELOPE, one row. The records are at $.message.items and DuckDB")
print("    found the root object, exactly as polars' read_json did.")
con.execute(f"""CREATE VIEW f AS
  SELECT unnest(items) AS w FROM (SELECT message.items AS items FROM env)""")
cols = con.execute("""SELECT unnest(map_keys(row_to_json_stub)) FROM (SELECT NULL AS row_to_json_stub) WHERE false""").fetchall() if False else None
con.execute(f"""CREATE VIEW items AS SELECT unnest(json_transform_strict(
  json_extract(json, '$.message.items'), '["JSON"]')) AS j
  FROM read_json_objects('{RAW}')""")
n = con.execute("SELECT count(*) FROM items").fetchone()[0]
print(f"\nQ1  pointed at $.message.items via json_extract: {n:,} records, "
      f"{time.time()-t:.1f}s")
keys = con.execute("""
  SELECT k, count(*) AS present FROM (SELECT unnest(json_keys(j)) AS k FROM items)
  GROUP BY k ORDER BY present DESC""").fetchdf()
print(f"Q1  {len(keys)} distinct record keys")

# ── Q2. ──────────────────────────────────────────────────────────────────────
w = con.execute("SELECT column_type FROM (DESCRIBE env) WHERE column_name='message'").fetchone()
print(f"\nQ2  the envelope's `message` type is {len(w[0]):,} characters of nested SQL type.")
print("    Depth is readable from it by counting brackets and is never reported.")
print("    The probe says 9. PARTLY.")

# ── Q3. THE SPLIT, third independent frame. ──────────────────────────────────
print("\nQ3  the record and its cost, computed with json_keys so the column set")
print("    is per-group rather than fixed — WHICH IS THE THING pandas AND polars")
print("    CANNOT DO, and DuckDB can only because it left the relational world:")
split = con.execute("""
WITH r AS (SELECT j, json_extract_string(j, '$.type') AS type FROM items),
     cols AS (SELECT type, count(DISTINCT k) AS ncol FROM
              (SELECT type, unnest(json_keys(j)) AS k FROM r) GROUP BY type),
     cnt  AS (SELECT type, count(*) AS nrow, sum(len(json_keys(j))) AS filled FROM r GROUP BY type)
SELECT c.type, c.nrow, x.ncol, 1 - (c.filled::DOUBLE / (c.nrow * x.ncol)) AS empty
FROM cnt c JOIN cols x USING (type) ORDER BY c.nrow DESC""").fetchdf()
tot_rows = split["nrow"].sum()
weighted = (split["nrow"] * split["empty"]).sum() / tot_rows
allcols = con.execute("SELECT count(DISTINCT k) FROM (SELECT unnest(json_keys(j)) AS k FROM items)").fetchone()[0]
filled = con.execute("SELECT sum(len(json_keys(j))) FROM items").fetchone()[0]
unsplit = 1 - filled / (n * allcols)
print(split.head(5).to_string(index=False))
print(f"    worst {split['empty'].max():.4f}, weighted {weighted:.4f}, "
      f"unsplit {unsplit:.4f}")
print("    THESE ARE jq's NUMBERS, not pandas'. Recomputing the column set per")
print("    group is what makes a split visible, and it took `json_keys` — a")
print("    JSON scalar function — rather than anything relational.")
print("    DuckDB is the only tool in this directory that can compute the")
print("    quantity BOTH ways, and it has no verb that chooses to.")

# ── Q4. ──────────────────────────────────────────────────────────────────────
absent = keys[keys["present"] < n]
print(f"\nQ4  keys not on every record: {len(absent)} of {len(keys)}")
nulls = con.execute("""SELECT count(*) FROM (SELECT unnest(json_keys(j)) AS k, j FROM items)
                       WHERE json_type(json_extract(j, '$.' || k)) = 'NULL'""").fetchone()[0]
print(f"Q4  keys written as null anywhere: {nulls}")
print("    ZERO. json_keys counts PRESENCE and there is nothing to conflate, so")
print("    every tool in this directory should agree on question 4 — the entry-14")
print("    situation, and the document is the reason.")

# ── Q5. ──────────────────────────────────────────────────────────────────────
print("\nQ5  the probe's one site is issued.date-parts, [[2018,11,3]] vs [[null]]:")
dp = con.execute("""SELECT json_type(json_extract(j, '$.issued.date-parts[0][0]')) AS t,
                           count(*) AS n FROM items GROUP BY t ORDER BY n DESC""").fetchdf()
print(dp.to_string(index=False))
print("    DuckDB CAN see it — `json_type` two levels into the array — and only")
print("    because the path was written by someone who already knew. There is no")
print("    census verb; finding the site is question 5 and this only confirms it.")

# ── Q6. ──────────────────────────────────────────────────────────────────────
# TWO WRONG DRAFTS BEFORE THIS ONE, both plausible: counting key occurrences
# gave 109,264 and windowing before the unnest gave 535 (the number of WORKS
# with a reference). The copies are the unnested rows themselves.
con.execute("""CREATE VIEW refs AS
  SELECT unnest(json_transform_strict(json_extract(j,'$.reference'), '["JSON"]')) AS r
  FROM items WHERE json_extract(j,'$.reference') IS NOT NULL""")
ref = con.execute("""SELECT
    (SELECT count(DISTINCT k) FROM (SELECT unnest(json_keys(r)) AS k FROM refs)),
    (SELECT count(*) FROM refs)""").fetchone()
print(f"\nQ6  reference[]: {ref[0]} keys over {ref[1]:,} copies")
print("    The probe DECLINES it as a vocabulary rather than data. DuckDB counts.")

# ── HYPHENS AND RESERVED WORDS. ──────────────────────────────────────────────
hy = [k for k in keys["k"] if "-" in k]
print(f"\n     HYPHENATED KEYS: {len(hy)} of {len(keys)}")
try:
    con.execute("SELECT is-referenced-by-count FROM env LIMIT 0")
    print("     unquoted hyphen parsed — rewrite this note")
except Exception as e:
    print(f"     unquoted: {type(e).__name__}: {' '.join(str(e).split())[:64]}")
    print("     A hyphen is SQL's minus sign, so every one of these needs double")
    print("     quotes. Entry 20 hit the same wall with `desc`, a reserved word;")
    print("     here it is 20 field names and the cause is the grammar itself.")

# ── Q7/Q8/Q9/Q10/Q11/Q12. ────────────────────────────────────────────────────
tot = con.execute("SELECT message['total-results'] FROM env").fetchone()[0]
print(f"\nQ7  {n:,} records in the array; total-results says {tot:,}")
t8 = con.execute("""SELECT json_extract_string(j,'$.DOI') AS doi,
                           json_extract_string(j,'$.type') AS type,
                           json_extract_string(j,'$.publisher') AS publisher
                    FROM items LIMIT 2""").fetchdf()
print(f"\nQ8  {t8.shape}\n{t8.to_string(index=False)}")
q9 = con.execute("""SELECT count(*) FILTER (WHERE json_extract(j,'$.abstract') IS NOT NULL)
                    FROM items""").fetchone()[0]
print(f"\nQ9  abstract present on {q9} of {n:,}; the row is kept either way")
t = time.time()
q10 = con.execute("""SELECT count(*) FROM (
  SELECT json_extract_string(j,'$.DOI') AS work_doi,
         unnest(json_transform_strict(json_extract(j,'$.reference'), '["JSON"]')) AS r
  FROM items WHERE json_extract(j,'$.reference') IS NOT NULL)""").fetchone()[0]
print(f"\nQ10 reference[] -> {q10:,} rows, {time.time()-t:.1f}s — the true count is 18,155")
print("    The parent DOI is aliased, so no collision: DuckDB renames on")
print("    collision anyway, which entry 20 measured.")
print("\nQ11 no `paths(...)`. A recursive CTE over json_each would reach every")
print("    string; the named-path version answers a smaller question:")
u = con.execute("""SELECT count(*) FROM items
                   WHERE json_extract_string(j,'$.URL') SIMILAR TO '^https?://.*'""").fetchone()[0]
print(f"    $.URL matches ^https?:// on {u:,} of {n:,}. jq reports 13 distinct URL PATHS.")
print(f"\nQ12 the honest table is {n:,} x {len(keys)} with JSON in the cells, or the")
print("    envelope's 4 columns if you let read_json_auto choose. TWO ANSWERS")
print("    from one tool, and the difference is which view you created.")
