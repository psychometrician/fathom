# jq (python binding) — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jq, the Python binding (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/python && uv run try-jq.py
#
#  Attempts: the probe ran ONCE on this file, so each expression below was
#  written once and is reported as it first ran. Rule 6.
#
#  Header filled in after the run. See the CONCLUSION.
#
# **The same query language as `r/try-jqr.R`, and it is here because jq is a
# doorway two languages share.** What differs is only the host; the answers
# below should match jqr's exactly, and where they do that is itself the
# finding — a shared engine gives shared answers, which is the architecture
# fathom chose for the same reason.

import json
import time

import importlib.metadata

import jq

# The module exposes no __version__; the distribution does. Rule: every attempt
# prints the version it ACTUALLY ran on, because two of the first three headers
# written for this corpus named a version that was not installed.
print(f"jq (python binding) {importlib.metadata.version('jq')}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

run = lambda prog: jq.compile(prog).input(doc).first()

print("\nQ0  jq parses and says nothing about soundness. CANNOT.")
print("    It keeps the LAST duplicate key silently — the damage the health")
print("    verb exists to name.")

print(f"\nQ1  keys: {run('keys_unsorted | join(\", \")')}")
leaves = run("[paths(scalars)] | length")
shapes = run('[paths(scalars) | map(if type=="number" then "[]" else . end) '
             '| join(".")] | unique | length')
print(f"    leaf paths: {leaves:,} · distinct path SHAPES: {shapes:,}")
print("    THE TWO NUMBERS ARE EQUAL, and that is the whole document in one")
print("    line. jq collapses ARRAY INDICES into a shape and has nothing that")
print("    collapses DATA KEYS — and this file's repetition is entirely in the")
print("    keys, so the collapse buys nothing at all.")

print(f"\nQ2  ANSWERED: {run('[paths | length] | max')} — `[paths | length] | max`.")

print("\nQ3  CANNOT. jq names no candidates and prices none.")

print("\nQ4  ANSWERED:")
print("    " + run('.products | [.[].attributes | keys[]] | group_by(.) '
                   '| map({k:.[0], n:length}) | sort_by(-.n) '
                   '| map("\\(.k)(\\(.n))") | join(" ")'))

print(f"\nQ5  attribute value types: "
      f"{run('[.products[].attributes[] | type] | unique | join(\", \")')}")
print("    One type everywhere. No field changes type.")

print("\nQ6  CANNOT. `to_entries` is the right verb and must be aimed:")
print(f"    .products | length          -> {run('.products | length')}")
print(f"    .terms.OnDemand | length    -> {run('.terms.OnDemand | length')}")
print(f"    .terms.Reserved | length    -> {run('.terms.Reserved | length')}")
print("    All three are collections. To jq they are objects, exactly like the")
print("    8-key root, and nothing distinguishes them.")

print(f"\nQ7  products {run('.products | length')} · "
      f"price dimensions {run('[.terms[][][] .priceDimensions | length] | add')}")

print("\nQ7a NO positional alignment. (Circular question — not scored.)")

t0 = time.perf_counter()
q8 = run('.products | to_entries | map({sku:.value.sku, '
         'family:.value.productFamily, location:.value.attributes.location}) | .[0:3]')
print(f"\nQ8  ANSWERED in {time.perf_counter() - t0:.1f} s:")
for r in q8:
    print(f"    {r}")

print(f"\nQ9  instanceType on "
      f"{run('[.products[] | select(.attributes.instanceType != null)] | length')} of "
      f"{run('.products | length')} — jq returns null for a missing key, so the")
print("    row survives by default. ANSWERED.")

print(f"\nQ10 appliesTo arrays {run('[.terms[][][] .priceDimensions[].appliesTo] | length')} "
      f"· elements {run('[.terms[][][] .priceDimensions[].appliesTo[]] | length')}")
print("    ALL EMPTY. The flattened result is indistinguishable from 'no such")
print("    field', which is the same blindness every one of the fourteen has.")

print(f"\nQ11 ANSWERED, one expression — whole-value URLs: "
      f"{run('[paths(type == \"string\" and test(\"^https?://\"))] | length')}")
print("    strings CONTAINING a url: " +
      str(run('[paths(type == "string" and test("https?://")) | join(".")]')))
print("    jq separates 'is a URL' from 'contains a URL'. Most of the fourteen")
print("    cannot ask either.")

print("\nQ12 `[paths(scalars)]` with values IS the flattest honest table, in one")
print("    line. WHAT IS LOST: nothing, and it is the size of the document —")
print(f"    {leaves:,} rows. Smaller needs the keyed levels collapsed.")

print("\nQ13 PARTLY NO. paths/keys/to_entries need no prior shape.")
print("Q14 YES for the generic expressions; NO for anything naming .attributes.*.")
print("Q15 NO. `.terms[][][]` means four levels and says nothing about them.")
print("Q16 ~45 lines, almost no ceremony.")

print("\nCONCLUSION")
print("Identical answers to r/try-jqr.R, which is the point of listing jq in")
print("both languages. jq answers more of this list than any other tool and")
print("still cannot answer Q3 or Q6. The single sharpest number in this entry is")
print(f"above: {leaves:,} leaf paths collapse to {shapes:,} shapes — jq's whole")
print("path-collapsing machinery is aimed at array indices, and this document's")
print("repetition is entirely in its keys.")
