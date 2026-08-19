# jmespath — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jmespath (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/python && uv run try-jmespath.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **jmespath is AWS's own query language and this is an AWS document**, which
# makes it the fairest possible test in the fourteen: the tool and the file
# come from the same organisation. It still cannot describe the document, and
# it meets the same dotted-key wall glom does — with an escape hatch that
# glom's path language lacks.

import json
import time

import jmespath
import importlib.metadata

print(f"jmespath {importlib.metadata.version('jmespath')}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

s = lambda expr: jmespath.search(expr, doc)

print("\nQ0  jmespath does not parse. CANNOT — it never sees the bytes.")

print(f"\nQ1  PARTIAL — `keys(@)` is a real verb and answers one level:")
print(f"    {len(s('keys(@)'))}: {', '.join(s('keys(@)'))}")
print("    There is no recursive descent in JMESPath at all, so 'at every")
print("    level' is CANNOT — and the absence is deliberate in the spec.")

print("\nQ2  CANNOT. No depth verb, no recursion.")
print("\nQ3  CANNOT. jmespath names no candidates and prices none.")

print("\nQ4  PARTIAL and expensive. `keys()` per record, unioned by hand:")
t0 = time.perf_counter()
keysets = s("values(products)[].keys(attributes)")
from collections import Counter
c = Counter(k for ks in [s("values(products)[*].attributes")][0] for k in ks)
n = len(doc["products"])
print(f"    {len(c)} attribute keys over {n} products in "
      f"{time.perf_counter() - t0:.1f} s")
print(f"    always: {' '.join(sorted(k for k, v in c.items() if v == n))}")
print(f"    sometimes: "
      f"{' '.join(f'{k}({v})' for v, k in sorted(((v, k) for k, v in c.items() if v < n), reverse=True))}")
print("    `values()` and `keys()` did real work; the census is Python's.")

print("\nQ5  CANNOT. `type()` exists per value but there is no way to group it")
print("    across records without leaving the language.")

print(f"\nQ6  CANNOT — and `values()` is the verb that WOULD answer it:")
print(f"    length(products)       -> {s('length(products)')}")
print(f"    length(terms.OnDemand) -> {s('length(terms.OnDemand)')}")
print(f"    length(terms.Reserved) -> {s('length(terms.Reserved)')}")
print("    `values(products)` turns a keyed collection into a list, which is")
print("    exactly right — and jmespath never suggests it, because to the")
print("    language `products` and the 8-key root are the same kind of thing.")

print(f"\nQ7  {s('length(products)')} products.")

print("\nQ7a NO positional alignment. (Circular question — not scored.)")

t0 = time.perf_counter()
q8 = s("values(products)[*].{sku: sku, family: productFamily, "
       "location: attributes.location}")
print(f"\nQ8  ANSWERED in {time.perf_counter() - t0:.1f} s — {len(q8)} rows, and the")
print("    multiselect-hash syntax is the nicest of the fourteen for this:")
for r in q8[:3]:
    print(f"      {r}")

q9 = s("values(products)[*].attributes.instanceType")
print(f"\nQ9  PARTIAL AND DANGEROUS. `[*].attributes.instanceType` returns")
print(f"    {len(q9)} values from {n} products — jmespath DROPS the missing ones")
print("    silently rather than yielding null, so the result no longer lines up")
print("    with the records. Keeping the rows needs the multiselect form:")
q9b = s("values(products)[*].{i: attributes.instanceType}")
print(f"    `[*].{{i: attributes.instanceType}}` -> {len(q9b)} rows, "
      f"{sum(1 for r in q9b if r['i'] is not None)} non-null. THAT is the answer,")
print("    and the difference between the two is invisible until you count.")

print("\nQ10 The deepest array is appliesTo and all 4,505 are EMPTY.")
ap = s("values(terms)[].values(@)[].values(@)[].values(priceDimensions)[].appliesTo")
print(f"    {len(ap)} arrays, {sum(len(a) for a in ap)} elements — flattening")
print("    gives nothing, indistinguishable from an absent field.")

print("\nQ11 CANNOT. No path search by value and no way to report a path at all —")
print("    JMESPath returns values, never locations.")

# ── THE DOTTED KEY, AND JMESPATH HAS AN ANSWER. ──────────────────────────────
print("\n    ** THE DOTTED KEY: jmespath survives where glom does not. **")
tsku = next(iter(doc["terms"]["Reserved"]))
tkey = next(iter(doc["terms"]["Reserved"][tsku]))
print(f"    the term key is {tkey!r} — it contains dots.")
bare = s(f"terms.Reserved.{tsku}.{tkey}.offerTermCode")
print(f"    unquoted  terms.Reserved.{tsku[:8]}….{tkey[:12]}… -> {bare!r}")
quoted = s(f'terms.Reserved."{tsku}"."{tkey}".offerTermCode')
print(f"    QUOTED    …\"{tkey[:12]}…\" -> {quoted!r}")
print("    JMESPath has quoted identifiers, so a dotted key is addressable.")
print("    glom has no such escape and raises. Same document, same reserved")
print("    character, opposite outcomes — and the unquoted form returns None")
print("    rather than an error, which is the worse of the two failures.")

print("\nQ12 CANNOT as exploration. The flat table is expressible once known.")

print("\nQ13 YES. Every expression above names keys I learned from AWS's docs.")
print("Q14 NO — and this is jmespath's specific weakness: a wrong path returns")
print("    None, never an error, so the next file fails silently.")
print("Q15 YES. The multiselect syntax is the most readable of the fourteen.")
print("Q16 ~50 lines. Low ceremony, and `values()` is doing real work.")

print("\nCONCLUSION")
print("jmespath is AWS's language reading AWS's document and answers Q1")
print("partially, Q4, Q8 and Q9 — and cannot answer Q2, Q3, Q6 or Q11 at all,")
print("because it has no recursion and returns values rather than locations.")
print("Its two failures here are both SILENT: a missing key collapses the list")
print("without warning, and an unquoted dotted key returns None as though the")
print("data were absent.")
