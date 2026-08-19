"""pydash — USGS earthquakes, one month

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   7.4 MB, 10,885 features, depth 5
  measured      2026-08-10
  run           cd corpus/25-usgs-quakes/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             3   YES                 PARTLY
   2 how deep                                    2   -                   CANNOT
   3 what is one record                          1   YES                 CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  4   YES                 by hand
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   YES                 yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              8   YES                 yes, NOT via default
  10 flatten the deepest array                   2   YES                 yes
  11 find every path matching something          2   -                   CANNOT
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    YES, for every answer
  14 survives the next file unchanged?               no — every call names a path
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~55, almost none

**pydash IS LODASH, AND LODASH IS FOR DATA YOU ALREADY UNDERSTAND.** `get` with
a dotted path and a default is genuinely pleasant, and `pluck`/`map_` make the
extraction one-liners. But there is no `paths`, no descend, no schema and no way
to ask a question whose answer you cannot already spell — questions 2 and 11 are
CANNOT for the same reason they are in jmespath.

**The one thing it does that jmespath cannot** is take an arbitrary python
callable, so anything genuinely exploratory is possible — as python, with pydash
holding the iteration. That is the same verdict glom got, and by now it is the
Python half's refrain rather than a finding about any one library.

**And one thing it does that four of the eight cannot**, found by running it
rather than by reading the docs: `_.get(f, 'properties.alert', 'none')` returns
**None, not the default**, because the key is PRESENT and holds null. pydash
keeps presence and null apart; pandas, polars, duckdb and jmespath all lose the
distinction.
"""
import json
from collections import Counter, defaultdict
from importlib.metadata import version

import pydash as _

print(f"pydash {version('pydash')}")
doc = json.load(open("../source.json"))
feats = doc["features"]

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pydash takes a parsed object. It never saw the bytes. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
print("\nQ1  root keys:", _.keys(doc))
print("Q1  a feature's keys:", _.keys(feats[0]))
print("Q1  its properties' keys:", len(_.keys(feats[0]["properties"])), "fields")
print("    One object at one level, exactly like jmespath's keys().")
print("Q2  CANNOT — no recursive descent, so depth is not expressible.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3/Q7  {_.size(feats):,} features. No candidates named. CANNOT for Q3.")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
present = Counter(k for f in feats for k in f["properties"])
n = len(feats)
print(f"\nQ4  keys present on fewer than all {n:,}: "
      f"{ {k: v for k, v in present.items() if v < n} or 'none'}")
print("    That count is a python Counter, not pydash. `_.has(f, 'properties.alert')`")
print("    answers PER OBJECT and would need the same loop around it.")
print(f"Q4  _.has on the first feature: {_.has(feats[0], 'properties.alert')} — "
      "so presence IS reachable, one object at a time.")

# ── Q5. Does any field change type between records? ──────────────────────────
types = defaultdict(set)
for f in feats:
    for k, v in f["properties"].items():
        types[k].add("null" if v is None else
                     "number" if isinstance(v, (int, float)) and not isinstance(v, bool)
                     else "string" if isinstance(v, str) else type(v).__name__)
changing = {k: sorted(v - {"null"}) for k, v in types.items() if len(v - {"null"}) > 1}
print(f"\nQ5  fields changing JSON type, ignoring null: {changing or 'none'}")
print("    Agrees with jq, ijson, glom and the probe. Written as a python loop;")
print("    pydash has no verb that surveys a field across records.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections here. n/a")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
rows = _.map_(feats, lambda f: {"mag": _.get(f, "properties.mag"),
                                "place": _.get(f, "properties.place"),
                                "time": _.get(f, "properties.time")})
print(f"\nQ8  {len(rows):,} rows: {rows[0]}")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
# `get` with a default is pydash's `first_present`-adjacent move, and unlike
# glom's Coalesce it takes ONE path rather than a priority list.
rows9 = _.map_(feats, lambda f: {"place": _.get(f, "properties.place"),
                                 "alert": _.get(f, "properties.alert", "none")})
print(f"\nQ9  {sum(1 for r in rows9 if r['alert'] not in ('none', None))} have an alert;")
print(f"    {rows9[0]}")
print("    **THE DEFAULT DID NOT FIRE, and that is the useful part.** `_.get`")
print("    returns the default only when the key is MISSING; here every feature")
print("    HAS `alert` and 10,809 of them hold null, so `get` returns None and")
print("    the default is never reached. pydash keeps presence and null apart —")
print("    which pandas, polars and duckdb cannot, and jmespath cannot either.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
coords = _.map_(feats, lambda f: dict(zip(("lon", "lat", "depth_km"),
                                          _.get(f, "geometry.coordinates"))))
print(f"\nQ10 {len(coords):,} rows: {coords[0]}")

# ── Q11. Find every path whose value matches something. ──────────────────────
print("\nQ11 CANNOT. No `paths`, no descend, no predicate over unnamed keys.")
print("    Same wall as jmespath, and the same workaround: write the walk yourself.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
wide = _.map_(feats, lambda f: {**f["properties"], "id": f["id"],
                                **dict(zip(("lon", "lat", "depth_km"),
                                           _.get(f, "geometry.coordinates")))})
print(f"\nQ12 {len(wide):,} x {len(wide[0])}. Nothing lost; the coordinate names are mine.")

# ── The packed strings, because defect 26 came from this file. ───────────────
print("\nDEFECT 26  does pydash notice a list packed into a string?")
print("   ", _.get(feats[0], "properties.types"))
print("    A string. pydash CAN act on it once told —")
print("   ", _.compact(_.get(feats[0], "properties.types").split(",")))
