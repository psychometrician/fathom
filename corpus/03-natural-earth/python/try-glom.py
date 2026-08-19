"""glom — Natural Earth country geometry

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   3.9 MB, 241 features, GeoJSON
  measured      2026-08-09
  run           cd corpus/03-natural-earth/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   YES                 PARTLY
   5 does any field change type                  -   -                   cannot
   7 how many records                            1   YES                 YES
   8 three named fields to a table               4   YES                 YES

WHY THIS FILE. glom has no describer — established on four files now. GeoJSON is
where its extraction side should be effortless, since the record is declared by
the format, and it is. Recorded so the grid is not only a list of refusals.
"""
import json, sys
from importlib.metadata import version
from glom import glom, Iter, T

print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = json.load(open("../source.json"))

print(f"\n7. features: {len(doc['features'])}")
print(f"1. top-level keys: {sorted(doc)} — `sorted(dict)`, not glom.")

rows = glom(doc, ("features", Iter({
    "name": "properties.name",
    "iso": "properties.iso_a3",
    "kind": "geometry.type",
}).all()))
print(f"\n8. three named fields to a table: {len(rows)} rows x {len(rows[0])} cols")
for r in rows[:3]:
    print(f"     {r['name']:<20} {r['iso']:<5} {r['kind']}")
print("   one spec, no ceremony, and the cleanest extraction in the corpus.")
print("   It is clean because GeoJSON answered question 3 before anyone looked.")
print("""
   AND GLOM RAISED WHEN THE NAMES WERE WRONG, WHICH IS THE FINDING.
   This spec was first written with `properties.NAME` and `properties.ISO_A3`,
   guessed from Natural Earth's documentation. glom raised PathAccessError and
   named the missing key. jmespath, given the identical wrong paths, returned
   241 rows of None and reported success — a full-size table of nothing.

   On a document you have never seen, every path is a guess. A tool that fails
   loudly on a wrong guess and a tool that returns the right SHAPE full of
   nulls are not comparable, and the grid's `worked` column cannot express the
   difference. It is the most consequential thing measured on this file.""")

print("""
5. cannot, and here it matters more than usual.

  glom fetches `geometry.coordinates` and hands back a list. It has no opinion
  about whether that list nests 3 deep or 4, which on this file is the difference
  between a Polygon and a MultiPolygon — the only structural variation the
  document has. A tool built to reshape data is blind to the one reshaping
  decision this file forces.
""")
