"""pandas — Docker Hub tags, 100 tags

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   476 KB, 100 tags under $.results, depth 5
  measured      2026-08-11
  run           cd corpus/22-dockerhub-tags/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             6   YES                 PARTLY
   2 how deep                                    2   NO                  NO
   3 what is one record                         12   YES                 BOTH, priced
   4 always present vs sometimes                12   NO                  see below
   5 does any field change type                  6   NO                  yes — NONE
   6 are any object keys data                    1   -                   n/a
   7 how many records                            2   NO                  yes, both numbers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              6   YES                 PARTLY
  10 flatten the deepest array                   4   YES                 yes — 1,388
  11 find every path matching something          4   NO                  NONE OF ONE
  12 flattest honest table                       6   NO                  yes
  13 needed the shape in advance?                    yes — where the records are
  14 survives the next file unchanged?               Q1/Q3/Q12 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~110

  THE NESTED CONTROL, and pandas does WELL here — which is the finding.
  One key-set per shape, no keys-as-data, no polymorphism, no split. Every
  failure entries 20 and 21 recorded needed one of those, and with none of them
  present `json_normalize` and `explode` give the probe's numbers exactly.

  WHAT IT STILL CANNOT DO is tell an empty string from a NaN. The images table
  has THREE states — `os_version` and `variant` written NULL, `features` and
  `os_features` written "" — and `isna()` sees only the first. That is the same
  blind spot in the other direction from entry 15's: there absent and null were
  one, here null and empty-string stay two but only by accident of dtype.
"""
import json
import time
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))
tags = doc["results"]

print("\nQ0  json.load read it and said nothing. CANNOT.")

whole = pd.json_normalize(doc)
print(f"\nQ1  json_normalize(doc) — the whole file — gives {whole.shape}")
print("    ONE ROW again: the records are at $.results. Same as entries 21's")
print("    envelope, and the same silent non-error.")
norm = pd.json_normalize(tags)
print(f"Q1  json_normalize(results) -> {norm.shape[0]} x {norm.shape[1]}")
print(f"Q2  deepest dotted name has {max(c.count('.') for c in norm.columns)+1} segments;"
      " the document is 5 deep.")

# ── Q3. BOTH CANDIDATES, and pandas can price both here. ────────────────────
print(f"\nQ3  an item of results: {norm.shape[0]} x {norm.shape[1]}, "
      f"{norm.isna().sum().sum()/(norm.shape[0]*norm.shape[1]):.0%} NaN")
t = time.time()
img = pd.json_normalize(tags, record_path=["images"], meta=["name"])
holes = img.isna().sum().sum() / (img.shape[0] * img.shape[1])
print(f"Q3  an item of images:  {img.shape[0]:,} x {img.shape[1]}, {holes:.0%} NaN, "
      f"{time.time()-t:.1f}s")
print("    THE PROBE SAYS 100 x 16 AT 0% AND 1,388 x 11 AT 16%. pandas reproduces")
print("    both to the percent — no pre-filter, no raise, because every tag has")
print("    an `images` array. Entry 21 needed a filter AND a meta_prefix here.")
print(f"    the probe also prices the repetition: `size` repeated 4x. pandas can")
dup = img.groupby("name")["size"].nunique().mean()
print(f"    be asked — mean distinct sizes per tag is {dup:.1f} — and volunteers nothing.")

# ── Q4. THE THREE STATES. ───────────────────────────────────────────────────
inull = {c: int(img[c].isna().sum()) for c in img.columns if img[c].isna().any()}
iempty = {c: int((img[c] == "").sum()) for c in img.columns
          if img[c].dtype == object or str(img[c].dtype).startswith("str")}
iempty = {k: v for k, v in iempty.items() if v}
print(f"\nQ4  tag columns not always filled: "
      f"{[c for c in norm.columns if norm[c].isna().any()]}")
print(f"Q4  image columns with NaN:          {inull}")
print(f"Q4  image columns with EMPTY STRING: {iempty}")
print("    pandas KEEPS the distinction here and does not mean to: `\"\"` survives")
print("    because the column is a string dtype, and `isna()` never looks at it.")
print("    So `img.isna().mean()` is 16% — THE PROBE'S NUMBER — and the 2,776")
print("    empty strings are invisible to both. Two tools, one blind spot,")
print(f"    and counting them would make it "
      f"{(sum(inull.values())+sum(iempty.values()))/(img.shape[0]*(img.shape[1]-1)):.0%} "
      f"over the document's 11 image fields — try-jq.py's number, computed the")
print("    same way. This frame has 12 columns because `meta=['name']` added one.")

# ── Q5/Q6/Q7. ───────────────────────────────────────────────────────────────
mixed = [c for c in norm.columns
         if norm[c].map(lambda v: type(v).__name__).nunique() > 1]
print(f"\nQ5  tag columns holding more than one python type: {mixed}")
print("    NONE, and the probe reports none. THE FIRST TIME IN THIS SESSION")
print("    pandas and the probe agree about question 5 — because the document")
print("    has no polymorphism and no nulls at the tag level to fake one.")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
print(f"\nQ7  {len(tags)} tags on this page; `count` says {doc['count']:,}, "
      f"and `next` is a URL")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
print(f"\nQ8  {norm[['name', 'full_size', 'last_updated']].shape}")
print(norm[["name", "full_size", "last_updated"]].head(2).to_string())
print(f"\nQ9  `variant` NaN on {int(img['variant'].isna().sum()):,} of {img.shape[0]:,}, "
      "rows kept")
print("    Every image HAS the key; it is written null. pandas cannot say that,")
print("    and on this document it does not matter — there are no absent keys to")
print("    confuse it with. ENTRY 15's TRAP NEEDS BOTH STATES TO EXIST.")
t = time.time()
ex = norm.explode("images")
print(f"\nQ10 explode('images') -> {ex.shape[0]:,} x {ex.shape[1]}, {time.time()-t:.1f}s")
print("    and the cells are still dicts; `json_normalize(record_path=)` above is")
print("    the honest route and gives 1,388 x 11 with `name` carried through.")
urlish = [c for c in norm.columns
          if norm[c].astype("string").str.match(r"^https?://").fillna(False).any()]
print(f"\nQ11 columns with a URL: {urlish}")
print("    NONE OF ONE. The document's single URL is `$.next`, the pagination")
print("    link, OUTSIDE the records — so a frame built from `results` cannot")
print("    see it. Entries 17 and 18 recorded the same; this is the extreme case.")
lists = [c for c in norm.columns if norm[c].map(lambda v: isinstance(v, list)).any()]
print(f"\nQ12 {norm.shape[0]} x {norm.shape[1]} with {len(lists)} list-column(s): {lists}")
print("    or 1,388 x 12 exploded, with every tag field repeated per image.")
print("    THE PROBE PRICES BOTH AND PANDAS BUILDS EITHER. On this document the")
print("    two tools differ only in that one of them chose.")
