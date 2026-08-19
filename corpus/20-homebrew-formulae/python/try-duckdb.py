"""DuckDB — Homebrew's whole formula index

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
  measured      2026-08-11
  run           cd corpus/20-homebrew-formulae/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             6   NO                  yes
   2 how deep                                    4   NO                  PARTLY
   3 what is one record                          2   NO                  PARTLY
   4 always present vs sometimes                 6   NO                  NO — 20, not 3
  4b the same question via json_keys              9   NO                  YES — 3, correct
   5 does any field change type                 14   NO                  PARTLY, in the TYPE
   6 are any object keys data                   24   NO                  PARTLY — see below
   7 how many records                            1   NO                  yes
   8 three named fields to a table              10   YES                 yes, after quoting
   9 a field missing from some rows              2   YES                 PARTLY
  10 flatten the deepest array                   6   YES                 yes — 557, correct
  11 find every path matching something          9   NO                  PARTLY
  12 flattest honest table                       9   NO                  PARTLY
  13 needed the shape in advance?                    NO for 1, 4, 4b, 5, 6
  14 survives the next file unchanged?               Q1/Q4/Q4b/Q5/Q6 yes
  15 readable a week later?                          Q4b and Q6 need a comment
  16 lines, and how much is ceremony?                ~170, and the SQL is dense
  timing        read_json_auto 0.5s on 29.6 MB. Everything here is under a second

  ══════════════════════════════════════════════════════════════════════════════
  DUCKDB IS THE ONLY TOOL IN THIS CORPUS WITH A TYPE MEANING "THE KEYS ARE DATA",
  AND IT APPLIES IT TO ONE OF TWO IDENTICAL SITES.
  ══════════════════════════════════════════════════════════════════════════════

  `variations` and `bottle.stable.files` are both keyed by Homebrew platform
  names — arm64_sequoia, sonoma, x86_64_linux — in the same document.

      bottle.stable.files   16 keys over 54,619 occurrences  ->  a 16-field STRUCT
      variations            15 keys over  5,295 occurrences  ->  MAP(VARCHAR, …)

  One structure, one document, two verdicts. That is word for word the criticism
  `FINDINGS.md` records against the probe at defect 22 — and DuckDB reaches it
  independently, sharing no code. It is the strongest evidence in this corpus
  that keys-as-data is genuinely hard rather than merely unimplemented.

  Against the probe's four keys-as-data sites they agree on exactly ONE,
  `service.environment_variables`. On the other three DuckDB never reached the
  question: it gave up on the VALUES and stored raw JSON.

  THREE MORE THINGS THE RUN SETTLED:

  Q5 is answered IN THE TYPE and never in words. Where DuckDB cannot unify it
  falls back to `JSON` — 13 columns, 17 positions — and `uses_from_macos JSON[]`
  is exactly the probe's headline polymorphism. The fallback does not
  distinguish "two types here" from "always an empty array, nothing to judge".

  Q4 AND Q4b DISAGREE AND NOTHING SAYS SO. The frame reports 20 columns not
  always filled; `json_keys` over the same file reports 3 keys not always
  present, which is correct. Both are DuckDB, one from a table and one from a
  JSON scalar function, and no part of the tool connects them.

  `desc` IS A SQL RESERVED WORD. `SELECT name, desc, homepage` is a parse
  error on a document whose records have a field called `desc`. No other tool
  in this directory cares what a field is called.
"""
import time
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
con = duckdb.connect()

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  DuckDB parses or refuses. It has no duplicate-key report and no")
print("    big-int report; `read_json_auto` either builds a schema or errors.")
print("    Entry 13 recorded it REFUSING over one zero-length key. Answered CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
t = time.time()
try:
    con.execute(f"CREATE VIEW f AS SELECT * FROM read_json_auto('{RAW}')")
    cols = con.execute("DESCRIBE f").fetchall()
    print(f"\nQ1  read_json_auto: {len(cols)} columns in {time.time()-t:.1f}s")
    for name, typ, *_ in cols[:5]:
        print(f"    {name:24} {typ[:90]}")
except Exception as e:
    print(f"\nQ1  read_json_auto RAISES: {type(e).__name__}: {str(e)[:300]}")
    cols = []

n = con.execute("SELECT count(*) FROM f").fetchone()[0]
print(f"Q7  {n:,} formulae")

# ── Q2. Depth, from the inferred type string. ────────────────────────────────
types = con.execute("SELECT column_type FROM (DESCRIBE f)").fetchall()
deepest = max(types, key=lambda r: r[0].count("STRUCT") + r[0].count("["))
print(f"\nQ2  DuckDB infers a full nested TYPE, so depth is readable from it, by")
print(f"    counting brackets. The deepest column type is {len(deepest[0]):,} characters long.")
print("    That is an answer and it is not a report: nothing prints '8 levels'.")

# ── Q3. What is one record. ──────────────────────────────────────────────────
print(f"\nQ3  a formula: {n:,} rows x {len(cols)} columns. DuckDB names one")
print("    candidate — the top-level array — and prices none.")

# ── Q4. Always present vs sometimes. THE MANUFACTURED-NULL TEST. ─────────────
print("\nQ4  counting non-null per column, the frame's answer:")
sel = ", ".join(f'count("{c[0]}") AS "{c[0]}"' for c in cols)
counts = con.execute(f"SELECT {sel} FROM f").fetchdf().iloc[0].to_dict()
some = {k: int(v) for k, v in counts.items() if v < n}
print(f"Q4  {len(some)} of {len(cols)} columns are not filled on every row")
print(f"    {dict(sorted(some.items(), key=lambda kv: -kv[1])[:8])}")
print("    The document has 3 sometimes-ABSENT fields and 17 always-present-")
print("    but-null ones. Read the number above against 20.")

# ── The json_objects route, which entry 17 showed gives a different answer. ──
# NOTE `format='array'` ALREADY yields one row per element. The first draft
# wrapped it in json_transform_strict and got
#   Invalid Input Error: Expected ARRAY, but got OBJECT
# because it was unnesting an array that had already been unnested.
print("\nQ4b the OTHER route — read the file as raw JSON and ask about KEYS:")
t = time.time()
kdf = con.execute(f"""
SELECT k, count(*) AS present
FROM (SELECT unnest(json_keys(json)) AS k
      FROM read_json_objects('{RAW}', format='array'))
GROUP BY k ORDER BY present DESC
""").fetchdf()
absent = kdf[kdf["present"] < n]
print(f"    {len(kdf)} distinct root keys in {time.time()-t:.1f}s")
print(f"    keys NOT PRESENT on every record: {absent.to_dict('records')}")
print(f"    THREE, against the frame's {len(some)}. json_keys counts PRESENCE, so a")
print("    key written as null is present. This is entry 15's discriminator and")
print("    DuckDB HAS BOTH HALVES — but only by leaving the relational world:")
print("    one answer comes from a table, the other from a JSON scalar function,")
print("    and nothing connects them or says they disagree.")

# ── Q5. Does any field change type? IT ANSWERS, IN THE TYPE, WITHOUT SAYING SO ─
import re
print("\nQ5  DuckDB must unify types to build a column. WHERE IT CANNOT, IT FALLS")
print("    BACK TO `JSON`, AND THAT FALLBACK IS A POLYMORPHISM REPORT NOBODY")
print("    CALLS ONE. Every position in the schema typed JSON:")
json_cols = [(c, t) for c, t, *_ in cols if re.search(r"\bJSON\b", t)]
tot = sum(len(re.findall(r"\bJSON\b", t)) for _, t in json_cols)
for c, t in json_cols:
    print(f"    {c:26} {t[:78]}")
print(f"    {len(json_cols)} columns, {tot} JSON positions, against the probe's NINE sites.")
print("    `uses_from_macos JSON[]` is exactly the probe's headline: strings on")
print("    1,163 formulae, objects on 632. `service.run JSON` is another of the")
print("    nine. THE SIGNAL IS REAL AND IT IS UNLABELLED — several of the rest")
print("    are columns that are always EMPTY arrays, where the element type is")
print("    unknown rather than conflicting, and the type does not distinguish")
print("    'two types here' from 'no elements to judge'.")

# ── Q6. Are any object keys actually data? DUCKDB HAS A TYPE FOR IT. ─────────
print("\nQ6  DUCKDB IS THE ONLY TOOL IN THIS DIRECTORY WITH A TYPE THAT MEANS")
print("    'THE KEYS ARE DATA'. It chooses between STRUCT and MAP, per position:")
for c, t, *_ in cols:
    for m in re.finditer(r"MAP\(", t):
        print(f"    MAP     {c:24} …{t[m.start():m.start()+64]}")
bottle = [t for c, t, *_ in cols if c == "bottle"][0]
print(f"    STRUCT  {'bottle':24} {bottle[:64]}…")
print("\n    Against the probe's FOUR keys-as-data sites, they agree on ONE:")
print("      $[].service.environment_variables   probe: DATA   duckdb: MAP   AGREE")
print("      $[].uses_from_macos[]               probe: DATA   duckdb: JSON[]")
print("      $[].head_dependencies.uses_from_macos[]              duckdb: JSON[]")
print("      $[].variations.<key>.head_dependencies.uses_from_macos[]  duckdb: JSON[]")
print("    On the three it misses, DuckDB did not decide the keys were schema —")
print("    it gave up on the VALUES and stored raw JSON, so the key question")
print("    never came up. One agreement out of four, by two unrelated routes.")
t = time.time()
plat = con.execute(f"""
SELECT count(DISTINCT k) AS keys, count(*) AS copies FROM (
  SELECT unnest(json_keys(json_extract(json, '$.bottle.stable.files'))) AS k
  FROM read_json_objects('{RAW}', format='array'))
""").fetchone()
varn = con.execute(f"""
SELECT count(DISTINCT k) AS keys, count(*) AS copies FROM (
  SELECT unnest(json_keys(json_extract(json, '$.variations'))) AS k
  FROM read_json_objects('{RAW}', format='array'))
""").fetchone()
print(f"\n    bottle.stable.files  {plat[0]:>3} platform keys over {plat[1]:>6,} occurrences -> STRUCT")
print(f"    variations           {varn[0]:>3} platform keys over {varn[1]:>6,} occurrences -> MAP")
print("    TWO STRUCTURALLY IDENTICAL KEYED COLLECTIONS, KEYED BY THE SAME")
print("    PLATFORM NAMES, IN ONE DOCUMENT, AND DUCKDB TYPES THEM OPPOSITELY.")
print("    `variations` becomes MAP(VARCHAR, MAP(VARCHAR, JSON)) — keys as data.")
print("    `bottle.stable.files` becomes a 16-field STRUCT — keys as schema.")
print("    The probe DECLINES BOTH, as vocabularies rather than data, and says so")
print("    in one line each. This is defect 22's own criticism — *one structure,")
print("    one document, two verdicts* — arrived at independently by a tool that")
print("    shares no code with the probe, which is the strongest evidence in this")
print("    corpus that the distinction is genuinely hard and not merely unimplemented.")

# ── Q8. Three named fields into a table. AND A RESERVED WORD. ────────────────
# FIRST DRAFT WAS A PARSE ERROR: `SELECT name, desc, homepage` fails with
#   Parser Error: syntax error at or near "desc"
# because `desc` is SQL's DESCENDING keyword. A JSON field name is not a SQL
# identifier, and this document has one that collides.
try:
    con.execute("SELECT name, desc, homepage FROM f LIMIT 2").fetchdf()
    print("\nQ8  unquoted `desc` parsed — rewrite this note")
except Exception as e:
    print(f"\nQ8  unquoted: {type(e).__name__}: {' '.join(str(e).split())[:70]}")
    print('    `desc` is a SQL reserved word. It must be written "desc".')
t8 = con.execute('SELECT name, "desc", homepage FROM f LIMIT 2').fetchdf()
print(t8.to_string())
print("    No other tool in this directory cares what a field is called. This is")
print("    the cost of a query language with its own grammar meeting names that")
print("    were never chosen to satisfy one.")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
q9 = con.execute("SELECT count(*) FILTER (WHERE executables IS NOT NULL), count(*) FROM f").fetchone()
print(f"\nQ9  executables non-null on {q9[0]:,} of {q9[1]:,}; LEFT semantics keep the row")
print("    185 of those nulls are ABSENT keys and SQL has no word for the difference.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
t = time.time()
try:
    q10 = con.execute("""
        SELECT count(*) FROM (
          SELECT name, unnest(r.resolves) AS res
          FROM (SELECT name, unnest(patches) AS r FROM f) WHERE r.resolves IS NOT NULL)
    """).fetchone()
    print(f"\nQ10 patches[].resolves[] -> {q10[0]:,} rows, {time.time()-t:.1f}s")
    print("    unnest twice, and `name` survives both. The true count is 557.")
except Exception as e:
    print(f"\nQ10 RAISES: {type(e).__name__}: {str(e)[:250]}")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
t = time.time()
urls = con.execute(f"""
SELECT count(*) AS hits, count(DISTINCT p) AS paths FROM (
  SELECT unnest(json_keys(json, '$')) AS p FROM read_json_objects('{RAW}', format='array'))
""").fetchone() if False else None
print("\nQ11 DuckDB has no `paths(...)`. json_keys walks ONE level; reaching every")
print("    string in the document means a recursive CTE over json_each, written")
print("    by hand. The column-wise version answers a smaller question:")
strcols = [c[0] for c in cols if c[1] == "VARCHAR"]
if strcols:
    naive = " + ".join(f"CASE WHEN \"{c}\" LIKE 'http%' THEN 1 ELSE 0 END" for c in strcols)
    strict = " + ".join(f"CASE WHEN regexp_matches(\"{c}\", '^https?://') THEN 1 ELSE 0 END"
                        for c in strcols)
    hits = con.execute(f"SELECT sum({naive}), sum({strict}) FROM f").fetchone()
    print(f"    over {len(strcols)} VARCHAR columns: {hits[0]:,} LIKE 'http%', "
          f"{hits[1]:,} matching ^https?://")
    print(f"    the {hits[0]-hits[1]:,} difference is exactly 15 formulae NAMED http* seen in")
    print("    2 columns each — `name` and `full_name`. Same trap as every tool here.")
print("    PARTLY: a column scan, not a path scan. Only 16 of 61 columns are")
print("    VARCHAR, so every URL inside a STRUCT or LIST is outside this query.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print(f"\nQ12 {n:,} x {len(cols)} with STRUCT, LIST and MAP columns intact — which is")
print("    honest and is not flat. `SELECT struct.*` expands one level:")
for qq in ("SELECT versions.* FROM f LIMIT 0",
           "SELECT urls.*, versions.* FROM f LIMIT 0"):
    w = con.execute(qq).fetchdf()
    dup = sorted({c for c in w.columns if list(w.columns).count(c) > 1})
    print(f"    {qq[7:-13]:26} -> {list(w.columns)}  dups={dup}")
print("    ON THIS DOCUMENT DUCKDB RENAMES ON COLLISION — `stable_1`, `head_1` —")
print("    and returns no duplicate names at all. Entry 15 recorded `struct.*`")
print("    silently returning 19 DUPLICATES on `15-github-issues`. The two runs")
print("    used different queries on different documents and are recorded as")
print("    measured; a session wanting one rule should re-run both side by side.")
print("    Either way the flattening is ONE LEVEL, and this document is 8 deep.")
