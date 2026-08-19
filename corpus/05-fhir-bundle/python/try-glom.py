"""glom — a Synthea FHIR bundle

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
  measured      2026-08-09
  run           cd corpus/05-fhir-bundle/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  PARTLY
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   7 how many records                            1   YES                 partly
   9 a field missing from some records           6   YES                 YES

WHY THIS FILE MATTERS MOST FOR glom. FHIR's `value[x]` writes one field under
eight different names — `valueQuantity`, `valueString`, `valueCodeableConcept` and
so on. `design/vocabulary.md` proposes `first_present` for exactly this and has
never run it. **`Coalesce` is `first_present`, shipped, in a library that has
existed for years.** This attempt is the closest thing to a prior-art check the
project has, and it belongs on the record.
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

from glom import Coalesce, glom

print(f"python {sys.version.split()[0]}, glom {version('glom')}")

doc = json.load(open("../source.json"))
res = [e["resource"] for e in doc["entry"]]

print(f"\n1/7. {len(res)} resources. Top-level keys of the bundle: "
      f"{sorted(doc)}")
print("     and that is `sorted(dict)`. glom has no describer, established on")
print("     files 01, 02 and 04 and unchanged here.")

# ── 9. value[x], which is what this file was chosen for ──────────────────────
VALUE = Coalesce("valueQuantity", "valueCodeableConcept", "valueString",
                 "valueBoolean", "valueInteger", "valueRatio", "valueTime",
                 "valueDateTime", "valuePeriod", default=None)
got = [glom(r, VALUE) for r in res]
hits = sum(1 for g in got if g is not None)
print(f"\n9. one Coalesce over nine spellings found a value on {hits} of "
      f"{len(res)} resources")

kinds = Counter()
for r in res:
    for k in r:
        if k.startswith("value") and k[5:6].isupper():
            kinds[k] += 1
print(f"   the spellings actually present, and their counts:")
for k, v in kinds.most_common():
    print(f"     {k:<26} {v}")
print(f"   nine were guessed and {len(kinds)} exist — the ones not guessed would")
print(f"   have been silently absent, which is the cost of writing the list.")

print("""
PRIOR ART FOR `first_present`, stated plainly.

  design/vocabulary.md derives `first_present(a, b, …)` from question 9 and marks
  it unrun. glom's `Coalesce` is the same operation with a different name, in a
  library that predates this project, and on this document it works.

  That does NOT retire the word. Two things differ and both are the project's
  actual claim:

    - `Coalesce` takes the alternatives as arguments. Every spelling above was
      typed by a person who already knew FHIR's `value[x]` convention. fathom's
      case for the word is that the DESCRIBER supplies the list, having found the
      eight spellings itself — which is question 1, and glom has no answer to it.

    - `Coalesce` returns the value and forgets which path produced it. On this
      file the path IS the type: `valueQuantity` and `valueString` mean different
      things, and a column of reconciled values without the spelling has lost the
      only thing that distinguished them.

  So the finding is that the extraction half of `first_present` is solved prior
  art and the project should say so, and that the half fathom is actually
  proposing — deriving the alternatives rather than being told them — is
  untouched by it.

3, 4. cannot, as on every other file.
""")
