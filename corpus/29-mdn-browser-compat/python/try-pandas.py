# pandas — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          pandas (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/python && uv run try-pandas.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **`json_normalize` is pandas' whole answer to a nested document**, and this
# file measures what it does here rather than describing it. The tool-sweep
# prediction was that it explodes — over 100,000 columns or dies trying — and
# the point of writing that down first is that it could come out otherwise.

import json
import time
import pandas as pd

print(f"pandas {pd.__version__}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

print("\nQ0  json.load parsed and said nothing.")
d = json.loads('{"a":1,"a":2}')
print(f"    duplicate keys {{'a':1,'a':2}} -> {d}   (last wins, silent)")
print(f"    9007199254740993 -> {json.loads('{\"n\":9007199254740993}')['n']}  (exact — Python has bignums)")
print("    ** AND THAT IS THE ONE PLACE PYTHON BEATS R HERE. ** jsonlite gives")
print("    9007199254740992. design/implementation.md is why neither fathom")
print("    binding parses JSON: a parser per language makes the two disagree.")
print("    Still CANNOT — it read correctly and reported nothing.")

# ── Q1/Q2. ───────────────────────────────────────────────────────────────────
print(f"\nQ1  list(doc) -> {len(doc)} keys: {', '.join(doc)}")
print("    ONE LEVEL. pandas has no field listing.")


def depth(x):
    if isinstance(x, dict) and x:
        return 1 + max(depth(v) for v in x.values())
    if isinstance(x, list) and x:
        return 1 + max(depth(v) for v in x)
    return 0


t0 = time.perf_counter()
print(f"\nQ2  {depth(doc)}, by a recursive function I wrote "
      f"({time.perf_counter() - t0:.1f} s). pandas contributed nothing.")

# ── THE MEASUREMENT. json_normalize at increasing depth. ─────────────────────
print("\n── json_normalize, one max_level at a time ──────────────────────────────")
print("  max_level      rows x cols        seconds      memory")
for lvl in (0, 1, 2, 3, 4, None):
    t0 = time.perf_counter()
    try:
        df = pd.json_normalize(doc, max_level=lvl)
        s = time.perf_counter() - t0
        mb = df.memory_usage(deep=True).sum() / 1e6
        print(f"  {str(lvl):<12} {df.shape[0]:>6,} x {df.shape[1]:>9,} {s:>10.2f} s {mb:>9.1f} MB")
        widest = df
    except Exception as e:
        print(f"  {str(lvl):<12} FAILED after {time.perf_counter()-t0:.1f} s: "
              f"{type(e).__name__}: {str(e)[:70]}")

print("\nQ12 ONE ROW. Every max_level gives a single row and more columns,")
print("    because the document's root is an OBJECT, not an array of records.")
print("    json_normalize's contract is `list of dicts -> one row each`, and")
print("    this document is one dict. PARTLY at best, and the table it")
print("    produces is a document turned sideways rather than a table.")

# ── The record-shaped attempt: treat api as the record list. ─────────────────
print("\n── the honest attempt: hand pandas a list of records ────────────────────")
recs = [{"feature": k, **v.get("__compat", {})} for k, v in doc["api"].items()
        if isinstance(v, dict) and "__compat" in v]
t0 = time.perf_counter()
api = pd.json_normalize(recs)
print(f"  api __compat records -> {api.shape[0]:,} x {api.shape[1]:,} "
      f"in {time.perf_counter()-t0:.2f} s")
print(f"  columns (first 8): {', '.join(list(api.columns)[:8])}")
print("  ** THAT WORKS, AND THE `api` WAS MINE. ** Question 3 is the one that")
print("  chose it, and pandas neither named the candidate nor priced it.")

# ── Q4/Q5. ───────────────────────────────────────────────────────────────────
miss = api.isna().sum()
print(f"\nQ4  columns always present: {(miss == 0).sum()} of {api.shape[1]}")
print(f"    emptiest column: {miss.idxmax()} missing in {miss.max():,} of {len(api):,}")
print("    yes, once the record list is chosen — and choosing it is Q3.")

va = [c for c in api.columns if c.endswith("version_added")]
print(f"\nQ5  {len(va)} version_added columns after the normalize.")
if va:
    col = api[va[0]]
    kinds = col.map(lambda z: type(z).__name__).value_counts()
    print(f"    types actually in {va[0]}:")
    for k, n in kinds.items():
        print(f"      {k:<10} {n:>8,}")
    print(f"    dtype pandas assigned: {col.dtype}")
    print("    ** PARTLY, AND TWICE QUALIFIED. ** The values keep their Python")
    print("    types inside an `object` column, so a str and a bool sit side by")
    print("    side — but the dtype says `object` and nothing reports it. You")
    print("    find out by calling type() yourself, which is not the tool")
    print("    answering. Compare jq, where `type` is a first-class function.")
    print("    AND THE `float` COUNT IS PANDAS' OWN. Those are NaN, written by")
    print("    the normalize where a record had no such key — not a third type")
    print("    in the document. jq says this field is string and boolean only.")
    print("    A type census over a normalized frame counts the tool's fills.")

print("\nQ3  pandas names no candidates and prices none. CANNOT.")
print("Q6  CANNOT.")

# ── Q8/Q9/Q10/Q11. ───────────────────────────────────────────────────────────
three = api[["feature", "mdn_url", "source_file"]].head(2)
print(f"\nQ8  three named fields -> {three.shape[0]} x {three.shape[1]}. yes,")
print("    once the record list exists.")
print(f"\nQ9  mdn_url missing in {api['mdn_url'].isna().sum():,} of {len(api):,} rows,")
print("    and those rows survive as NaN. YES.")

print("\nQ10 json_normalize has record_path for exactly this, but it needs the")
print("    path NAMED. The deepest arrays here sit under a browser key that")
print("    varies, so there is no single record_path. CANNOT without a loop.")
print("\nQ11 CANNOT. pandas has no search over paths.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

THE PREDICTION WAS THAT json_normalize EXPLODES, AND IT DOES: 1 ROW x 427,019
COLUMNS. It does not die — 3.5 seconds, 21 MB — which makes it worse rather
than better, because a failure would at least have said so. The progression is
the whole result: 14 columns at max_level=0, then 1,163, 11,101, 24,835,
98,059, and 427,019 with no limit. Every one of them is ONE ROW.

THE REASON IS STRUCTURAL AND NOT A SETTING. json_normalize's contract is `a
list of dicts becomes a row each`, and this document's root is a single dict.
Every level it descends therefore widens rather than lengthens. That is not a
document fathom is unusually good at and pandas unusually bad at; it is a tool
whose input shape this file does not have.

HAND IT A RECORD LIST AND IT IS EXCELLENT. 1,090 x 134 in 0.02 seconds, dotted
column names, NaN where a key is absent, and every rectangular question after
that is easy — Q4, Q8 and Q9 are one line each. THE `api` WAS MINE, and
choosing it is question 3, which pandas neither answers nor helps with. That is
the division this corpus keeps finding: pandas is superb once somebody has said
what a row is, and says nothing about what a row could be.

ONE THING PYTHON WINS OUTRIGHT AND IT IS NOT PANDAS'. `json.load` reads
9007199254740993 exactly where jsonlite gives …992, because Python has
arbitrary-precision integers and base R does not. That difference is why
design/implementation.md forbids either fathom binding from parsing JSON: two
parsers would make the two languages disagree about a value the health verb
exists to warn about.

AND A TRAP WORTH RECORDING. Counting value types over a normalized frame counts
PANDAS' fills, not the document's: version_added shows str/bool/float, and the
float is NaN written by the normalize. The document has no floats there at all.
""")
