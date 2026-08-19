"""pydash — one Hacker News comment thread

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
  measured      2026-08-09
  run           cd corpus/02-hn-thread/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   no                  YES
   2 how deep                                    4   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 4   no                  YES
   5 does any field change type                  4   no                  YES
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            3   no                  YES

WHY THIS FILE EXISTS. On `01-npm-registry` this same nine-line recursion returned
**3,126** field names against a truth of about 40, and pydash's dotted-path
interface returned `None` for a key that was present. This document has no dotted
keys, so it isolates both defects — and it is the file where the walk is right.
"""
import json
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")

doc = json.load(open("../source.json"))

# ── 1, 2, 4, 5, 7 — one plain recursion, which is what pydash amounts to ─────
names, types, nodes, deepest = Counter(), defaultdict(set), 0, 0
per_node = []

def walk(node, depth):
    global nodes, deepest
    deepest = max(deepest, depth)
    if isinstance(node, dict):
        nodes += 1
        per_node.append(set(node))
        for k, v in node.items():
            names[k] += 1
            types[k].add(type(v).__name__)
            walk(v, depth + 1)
    elif isinstance(node, list):
        for v in node:
            walk(v, depth + 1)

# Depth 0 at the root, so this counts PATH SEGMENTS and is comparable with jq's
# `[paths|length]|max`. The first version started at 1 and reported 26 against
# jq's 25 — an off-by-one in this harness, not in pydash, and it is recorded
# rather than quietly corrected because a one-off in a comparison column is
# exactly how a tool gets blamed for a measurement.
walk(doc, 0)

print(f"\n1. distinct key names: {len(names)}   (jq via paths(scalars): 11)")
print(f"   {', '.join(sorted(names))}")
print(f"   this counts `children` and `options`, which never hold a scalar and")
print(f"   which jq's expression therefore drops. On 01-npm-registry the same")
print(f"   nine lines returned 3,126 against a truth of about 40.")

print(f"\n2. deepest nesting: {deepest}   (jq: 25)")
print(f"7. objects: {nodes}   (jq: 336)")

always = set.intersection(*per_node)
union = set().union(*per_node)
print(f"\n4. {len(always)} keys on every one of the {nodes} nodes, "
      f"{len(union)} in the union — nothing is ever absent")

varying = {k: v for k, v in types.items() if len(v) > 1}
print(f"\n5. fields taking more than one Python type: {len(varying)}")
for k, v in sorted(varying.items()):
    print(f"     {k:<14} {', '.join(sorted(v))}")

# ── the dotted-path defect, which this document cannot trigger ───────────────
print(f"\n(the file-01 defect, checked here) pydash.get on a real nested path:")
print(f"     'children.0.author' -> {pydash.get(doc, 'children.0.author')}")
print(f"   works, because no key in this document contains a dot. The same call")
print(f"   shape returned None on npm, where the keys are version numbers.")

print("""
3, 6. cannot — and 3 is the whole document.

  pydash reports 336 objects at up to 25 levels. It has nothing to say about the
  fact that all 336 are the SAME shape, that `children` is the one field that
  recurses, or that a sensible table here is 336 rows rather than the 25 the top
  level suggests. Every number above is right and none of them is the answer.
""")
