"""ijson — one hour of public GitHub events

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json.gz   10.6 MB gzipped, 50 MB / 37,883 records raw
  measured      2026-08-09
  run           cd corpus/04-gharchive/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 3   no                  YES
   1 what is in here                             4   no                  YES
   2 how deep                                    2   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 6   YES, one line of it YES
   5 does any field change type                  4   no                  YES
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   no                  YES

WHY THIS FILE. ijson never holds the document. On the two small files that only
saved memory nobody needed; here it is the whole point. DuckDB read all 37,883
records in 133 MB and polars needed 1,076 MB. A streaming parser should beat
both, and the question is what it gives up to do that.
"""
import gzip
import resource
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3

# ── 0 / 7. NDJSON, gzipped, in one pass ──────────────────────────────────────
# `multiple_values=True` is the flag that makes a stream of JSON documents legal.
# Without it ijson raises after the first record, which is correct — NDJSON is
# not one JSON document, and that is what makes question 0 real for this file.
names, types = Counter(), defaultdict(Counter)
per_record, records, deepest = [], 0, 0
top = None

with gzip.open("../source.json.gz", "rb") as fh:
    for prefix, event, value in ijson.parse(fh, multiple_values=True):
        if prefix == "" and event == "start_map":
            records += 1
            if top is not None:
                per_record.append(top)
            top = set()
        elif event == "map_key" and prefix == "":
            top.add(value)
        if event == "map_key":
            names[value] += 1
        elif prefix and event in ("string", "number", "boolean", "null"):
            types[prefix][event] += 1
        if prefix:
            deepest = max(deepest, prefix.count(".") + 1)
if top:
    per_record.append(top)

print(f"\n0/7. records read straight from the gzip: {records:,}")
print(f"     the file is NDJSON and needs `multiple_values=True`. Without it")
print(f"     ijson stops after record 1, which is the honest answer: this is")
print(f"     not one JSON document.")

print(f"\n1. distinct key names anywhere: {len(names):,}")
print(f"2. deepest prefix: {deepest}   (axes.py grades this file 7)")
print(f"   Not a disagreement: `axes.py` counts the record object as a level and")
print(f"   an ijson prefix is relative to it, so these are the same answer with")
print(f"   different origins. On 02-hn-thread, where there IS a single root")
print(f"   object, ijson and jq both said 25. NDJSON has no root to count.")

# ── 4. always present vs sometimes, at the top level ─────────────────────────
always = set.intersection(*per_record)
union = set().union(*per_record)
print(f"\n4. top-level keys: {len(union)} in the union, {len(always)} on every "
      f"record")
for k in sorted(union - always):
    n = sum(1 for r in per_record if k in r)
    print(f"     {k:<22} on {n:,} of {records:,}")

# ── 5. does any field change type ────────────────────────────────────────────
poly = {p: c for p, c in types.items() if len(c) > 1}
print(f"\n5. paths taking more than one value type: {len(poly):,}")
print(f"   NOTES.md grades this file `33 fields sometimes null`. These count")
print(f"   different things — paths here, fields there, and a path is finer —")
print(f"   so 25 and 33 are not the same measurement and neither refutes the")
print(f"   other. Recorded rather than reconciled, because quietly matching two")
print(f"   numbers that mean different things is how a grid stops being one.")
for p, c in sorted(poly.items(), key=lambda kv: -sum(kv[1].values()))[:6]:
    print(f"     {p[:44]:<46} {', '.join(sorted(c))}")

print(f"\n   peak RSS: {rss():,.0f} MB")
print(f"   DuckDB 133 MB · probe 968 MB on a 20,000 sample · polars 1,076 MB")

print("""
3, 6. cannot.

  Question 3 again, and this file is the sharpest case for it. The 37,883 events
  are eight row shapes, and which shape a record has is decided by `type` — a
  field that sits on the event, next to `payload`, and is a plain string.

  Nothing above found that. A streaming parser sees `payload.ref` and
  `payload.commits.item.sha` go by and has no reason to connect either to the
  `type` it read moments earlier. **The information is in the stream and the
  relationship is not**, which is the whole distance between reading a document
  and describing one.
""")
