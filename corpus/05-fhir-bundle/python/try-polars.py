"""polars — a Synthea FHIR bundle

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
  measured      2026-08-09
  run           cd corpus/05-fhir-bundle/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is it sound                                18   no                  CANNOT OPEN
   1 what is in here                             -   -                   CANNOT OPEN
   2 how deep                                    -   -                   CANNOT OPEN
   3 what is one record                          -   -                   CANNOT OPEN
   4 always present vs sometimes                 -   -                   CANNOT OPEN
   5 does any field change type                  -   -                   CANNOT OPEN
   6 are any keys actually data                  -   -                   CANNOT OPEN
   7 how many records                            -   -                   CANNOT OPEN

  **Every row is CANNOT OPEN, which is a first for this grid.** The code below
  question 0 is kept and never executes; it is what the attempt would have done,
  left in place so a future polars release can be re-run against it unchanged.

WHY THIS FILE. polars aborted on `04-gharchive` because it infers a schema from a
sample and the data was ragged. This document is worse in exactly that way: one
array holding 20 record kinds, 97 fields in the union, and only `id` and
`resourceType` present on all of them.
"""
import json
import sys
from importlib.metadata import version

import polars as pl

print(f"python {sys.version.split()[0]}, polars {version('polars')}")

# ── 0. does it read at all ───────────────────────────────────────────────────
print("\n0. polars on the bundle:")
for label, kw in [("default", {}), ("infer_schema_length=None", {"infer_schema_length": None})]:
    try:
        h = pl.read_json("../source.json", **kw).height
        print(f"     {label:<26} OK, {h} row(s)")
    except Exception as e:
        print(f"     {label:<26} FAILED — {type(e).__name__}: "
              f"{str(e).splitlines()[0][:44]}")

print("""
   polars CANNOT READ THIS DOCUMENT. Both settings fail with

     error deserializing value Object({"reference": ..., "display": ...}) as list

   which is `location`: an object on Immunization, Procedure and ImagingStudy,
   an array on Encounter. polars picked `list` from what it saw first and the
   object contradicts it.

   THE ERROR'S OWN ADVICE DOES NOT WORK. It says "Try increasing
   `infer_schema_length` or specifying a schema", and `infer_schema_length=None`
   reads every record and fails identically — because this is not a sampling
   problem. No amount of looking reconciles an object with a list. The remaining
   suggestion, specifying a schema, is asking the user for question 1's answer.

   On 04-gharchive the same message was correct and the flag fixed it. Here the
   same message is a dead end, and nothing distinguishes the two cases from the
   outside.

   `location` is one of the four fields DuckDB stored as raw JSON, and one of the
   three design/probe.py flags as changing type. All three tools found this
   field. Only polars is stopped by it.
""")

size = len(open("../source.json", "rb").read())
# Everything below needs a frame, so fall back to the entries alone, which is
# already a person deciding what a record is — question 3, supplied by hand.
doc = json.load(open("../source.json"))
try:
    df = pl.read_json("../source.json", infer_schema_length=None)
except Exception:
    df = None

if df is None:
    print("\n1, 2, 4, 5, 6, 7. all unanswerable: there is no frame to inspect.")
    print(f"   For scale, the entries a person would have to hand it: "
          f"{len(doc['entry'])}")
    kinds = {}
    for e in doc["entry"]:
        kinds[e["resource"]["resourceType"]] = \
            kinds.get(e["resource"]["resourceType"], 0) + 1
    print(f"   and the {len(kinds)} kinds polars never got far enough to see.")
    print("""
  This is the first file in the corpus that a tool in the comparison cannot
  open. jmespath could not READ 02-hn-thread in the sense of reaching its
  records, but it parsed. polars parses the JSON and then refuses to build a
  frame, which for a dataframe library is the same thing as refusing the file.
""")
    raise SystemExit(0)

schema = df.schema

# ── 1 / 2. what the schema costs ─────────────────────────────────────────────
print(f"\n1. top-level columns: {len(schema)}")
print(f"   schema as one string: {len(str(schema)):,} characters "
      f"({len(str(schema)) / size:.1%} of the document)")
print(f"   npm 486,924 = 60% · thread 3,154 = 1.6% · gharchive 18,155")

def type_depth(dt):
    inner = getattr(dt, "inner", None)
    if inner is not None:
        return 1 + type_depth(inner)
    fields = getattr(dt, "fields", None)
    if fields:
        return 1 + max(type_depth(f.dtype) for f in fields)
    return 0

print(f"\n2. deepest nesting in the schema: "
      f"{max(type_depth(t) for t in schema.values())}   (axes.py grades 11)")

# ── 3 / 7. the test ──────────────────────────────────────────────────────────
print(f"\n7. rows polars reports: {df.height}")
doc = json.load(open("../source.json"))
print(f"   entries inside: {len(doc['entry'])}")
print("\n3. does polars suggest the entries are 20 kinds? No. `entry` is one")
print("   list column of one struct type, and that struct is the union of every")
print("   resource kind. Exploding it gives one very wide, very empty frame.")

ex = df.explode("entry").unnest("entry")
print(f"   df.explode('entry').unnest('entry') -> {ex.height} rows x "
      f"{ex.width} cols")
kinds = ex.unnest("resource").select("resourceType").n_unique()
print(f"   and `resourceType` has {kinds} distinct values — visible only because")
print("   a person unnested twice and then named the column.")

print("""
4, 5, 6. cannot.

  Question 4 is the one polars structurally cannot answer here. It gives `entry`
  ONE struct type, so a field carried by 1 of 564 resources and a field carried
  by all 564 are both simply members of that struct. The distinction between
  always and sometimes is the whole of question 4 and the type system erases it
  on read.

  DuckDB, given the same document, at least emits `JSON` where it gave up, which
  is four characters of honesty. polars unifies silently.
""")
