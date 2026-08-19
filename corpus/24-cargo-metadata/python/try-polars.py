"""polars — cargo metadata for this repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   27 KB, 8 packages, depth 8
  measured      2026-08-11
  run           cd corpus/24-cargo-metadata/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             8   YES                 PARTLY
   2 how deep                                    5   NO                  YES — 6 + 2 = 8
   3 what is one record                          4   YES                 one of nine
   4 always present vs sometimes                 6   NO                  PARTLY
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                   14   NO                  IT PUTS THEM IN THE TYPE
   7 how many records                             2  NO                  yes
   8 three named fields to a table                2 YES                 yes
   9 a field missing from some rows                2 YES                 PARTLY
  10 flatten the deepest array                     4 YES                 yes
  11 find every path matching something            4 NO                  PARTLY
  12 flattest honest table                         4 NO                  yes
  13 needed the shape in advance?                    yes — `packages` by name
  14 survives the next file unchanged?               NO — THE SCHEMA IS THE DATA
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~95

  polars PUTS THE FEATURE NAMES IN THE TYPE. `features` becomes a Struct with
  one field per Cargo feature, so the DTYPE of this frame is this repository's
  dependency graph — a stronger commitment than pandas' column names, because a
  dtype is a value the rest of the program can be written against.

  AND IT COSTS NOTHING TO ESCAPE. `pl.col("features").struct.field("zlib-ng-compat")`
  is a string argument, so polars is the only frame here that neither breaks nor
  needs quoting on the 14 hyphenated feature names. IT STILL BUILT THEM INTO THE
  SCHEMA, which is question 6 answered wrongly and comfortably.
"""
import json
import time
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))
pkgs = doc["packages"]

print("\nQ0  polars has its own reader and no health report. CANNOT.")

env = pl.read_json(RAW)
print(f"\nQ1  read_json on the file -> {env.height} x {env.width}: the ENVELOPE,")
print(f"    one row. {env.columns[:5]} …")
t = time.time()
df = pl.DataFrame(pkgs, infer_schema_length=None)
print(f"Q1  pl.DataFrame(packages) -> {df.height} x {df.width} in {time.time()-t:.3f}s")


def depth(dt, d=1):
    if isinstance(dt, pl.Struct):
        return max([depth(f.dtype, d + 1) for f in dt.fields] or [d])
    if isinstance(dt, pl.List):
        return depth(dt.inner, d + 1)
    return d


dp = max(depth(df.schema[c]) for c in df.columns)
print(f"\nQ2  deepest column nests {dp} below the row; packages are 2 levels in,")
print(f"    so {dp} + 2 = {dp+2} — the probe says 8.")

# ── Q6. THE CENTREPIECE. ────────────────────────────────────────────────────
ft = df.schema["features"]
names = [f.name for f in ft.fields] if isinstance(ft, pl.Struct) else []
print(f"\nQ6  THE PROBE CALLS $.packages[].features KEYS THAT ARE DATA.")
print(f"    polars typed it {str(ft)[:64]}…")
print(f"    {len(names)} struct FIELDS, one per Cargo feature: {names[:6]} …")
hy = [n for n in names if "-" in n]
print(f"Q6  {len(hy)} of them contain a HYPHEN, and polars does not care —")
print('    `pl.col("features").struct.field("zlib-ng-compat")` is a string')
print("    argument. It is the only frame here that neither breaks nor needs")
print("    quoting on these names. IT STILL BUILT THEM INTO THE SCHEMA.")
print("    THAT IS A STRONGER COMMITMENT THAN PANDAS' COLUMN NAMES, because a")
print("    dtype is a value the rest of the program can be written against —")
print("    and `cargo add` changes it. QUESTION 14 IS NO, and not because the")
print("    ATTEMPT named a column: because the SCHEMA is a function of the data.")

# ── Q3/Q4/Q5/Q7. ────────────────────────────────────────────────────────────
nulls = sum(df.null_count().row(0))
print(f"\nQ3  an item of packages: {df.height} x {df.width}, "
      f"{nulls/(df.height*df.width):.0%} null")
print("    the probe prices the same candidate at 8 x 57, 63% empty, because it")
print("    counts the FLATTENED columns — polars keeps `features` as one Struct")
print("    column, so its width is smaller and its emptiness is elsewhere.")
ncols = {c: n for c, n in zip(df.columns, df.null_count().row(0)) if n}
alln = [c for c, n in ncols.items() if n == df.height]
rk = [set(p) for p in pkgs]
print(f"\nQ4  columns with any null: {len(ncols)}; 100% NULL: {alln}")
print(f"Q4  the document: {len([k for k in set().union(*rk) if sum(k in p for p in rk) < len(pkgs)])}"
      " keys ever ABSENT — every package has all 24.")
print("    Every null is a WRITTEN null and four columns are nothing else.")
print(f"\nQ5  polars unified every column; the probe reports NO type change, and")
print("    jq confirms zero once `an empty array is not a type` is applied.")
print(f"\nQ7  {len(pkgs)} packages, {len(doc['workspace_members'])} workspace members,"
      f" {len(doc['resolve']['nodes'])} resolve nodes")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
print(f"\nQ8  {df.select('name', 'version', 'edition').shape}")
print(df.select("name", "version", "edition").head(2))
print(f"\nQ9  `description` null on {df['description'].null_count()} of {df.height}, rows kept")
print("\nQ10 explode+unnest targets:")
try:
    df.select("name", "targets").explode("targets").unnest("targets")
    print("    succeeded unrenamed — rewrite this note")
except Exception as e:
    print(f"    RAISES: {type(e).__name__}: {' '.join(str(e).split())[:66]}")
    print("    A TARGET HAS ITS OWN `name`, so unnesting collides with the")
    print("    package's. SECOND DOCUMENT WHERE POLARS RAISES ON THIS — entry 21")
    print("    was `DOI` under `reference[]`. pandas needs `meta_prefix` and says")
    print("    so; polars raises and names no fix; DuckDB renamed silently on")
    print("    entry 20. Three tools, three behaviours, confirmed twice now.")
t = time.time()
tg = (df.select(pl.col("name").alias("pkg"), "targets")
        .explode("targets").unnest("targets"))
print(f"    renamed first: {tg.height} x {tg.width}, {time.time()-t:.3f}s")
print("    THE DEEPEST array is resolve.nodes[].deps[].dep_kinds[], not under")
print("    `packages` at all, so this frame cannot reach it.")
strs = [c for c in df.columns if df.schema[c] == pl.String]
u = [c for c in strs if df[c].str.contains(r"^https?://").any()]
print(f"\nQ11 of {len(strs)} String columns, {len(u)} hold a URL: {u}")
print("    jq reports 5 distinct URL PATHS; two are inside")
print("    `metadata.release.pre-release-replacements[]`, out of a column scan's reach.")
print(f"\nQ12 {df.height} x {df.width} with Struct and List columns intact. Unnesting")
print(f"    `features` would add {len(names)} columns whose names are data —")
print("    THE HONEST TABLE IS NARROWER THAN THE FLAT ONE, and the difference is")
print("    exactly question 6.")
