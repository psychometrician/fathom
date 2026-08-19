"""pandas — movie ratings, Kaggle data-cleaning challenge, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
  measured      2026-08-10
  run           cd corpus/16-movie-ratings/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  WRONG
   2 how deep                                    2   -                   CANNOT
   3 what is one record                          6   YES                 PARTLY
   4 always present vs sometimes                 6   NO                  yes
   5 does any field change type                  6   NO                  PARTLY
   6 are any object keys data                    5   YES                 WRONG
   7 how many records                            2   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              4   YES                 yes
  10 flatten the deepest array                   1   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       6   YES                 PARTLY
  13 needed the shape in advance?                    YES — Q1 is actively wrong
  14 survives the next file unchanged?               no
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~40, little ceremony

THE SECOND GROUND TRUTH IN THE CORPUS. Rachael Tatman's data-cleaning challenge,
whose published point is that the same field appears under two spellings and that
missing values are written as the word "unknown". Both are structural, both are
here, and what each tool does with them is the measurement.
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

import pandas as pd

print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")
doc = json.load(open("../source.json"))

# ── 1, 6. what is in here — and json_normalize gets it backwards ─────────────
flat = pd.json_normalize(doc)
print(f"\n1. json_normalize(doc): {flat.shape[0]} row x {flat.shape[1]} cols")
print(f"   first three columns: {list(flat.columns)[:3]}")
print("   WRONG, and instructively so. The document is a ONE-ELEMENT ARRAY")
print("   holding an object keyed by MOVIE TITLE, so json_normalize produced")
print("   one row and a column per title-and-field — `12 Strong.Genre`,")
print("   `A Ciambra.rating`. **The keys that are data became column names and")
print("   the 38 records became one row.** That is the keys-as-data failure at")
print("   full strength on a 7 KB file.")
print(f"\n6. WRONG. 38 movie titles are values; pandas made {flat.shape[1]} columns")
print("   out of them and nothing marks any of them as data.")

movies = doc[0]
df = pd.DataFrame.from_dict(movies, orient="index")
print(f"\n   Told the right shape, `from_dict(orient='index')` gives "
      f"{df.shape[0]} x {df.shape[1]} — which needed knowing the answer first.")

# ── 2, 10, 11 ────────────────────────────────────────────────────────────────
print("\n2. CANNOT. depth is 3; json_normalize reports no nesting because it")
print("   flattened all of it into column names.")
print("\n10. n/a — no nested array. 11. CANNOT — no whole-document search.")

# ── 4. the striking one ──────────────────────────────────────────────────────
print("\n4. non-null count per field, over the 38 movies:")
for k, v in df.notna().sum().sort_values(ascending=False).items():
    print(f"     {k:18} {int(v):>3} of {len(df)}")
print("   **NOTHING is present on all 38.** The 23 lowercase movies and the 15")
print("   Title Case ones share NO FIELD AT ALL — the key-sets are disjoint.")
print("   pandas reports this correctly and the 54% of holes it implies is not")
print("   raggedness: it is two documents in one file.")

# ── 5. the type change, and the sentinels underneath it ──────────────────────
print("\n5. dtypes:", dict(df.dtypes.astype(str)))
for f in ("Popcorn Score", "Tomato Score"):
    print(f"     {f:18} {dict(Counter(type(v).__name__ for v in df[f].dropna()))}")
print("   `object` on both, which is pandas for `I have no idea`. Underneath:")
print("   9 ints and 6 strings each, and the 6 strings are the SENTINELS —")
print("   'unknown' on Popcorn Score, 'unkown' (misspelt) on Tomato Score.")
sent = Counter((f, v) for f in df.columns for v in df[f].dropna()
               if isinstance(v, str) and v.lower().startswith("unk"))
print(f"   sentinels found by hand: {dict(sent)}")
print("   17 of the 159 present cells. pandas counts every one as PRESENT, so")
print("   its 54% empty is really 58%. No dtype, no `isna`, no verb sees this.")

# ── 3, 7 ─────────────────────────────────────────────────────────────────────
print(f"\n7. {len(df)} movies.")
print("\n3. one movie per row, and there are TWO tables inside it:")
lower = df[df["rating"].notna()]
upper = df[df["Rating"].notna()]
print(f"     all movies      {len(df):>3} rows x {df.shape[1]} cols   "
      f"{100 * df.isna().mean().mean():.0f}% empty")
for nm, sub in (("lowercase", lower), ("Title Case", upper)):
    live = [c for c in sub.columns if sub[c].notna().any()]
    print(f"     {nm:15} {len(sub):>3} rows x {len(live)} cols   "
          f"{100 * sub[live].isna().mean().mean():.0f}% empty")
print("   54% to 0%. And there is NO DISCRIMINATOR FIELD to split on — the two")
print("   groups share no key, so the thing that separates them is the CASE OF")
print("   THE FIELD NAMES. No value in the document tells you which group a")
print("   movie is in. That is a shape the corpus has not had before.")

# ── 8, 9, 12 ─────────────────────────────────────────────────────────────────
t = df[["Rating", "rating", "Genre"]]
print(f"\n8. three fields:\n{t.head(3).to_string()}")
print(f"\n9. `Genre` is NaN on {int(t['Genre'].isna().sum())} of {len(t)} rows, "
      f"all kept — the 23 lowercase movies never had it.")

merged = df["Rating"].fillna(df["rating"])
print(f"\n12. flattest honest table: {len(df)} x {df.shape[1]}.")
print(f"   `Rating.fillna(rating)` collapses the two spellings to "
      f"{merged.notna().sum()} of {len(df)} filled — one line, and it needs both")
print("   names typed by hand. pandas has no verb for `these are one field`.")
print("   WHAT IS LOST: the 17 sentinels, still counted as data; and the fact")
print("   that this is two tables, still counted as one 54%-empty one.")
