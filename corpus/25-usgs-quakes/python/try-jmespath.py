"""jmespath — USGS earthquakes, one month

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   7.4 MB, 10,885 features, depth 5
  measured      2026-08-10
  run           cd corpus/25-usgs-quakes/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             3   YES                 PARTLY — keys()
   2 how deep                                    2   -                   CANNOT
   3 what is one record                          1   YES                 CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  3   YES                 PARTLY
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   YES                 yes
   8 three named fields to a table               2   YES                 yes — best here
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   2   YES                 yes
  11 find every path matching something          2   -                   CANNOT
  12 flattest honest table                       3   YES                 PARTLY
  13 needed the shape in advance?                    YES, for every answer
  14 survives the next file unchanged?               no — every expression names keys
  15 readable a week later?                          YES — the cleanest syntax here
  16 lines, and how much is ceremony?                ~55, almost none

**jmespath HAS NO WAY TO ASK ABOUT A DOCUMENT IT HAS NOT BEEN TOLD ABOUT.**
There is no `paths`, no wildcard-descend, no way to reach a key whose name you
do not already know beyond `keys()` one level at a time. Questions 2 and 11 are
CANNOT — not awkward, not slow, absent.

**Its Phase 2 answers are the most readable in the Python half.** The multiselect
hash is a table definition that a person can read aloud, and question 8 is one
expression with no imports, no lambdas and no schema.
"""
import json
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))


def q(expr, d=doc):
    return jmespath.search(expr, d)


# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  jmespath receives a parsed object. It never saw the bytes. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
print("\nQ1  keys(@) at the root:", q("keys(@)"))
print("Q1  keys of one feature:", q("features[0] | keys(@)"))
print("Q1  keys of its properties:", q("features[0].properties | keys(@)"))
print("    `keys()` reads ONE object at ONE level. To list the document I would")
print("    have to walk it myself, and jmespath has no recursion to do that with.")
print("Q2  CANNOT. There is no descend-and-report; depth is not expressible.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3/Q7  length(features) = {q('length(features)'):,}. No candidates named. CANNOT for Q3.")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
n = q("length(features)")
for k in ("alert", "felt", "tz", "mag"):
    got = q(f"length(features[?properties.{k} != null])")
    print(f"Q4  {k:6} non-null on {got:>6,} of {n:,}")
print("    PARTLY: this counts NON-NULL, not PRESENT, and jmespath cannot")
print("    distinguish them — `properties.alert` is null whether the key was")
print("    absent or explicitly null. Same blindness as the data frames, for a")
print("    different reason: not a schema, but a path language with no `has`.")

# ── Q5. Does any field change type between records? ──────────────────────────
print(f"\nQ5  type(features[0].properties.mag) = {q('type(features[0].properties.mag)')}")
kinds = {q(f"type(features[{i}].properties.alert)") for i in range(0, n, 500)}
print(f"Q5  sampling alert every 500th feature: {kinds}")
print("    PARTLY, and only because I named the field. There is no way to ask")
print("    `which fields vary` — `type()` takes one value at a time.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections here. n/a")

# ── Q8. Three named fields into a table. THE THING IT IS FOR. ────────────────
rows = q("features[].{mag: properties.mag, place: properties.place, time: properties.time}")
print(f"\nQ8  one expression, {len(rows):,} rows: {rows[0]}")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
rows9 = q("features[].{place: properties.place, alert: properties.alert}")
print(f"\nQ9  {sum(1 for r in rows9 if r['alert'] is not None)} of {len(rows9):,} have an alert;")
print(f"    rows are kept and the hole is null: {rows9[0]}")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
coords = q("features[].{lon: geometry.coordinates[0], lat: geometry.coordinates[1], "
           "depth_km: geometry.coordinates[2]}")
print(f"\nQ10 {len(coords):,} rows: {coords[0]}")

# ── Q11. Find every path whose value matches something. ──────────────────────
print("\nQ11 CANNOT. There is no `paths`, no recursive descent, and no way to")
print("    test a value without first naming the key that holds it.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
wide = q("features[].merge(properties, {id: id, lon: geometry.coordinates[0], "
         "lat: geometry.coordinates[1], depth_km: geometry.coordinates[2]})")
print(f"\nQ12 {len(wide):,} x {len(wide[0])} via merge(). Nothing lost — but the")
print("    three coordinate names are mine, so it is a table I specified.")

# ── The packed strings, because defect 26 came from this file. ───────────────
print("\nDEFECT 26  does jmespath notice a list packed into a string?")
print("   ", q("features[0].properties.types"))
print("    A string, and jmespath has no string-splitting function at all —")
print("    it is the one tool here that could not act on it even once told.")
