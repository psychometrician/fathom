"""jq (Python binding) — npm registry metadata for `express`

Scoring header follows ../r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.json   804,956 bytes, 288 versions, 25,044 paths
  measured      2026-08-09
  run           cd corpus/01-npm-registry/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  WRONG
   2 how deep                                    1   no                  yes
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 3   YES                 partly
   5 does any field change type                  2   YES                 partly
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 yes
  13 needed the shape in advance?                    see notes below

WHAT THIS FILE IS FOR, AND THE RULE IT IS UNDER. `CLAUDE.md` lists `jq` under
Python as well as `jqr` under R because the two are doorways to one query
language, and listing it under R alone misreports what a Python person can reach
for. **The expressions here are character-for-character the ones in
../r/try-jqr.R**, deliberately: if the same language through a different binding
gives a different answer, that is a finding about the binding, and if it gives the
same answer that is a control on the R measurement rather than new evidence.
"""
import json
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq {version('jq')}")

doc = json.load(open("../source.json"))


def ask(expr):
    return jq.compile(expr).input_value(doc).first()


# ── 1. what is in here ───────────────────────────────────────────────────────
# The identical expression from ../r/try-jqr.R line 35.
names = ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
print(f"\n1. distinct field names: {names}")
print(f"   the true answer is about 40. jqr, same expression, said 3100.")

# ── 2. how deep ──────────────────────────────────────────────────────────────
print(f"\n2. depth: {ask('[paths|length]|max')}")

# ── 7. how many records ──────────────────────────────────────────────────────
# Answerable only because a human has already said a version is a record.
print(f"\n7. versions: {ask('.versions|length')}   "
      f"(only because `versions` was named by a person)")

# ── 4, 5 — answerable, but only once question 3 is answered for it ───────────
always = ask('[.versions[]|keys]|map(select(.!=null))'
             '|reduce .[] as $k (null; if .==null then $k else .-(.-$k) end)|length')
union = ask('[.versions[]|keys[]]|unique|length')
print(f"\n4. across the 288 versions: {always} keys in every one, "
      f"{union} in the union")
poly = ask('[.versions[]|.dist|type]|unique|length')
print(f"5. `dist` takes {poly} distinct type(s) across versions")

# ── 3, 6 — cannot ────────────────────────────────────────────────────────────
print("""
3, 6. cannot.

  Question 3 (what is one record) is the question jq is least able to answer,
  because jq has no notion of a record at all — it has paths. Every answer above
  that mentions `versions` is one a PERSON supplied.

  Question 6 (are any keys actually data) is the reason question 1 returns 3,100
  instead of about 40. jq walked into `versions` and treated "4.17.1" as a field
  name, 288 times over, and there is no jq expression that decides otherwise
  without being told which keys are data first — which is the answer.
""")
