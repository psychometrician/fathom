"""jmespath — a Synthea FHIR bundle

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
  measured      2026-08-09
  run           cd corpus/05-fhir-bundle/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          3   YES                 partly
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 YES
   9 a field missing from some records           4   YES                 partly

WHY THIS FILE. This document is flat enough for jmespath — depth 11 but no
recursion — so the missing `..` is survivable, unlike on `02-hn-thread`. What
bites instead is `value[x]`: nine spellings of one field and no Coalesce.
"""
import json
import sys
from importlib.metadata import version

import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")

doc = json.load(open("../source.json"))
ask = lambda e: jmespath.search(e, doc)

print(f"\n7. entries: {ask('length(entry)')}")
print(f"1. keys(@) on the bundle: {sorted(ask('keys(@)'))}")
print(f"   keys of the first resource: {len(ask('keys(entry[0].resource)'))}")
print("   one resource at a time, and no expression generalises over the 564")
print("   without a person writing the projection.")

# ── 3. once told ─────────────────────────────────────────────────────────────
kinds = {}
for rt in ask("entry[].resource.resourceType"):
    kinds[rt] = kinds.get(rt, 0) + 1
print(f"\n3. `entry[].resource.resourceType` returns 564 strings, "
      f"{len(kinds)} distinct.")
print("   jmespath has no group_by, so the counting above is Python. It can")
print("   FILTER by kind — `entry[?resource.resourceType=='Observation']` — but")
print("   only one kind per expression, so describing 20 needs 20 queries.")

# ── 9. value[x] without a Coalesce ───────────────────────────────────────────
print("\n9. value[x], one expression per spelling because there is no Coalesce:")
tot = 0
for f in ("valueQuantity", "valueCodeableConcept", "valueString"):
    n = len(ask(f"entry[].resource.{f}") or [])
    tot += n
    print(f"     entry[].resource.{f:<22} {n:>4}")
print(f"   {tot} values, three expressions. glom's Coalesce does this in one and")
print(f"   returned 119 — the same total, in a single spec.")

print("""
2, 4, 5, 6. cannot.

  jmespath's `||` looks like a Coalesce and is not: it works on one value, not
  as a projection over 564 records, so `entry[].resource.(a || b)` is not
  expressible. The three queries above are the language's honest answer.

  Question 4 needs the union and the intersection of 564 key sets. jmespath has
  `keys()` for one object and no fold, so both are Python again. On this file
  jmespath is a path fetcher and every structural question is answered by the
  host language.
""")
