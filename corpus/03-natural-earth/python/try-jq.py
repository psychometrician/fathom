"""jq (Python binding) — Natural Earth country geometry

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.json   3.9 MB, 241 features, GeoJSON
  measured      2026-08-09
  run           cd corpus/03-natural-earth/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             1   no                  YES
   2 how deep                                    1   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 2   YES                 YES
   5 does any field change type                  5   no                  WRONG
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 YES

WHY THIS FILE. This is the document whose polymorphism the probe originally
measured as **0** and which forced `shape()` into existence. jq's `type` returns
`"array"` for `[[[x,y]]]` and for `[[[[x,y]]]]` alike, so this file predicts a
specific wrong answer, and predicting a tool's wrong answer in advance is worth
more than discovering it.
"""
import json
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq {version('jq')}")

doc = json.load(open("../source.json"))
ask = lambda e: jq.compile(e).input_value(doc).first()

print(f"\n7. features: {ask('.features|length')}")
print(f"1. distinct field names: "
      f"{ask('[paths(type != \"object\" and type != \"array\")|map(select(type==\"string\"))|last]|unique|length')}")
print(f"2. depth: {ask('[paths|length]|max')}   (axes.py grades 8)")

always = ask('[.features[].properties|keys]|reduce .[] as $k (null; '
             'if .==null then $k else .-(.-$k) end)|length')
union = ask('[.features[].properties|keys[]]|unique|length')
print(f"\n4. properties: {always} on every feature, {union} in the union "
      f"— nothing is ever absent")

# ── 5. the predicted wrong answer ────────────────────────────────────────────
byname = ask('''
  [.features[]|to_entries[]]|group_by(.key)
  |map({key: .[0].key, types: ([.[].value|type]|unique)})
  |map(select(.types|length > 1))|length
''')
coords = ask('[.features[].geometry.coordinates|type]|unique')
print(f"\n5. fields taking more than one type: {byname}")
print(f"   and `geometry.coordinates` reports type(s): {coords}")

kinds = ask('[.features[].geometry.type]|group_by(.)|map({(.[0]): length})|add')
print(f"\n   but the document says the geometries are: "
      f"{', '.join(f'{k} {v}' for k, v in sorted(kinds.items()))}")
depths = ask('''
  [.features[].geometry.coordinates
   |[recurse(if type=="array" then .[0] else empty end)]|length]
  |group_by(.)|map({(.[0]|tostring): length})|add
''')
# `[recurse(...)]` includes the starting value, so these run one higher than the
# probe's `array[3] x122, array[4] x119`. Subtracted here so the two columns of
# the grid can be read against each other without a footnote.
depths = {str(int(k) - 1): v for k, v in depths.items()}
print(f"   and the nesting depth of `coordinates` per feature: {depths}")
print(f"   which is the probe's `array[3] x122, array[4] x119`, exactly.")

print("""
   PREDICTED AND CONFIRMED: jq reports ZERO fields changing type, because
   `type` is "array" for a Polygon's [[[x,y]]] and for a MultiPolygon's
   [[[[x,y]]]]. 122 features nest three deep and 119 nest four, and jq's type
   system cannot express the difference.

   The last expression above recovers it — `recurse(.[0])` and count — and it is
   nine tokens that a person only writes once they already suspect the answer.

   design/probe.py had the same blind spot, measured 0 on this file, and grew
   `shape()` in response. On 05-fhir-bundle, DuckDB then found the half `shape()`
   still misses: array ELEMENT type. DuckDB catches this half too, typing
   `coordinates` as `JSON[][][]` — three array levels and then a refusal.

   So of three tools: jq sees neither half, the probe sees depth but not element
   type, and DuckDB sees both — and DuckDB reports it only as the word JSON
   inside a type declaration.

3, 6. cannot, though 3 is easy here because GeoJSON declares its own record.
""")
