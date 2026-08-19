# jq (the Python binding) — one hour of public GitHub events, at 17x entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jq, the Python binding (see uv.lock)
#  file          ../source.json.gz   118 MB gzipped, 870 MB / 286,864 records raw
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/python && uv run try-jq.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# ⚠ THE CORRECTED LEAF EXPRESSION IS USED. `paths(scalars)` silently drops any
# leaf that IS `false` or `null`, and this file has 1,581,755 booleans and
# 426,888 nulls by ijson's exact count — so the broken idiom would lose over two
# million leaves here.
#
# **The binding takes a PARSED value**, one record at a time, so this attempt
# streams records past a compiled program rather than handing it the document.
import gzip, json, time, jq
from _budget import Attempt

SRC = "../source.json.gz"
print("jq python binding (version in uv.lock)")
print("\nQ0  jq parses and says nothing. Duplicate keys: last wins. CANNOT.")

LEAF = jq.compile('[path(.. | select(type != "object" and type != "array"))] | length')
BROKEN = jq.compile('[paths(scalars)] | length')
TYPES = jq.compile('[.. | select(type != "object" and type != "array") | type]')

with Attempt("stream all records past three programs") as a:
    n = leaves = broken = 0
    kinds = {}
    with gzip.open(SRC, "rt") as fh:
        for line in fh:
            d = json.loads(line)
            n += 1
            leaves += LEAF.input_value(d).first()
            broken += BROKEN.input_value(d).first()
            for t in TYPES.input_value(d).first():
                kinds[t] = kinds.get(t, 0) + 1
ok = a.finished

if ok:
    print(f"\nQ7  {n:,} records, {leaves:,} leaves — THE WHOLE FILE.")
    print(f"\n── the broken idiom, at scale ──────────────────────────────────────────")
    print(f"  paths(scalars)   {broken:>12,}")
    print(f"  corrected        {leaves:>12,}")
    print(f"  DROPPED SILENTLY {leaves-broken:>12,}  ({100*(leaves-broken)/leaves:.2f}%)")
    print("\nQ5  leaves by JSON type, exact, because `type` is a function:")
    for k, v in sorted(kinds.items(), key=lambda kv: -kv[1]):
        print(f"      {k:<10} {v:>12,}")
else:
    print(f"\n  did not finish: {a.why}")

print("\nQ1  `keys` per record, one level. Q2 expressible via `path` lengths.")
print("Q3  CANNOT. Q6 jq COUNTS keys and decides nothing. CANNOT.")
print("Q8/Q9 a multiselect hash per record — yes; absent and null are one value.")
print("Q10 EXACT: a jq path is an array of steps, an index is a NUMBER and a key")
print("    a STRING, so the two never blur. Q11/Q12 expressible via `..`.")
print(f"""
CONCLUSION. Written after the run and corrected against what printed.

IT COMPLETES, ONE RECORD AT A TIME, IN 224 SECONDS AT 24 MB. That is the only
way it can: the Python binding takes a parsed VALUE, so a 286,864-record NDJSON
file is 286,864 invocations rather than one. Memory stays flat — the second
lowest of the fourteen after ijson — and the time is the highest of anything
that finished. That is jq's cost model at this scale, and entry 04 at 50 MB was
too small to show it.

ITS COUNTS MATCH ijson EXACTLY, ALL FIVE OF THEM: 17,670,186 leaves, and
13,009,389 strings, 2,652,154 numbers, 1,581,755 booleans, 426,888 nulls. Two
independent parsers, two languages, one set of numbers.

THE BROKEN IDIOM DROPS 1,212,833 LEAVES HERE, 6.86%. And the arithmetic is
worth stating because it corrects the obvious reading: the file holds 1,581,755
booleans and 426,888 nulls, which is 2,008,643 — but `paths(scalars)` only
loses the ones that are FALSY. Every `true` survives its own filter. The
1,212,833 lost are the nulls plus roughly 786,000 falses.

AND jq REMAINS THE ONLY TOOL THAT ANSWERS QUESTION 5 EXACTLY, because `type` is
a first-class function rather than an inference from a dtype or a Python value.
Questions 3 and 6 are CANNOT, for the 30th entry running.
""")
