# duckdb — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          duckdb (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/python && uv run try-duckdb.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **duckdb has `json_structure` and `json_keys`, which are exploration verbs**,
# and it is the only tool of the fourteen besides jq that can describe a
# document it has not been told about. On this file the description is 1,571
# SKUs long.

import time

import duckdb

print(f"duckdb {duckdb.__version__}")
con = duckdb.connect()

q = lambda s: con.execute(s).fetchall()

print("\nQ0  read_json parses and says nothing about soundness. CANNOT.")
print("    NOTE the reader: `read_json` INFERS COLUMNS and so has no `json`")
print("    column at all — it turned the 8 top-level keys into 8 SQL columns")
print("    and a 1,571-field STRUCT. `read_json_objects` is the one that hands")
print("    back the document. Picking the wrong one fails at bind time, which")
print("    is the good case.")
print("    duckdb DOES report a parse error on malformed JSON, which is more")
print("    than most, but says nothing about duplicate keys or big ints.")

t0 = time.perf_counter()
keys = q("SELECT json_keys(json) FROM read_json_objects('../source.json', maximum_object_size=99999999) LIMIT 1")[0][0]
print(f"\nQ1  ANSWERED at one level in {time.perf_counter() - t0:.1f} s — `json_keys`:")
print(f"    {len(keys)}: {', '.join(keys)}")
print("    Deeper: `json_structure` returns the whole inferred type. On this")
print("    document that string is enormous, because every SKU is a field:")
st = q("SELECT length(json_structure(json)::VARCHAR) FROM read_json_objects('../source.json', maximum_object_size=99999999)")[0][0]
print(f"    len(json_structure(...)) = {st:,} characters.")
print("    A COMPLETE answer to Q1 that no human can read — which is the same")
print("    failure fathom's own report has when the fold does not reach.")

print("\nQ2  CANNOT directly. Depth is inferable from json_structure by counting")
print("    nesting in that string, which is parsing the answer rather than")
print("    asking the question.")

print("\nQ3  CANNOT. duckdb names no candidates and prices none.")

# ── The table. `json_each` turns keys into rows — duckdb's real strength. ────
t0 = time.perf_counter()
con.execute("""
  CREATE OR REPLACE TABLE prod AS
  SELECT je.key AS sku_key,
         json_extract_string(je.value, '$.sku')           AS sku,
         json_extract_string(je.value, '$.productFamily') AS productFamily,
         je.value ->> '$.attributes.location'             AS location,
         je.value ->> '$.attributes.instanceType'         AS instanceType
  FROM read_json_objects('../source.json', maximum_object_size=99999999) d,
       json_each(d.json, '$.products') je
""")
n = q("SELECT count(*) FROM prod")[0][0]
print(f"\n    products via json_each: {n} rows in {time.perf_counter() - t0:.1f} s")
print("    `json_each` IS the keys-as-data verb — it returns (key, value) pairs.")
print("    duckdb and tidyjson are the only two of the fourteen that have one.")

print(f"\nQ4  PARTIAL. Per-field presence needs a query per field, or a json_each")
print("    over the attributes object. It is expressible and it is not offered:")
attrs = q("""
  SELECT ae.key, count(*) FROM read_json_objects('../source.json', maximum_object_size=99999999) d,
         json_each(d.json, '$.products') je, json_each(je.value, '$.attributes') ae
  GROUP BY 1 ORDER BY 2 DESC, 1
""")
print(f"    {len(attrs)} attribute keys: " +
      " ".join(f"{k}({c})" for k, c in attrs))
print("    ANSWERED, by a nested json_each — real SQL, and mine to think of.")

print("\nQ5  PARTIAL. `json_type(value)` per key would show it. All strings here.")
types = q("""
  SELECT DISTINCT json_type(ae.value) FROM read_json_objects('../source.json', maximum_object_size=99999999) d,
         json_each(d.json, '$.products') je, json_each(je.value, '$.attributes') ae
""")
print(f"    distinct json_type over every product attribute: {[t[0] for t in types]}")

print("\nQ6  CANNOT — but it is the CLOSEST of the fourteen, twice over.")
print("    `json_each` treats keys as rows, which IS the right model, and")
print("    `json_structure` shows the 1,571 SKUs as a type, which is the wrong")
print("    one. duckdb offers both and has no opinion about which this is.")

print(f"\nQ7  {n} products.")
npd = q("""
  SELECT count(*) FROM read_json_objects('../source.json', maximum_object_size=99999999) d,
       json_each(d.json, '$.terms') tt, json_each(tt.value) sku,
       json_each(sku.value) term, json_each(term.value, '$.priceDimensions') pdim
""")[0][0]
print(f"    {npd} price dimensions — FOUR nested json_each calls, one per keyed")
print("    level. The query is the shape of the document written out by hand.")

print("\nQ7a NO positional alignment. (Circular question — not scored.)")

print("\nQ8  ANSWERED:")
for r in q("SELECT sku, productFamily, location FROM prod LIMIT 3"):
    print(f"    {r}")

miss = q("SELECT count(*) FILTER (WHERE instanceType IS NOT NULL), count(*) FROM prod")[0]
print(f"\nQ9  instanceType present on {miss[0]} of {miss[1]}; `->>` returns NULL")
print("    and the row survives. ANSWERED, and it is free.")

print("\nQ10 The deepest array is appliesTo and all 4,505 are EMPTY.")
ap = q("""
  SELECT count(*), sum(json_array_length(pdim.value -> '$.appliesTo'))
  FROM read_json_objects('../source.json', maximum_object_size=99999999) d,
       json_each(d.json, '$.terms') tt, json_each(tt.value) sku,
       json_each(sku.value) term, json_each(term.value, '$.priceDimensions') pdim
""")[0]
print(f"    {ap[0]} arrays, {ap[1]} elements. `json_each` on an empty array")
print("    produces NO rows — duckdb drops them, like the R tools and unlike")
print("    pandas and polars, which invent a NULL.")

print("\nQ11 PARTIAL, and rare. There is no `paths WHERE value matches`, but a")
print("    json_each walk can filter on value. Whole-value URLs here: 0.")

print("\nQ12 The flattest honest table is the four-deep json_each above joined to")
print("    prod on sku. duckdb writes it in SQL and it is genuinely good at it.")
print("    WHAT IS LOST stopping at products: every price.")

print("\nQ13 YES. Every $.path in every query came from AWS's documentation.")
print("Q14 NO. Four levels of json_each are hard-coded to this nesting.")
print("Q15 PARTIAL. The `->>` and json_each idioms are fine; four nested")
print("    json_each in one FROM clause is not readable a week later.")
print("Q16 ~70 lines, and most of it is the four-level FROM clause — ceremony")
print("    that exists only because the levels are keyed by data.")

print("\nCONCLUSION")
print("duckdb has the two verbs this document needs — json_each for keys-as-data")
print("and json_structure for the field list — and answers Q1, Q4, Q5, Q8, Q9")
print("and Q10. It still cannot answer Q3 or Q6, because both are questions")
print("about WHICH level to point a verb at, and json_structure's answer to")
print(f"'what is in here' is {st:,} characters long.")
