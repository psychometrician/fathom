"""jq (via the `jq` python binding) — USGS earthquakes, one month

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   7.4 MB, 10,885 features, depth 5
  measured      2026-08-10
  run           cd corpus/25-usgs-quakes/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             5   NO                  YES — 45
   2 how deep                                    1   NO                  YES — 5
   3 what is one record                          2   YES                 CANNOT
   4 always present vs sometimes                 4   NO                  YES — best here
   5 does any field change type                  5   NO                  yes, with a caveat
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   YES                 yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   2   YES                 yes
  11 find every path matching something          4   NO                  YES — best here
  12 flattest honest table                       3   YES                 PARTLY
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
  14 survives the next file unchanged?               yes for 1, 2, 4, 5, 11
  15 readable a week later?                          the array-index fold needs a comment
  16 lines, and how much is ceremony?                ~90, and the folds are most of it

**jq INDEPENDENTLY REPRODUCES THE PROBE ON QUESTIONS 1, 2 AND 5.** 45 distinct
path shapes and depth 5 are exactly what `design/probe.py` printed, and once
null is excluded jq agrees that **no field on this document changes type** —
which is `design/axes.py`'s rule arrived at from the other direction.

**IT IS ALSO THE ONLY TOOL HERE THAT ANSWERS QUESTION 4 CORRECTLY.** `keys`
counts PRESENCE, so jq reports every one of the 26 property keys on every one of
the 10,885 features — which is the truth. pandas, polars and duckdb all report
six fields as "sometimes", because each of them built a frame first and **once a
row exists, absent and null are the same hole.** That is item 22's five-to-eight
split reappearing on a document chosen for something else entirely.

**AND ONLY JQ FOUND ALL THREE URL PATHS.** `metadata.url` sits outside
`features`, so the frame-shaped tools never looked at it: pandas and polars found
two, duckdb found two, jq found three.

**What it cannot do is question 3.** jq names no row candidates and prices
nothing; I picked `features` because I had already read Q1's output. The two
folds — collapsing array indices, and excluding null before judging a type —
are both things I had to write, and both are things the probe does unasked.
"""
import json
from importlib.metadata import version

import jq

print(f"jq (python binding) {version('jq')}")
doc = json.load(open("../source.json"))


def q(prog, d=doc):
    return jq.compile(prog).input(d).all()


# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  jq parses or fails. Nothing about duplicate keys, big ints or")
print("    encoded payloads — and the LAST duplicate silently wins. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
# `paths` is the closest thing to an answer, and it is O(data): it enumerates
# every path in every record, so it must be folded by hand to be readable.
shapes = q('[paths | map(if type=="number" then "[]" else . end) | join(".")] '
           '| unique | length')[0]
print(f"\nQ1  distinct path SHAPES after folding array indices: {shapes}")
print("Q1  the shapes:", q('[paths | map(if type=="number" then "[]" else . end) '
                           '| join(".")] | unique')[0][:12], "…")
print(f"Q2  depth: {q('[paths | length] | max')[0]}")
print("    Both answers required WRITING THE FOLD. `paths` alone yields one entry")
print("    per array element, which on this file is millions of them.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3/Q7  .features | length = {q('.features | length')[0]:,}")
print("    jq names no candidates and prices nothing. I chose `features` because")
print("    I had already read Q1's output. CANNOT, in the sense the question means.")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
# `from_entries` wants `key`/`value`; the first draft emitted `key`/`n` and got
# a dict of Nones without complaining, which is the quiet kind of wrong.
counts = q('[.features[].properties | keys[]] | group_by(.) '
           '| map({key: .[0], value: length}) | from_entries')[0]
n = q('.features | length')[0]
print(f"\nQ4  key counts over {n:,} features:")
print("   ", {k: v for k, v in counts.items() if v < n} or "every key on every feature")
print("    NOTE `keys` includes a key whose value is null, so this counts PRESENCE.")
print("    That is the right answer to Q4 and the one the data frames cannot give.")

# ── Q5. Does any field change type between records? ──────────────────────────
types = q('[.features[].properties | to_entries[] | {k: .key, t: (.value|type)}] '
          '| group_by(.k) | map({key: .[0].k, value: (map(.t) | unique)}) | from_entries')[0]
changing = {k: v for k, v in types.items() if len(v) > 1}
print(f"\nQ5  fields taking more than one JSON type: {changing}")
print("    Every one of these is X-or-null. jq reports null AS a type, so this")
print("    over-reports exactly the way pandas does — and `design/axes.py` and")
print("    defect 11 both rule that a null is not a type.")
real = {k: v for k, v in changing.items() if set(v) - {"null"} and len(set(v) - {"null"}) > 1}
print(f"Q5  fields that change type IGNORING null: {real or 'none'}")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections here. n/a")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
print("\nQ8 ", q('[.features[] | {mag: .properties.mag, place: .properties.place, '
                 'time: .properties.time}] | .[0:2]')[0])

# ── Q9. A field missing from some records, keeping those rows. ───────────────
print("\nQ9  features whose alert is non-null:",
      q('[.features[] | select(.properties.alert != null)] | length')[0])
print("    and keeping ALL rows with the field as-is is the default — jq gives")
print("    null rather than dropping, which is what the question asks for.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
print("\nQ10 ", q('[.features[] | {lon: .geometry.coordinates[0], '
                  'lat: .geometry.coordinates[1], d: .geometry.coordinates[2]}] | .[0:2]')[0])

# ── Q11. Find every path whose value matches something — here, a URL. ────────
# THE QUESTION JQ IS BUILT FOR. No column list, no schema, no naming anything.
urls = q('[paths(type=="string" and startswith("http")) '
         '| map(if type=="number" then "[]" else . end) | join(".")] | group_by(.) '
         '| map({key: .[0], value: length}) | from_entries')[0]
print(f"\nQ11 path shapes whose value is a URL: {urls}")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat = q('[.features[] | .properties + {id, lon: .geometry.coordinates[0], '
         'lat: .geometry.coordinates[1], depth_km: .geometry.coordinates[2]}] | .[0] | keys | length')[0]
print(f"\nQ12 {flat} scalar columns, with coordinates split out by hand.")
print("    Nothing is lost — but the expression NAMES the three coordinates,")
print("    so it is a table I designed rather than one the tool derived.")

# ── The packed strings, because defect 26 came from this file. ───────────────
print("\nDEFECT 26  does jq notice a list packed into a string?")
print("   ", q('.features[0].properties.types')[0])
print("    Reported as a string, correctly. jq can split it in one step once a")
print("    human has noticed:")
print("   ", q('.features[0].properties.types | split(",") | map(select(. != ""))')[0])
