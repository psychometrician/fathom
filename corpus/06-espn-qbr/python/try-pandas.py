"""pandas — ESPN quarterback rating, 2019

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   176 KB, 28 athletes
  measured      2026-08-09
  run           cd corpus/06-espn-qbr/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   no                  YES
   3 what is one record                          2   YES                 YES
   7 how many records                            1   YES                 YES
   7a related by position, not nesting           5   no                  CANNOT
"""
import json, sys
from importlib.metadata import version
import pandas as pd
print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")
doc = json.load(open("../source.json"))

df = pd.json_normalize(doc["athletes"])
print(f"\n1/3/7. json_normalize(doc['athletes']) -> {df.shape[0]} rows x "
      f"{df.shape[1]} cols, {df.isna().to_numpy().mean():.1%} NaN")
print(f"   the tutorial this file comes from produces 28 rows x 14 cols.")
print(f"   pandas gets the ROW right unaided; the columns are a person's choice.")

tot = pd.DataFrame([a["categories"][0]["totals"] for a in doc["athletes"]])
print(f"\n7a. the ten statistics as pandas sees them: {tot.shape[0]} x {tot.shape[1]}")
print(f"    column names: {list(tot.columns)}")
print(f"    the real names, from categories[0].labels:")
print(f"      {doc['categories'][0]['labels']}")
print(f"    and glossary, same length, sorted differently:")
print(f"      {[g['abbreviation'] for g in doc['glossary']]}")
print("""    pandas numbered the columns 0..9 because the array carries no names.
    Naming them needs `labels`, which lives in a different subtree, and there is
    no pandas operation that relates two arrays by position across subtrees —
    `set_axis` will do it once a person supplies the list, which is the tutorial's
    approach and is why the tutorial hard-codes the names.""")
