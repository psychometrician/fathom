"""polars — 100 GitHub issues from one repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   686 KB, 100 issues, depth 4
  measured      2026-08-11
  run           cd corpus/15-github-issues/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             4   NO                  yes
   2 how deep                                    5   NO                  YES — exactly 4
   3 what is one record                          4   NO                  PARTLY
   4 always present vs sometimes                 9   NO                  NO — conflates 5 with 8
   5 does any field change type                  6   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              6   YES                 YES — and NO ghost
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          5   NO                  PARTLY
  12 flattest honest table                      16   NO                  NO — unnest RAISES
  13 needed the shape in advance?                    NO for 1, 2, 5, 7
  14 survives the next file unchanged?               Q1/Q2/Q5 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~120, and the dtype walk is 5

**polars HAS A `Null` DTYPE AND IT IS THE ONLY TOOL HERE THAT SAYS SO OUT LOUD.**
Three fields are null on **all 100 issues** — `type`, `active_lock_reason`,
`performed_via_github_app` — and a fourth, `pinned_comment`, is null on all 16
issues that carry it. polars types those columns **`Null`**. That is a schema
fact, not a count of holes, and it is exactly the thing this corpus keeps saying
frames cannot express.

    pandas    object column, all NaN     — indistinguishable from empty
    DuckDB    JSON                        — the "could not infer" fallback
    polars    Null                        — a type that MEANS null

**AND IT DOES NOT BUILD pandas' GHOST COLUMN.** `closed_by` is an object on 48
issues and null on 52. pandas emits **20 columns** — an entirely empty
`closed_by` plus 19 populated `closed_by.*`. polars emits **one** Struct column
with 52 nulls. Same document, same field: one tool multiplies it by twenty and
leaves an empty decoy, the other keeps it whole.

**IT STILL FAILS THE DISCRIMINATOR, AND SO DOES EVERY FRAME.** Of 36 fields, 5
are sometimes ABSENT and 8 are always present but sometimes NULL. polars reports
**13 columns with nulls** — exactly 5 + 8 — and cannot separate them. `null_count`
counts holes, and a hole has no history. `14-nyc-311` has zero nulls so this cost
nothing there; this document has 709.

**AND THEN `unnest` REFUSES TO FLATTEN THE DOCUMENT AT ALL.**
`DuplicateError: column with name 'html_url' has more than one occurrence`.
**`unnest` does not prefix**, and this document has `url` at the top level and
inside six nested objects. Measured below: **26 colliding names, 58 columns that
must be renamed by hand** before a flat table exists. `VERDICT.md` records the
same failure on `25-usgs-quakes`, where three fields were called `type`. **The
finding generalises to a second document and gets twenty times worse.** pandas'
`json_normalize` prefixes automatically and never collides — which is the reason
it produced 144 columns and the ghost, so the two behaviours are the same
decision seen from opposite ends.

**Question 2 is right for the third file running**: walking the dtype tree gives
4, which is the probe's depth, where pandas' dotted names say 3 because
`json_normalize` never enters `labels[]`.
"""
import json
import time
from collections import Counter
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))
n = len(doc)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
t0 = time.time()
df = pl.read_json(RAW)
print(f"\nQ0  pl.read_json: {df.shape} in {time.time() - t0:.2f}s — no refusal.")
print("    It refused 14-nyc-311 and DuckDB refused 13-package-lock; this file")
print("    troubles neither. No duplicate-key, big-int or NaN report. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
print(f"\nQ1  {df.width} columns — the record's own fields, not flattened.")
print("    pandas gives 144 for the same document because it expands the nested")
print("    objects into dotted names; polars keeps them as Structs.")

# ── Q2. How deep does it go — walking the dtype tree. ────────────────────────
def dtype_depth(dt):
    if isinstance(dt, pl.Struct):
        return 1 + max((dtype_depth(f.dtype) for f in dt.fields), default=0)
    if isinstance(dt, pl.List):
        return 1 + dtype_depth(dt.inner)
    return 0


deep = max(dtype_depth(d) for d in df.dtypes)
# The row is level 2: read_json unwrapped the outer array, so `$` is 1 and the
# issue object is 2. On 13-package-lock the document was ONE object and the row
# was level 1 — the offset is a property of the document, not of polars.
print(f"\nQ2  deepest dtype nests {deep} levels below the row; the row is level 2")
print(f"    (the file is an array of issues), so the document is {2 + deep} deep.")
print("    THE PROBE PRINTS 4. pandas says 3, because json_normalize stops at")
print("    `labels[]` and never reaches `labels[].name`. Third file running that")
print("    the dtype walk gets this right and the dotted names do not.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
nulls = df.null_count().row(0)
print(f"\nQ3  one record is an issue: {df.height} rows x {df.width} cols,"
      f" {sum(nulls) / (df.height * df.width):.1%} null")
print("    The probe prices the FLATTENED shape at `100 rows x 144 cols 53%")
print("    empty`; polars is describing the 36-column one, so the percentages")
print("    are not comparable. It names one candidate and prices none. PARTLY.")
print(f"Q7  {df.height} issues")

# ── Q4. Always present vs sometimes. THE DISCRIMINATOR. ─────────────────────
absent = sorted(k for k in {k for r in doc for k in r}
                if sum(k in r for r in doc) < n)
nullish = sorted(k for k in {k for r in doc for k in r}
                 if sum(k in r for r in doc) == n
                 and sum(r.get(k) is not None for r in doc) < n)
reported = sorted(c for c, x in zip(df.columns, nulls) if x > 0)
print(f"\nQ4  THE TRUTH: {len(absent)} sometimes ABSENT, {len(nullish)} always present but NULL")
print(f"      absent: {absent}")
print(f"      null  : {nullish}")
print(f"Q4  polars reports {len(reported)} columns with nulls — and"
      f" {len(absent)} + {len(nullish)} = {len(absent) + len(nullish)}.")
print(f"    identical sets: {reported == sorted(set(absent) | set(nullish))}")
print("    `null_count` counts HOLES, and a hole has no history. NO.")

# ── Q5. Does any field change type? AND THE `Null` DTYPE. ───────────────────
null_typed = [c for c, dt in zip(df.columns, df.dtypes) if dt == pl.Null]
print(f"\nQ5  no column carries two dtypes — one dtype per column is the model, and")
print("    on this document the model is RIGHT: the probe reports no field that")
print("    changes type here. pandas' python-type check reports 9, all of them")
print("    the Q4 hole against the real type.")
print(f"\nQ5b polars types {len(null_typed)} columns `Null`: {null_typed}")
print("    THAT IS A SCHEMA FACT, NOT A COUNT. Three of them are null on all 100")
print("    issues and `pinned_comment` on all 16 that carry it. pandas gives an")
print("    all-NaN object column; DuckDB falls back to JSON; polars has a TYPE")
print("    that means null, and it is the only tool here that does.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — GitHub ships fixed field names. n/a, and the")
print("    probe's KEYS THAT ARE DATA section is empty for this file.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
print(f"\nQ8  {df.select('number', 'title', 'state').height} rows x 3 cols")
print(df.select("number", "state").head(3))

# ── Q9. A field missing from some records — AND NO GHOST. ───────────────────
cb_null = df.select(pl.col("closed_by").struct.field("login")).null_count().row(0)[0]
print(f"\nQ9  `closed_by` is ONE Struct column, {df.height - nulls[df.columns.index('closed_by')]}"
      " non-null of 100")
print(f"    closed_by.login null on {cb_null} — the same 52 issues, consistently")
print("    pandas turns this ONE field into TWENTY columns: an entirely empty")
print("    `closed_by` plus 19 populated `closed_by.*`. polars does not, because")
print("    a null Struct is a null Struct rather than a value it failed to expand.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
labels = (df.select("number", "labels").explode("labels", empty_as_null=True)
            .drop_nulls("labels").unnest("labels"))
print(f"\nQ10 labels exploded to {labels.height} x {labels.width}")
print(labels.select("number", "name").head(3))
print("    `explode` keeps a null row for the 40 issues with no labels; the")
print("    drop_nulls is mine. pandas' record_path drops them silently.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
hits = {c: int(df[c].str.contains("http").sum())
        for c, dt in zip(df.columns, df.dtypes) if dt == pl.String}
hits = {c: v for c, v in hits.items() if v}
print(f"\nQ11 top-level string columns holding a URL: {len(hits)}, {sum(hits.values())} values")
print("    The truth is 77 paths and 3,297 values. Everything inside the Structs")
print("    and Lists — `user.avatar_url`, `labels[].url` — needs its own")
print("    expression, because the loop must skip any dtype `.str` cannot enter.")
print("    PARTLY.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
structs = [c for c, dt in zip(df.columns, df.dtypes) if isinstance(dt, pl.Struct)]
print(f"\nQ12 unnest of the {len(structs)} Struct columns:")
try:
    flat = df.unnest(*structs)
    print(f"    {flat.shape} — it worked, which contradicts the recorded claim.")
except Exception as e:
    print(f"    {type(e).__name__}: {e}")

names = Counter()
for c, dt in zip(df.columns, df.dtypes):
    if isinstance(dt, pl.Struct):
        names.update(f.name for f in dt.fields)
    else:
        names[c] += 1
dup = {k: v for k, v in names.items() if v > 1}
print(f"\nQ12 `unnest` DOES NOT PREFIX, so flattening collides:")
print(f"    {len(dup)} names occur more than once; {sum(v - 1 for v in dup.values())}"
      " columns must be renamed by hand.")
print(f"    worst: {dict(sorted(dup.items(), key=lambda kv: -kv[1])[:6])}")
print("    `url` appears at the top level and inside user, closed_by, milestone,")
print("    assignee, pull_request and reactions — seven times.")
print("    THIS IS ENTRY 25's FAILURE ON A SECOND DOCUMENT. There `unnest` hit 3")
print("    columns called `type` on ordinary GeoJSON; here it is 58 renames.")
print("    pandas' json_normalize prefixes automatically and never collides.")
print("\nQ12 Three List columns also remain — labels, assignees,")
print("    issue_field_values — and `issue_field_values` is an EMPTY LIST on all")
print("    100 issues, which is why a naive path walk counts 180 where the probe")
print("    counts 179: no element path under an array that never has an element.")
