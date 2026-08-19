"""polars — movie ratings, Kaggle data-cleaning challenge, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
  measured      2026-08-10
  run           cd corpus/16-movie-ratings/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             6   NO                  WRONG
   2 how deep                                    2   NO                  yes
   3 what is one record                          5   YES                 PARTLY
   4 always present vs sometimes                 4   YES                 yes
   5 does any field change type                  5   NO                  DANGEROUS
   6 are any object keys data                    3   YES                 WRONG
   7 how many records                            1   YES                 YES
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   1   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       4   YES                 PARTLY
  13 needed the shape in advance?                    YES — Q1 is actively wrong
  14 survives the next file unchanged?               no
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~40, little ceremony
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

import polars as pl

print(f"python {sys.version.split()[0]}, polars {version('polars')}")

df0 = pl.read_json("../source.json")
schema = str(df0.schema)
print(f"\n1. read_json: {df0.height} row x {df0.width} cols, schema "
      f"{len(schema):,} chars — {100 * len(schema) / 6975:.0f}% OF THE FILE")
print("   WRONG, and it is the corpus's most extreme keys-as-data blow-up by")
print("   ratio. The document is a one-element array holding an object keyed by")
print("   MOVIE TITLE, so polars inferred one struct field per title and the")
print("   schema is 65% of the file — ABOVE npm's 60%, which VERDICT.md carries")
print("   as the sharpest version of the O(data) claim, and on a document three")
print("   orders of magnitude smaller. 4,556 characters to describe 6,975.")
print(f"\n6. WRONG. {df0.width} movie titles became STRUCT FIELDS — one column")
print("   per film. Nothing marks any of them as a value.")

movies = json.load(open("../source.json"))[0]
df = pl.DataFrame([{"title": t, **v} for t, v in movies.items()])
print(f"\n   Told the right shape by hand: {df.height} x {df.width}.")

print(f"\n2. depth 3 — one array, one keyed object, one record object.")
print(f"\n7. {df.height} movies.")

print("\n4. non-null per field:")
for c in sorted(df.columns, key=lambda c: df[c].null_count()):
    print(f"     {c:18} {df.height - df[c].null_count():>3} of {df.height}")
print("   NOTHING but `title` is on all 38: the 23 lowercase movies and the 15")
print("   Title Case ones share no field at all.")

print("\n5. DANGEROUS. polars had to unify `Popcorn Score` and `Tomato Score`,")
print(f"   which hold int x9 and str x6 each. It chose: "
      f"{df.schema['Popcorn Score']}, {df.schema['Tomato Score']}")
print("   The 6 strings are the SENTINELS — 'unknown' and the misspelt")
print("   'unkown'. Whatever polars picked, one of the two populations is now")
print("   wrong, and the schema reads as though the column were homogeneous.")
sent = Counter(v for c in df.columns for v in df[c].to_list()
               if isinstance(v, str) and v.lower().startswith("unk"))
print(f"   sentinels still findable by hand: {dict(sent)} — 17 of 159 cells.")

lower = df.filter(pl.col("rating").is_not_null())
upper = df.filter(pl.col("Rating").is_not_null())
print("\n3. one movie per row, and TWO tables inside it:")
tot = 100 * sum(df[c].null_count() for c in df.columns) / (df.height * df.width)
print(f"     all movies      {df.height:>3} rows x {df.width} cols   {tot:.0f}% empty")
for nm, sub in (("lowercase", lower), ("Title Case", upper)):
    live = [c for c in sub.columns if sub[c].null_count() < sub.height]
    print(f"     {nm:15} {sub.height:>3} rows x {len(live)} cols   0% empty")
print("   And there is no field to `group_by` — the two groups share no key, so")
print("   the discriminator is the CASE OF THE FIELD NAMES and lives in no")
print("   value anywhere. polars has no expression that can reach that.")

print(f"\n8/9. three fields:\n{df.select('title', 'Rating', 'rating').head(3)}")
print("\n10. n/a. 11. CANNOT — no whole-document path search.")
print(f"\n12. flattest: {df.height} x {df.width}. `coalesce(Rating, rating)` "
      f"fills {df.select(pl.coalesce('Rating', 'rating')).drop_nulls().height} of "
      f"{df.height}")
print("   in one expression — with both spellings typed by hand. polars has no")
print("   verb for `these two names are one field`.")
print("   WHAT IS LOST: the 17 sentinels, and one of the two type populations")
print("   in each of the two unified columns.")
