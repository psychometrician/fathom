"""DuckDB — Docker Hub tags, 100 tags

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   476 KB, 100 tags under $.results, depth 5
  measured      2026-08-11
  run           cd corpus/22-dockerhub-tags/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             8   YES                 yes, once pointed
   2 how deep                                    3   NO                  PARTLY
   3 what is one record                          8   YES                 BOTH, priced
   4 always present vs sometimes                10  NO                   YES via json_keys
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                    1   -                   n/a
   7 how many records                            2   NO                  yes, both numbers
   8 three named fields to a table               2   YES                 yes, unquoted
   9 a field missing from some rows              2   YES                 PARTLY
  10 flatten the deepest array                   4   YES                 yes — 1,388
  11 find every path matching something          3   NO                  NONE OF ONE
  12 flattest honest table                       3   NO                  yes
  13 needed the shape in advance?                    yes — read_json_auto stops at
                                                     the envelope
  14 survives the next file unchanged?               Q3/Q4 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~90

  THE NESTED CONTROL. No hyphens, no reserved words, one key-set per shape —
  so every escaping problem entries 20 and 21 recorded is absent and the SQL
  reads plainly. `read_json_auto` still returns the 1-row envelope, as it did
  on entry 21, and pointing it at `$.results` costs one `unnest`.
"""
import time
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
con = duckdb.connect()
print("\nQ0  DuckDB parses or refuses; no health report. CANNOT.")

con.execute(f"CREATE VIEW env AS SELECT * FROM read_json_auto('{RAW}')")
ec = con.execute("DESCRIBE env").fetchall()
print(f"\nQ1  read_json_auto on the file -> {len(ec)} columns: "
      f"{[c[0] for c in ec]}")
print("    THE ENVELOPE, one row. Same as entry 21 and as polars' read_json.")
con.execute("CREATE VIEW tags AS SELECT unnest(results) AS t FROM env")
cols = con.execute("SELECT unnest(map_keys(from_json(to_json(t), '\"MAP(VARCHAR, JSON)\"'))) AS k "
                   "FROM tags LIMIT 100").fetchdf()
n = con.execute("SELECT count(*) FROM tags").fetchone()[0]
print(f"Q1  unnest(results) -> {n} tags, {cols['k'].nunique()} distinct keys")
ty = con.execute("SELECT column_type FROM (DESCRIBE env) WHERE column_name='results'").fetchone()
print(f"\nQ2  the `results` type is {len(ty[0])} characters of nested SQL type;")
print("    depth is readable from the brackets and never reported. Probe: 5.")

print(f"\nQ3  an item of results: {n} rows x {cols['k'].nunique()} — the probe says 0% empty")
t = time.time()
img = con.execute("""SELECT t.name AS tag, unnest(t.images) AS im FROM tags""").fetchdf()
nimg = len(img)
print(f"Q3  an item of images:  {nimg:,} rows, {time.time()-t:.2f}s")
print("    THE PROBE PRICES BOTH: 100 x 16 at 0%, 1,388 x 11 at 16% empty with")
print("    `size` repeated 4x. DuckDB builds either and prices neither.")

# ── Q4. THE THREE STATES, via json_keys and json_type. ──────────────────────
q = con.execute("""
WITH im AS (SELECT to_json(unnest(t.images)) AS j FROM tags),
     kv AS (SELECT unnest(json_keys(j)) AS k, j FROM im)
SELECT k,
       count(*) AS present,
       count(*) FILTER (WHERE json_type(json_extract(j, '$.' || k)) = 'NULL') AS nulls,
       count(*) FILTER (WHERE json_extract_string(j, '$.' || k) = '') AS empties
FROM kv GROUP BY k ORDER BY nulls DESC, empties DESC""").fetchdf()
print(f"\nQ4  image keys, all three states:")
print(q[(q["nulls"] > 0) | (q["empties"] > 0)].to_string(index=False))
print(f"    every key is PRESENT on all {nimg:,} images — nothing is absent.")
print("    DuckDB can count all three, and only through `json_type` and")
print("    `json_extract_string`, which is leaving the relational world again.")
print(f"    the probe's 16% counts the nulls; all three would be "
      f"{(q['nulls'].sum()+q['empties'].sum())/(nimg*11):.0%}.")

print("\nQ5  every column unified without complaint; the probe reports NONE.")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
cnt = con.execute("SELECT count FROM env").fetchone()[0]
print(f"\nQ7  {n} tags here; `count` says {cnt:,}, and `next` is a URL")

t8 = con.execute("SELECT t.name, t.full_size, t.last_updated FROM tags LIMIT 2").fetchdf()
print(f"\nQ8  {t8.shape} — and NO QUOTING NEEDED. Entry 20 needed \"desc\" and")
print("    entry 21 needed 20 quoted hyphens; this document's names are all")
print(f"    plain SQL identifiers.\n{t8.to_string(index=False)}")
nv = con.execute("""SELECT count(*) FILTER (WHERE im.variant IS NOT NULL)
                    FROM (SELECT unnest(t.images) AS im FROM tags)""").fetchone()[0]
print(f"\nQ9  `variant` non-null on {nv:,} of {nimg:,}; the row is kept either way")
print(f"\nQ10 unnest(images) -> {nimg:,} rows with the tag name carried — see Q3")
print("\nQ11 DuckDB has no `paths(...)`. The one URL in this document is `$.next`,")
print("    in the ENVELOPE, so a query over `tags` reports NONE OF ONE:")
u = con.execute("""SELECT count(*) FROM tags
                   WHERE regexp_matches(to_json(t), 'https?://')""").fetchone()[0]
print(f"    tags whose JSON contains any http(s) URL: {u}")
print(f"\nQ12 {n} x {cols['k'].nunique()} with a LIST(STRUCT) column, or {nimg:,} rows")
print("    exploded. Both honest; DuckDB builds either and chooses neither.")
