"""polars — 100 openFDA adverse-event reports

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   2.7 MB, 100 results, depth 8
  measured      2026-08-11
  run           cd corpus/18-openfda-events/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    6   NO                  YES — exactly 8
   3 what is one record                          10  YES                 PARTLY
   4 always present vs sometimes                 6   NO                  YES
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    4   -                   n/a — and no abstention
   7 how many records                             5   NO                  yes — four answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   6   YES                 yes
  11 find every path matching something          4   NO                  NO — finds ZERO
  12 flattest honest table                       4   YES                 yes — no collisions
  13 needed the shape in advance?                    NO for 2, 4, 5
  14 survives the next file unchanged?               Q2/Q4/Q5 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~110, and the dtype walk is 6

**THE DTYPE WALK GETS DEPTH 8 EXACTLY, ON THE DEEPEST DOCUMENT IN THE CORPUS.**
`read_json` returns one row of two columns, and the `results` dtype is a
`List(Struct(... List(Struct(... List(String)))))` seven levels below the row.
**pandas answers 3 of 8 on the same file**, because `json_normalize` stops at
the first array and this document has arrays inside arrays inside objects.
Fourth file running that this comparison comes out the same way.

**AND NOTHING COLLIDES, WHICH IS WORTH RECORDING.** `unnest` RAISED on
`15-github-issues` (26 names, 58 renames) and on `25-usgs-quakes`. Here the
nested objects — `patient`, `primarysource`, `sender`, `receiver`,
`reportduplicate` — share no field names with the record or each other, so the
same call just works.

**QUESTION 11 IS A ZERO AGAIN.** The two URLs are `meta.terms` and `meta.license`,
outside `results`. Framing the records cannot reach them — exactly as on
`17-openlibrary`, where there was one and polars found none of it.

**AND polars HAS NO WAY TO ABSTAIN.** The probe prints `could not call 3 small
single-copy objects` and names them. That is a third state — not "keys are
data", not "keys are fields", but "one copy, too few keys to judge". A schema
has no room for it: every struct is simply a struct.
"""
import json
import time
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))
R = doc["results"]
n = len(R)
drugs = [dr for r in R for dr in r["patient"]["drug"]]
rx = [x for r in R for x in r["patient"]["reaction"]]

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
t0 = time.time()
top = pl.read_json(RAW)
print(f"\nQ0  pl.read_json: {top.shape} in {time.time() - t0:.2f}s — no refusal.")
print("    It refused 14-nyc-311 and DuckDB refused 13-package-lock; 2.7 MB and")
print("    eight levels give it no trouble. No health report of any kind. CANNOT.")

# ── Q1. What is in here. ───────────────────────────────────────────────────
df = pl.DataFrame(R, infer_schema_length=None)
print(f"\nQ1  the whole document is {top.shape}: {top.columns}")
print(f"Q1  the results are {df.shape}")
print("    PARTLY: `results` had to be named. The probe prints 122 distinct")
print("    paths and ELEVEN record shapes without being told anything.")

# ── Q2. How deep does it go. ──────────────────────────────────────────────
def dtype_depth(dt):
    if isinstance(dt, pl.Struct):
        return 1 + max((dtype_depth(f.dtype) for f in dt.fields), default=0)
    if isinstance(dt, pl.List):
        return 1 + dtype_depth(dt.inner)
    return 0


deep = max(dtype_depth(x) for x in top.dtypes)
print(f"\nQ2  the deepest dtype nests {deep} levels below the row; the row is level 1")
print(f"    (the file is one object), so the document is {1 + deep} deep.")
print("    THE PROBE PRINTS 8, AND THIS IS THE DEEPEST FILE IN THE CORPUS.")
print("    pandas says 3, because json_normalize stops at the first array and")
print("    this document nests arrays inside arrays inside objects:")
print("      results[] -> patient.drug[] -> openfda.brand_name[]")

# ── Q3. The four row candidates. ──────────────────────────────────────────
print("\nQ3  the probe names FOUR candidates at three nesting levels, priced:")
print("      the whole document        1 rows x  2 cols")
print("      an item of results      100 rows x 39 cols   26% empty")
print("      an item of drug         265 rows x 41 cols   47% empty")
print("      an item of reaction     247 rows x  3 cols")
for label, rows in (("results", R), ("drug", drugs), ("reaction", rx)):
    truth = len(set().union(*(set(x) for x in rows)))
    f = pl.DataFrame(rows)
    g = pl.DataFrame(rows, infer_schema_length=None)
    nulls = sum(g.null_count().row(0))
    tag = "" if f.width == truth else f"   <- DEFAULT DROPS {truth - f.width} SILENTLY"
    print(f"      polars {label:10} {g.height:4} x {g.width:3} cols"
          f"  {nulls / (g.height * g.width):5.1%} null{tag}")
print("    polars counts the record's OWN fields, so its column counts are the")
print("    pre-flattening ones where the probe prices the FLATTENED shape pandas")
print("    builds. Different questions, and only the probe says which it answers.")
lost = sorted(set().union(*(set(x) for x in drugs)) - set(pl.DataFrame(drugs).columns))
print(f"\nQ3b AND THE DEFAULT LOSES TWO DRUG FIELDS SILENTLY: {lost}")
print("    They are on 3 of 265 drugs, so the inference sample never sees them.")
print("    `infer_schema_length=None` recovers both — which is more than it did")
print("    on 13-package-lock, where that flag did NOT help the same route and")
print("    7 of 21 fields stayed lost. Same failure, and the fix works here.")

# ── Q7. How many records. ─────────────────────────────────────────────────
print(f"\nQ7  FOUR right answers:")
print(f"      results {len(R):4} · drug {len(drugs):4} · reaction {len(rx):4}")
print(f"      and meta.results.total says {doc['meta']['results']['total']:,} exist")
print("    The last one is in a field no frame built from `results` can see.")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
nulls = df.null_count().row(0)
some = sorted(((c, df.height - x) for c, x in zip(df.columns, nulls) if x > 0),
              key=lambda kv: kv[1])
print(f"\nQ4  over the results frame: always"
      f" {sum(1 for x in nulls if x == 0)}, sometimes {len(some)}")
print(f"    rarest five: {some[:5]}")
print("    The whole document holds THREE nulls, so this is almost all genuine")
print("    absence. On 15-github-issues 709 nulls made this same count useless.")

# ── Q5. Does any field change type. ───────────────────────────────────────
print(f"\nQ5  dtypes in the results frame: {len({str(x) for x in df.dtypes})} distinct,"
      " one per column")
print("    No column carries two, which is correct — the probe reports no field")
print("    that changes type. pandas' python-type check reports TWELVE on this")
print("    document, eleven of them NaN and the twelfth a single null.")

# ── Q6. Are any object keys actually data? ────────────────────────────────
print("\nQ6  no keyed collections. n/a — but the probe says something polars")
print("    cannot: `could not call 3 small single-copy objects`, naming $.meta,")
print("    $.meta.results and $.results[].patient.patientdeath. THAT IS AN")
print("    ABSTENTION, and a schema has no room for one: every struct is a struct.")

# ── Q8/Q9. Extraction. ────────────────────────────────────────────────────
print(f"\nQ8  {df.height} rows x 3 cols")
print(df.select("safetyreportid", "serious", "receivedate").head(2))
print(f"\nQ9  seriousnessdeath present on"
      f" {df.height - df['seriousnessdeath'].null_count()} of {df.height} — rows kept")

# ── Q10. Flatten the deepest array into rows. ─────────────────────────────
step = (df.select("safetyreportid", pl.col("patient").struct.field("drug"))
          .explode("drug", empty_as_null=True).drop_nulls("drug").unnest("drug"))
brands = (step.select("safetyreportid",
                      pl.col("openfda").struct.field("brand_name"))
              .explode("brand_name", empty_as_null=True).drop_nulls("brand_name"))
print(f"\nQ10 results {df.height} -> drugs {step.height} -> brand names {brands.height}")
print("    TWO explodes and two struct-field accesses, and the parent key had to")
print("    be carried by hand at each step. polars does cross the levels, which")
print("    json_normalize cannot — but the path is spelled out one link at a time.")

# ── Q11. Find every path whose value matches something. ──────────────────
hits = {c: int(df[c].str.contains("http").sum())
        for c, x in zip(df.columns, df.dtypes) if x == pl.String}
print(f"\nQ11 URLs in the results frame: { {c: v for c, v in hits.items() if v} or 'NONE'}")
print(f"    The document holds TWO: meta.terms and meta.license, both OUTSIDE")
print("    `results`. Same failure as 17-openlibrary. NO.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────
structs = [c for c, x in zip(df.columns, df.dtypes) if isinstance(x, pl.Struct)]
flat = df.unnest(*structs)
print(f"\nQ12 unnest of {len(structs)} Struct columns -> {flat.shape}, no error.")
print("    NOTHING COLLIDES — `unnest` RAISED on 15-github-issues (26 names, 58")
print("    renames) and on 25-usgs-quakes. These nested objects share no field")
print("    names, so the same call just works. The collision is a property of")
print("    the document's names, not of the verb.")
print("    Two List columns remain — drug and reaction — holding the probe's")
print("    other two row candidates, 265 and 247 rows.")
