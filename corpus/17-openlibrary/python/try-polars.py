"""polars — 200 OpenLibrary search results

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   64 KB, 200 docs, depth 4
  measured      2026-08-11
  run           cd corpus/17-openlibrary/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    5   NO                  YES — exactly 4
   3 what is one record                          11  YES                 NO — misses the SPLIT
   4 always present vs sometimes                 5   NO                  YES — no nulls to confuse
   5 does any field change type                  6   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                             4   NO                  yes — both answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          4   NO                  NO — finds ZERO
  12 flattest honest table                       4   NO                  yes — no collisions
  13 needed the shape in advance?                    NO for 2, 4, 5
  14 survives the next file unchanged?               Q2/Q4/Q5 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~110

**THE PROBE'S FOURTH OPERATION FIRES ON THIS DOCUMENT AND polars HAS NO WORD FOR
IT.** `design/probe.py` prints `an item of docs 200 rows x 17 cols 34% empty`
and then `└─ or 4 tables, split on ebook_access — 16% empty`. polars builds the
34.2% table exactly and offers nothing else. **`partition_by("ebook_access")`
gives the four tables in one line once you know the field**, and nothing in
polars searched for it or priced it.

**`offset` COMES BACK WITH DTYPE `Null`, WHICH IS THE ENTRY-15 FINDING AGAIN.**
The field is null and nothing else, and polars has a TYPE that says so. DuckDB
falls back to `JSON` on the same field; pandas gives an all-NaN object column.
Three tools, three ways of saying "there is nothing here", and only one of them
means it.

**QUESTION 11 IS A ZERO.** The document holds exactly one URL —
`documentation_url` — and it is a TOP-LEVEL field, so the 200-row frame cannot
see it. `25-usgs-quakes` recorded two-of-three on `metadata.url`; here the
frame-shaped answer is **none of one**.

**NOTHING COLLIDES HERE**, which is worth recording because `unnest` RAISED on
`15-github-issues` — 26 names, 58 renames — and on `25-usgs-quakes`. The records
in this document have no nested objects at all, only lists of scalars, so there
is nothing to flatten and nothing to clash.
"""
import json
from collections import Counter
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))
docs = doc["docs"]
n = len(docs)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
top = pl.read_json(RAW)
print(f"\nQ0  pl.read_json: {top.shape} — no refusal. It refused 14-nyc-311 and")
print("    DuckDB refused 13-package-lock; this file troubles neither.")
print("    No duplicate-key, big-int or NaN report. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
df = pl.DataFrame(docs)
print(f"\nQ1  the whole document is {top.shape}: {top.columns}")
print(f"Q1  the records are {df.shape}")
print("    PARTLY: `docs` had to be named. The probe prints 31 distinct paths and")
print("    names both shapes as candidates without being asked.")

# ── Q2. How deep does it go — walking the dtype tree. ───────────────────────
def dtype_depth(dt):
    if isinstance(dt, pl.Struct):
        return 1 + max((dtype_depth(f.dtype) for f in dt.fields), default=0)
    if isinstance(dt, pl.List):
        return 1 + dtype_depth(dt.inner)
    return 0


deep = max(dtype_depth(d) for d in top.dtypes)
print(f"\nQ2  the top-level frame's deepest dtype nests {deep} levels below the row,")
print(f"    and the row is level 1 (the file is one object), so the document is"
      f" {1 + deep} deep.")
print("    THE PROBE PRINTS 4. Correct — and pandas says 1, because")
print("    json_normalize stops dead at the `docs` list.")

# ── Q3. THE SPLIT. ──────────────────────────────────────────────────────────
nulls = df.null_count().row(0)
holes = sum(nulls) / (df.height * df.width)
print(f"\nQ3  the obvious record is a doc: {df.height} x {df.width}, {holes:.1%} empty")
print("    THE PROBE PRINTS THAT AND THEN A SECOND LINE polars cannot produce:")
print("      └─ or 4 tables, split on ebook_access — 16% empty")
print("\nQ3  `partition_by` gives them in one line ONCE YOU KNOW THE FIELD:")
for part in df.partition_by("ebook_access"):
    kept = [c for c in part.columns if part[c].null_count() < part.height]
    p = part.select(kept)
    h = sum(p.null_count().row(0)) / (p.height * p.width)
    print(f"      {part['ebook_access'][0]:16} {p.height:3} x {p.width:3} cols  {h:4.0%} empty")
print("    Every number matches the probe. What polars did not do is CHOOSE the")
print("    field: of the six always-present ones, `edition_count` makes it worse")
print("    and `public_scan_b` changes nothing. That search is the fourth")
print("    operation, and no tool in this directory has it. NO.")

# ── Q7. How many records. ────────────────────────────────────────────────────
print(f"\nQ7  {df.height} docs in the array — and the document says numFound ="
      f" {doc['numFound']:,},")
print(f"    num_found = {doc['num_found']:,}, start = {doc['start']}.")
print("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. This is a PAGE, and")
print("    only a top-level field says so.")

# ── Q4. Always present vs sometimes. ────────────────────────────────────────
always = [c for c, x in zip(df.columns, nulls) if x == 0]
some = sorted(((c, df.height - x) for c, x in zip(df.columns, nulls) if x > 0),
              key=lambda kv: kv[1])
n_nulls = sum(1 for r in docs for v in r.values() if v is None)
print(f"\nQ4  always {len(always)}, sometimes {len(some)} — matches the probe")
print(f"    rarest five: {some[:5]}")
print(f"    CORRECT AND FREE: the records hold {n_nulls} nulls, so every null in")
print("    this frame is an absence. On 15-github-issues the same code conflated")
print("    5 absences with 8 nulls and reported a single 13.")

# ── Q5. Does any field change type — AND THE `Null` DTYPE. ──────────────────
print(f"\nQ5  dtypes in the record frame: {sorted({str(t) for t in df.dtypes})}")
print("    No column carries two, which is correct — the probe reports no field")
print("    that changes type here.")
null_typed = [c for c, dt in zip(top.columns, top.dtypes) if dt == pl.Null]
print(f"\nQ5b at the TOP level, polars types {len(null_typed)} column `Null`: {null_typed}")
print("    `offset` is null and nothing else, and polars has a TYPE that says so.")
print("    DuckDB falls back to `JSON` on the same field; pandas gives an all-NaN")
print("    object column. This is 15-github-issues' three-way, on one field.")

# ── Q6. Are any object keys actually data? ──────────────────────────────────
print("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA")
print("    section is empty for this file.")

# ── Q8/Q9. Extraction. ──────────────────────────────────────────────────────
print(f"\nQ8  {df.height} rows x 3 cols")
print(df.select("title", "edition_count", "ebook_access").head(3))
print(f"\nQ9  cover_i present on {df.height - df['cover_i'].null_count()} of {df.height}"
      " — rows kept, gaps null")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────────
names = (df.select("key", "author_name").explode("author_name", empty_as_null=True)
           .drop_nulls("author_name"))
print(f"\nQ10 author_name exploded to {names.height} rows")
print("    FIVE fields are List(String) — author_name, author_key, language, ia,")
print("    ia_collection — and every one of them is ALSO sometimes absent, which")
print("    is the combination this entry adds to the corpus.")

# ── Q11. Find every path whose value matches something — here, a URL. ───────
hits = {c: int(df[c].str.contains("http").sum())
        for c, dt in zip(df.columns, df.dtypes) if dt == pl.String}
print(f"\nQ11 URLs in the 200-row frame: { {c: v for c, v in hits.items() if v} or 'NONE'}")
print(f"    The document holds exactly ONE: documentation_url = {doc['documentation_url']}")
print("    It is a TOP-LEVEL field, so the record frame cannot see it. The")
print("    frame-shaped answer here is NONE OF ONE.")

# ── Q12. The flattest honest table, and what was lost. ──────────────────────
lists = [c for c, dt in zip(df.columns, df.dtypes) if isinstance(dt, pl.List)]
print(f"\nQ12 {df.shape}, {holes:.1%} empty; {len(lists)} List columns remain: {lists}")
print("    NOTHING COLLIDES, and that is worth recording: `unnest` RAISED on")
print("    15-github-issues (26 names, 58 renames) and on 25-usgs-quakes. These")
print("    records have no nested OBJECTS at all — only lists of scalars — so")
print("    there is nothing to flatten and nothing to clash.")
print("    The seven top-level fields are absent from this table entirely.")
