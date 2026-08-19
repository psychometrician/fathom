"""duckdb — USGS earthquakes, one month

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   7.4 MB, 10,885 features, depth 5
  measured      2026-08-10
  run           cd corpus/25-usgs-quakes/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             8   NO                  YES — best here
   2 how deep                                    -   NO                  yes, via Q1
   3 what is one record                          2   YES                 PARTLY
   4 always present vs sometimes                 5   NO                  PARTLY
   5 does any field change type                  2   -                   CANNOT
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   5   YES                 yes
  11 find every path matching something          7   NO                  YES — real scan
  12 flattest honest table                       3   NO                  yes
  13 needed the shape in advance?                    NO for Q1 and Q11, yes elsewhere
  14 survives the next file unchanged?               Q1 and Q11 do; the rest name fields
  15 readable a week later?                          Q11's double `unnest` needs a look
  16 lines, and how much is ceremony?                ~110, of which ~10 are workarounds

**`json_structure` DESCRIBES A 7.4 MB FILE IN 716 CHARACTERS**, without being
told the shape, and it is the only tool in this comparison that does. For scale:
`design/probe.py`'s whole report on this document is 926 bytes. **duckdb is the
nearest thing to a competitor the corpus has found for question 1**, and this is
the second file to say so.

What it buys and what it does not: the structure is a TYPE tree, so it answers
questions 1, 2 and 5-as-resolved, and says nothing about how many records, how
empty a table would be, or which fields are only sometimes there. It also
reports `"tz":"NULL"` as a type, which is the thing `design/axes.py` and defect
11 rule against.

**Q11 IS A REAL PATH SCAN AND NOT A COLUMN SCAN**, which pandas and polars
cannot do on this file: `json_keys` + `json_extract_string` finds `url` and
`detail` at 10,885 each without either being named in advance.

**THE STRUCT SYNTAX FOUGHT BACK THREE TIMES**, each a parser error rather than a
message: `DESCRIBE SELECT f.* …`, `(f).*`, and `f.properties.*`. Struct expansion
goes exactly one level and `unnest()` is what reaches further. None of that is
about JSON — it is about having to know which of four spellings duckdb accepts.
"""
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")
db = duckdb.connect()

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  duckdb reads it or errors. Nothing about duplicate keys or big ints.")
print("    CANNOT, same as every parser here.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
# `json_structure` is the thing no other tool in this comparison has: a SCHEMA
# printed from the data, without being told the shape.
# `read_json` auto-detects and hands back COLUMNS, so `json_structure` has
# nothing to chew on — the first draft asked for a column called `json` and got
# `Binder Error: Referenced column "json" not found`. `read_json_objects` is the
# one that keeps the document as JSON.
struct = db.sql("""
    SELECT json_structure(json)::VARCHAR AS s
    FROM read_json_objects('../source.json', maximum_object_size=200000000)
""").fetchone()[0]
print(f"\nQ1  json_structure, truncated to 400 chars:\n    {struct[:400]}")
print(f"Q1  json_structure is {len(struct):,} characters for a 7.4 MB file")

feat = db.sql("""
    SELECT unnest(features) AS f
    FROM read_json('../source.json', maximum_object_size=200000000)
""")
db.sql("CREATE OR REPLACE TABLE feats AS SELECT * FROM feat")
# `f.*` expands a struct in SELECT but NOT inside `DESCRIBE SELECT`, which is a
# parser error rather than a message — so the shape has to be materialised first.
db.sql("CREATE OR REPLACE TABLE feat_flat AS SELECT f.* FROM feats")
cols = db.sql("DESCRIBE feat_flat").fetchall()
print(f"Q1  a feature has {len(cols)} fields: {[c[0] for c in cols]}")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
n = db.sql("SELECT count(*) FROM feats").fetchone()[0]
print(f"\nQ3/Q7  a feature: {n:,} rows")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
# `f.properties.*` is a parser error too — struct expansion goes one level, and
# `unnest()` is the one that reaches a nested struct.
db.sql("CREATE OR REPLACE TABLE prop_flat AS SELECT unnest(f.properties) FROM feats")
props = db.sql("DESCRIBE prop_flat").fetchall()
names = [c[0] for c in props]
sql = ", ".join(f"count(f.properties.\"{p}\") AS \"{p}\"" for p in names)
counts = db.sql(f"SELECT {sql} FROM feats").fetchdf().iloc[0].to_dict()
some = {k: int(v) for k, v in counts.items() if v < n}
print(f"\nQ4  properties has {len(names)} fields; always non-null: {len(names) - len(some)}")
print(f"Q4  sometimes: {some}")
print("    duckdb built ONE struct type for all 10,885 features, so a key that")
print("    was absent and one that was null are the same null. Same limit as the frames.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  duckdb RESOLVED one type per field when it built the struct:")
print("   ", {c[0]: c[1] for c in props[:8]}, "…")
print("    Like polars it cannot report a change, because it has already made one.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections here. n/a")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
print("\nQ8 ", db.sql("""
    SELECT f.properties.mag AS mag, f.properties.place AS place, f.properties.time AS time
    FROM feats LIMIT 3
""").fetchall())

# ── Q9. A field missing from some records, keeping those rows. ───────────────
print("\nQ9 ", db.sql("""
    SELECT count(*) AS rows, count(f.properties.alert) AS with_alert FROM feats
""").fetchall())

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
print("\nQ10 ", db.sql("""
    SELECT f.geometry.coordinates[1] AS lon,
           f.geometry.coordinates[2] AS lat,
           f.geometry.coordinates[3] AS depth_km
    FROM feats LIMIT 3
""").fetchall())

# ── Q11. Find every path whose value matches something — here, a URL. ────────
# THE ONE TOOL THAT CAN ASK THIS WITHOUT NAMING COLUMNS: json_keys/json_extract
# over the raw text, rather than over a schema somebody already resolved.
hits = db.sql("""
    SELECT key, count(*) AS n FROM (
      SELECT unnest(json_keys(f.properties::JSON)) AS key,
             json_extract_string(f.properties::JSON, '$.' || unnest(json_keys(f.properties::JSON))) AS val
      FROM feats
    ) WHERE val LIKE 'http%' GROUP BY key ORDER BY n DESC
""").fetchall()
print(f"\nQ11 keys whose values start with http: {hits}")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 flattening needs `unnest(f.properties)`, which expands only because")
print("    duckdb already resolved a struct. `coordinates` stays a LIST[DOUBLE],")
print("    which is the list-column god's spec refuses.")

# ── The packed strings, because defect 26 came from this file. ───────────────
print("\nDEFECT 26  does duckdb notice a list packed into a string?")
print(db.sql("""
    SELECT f.properties.types AS types, f.properties.ids AS ids FROM feats LIMIT 2
""").fetchall())
print("    VARCHAR. But duckdb is the ONE tool here that could act on it in one")
print("    expression once a human has noticed:")
print(db.sql("""
    SELECT string_split_regex(trim(f.properties.types, ','), ',') AS split_types
    FROM feats LIMIT 2
""").fetchall())
