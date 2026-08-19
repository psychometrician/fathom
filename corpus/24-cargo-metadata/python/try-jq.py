"""jq (the Python binding) — cargo metadata for this repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, the Python binding (version printed at run time)
  file          ../source.json   27 KB, 8 packages, depth 8
  measured      2026-08-11
  run           cd corpus/24-cargo-metadata/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   PARTLY
   1 what is in here                             4   NO                  yes — 143
   2 how deep                                    1   NO                  yes — 8
   3 what is one record                          8   NO                  PARTLY
   4 always present vs sometimes                 8   NO                  YES — four always-null
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                   18   NO                  ALL THE INGREDIENTS
   7 how many records                             3  NO                  yes
   8 three named fields to a table                2 YES                 yes
   9 a field missing from some rows                2 YES                 yes
  10 flatten the deepest array                     3 YES                 yes
  11 find every path matching something            4 NO                  yes — 5
  12 flattest honest table                         3 NO                  PARTLY
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 6, 11
  14 survives the next file unchanged?               yes except Q8/Q9/Q10
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~110

  ══════════════════════════════════════════════════════════════════════════════
  THE ONLY LOCALLY-GENERATED DOCUMENT IN THE CORPUS, AND ITS KEYS-AS-DATA SITE
  IS ALSO ITS HYPHEN PROBLEM. THEY ARE THE SAME KEYS.
  ══════════════════════════════════════════════════════════════════════════════

  `cargo metadata` on this repository. The probe calls `$.packages[].features`
  KEYS THAT ARE DATA — 5 keys over 6 copies — and the entry's own cold-run note
  records that as the one thing the probe read correctly where the prediction
  had guessed otherwise.

  The feature names are `zlib-ng-compat`, `rustc-dep-of-std`, `simd-adler32`,
  `document-features`. TWENTY OF THE DOCUMENT'S KEY NAMES CONTAIN A HYPHEN AND
  MOST OF THEM ARE FEATURE NAMES — so on this document the escaping hazard that
  cost DuckDB and R a query on entries 21 and 23 is not a schema problem at all.
  IT IS A DATA PROBLEM WEARING A SCHEMA'S CLOTHES, and that is question 6 stated
  from the other end.

  TWO PACKAGES HAVE ZERO FEATURES — this repository's own two crates — so the
  site is 6 non-empty copies out of 8, which is why the probe's ratio is 0.24.
"""
import json
import time
from collections import Counter
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
print(f"\nQ1  {paths[0]} distinct paths, {t:.3f}s — the probe says 143")
print(f"Q2  depth {depth[0]} — the probe says 8, in a 27 KB file. THE DEEPEST")
print("    STRUCTURE PER BYTE IN THE CORPUS.")
roots, _ = q("keys_unsorted")
print(f"Q1  the root is an OBJECT of {len(roots[0])} keys: {roots[0]}")

# ── Q3. ─────────────────────────────────────────────────────────────────────
print("\nQ3  the probe prices NINE candidates. jq counts any you name:")
for name, prog in [("an item of packages", ".packages | length"),
                   ("an item of targets", "[.packages[].targets[]] | length"),
                   ("an item of dependencies", "[.packages[].dependencies[]] | length"),
                   ("an entry of features", "[.packages[].features | keys[]] | length"),
                   ("an item of nodes", ".resolve.nodes | length")]:
    n, _ = q(prog)
    print(f"    {name:26} {n[0]:>3} rows")
print("    the probe prices `an item of packages` at 8 x 57, 63% EMPTY — the")
print("    widest-per-row table in the corpus relative to its record count.")

# ── Q6. THE CENTREPIECE. ────────────────────────────────────────────────────
feat, _ = q('[.packages[] | {name, features: (.features | keys)}]')
allf, _ = q('[.packages[].features | keys[]] | group_by(.) | map({k: .[0], n: length}) '
            '| sort_by(-.n)')
once = [r["k"] for r in allf[0] if r["n"] == 1]
print(f"\nQ6  $.packages[].features — THE PROBE CALLS THESE KEYS DATA.")
for p in feat[0]:
    print(f"    {p['name']:16} {len(p['features']):>2} features")
print(f"Q6  {len(allf[0])} distinct feature names over {len(feat[0])} packages;"
      f" {len(once)} appear ONCE")
print("    An open vocabulary: most names occur in exactly one package, which is")
print("    what `classify()` is looking at. jq supplies every ingredient —")
print("    `keys`, the counts, the distribution — and states no verdict.")
hy = [k for k in [r["k"] for r in allf[0]] if "-" in k]
print(f"\nQ6  AND {len(hy)} OF THE {len(allf[0])} FEATURE NAMES CONTAIN A HYPHEN:")
print(f"    {hy[:6]} …")
allkeys, _ = q('[paths | .[] | select(type == "string")] | unique '
               '| map(select(test("-"))) | length')
print(f"    of {allkeys[0]} hyphenated key names in the whole document, most are")
print("    these. SO THE ESCAPING HAZARD AND THE KEYS-AS-DATA SITE ARE THE SAME")
print("    KEYS. On entries 21 and 23 a hyphen cost DuckDB and R a query and")
print("    the names were genuine FIELDS; here they are VALUES that a frame will")
print("    turn into column names it then cannot quote. Question 6 from the")
print("    other end.")

# ── Q4/Q5/Q7. ───────────────────────────────────────────────────────────────
some, _ = q('[.packages[] | keys[]] | group_by(.) | map(select(length < 8)) | length')
nulls, _ = q('[.packages[] | to_entries[] | select(.value == null) | .key] '
             '| group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)')
alln = [r["k"] for r in nulls[0] if r["n"] == 8]
print(f"\nQ4  package fields sometimes ABSENT: {some[0]} — every package has all 24")
print(f"Q4  written NULL: {len(nulls[0])} fields; NULL ON ALL 8: {alln}")
print("    FOUR FIELDS THE TOOL ALWAYS EMITS AND NEVER FILLS. A field that is")
print("    never anything but null has ONE type — the distinction entries 20,")
print("    22 and 23 pinned, and this document has four of them.")
CENSUS = """
def ptype: if type == "array" then (if length == 0 then "array" else "array[1] " + (.[0]|type) end)
           else type end;
def novaries: .;
def varies: . as $ts
          | if (any(.[]; startswith("array["))) then map(select(. != "array")) else $ts end;
. as $d | [ paths as $p | {k: ($p | map(if type=="number" then "[]" else . end) | join(".")),
                           t: ($d | getpath($p) | ptype)} ]
| group_by(.k) | map({k: .[0].k, t: (map(.t) | unique | map(select(. != "null")) | ARRAYRULE)})
| map(select(.t | length > 1)) | map(.k)
"""
loose, _ = q(CENSUS.replace("ARRAYRULE", "novaries"))
tight, _ = q(CENSUS.replace("ARRAYRULE", "varies"))
print(f"\nQ5  a null is not a type, empty arrays still counted: {len(loose[0])} paths")
for pth in loose[0]:
    print(f"      {pth}")
print(f"Q5  + AN EMPTY ARRAY IS NOT A TYPE:                    {len(tight[0])} paths")
print("    ZERO, and the probe says NONE. The six above are all `array` beside")
print("    `array[1] something` — an optional list that is sometimes empty, which")
print("    `varies()` discards and which every optional list in every document")
print("    would otherwise report. ENTRY 20's LADDER ON A DOCUMENT WITH NOTHING")
print("    ELSE TO FIND: the rule does all of the work here, and leaving it out")
print("    turns a clean document into six false positives.")
c, _ = q('{packages: (.packages | length), workspace_members: (.workspace_members | length), '
         'resolve_nodes: (.resolve.nodes | length)}')
print(f"\nQ7  {c[0]}")
print("    `packages` and `resolve.nodes` BOTH say 8 and mean the same eight;")
print("    `workspace_members` says 2, and those two are THIS repository's own")
print("    crates — the other six are dependencies. So the three numbers are not")
print("    three answers to one question but answers to two: how many packages")
print("    are in the graph, and how many are MINE. FIRST DOCUMENT IN THE CORPUS")
print("    WHERE QUESTION 7's SEVERAL COUNTS ARE ALL CORRECT AND NONE IS A TRAP.")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8, _ = q('[.packages[] | {name, version, edition}] | length')
print(f"\nQ8  {t8[0]} rows x 3, one expression")
t9, _ = q('[.packages[] | {name, description: (.description // null)}] '
          '| map(select(.description != null)) | length')
print(f"\nQ9  `description` non-null on {t9[0]} of 8; `//` keeps every row")
t10, _ = q('[.packages[] as $p | $p.targets[] | {pkg: $p.name, name, kind: (.kind|join(","))}] '
           '| length')
print(f"\nQ10 targets[] -> {t10[0]} rows x 3, parent kept")
deep, _ = q('[.resolve.nodes[] as $n | $n.deps[] | .dep_kinds[] '
            '| {node: $n.id, kind, target}] | length')
print(f"Q10 the DEEPEST array is resolve.nodes[].deps[].dep_kinds[]: {deep[0]} rows")
print("    at depth 6, and jq reaches it with three `[]` and no level names.")
u, _ = q('[paths(type=="string" and test("^https?://")) '
         '| map(if type=="number" then "[]" else . end) | join(".")] | unique')
print(f"\nQ11 {len(u[0])} distinct URL paths: {u[0]}")
print("\nQ12 jq has no `to_table`. The honest table is question 3's, and this")
print("    document's widest candidate is 63% empty because `features` spreads")
print("    into a column per feature name — which is question 6 paid for in")
print("    width.")
