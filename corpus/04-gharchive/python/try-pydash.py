"""pydash — one hour of public GitHub events

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json.gz   10.6 MB gzipped, 50 MB / 37,883 records raw
  measured      2026-08-09
  run           cd corpus/04-gharchive/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 2   no                  cannot
   1 what is in here                             3   no                  YES
   2 how deep                                    2   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 4   no                  YES
   5 does any field change type                  4   no                  YES
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   no                  cannot

WHY THIS FILE. pydash has no reader at all, so questions 0 and 7 are answered by
`gzip` and `json` before pydash is imported. What it shows is the floor: what a
plain nine-line recursion gets you, and what it costs at 50 MB.
"""
import gzip
import json
import resource
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")

def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3

# ── 0 / 7 — the standard library, not pydash ─────────────────────────────────
with gzip.open("../source.json.gz", "rt") as fh:
    docs = [json.loads(line) for line in fh if line.strip()]
print(f"\n0/7. {len(docs):,} records — read by `gzip` and `json`. pydash has no")
print(f"     reader, so it contributes nothing to either question.")

# ── 1, 2, 4, 5 — one recursion ───────────────────────────────────────────────
names, types, deepest = Counter(), defaultdict(set), 0

def walk(node, depth):
    global deepest
    deepest = max(deepest, depth)
    if isinstance(node, dict):
        for k, v in node.items():
            names[k] += 1
            types[k].add(type(v).__name__)
            walk(v, depth + 1)
    elif isinstance(node, list):
        for v in node:
            walk(v, depth + 1)

for d in docs:
    walk(d, 0)

print(f"\n1. distinct key names: {len(names):,}   "
      f"(ijson 305, jq via paths(scalars) 254)")
print(f"2. deepest nesting: {deepest}   (jq: 6)")

per = [set(d) for d in docs]
always, union = set.intersection(*per), set().union(*per)
print(f"\n4. top-level: {len(union)} keys, {len(always)} on every record")
for k in sorted(union - always):
    print(f"     {k:<22} on {sum(1 for r in per if k in r):,}")

varying = {k: v for k, v in types.items() if len(v) > 1}
print(f"\n5. key names taking more than one Python type: {len(varying):,}")
for k, v in sorted(varying.items())[:6]:
    print(f"     {k:<22} {', '.join(sorted(v))}")

print(f"\n   peak RSS: {rss():,.0f} MB")
print(f"   ijson 71 · DuckDB 133 · jq 674 · probe 968 (sample) · polars 1,076")

print("""
3, 6. cannot.

  Question 5 above is worth reading carefully, because it is RIGHT and useless.
  It groups by key NAME rather than by path, so `description` varying between
  null and string is reported once no matter where in the tree it happened, and
  a name reused at two unrelated paths is reported as varying when neither does.
  ijson's per-path answer of 25 is the better one and costs the same walk.

  Question 3 is the file's whole difficulty and nothing here approaches it.
""")
