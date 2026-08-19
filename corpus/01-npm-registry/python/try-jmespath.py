"""jmespath — npm registry metadata for `express`

Scoring header follows ../r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   804,956 bytes, 288 versions, 25,044 paths
  measured      2026-08-09
  run           cd corpus/01-npm-registry/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             1   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 2   YES                 partly
   5 does any field change type                  1   YES                 partly
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 yes
  13 needed the shape in advance?                    YES, for everything

WHAT THIS FILE IS FOR, AND THE ONE THING THAT SEPARATES IT FROM jq. jmespath has
`keys(@)` and so can enumerate one level, but it has **no recursive descent** —
no `..`, no `paths`. jq's wrong answer of 3,100 is at least an answer; jmespath
cannot produce a wrong answer to question 1 because it cannot walk the document
at all without being told the depth in advance. That distinction is the finding.
"""
import json
import sys
from importlib.metadata import version

import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")

doc = json.load(open("../source.json"))
ask = lambda e: jmespath.search(e, doc)

# ── 1. what is in here ───────────────────────────────────────────────────────
print(f"\n1. keys(@) at the top: {len(ask('keys(@)'))}")
print("   and no further. jmespath has no recursive descent operator, so there")
print("   is no expression that enumerates the paths below this without a human")
print("   writing one level of `keys()` per level of nesting — which requires")
print("   already knowing how deep it goes, which is question 2.")

# ── 7, 4, 5 — answerable, all of them downstream of a human answering Q3 ─────
print(f"\n7. versions: {ask('length(versions)')}")

# Question 4 needs a union and an intersection across 288 objects. jmespath has
# no set operations and no fold, so this is Python doing the work.
allkeys = set()
for v in doc["versions"].values():
    allkeys |= set(v)
print(f"\n4. jmespath can fetch `versions.*` but has no set operations, so the")
print(f"   union of {len(allkeys)} keys was computed in Python, not in jmespath.")

print(f"\n5. `keys(versions.*[0])` style probing is possible one field at a time;")
print(f"   there is no expression for 'which fields vary in type'.")

print("""
2, 3, 6. cannot.

  Question 2 (how deep) is the sharpest refusal in the whole grid. jmespath has
  no recursive descent, so measuring depth requires writing an expression per
  level, which requires knowing the depth. **The tool cannot answer the question
  whose answer it needs in order to be used.**

  Question 3 and question 6 are the same two nobody answers. jmespath was
  designed for AWS API responses, whose shape is published in advance, and it is
  a good fit for that. This corpus is the other case.
""")
