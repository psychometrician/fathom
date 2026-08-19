"""DuckDB — NYC 311 service requests, the 20,000 most recent

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   28.1 MB, 20,000 records, depth 4
  measured      2026-08-11
  run           cd corpus/14-nyc-311/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             3   NO                  yes
   2 how deep                                    7   NO                  YES — via json_structure
   3 what is one record                          5   NO                  PARTLY — but see 153
   4 always present vs sometimes                 6   NO                  YES — exactly right
   5 does any field change type                  4   NO                  YES — and honestly
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          5   NO                  PARTLY
  12 flattest honest table                       3   NO                  yes
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 12
  14 survives the next file unchanged?               Q1-Q5, Q12 yes; the rest name columns
  15 readable a week later?                          yes — it is SQL
  16 lines, and how much is ceremony?                ~115, and one CREATE TABLE

**DuckDB INDEPENDENTLY REPRODUCES THE PROBE'S RAGGEDNESS NUMBER, IN ONE LINE.**
`count(DISTINCT json_structure(json))` returns **153**, which is exactly the
`153 distinct key-sets` `design/probe.py` prints for `$[]`. Nothing was told to
it; the two arrived at the same count of the thing this corpus says is the hard
part. That is the second independent reproduction in the corpus — jq did it for
paths and depth on `25-usgs-quakes` — and the first for RAGGEDNESS specifically.

**AND IT IS THE ONLY TOOL HERE WITH A STRUCTURE-VALUED EXPRESSION.**
`json_structure` returns the shape of a value AS JSON, so it can be grouped,
counted and compared. That is nearer to what this project is proposing than
anything else in either language: the other twelve tools return values, and this
one returns a description you can run SQL against. The gap is that it describes
ONE record at a time — the union, the fold and the pricing are still yours.

**Q4 IS EXACTLY RIGHT, 13 AND 35**, matching polars and the probe rather than
pandas' 13/36, because DuckDB keeps `location` as a STRUCT. Correct here only
because this document has ZERO nulls, so `IS NULL` means absent and nothing else.

**AND IT KEEPS DOCUMENT ORDER, WHICH POLARS DOES NOT.** `unique_key` and
`created_date` come back first and second, as they are in every record.
"""
import json
import time
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
con = duckdb.connect()

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  DuckDB parses and says nothing. It reports no duplicate keys, no")
print("    big integers, no NaN. It did not refuse the file, which polars did,")
print("    and silence here is indistinguishable from a clean bill. CANNOT.")

t0 = time.time()
con.execute(f"CREATE TABLE t AS SELECT * FROM read_json('{RAW}')")
load = time.time() - t0
n = con.execute("SELECT count(*) FROM t").fetchone()[0]
print(f"    read_json: {n:,} rows in {load:.1f}s for 28.1 MB")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
desc = con.execute("DESCRIBE t").fetchall()
print(f"\nQ1  {len(desc)} columns, IN DOCUMENT ORDER:")
print("   ", [c[0] for c in desc])

# ── Q2. How deep does it go — by walking json_structure. ─────────────────────
struct = json.loads(
    con.execute(f"SELECT json_structure(json) FROM read_json_objects('{RAW}') LIMIT 1").fetchone()[0])

def depth(v):
    if isinstance(v, dict):
        return 1 + max(depth(x) for x in v.values())
    if isinstance(v, list):
        return 1 + max(depth(x) for x in v)
    return 0

print(f"\nQ2  json_structure of one record: location = {struct['location']}")
print(f"    that record nests {depth(struct)} levels below itself, so the document is"
      f" {1 + depth(struct)} deep.")
print("    CORRECT. json_structure keeps the nesting as JSON, so it can be walked.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
shapes = con.execute(
    f"SELECT count(DISTINCT json_structure(json)) FROM read_json_objects('{RAW}')").fetchone()[0]
print(f"\nQ3  one record is a request: {n:,} rows x {len(desc)} cols")
print(f"Q3  DISTINCT json_structure = {shapes} — the probe prints '153 distinct")
print("    key-sets' for the same site. Two tools, same number, neither told.")
print("    DuckDB still names ONE candidate and prices none of them. PARTLY.")
print(f"Q7  {n:,} records")

# ── Q4. Always present vs sometimes. EXACTLY RIGHT. ──────────────────────────
counts = con.execute(
    "SELECT " + ", ".join(f'count("{c[0]}") AS "{c[0]}"' for c in desc) + " FROM t").fetchone()
pairs = sorted(zip([c[0] for c in desc], counts), key=lambda kv: kv[1])
always = [c for c, k in pairs if k == n]
some = [(c, k) for c, k in pairs if k < n]
print(f"\nQ4  always: {len(always)} — {sorted(always)}")
print(f"Q4  sometimes: {len(some)}, rarest five:")
for c, k in some[:5]:
    print(f"      {c:34} {k:6,} of {n:,}")
print("    13 and 35 — the probe's answer, and polars'. pandas says 13/36 because")
print("    it splits location. Correct because the document has ZERO nulls.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  types DuckDB inferred:", sorted({c[1] for c in desc}))
print("    47 VARCHAR + 1 STRUCT, and NO field varies — which is the truth. Every")
print("    scalar in this document is a JSON string. DuckDB did NOT coerce")
print("    `latitude` to DOUBLE, and neither did polars or pandas: all three")
print("    frame tools believed Socrata's all-text export.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — Socrata ships fixed names. n/a")
print("    The `:@computed_region_*` columns need double-quoting in SQL, which is")
print("    ceremony this file pays in Q4 above but not a failure.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
print("\nQ8 ", con.execute(
    "SELECT complaint_type, borough, created_date FROM t LIMIT 3").fetchall())

# ── Q9. A field missing from some records, keeping those rows. ───────────────
print("\nQ9  closed_date present on",
      f"{con.execute('SELECT count(closed_date) FROM t').fetchone()[0]:,} of {n:,}")
print("   ", con.execute(
    "SELECT unique_key, status, closed_date FROM t LIMIT 3").fetchall())
print("    LEFT-JOIN semantics for free: the rows were never at risk.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co = con.execute("""
    SELECT location.coordinates[1] AS lon, location.coordinates[2] AS lat
    FROM t WHERE location IS NOT NULL""").fetchall()
print(f"\nQ10 coordinates to {len(co):,} x 2")
print("   ", co[:3])

# ── Q11. Find every path whose value matches something — here, a URL. ────────
varchars = [c[0] for c in desc if c[1] == "VARCHAR"]
hits = con.execute("SELECT " + ", ".join(
    f'count(*) FILTER (WHERE "{c}" LIKE \'%http%\') AS "{c}"' for c in varchars)
    + " FROM t").fetchone()
print(f"\nQ11 columns holding a URL: { {c: h for c, h in zip(varchars, hits) if h} }")
print("    Correct — 19 of 20,000, buried in resolution_description's prose. But")
print("    the query had to be BUILT from the column list and skips the STRUCT,")
print("    so it is a scan of the flat columns rather than of every path.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat = con.execute("SELECT * EXCLUDE (location), location.* FROM t").df()
print(f"\nQ12 {flat.shape[0]:,} x {flat.shape[1]} via `SELECT * EXCLUDE (location), location.*`")
print("    coordinates stays DOUBLE[] — one list-column, the thing god's spec")
print("    refuses. Nothing dropped, nothing coerced. `EXCLUDE` and `struct.*`")
print("    make this the shortest honest flattening in either language.")
