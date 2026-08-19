"""jq (Python binding) — one Hacker News comment thread

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
  measured      2026-08-09
  run           cd corpus/02-hn-thread/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 -   -                   cannot
   1 what is in here                             1   no                  YES
   2 how deep                                    1   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 1   no                  YES
   5 does any field change type                  1   no                  YES
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   no                  YES
  13 needed the shape in advance?                    NO
  14 survives the next file unchanged?               yes — and that is the finding

WHY THIS FILE EXISTS. `VERDICT.md` says the describers "fail together", measured
on `01-npm-registry` where five implementations landed between 2,852 and 3,126
against a truth of about 40. **This is the control.** The expressions below are
character-for-character the ones in ../r/try-jqr.R, which are character-for-
character the ones in ../../01-npm-registry/python/try-jq.py. If the same code is
RIGHT here and WRONG there, the failure is a property of the document rather than
of the tool — which is the whole claim.
"""
import json
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq {version('jq')}")

doc = json.load(open("../source.json"))
ask = lambda e: jq.compile(e).input_value(doc).first()

# ── 2. how deep ──────────────────────────────────────────────────────────────
print(f"\n2. depth: {ask('[paths|length]|max')}   (jqr: 25)")

# ── 1. what is in here ───────────────────────────────────────────────────────
names = ask('[paths(scalars)|map(select(type=="string"))|last]|unique|length')
print(f"1. distinct field names: {names}   (jqr: 11, and 11 is CORRECT)")

# ── 7. how many records ──────────────────────────────────────────────────────
print(f"7. objects anywhere: {ask('[..|objects]|length')}   (jqr: 336)")

# ── 4. always present vs sometimes ───────────────────────────────────────────
# Every one of the 11 appears on all 336 nodes, so nothing is ever absent. That
# is a real and slightly surprising property of this document, not a shortcut.
counts = ask('[..|objects|keys[]]|group_by(.)|map({(.[0]): length})|add')
print(f"\n4. key -> how many of the 336 nodes carry it:")
for k, v in sorted(counts.items()):
    print(f"     {k:<14} {v}")

# ── 5. does any field change type ────────────────────────────────────────────
poly = ask('[..|objects|to_entries[]]|group_by(.key)'
           '|map({(.[0].key): ([.[].value|type]|unique)})|add')
varying = {k: v for k, v in poly.items() if len(v) > 1}
print(f"\n5. fields taking more than one type: {len(varying)}")
for k, v in sorted(varying.items()):
    print(f"     {k:<14} {', '.join(v)}")

# ── 1, again, and the answer recorded as CORRECT is missing two fields ───────
# Found 2026-08-09 while running this file, by noticing that question 4 lists 13
# keys and question 1 says 11.
allkeys = ask('[..|objects|keys[]]|unique')
scalar_bearing = ask('[paths(scalars)|map(select(type=="string"))|last]|unique')
missing = sorted(set(allkeys) - set(scalar_bearing))
print(f"\n1 (revisited). keys that exist: {len(allkeys)}. "
      f"keys `paths(scalars)` finds: {len(scalar_bearing)}.")
print(f"   silently omitted: {', '.join(missing)}")
print(f"   `children` is an array of {len(doc['children'])} at the top and the")
print(f"   reason this document has 13 levels and 336 nodes. `options` is an")
print(f"   empty array. Neither ever holds a scalar, so neither is on any path")
print(f"   `paths(scalars)` returns — and 11 has been recorded as the CORRECT")
print(f"   answer for this file by jqr, by rrapply, and by the grading.")

print("""
0, 3, 6. cannot — the same three as everywhere else.

  Question 3 is the one that matters. jq reports 336 objects, and a person still
  has to say that a comment IS the record and that the 13 levels of `children`
  are the same record repeated. `[..|objects]` would have said 336 whether this
  document were a thread, a flat list, or a tree of unrelated things.

  The finding is that the numbers above are RIGHT. Identical expressions on
  01-npm-registry return 3,100 for a document with about 40 fields. The code did
  not change. The document did.

  With one correction this run produced, recorded above: "right" was measured by
  an expression that cannot see a field which never holds a scalar. Three
  implementations agreed on 11 and all three dropped `children`. Agreement across
  tools is not a check on the QUESTION, only on the tools, and here the question
  was `paths(scalars)` and it was the wrong one.
""")
