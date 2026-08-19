"""glom — one Hacker News comment thread

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
  measured      2026-08-09
  run           cd corpus/02-hn-thread/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             1   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            5   YES                 partly
  10 flatten the deepest array                   6   YES                 YES

WHY THIS FILE EXISTS. glom has no describer, which file 01 already established.
What this document adds is the extraction half: glom ships `Recursive`-style
specs, so a recursive thread is the case where it should shine. The exploration
row stays empty and the extraction row is the interesting one.
"""
import json
import sys
from importlib.metadata import version

from glom import glom, Iter, T

print(f"python {sys.version.split()[0]}, glom {version('glom')}")

doc = json.load(open("../source.json"))

# ── 1. what is in here ───────────────────────────────────────────────────────
print(f"\n1. top-level keys: {len(doc)} — {', '.join(sorted(doc))}")
print("   which is `dict.keys()`. glom is a fetching library; it has no")
print("   describer, so it cannot tell you that these same 13 keys repeat at")
print("   all 25 levels, which is the only interesting fact about this file.")

# ── 7 / 10. the recursive walk, which glom CAN express ───────────────────────
# The spec has to be written as an explicit recursion. glom has no built-in
# fixpoint, so this is a Python function that happens to call glom.
def descend(node):
    yield node
    for child in glom(node, "children", default=[]):
        yield from descend(child)

nodes = list(descend(doc))
print(f"\n7. nodes reached by following `children`: {len(nodes)}   (jq: 336)")

rows = glom(nodes, Iter().map(lambda n: glom(n, {
    "id": "id", "author": "author", "parent": "parent_id",
    "text": T.get("text"),
})).all())
print(f"\n10. flattened to a table: {len(rows)} rows x {len(rows[0])} cols")
for r in rows[:3]:
    print(f"     {r['id']}  {r['author']:<16} {str(r['text'])[:38]}")

print("""
2, 3, 4, 5, 6. cannot.

  The `descend` function above is the answer to question 3, and a PERSON wrote
  it. It encodes that a node contains nodes under `children`, that `children` is
  the only recursive field, and that every node is one record. Those are exactly
  the three things the document does not declare, and glom asked for all three
  before it would do anything.

  Once told, glom is good: the table above is one readable spec. The cost is the
  telling, and this project's whole claim is that the telling is the expensive
  half and the one nobody measures.
""")
