"""jq (the Python binding) — crates.io summary

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, the Python binding (version printed at run time)
  file          ../source.json   41 KB, six collections at the root, depth 4
  measured      2026-08-11
  run           cd corpus/23-cratesio-summary/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   PARTLY
   1 what is in here                             4   NO                  yes — 140
   2 how deep                                    1   NO                  yes — 4
   3 what is one record                          16  NO                  PARTLY — and see below
   4 always present vs sometimes                 8   NO                  YES — three always-null
   5 does any field change type                  6   NO                  yes — NONE
   6 are any object keys data                    2   -                   n/a
   7 how many records                            10  NO                  THREE answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          6   NO                  yes — 11
  12 flattest honest table                       4   NO                  PARTLY
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
  14 survives the next file unchanged?               yes except Q8/Q9/Q10
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~120

  ══════════════════════════════════════════════════════════════════════════════
  THIS IS THE DEFECT-25 DOCUMENT, AND THE QUESTION IS WHETHER ANY TOOL NOTICES
  THAT FOUR OF THE SIX COLLECTIONS ARE ONE SHAPE.
  ══════════════════════════════════════════════════════════════════════════════

  `new_crates`, `most_downloaded`, `most_recently_downloaded` and `just_updated`
  each hold ten crate records with the SAME 23 fields and the same 6-field
  `links`. The probe used to print all four lists in full — 32 of 49 lines — and
  since `d595d1d2…` prints `same shape as $.new_crates[]` instead.

  jq can COMPUTE the identity in one expression and says nothing unasked. That
  is this corpus's usual sentence; what makes this document worth its place is
  the SECOND thing, which no tool reports and the probe does not either:

  THE FOUR LISTS OVERLAP. 40 crate rows, 33 DISTINCT crates — seven crates
  appear in more than one collection. Concatenating the four gives 40 rows with
  seven duplicates, and nothing in any of the thirteen tools warns.
"""
import json
import time
from importlib.metadata import version

import jq

print(f"jq (python binding) {version('jq')}")

RAW = "../source.json"
doc = json.load(open(RAW))
CRATE = ["new_crates", "most_downloaded", "most_recently_downloaded", "just_updated"]


def q(prog):
    t = time.time()
    return jq.compile(prog).input(doc).all(), time.time() - t


print("\nQ0  parsed. jq says 'valid JSON' and nothing else. PARTLY.")

paths, t = q('[paths | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
depth, _ = q('[paths | length] | max')
print(f"\nQ1  {paths[0]} distinct paths, {t:.2f}s — the probe says 140")
print(f"Q2  depth {depth[0]} — the probe says 4")
roots, _ = q('keys_unsorted')
print(f"Q1  the root is an OBJECT of {len(roots[0])} keys: {roots[0]}")
print("    SIX COLLECTIONS AND TWO SCALARS. There is no single record array,")
print("    which is why the probe's first row candidate is `the whole document`.")

# ── Q3. THE FOUR-IN-ONE, computed. ──────────────────────────────────────────
print("\nQ3  the probe prices SEVEN candidates. jq counts any you name:")
for k in CRATE + ["popular_keywords", "popular_categories"]:
    n, _ = q(f'.{k} | length')
    print(f"    an item of {k:26} {n[0]:>3} rows")
same, _ = q(f'[{", ".join("(." + k + "[0] | keys | sort)" for k in CRATE)}] | unique | length')
print(f"\nQ3  DO THE FOUR SHARE A SHAPE? distinct key-sets across the four: {same[0]}")
allsame, _ = q('[.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
               '.just_updated[] | keys | sort] | unique | length')
print(f"Q3  over all 40 records, distinct key-sets: {allsame[0]}")
print("    ONE. jq PROVES the four collections are one shape in a single")
print("    expression — and it took me writing `unique | length` on purpose.")
print("    The probe prints `same shape as $.new_crates[]` unasked, which is")
print("    defect 25's repair. NO OTHER TOOL IN THIS DIRECTORY VOLUNTEERS IT.")

# ── THE OVERLAP, which nothing reports. ─────────────────────────────────────
tot, _ = q('[.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
           '.just_updated[]] | length')
dist, _ = q('[.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
            '.just_updated[] | .id] | unique | length')
dup, _ = q('[.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
           '.just_updated[] | .name] | group_by(.) | map(select(length > 1)) '
           '| map({name: .[0], n: length})')
print(f"\n     THE OVERLAP: {tot[0]} crate rows, {dist[0]} DISTINCT crates.")
print(f"     {dup[0]}")
print("     SEVEN CRATES APPEAR IN MORE THAN ONE COLLECTION. Concatenating the")
print("     four — which is the obvious thing to do once you know they share a")
print("     shape — gives 40 rows with seven duplicates. THE PROBE DOES NOT")
print("     REPORT THIS EITHER: it prices each list at 10 rows and says the")
print("     shapes are identical, which is true and is not the same as saying")
print("     the CONTENTS overlap.")

# ── Q4. ─────────────────────────────────────────────────────────────────────
some, _ = q('[.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
            '.just_updated[] | keys[]] | group_by(.) | map(select(length < 40)) | length')
nulls, _ = q('[.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
             '.just_updated[] | to_entries[] | select(.value == null) | .key] '
             '| group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)')
print(f"\nQ4  crate fields sometimes ABSENT: {some[0]} — every crate has all 23 keys")
print(f"Q4  crate fields written NULL: {nulls[0]}")
always = [r["k"] for r in nulls[0] if r["n"] == tot[0]]
print(f"    THREE ARE NULL ON ALL 40: {always}. A field that is never anything")
print("    but null has ONE type, not two — which is the distinction entry 20")
print("    found tidyjson turning on, and this document has three of them.")

# ── Q5/Q6/Q7. ───────────────────────────────────────────────────────────────
vary, _ = q('''
def ptype: if type == "array" then (if length == 0 then "array" else "array[1] " + (.[0]|type) end)
           else type end;
. as $d | [ paths as $p | {k: ($p | map(if type=="number" then "[]" else . end) | join(".")),
                           t: ($d | getpath($p) | ptype)} ]
| group_by(.k) | map({k: .[0].k, t: (map(.t) | unique | map(select(. != "null")))})
| map(select(.t | length > 1)) | length''')
print(f"\nQ5  paths with more than one non-null shape: {vary[0]} — the probe says NONE")
print("\nQ6  no keyed collections; every level names its fields. The probe agrees.")
counts, _ = q('{num_crates, num_downloads, rows_in_four_lists: '
              '([.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
              '.just_updated[]] | length)}')
print(f"\nQ7  {counts[0]}")
print("    THREE ANSWERS AND THEY MEASURE THREE DIFFERENT THINGS: `num_crates`")
print("    is the registry's total, `num_downloads` is not a record count at")
print("    all, and 40 is the rows here — of which 33 are distinct.")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8, _ = q('[.new_crates[] | {name, max_version, downloads}] | length')
print(f"\nQ8  {t8[0]} rows x 3, one expression")
t9, _ = q('[.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
          '.just_updated[] | {name, homepage: (.homepage // null)}] '
          '| map(select(.homepage != null)) | length')
print(f"\nQ9  `homepage` non-null on {t9[0]} of {tot[0]}; `//` keeps every row")
t10, _ = q('[.new_crates[], .most_downloaded[], .most_recently_downloaded[], '
           '.just_updated[] | . as $c | .links | to_entries[] '
           '| {crate: $c.name, link: .key, url: .value}] | length')
print(f"\nQ10 links flattened to {t10[0]} rows x 3 — the deepest structure here")
print("    is `links`, an OBJECT of 6 fields, not an array. Question 10 asks for")
print("    the deepest ARRAY and this document has none below the collections.")
u, t = q('[paths(type=="string" and test("^https?://")) '
         '| map(if type=="number" then "[]" else . end) | join(".")] | unique')
print(f"\nQ11 {len(u[0])} distinct URL paths, {t:.2f}s")
for p in u[0][:6]:
    print(f"      {p}")
import re as _re
fold = sorted({_re.sub(r"^(new_crates|most_downloaded|most_recently_downloaded|just_updated)\.",
                       "<one of the four>.", p) for p in u[0]})
print(f"    AND FOLDING THE FOUR IDENTICAL COLLECTIONS TAKES {len(u[0])} -> {len(fold)}:")
for p in fold:
    print(f"      {p}")
print("    The four-in-one shape inflates the URL path count four times over,")
print("    exactly as it inflated the record-shape listing before defect 25's")
print("    repair. The probe folds the SHAPES and does not fold the PATHS.")
print("\nQ12 jq has no `to_table`. The honest table on THIS document is the one")
print("    question 3 asks about: four lists of one shape, concatenable into 40")
print("    rows — of which seven are the same crate twice.")
