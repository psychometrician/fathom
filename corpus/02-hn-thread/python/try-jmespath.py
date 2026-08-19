"""jmespath — one Hacker News comment thread

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
  measured      2026-08-09
  run           cd corpus/02-hn-thread/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             1   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            -   -                   CANNOT
  10 flatten the deepest array                   -   -                   CANNOT

WHY THIS FILE EXISTS, AND IT IS THE STRONGEST "CANNOT" IN THE GRID. On file 01
jmespath could not answer question 2 because it has no recursive descent. **On a
recursive document that same absence takes out questions 7 and 10 as well**, and
those are extraction questions that every other tool here answers. This is the
one file where a missing operator makes a tool unable to read the document at all.
"""
import json
import sys
from importlib.metadata import version

import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")

doc = json.load(open("../source.json"))
ask = lambda e: jmespath.search(e, doc)

# ── 1. what is in here ───────────────────────────────────────────────────────
print(f"\n1. keys(@): {len(ask('keys(@)'))} — {', '.join(sorted(ask('keys(@)')))}")

# ── 7 / 10. the thing it cannot do ───────────────────────────────────────────
# jmespath has no `..`. Reaching depth N takes an expression naming N levels.
print("\n7, 10. one hand-written level at a time, because there is no `..`:")
expr, total = "children", 0
for level in range(1, 7):
    got = ask(f"length({expr})") or 0
    total += got
    print(f"     level {level}: {expr[:38]:<40} {got:>4} nodes")
    expr = expr + "[].children[]"
print(f"     ... and the thread is 13 levels deep, so this list would need")
print(f"         thirteen expressions. Six of them reach {total} of 336 nodes.")

print("""
2, 3, 4, 5, 6, 7, 10. cannot.

  This is the file that makes the file-01 refusal concrete. There, the missing
  recursive descent meant question 2 was unanswerable and the rest were merely
  laborious. Here it means the document cannot be READ.

  Every expression above needs to know how deep the thread goes, and how deep
  the thread goes is question 2, which needs recursive descent. A tool whose
  answers all require an answer it cannot produce has one honest cell, and this
  is what it looks like written out.

  jmespath was designed for AWS API responses, whose shape is published in
  advance and is never recursive. That is a reasonable design. This corpus is
  the other case, and the point of the grid is to say which case you are in.
""")
