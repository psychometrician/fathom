"""DuckDB — movie ratings, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
  measured      2026-08-10
  run           cd corpus/16-movie-ratings/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  WRONG
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          4   YES                 PARTLY
   4 always present vs sometimes                 4   YES                 yes
   5 does any field change type                  5   NO                  yes
   6 are any object keys data                    3   YES                 WRONG
   7 how many records                            1   YES                 YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   1   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       4   YES                 PARTLY
  13 needed the shape in advance?                    YES — Q1 is actively wrong
  14 survives the next file unchanged?               no
  15 readable a week later?                          yes, it is SQL
  16 lines, and how much is ceremony?                ~35, some SQL ceremony
"""
import json
import sys
from importlib.metadata import version

import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")
con = duckdb.connect()
SRC = "read_json_auto('../source.json', maximum_object_size=100000000)"

d = con.sql(f"DESCRIBE SELECT * FROM {SRC}").df()
total = sum(len(str(t)) for t in d["column_type"])
print(f"\n1. DESCRIBE: {len(d)} rows, all type cells {total:,} chars "
      f"({100 * total / 6975:.0f}% of the file)")
print(f"   first three column names: {list(d['column_name'])[:3]}")
print("   WRONG. The 38 MOVIE TITLES became columns, because the document is a")
print("   one-element array holding an object keyed by film. DESCRIBE returns")
print("   38 tidy rows and every one of them is a value.")
print(f"\n6. WRONG, and expensively: {len(d)} columns, {total:,} characters of")
print("   type, for 38 films. This is npm's failure on a 7 KB file.")

movies = json.load(open("../source.json"))[0]
con.register("m", __import__("pandas").DataFrame(
    [{"title": t, **v} for t, v in movies.items()]))
print(f"\n   Told the right shape by hand: "
      f"{con.sql('SELECT count(*) FROM m').fetchone()[0]} rows.")

print("\n2. CANNOT. The depth is inside the type strings and DuckDB has no verb")
print("   for it. The true depth is 3.")

n = con.sql("SELECT count(*) FROM m").fetchone()[0]
print(f"\n7. {n} movies.")

print("\n4. non-null per field:")
cols = [c for c in con.sql("DESCRIBE m").df()["column_name"]]
q = ", ".join(f'count("{c}") AS "{c}"' for c in cols)
for k, v in con.sql(f"SELECT {q} FROM m").df().iloc[0].sort_values(
        ascending=False).items():
    print(f"     {k:18} {int(v):>3} of {n}")
print("   Nothing but `title` is on all 38 — the two key-sets are disjoint.")

# ── 5. THE FINDING, and it is one nobody would have predicted ────────────────
# DuckDB identifiers are CASE-INSENSITIVE. `rating` collides with `Rating`, so
# the second arrives renamed to `rating_1` — and `SELECT rating` then returns
# `Rating`'s data.
cols = list(con.sql("DESCRIBE m").df()["column_name"])
print("\n5. DuckDB's columns:", cols)
print("   `rating` IS NOT THERE. It arrived as `rating_1`, because DuckDB")
print("   identifiers are case-insensitive and `Rating` took the name first.")
Q_UPPER = 'SELECT "Rating" FROM m LIMIT 2'
Q_COUNT = 'SELECT count("Rating") FROM m'
Q_LOWER = "SELECT count(rating_1) FROM m"
print(f"     SELECT \"Rating\"   -> {con.sql(Q_UPPER).fetchall()}")
print(f"     SELECT rating     -> {con.sql('SELECT rating FROM m LIMIT 2').fetchall()}")
print(f"     SELECT rating_1   -> {con.sql('SELECT rating_1 FROM m LIMIT 2').fetchall()}")
print(f'   non-null: "Rating" {con.sql(Q_COUNT).fetchone()[0]}, '
      f"rating_1 {con.sql(Q_LOWER).fetchone()[0]}")
print("   **Typing the field name that is in the document returns the OTHER")
print("   population's data, silently.** On the one corpus file whose published")
print("   point is that `Rating` and `rating` are two spellings of one field,")
print("   DuckDB merged the NAMES and kept the DATA apart — the exact inverse")
print("   of what a reader wants, with no warning and no error.")
print("   `Popcorn Score`/`popcornscore` do NOT collide: the space makes them")
print("   different identifiers even case-insensitively. So the hazard is")
print("   present on one of the three renamed pairs and absent on two, which")
print("   is worse than uniform — it is unpredictable.")

print("\n   types after unification:")
print("   " + ", ".join(f"{c}={t}" for c, t in
                        zip(cols, con.sql("DESCRIBE m").df()["column_type"])))
print("   `Popcorn Score` and `Tomato Score` hold int x9 and str x6 each; the")
print("   6 strings are the SENTINELS, and coercion to VARCHAR makes the column")
print("   read as homogeneous.")
s = con.sql("""SELECT count(*) FROM m WHERE lower(CAST("Popcorn Score" AS VARCHAR))
               LIKE 'unk%' OR lower(CAST("Tomato Score" AS VARCHAR)) LIKE 'unk%'
               OR lower(CAST("Gross" AS VARCHAR)) LIKE 'unk%'""").fetchone()[0]
print(f"   rows carrying at least one sentinel: {s} of {n} — findable only")
print("   because I supplied the string 'unk'.")

print("\n3. one film per row, and TWO tables inside it:")
for r in con.sql("""SELECT CASE WHEN rating_1 IS NOT NULL THEN 'lowercase'
                    ELSE 'TitleCase' END k, count(*) n FROM m GROUP BY 1
                    ORDER BY 2 DESC""").fetchall():
    print(f"     {r[0]:15} {r[1]:>3} rows")
print("   **The first version of this query said `WHEN rating IS NOT NULL` and")
print("   reported the two groups BACKWARDS** — 23 TitleCase, 15 lowercase —")
print("   because `rating` resolved to `Rating`. The numbers looked plausible")
print("   and were exactly inverted. That is what a silent rename costs.")
print("   There is no column to GROUP BY honestly: the two groups share no")
print("   field, so the discriminator is the naming convention itself.")

print("\n8/9. three fields:")
print(con.sql('SELECT title, "Rating", rating_1 FROM m LIMIT 3').df()
      .to_string(index=False))
miss = con.sql('SELECT count(*) FROM m WHERE "Rating" IS NULL').fetchone()[0]
print(f'   "Rating" NULL on {miss} of {n} rows, all kept.')

print("\n10. n/a. 11. CANNOT — no path search over an arbitrary document.")
merged = con.sql('SELECT count(coalesce("Rating", rating_1)) FROM m').fetchone()[0]
print(f"\n12. flattest: {n} x {len(cols)}. `coalesce(\"Rating\", rating_1)` fills")
print(f"   {merged} of {n} — and it only works once you know the second column")
print("   is called `rating_1`, which is a name that appears nowhere in the")
print("   document.")
print("   WHAT IS LOST: the 17 sentinels; one type population per unified")
print("   column; and the name `rating`, which now resolves to something else.")
