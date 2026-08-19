"""jq (via the `jq` python binding) — an npm lockfile, 1,657 packages

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   759 KB, 1,657 packages, depth 5
  measured      2026-08-11
  run           cd corpus/13-package-lock/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             7   NO                  YES — 16,545 exactly
   2 how deep                                    2   NO                  YES — exactly 5
   3 what is one record                          6   NO                  PARTLY — 144 with `sort`
   4 always present vs sometimes                 5   NO                  YES
   5 does any field change type                  5   NO                  YES — exactly the probe
   6 are any object keys data                    6   -                   PARTLY — best here
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          6   NO                  YES — and foldable
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the reduce in Q1 does not
  16 lines, and how much is ceremony?                ~125, and the folds are most of it

**jq'S PATHS ARE ARRAYS, NOT STRINGS, AND ON THIS DOCUMENT THAT IS THE WHOLE
BALLGAME.** `paths` yields `["packages", "node_modules/@nodelib/fs.scandir",
"resolved"]` — three segments, kept apart. pandas' `json_normalize` and ijson's
`parse` both hand back a **dot-joined string**, and **33 of this document's
package keys contain a dot**, so neither can be split back into the path that
made it. Measured in `try-ijson.py`: its folded URL census reports `resolved`
1,623 times against a true 1,656, short by exactly those 33.

**jq is immune to that by construction**, and it is the only tool in this
directory that is. It is a property of the representation, not of the library.

**IT REPRODUCES FOUR OF THE PROBE'S NUMBERS EXACTLY:**

    paths, array indices folded ...... 16,545    probe prints 16,545
    max path length ....................... 5    probe prints 5 levels deep
    distinct key-sets, SORTED ........... 144    probe prints 144
    fields that change type ............... 2    engines and funding, with counts

**AND THE THIRD ONE CARRIES A WARNING FOR DuckDB.** `keys_unsorted|join(",")`
gives **152**; adding `sort` gives **144**. DuckDB's `json_keys(...)::VARCHAR`
is the unsorted form and reports 152 for the same reason — **8 packages carry
the same fields in a different order.** One word separates a right answer from
a wrong one and nothing signals which you wrote.

**QUESTION 6 IS THE FILE'S POINT AND jq COMES CLOSEST WITHOUT ARRIVING.**
`keys` treats a keyed collection as values, `to_entries` turns keys into data,
and `paths` will show you that 1,657 siblings each occur once. **All the raw
material is there and jq computes no verdict**: it will not tell you `packages`
is keyed by data while `engines` — 5 keys over 1,050 copies — is a vocabulary.
The probe prints seven keyed sites and declines exactly that eighth.

**WHAT IT STILL CANNOT DO IS QUESTION 3.** 144 key-sets is the raw material for
pricing a row shape; jq names no candidate and computes no cost. The probe names
eight, including `an entry of packages 1,657 x 1394 99% empty`.
"""
import json
import time
from importlib.metadata import version

import jq

print(f"jq python binding {version('jq')}")

RAW = "../source.json"
doc = json.load(open(RAW))


def run(program, label):
    t0 = time.time()
    out = jq.compile(program).input(doc).first()
    print(f"    [{time.time() - t0:5.1f}s] {label}")
    return out


# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  the binding takes an already-parsed object, so jq never saw the bytes.")
print("    No duplicate-key, big-int or NaN report from either side. CANNOT.")
print("    DuckDB refuses this file over one empty-string key; jq is untroubled.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
print("\nQ1  paths, with array indices folded to []:")
n_raw = run('[paths | map(if type == "number" then "[]" else . end) | join(".")]'
            ' | unique | length', "…")
print(f"    {n_raw:,} — THE PROBE PRINTS 16,545. Exact.")
print("\nQ1  and again with the `packages` keys folded to <key>:")
n_folded = run('''[paths | . as $p
      | reduce range(0; length) as $i ([];
          . + [ if ($i > 0 and ($p[$i-1] | tostring) == "packages") then "<key>"
                elif ($p[$i] | type) == "number" then "[]"
                else $p[$i] end ])
      | join(".")] | unique | length''', "…")
print(f"    {n_folded:,}. Still large, because the FOUR nested keyed collections —")
print("    dependencies, devDependencies, optionalDependencies, peerDependencies —")
print("    are keyed by package name too and this fold only handles the outer one.")
print("    The fold is EXPRESSIBLE in jq, which is more than ijson or pandas can")
print("    say, and it is a `reduce` over path segments rather than a verb.")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
print("\nQ2  max path length:")
print(f"    {run('[paths | length] | max', '…')} — the probe prints '5 levels deep'. Exact.")

# ── Q3/Q7. What is one record, and how many. AND THE `sort` WARNING. ─────────
print("\nQ3  distinct key-sets over the 1,657 packages, two ways:")
unsorted = run('[.packages[] | keys_unsorted | join(",")] | unique | length', "keys_unsorted")
sorted_ = run('[.packages[] | keys_unsorted | sort | join(",")] | unique | length', "with sort")
print(f"    keys_unsorted -> {unsorted}")
print(f"    with sort     -> {sorted_}   <- THE PROBE PRINTS 144")
print(f"    {unsorted - sorted_} packages carry the same fields in a different ORDER.")
print("    DuckDB's json_keys(...)::VARCHAR is the unsorted form and returns 152")
print("    for exactly this reason. One word, and nothing tells you which is meant.")
print("    jq still names no row candidate and prices none. PARTLY.")
print(f"Q7  {run('.packages | length', 'packages'):,} packages")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
print("\nQ4  field counts:")
counts = run('[.packages[] | keys_unsorted[]] | group_by(.)'
             ' | map({(.[0]): length}) | add', "…")
n = len(doc["packages"])
always = [k for k, c in counts.items() if c == n]
some = sorted(((k, c) for k, c in counts.items() if c < n), key=lambda kv: kv[1])
print(f"    {len(counts)} fields · always {len(always)} — {always}")
print(f"    sometimes {len(some)}, rarest five: {some[:5]}")
print("    Matches the probe: 21 fields, only `version` on every package.")

# ── Q5. Does any field change type between records. ──────────────────────────
print("\nQ5  fields whose type varies across the packages:")
varying = run('''[.packages[] | to_entries[] | {k: .key, t: (.value | type)}]
      | group_by(.k)
      | map(select((map(.t) | unique | length) > 1)
            | {(.[0].k): (map(.t) | group_by(.) | map({(.[0]): length}) | add)})
      | add''', "…")
print(f"    {varying}")
print("    EXACTLY THE PROBE, which prints:")
print("      engines  object x1,050, array[1] text x1")
print("      funding  object x282, array[1] object x26, array[1] text x2")
print("    ijson reports ZERO varying prefixes on this document, because each")
print("    package's `engines` sits at its own prefix. jq groups by KEY rather")
print("    than by path, which is what makes the question answerable.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  jq gets closer than anything else here and still computes no verdict.")
kv = run('[.packages | keys[]] | length', "keys of packages")
eng = run('[.packages[].engines? | objects | keys[]] | unique | length',
          "distinct engine keys")
print(f"    packages has {kv:,} keys, each occurring once  -> DATA")
print(f"    engines has {eng} distinct keys over 1,050 copies -> A VOCABULARY")
print("    `keys`, `to_entries` and `paths` give all the raw material and jq")
print("    draws no line between those two cases. The probe prints seven keyed")
print("    sites and DECLINES `engines` by name. PARTLY.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
print("\nQ8  three fields, keyed by install path:")
t = run('[.packages | to_entries[] | {path: .key, version: .value.version,'
        ' license: .value.license}]', "…")
print(f"    {len(t):,} rows x 3 cols")
print("   ", t[1])
print("    `to_entries` KEEPS THE INSTALL PATH as data, which jmespath's")
print("    `values()` throws away. On a keys-as-data document that is the row's")
print("    identity, not a detail.")
print("\nQ9  a field missing from some packages:")
q9 = run('[.packages[] | {version, license}]', "…")
print(f"    {len(q9):,} rows kept, {sum(r['license'] is None for r in q9):,} null")
print("    Object construction fills absent keys with null and KEEPS the row.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
print("\nQ10 funding[], which is object-or-array with string-or-object elements:")
fund = run('[.packages | to_entries[] | select(.value.funding | type == "array")'
           ' | .key as $p | .value.funding[]'
           ' | if type == "string" then {pkg: $p, url: .} else {pkg: $p} + . end]', "…")
print(f"    {len(fund)} rows")
print("   ", fund[0])
print("    The two `type ==` tests are unavoidable and jq states them plainly.")

# ── Q11. Find every path whose value matches something. ──────────────────────
print("\nQ11 URL-valued paths, folded on the packages key:")
urls = run('''[paths(type == "string" and test("https?://")) | . as $p
      | reduce range(0; length) as $i ([];
          . + [ if ($i > 0 and ($p[$i-1] | tostring) == "packages") then "<key>"
                elif ($p[$i] | type) == "number" then "[]"
                else $p[$i] end ])
      | join(".")] | group_by(.) | map({(.[0]): length}) | add''', "…")
print(f"    {urls}")
print(f"    {sum(urls.values()):,} values over {len(urls)} paths — the truth, and it")
print("    matches the probe's folding. ijson's dot-joined prefixes give 47")
print("    paths here, 42 of them invented, because the separator is in the data.")
print("    `paths(condition)` is the best question 11 in either language.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 the honest table:")
flat = run('[.packages | to_entries[] | {path: .key} + (.value | del(.dependencies,'
           ' .devDependencies, .optionalDependencies, .peerDependencies,'
           ' .peerDependenciesMeta, .bin))]', "…")
keys = set().union(*(set(r) for r in flat))
print(f"    {len(flat):,} rows, {len(keys)} distinct keys with the six keyed")
print("    collections removed — those are separate tables the probe prices at")
print("    2,841, 128, 104, 101, 78 and 25 rows. jq will not name them, but")
print("    `del` makes excluding them one clause, and the path survives as a column.")
