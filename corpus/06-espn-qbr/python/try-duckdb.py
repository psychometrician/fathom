"""DuckDB — ESPN quarterback rating, 2019

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   176 KB, 28 athletes
  measured      2026-08-09
  run           cd corpus/06-espn-qbr/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   no                  PARTLY
   3 what is one record                          3   YES                 partly
   7 how many records                            2   YES                 YES
   7a related by position, not nesting           6   no                  CANNOT

WHY THIS FILE. It is the easiest document in the corpus and it hides the corpus's
nastiest trap: the ten statistics in every `totals` array are named by a SEPARATE
array, `categories[0].labels`, and a second array of the same length —
`glossary` — carries the same ten names sorted differently. Joining against the
wrong one gives plausible numbers and no error.

Question 7a is marked circular in QUESTIONS.md and MUST NOT be used to score
tools against fathom. It is asked here because rule 3 requires every file to be
asked the same questions.
"""
import sys
from importlib.metadata import version
import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")
con = duckdb.connect()
SRC = "'../source.json'"

desc = con.sql(f"DESCRIBE SELECT * FROM read_json_auto({SRC})").fetchall()
size = len(open("../source.json", "rb").read())
print(f"\n1. DESCRIBE returns {len(desc)} rows for a {size:,}-byte file")
for name, typ, *_ in desc:
    print(f"     {name:<16} {str(typ)[:56]}")

n = con.sql(f"SELECT len(athletes) FROM read_json_auto({SRC})").fetchone()[0]
print(f"\n7. rows DuckDB reports: 1. Athletes inside: {n}")

# 7a — the parallel arrays
lens = con.sql(f"""
    SELECT len(categories[1].labels)      AS labels,
           len(categories[1].names)       AS names,
           len(glossary)                  AS glossary,
           len(athletes[1].categories[1].totals) AS totals
    FROM read_json_auto({SRC})
""").fetchone()
print(f"\n7a. four arrays, and DuckDB reports each length independently:")
for k, v in zip(("categories[1].labels", "categories[1].names",
                 "glossary", "athletes[1]...totals"), lens):
    print(f"     {k:<26} {v}")
print("""
    Same length, four times, and nothing connects them. `totals` is typed
    VARCHAR[] — ten strings with no names. The names are in `labels`, which
    DuckDB reports as another VARCHAR[] of ten, and the relationship between
    them is positional and therefore invisible to a type system.

    CREDIT WHERE IT IS DUE: DESCRIBE does list `categories` and its `labels`
    field at the top level. design/probe.py did NOT until it was repaired on
    2026-08-09, because `categories` is a single-copy object and the fold skips
    anything appearing once. DuckDB has no fold, so it never had that blind
    spot. It shows you that `labels` exists; it does not connect it to `totals`.

    Worse: `glossary` is also ten, and holds the same ten abbreviations sorted
    alphabetically. A reader joining `totals` to `glossary` by position gets
    TQBR = -7.4 for the league's top-rated quarterback, whose Total QBR is 83.0.
    Nothing in the schema, and nothing in any of these tools, distinguishes the
    right array of ten from the wrong one.
""")
