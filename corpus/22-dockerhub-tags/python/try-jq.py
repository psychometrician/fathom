"""jq (the Python binding) — Docker Hub tags, 100 tags

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, the Python binding (version printed at run time)
  file          ../source.json   476 KB, 100 tags under $.results, depth 5
  measured      2026-08-11
  run           cd corpus/22-dockerhub-tags/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   PARTLY
   1 what is in here                             2   NO                  yes — 33
   2 how deep                                    1   NO                  yes — 5
   3 what is one record                           8  NO                  PARTLY — counts, no cost
   4 always present vs sometimes                 14  NO                  YES — three states
   5 does any field change type                  10  NO                  yes — NONE, correctly
   6 are any object keys data                    1   -                   n/a
   7 how many records                             8  NO                  yes, both numbers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   2   YES                 yes — 1,388, parent kept
  11 find every path matching something          4   NO                  yes — 1
  12 flattest honest table                       3   NO                  PARTLY
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
  14 survives the next file unchanged?               yes except Q8/Q9/Q10
  15 readable a week later?                          the Q5 census, no
  16 lines, and how much is ceremony?                ~110, almost none

  THIS DOCUMENT IS THE NESTED CONTROL. 33 paths, 5 levels, ONE key-set at every
  record shape, no keys-as-data, no type change, no split — the probe found
  nothing here and scored ten of ten. Entry 14 was the FLAT control and all
  thirteen tools agreed. This one is regular in the same way and adds a
  ONE-TO-MANY child: 100 tags holding 1,388 images.

  ITS ONE REAL FINDING IS ABOUT THE PROBE, NOT THE TOOLS. The images table has
  THREE states of empty, and the probe counts two:

      os_version   NULL          on 1,360 of 1,388
      variant      NULL          on 1,125
      features     EMPTY STRING  on 1,388
      os_features  EMPTY STRING  on 1,388

  The probe's `16% empty` is exactly the nulls, (1,360 + 1,125) / (1,388 x 11).
  The 2,776 empty strings count as FILLED. That is a defensible choice and it is
  a choice, and this is the first corpus document where it moves the headline:
  counting empty strings too would make it 34%.

  THIS DOCUMENT IS THE NESTED CONTROL. 33 paths, 5 levels, ONE key-set at
  every record shape, no keys-as-data, no type change, no split. Entry 14 was
  the FLAT control and all thirteen tools agreed there. This one is regular in
  the same way and has a ONE-TO-MANY child — 100 tags holding 1,388 images —
  so it asks whether agreement survives a second table.
"""
import json
import time
from importlib.metadata import version

import jq

print(f"jq (python binding) {version('jq')}")

RAW = "../source.json"
doc = json.load(open(RAW))


def q(prog):
    t = time.time()
    return jq.compile(prog).input(doc).all(), time.time() - t


print("\nQ0  parsed. jq says 'valid JSON' and nothing else. PARTLY.")

paths, t = q('[paths | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
depth, _ = q('[paths | length] | max')
print(f"\nQ1  {paths[0]} distinct paths, {t:.3f}s — the probe says 33")
print(f"    RULE-6 TIMING: ../r/try-jqr.R runs the identical expression and\n    prints its own time. Entry 14 measured jqr 2.8x faster, entry 20 2.5x\n    on a 29.6 MB file; this one is 476 KB.")
print(f"Q2  depth {depth[0]} — the probe says 5")

# ── Q3. TWO REAL CANDIDATES, and this is the cleanest such document here. ────
print("\nQ3  jq counts any candidate you name and prices none:")
for name, prog in [("the whole document", "1"),
                   ("an item of results", ".results | length"),
                   ("an item of images", "[.results[].images[]] | length")]:
    n, _ = q(prog)
    print(f"    {name:24} {n[0]:>6,} rows")
print("    THE PROBE PRICES BOTH: 100 x 16 at 0% empty, and 1,388 x 11 at 16%")
print("    empty with `size` repeated 4x. Two honest answers with different")
print("    costs, and jq supplies neither cost.")

# ── Q4 / THE THREE STATES OF EMPTY. ─────────────────────────────────────────
some, _ = q('[.results[] | keys[]] | group_by(.) | map(select(length < 100)) | length')
inull, _ = q('[.results[].images[] | to_entries[] | select(.value == null) | .key] '
             '| group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)')
iempty, _ = q('[.results[].images[] | to_entries[] | select(.value == "") | .key] '
              '| group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)')
print(f"\nQ4  tag fields sometimes absent: {some[0]}. Every tag has all 16 keys.")
print(f"Q4  image fields written NULL:         {inull[0]}")
print(f"Q4  image fields written EMPTY STRING: {iempty[0]}")
print("    THREE STATES, AND THE PROBE COUNTS ONLY TWO. Its `16% empty` on the")
print("    images table is (1,360 + 1,125) / (1,388 x 11) — the NULLS. The 2,776")
print("    EMPTY STRINGS in `features` and `os_features` are counted as FILLED.")
print("    That is defensible and it is a choice, and this document is the first")
print("    in the corpus where the choice changes the headline number: counting")
print(f"    empty strings too would take 16% to {(2485+2776)/(1388*11):.0%}.")

# ── Q5/Q6. ──────────────────────────────────────────────────────────────────
vary, _ = q('''
def ptype: if type == "array" then (if length == 0 then "array" else "array[1] " + (.[0]|type) end)
           else type end;
. as $d | [ paths as $p | {k: ($p | map(if type=="number" then "[]" else . end) | join(".")),
                           t: ($d | getpath($p) | ptype)} ]
| group_by(.k) | map({k: .[0].k, t: (map(.t) | unique | map(select(. != "null")))})
| map(select(.t | length > 1)) | map(.k)''')
print(f"\nQ5  paths with more than one non-null shape: {vary[0]}")
print("    The probe reports NONE. A perfectly typed document, which is what")
print("    makes it the control.")
print("\nQ6  no keyed collections; every level names its fields. The probe agrees.")

# ── Q7. ─────────────────────────────────────────────────────────────────────
c, _ = q('{count, in_array: (.results | length), next: (.next != null)}')
print(f"\nQ7  {c[0]}")
print(f"    `count` is the SERVER's total and `results` is this page — "
      f"{c[0]['count'] / c[0]['in_array']:.1f}x apart, and `next` is a real URL, so the")
print("    document says outright that it is a PAGE. Entry 21's total-results was")
print("    185,000x the array and entry 17's numFound was read as a row count.")
print("    THREE DOCUMENTS, ONE TRAP, AND THIS IS THE ONLY ONE THAT ALSO SHIPS")
print("    THE LINK TO THE REST — which no tool here notices either.")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8, _ = q('[.results[] | {name, full_size, last_updated}] | length')
print(f"\nQ8  {t8[0]} rows x 3, one expression")
t9, _ = q('[.results[].images[] | {digest, variant: (.variant // "<null>")}] '
          '| map(select(.variant != "<null>")) | length')
print(f"\nQ9  `variant` non-null on {t9[0]:,} of 1,388; `//` keeps every row")
t10, t = q('[.results[] as $t | $t.images[] | {tag: $t.name, architecture, os, size}] | length')
print(f"\nQ10 images[] flattened to {t10[0]:,} rows x 4, {t:.1f}s — parent kept")
u, _ = q('[paths(type=="string" and test("^https?://")) '
         '| map(if type=="number" then "[]" else . end) | join(".")] | unique')
print(f"\nQ11 {len(u[0])} URL path: {u[0]}")
print("    ONE, and it is the pagination `next` link — OUTSIDE the records.")
print("    Entry 17 recorded the same shape and entry 18 twice; a frame built")
print("    from `results` reports NONE OF ONE.")
print("\nQ12 jq has no `to_table`. The honest table is question 3's, and this")
print("    document is the one where that choice actually matters: 100 x 16 with")
print("    a list-column, or 1,388 x 11 with `size` repeated 4x.")
