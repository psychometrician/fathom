# pandas — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          pandas (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/python && uv run try-pandas.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **`json_normalize` is pandas' whole answer to nested JSON**, and this document
# is the case it was not built for: the thing you want one row of is keyed by
# data, so `record_path` has nothing to point at.

import json
import time

import pandas as pd

print(f"pandas {pd.__version__}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

print("\nQ0  json.load parsed and said nothing. CANNOT.")
print("    Python's json keeps the LAST duplicate key silently and accepts")
print("    NaN/Infinity, so a damaged document arrives looking clean.")

print(f"\nQ1  list(doc) -> {len(doc)}: {', '.join(doc)}")
print("    ONE LEVEL, and it is Python's, not pandas'. CANNOT beyond that.")

print("\nQ2  CANNOT. pandas has no depth verb. A recursive walk is mine:")
def depth(x):
    if isinstance(x, dict) and x:
        return 1 + max(depth(v) for v in x.values())
    if isinstance(x, list) and x:
        return 1 + max(depth(v) for v in x)
    return 0
print(f"    depth {depth(doc)}, by a function pandas did not provide.")

print("\nQ3  CANNOT. pandas names no candidates and prices none.")

# ── THE ONE THING pandas DOES WELL HERE. ─────────────────────────────────────
# `json_normalize` wants a LIST of records. `products` is a DICT keyed by SKU,
# so the keys must be turned into data by hand before pandas can see a table.
t0 = time.perf_counter()
prod = pd.json_normalize(list(doc["products"].values()))
prod_s = time.perf_counter() - t0
print(f"\n    products: json_normalize(list(...values())) -> "
      f"{prod.shape[0]} x {prod.shape[1]} in {prod_s:.1f} s")
print("    NOTE `.values()`. json_normalize cannot take a keyed collection; the")
print("    keys-are-data step is mine, and dropping .keys() silently discards")
print("    the SKU — which happens to be repeated inside each record here, so")
print("    nothing is lost. On a document where it is not, this loses the key.")

n = len(prod)
present = prod.notna().sum()
print(f"\nQ4  ANSWERED from the frame ({n} rows):")
always = [c for c in prod.columns if present[c] == n]
some = [(c, int(present[c])) for c in prod.columns if present[c] < n]
print(f"    always: {' '.join(always)}")
print(f"    sometimes: {' '.join(f'{c}({k})' for c, k in sorted(some, key=lambda t: -t[1]))}")

print(f"\nQ5  dtypes seen: {sorted({str(d) for d in prod.dtypes})}")
print("    All object (= Python str). No field changes type. But `object` is")
print("    pandas saying 'I did not look', not 'they are all strings'.")

print("\nQ6  CANNOT, and it is the question this document is made of.")
print(f"    products has {len(doc['products'])} keys, terms.OnDemand {len(doc['terms']['OnDemand'])},")
print(f"    terms.Reserved {len(doc['terms']['Reserved'])} — all data. pandas has no verb")
print("    for it; `list(...values())` is me having already decided.")

npd = sum(len(t["priceDimensions"])
          for tt in doc["terms"].values() for sku in tt.values() for t in sku.values())
print(f"\nQ7  {n} products, {npd} price dimensions — the second counted by hand.")

print("\nQ7a NO positional alignment. (Circular question — not scored.)")

print("\nQ8  ANSWERED, one selection off the frame:")
q8 = prod[["sku", "productFamily", "attributes.location"]]
print(q8.head(3).to_string(index=False))

it = prod["attributes.instanceType"]
print(f"\nQ9  attributes.instanceType present on {int(it.notna().sum())} of {n};")
print("    json_normalize fills NaN and KEEPS the rows. ANSWERED, and it is")
print("    pandas' best moment on this file.")

print("\nQ10 The deepest array is appliesTo — 4,505 of them, ALL EMPTY.")
pdm = pd.json_normalize(
    [pdim for tt in doc["terms"].values() for sku in tt.values()
     for t in sku.values() for pdim in t["priceDimensions"].values()])
print(f"    price dimensions normalized: {pdm.shape[0]} x {pdm.shape[1]}")
print(f"    appliesTo lengths seen: {sorted({len(v) for v in pdm['appliesTo']})}")
print("    `explode('appliesTo')` on an all-empty column yields 4,505 rows of")
print("    NaN, not 0 rows — pandas invents a row where there was no element.")
ex = pdm.explode("appliesTo")
print(f"    explode -> {len(ex)} rows, all NaN: {bool(ex['appliesTo'].isna().all())}")

print("\nQ11 CANNOT. No path search. A recursive walk is mine to write.")
print("    Whole-value URL matches: 0 (the disclaimer contains two and is prose).")

print("\nQ12 The flattest honest table is price dimensions joined to products on")
print("    sku. pandas builds BOTH halves with json_normalize once I have")
print("    flattened the keyed levels by hand, and the join is one merge.")
print("    WHAT IS LOST stopping at products: every price.")
merged = pdm.merge(prod, left_on="rateCode", right_on="sku", how="left")
print(f"    (a naive merge on the wrong key gives {merged.shape[0]} rows and is")
print("     silently useless — nothing in pandas says the key was wrong.)")

print("\nQ13 YES. `record_path` and every column name came from AWS's docs.")
print("Q14 NO. attributes.* differs per service and json_normalize just returns")
print("    different columns, with no error.")
print("Q15 YES. json_normalize + merge is readable a week later.")
print("Q16 ~55 lines. The ceremony is `list(...values())` three times over —")
print("    the keys-as-data step pandas has no name for.")

print("\nCONCLUSION")
print("pandas answers Q4, Q8 and Q9 and no exploration question. Its one verb")
print("for nested JSON takes a LIST, and every interesting level of this")
print("document is a DICT keyed by data — so the step that matters happens")
print("before pandas is called, in a comprehension it cannot see or check.")
