"""jq (Python binding) — a Synthea FHIR bundle

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
  measured      2026-08-09
  run           cd corpus/05-fhir-bundle/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  WRONG
   2 how deep                                    1   no                  YES
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 3   YES                 YES
   5 does any field change type                  4   no                  YES
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 YES

WHY THIS FILE. jq is the only tool in the comparison with no schema, so it is the
only one that cannot be stopped by a type conflict — polars refuses this document
outright and DuckDB stores four fields as raw JSON. The cost of having no schema
is that nothing is ever reconciled FOR you, and this file shows both sides.
"""
import json
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq {version('jq')}")

doc = json.load(open("../source.json"))
ask = lambda e: jq.compile(e).input_value(doc).first()

# ── 1 / 2 / 7 ────────────────────────────────────────────────────────────────
print(f"\n1. distinct field names: "
      f"{ask('[paths(type != \"object\" and type != \"array\")|map(select(type==\"string\"))|last]|unique|length')}")
print("   the union of every resource kind's fields, flattened together, and the")
print("   same paths(scalars) blind spot as files 01, 02 and 04.")
print(f"2. depth: {ask('[paths|length]|max')}   (axes.py grades 11)")
print(f"7. entries: {ask('.entry|length')}   "
      f"(only because a person named `entry`)")

# ── 5. the thing jq CAN do that the type systems cannot ──────────────────────
poly = ask('''
  [.entry[].resource|to_entries[]]|group_by(.key)
  |map({key: .[0].key, types: ([.[].value|type]|unique)})
  |map(select(.types|length > 1))
''')
print(f"\n5. fields taking more than one type across the 564 resources: {len(poly)}")
for p in poly:
    print(f"     {p['key']:<14} {', '.join(sorted(p['types']))}")
print("   design/probe.py reports three: type, location, total.")
print("   DuckDB stored four as raw JSON: those three plus `category`.")

# ── 3. the test this file exists for ─────────────────────────────────────────
print("\n3. does jq suggest the 564 entries are 20 kinds? No — but it is the")
print("   only tool here that shows you the evidence without being asked:")
counts = ask('[.entry[].resource|keys|length]|{min: min, max: max}')
print(f"     resource key counts range {counts['min']}..{counts['max']} — the")
print("     records are visibly not one shape, and that is as far as it goes.")

kinds = ask('[.entry[].resource.resourceType]|group_by(.)|map({(.[0]): length})|add')
print(f"\n   once a person writes `group_by(.resourceType)`: {len(kinds)} kinds")
for k, v in sorted(kinds.items(), key=lambda kv: -kv[1])[:5]:
    print(f"     {k:<24} {v:>4}")

# ── 4. always vs sometimes, which needs question 3 answered first ───────────
always = ask('[.entry[].resource|keys]|reduce .[] as $k (null; '
             'if .==null then $k else .-(.-$k) end)')
union = ask('[.entry[].resource|keys[]]|unique|length')
print(f"\n4. {len(always)} fields on every resource ({', '.join(always)}), "
      f"{union} in the union")
print("   which is the probe's 'always id resourceType' and its 97, exactly.")

print("""
6. cannot, as everywhere.

  The pair of numbers in question 4 is the whole finding of this file and jq
  produces it in one expression: 2 fields always, 97 in the union, across 564
  records. A 97-column table with 2 reliable columns is a table that should be
  several tables.

  **jq shows the evidence and draws no conclusion.** That is not a criticism —
  it is a query language and concluding is not its job. It is the precise gap
  design/probe.py's fourth operation fills, and the reason that operation is
  worth having is that nothing else in either language takes this step.
""")
