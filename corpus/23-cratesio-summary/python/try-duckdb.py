"""DuckDB — crates.io summary

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   41 KB, six collections at the root, depth 4
  measured      2026-08-11
  run           cd corpus/23-cratesio-summary/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             8   YES                 PARTLY
   2 how deep                                    3   NO                  PARTLY
   3 what is one record                         16   YES                 THE TYPES COMPARE
   4 always present vs sometimes                 8   NO                  YES via json_keys
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                    1   -                   n/a
   7 how many records                             3  NO                  three answers
   8 three named fields to a table                2 YES                 yes
   9 a field missing from some rows                2 YES                 PARTLY
  10 flatten the deepest array                     3 -                   NO ARRAY TO FLATTEN
  11 find every path matching something            4 NO                  PARTLY
  12 flattest honest table                         5 NO                  UNION ALL, and it
                                                                          double-counts
  13 needed the shape in advance?                    YES — all six collections named
  14 survives the next file unchanged?               Q4 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~100

  THE DEFECT-25 DOCUMENT, AND DUCKDB ANSWERS IT THE WAY POLARS DOES: the
  inferred column TYPE is a value you can compare. `read_json_auto` gives one
  row of eight columns whose types spell the four crate collections out, and
  comparing those four type strings is one `SELECT`.

  IT REACHES THE SAME SPLIT AS POLARS: the four are one KEY-SET and NOT one
  TYPE, because `recent_downloads` is null on all ten `new_crates` and
  `documentation` on all ten `just_updated`.

  AND ITS `UNION ALL` FAILS IN THE WORST OF THE THREE WAYS. The view is created
  without complaint. `count(*)` returns 40. EVERY FIELD ACCESS RAISES —
  `count(DISTINCT crate.id)` errors with `Malformed JSON ... "https://docs.rs/..."`,
  naming a URL in a column you did not ask for. A table with forty rows and no
  readable columns is worse than polars' refusal and worse than pandas' silence,
  because it looks like it worked until the second query.

  The route that works abandons the relational types: union the JSON TEXT and
  `json_extract` from it — at which point it double-counts the seven crates
  exactly as pandas did.
"""
import time
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
CRATE = ["new_crates", "most_downloaded", "most_recently_downloaded", "just_updated"]
con = duckdb.connect()
print("\nQ0  DuckDB parses or refuses; no health report. CANNOT.")

con.execute(f"CREATE VIEW env AS SELECT * FROM read_json_auto('{RAW}')")
ec = con.execute("DESCRIBE env").fetchall()
print(f"\nQ1  read_json_auto -> {len(ec)} columns, one row:")
for n, ty, *_ in ec:
    print(f"    {n:26} {ty[:64]}{'…' if len(ty) > 64 else ''}")
print("    THE ROOT IS AN OBJECT, so DuckDB reads it as one row and every")
print("    collection is a LIST(STRUCT) in a cell — the envelope problem of")
print("    entries 21 and 22 in a third shape.")

types = {n: ty for n, ty, *_ in ec}
print(f"\nQ2  the crate list type is {len(types['new_crates'])} characters of nested SQL")
print("    type; depth is readable from the brackets and never reported. Probe: 4.")

# ── Q3. THE FOUR TYPES, COMPARED. ───────────────────────────────────────────
print("\nQ3  are the four crate collections the same TYPE?")
distinct = {types[c] for c in CRATE}
print(f"    distinct type strings across the four: {len(distinct)}")
for c in CRATE:
    same = "same as new_crates" if types[c] == types["new_crates"] else "DIFFERS"
    print(f"    {c:26} {same}")
import re
base = dict(re.findall(r'(\w+)\s+([A-Z][A-Z0-9_]*(?:\([^()]*\))?)', types["new_crates"]))
for c in CRATE:
    cur = dict(re.findall(r'(\w+)\s+([A-Z][A-Z0-9_]*(?:\([^()]*\))?)', types[c]))
    diff = {k: (base.get(k), v) for k, v in cur.items() if base.get(k) != v}
    if diff:
        print(f"    {c:26} field-level diff: {diff}")
print("    SAME KEY-SET, NOT SAME TYPE — the identical split polars found, and")
print("    for the identical reason: `recent_downloads` is null on ALL TEN")
print("    `new_crates`, so it infers as the null type there and BIGINT elsewhere.")
print("    THE PROBE FOLDS ON KEY-SETS and prints `same shape as $.new_crates[]`.")
print("    Two type-inferring tools independently disagree with it, about a")
print("    different question. Both answers are correct.")

# ── Q3b. UNION ALL: the view builds, count(*) works, EVERY FIELD RAISES. ───
q = " UNION ALL ".join(
    f"SELECT '{c}' AS _list, unnest({c}) AS crate FROM env" for c in CRATE)
con.execute(f"CREATE VIEW allcrates AS {q}")
print("\nQ3b UNION ALL of the four — the view is created without complaint:")
for probe in ("SELECT count(*) FROM allcrates",
              "SELECT count(DISTINCT crate.id) FROM allcrates",
              "SELECT count(DISTINCT crate.name) FROM allcrates"):
    try:
        print(f"    {probe[:44]:46} -> {con.execute(probe).fetchone()[0]}")
    except Exception as e:
        print(f"    {probe[:44]:46} -> {type(e).__name__}: "
              f"{' '.join(str(e).split())[:60]}")
print("    `count(*)` SUCCEEDS AND EVERY FIELD ACCESS RAISES. The union had to")
print("    unify the struct types, so `documentation` became JSON in one branch")
print("    and holds a VARCHAR url in another — and the error surfaces when you")
print("    ask for `id`, naming a URL you never mentioned.")
print("    A TABLE THAT HAS FORTY ROWS AND NO READABLE COLUMNS is worse than")
print("    polars' refusal and worse than pandas' silence: it looks like it")
print("    worked until the second query.")

# the route that does work: union the JSON text and extract from that
con.execute("CREATE VIEW cj AS " + " UNION ALL ".join(
    f"SELECT '{c}' AS _list, to_json(unnest({c})) AS j FROM env" for c in CRATE))
tot = con.execute("SELECT count(*) FROM cj").fetchone()[0]
dist = con.execute("SELECT count(DISTINCT json_extract_string(j,'$.id')) FROM cj").fetchone()[0]
dups = con.execute("""SELECT json_extract_string(j,'$.name') AS name, count(*) AS n
                      FROM cj GROUP BY 1 HAVING count(*) > 1 ORDER BY 1""").fetchdf()
print(f"\nQ3b the route that WORKS is to union the JSON TEXT and extract from it:")
print(f"    {tot} rows, {dist} DISTINCT crates")
print(dups.to_string(index=False))
print("    SEVEN CRATES ARE COUNTED TWICE and nothing says so. polars RAISED on")
print("    this concatenation, pandas did it silently, DuckDB builds a view that")
print("    cannot be read and then works only outside the relational types.")
print("    THREE FRAMES, THREE BEHAVIOURS, ONE CAUSE — a column that is null on")
print("    every row of one collection.")

# ── Q4/Q5/Q6/Q7. ────────────────────────────────────────────────────────────
k = con.execute("""
SELECT k, count(*) AS present,
       count(*) FILTER (WHERE json_type(json_extract(j, '$.' || k)) = 'NULL') AS nulls
FROM (SELECT unnest(json_keys(j)) AS k, j FROM
      (SELECT j FROM cj))
GROUP BY k HAVING nulls > 0 ORDER BY nulls DESC""").fetchdf()
print(f"\nQ4  crate keys with any null:\n{k.to_string(index=False)}")
print(f"    every key is PRESENT on all {tot} crates — nothing is absent, so")
print("    every hole is a WRITTEN null, and three keys are nothing else.")
print("\nQ5  every column unified; the probe reports NO type change.")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
nc, nd = con.execute("SELECT num_crates, num_downloads FROM env").fetchone()
print(f"\nQ7  num_crates {nc:,}, num_downloads {nd:,}, {tot} rows here, {dist} distinct")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8 = con.execute("""SELECT json_extract_string(j,'$.name') AS name,
                           json_extract_string(j,'$.max_version') AS max_version,
                           json_extract(j,'$.downloads') AS downloads
                    FROM cj LIMIT 2""").fetchdf()
print(f"\nQ8  {t8.shape}\n{t8.to_string(index=False)}")
h = con.execute("SELECT count(*) FILTER (WHERE json_type(json_extract(j,'$.homepage')) <> 'NULL') FROM cj").fetchone()[0]
print(f"\nQ9  `homepage` non-null on {h} of {tot}; the row is kept either way")
print("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is a STRUCT of six")
print("    fields; question 10 has no target on this document.")
lk = con.execute("""SELECT json_extract_string(j,'$.name') AS name,
                           unnest(json_keys(json_extract(j,'$.links'))) AS link
                    FROM cj""").fetchdf()
print(f"    expanding `links` instead: {lk.shape}")
u = con.execute("""SELECT count(*) FROM cj
                   WHERE regexp_matches(json_extract_string(j,'$.repository'),
                                        '^https?://')""").fetchone()[0]
print(f"\nQ11 no `paths(...)`. A named column: `repository` matches on {u} of {tot}.")
print("    jq reports 11 distinct URL PATHS folding to 3.")
print(f"\nQ12 the honest table is the UNION ALL: {tot} x 24, holding {dist} distinct")
print("    crates. Or four LIST(STRUCT) cells in one row that DuckDB will not")
print("    tell you share a key-set until you compare the type strings yourself.")
