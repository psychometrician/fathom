"""polars — USGS earthquakes, one month

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   7.4 MB, 10,885 features, depth 5
  measured      2026-08-10
  run           cd corpus/25-usgs-quakes/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             8   YES — it RAISED     PARTLY
   2 how deep                                    6   NO                  yes — 5
   3 what is one record                          4   YES                 PARTLY
   4 always present vs sometimes                 3   NO                  PARTLY
   5 does any field change type                  3   -                   CANNOT
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               1   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   5   YES                 yes
  11 find every path matching something          3   NO                  PARTLY
  12 flattest honest table                       2   NO                  yes
  13 needed the shape in advance?                    WORSE THAN THAT — see below
  14 survives the next file unchanged?               no
  15 readable a week later?                          the renames need the comment
  16 lines, and how much is ceremony?                ~105, and 6 are the workaround

**`unnest` RAISES ON ORDINARY GEOJSON**, which is the result of this run:

    polars.exceptions.DuplicateError: could not create a new DataFrame:
    column with name 'type' has more than one occurrence

**Three fields are called `type`** — the feature's (`"Feature"`), the
properties' (`"earthquake"`) and the geometry's (`"Point"`) — and `unnest`
flattens without prefixing, so two of them have to be renamed BY HAND before
anything works. `pandas.json_normalize` has no such trouble because it prefixes
everything: `type` and `properties.type` are different names there.

**Question 13 asks whether you needed to know the shape in advance. Here the
honest answer is that you needed to have already FAILED once** — the collision
is invisible until the exception, and the exception names the symptom rather
than the two levels that collided.

**Two places polars beats pandas on this file**, both worth recording because
the corpus's polars entries are mostly losses: **Q2 answers 5** from the struct
schema where `json_normalize` says 2, and **Q5's single-dtype resolution is at
least honest** — polars types `tz` as `Null` rather than inventing a type for a
column that is empty on all 10,885 rows.
"""
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  polars reads it or raises. It says nothing about duplicate keys,")
print("    ints past 2^53, or a field holding an encoded document. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
# The whole file is one object, so polars needs to be pointed at the array.
df = pl.read_json("../source.json")
print(f"\nQ1  whole file: {df.shape[0]} row x {df.shape[1]} cols — {df.columns}")

feats = df.select("features").explode("features").unnest("features")
print(f"Q1  after explode+unnest: {feats.shape[0]:,} x {feats.shape[1]} — {feats.columns}")

# **`unnest` RAISES ON THIS DOCUMENT, and the reason is ordinary GeoJSON.**
#   polars.exceptions.DuplicateError: could not create a new DataFrame:
#   column with name 'type' has more than one occurrence
# A feature has `type` ("Feature") and so does `properties` ("earthquake"), and
# `unnest` flattens without prefixing, so the two collide. pandas'
# `json_normalize` has no such trouble because it prefixes everything —
# `type` and `properties.type` are different names there.
#
# The fix is to rename before unnesting, which means KNOWING THE COLLISION IS
# COMING. Question 13 asks exactly that, and on this file the answer is not
# "did you need the shape" but "did you need to have already failed once".
# THREE fields are called `type` — the feature's, the properties', and the
# geometry's — so two of them have to be renamed by hand before anything flattens.
feats = feats.rename({"type": "feature_type"})
flat = (feats
        .with_columns(pl.col("geometry").struct.rename_fields(["geom_type", "coordinates"]))
        .unnest("properties")
        .unnest("geometry"))
print(f"Q1  after unnesting properties and geometry: {flat.shape[1]} columns")
print("   ", flat.columns)


def depth(dt, d=1):
    if isinstance(dt, pl.Struct):
        return max(depth(f.dtype, d + 1) for f in dt.fields)
    if isinstance(dt, pl.List):
        return depth(dt.inner, d + 1)
    return d


print(f"Q2  deepest nesting polars can see from the schema: "
      f"{max(depth(t) for t in df.schema.values())}")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  a feature: {flat.shape[0]:,} rows x {flat.shape[1]} cols")
nulls = sum(flat[c].null_count() for c in flat.columns)
print(f"Q3  {nulls / (flat.shape[0] * flat.shape[1]):.1%} null")
print(f"Q7  {flat.shape[0]:,} features")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
some = {c: flat.shape[0] - flat[c].null_count()
        for c in flat.columns if flat[c].null_count()}
print(f"\nQ4  always: {flat.shape[1] - len(some)} columns")
print(f"Q4  sometimes (non-null count): {some}")
print("    Same limit as pandas: a struct field that was ABSENT and one that was")
print("    NULL are both null here, because unnest built a column for every key.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  polars gives ONE dtype per column, so it cannot report a change —")
print("    it resolves one. What it inferred:")
print({c: str(t) for c, t in list(flat.schema.items())[:8]}, "…")
print("    That resolution is the answer AND the reason the question is unanswerable.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections in this document. n/a")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
print("\nQ8 ", flat.select("mag", "place", "time").head(3))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
print("\nQ9  alert is non-null on",
      flat.shape[0] - flat["alert"].null_count(), "of", f"{flat.shape[0]:,}")
print(flat.select("place", "alert").head(3))

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
coords = flat.select(
    pl.col("coordinates").list.get(0).alias("lon"),
    pl.col("coordinates").list.get(1).alias("lat"),
    pl.col("coordinates").list.get(2).alias("depth_km"),
)
print(f"\nQ10 {coords.shape[0]:,} x {coords.shape[1]}")
print(coords.head(3))

# ── Q11. Find every path whose value matches something — here, a URL. ────────
urlish = [c for c, t in flat.schema.items()
          if t == pl.String and flat[c].str.starts_with("http").mean() and
          (flat[c].str.starts_with("http").mean() or 0) > 0.9]
print(f"\nQ11 string columns whose values are URLs: {urlish}")
print("    A column scan again. polars has no path language, so 'every path'")
print("    means 'every column I already decided to build'.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print(f"\nQ12 {flat.shape[0]:,} x {flat.shape[1]}. `coordinates` stays list[f64] —")
print("    a list-column, which god's spec refuses. Nothing else is nested.")

# ── The packed strings, because defect 26 came from this file. ───────────────
print("\nDEFECT 26  does polars notice a list packed into a string?")
print(flat.select("types", "ids", "sources").head(2))
print("    dtype String. Correct, and no more useful than pandas'.")
