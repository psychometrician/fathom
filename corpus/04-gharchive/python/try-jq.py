"""jq (Python binding) — one hour of public GitHub events

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.jsonl   50 MB, 37,883 records (gzip NOT read directly)
  measured      2026-08-09
  run           cd corpus/04-gharchive/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 4   no                  PARTLY
   1 what is in here                             3   no                  YES
   2 how deep                                    2   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 3   no                  YES
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   no                  YES

WHY THIS FILE. jq the COMMAND handles a stream of JSON documents natively — it
is what NDJSON was designed for. The Python binding takes a value or a string,
not a file, so the ceremony here is entirely about getting 50 MB into it, and
that is the finding rather than an aside.
"""
import gzip
import json
import resource
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq {version('jq')}")

def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3

# ── 0. the binding does not take a file, and NDJSON is not one document ──────
print("\n0. `jq.compile(...).input_value(doc)` wants a parsed value and")
print("   `.input_text(...)` wants a string. Neither takes a path, so the gzip")
print("   has to be opened, decompressed and split in Python before jq sees it.")
print("   The jq BINARY would do `jq '...' <file` over this stream unaided; the")
print("   binding gives up that property, which is a fact about the doorway")
print("   rather than about the language.")

with gzip.open("../source.json.gz", "rt") as fh:
    docs = [json.loads(line) for line in fh if line.strip()]
print(f"\n7. records, after Python did the reading: {len(docs):,}")

# jq over the whole array in one pass.
ask = lambda e: jq.compile(e).input_value(docs).first()

# ── 1. what is in here ───────────────────────────────────────────────────────
names = ask('[.[]|paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
print(f"\n1. distinct field names: {names}   "
      f"(ijson counts keys and says 305)")
print("   the same `paths(scalars)` expression as files 01 and 02, and the same")
print("   blind spot: a field that never holds a scalar is not counted.")

# ── 2. how deep ──────────────────────────────────────────────────────────────
print(f"\n2. depth: {ask('[.[]|paths|length]|max')}")

# ── 4. always present vs sometimes ───────────────────────────────────────────
counts = ask('[.[]|keys[]]|group_by(.)|map({(.[0]): length})|add')
print(f"\n4. top-level keys and how many of the {len(docs):,} records carry them:")
for k, v in sorted(counts.items(), key=lambda kv: -kv[1]):
    print(f"     {k:<22} {v:,}")

print(f"\n   peak RSS: {rss():,.0f} MB")
print(f"   ijson 71 · DuckDB 133 · probe 968 (20,000 sample) · polars 1,076")

print("""
3, 5, 6. cannot.

  Question 5 is expressible in jq and was left out on purpose: the expression
  that answers it for 37,883 records builds a group per path and did not finish
  in reasonable time on this file. "Expressible but not affordable" is a real
  cell and it is not the same as "cannot", so it is recorded as what it is.

  Question 3 is the one that decides this file. Eight row shapes, chosen by
  `type`, and jq will tell you every one of them if a person writes
  `group_by(.type)`. Nothing in the language proposes it.
""")
