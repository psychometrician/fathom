"""pandas — one hour of public GitHub events

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json.gz   10.6 MB gzipped, 50 MB / 37,883 records raw
  measured      2026-08-09
  run           cd corpus/04-gharchive/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 2   no                  YES
   1 what is in here                             3   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 3   no                  YES
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   no                  YES

WHY THIS FILE. pandas reads gzipped NDJSON in one call with `lines=True` and
infers compression from the extension, so it is the least ceremony of anything
here. The cost is what it does to the nested half.
"""
import resource
import subprocess
import sys
import time
from importlib.metadata import version

import pandas as pd

print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")

def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3

# ── 0 / 7. one call, gzip and NDJSON both handled ────────────────────────────
t0 = time.time()
df = pd.read_json("../source.json.gz", lines=True)
elapsed = time.time() - t0
print(f"\n0/7. pd.read_json('../source.json.gz', lines=True) -> "
      f"{len(df):,} rows x {df.shape[1]} cols in {elapsed:.1f}s")
print("     gzip inferred from the extension, NDJSON from `lines=True`, and no")
print("     schema flag was needed — polars aborted here without one.")

# ── 1. what is in here ───────────────────────────────────────────────────────
print(f"\n1. columns: {list(df.columns)}")
nested = [c for c in df.columns if df[c].map(lambda v: isinstance(v, (dict, list))).any()]
print(f"   of which hold dicts or lists: {nested}")
print("   those arrive as Python objects in object-dtype cells. pandas has")
print("   described the top level and stored the rest.")

# ── 4. always present vs sometimes ───────────────────────────────────────────
missing = df.isna().sum()
print(f"\n4. columns null on some rows:")
for c, n in missing[missing > 0].items():
    print(f"     {c:<22} null on {n:,} of {len(df):,}")

ONE_READ = ("import pandas as pd, resource, sys;"
            "pd.read_json('../source.json.gz', lines=True);"
            "r=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;"
            "print(r/1e6 if sys.platform=='darwin' else r/1e3)")
clean = float(subprocess.run([sys.executable, "-c", ONE_READ],
                             capture_output=True, text=True).stdout.strip())
print(f"\n   peak RSS, one read in a clean process: {clean:,.0f} MB")
print(f"   ijson 71 · DuckDB 133 · probe 968 (20,000 sample) · polars 1,076")

print("""
2, 3, 5, 6. cannot.

  `payload` is an object-dtype column of dicts. pandas will not look inside it,
  so depth, polymorphism and keys-as-data all stop at the top level, and
  `json_normalize` cannot help because the payload's shape depends on `type`.

  This is the cheapest read in the comparison and the shallowest description.
  Both facts are the same fact: pandas answered question 0 and question 7 by
  declining to look at the part of the document the other questions are about.
""")
