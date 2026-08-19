"""pandas — crates.io summary

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   41 KB, six collections at the root, depth 4
  measured      2026-08-11
  run           cd corpus/23-cratesio-summary/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             8   YES                 PARTLY
   2 how deep                                    2   NO                  yes — 3 of 4
   3 what is one record                         18   YES                 FOUR FRAMES, no verdict
   4 always present vs sometimes                10   NO                  NO — 3 phantom columns
   5 does any field change type                  6   NO                  yes — NONE
   6 are any object keys data                    1   -                   n/a
   7 how many records                             3  NO                  three answers
   8 three named fields to a table                2  YES                 yes
   9 a field missing from some rows                2 YES                 PARTLY
  10 flatten the deepest array                     4 YES                 no array to flatten
  11 find every path matching something            5 NO                  PARTLY
  12 flattest honest table                         8 NO                  yes, and it DUPLICATES
  13 needed the shape in advance?                    YES — six collections, and which
                                                     four are the same shape
  14 survives the next file unchanged?               Q1/Q3 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~115

  THE DEFECT-25 DOCUMENT. `json_normalize` builds FOUR IDENTICAL FRAMES and has
  no way to say they are identical — you get 10 x 28 four times and must notice
  yourself. Concatenating them, which is the obvious move, produces 40 rows of
  which SEVEN ARE THE SAME CRATE TWICE, and `concat` warns about nothing.

  Three columns — `categories`, `keywords`, `versions` — are NULL ON ALL 40
  RECORDS, so pandas gives them a dtype from nothing and they are entirely NaN.
  A column that is 100% empty is the strongest possible case of the shape cap
  paying for something worthless, and no tool here flags it.
"""
import json
import time
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))
CRATE = ["new_crates", "most_downloaded", "most_recently_downloaded", "just_updated"]

print("\nQ0  json.load read it and said nothing. CANNOT.")

whole = pd.json_normalize(doc)
print(f"\nQ1  json_normalize(doc) -> {whole.shape}")
print(f"    ONE ROW of {whole.shape[1]} columns, and every collection is a list in a")
print("    cell. The root is an OBJECT of six collections and two scalars, so")
print("    there is no single record array for pandas to find.")
frames = {k: pd.json_normalize(doc[k]) for k in CRATE}
for k, f in frames.items():
    print(f"Q1  {k:26} -> {f.shape[0]} x {f.shape[1]}")
print(f"Q2  deepest dotted name has "
      f"{max(c.count('.') for c in frames['new_crates'].columns)+1} segments;"
      " the document is 4 deep.")

# ── Q3. FOUR IDENTICAL FRAMES. ──────────────────────────────────────────────
sig = {k: tuple(sorted(f.columns)) for k, f in frames.items()}
print(f"\nQ3  are the four frames the same shape? "
      f"{len(set(sig.values()))} distinct column-set(s)")
print("    ONE — and pandas said nothing. It built four frames, each 10 x 28,")
print("    and there is no verb that compares them. The probe prints")
print("    `same shape as $.new_crates[]` unasked; that is defect 25's repair.")
for k, f in frames.items():
    print(f"    {k:26} {f.shape[0]} x {f.shape[1]}, "
          f"{f.isna().sum().sum()/(f.shape[0]*f.shape[1]):.0%} NaN")
print("    the probe prices the same four at 16%, 14%, 15% and 17% empty.")

t = time.time()
cat = pd.concat([f.assign(_list=k) for k, f in frames.items()], ignore_index=True)
print(f"\nQ3  pd.concat of the four -> {cat.shape[0]} x {cat.shape[1]}, {time.time()-t:.2f}s")
ndist = cat["id"].nunique()
dups = cat["name"].value_counts()
print(f"    AND {cat.shape[0]} ROWS HOLD ONLY {ndist} DISTINCT CRATES.")
print(f"    appearing twice: {sorted(dups[dups > 1].index.tolist())}")
print("    `concat` warns about nothing. This is the obvious move once you have")
print("    noticed the four shapes agree, and it silently double-counts seven")
print("    crates. NEITHER THE PROBE NOR ANY TOOL HERE REPORTS THE OVERLAP.")

# ── Q4. THE ALWAYS-NULL COLUMNS. ────────────────────────────────────────────
present = cat.notna().sum()
allnull = [c for c in cat.columns if present[c] == 0]
some = [c for c in cat.columns if 0 < present[c] < len(cat)]
print(f"\nQ4  columns that are 100% NaN across all {len(cat)} rows: {allnull}")
print(f"Q4  columns sometimes filled: {some}")
rk = [set(r) for r in sum((doc[k] for k in CRATE), [])]
absent = [k for k in set().union(*rk) if sum(k in r for r in rk) < len(rk)]
print(f"Q4  the document: {len(absent)} keys ever ABSENT — every crate has all 23.")
print("    SO EVERY NaN HERE IS A WRITTEN NULL, and three columns are nothing")
print("    else. pandas cannot say a column is 100% null rather than 100%")
print("    absent, and on this document the difference is the whole of what")
print("    those three columns mean: the API returns the key and omits the data.")

# ── Q5/Q6/Q7. ───────────────────────────────────────────────────────────────
mixed = [c for c in cat.columns
         if cat[c].map(lambda v: type(v).__name__).value_counts()
         .drop("NoneType", errors="ignore").pipe(len) > 1]
print(f"\nQ5  columns holding more than one python type: {mixed}")
for c in mixed:
    kinds = cat[c].map(lambda v: type(v).__name__).value_counts().to_dict()
    print(f"    {c}: {kinds}")
print("    EVERY ONE IS A MISSING-VALUE MARKER BESIDE A STRING — NaN or None,")
print("    depending on how the column was built. FALSE POSITIVES BY THIS")
print("    CORPUS'S OWN RULE: defect 11 and `design/axes.py` both say a null is")
print("    not a type, and the probe reports NO type change on this document.")
print("    The same false positive entries 20 and 25 recorded, here on a")
print("    document with nothing else at all to find.")
print("    AND NOTE `documentation`: str 16, float 14, NoneType 10 — TWO")
print("    DIFFERENT MISSING MARKERS IN ONE COLUMN. The four sub-frames were")
print("    typed independently before `concat`, and at least one of them had")
print("    `documentation` null on all ten rows, so it stayed `object` holding")
print("    None while the others became float NaN. Concatenating four frames")
print("    that pandas will not tell you are the same shape produces a column")
print("    that is missing in two incompatible ways.")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
print(f"\nQ7  num_crates {doc['num_crates']:,}; num_downloads {doc['num_downloads']:,};"
      f" {len(cat)} rows here, {ndist} distinct")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
print(f"\nQ8  {frames['new_crates'][['name', 'max_version', 'downloads']].shape}")
print(frames["new_crates"][["name", "max_version", "downloads"]].head(2).to_string())
print(f"\nQ9  `homepage` filled on {int(present['homepage'])} of {len(cat)}, rows kept")
print("    PARTLY: 19 of those NaN are written nulls and pandas cannot say so —")
print("    though on this document nothing is ever absent, so nothing is lost.")
print("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. The deepest structure is")
print("    `links`, an object of six fields, which json_normalize already")
print("    flattened into `links.owner_team` and friends. Question 10 has no")
print("    target here, which is itself worth recording — it is the first")
print("    corpus document where that is true.")
urlish = [c for c in cat.columns
          if cat[c].astype("string").str.match(r"^https?://").fillna(False).any()]
print(f"\nQ11 columns with a URL: {urlish}")
print("    jq reports 11 distinct URL PATHS, which fold to 3 once the four")
print("    identical collections are collapsed. pandas' column names ARE the")
print("    folded form, because it built one frame per collection — so here the")
print("    frame's blindness to the four-way repetition works in its favour.")
print(f"\nQ12 the honest table is the concat: {cat.shape[0]} x {cat.shape[1]}, and it")
print("    contains seven crates twice. Or four frames of 10 x 28 that pandas")
print("    will not tell you are the same shape. BOTH ANSWERS ARE WRONG IN A")
print("    WAY THE TOOL CANNOT NAME.")
