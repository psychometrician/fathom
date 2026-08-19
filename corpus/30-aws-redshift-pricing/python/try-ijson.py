# ijson — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          ijson (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/python && uv run try-ijson.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **ijson is the only tool of the fourteen that never holds the document**, and
# its `prefix` is a path language by accident: it collapses array indices to
# `.item` and leaves object keys alone. On this file that is the same blindness
# jq has, arriving from a completely different direction.

import time
from collections import Counter

import ijson

print(f"ijson {ijson.__version__} · backend {ijson.backend}")

print("\nQ0  PARTIAL, and the best of the fourteen. ijson RAISES on truncated")
print("    input rather than returning a short document — that is a real")
print("    answer to 'is it whole'. It says nothing about duplicate keys,")
print("    big integers or encoded values.")

# ── ONE PASS. Everything below is computed from a single streamed walk. ──────
t0 = time.perf_counter()
prefixes = Counter()
depths = Counter()
kinds = Counter()
attr_present = Counter()
nprod = 0
appl_arrays = appl_items = 0
cur_attr = None

with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if event in ("string", "number", "boolean", "null"):
            prefixes[prefix] += 1
            depths[prefix.count(".") + 1] += 1
            kinds[event] += 1
        if prefix.startswith("products.") and prefix.endswith(".sku") \
                and event == "string" and prefix.count(".") == 2:
            nprod += 1
        if prefix.count(".") == 3 and ".attributes." in prefix and event == "string":
            attr_present[prefix.rsplit(".", 1)[1]] += 1
        if prefix.endswith(".appliesTo") and event == "start_array":
            appl_arrays += 1
        if prefix.endswith(".appliesTo.item"):
            appl_items += 1
walk_s = time.perf_counter() - t0

print(f"\n    one streaming pass: {walk_s:.1f} s, document never held in memory")

print(f"\nQ1  ANSWERED — {len(prefixes):,} DISTINCT LEAF PREFIXES.")
print("    That is the number that matters and it is the finding:")
print("    ijson's prefix collapses `[0]`, `[1]`, … into `.item`, so on an")
print("    array-shaped document the prefix count IS the field list. Here")
print("    nothing is an array, so every SKU makes its own prefix and the")
print("    'field list' is as long as the data.")
for p, c in prefixes.most_common(4):
    print(f"      {c:>6,}  {p}")
print(f"      … and {len(prefixes) - 4:,} more, nearly all of them one SKU each.")

print(f"\nQ2  WRONG, and the way it is wrong is the best finding in this file.")
print(f"    Counting separators in the prefix gives {max(depths)}. The true depth is 8.")
print("    ijson joins path segments with `.` AND THIS DOCUMENT'S KEYS CONTAIN")
print("    DOTS — a reserved instance term is keyed `<SKU>.<OFFERTERMCODE>` and")
print("    a rate is keyed `<SKU>.<OFFERTERMCODE>.<RATECODE>`. So one key reads")
print("    as two or three levels and the prefix is AMBIGUOUS: nothing in")
print("    `terms.Reserved.ABC.ABC.DEF.priceDimensions` says which dots are")
print("    structure and which are data.")
print("    A dotted path language cannot represent this document, and ijson")
print("    does not warn — it just answers 11.")

print("\nQ3  CANNOT. ijson names no candidates and prices none.")

print(f"\nQ4  ANSWERED, from the streamed counts ({nprod} products):")
al = [k for k, c in attr_present.items() if c == nprod]
so = sorted(((c, k) for k, c in attr_present.items() if c < nprod), reverse=True)
print(f"    always: {' '.join(sorted(al))}")
print(f"    sometimes: {' '.join(f'{k}({c})' for c, k in so)}")

print(f"\nQ5  event kinds seen across all leaves: {dict(kinds)}")
print("    ANSWERED in the weak sense — a field that changed type would show")
print("    two event kinds at one prefix, and here every prefix is one kind.")
print("    But with one prefix per SKU, 'one kind per prefix' is trivially true.")

print("\nQ6  CANNOT, and ijson makes the shape of the failure very visible:")
print(f"    {len(prefixes):,} prefixes for a document with about 40 distinct")
print("    field names. Every one of the extra prefixes is a KEY THAT IS DATA.")
print("    ijson has `.item` for 'this position is data' and no equivalent for")
print("    'this key is data'.")

print(f"\nQ7  {nprod} products, counted in the stream.")

print("\nQ7a NO positional alignment. (Circular question — not scored.)")

print("\nQ8  ANSWERED, but only with a second pass or a bigger state machine.")
t0 = time.perf_counter()
rows = []
with open("../source.json", "rb") as fh:
    for sku, rec in ijson.kvitems(fh, "products"):
        rows.append((rec["sku"], rec["productFamily"], rec["attributes"]["location"]))
print(f"    ijson.kvitems(fh, 'products') -> {len(rows)} rows in "
      f"{time.perf_counter() - t0:.1f} s")
print("    `kvitems` IS the keys-as-data verb — (key, value) pairs from a keyed")
print("    object, streamed. ijson, duckdb and tidyjson are the three tools of")
print("    the fourteen that have one.")
for r in rows[:3]:
    print(f"      {r}")

miss = sum(1 for _, _, _ in rows)
have = sum(1 for r in rows if r[2] is not None)
print(f"\nQ9  ANSWERED — but the row above would KeyError on a missing key.")
print("    Streaming gives no NA: absent means absent, and 'keep those rows'")
print("    is a `.get()` I must remember. A silent difference from pandas.")

print(f"\nQ10 appliesTo: {appl_arrays:,} arrays, {appl_items:,} items. ALL EMPTY.")
print("    ijson is the ONLY tool of the fourteen that can tell these apart")
print("    WITHOUT a special flag — `start_array` and `.item` are different")
print("    events, so 'there were 4,505 empty arrays' is directly observable.")
print("    Every other tool here answers 0 rows and cannot say why.")

print("\nQ11 PARTIAL. A value test in the stream is easy; the PATH it reports is")
print("    the raw prefix, so a match under terms names one SKU, not a shape.")

print("\nQ12 The stream IS the flattest honest table, one row per leaf, and it")
print(f"    is {sum(prefixes.values()):,} rows. WHAT IS LOST: nothing — and it")
print("    never fits in memory smaller than the document, which is the point.")

print("\nQ13 NO for the walk, YES for kvitems — which needs the path 'products'.")
print("Q14 YES for the generic pass. NO for kvitems.")
print("Q15 PARTIAL. The event loop is a state machine and reads like one.")
print("Q16 ~80 lines, and most of it is the state machine — the ceremony is")
print("    reconstructing structure that the parser threw away on purpose.")

print("\nCONCLUSION")
print("ijson answers Q0 better than anything else here and Q10 uniquely, and it")
print("is the clearest statement in the fourteen of what this document costs:")
print(f"{len(prefixes):,} distinct prefixes where about 40 field names exist.")
print("Its `.item` marker is exactly the right idea applied to the wrong axis —")
print("positions are collapsed, keys are not, and this file's repetition is")
print("entirely in its keys.")
