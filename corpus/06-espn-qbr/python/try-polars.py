"""polars — ESPN quarterback rating, 2019

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   176 KB, 28 athletes
  measured      2026-08-09
  run           cd corpus/06-espn-qbr/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   no                  PARTLY
   7 how many records                            2   YES                 YES
   7a related by position, not nesting           4   no                  CANNOT
"""
import json, sys
from importlib.metadata import version
import polars as pl
print(f"python {sys.version.split()[0]}, polars {version('polars')}")
df = pl.read_json("../source.json")
size = len(open("../source.json", "rb").read())
print(f"\n1. columns: {len(df.schema)}; schema {len(str(df.schema)):,} chars "
      f"({len(str(df.schema))/size:.2%} of the file)")
print("   it reads this one without a flag — the first easy document polars has")
print("   met in the corpus, and the only one it has not fought.")
doc = json.load(open("../source.json"))
print(f"\n7. rows polars reports: {df.height}. Athletes inside: {len(doc['athletes'])}")
ath = df.schema["athletes"]
inner = str(ath)
i = inner.find("totals")
print(f"\n7a. the `totals` entry inside the athletes type:")
print(f"     {inner[i:i+46] if i >= 0 else '(not found)'}")
print(f"     and `labels`, in a different column entirely:")
j = str(df.schema['categories']).find('labels')
print(f"     {str(df.schema['categories'])[j:j+46] if j >= 0 else '(n/a)'}")
print("""    The ten statistics are a list of strings and the schema says so. It
    cannot say they are named by `categories[0].labels`, because a type describes
    one value and this is a relationship between two. No type system in the
    comparison expresses positional correspondence, and all three here — polars,
    DuckDB, pandas — fail identically and silently.""")
