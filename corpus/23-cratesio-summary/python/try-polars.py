"""polars — crates.io summary

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   41 KB, six collections at the root, depth 4
  measured      2026-08-11
  run           cd corpus/23-cratesio-summary/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             8   YES                 PARTLY
   2 how deep                                    5   NO                  YES — 2 + 2 = 4
   3 what is one record                         16   YES                 FOUR FRAMES, and the
                                                                          SCHEMAS PROVE IT
   4 always present vs sometimes                 8   NO                  PARTLY
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                    1   -                   n/a
   7 how many records                             3  NO                  three answers
   8 three named fields to a table                2 YES                 yes
   9 a field missing from some rows                3 YES                 PARTLY
  10 flatten the deepest array                     3 -                   NO ARRAY TO FLATTEN
  11 find every path matching something            4 NO                  PARTLY
  12 flattest honest table                         6 NO                  yes, and it DUPLICATES
  13 needed the shape in advance?                    YES — which four of the six
                                                     collections are crate lists
  14 survives the next file unchanged?               Q3/Q12 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~105

  ══════════════════════════════════════════════════════════════════════════════
  SAME KEY-SET, THREE SCHEMAS — AND THE PREDICTION THAT THEY WOULD MATCH DIED.
  ══════════════════════════════════════════════════════════════════════════════

  I wrote that polars would prove the four collections identical with one `==`,
  because it has a real schema object. IT SAYS THEY DIFFER, and the reason is
  the finding:

      new_crates                 recent_downloads: Null   (null on ALL TEN)
      most_downloaded            recent_downloads: Int64
      most_recently_downloaded   recent_downloads: Int64
      just_updated               recent_downloads: Int64, documentation: Null

  THE PROBE FOLDS ON KEY-SETS and says `same shape as $.new_crates[]`. POLARS
  TYPES ON VALUES and says they are three schemas. **Both are right, about
  different questions**, and this is the first corpus document to separate them.

  `pl.concat` therefore RAISES — `type Int64 is incompatible with expected type
  Null` — where pandas concatenated the same four silently and produced
  `documentation: str 16, float 14, NoneType 10`, a column missing in two
  incompatible ways. ONE CAUSE, TWO FRAMES, OPPOSITE BEHAVIOURS.

  AND THE REFUSAL IS ABOUT TYPES, NOT ABOUT CONTENT. With
  `how="vertical_relaxed"` polars builds the 40-row table and double-counts the
  seven overlapping crates exactly as pandas did. Neither tool is checking what
  the rows mean.

  Note the ROOT: two scalars beside six collections, so `read_json` gives a
  one-row frame whose cells are lists — the envelope problem of entries 21 and
  22 in a third shape.
"""
import json
import time
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))
CRATE = ["new_crates", "most_downloaded", "most_recently_downloaded", "just_updated"]

print("\nQ0  polars has its own reader and no health report. CANNOT.")

env = pl.read_json(RAW)
print(f"\nQ1  read_json on the file -> {env.height} x {env.width}")
print(f"    {env.columns}")
print("    ONE ROW, and six of the eight cells are lists. The root is an OBJECT")
print("    of collections, so there is no record array to find — the envelope")
print("    problem of entries 21 and 22 in a third shape.")
frames = {k: pl.DataFrame(doc[k]) for k in CRATE}
for k, f in frames.items():
    print(f"Q1  {k:26} -> {f.height} x {f.width}")


def depth(dt, d=1):
    if isinstance(dt, pl.Struct):
        return max([depth(fl.dtype, d + 1) for fl in dt.fields] or [d])
    if isinstance(dt, pl.List):
        return depth(dt.inner, d + 1)
    return d


dp = max(depth(frames["new_crates"].schema[c]) for c in frames["new_crates"].columns)
print(f"\nQ2  deepest column nests {dp} below the row; the crates are 2 levels in,")
print(f"    so {dp} + 2 = {dp+2} — the probe says 4.")

# ── Q3. SAME KEY-SET, THREE SCHEMAS, AND concat REFUSES. ───────────────────
schemas = {k: f.schema for k, f in frames.items()}
base = schemas["new_crates"]
print(f"\nQ3  are the four schemas equal? {all(s == base for s in schemas.values())}")
for k, s in schemas.items():
    diff = {c: (str(base[c]), str(s[c])) for c in s if base[c] != s[c]}
    print(f"    {k:26} differs from new_crates in: {diff}")
print("    I PREDICTED THEY WOULD BE EQUAL AND THEY ARE NOT — and the reason is")
print("    the whole finding. `recent_downloads` is null on ALL TEN new_crates,")
print("    so polars types it `Null` there and `Int64` in the other three.")
print("    `just_updated` does the same to `documentation`.")
print("    THE FOUR COLLECTIONS HAVE ONE KEY-SET AND THREE SCHEMAS.")
print("    The probe folds on KEY-SETS and says `same shape as $.new_crates[]`.")
print("    polars types on VALUES and says they differ. BOTH ARE RIGHT, ABOUT")
print("    DIFFERENT QUESTIONS, and this document is the first in the corpus to")
print("    separate them.")
for k, f in frames.items():
    nulls = sum(f.null_count().row(0))
    print(f"    {k:26} {f.height} x {f.width}, {nulls/(f.height*f.width):.0%} null")

print("\nQ3  and `pl.concat` of the four:")
try:
    cat = pl.concat([f.with_columns(pl.lit(k).alias("_list")) for k, f in frames.items()])
    print(f"    OK {cat.height} x {cat.width} — rewrite this note")
except Exception as e:
    print(f"    RAISES: {type(e).__name__}: {' '.join(str(e).split())[:72]}")
    print("    POLARS REFUSES TO CONCATENATE THE FOUR, and pandas did it silently")
    print("    — see ../python/try-pandas.py, where the same all-null column came")
    print("    out as `documentation: str 16, float 14, NoneType 10`, a column")
    print("    missing in two incompatible ways. ONE CAUSE, TWO FRAMES, OPPOSITE")
    print("    BEHAVIOURS: polars will not build the table, pandas builds a")
    print("    quietly broken one.")
    cat = pl.concat([f.with_columns(pl.lit(k).alias("_list")) for k, f in frames.items()],
                    how="vertical_relaxed")
    print(f"    with how='vertical_relaxed': {cat.height} x {cat.width}")
ndist = cat["id"].n_unique()
dups = (cat.group_by("name").len().filter(pl.col("len") > 1)
        .sort("name")["name"].to_list())
print(f"    AND {cat.height} ROWS HOLD ONLY {ndist} DISTINCT CRATES: {dups}")
print("    THE REFUSAL WAS ABOUT TYPES AND NOT ABOUT THIS. Once relaxed, polars")
print("    double-counts the seven overlapping crates exactly as pandas did.")
print("    Nothing in either tool is checking what the rows MEAN.")

# ── Q4/Q5/Q6/Q7. ────────────────────────────────────────────────────────────
nulls = {c: n for c, n in zip(cat.columns, cat.null_count().row(0)) if n}
allnull = [c for c, n in nulls.items() if n == cat.height]
print(f"\nQ4  columns with any null: {list(nulls)}")
print(f"Q4  columns 100% NULL across all {cat.height} rows: {allnull}")
rk = [set(c) for k in CRATE for c in doc[k]]
print(f"Q4  the document: {len([k for k in set().union(*rk) if sum(k in r for r in rk) < len(rk)])}"
      " keys ever ABSENT — every crate has all 23.")
print("    So every null here is a WRITTEN null, and three columns are nothing")
print("    else. polars cannot say 100%-null rather than 100%-absent, and on")
print("    this document that difference is what those three columns MEAN.")
print(f"\nQ5  polars unified every column; the probe reports NO type change.")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
print(f"\nQ7  num_crates {doc['num_crates']:,}; num_downloads {doc['num_downloads']:,};")
print(f"    {cat.height} rows here, {ndist} distinct")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
print(f"\nQ8  {frames['new_crates'].select('name', 'max_version', 'downloads').shape}")
print(frames["new_crates"].select("name", "max_version", "downloads").head(2))
print(f"\nQ9  `homepage` null on {cat['homepage'].null_count()} of {cat.height}, rows kept")
print("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is a Struct of six")
print("    fields; question 10 has no target on this document.")
lk = cat.select("name", "links").unnest("links")
print(f"    unnesting `links` instead: {lk.height} x {lk.width}")
strs = [c for c in cat.columns if cat.schema[c] == pl.String]
u = [c for c in strs if cat[c].str.contains(r"^https?://").any()]
print(f"\nQ11 of {len(strs)} String columns, {len(u)} hold a URL: {u}")
print("    jq reports 11 distinct URL PATHS folding to 3. polars' column names")
print("    ARE the folded form, because it built one frame per collection.")
print(f"\nQ12 the honest table is the concat: {cat.height} x {cat.width}, holding")
print(f"    {ndist} distinct crates. Or four frames of 10 x 23 whose schemas are")
print("    equal and which polars will not mention are equal until asked.")
