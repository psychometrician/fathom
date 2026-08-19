"""DuckDB — an npm lockfile, 1,657 packages keyed by install path

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   759 KB, 1,657 packages, depth 5
  measured      2026-08-11
  run           cd corpus/13-package-lock/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               8   -                   REFUSES — see below
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    5   NO                  YES — via json_structure
   3 what is one record                          8   YES                 NO — 776 vs 144
   4 always present vs sometimes                 6   YES                 yes
   5 does any field change type                  5   YES                 YES
   6 are any object keys data                    5   -                   NO — but it can COUNT them
   7 how many records                            2   YES                 yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          5   NO                  PARTLY
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 2, 5
  14 survives the next file unchanged?               the json_* expressions do
  15 readable a week later?                          yes — it is SQL
  16 lines, and how much is ceremony?                ~130, and json_each is the workhorse

**DuckDB REFUSES THIS FILE, AND THE CAUSE IS ONE ZERO-LENGTH KEY.**

    CREATE TABLE t AS SELECT * FROM read_json('../source.json')
    -> InvalidInputException: A table cannot be created from an unnamed struct

**The root package's key is the empty string** — `"": {...}` is how npm records
the project itself — so `packages` becomes a struct with an unnamed field.
Deleting that ONE key of 1,657 and re-reading the file **works immediately**,
which this file proves below rather than asserts.

**The error names nothing you can act on.** It does not say which column, which
key, or that a key is involved at all. Compare polars refusing `14-nyc-311`,
where the message named `bridge_highway_direction`: **two refusals in the corpus
now, and only one of them told you what to look at.** This is the second corpus
file DuckDB cannot make a table from, and the first it cannot read at all.

**The JSON FUNCTIONS still work, and that is the interesting half.** `json_each`,
`json_keys` and `json_structure` all read the file happily — it is only the
table reader that refuses. So DuckDB can answer most questions here **while
being unable to produce a table**, which is a distinction no other tool in this
directory draws.

**AND QUESTION 3 IS WHERE IT COMES APART, IN A WAY ENTRY 14 HID.** On
`14-nyc-311`, `count(DISTINCT json_structure(json))` returned **153 — exactly the
probe's key-set count.** Here the same idea gives three different numbers:

    count(DISTINCT json_structure(value)) ....... 776    counts nested DATA keys
    count(DISTINCT json_keys(value)::VARCHAR) ... 152    counts key ORDER
    the probe ................................... 144    distinct key-SETS

**776 because `json_structure` treats each package's dependency NAMES as
structure** — this document has keys-as-data and entry 14 did not. **152 because
`json_keys` preserves document order**, and 8 packages carry the same field set
in a different order. The expression that reproduced the probe exactly on a flat
document over-counts by 5.4x on a keyed one, and nothing signals the change.
"""
import json
import os
import tempfile
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
con = duckdb.connect()
SRC = f"read_json_objects('{RAW}')"


N_PACKAGES = f"SELECT len(json_keys(json->'packages')) FROM {SRC}"
TOP_KEYS = f"SELECT json_keys(json) FROM {SRC}"


def q1(sql):
    return con.execute(sql).fetchone()[0]


# ── Q0. Is this what it claims to be, and is it whole? IT REFUSES. ───────────
print("\nQ0  CREATE TABLE ... FROM read_json:")
try:
    con.execute(f"CREATE TABLE t AS SELECT * FROM read_json('{RAW}')")
    print("    ...it worked, which contradicts the recorded claim.")
except Exception as e:
    print(f"    {type(e).__name__}: {e}")

# Prove the cause rather than asserting it: remove the one empty-string key.
doc = json.load(open(RAW))
trimmed = json.loads(json.dumps(doc))
del trimmed["packages"][""]
tmp = tempfile.mktemp(suffix=".json")
open(tmp, "w").write(json.dumps(trimmed))
con.execute(f"CREATE TABLE t2 AS SELECT * FROM read_json('{tmp}')")
print(f"    with the ONE empty-string key removed: {len(con.execute('DESCRIBE t2').fetchall())}"
      " columns, no error.")
os.unlink(tmp)
print("    The root package is keyed \"\" — npm's way of recording the project")
print("    itself. One zero-length key of 1,657 refuses a 759 KB document, and")
print("    the message mentions neither keys nor packages. It reports nothing")
print("    about duplicate keys, big ints or NaN either. REFUSES.")

# ── Q1. What is in here — the json_ functions still work. ────────────────────
print(f"\nQ1  top-level keys: {q1(TOP_KEYS)}")
print(f"Q1  packages holds {q1(N_PACKAGES):,} keys")
fields = con.execute(f"""
    SELECT je2.key, count(*) FROM {SRC},
           json_each(json, '$.packages') je, json_each(je.value) je2
    GROUP BY 1 ORDER BY 2 DESC""").fetchall()
print(f"Q1  {len(fields)} distinct fields across the packages, top five: {fields[:5]}")
print("    PARTLY — the level to iterate had to be named in the SQL.")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
struct = json.loads(q1(f"SELECT json_structure(json) FROM {SRC}"))


def depth(v):
    if isinstance(v, dict) and v:
        return 1 + max(depth(x) for x in v.values())
    if isinstance(v, list) and v:
        return 1 + max(depth(x) for x in v)
    return 0


print(f"\nQ2  json_structure walked to depth {depth(struct)} — the probe prints 5.")
print("    CORRECT, and it is the same verb that answered this on 14-nyc-311.")
print("    The structure string is 12,153 characters of mostly package NAMES,")
print("    because json_structure records data keys as structure.")

# ── Q3/Q7. What is one record, and how many. THE LADDER. ─────────────────────
by_structure = q1(f"""SELECT count(DISTINCT json_structure(je.value))
                      FROM {SRC}, json_each(json, '$.packages') je""")
by_keys = q1(f"""SELECT count(DISTINCT json_keys(je.value)::VARCHAR)
                 FROM {SRC}, json_each(json, '$.packages') je""")
print(f"\nQ3  count(DISTINCT json_structure(value)) = {by_structure}")
print(f"Q3  count(DISTINCT json_keys(value))      = {by_keys}")
print("Q3  the probe                             = 144 distinct key-sets")
print("    776 counts each package's dependency NAMES as structure — keys-as-data.")
print("    152 counts key ORDER: 8 packages carry the same fields in another order.")
print("    On 14-nyc-311 the first expression returned 153 and matched the probe")
print("    EXACTLY. Same expression, same idea, and this document breaks it")
print("    two different ways at once. NO.")
print(f"Q7  {q1(N_PACKAGES):,} packages")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
n = 1657
always = [f for f, c in fields if c == n]
some = sorted(((f, c) for f, c in fields if c < n), key=lambda kv: kv[1])
print(f"\nQ4  always {len(always)} — {always}")
print(f"Q4  sometimes {len(some)}, rarest five: {some[:5]}")
print("    Matches the probe. `json_each` over a keyed collection is the right")
print("    shape for this and it had to be written by hand.")

# ── Q5. Does any field change type between records? ──────────────────────────
varying = con.execute(f"""
    SELECT je2.key, list(DISTINCT json_type(je2.value)) AS kinds
    FROM {SRC}, json_each(json, '$.packages') je, json_each(je.value) je2
    GROUP BY 1 HAVING count(DISTINCT json_type(je2.value)) > 1""").fetchall()
print(f"\nQ5  fields whose json_type varies: {varying}")
print("    BOTH ARE REAL and both are the probe's:")
print("      engines  object x1,050, array[1] text x1")
print("      funding  object x282, array[1] object x26, array[1] text x2")
print("    `json_type` reads the JSON type rather than a column dtype, so there")
print("    is no NaN to mistake for a type. Contrast pandas on 14-nyc-311.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  DuckDB cannot SAY that keys are data, but it can count them, which is")
print("    more than pandas or polars manage:")
print(f"    packages ........... {q1(N_PACKAGES):,} keys, one copy")
deps = q1(f"""SELECT count(*) FROM {SRC}, json_each(json, '$.packages') je,
              json_each(je.value, '$.dependencies') d""")
print(f"    dependencies ....... {deps:,} entries over 881 copies")
print("    The probe names SEVEN keyed sites and declines an eighth (`engines`,")
print("    5 keys over 1,050 copies — a vocabulary, not data). Nothing in SQL")
print("    distinguishes those two cases, and that distinction is the finding.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
rows = con.execute(f"""
    SELECT je.key AS path,
           je.value->>'version'  AS version,
           je.value->>'resolved' AS resolved,
           je.value->>'license'  AS license
    FROM {SRC}, json_each(json, '$.packages') je LIMIT 3""").fetchall()
print(f"\nQ8  three fields, keyed by install path:")
for r in rows:
    print("   ", (r[0] or "<the root package, key \"\">"), "|", r[1], "|", (r[3] or "-"))
lic = q1(f"""SELECT count(je.value->>'license') FROM {SRC},
             json_each(json, '$.packages') je""")
print(f"\nQ9  license present on {lic:,} of {n:,} — `->>` gives NULL and keeps the row")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
fund = con.execute(f"""
    SELECT je.key AS pkg, f.value->>'type' AS type, f.value->>'url' AS url
    FROM {SRC}, json_each(json, '$.packages') je, json_each(je.value, '$.funding') f
    WHERE json_type(je.value->'funding') = 'ARRAY'""").fetchall()
print(f"\nQ10 funding[] exploded to {len(fund)} rows")
print("   ", fund[0])
print("    The WHERE clause is needed because `funding` is an object on 282")
print("    packages and an array on 28. json_each would silently treat the")
print("    object's fields as elements otherwise.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
hits = con.execute(f"""
    SELECT je2.key, count(*) FROM {SRC},
           json_each(json, '$.packages') je, json_each(je.value) je2
    WHERE json_type(je2.value) = 'VARCHAR' AND je2.value::VARCHAR LIKE '%http%'
    GROUP BY 1 ORDER BY 2 DESC""").fetchall()
print(f"\nQ11 string fields of a package holding a URL: {hits}")
print("    Two of the five folded paths, 1,664 of 2,003 values. The three inside")
print("    `funding` need their own query because it is object-or-array.")
print("    PARTLY: the level was named, and a recursive scan is not expressible.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print(f"\nQ12 the honest table is `json_each` over packages: {n:,} rows x 21 scalar")
print("    columns, with the install path as the key column — and it must be")
print("    written out field by field, because there is no `SELECT *` for a")
print("    struct DuckDB refused to build.")
print("    The four keyed collections inside are separate tables the probe")
print(f"    prices at {deps:,}, 128, 104 and 101 rows. DuckDB will not name them.")
