# polars — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          polars (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/python && uv run try-polars.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **polars types everything, which makes it the loudest tool of the fourteen on
# this document** — `read_json` infers a struct schema and the schema IS the
# field list. It is also where keys-as-data hurts most: a struct with 1,571
# fields is a legal schema and polars will happily build one.

import json
import time

import polars as pl

print(f"polars {pl.__version__}")

t0 = time.perf_counter()
df = pl.read_json("../source.json")
print(f"read_json: {time.perf_counter() - t0:.1f} s -> {df.shape[0]} x {df.shape[1]}")

with open("../source.json") as fh:
    doc = json.load(fh)

print("\nQ0  read_json parsed and said nothing about soundness. CANNOT.")

print(f"\nQ1  ANSWERED at the top: {df.width} columns — {', '.join(df.columns)}")
print("    AND ANSWERED DEEPER, by the inferred schema, which is polars' real")
print("    contribution here:")
prods = df.select("products").dtypes[0]
print(f"    products dtype is a Struct with {len(prods.fields)} FIELDS —")
print("    one per SKU. polars read 1,571 data values as a SCHEMA.")
print("    That is a real answer to Q1 and the wrong answer to Q6, from one")
print("    inference, and nothing distinguishes them.")

print("\nQ2  PARTIAL. The nested dtype has a depth and polars will print it, but")
print("    there is no depth verb; measuring it means walking the dtype myself.")
def dt_depth(dt):
    if isinstance(dt, pl.Struct):
        return 1 + max((dt_depth(f.dtype) for f in dt.fields), default=0)
    if isinstance(dt, pl.List):
        return 1 + dt_depth(dt.inner)
    return 0
print(f"    walking the dtype gives {max(dt_depth(d) for d in df.dtypes) + 1}.")

print("\nQ3  CANNOT. polars names no candidates and prices none.")

# ── The table, once the keyed level is flattened BY HAND. ────────────────────
t0 = time.perf_counter()
prod = pl.DataFrame(list(doc["products"].values())).unnest("attributes")
prod_s = time.perf_counter() - t0
print(f"\n    products: pl.DataFrame(list(...values())).unnest('attributes')")
print(f"    {prod.height} x {prod.width} in {prod_s:.1f} s")
print("    `.values()` again — the keys-as-data step is mine in every tool.")

n = prod.height
nn = {c: prod[c].null_count() for c in prod.columns}
print(f"\nQ4  ANSWERED ({n} rows), from null counts:")
print(f"    always: {' '.join(c for c in prod.columns if nn[c] == 0)}")
print(f"    sometimes: {' '.join(f'{c}({n - nn[c]})' for c in prod.columns if nn[c])}")

print(f"\nQ5  ANSWERED, and better than pandas: {sorted({str(d) for d in prod.dtypes})}")
print("    polars gives a REAL type per column, not `object`. A field that")
print("    changed type would have forced a supertype or an error here.")

print("\nQ6  CANNOT — and polars fails at it the most spectacularly of the")
print("    fourteen, because it succeeds. The inferred schema treats 1,571 SKUs")
print("    as 1,571 struct fields, so `df['products']` is a ONE-ROW frame that")
print("    is 1,571 columns wide once unnested. That is exactly the 100%-empty")
print("    table fathom's own menu prices, produced silently and called a schema.")
wide = df.select("products").unnest("products")
print(f"    df.select('products').unnest('products') -> {wide.height} x {wide.width}")

npd = sum(len(t["priceDimensions"])
          for tt in doc["terms"].values() for sku in tt.values() for t in sku.values())
print(f"\nQ7  {n} products, {npd} price dimensions.")

print("\nQ7a NO positional alignment. (Circular question — not scored.)")

print("\nQ8  ANSWERED:")
print(prod.select(["sku", "productFamily", "location"]).head(3))

print(f"\nQ9  instanceType present on {n - nn['instanceType']} of {n}; nulls kept.")

print("\nQ10 The deepest array is appliesTo and all 4,505 are EMPTY.")
pdm = pl.DataFrame([pdim for tt in doc["terms"].values() for sku in tt.values()
                    for t in sku.values() for pdim in t["priceDimensions"].values()])
print(f"    price dimensions: {pdm.height} x {pdm.width}")
ex = pdm.explode("appliesTo")
print(f"    .explode('appliesTo') -> {ex.height} rows, "
      f"all null: {ex['appliesTo'].null_count() == ex.height}")
print("    polars INVENTS a null row per empty list, like pandas and unlike the")
print("    three R tools, which drop them. Same question, two opposite answers,")
print("    and neither says 'there were 4,505 arrays and all were empty'.")

print("\nQ11 CANNOT. No path search by value.")

print("\nQ12 price dimensions joined to products on sku. polars does the join")
print("    well; the flattening of five keyed levels is mine. WHAT IS LOST")
print("    stopping at products: every price.")

print("\nQ13 YES for the frames, NO for the schema — `read_json` inferred the")
print("    field list with no help, which is a genuine exploration answer.")
print("Q14 NO. A different service infers a different struct, silently.")
print("Q15 YES. unnest/explode/select read back cleanly.")
print("Q16 ~55 lines, low ceremony except the three `.values()` comprehensions.")

print("\nCONCLUSION")
print("polars is the only tool of the fourteen whose PARSER answers question 1")
print("at depth, because inference forces it to name every field. The same")
print("mechanism gives the worst answer to question 6 in the whole comparison:")
print("it reads 1,571 SKUs as a schema, builds the 1,571-column table without")
print("complaint, and calls the result typed.")
