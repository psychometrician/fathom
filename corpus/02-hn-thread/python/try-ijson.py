"""ijson — one Hacker News comment thread

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
  measured      2026-08-09
  run           cd corpus/02-hn-thread/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   no                  YES
   2 how deep                                    2   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  3   no                  YES
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   no                  YES

WHY THIS FILE EXISTS. On `01-npm-registry` ijson answered depth **9** for a
document of depth **6**, because its prefix is a dotted string and npm's keys are
version numbers. **This thread's keys contain no dots.** So this file isolates
that defect: if ijson is right here and wrong there, the bug is in the interface
rather than in the walker, which is the distinction worth having.
"""
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

names, types = Counter(), defaultdict(Counter)
deepest, objects = 0, 0
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if event == "start_map":
            objects += 1
        if prefix:
            deepest = max(deepest, prefix.count(".") + 1)
        if event == "map_key":
            names[value] += 1
        elif prefix and event in ("string", "number", "boolean", "null"):
            # Only real value events. `map_key` is not a value type, and neither
            # are `start_array`/`end_map` — counting those reported 7 varying
            # fields on the first run, three of which were `children` being an
            # array (start_array, end_array). The counter measuring itself, twice
            # in two files; ijson's event stream is structure and content mixed.
            types[prefix.split(".")[-1]][event] += 1

print(f"\n2. deepest prefix: {deepest}   (jq: 25)")
print("   RIGHT here, and ijson answered 9 for a depth-6 document on file 01.")
print("   The difference is entirely the keys: a thread's keys have no dots in")
print("   them, and npm's keys are version numbers. Same walker, same interface,")
print("   and the interface is only wrong when the data contains its delimiter.")

print(f"\n1. distinct key names: {len(names)}   (jq via paths(scalars): 11)")
print(f"   {', '.join(sorted(names))}")
print("   ijson counts `map_key` events, so it sees EVERY key including the two")
print("   that never hold a scalar. On this document that is the better answer:")
print("   jq's 11 omits `children`, which is what makes this a thread.")

print(f"\n7. objects: {objects}   (jq: 336)")

poly = {k: c for k, c in types.items() if len(c) > 1}
print(f"\n5. fields taking more than one event type: {len(poly)}")
for k, c in sorted(poly.items()):
    print(f"     {k:<14} {', '.join(sorted(c))}")

print("""
3, 4, 6. cannot.

  Question 4 is the same refusal as on file 01 and it is worse here. Answering
  needs a per-record key set reset at the record boundary, and this document's
  record boundary is RECURSIVE — `children.item`, `children.item.children.item`,
  and so on to 13 levels. There is no fixed prefix to watch for.

  A streaming parser can describe a document whose records are at a known depth.
  This one's records are at every depth, which is question 3 again.
""")
