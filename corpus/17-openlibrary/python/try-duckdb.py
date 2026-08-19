"""DuckDB — 200 OpenLibrary search results

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   64 KB, 200 docs, depth 4
  measured      2026-08-11
  run           cd corpus/17-openlibrary/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    4   NO                  YES — exactly 4
   3 what is one record                          12  YES                 NO — misses the SPLIT
   4 always present vs sometimes                16  NO                  TWO ROUTES, ONE WRONG
   5 does any field change type                  8   NO                  NO by one route, YES by the other
   6 are any object keys data                    9   -                   n/a; and 15 key-sets, right
   7 how many records                             4   NO                  yes — both answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   6   YES                 NO by one route
  11 find every path matching something          6   NO                  YES — only frame that does
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 2, 6b, 11
  14 survives the next file unchanged?               Q2 yes
  15 readable a week later?                          NO — the two routes look alike
  16 lines, and how much is ceremony?                ~140

**`unnest(docs)` MANUFACTURES 1,164 NULLS THAT ARE NOT IN THE DOCUMENT, AND THAT
IS THE FINDING.** DuckDB builds a STRUCT with the **union** of all 17 fields, so
a record that carried 16 keys comes back with 17 — the missing one written as an
explicit `null` by `::JSON`. **The records contain ZERO nulls; after the round
trip they contain 1,164.**

Everything downstream then reads the invented nulls as data:

    route                                   Q4 always/sometimes   Q5 varying   Q10 rows
    unnest(docs) -> STRUCT -> ::JSON              17 / 0              11          350
    json_each(json, '$.docs') -> raw JSON          6 / 11              0          349
    the probe                                      6 / 11              0          349

**Two routes, one tool, a couple of lines apart, and only one is right.** The
wrong one is the obvious one — `unnest` is what the documentation reaches for —
and it fails silently, reporting a perfectly regular document with no missing
fields and eleven polymorphic ones.

> **This is the exact inverse of `15-github-issues`.** There the frame tools
> could not tell a null from an absence. Here DuckDB **creates** the nulls, so a
> document with none is described as riddled with them. Same conflation, opposite
> direction, and this one invents the evidence.

**IT STILL MISSES THE SPLIT, LIKE EVERYTHING ELSE.** The probe prints
`└─ or 4 tables, split on ebook_access — 16% empty`. `GROUP BY` produces them
once you know the field; of the six always-present fields, `edition_count` makes
the emptiness WORSE and `public_scan_b` changes nothing. Choosing is the fourth
operation and no tool here has it.

**IT IS THE ONLY FRAME TOOL THAT FINDS THE ONE URL**, because it reads the whole
object as a row so `documentation_url` is just a column. pandas and polars build
a 200-row frame from `docs` and report **none of one** — right by accident of
shape rather than by scanning paths.
"""
import json
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
con = duckdb.connect()
SRC = f"read_json_objects('{RAW}')"
doc = json.load(open(RAW))
docs = doc["docs"]
n = len(docs)

con.execute(f"CREATE TABLE t AS SELECT * FROM read_json('{RAW}')")
# ROUTE A — the obvious one. unnest gives a STRUCT of the UNION of fields.
con.execute("CREATE TABLE a AS SELECT unnest(docs) AS doc FROM t")
# ROUTE B — never becomes a STRUCT, so absence stays absence.
con.execute(f"CREATE TABLE b AS SELECT je.value AS doc"
            f" FROM {SRC}, json_each(json, '$.docs') je")

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  read_json succeeded and said nothing. It REFUSED 13-package-lock over")
print("    one empty-string key; this file gives it no trouble. No duplicate-key,")
print("    big-int or NaN report. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
desc = con.execute("DESCRIBE t").fetchall()
print(f"\nQ1  the whole document is one row of {len(desc)} columns:")
print("   ", [c[0] for c in desc])
fields_b = dict(con.execute(
    "SELECT k.key, count(*) FROM b, json_each(doc) k GROUP BY 1").fetchall())
print(f"Q1  the records carry {len(fields_b)} distinct fields.")
print("    PARTLY — `docs` had to be named. The probe prints 31 paths and names")
print("    both shapes as candidates unasked.")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
struct = json.loads(con.execute(f"SELECT json_structure(json) FROM {SRC}").fetchone()[0])


def depth(v):
    if isinstance(v, dict) and v:
        return 1 + max(depth(x) for x in v.values())
    if isinstance(v, list) and v:
        return 1 + max(depth(x) for x in v)
    return 0


print(f"\nQ2  json_structure walks to {depth(struct)} levels — THE PROBE PRINTS 4. Correct,")
print("    and it is the same verb that answered this on 13, 14 and 15. pandas")
print("    says 1 here, because json_normalize stops dead at the `docs` list.")

# ── Q3. THE SPLIT. ──────────────────────────────────────────────────────────
allf = sorted({k for r in docs for k in r})
holes = sum(1 for r in docs for k in allf if k not in r) / (n * len(allf))
print(f"\nQ3  the obvious record is a doc: {n} rows x {len(allf)} cols, {holes:.1%} empty")
print("    THE PROBE PRINTS THAT AND THEN A LINE no tool here can produce:")
print("      └─ or 4 tables, split on ebook_access — 16% empty")
print("\nQ3  GROUP BY gives the four tables ONCE YOU KNOW THE FIELD:")
for kind, rows in con.execute("""
        SELECT doc->>'ebook_access' AS kind, count(*) AS rows
        FROM b GROUP BY 1 ORDER BY rows DESC""").fetchall():
    g = [r for r in docs if r["ebook_access"] == kind]
    fs = sorted({k for r in g for k in r})
    h = sum(1 for r in g for k in fs if k not in r) / (len(g) * len(fs))
    print(f"      {kind:16} {rows:3} x {len(fs):3} cols  {h:4.0%} empty")
print("    Every number matches the probe. What SQL did not do is CHOOSE the")
print("    field: `edition_count` makes it worse, `public_scan_b` changes nothing,")
print("    and two tie at 16%. That search is the fourth operation, and this is")
print("    the first of four entries graded today where it fires at all. NO.")

# ── Q7. How many records. ────────────────────────────────────────────────────
print(f"\nQ7  {con.execute('SELECT count(*) FROM b').fetchone()[0]} docs in the array —")
print(f"    the document says numFound = {doc['numFound']:,}, num_found ="
      f" {doc['num_found']:,}, start = {doc['start']}.")
print("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. This is a PAGE, and")
print("    only a top-level field says so.")

# ── Q4. THE TWO ROUTES. ─────────────────────────────────────────────────────
fields_a = dict(con.execute(
    "SELECT k.key, count(*) FROM a, json_each(doc::JSON) k GROUP BY 1").fetchall())
truth = {k: sum(k in r for r in docs) for k in allf}
n_nulls = sum(1 for r in docs for v in r.values() if v is None)
print(f"\nQ4  the document's records hold {n_nulls} nulls. Two routes to the same table:")
for label, f in (("unnest(docs) -> STRUCT", fields_a),
                 ("json_each(json,'$.docs')", fields_b)):
    al = sum(1 for v in f.values() if v == n)
    so = sum(1 for v in f.values() if v < n)
    ok = f == truth
    print(f"      {label:26} always {al:2}, sometimes {so:2}   {'correct' if ok else 'WRONG'}")
print(f"      the probe                  always  6, sometimes 11")
made = n * len(allf) - sum(truth.values())
print(f"\nQ4  `unnest` BUILDS A STRUCT WITH THE UNION OF FIELDS, so a record that")
print(f"    carried 16 keys comes back with 17 and `::JSON` writes the missing one")
print(f"    as an explicit null. THAT MANUFACTURES {made:,} NULLS THAT ARE NOT IN")
print("    THE DOCUMENT, and route A then reports every field as always present.")
print("    15-github-issues found the frame tools unable to tell a null from an")
print("    absence. THIS IS THE INVERSE: DuckDB creates the nulls.")

# ── Q5. Does any field change type — by both routes. ───────────────────────
var_a = con.execute("""
    SELECT k.key FROM a, json_each(doc::JSON) k
    GROUP BY 1 HAVING count(DISTINCT json_type(k.value)) > 1""").fetchall()
var_b = con.execute("""
    SELECT k.key FROM b, json_each(doc) k
    GROUP BY 1 HAVING count(DISTINCT json_type(k.value)) > 1""").fetchall()
print(f"\nQ5  route A (STRUCT) reports {len(var_a)} fields as varying in type")
print(f"Q5  route B (raw JSON) reports {len(var_b)} — and the probe reports none.")
print("    Every one of route A's is `NULL` against the real type, and every one")
print("    of those nulls was invented at Q4. The wrong answer is the confident")
print("    one: eleven polymorphic fields on a document that has none.")

# ── Q6. Are any object keys actually data? AND json_structure. ─────────────
ks_a = con.execute("SELECT count(DISTINCT json_structure(doc::JSON)) FROM a").fetchone()[0]
ks_b = con.execute("SELECT count(DISTINCT json_structure(doc)) FROM b").fetchone()[0]
keysets = len({frozenset(r) for r in docs})
print("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA section")
print("    is empty for this file.")
print(f"\nQ6b count(DISTINCT json_structure(doc)):  route A {ks_a},  route B {ks_b}")
print(f"    distinct key-sets in the document: {keysets}, and THE PROBE PRINTS {keysets}.")
print("    BOTH ROUTES ARE RIGHT, and route A only by luck: its invented nulls")
print("    fall in exactly the pattern the absences did, so 'which fields are")
print("    null' is isomorphic to 'which fields are missing' and the COUNT")
print("    survives the corruption that ruined Q4, Q5 and Q10.")
print("    This is the first time the expression has been right since 14-nyc-311.")
print("    The ladder in 15-github-issues said it is trustworthy only where there")
print("    are neither data keys nor nulls, and this document has neither.")

# ── Q8/Q9. Extraction. ──────────────────────────────────────────────────────
print("\nQ8 ", con.execute("""
    SELECT doc->>'title' AS title, doc->>'edition_count' AS n,
           doc->>'ebook_access' AS access FROM b LIMIT 2""").fetchall())
n_cover = con.execute("SELECT count(doc->>'cover_i') FROM b").fetchone()[0]
print(f"\nQ9  cover_i present on {n_cover} of {n} — `->>` gives NULL, row kept")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────────
na = con.execute("SELECT count(*) FROM a, json_each(doc::JSON, '$.author_name') x").fetchone()[0]
nb = con.execute("SELECT count(*) FROM b, json_each(doc, '$.author_name') x").fetchone()[0]
real = sum(len(r["author_name"]) for r in docs if "author_name" in r)
print(f"\nQ10 author_name unnested:  route A {na},  route B {nb},  truth {real}")
print("    Route A's extra row is the ONE doc with no author_name, whose invented")
print("    null becomes an element. The error is small and it is the same error.")
print("    FIVE fields are arrays — author_name, author_key, language, ia,")
print("    ia_collection — and every one is ALSO sometimes absent.")

# ── Q11. Find every path whose value matches something — here, a URL. ──────
varchars = [c[0] for c in desc if str(c[1]) == "VARCHAR"]
hits = con.execute("SELECT " + ", ".join(
    f'count(*) FILTER (WHERE "{c}" LIKE \'%http%\') AS "{c}"' for c in varchars)
    + " FROM t").fetchone()
found = {c: v for c, v in zip(varchars, hits) if v}
in_docs = con.execute("""
    SELECT count(*) FROM b, json_each(doc) k
    WHERE json_type(k.value) = 'VARCHAR' AND k.value::VARCHAR LIKE '%http%'""").fetchone()[0]
print(f"\nQ11 URLs at the top level: {found}")
print(f"Q11 URLs inside the 200 records: {in_docs}")
print("    THE ONLY URL IN THE DOCUMENT IS THE TOP-LEVEL ONE, and DuckDB is the")
print("    only frame tool here that sees it — it reads the whole object as a")
print("    row, so the field is just a column. pandas and polars build a frame")
print("    from `docs` and report NONE OF ONE. Right by accident of shape.")

# ── Q12. The flattest honest table, and what was lost. ─────────────────────
print(f"\nQ12 the honest record table is {n} x {len(allf)} at {holes:.0%} empty, five array")
print("    columns intact. Nothing collides — these records have no nested")
print("    OBJECTS at all, so `struct.*` has nothing to duplicate. (It returned")
print("    19 duplicate names on 15-github-issues.)")
print("    The seven top-level fields are a different table, which is why the")
print("    probe names `the whole document 1 rows x 8 cols` as a candidate.")
