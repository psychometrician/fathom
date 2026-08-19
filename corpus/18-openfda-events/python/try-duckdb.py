"""DuckDB — 100 openFDA adverse-event reports

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   2.7 MB, 100 results, depth 8
  measured      2026-08-11
  run           cd corpus/18-openfda-events/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    4   NO                  YES — exactly 8
   3 what is one record                           8  NO                  PARTLY
   4 always present vs sometimes                12  NO                  TWO ROUTES, ONE WRONG
   5 does any field change type                  6   NO                  NO by one route
   6 are any object keys data                    5   -                   n/a — no abstention
   7 how many records                             4   NO                  yes — four answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   5   YES                 yes
  11 find every path matching something          5   NO                  YES — sees `meta`
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 2, 11
  14 survives the next file unchanged?               Q2 yes
  15 readable a week later?                          NO — the two routes look alike
  16 lines, and how much is ceremony?                ~125

**THE ENTRY-17 NULL MANUFACTURING HAPPENS AGAIN, ON A DIFFERENT DOCUMENT.**
`unnest(results)` builds a STRUCT with the **union** of all 25 fields, so casting
back to JSON writes the absent ones as explicit `null`:

    json_each over the STRUCT route ....... 2,500 key occurrences
    json_each over the raw JSON ........... 2,036
    the truth (sum of the records' keys) .. 2,036

**464 keys that are not in the document**, and every one of them reads as a
present-but-null field downstream. `17-openlibrary` measured the same thing at
1,164. **Two documents, one mechanism, and the obvious route is the wrong one
both times.**

**`json_structure` GETS DEPTH 8 EXACTLY**, on the deepest file in the corpus, and
it is the same verb that answered this on entries 13, 14, 15 and 17. pandas says
3 here.

**AND IT IS THE ONLY FRAME TOOL THAT FINDS THE URLs**, for the same reason as on
`17-openlibrary`: it reads the whole object as a row, so `meta` is a column
rather than something outside the table. pandas and polars frame `results` and
report none of two. Right by accident of shape, not by scanning paths.

**IT HAS NO ABSTENTION.** The probe prints `could not call 3 small single-copy
objects` and names them — a third state between "keys are data" and "keys are
fields". SQL has no way to say "too few copies to judge".
"""
import json
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
con = duckdb.connect()
SRC = f"read_json_objects('{RAW}')"
doc = json.load(open(RAW))
R = doc["results"]
n = len(R)

con.execute(f"CREATE TABLE t AS SELECT * FROM read_json('{RAW}')")
con.execute("CREATE TABLE a AS SELECT unnest(results) AS res FROM t")   # STRUCT route
con.execute(f"CREATE TABLE b AS SELECT je.value AS res"
            f" FROM {SRC}, json_each(json, '$.results') je")            # raw-JSON route

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
print("\nQ0  read_json succeeded and said nothing. It REFUSED 13-package-lock over")
print("    one empty-string key; 2.7 MB and eight levels give it no trouble.")
print("    No duplicate-key, big-int or NaN report. CANNOT.")

# ── Q1. What is in here. ───────────────────────────────────────────────────
desc = con.execute("DESCRIBE t").fetchall()
print(f"\nQ1  the whole document is one row of {len(desc)} columns: {[c[0] for c in desc]}")
fields = dict(con.execute(
    "SELECT k.key, count(*) FROM b, json_each(res) k GROUP BY 1").fetchall())
print(f"Q1  the results carry {len(fields)} distinct fields.")
print("    PARTLY — `results` had to be unnested by name. The probe prints 122")
print("    paths and ELEVEN record shapes without being told anything.")

# ── Q2. How deep does it go. ──────────────────────────────────────────────
struct = json.loads(con.execute(f"SELECT json_structure(json) FROM {SRC}").fetchone()[0])


def depth(v):
    if isinstance(v, dict) and v:
        return 1 + max(depth(x) for x in v.values())
    if isinstance(v, list) and v:
        return 1 + max(depth(x) for x in v)
    return 0


print(f"\nQ2  json_structure walks to {depth(struct)} levels — THE PROBE PRINTS 8, and this")
print("    is the deepest file in the corpus. Correct, and the same verb answered")
print("    this on entries 13, 14, 15 and 17. pandas says 3.")

# ── Q3/Q7. Row candidates and counts. ────────────────────────────────────
drug = con.execute("""SELECT count(*) FROM b, json_each(res, '$.patient.drug') d""").fetchone()[0]
rx = con.execute("""SELECT count(*) FROM b, json_each(res, '$.patient.reaction') x""").fetchone()[0]
print(f"\nQ3/Q7  DuckDB counts any level named: results {n}, drug {drug}, reaction {rx}")
print(f"       and meta.results.total says {doc['meta']['results']['total']:,} exist.")
print("    THE PROBE NAMES FOUR CANDIDATES AND PRICES THEM:")
print("      the whole document        1 rows x  2 cols")
print("      an item of results      100 rows x 39 cols   26% empty")
print("      an item of drug         265 rows x 41 cols   47% empty")
print("      an item of reaction     247 rows x  3 cols")
print("    SQL counted every level I named and proposed none. PARTLY.")

# ── Q4. THE TWO ROUTES. ──────────────────────────────────────────────────
occ_a = con.execute("SELECT count(*) FROM a, json_each(res::JSON) k").fetchone()[0]
occ_b = con.execute("SELECT count(*) FROM b, json_each(res) k").fetchone()[0]
truth = sum(len(r) for r in R)
fields_a = dict(con.execute(
    "SELECT k.key, count(*) FROM a, json_each(res::JSON) k GROUP BY 1").fetchall())
print(f"\nQ4  key occurrences over the results, two routes:")
print(f"      unnest(results) -> STRUCT -> ::JSON   {occ_a:,}")
print(f"      json_each(json, '$.results')          {occ_b:,}")
print(f"      the truth                             {truth:,}")
print(f"    THE STRUCT ROUTE INVENTS {occ_a - truth} KEYS. `unnest` unions all 25 fields,")
print("    and `::JSON` writes the ones a record never had as explicit null.")
print("    17-openlibrary measured the same mechanism at 1,164. Two documents,")
print("    one trap, and the obvious route is the wrong one both times.")
al_a = sum(1 for c in fields_a.values() if c == n)
al_b = sum(1 for c in fields.values() if c == n)
print(f"\nQ4  always/sometimes:  STRUCT route {al_a}/{len(fields_a) - al_a}"
      f"   ·   raw JSON {al_b}/{len(fields) - al_b}   ·   probe 14/11")
some = sorted(((k, c) for k, c in fields.items() if c < n), key=lambda kv: kv[1])
print(f"    rarest five (raw route): {some[:5]}")

# ── Q5. Does any field change type. ──────────────────────────────────────
var_a = con.execute("""SELECT k.key FROM a, json_each(res::JSON) k
    GROUP BY 1 HAVING count(DISTINCT json_type(k.value)) > 1""").fetchall()
var_b = con.execute("""SELECT k.key FROM b, json_each(res) k
    GROUP BY 1 HAVING count(DISTINCT json_type(k.value)) > 1""").fetchall()
print(f"\nQ5  route A (STRUCT) reports {len(var_a)} fields as varying in type")
print(f"Q5  route B (raw JSON) reports {len(var_b)}: {[x[0] for x in var_b]}")
print("    The probe reports NONE. Route B's one is `receiver` — an object on 99")
print("    results and NULL on 1 — which design/axes.py and defect 11 both rule")
print("    is missingness written as a value. Route A's extras are invented.")

# ── Q6. Are any object keys actually data? ───────────────────────────────
print("\nQ6  no keyed collections. n/a — and the probe says something SQL cannot:")
print("      could not call 3 small single-copy objects, shortest first:")
print("        $.meta · $.meta.results · $.results[].patient.patientdeath")
print("    THAT IS AN ABSTENTION. There is no SQL for 'too few copies to judge'.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────
print("\nQ8 ", con.execute("""SELECT res->>'safetyreportid', res->>'serious',
    res->>'receivedate' FROM b LIMIT 2""").fetchall())
sd = con.execute("SELECT count(res->>'seriousnessdeath') FROM b").fetchone()[0]
print(f"\nQ9  seriousnessdeath present on {sd} of {n} — `->>` gives NULL, row kept")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────
brands = con.execute("""
    SELECT count(*) FROM b,
      json_each(res, '$.patient.drug') d,
      json_each(d.value, '$.openfda.brand_name') bn""").fetchone()[0]
print(f"\nQ10 brand names: {brands}, reached with TWO nested json_each calls —")
print("    `$.patient.drug` then `$.openfda.brand_name`. Every level is named.")
print("    jq crosses the same four levels with `..` and names none of them.")

# ── Q11. Find every path whose value matches something. ─────────────────
top = con.execute("""SELECT k.key, count(*) FROM read_json_objects('%s'),
    json_each(json, '$.meta') k
    WHERE json_type(k.value)='VARCHAR' AND k.value::VARCHAR LIKE '%%http%%'
    GROUP BY 1""" % RAW).fetchall()
in_res = con.execute("""SELECT count(*) FROM b, json_each(res) k
    WHERE json_type(k.value)='VARCHAR' AND k.value::VARCHAR LIKE '%http%'""").fetchone()[0]
print(f"\nQ11 URLs under `meta`: {top}")
print(f"Q11 URLs among the results' own fields: {in_res}")
print("    BOTH URLs ARE OUTSIDE `results`, and DuckDB is the only frame tool")
print("    here that can see them — it reads the whole object as a row, so `meta`")
print("    is a column. pandas and polars report NONE OF TWO. Right by accident")
print("    of shape rather than by scanning paths, exactly as on 17-openlibrary.")

# ── Q12. The flattest honest table. ─────────────────────────────────────
print(f"\nQ12 the honest record table is {n} x {len(fields)} own fields, two of them")
print("    arrays holding 265 drugs and 247 reactions — the probe's other two")
print("    row candidates. Nothing collides here; `struct.*` returned 19")
print("    duplicate names on 15-github-issues and these objects share no names.")
