"""polars — NYC 311 service requests, the 20,000 most recent

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   28.1 MB, 20,000 records, depth 4
  measured      2026-08-11
  run           cd corpus/14-nyc-311/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               6   -                   REFUSES — see below
   1 what is in here                             3   NO                  yes
   2 how deep                                    8   NO                  YES — best here
   3 what is one record                          4   NO                  PARTLY
   4 always present vs sometimes                 5   NO                  YES — exactly right
   5 does any field change type                  4   NO                  YES — and honestly
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          4   NO                  PARTLY
  12 flattest honest table                       3   NO                  yes
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7
  14 survives the next file unchanged?               only with infer_schema_length=None
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~110, and the dtype walk is 8

**THE HEADLINE IS QUESTION 0, AND IT IS THE ONLY 'REFUSES' IN THIS DIRECTORY.**
`pl.read_json('../source.json')` ABORTS. It does not warn, degrade, or drop a
column — it raises `ComputeError` and returns nothing. VERDICT.md recorded this
refusal from a note and it is now written up, and the write-up CHANGES it: on
`04-gharchive` polars aborted with `expected null in json value, got object`,
which names nothing you can act on. **Here the message names the field** —
`extra field in struct data: bridge_highway_direction` — and that field is on
**46 of 20,000 records, 0.23%**, one of the six rarest in the document. polars
found the rarest thing in the file and put it in the error message.

**It is still a refusal, and the fix is still question 4's answer.**
`infer_schema_length=None` reads it in 0.1 s. You only know to pass it once you
know the document is ragged, which is the question you opened the tool to ask.

**AND THEN IT IS THE MOST ACCURATE TOOL IN THE DIRECTORY.** 13 always and 35
sometimes — the probe's numbers EXACTLY, not pandas' 13 and 36 — because polars
keeps `location` as one `Struct` column instead of splitting it into dotted
children. Its schema is the only one here that carries the document's shape:
`Struct({'type': String, 'coordinates': List(Float64)})` is depth 4 written down,
and walking it answers question 2 correctly where json_normalize says 2.

**ONE THING FOUND BY RUNNING IT TWICE, WHICH IS WHY THE METHOD SAYS TO.** The
column order is not the document's AND IS NOT STABLE BETWEEN RUNS — `unique_key`,
the first field of every record, came back at position 16, then 8, then 11 on
three consecutive runs of one unchanged line. The first draft of this file
confidently named two positions; both were wrong by the next run. The rare
fields at the tail stay put, so it is the common ones that shuffle.
"""
import time
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
# polars is the only tool in this directory that REFUSES the file.
print("\nQ0  pl.read_json with defaults:")
try:
    pl.read_json(RAW)
    print("    ...it worked, which contradicts the recorded claim.")
except Exception as e:
    print(f"    {type(e).__name__}: {e}")
    print("    It named `bridge_highway_direction`, which is on 46 of 20,000")
    print("    records. The abort is a schema inference failure, not a health")
    print("    report: polars still says nothing about duplicate keys or NaN.")

t0 = time.time()
df = pl.read_json(RAW, infer_schema_length=None)
print(f"\nQ0  infer_schema_length=None: {df.shape} in {time.time() - t0:.1f}s")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
print(f"\nQ1  {df.width} columns")
print("   ", df.columns)
print("    NOT IN DOCUMENT ORDER, AND NOT STABLE BETWEEN RUNS. `unique_key` is the")
print("    first field of every record; three consecutive runs of this exact line")
print("    put it at position 16, 8 and 11. Re-run this file and the list above")
print("    changes. The tail is stable — the rare fields, discovered late — so it")
print("    is the common ones that shuffle. Nothing warns you, and any code that")
print("    selects a column by position is silently wrong on the next run.")

# ── Q2. How deep does it go — by walking the dtype tree. ─────────────────────
def dtype_depth(dt):
    if isinstance(dt, pl.Struct):
        return 1 + max(dtype_depth(f.dtype) for f in dt.fields)
    if isinstance(dt, pl.List):
        return 1 + dtype_depth(dt.inner)
    return 0

deepest = max(dtype_depth(dt) for dt in df.dtypes)
print(f"\nQ2  deepest column dtype nests {deepest} levels below the row:")
print(f"    location = {df.schema['location']}")
print(f"    row is level 2 (array of objects), so the document is {2 + deepest} deep.")
print("    THIS IS CORRECT. polars is the only frame tool here that keeps the")
print("    nesting in the schema instead of flattening it into dotted names.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
nulls = df.null_count().row(0)
holes = sum(nulls) / (df.height * df.width)
print(f"\nQ3  one record is a request: {df.height:,} rows x {df.width} cols")
print(f"Q3  {holes:.1%} of that table is null — the probe prices its 49-col shape at 25%")
print("    polars names ONE candidate and prices nothing. PARTLY.")
print(f"Q7  {df.height:,} records")

# ── Q4. Always present vs sometimes. EXACTLY RIGHT. ──────────────────────────
always = [c for c, n in zip(df.columns, nulls) if n == 0]
some = sorted(((c, df.height - n) for c, n in zip(df.columns, nulls) if n > 0),
              key=lambda kv: kv[1])
print(f"\nQ4  always: {len(always)} — {always}")
print(f"Q4  sometimes: {len(some)}, rarest five:")
for c, n in some[:5]:
    print(f"      {c:34} {n:6,} of {df.height:,}")
print("    13 and 35 IS THE PROBE'S ANSWER EXACTLY. pandas says 13 and 36 because")
print("    it splits `location` in two; polars keeps it whole, so the counts match")
print("    the document's own fields. Correct here only because there are ZERO")
print("    nulls in the file — every null in this frame is an absence.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  dtypes polars inferred:")
print("   ", {str(t) for t in df.dtypes})
print("    47 String + 1 Struct, and NO field varies. That is the truth: every")
print("    scalar in this document is a JSON string, floats only inside coordinates.")
print("    polars cannot report a per-field type change at all — one dtype per")
print("    column is the model — but the model is RIGHT here, where pandas' more")
print("    flexible check invented 36 changes that do not exist.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections. n/a — and the `:@computed_region_*` names")
print("    survive as ordinary column names, needing no quoting in polars.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = df.select("complaint_type", "borough", "created_date")
print(f"\nQ8  {t.height:,} rows x {t.width} cols")
print(t.head(3))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
kept = df.select("unique_key", "status", "closed_date")
n_present = kept.height - kept["closed_date"].null_count()
print(f"\nQ9  closed_date present on {n_present:,} of {kept.height:,}; rows kept")
print(kept.head(3))

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
coords = (df.select(pl.col("location").struct.field("coordinates"))
            .drop_nulls()
            .select(pl.col("coordinates").list.get(0).alias("lon"),
                    pl.col("coordinates").list.get(1).alias("lat")))
print(f"\nQ10 coordinates to {coords.height:,} x {coords.width}")
print(coords.head(3))

# ── Q11. Find every path whose value matches something — here, a URL. ────────
hits = {c: int(df[c].str.contains("http").sum())
        for c, dt in zip(df.columns, df.dtypes) if dt == pl.String}
print(f"\nQ11 string columns holding a URL: { {c: n for c, n in hits.items() if n} }")
print("    Correct — 19 of 20,000, buried in resolution_description's prose. But")
print("    the loop had to SKIP the Struct column to avoid a type error, so this")
print("    is a scan of the flat columns, not of every path.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat = df.unnest("location")
print(f"\nQ12 unnest('location') gives {flat.height:,} x {flat.width}")
print("    coordinates remains List(Float64) — one list-column, the thing god's")
print("    spec refuses. Nothing else is lost: no field was dropped or coerced.")
