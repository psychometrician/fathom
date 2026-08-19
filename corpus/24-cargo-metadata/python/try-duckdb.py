"""DuckDB — cargo metadata for this repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   27 KB, 8 packages, depth 8
  measured      2026-08-11
  run           cd corpus/24-cargo-metadata/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             8   YES                 PARTLY
   2 how deep                                    3   NO                  PARTLY
   3 what is one record                          4   YES                 one of nine
   4 always present vs sometimes                 8   NO                  YES via json_keys
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                   16   NO                  MAP OR STRUCT — SEE BELOW
   7 how many records                             2  NO                  yes
   8 three named fields to a table                4 YES                 yes, and one needs quoting
   9 a field missing from some rows                2 YES                 PARTLY
  10 flatten the deepest array                     5 YES                 yes
  11 find every path matching something            4 NO                  PARTLY
  12 flattest honest table                         4 NO                  yes
  13 needed the shape in advance?                    yes
  14 survives the next file unchanged?               DEPENDS ON WHICH TYPE IT PICKED
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~100

  ══════════════════════════════════════════════════════════════════════════════
  THE REMATCH OF ENTRY 20's HEADLINE, ON A DOCUMENT WHERE THE PROBE SAYS
  "KEYS THAT ARE DATA" OUTRIGHT.
  ══════════════════════════════════════════════════════════════════════════════

  Entry 20 found DuckDB typing two structurally identical keyed collections
  oppositely — `variations` as MAP, `bottle.stable.files` as a STRUCT — and that
  was recorded as defect 22's own criticism reached independently.

  Here the probe calls `$.packages[].features` KEYS THAT ARE DATA outright: 28
  feature names over 8 packages, 23 appearing once. If DuckDB's MAP means what
  entry 20 suggested, this is the site it should choose it for.

  IT CHOOSES STRUCT. So the MAP/STRUCT decision does NOT track keys-as-data:
  three keyed collections across two documents, two verdicts, no rule between
  them.

  AND THE TYPING DESTROYS THE EVIDENCE THE PROBE JUDGED ON. A STRUCT has every
  field on every row, so counting through the typed column and through the raw
  JSON give different documents:

      through the TYPED column   28 names, 224 occurrences,  0 appearing once
      through the RAW JSON       28 names,  40 occurrences, 23 appearing once

  **The probe called this site data BECAUSE 23 of 28 names occur in exactly one
  package. Ask the same question of the table and every name occurs in all
  eight.** One tool, two routes, and only the second can see the property. The
  open vocabulary was not lost in the answer — it was lost in the schema.
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
print(f"\nQ1  read_json_auto -> {len(ec)} columns, one row: "
      f"{[c[0] for c in ec]}")
print("    THE ENVELOPE. `packages` is a LIST(STRUCT) in a cell.")
con.execute("CREATE VIEW pkgs AS SELECT unnest(packages) AS p FROM env")
n = con.execute("SELECT count(*) FROM pkgs").fetchone()[0]
ptype = [t for c, t, *_ in ec if c == "packages"][0]
print(f"Q1  unnest(packages) -> {n} packages")
print(f"\nQ2  the `packages` type is {len(ptype):,} characters of nested SQL type;")
print("    depth is readable from the brackets and never reported. Probe: 8.")

# ── Q6. THE REMATCH. ────────────────────────────────────────────────────────
# The first draft regex-searched the packages TYPE STRING for `features` and
# found a DEPENDENCY's `features BOOLEAN` instead of the package's. `typeof` on
# the column is the honest way to ask.
ftype = con.execute("SELECT typeof(p.features) FROM pkgs LIMIT 1").fetchone()[0]
print("\nQ6  THE PROBE CALLS $.packages[].features KEYS THAT ARE DATA.")
print(f"    DuckDB typed it: {ftype[:100]}…")
is_map = ftype.startswith("MAP")
print(f"    IS IT A MAP? {is_map}")
if is_map:
    print("    YES — entry 20's reading holds and DuckDB agrees with the probe.")
else:
    nf = ftype.count(" VARCHAR") + ftype.count(" JSON") + ftype.count("[]")
    print("    NO — a STRUCT with one field per FEATURE NAME, so the dtype of")
    print("    this table is this repository's dependency graph.")
    print("    ══ AND IT DESTROYS THE SIGNAL THE PROBE USED. ══")
    print("    A STRUCT has every field on every row, so after typing, all eight")
    print("    packages carry all 28 feature keys and most are null. The probe")
    print("    called this site data BECAUSE 23 of 28 names occur in exactly one")
    print("    package; ask DuckDB the same question through `json_keys` and")
    print("    every name occurs in all eight. THE EVIDENCE FOR THE VERDICT IS")
    print("    GONE BY THE TIME THE TABLE EXISTS.")
    print("    ENTRY 20 FOUND DUCKDB CHOOSING MAP FOR `variations` AND STRUCT FOR")
    print("    `bottle.stable.files`, two identical sites. Adding this one, that")
    print("    is three keyed collections and two verdicts with no rule between")
    print("    them — so the MAP/STRUCT choice does NOT track keys-as-data.")

feat = con.execute("""
SELECT count(DISTINCT k) AS names, count(*) AS occurrences FROM
  (SELECT unnest(json_keys(json_extract(to_json(p), '$.features'))) AS k FROM pkgs)
""").fetchone()
once = con.execute("""
SELECT count(*) FROM (
  SELECT k, count(*) AS n FROM
    (SELECT unnest(json_keys(json_extract(to_json(p), '$.features'))) AS k FROM pkgs)
  GROUP BY k HAVING count(*) = 1)
""").fetchone()[0]
print(f"Q6  through the TYPED column: {feat[0]} names over {feat[1]} occurrences,"
      f" {once} appearing once")
print(f"    {feat[1]} is {feat[0]} x {n} — every package carrying every name.")
raw = con.execute(f"""
SELECT count(DISTINCT k) AS names, count(*) AS occurrences FROM
  (SELECT unnest(json_keys(json_extract(j, '$.features'))) AS k FROM
    (SELECT unnest(json_transform_strict(json_extract(json, '$.packages'), '["JSON"]')) AS j
     FROM read_json_objects('{RAW}')))
""").fetchone()
rawonce = con.execute(f"""
SELECT count(*) FROM (SELECT k, count(*) AS c FROM
  (SELECT unnest(json_keys(json_extract(j, '$.features'))) AS k FROM
    (SELECT unnest(json_transform_strict(json_extract(json, '$.packages'), '["JSON"]')) AS j
     FROM read_json_objects('{RAW}'))) GROUP BY k HAVING count(*) = 1)
""").fetchone()[0]
print(f"Q6  through the RAW JSON:     {raw[0]} names over {raw[1]} occurrences,"
      f" {rawonce} appearing once")
print("    THE SAME TOOL, TWO ROUTES, AND ONLY THE SECOND CAN SEE THE PROPERTY")
print("    THE PROBE JUDGED ON. Reading the document gives the open vocabulary;")
print("    reading the TABLE gives a closed one, because typing manufactured it.")

# ── Q4/Q5/Q7. ───────────────────────────────────────────────────────────────
k = con.execute("""
SELECT k, count(*) AS present,
       count(*) FILTER (WHERE json_type(json_extract(j, '$.' || k)) = 'NULL') AS nulls
FROM (SELECT unnest(json_keys(j)) AS k, j FROM (SELECT to_json(p) AS j FROM pkgs))
GROUP BY k HAVING nulls > 0 ORDER BY nulls DESC, k""").fetchdf()
print(f"\nQ4  package keys with any null:\n{k.to_string(index=False)}")
print(f"    every key is PRESENT on all {n} packages, so every hole is a WRITTEN")
print(f"    null and {(k['nulls'] == n).sum()} keys are nothing else.")
print("\nQ5  every column unified; the probe reports NO type change, and jq")
print("    confirms zero once `an empty array is not a type` is applied.")
wm = con.execute("SELECT len(workspace_members), len(resolve.nodes) FROM env").fetchone()
print(f"\nQ7  {n} packages, {wm[0]} workspace members, {wm[1]} resolve nodes")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
print("\nQ8  and one of the three names needs quoting:")
try:
    con.execute("SELECT p.name, p.version, p.edition FROM pkgs LIMIT 1").fetchdf()
    print("    unquoted `version` parsed: OK — it is not reserved in DuckDB")
except Exception as e:
    print(f"    unquoted: {type(e).__name__}: {' '.join(str(e).split())[:60]}")
t8 = con.execute('SELECT p.name, p."version", p.edition FROM pkgs LIMIT 2').fetchdf()
print(t8.to_string(index=False))
d = con.execute("SELECT count(*) FILTER (WHERE p.description IS NOT NULL) FROM pkgs").fetchone()[0]
print(f"\nQ9  `description` non-null on {d} of {n}; the row is kept either way")
tg = con.execute("SELECT count(*) FROM (SELECT unnest(p.targets) AS t FROM pkgs)").fetchone()[0]
dk = con.execute("""SELECT count(*) FROM (
  SELECT unnest(d.dep_kinds) AS k FROM
    (SELECT unnest(nd.deps) AS d FROM (SELECT unnest(resolve.nodes) AS nd FROM env)))""").fetchone()[0]
print(f"\nQ10 targets -> {tg} rows; the DEEPEST array is")
print(f"    resolve.nodes[].deps[].dep_kinds[] at {dk} rows, THREE unnests deep,")
print("    and it is NOT under `packages` — a different root branch entirely.")
u = con.execute("""SELECT count(*) FROM pkgs
                   WHERE regexp_matches(p.repository, '^https?://')""").fetchone()[0]
print(f"\nQ11 no `paths(...)`. A named column: `repository` matches on {u} of {n}.")
print("    jq reports 5 distinct URL PATHS; two are under")
print("    `metadata.release.pre-release-replacements[]`.")
print(f"\nQ12 {n} x 24 with STRUCT and LIST columns intact. Expanding `features`")
print(f"    would add {feat[0]} columns whose names are DATA. THE HONEST TABLE IS")
print("    NARROWER THAN THE FLAT ONE, and the difference is question 6.")
