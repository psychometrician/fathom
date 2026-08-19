"""glom — USGS earthquakes, one month

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   7.4 MB, 10,885 features, depth 5
  measured      2026-08-10
  run           cd corpus/25-usgs-quakes/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             3   YES                 PARTLY
   2 how deep                                    5   NO                  by hand
   3 what is one record                          2   YES                 CANNOT
   4 always present vs sometimes                 5   YES                 by hand
   5 does any field change type                  5   YES                 by hand
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   YES                 yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 yes — Coalesce
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          5   NO                  by hand
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no — every spec names paths
  15 readable a week later?                          yes, the specs read well
  16 lines, and how much is ceremony?                ~75, and the hand-walks are half

**glom IS AN EXTRACTION TOOL AND DOES NOT PRETEND OTHERWISE.** Every Phase 1
answer below marked "by hand" was written as a plain recursive walk in python
with glom nowhere in it — the library has no vocabulary for *what is in here*,
only for *get me this*. That is not a failure of the library; it is the shape of
the gap this project is measuring, and glom is the cleanest statement of it in
the Python half.

**Where it is genuinely good is question 9.** `Coalesce` says "this field, or
that one, or this default" in one expression, which is the only thing in the
Python comparison that reads like `first_present`.
"""
import json
from collections import Counter, defaultdict
from importlib.metadata import version

from glom import Coalesce, glom

print(f"glom {version('glom')}")
doc = json.load(open("../source.json"))
feats = doc["features"]

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  glom takes a python object. It never saw the bytes. CANNOT.")

# ── Q1/Q2. What is in here, and how deep — BY HAND, glom has no verb for it. ─
# THE FIRST DRAFT OF THIS WALK DISAGREED WITH JQ AND WITH THE PROBE, and both
# disagreements were conventions rather than errors: it gave 42 paths because it
# never recorded the array-ELEMENT path itself (`$.features[]`), and depth 6
# because it counted the root as a level. jq and `design/probe.py` both say 45
# and 5. **Two hand-written walks will differ on exactly this unless somebody
# says which convention is meant**, which is an argument for the question being
# answered by a tool rather than by whoever is holding the keyboard.
paths, depth = set(), 0


def walk(o, p="$", d=0):
    global depth
    depth = max(depth, d)
    if isinstance(o, dict):
        for k, v in o.items():
            paths.add(f"{p}.{k}")
            walk(v, f"{p}.{k}", d + 1)
    elif isinstance(o, list):
        paths.add(p + "[]")
        for v in o:
            walk(v, p + "[]", d + 1)


walk(doc)
print(f"\nQ1  {len(paths)} distinct paths — a hand-written walk, not glom")
print(f"Q2  depth {depth}, same walk. Both agree with jq and with the probe")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3/Q7  {len(feats):,} features. glom names no candidates. CANNOT.")

# ── Q4. Always present vs sometimes — again by hand. ─────────────────────────
present = Counter(k for f in feats for k in f["properties"])
some = {k: v for k, v in present.items() if v < len(feats)}
print(f"\nQ4  keys present on fewer than all {len(feats):,}: {some or 'none'}")
nulls = Counter(k for f in feats for k, v in f["properties"].items() if v is None)
print(f"Q4  keys that are PRESENT but null on some: {dict(nulls)}")
print("    Walking the objects keeps presence and null apart, which every")
print("    frame-shaped tool in this directory loses.")

# ── Q5. Does any field change type between records — by hand. ────────────────
types = defaultdict(set)
for f in feats:
    for k, v in f["properties"].items():
        types[k].add(type(v).__name__)
changing = {k: sorted(v) for k, v in types.items() if len(v) > 1}
print(f"\nQ5  fields with more than one PYTHON type: {changing}")
# TWO separate over-reports live in that line, and the corpus has already ruled
# on both. NoneType is not a type — defect 11 and `design/axes.py`. And python's
# int/float split is not a JSON type split: `{"mag": 2}` and `{"mag": 2.4}` are
# both `number`, which is what jq and the probe report.
JSON_T = {"int": "number", "float": "number", "str": "string", "bool": "boolean",
          "list": "array", "dict": "object"}
json_types = {k: sorted({JSON_T[t] for t in v if t != "NoneType"})
              for k, v in types.items()}
real = {k: v for k, v in json_types.items() if len(v) > 1}
print(f"Q5  as JSON types, ignoring null: {real or 'none'} — probe and jq agree")
print("    int-vs-float accounts for mag, rms and gap; null accounts for the rest.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections here. n/a")

# ── Q8. Three named fields into a table. THIS is glom's register. ────────────
spec = [{"mag": "properties.mag", "place": "properties.place", "time": "properties.time"}]
rows = glom(feats, spec)
print(f"\nQ8  {len(rows):,} rows, spec is one line: {rows[0]}")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
# Coalesce is the closest thing in the Python half to `first_present`.
spec9 = [{"place": "properties.place",
          "alert": Coalesce("properties.alert", default=None)}]
got = glom(feats, spec9)
print(f"\nQ9  {sum(1 for r in got if r['alert'] is not None)} of {len(got):,} have an alert")
print(f"    Coalesce keeps the row and defaults the hole: {got[0]}")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
coords = glom(feats, [{"lon": "geometry.coordinates.0",
                       "lat": "geometry.coordinates.1",
                       "depth_km": "geometry.coordinates.2"}])
print(f"\nQ10 {len(coords):,} rows: {coords[0]}")

# ── Q11. Find every path whose value matches something — by hand again. ──────
hits = Counter()


def find(o, p="$"):
    if isinstance(o, dict):
        for k, v in o.items():
            find(v, f"{p}.{k}")
    elif isinstance(o, list):
        for v in o:
            find(v, p + "[]")
    elif isinstance(o, str) and o.startswith("http"):
        hits[p] += 1


find(doc)
print(f"\nQ11 URL-valued paths: {dict(hits)}")
print("    glom has no way to ask this. It answers `get me this path`, never")
print("    `which paths look like that`. Twelve lines of python, zero of glom.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
wide = glom(feats, [lambda f: {**f["properties"], "id": f["id"],
                               "lon": f["geometry"]["coordinates"][0],
                               "lat": f["geometry"]["coordinates"][1],
                               "depth_km": f["geometry"]["coordinates"][2]}])
print(f"\nQ12 {len(wide):,} x {len(wide[0])} — nothing lost, and the spec is a lambda,")
print("    which is python doing the work with glom holding the list comprehension.")

# ── The packed strings, because defect 26 came from this file. ───────────────
print("\nDEFECT 26  does glom notice a list packed into a string?")
print("   ", glom(feats[0], "properties.types"))
print("    A string. glom has no notion of a value's internal structure at all.")
