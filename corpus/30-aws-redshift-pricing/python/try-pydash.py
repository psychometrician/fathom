# pydash — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          pydash (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/python && uv run try-pydash.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **pydash is lodash for Python: a utility belt, not a JSON tool.** It is in
# the comparison because `pydash.get` with a dotted path is what a great many
# people actually reach for, and this document is the case where that habit
# fails in the most quietly wrong way available.

import json
import time
from collections import Counter

import pydash
import importlib.metadata

print(f"pydash {importlib.metadata.version('pydash')}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

print("\nQ0  pydash does not parse. CANNOT — it never sees the bytes.")

print(f"\nQ1  CANNOT beyond one level. `pydash.keys(doc)` -> {len(pydash.keys(doc))}:")
print(f"    {', '.join(pydash.keys(doc))}")
print("    That is a rename of list(). No recursive listing exists.")

print("\nQ2  CANNOT. No depth verb.")
print("\nQ3  CANNOT. pydash names no candidates and prices none.")

n = len(doc["products"])
t0 = time.perf_counter()
c = Counter(k for p in doc["products"].values() for k in p["attributes"])
print(f"\nQ4  PARTIAL — the counting is Python's, pydash contributes the spelling:")
print(f"    {len(c)} attribute keys over {n} products in "
      f"{time.perf_counter() - t0:.1f} s")
print(f"    always: {' '.join(sorted(k for k, v in c.items() if v == n))}")
print(f"    sometimes: "
      f"{' '.join(f'{k}({v})' for v, k in sorted(((v, k) for k, v in c.items() if v < n), reverse=True))}")

print("\nQ5  CANNOT. No type census.")

print(f"\nQ6  CANNOT. products has {n} keys, terms.OnDemand "
      f"{len(doc['terms']['OnDemand'])}, terms.Reserved {len(doc['terms']['Reserved'])} —")
print("    all data, and pydash has no verb that distinguishes a keyed")
print("    collection from a record.")

print(f"\nQ7  {n} products, via len().")

print("\nQ7a NO positional alignment. (Circular question — not scored.)")

t0 = time.perf_counter()
rows = [{"sku": pydash.get(p, "sku"),
         "family": pydash.get(p, "productFamily"),
         "location": pydash.get(p, "attributes.location")}
        for p in doc["products"].values()]
print(f"\nQ8  ANSWERED in {time.perf_counter() - t0:.1f} s — {len(rows)} rows.")
print("    `pydash.get(obj, 'a.b')` is the whole idea and it reads well:")
for r in rows[:3]:
    print(f"      {r}")

it = [pydash.get(p, "attributes.instanceType") for p in doc["products"].values()]
print(f"\nQ9  ANSWERED — {sum(v is not None for v in it)} of {len(it)}. `get`")
print("    returns None for a missing path and the row survives. This is")
print("    pydash's single best property and the reason people reach for it.")

print("\nQ10 The deepest array is appliesTo and all 4,505 are EMPTY.")
ap = [pdim["appliesTo"] for tt in doc["terms"].values() for sku in tt.values()
      for t in sku.values() for pdim in t["priceDimensions"].values()]
print(f"    {len(ap)} arrays; pydash.flatten -> {len(pydash.flatten(ap))} rows.")
print("    Indistinguishable from the field being absent.")

print("\nQ11 CANNOT. No path search by value.")

# ── THE FAILURE. ─────────────────────────────────────────────────────────────
print("\n    ** THE DOTTED KEY, AND THIS IS THE QUIETEST FAILURE OF THE FOURTEEN. **")
tsku = next(iter(doc["terms"]["Reserved"]))
tkey = next(iter(doc["terms"]["Reserved"][tsku]))
print(f"    the term key is {tkey!r} — it contains dots.")
bare = pydash.get(doc, f"terms.Reserved.{tsku}.{tkey}.offerTermCode")
print(f"    pydash.get(doc, 'terms.Reserved.<sku>.<sku>.<term>.offerTermCode')")
print(f"      -> {bare!r}")
esc = pydash.get(doc, ["terms", "Reserved", tsku, tkey, "offerTermCode"])
print(f"    pydash.get(doc, [..., {tkey[:14]!r}…, 'offerTermCode'])")
print(f"      -> {esc!r}")
print("    The dotted form returns None. NOT AN ERROR — None, which is exactly")
print("    what `get` returns for a legitimately missing field. So on this")
print("    document pydash cannot distinguish 'this path does not exist' from")
print("    'your path language ate my key', and the property that makes Q9 easy")
print("    is the property that makes this invisible.")
print("    The list form works. Nothing tells you to use it.")

print("\nQ12 CANNOT as exploration. Buildable once known, by hand.")

print("\nQ13 YES. Every `get` path is this document's shape written out.")
print("Q14 NO, and silently — a wrong path is None, like a missing field.")
print("Q15 YES. `get` with a dotted path is the most readable thing here.")
print("Q16 ~55 lines, and pydash contributes about six of them.")

print("\nCONCLUSION")
print("pydash answers Q8 and Q9 and nothing else, which is what a utility belt")
print("does. This document turns its central convenience into a hazard: `get`")
print("returns None both for an absent field and for a key its own path syntax")
print("cannot express, and 1,728 of this file's keys contain the separator.")
print("Of the three dot-path tools here, glom RAISES, jmespath can be QUOTED,")
print("and pydash silently returns None — the same defect with three different")
print("blast radii, and the quietest one is the one people use most.")
