"""jq (the Python binding) — Homebrew's whole formula index

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, the Python binding (version printed at run time)
  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
  measured      2026-08-11
  run           cd corpus/20-homebrew-formulae/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   PARTLY
   1 what is in here                             4   NO                  yes
   2 how deep                                    2   NO                  yes
   3 what is one record                          6   NO                  PARTLY
   4 always present vs sometimes                 5   NO                  YES
   5 does any field change type                 30   NO                  YES, on the 4th try
   6 are any object keys data                    6   NO                  by hand
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something         20   NO                  yes, three answers
  12 flattest honest table                       3   NO                  PARTLY
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 11
  14 survives the next file unchanged?               yes except Q8/Q9/Q10
  15 readable a week later?                          the survey lines, no
  16 lines, and how much is ceremony?                ~150, almost none ceremony
  timing        Q1 15.8s, Q5 24s per rung, Q11 4-6s. ~130s of CPU for the file

  TWO RESULTS, AND BOTH ARE ABOUT THE QUESTION RATHER THAN THE TOOL.

  Q5 IS A LADDER AND THE FIRST RUNG RETURNS ZERO. The obvious query — root
  fields, JSON `type`, nulls removed — finds NO type variation on a document
  where the probe finds nine sites. Every one is below the root or inside an
  array. Four attempts, printed: 0, then 193, then 140, then 31, then 12 after
  folding keys-as-data by hand, against the probe's 9. Each step down is a RULE
  the probe encodes — a null is not a type, an empty array is not a type,
  keys-as-data fold — and jq can express all three and suggests none of them.

  Q11 HAS THREE ANSWERS: 65, 48 or 9 distinct URL paths. 65 -> 48 because
  fifteen formulae are literally NAMED `http*` — httpd, httpie, http-server —
  so a `startswith("http")` scan reports package-name paths as URL paths.
  48 -> 9 because `bottle.stable.files.<platform>.url` is sixteen spellings of
  one path. THE PREDICATE AND THE FOLDING DECIDE THE ANSWER, NOT THE TOOL, and
  this lands identically in all thirteen attempts.

  jq answers 4 correctly because it walks keys. It is the only tool in this
  directory that gets question 6's ingredients by construction — `keys` on a
  folded path is one expression — and it still DECIDES nothing: it counts the
  16 platform keys and never says whether they are data.
"""
import json
import time
from importlib.metadata import version

import jq

print(f"jq (python binding) {version('jq')}")

RAW = "../source.json"
src = open(RAW).read()
doc = json.loads(src)


def q(prog, data=None):
    t = time.time()
    out = jq.compile(prog).input(data if data is not None else doc).all()
    return out, time.time() - t


# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
# jq parses or it does not. It has no duplicate-key report and no big-int report:
# jq 1.7 keeps the LAST duplicate silently, and numbers become IEEE doubles.
print("\nQ0  parsed:", type(doc).__name__, "of", len(doc))
print("    jq answers 'valid JSON' and nothing else. Duplicate keys: last wins,")
print("    silently. Ints past 2^53: become doubles, silently. Answered PARTLY.")

# ── Q1. What is in here — every path, at every level. ────────────────────────
paths, t = q('[paths | map(if type=="number" then "[]" else . end) | join(".")] '
             '| unique | length')
print(f"\nQ1  {paths[0]:,} distinct paths (array indices folded to []), {t:.1f}s")
top, _ = q('[.[] | keys_unsorted[]] | unique | length')
print(f"Q1  {top[0]} distinct field names on the root record")

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
depth, t = q('[paths | length] | max')
print(f"\nQ2  depth {depth[0]}, {t:.1f}s — agrees with the probe")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  jq names no candidates. It will count any one you name:")
for name, prog in [("a record", '. | length'),
                   ("an item of patches", '[.[].patches[]?] | length'),
                   ("an item of resolves", '[.[].patches[]?.resolves[]?] | length'),
                   ("an item of post_install_steps", '[.[].post_install_steps[]?] | length'),
                   ("a bottle file", '[.[].bottle.stable.files? | select(.) | keys[]] | length')]:
    n, _ = q(prog)
    print(f"    {name:32} {n[0]:>7,} rows")
print("    PARTLY: the counts are right and the COST is not computed. jq has no")
print("    way to say '85% empty' without being told the column set first.")
print(f"Q7  {len(doc):,} formulae under 'a record'")

# ── Q4. Always present vs sometimes — and null vs absent. ────────────────────
sometimes, t = q('[.[] | keys_unsorted[]] | group_by(.) | map({k: .[0], n: length}) '
                 '| map(select(.n < 8536)) | sort_by(-.n)')
print(f"\nQ4  sometimes-ABSENT fields: {sometimes[0]}")
nulls, _ = q('[.[] | to_entries[] | select(.value == null) | .key] | group_by(.) '
             '| map({k: .[0], n: length}) | sort_by(-.n) | length')
print(f"Q4  always-present-but-NULL fields: {nulls[0]}")
print("    THE DISCRIMINATOR. jq separates them because `keys` is presence and")
print("    `.value == null` is value. Every frame in this directory reports the")
print("    union of the two as one 'sometimes' set.")

# ── Q5. Does any field change type between records? ──────────────────────────
# THE LADDER. The obvious query returns NOTHING, and each rung below is one rule
# the probe encodes and jq does not. Four attempts, which is what rule 6 allows:
# `design/probe.py` was revised many times against many files.
root, t = q('[.[] | to_entries[] | {k: .key, t: (.value | type)}] '
            '| group_by(.k) | map({k: .[0].k, t: (map(.t) | unique)}) '
            '| map(select((.t - ["null"]) | length > 1)) | map(.k)')
print(f"\nQ5  attempt 1 — root fields, JSON `type`: {root[0]} ({len(root[0])}), {t:.1f}s")
print("    ZERO, on a document with nine type-changing sites. Every one of them")
print("    is below the root or inside an array, and `type` on the field says")
print("    'array' every time. A confident, plausible, wrong nothing.")

CENSUS = '''
def ptype: if type == "array"
           then (if length == 0 then "array" else "array[1] " + (.[0] | type) end)
           else type end;
def novaries: .;
def varies: . as $ts
          | if (any(.[]; startswith("array["))) then map(select(. != "array")) else $ts end;
. as $doc
| [ paths as $p | { k: ($p | map(if type == "number" then "[]" else . end) | join(".")),
                    t: ($doc | getpath($p) | ptype) } ]
| group_by(.k)
| map({ k: .[0].k, t: (map(.t) | unique | NULLRULE | ARRAYRULE) })
| map(select(.t | length > 1)) | map(.k)
'''
rungs = [("2  every path, null counts as a type ", "novaries", "novaries"),
         ("3  + a null is not a type           ", 'map(select(. != "null"))', "novaries"),
         ("4  + an empty array is not a type   ", 'map(select(. != "null"))', "varies")]
last = None
for label, nullrule, arrayrule in rungs:
    prog = CENSUS.replace("NULLRULE", nullrule).replace("ARRAYRULE", arrayrule)
    out, t = q(prog)
    last = out[0]
    print(f"Q5  attempt {label}: {len(last):>3} paths, {t:.1f}s")

import re
folded = sorted({re.sub(r"\.uses_from_macos\.\[\]\.[a-z0-9_]+$", ".uses_from_macos.[].<key>",
                        re.sub(r"\.variations\.[a-z0-9_]+\.", ".variations.<key>.", p))
                 for p in last})
print(f"Q5  + keys-as-data folded by hand      : {len(folded):>3} paths")
for p in folded:
    print(f"      {p}")
print("    THE PROBE SAYS NINE. These twelve are those nine plus the three")
print("    `.[]` array-element paths the probe folds into their parent.")
print("    193 -> 140 -> 31 -> 12 -> 9, and every step is a RULE, not a query:")
print("    a null is not a type, an empty array is not a type, keys-as-data fold.")
print("    jq can express all three. Nothing in jq suggests you need them.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  jq can COUNT a keyed collection in one line. It never CALLS one.")
for path, prog in [("$[].bottle.stable.files", '[.[].bottle.stable.files? | select(.) | keys[]]'),
                   ("$[].variations", '[.[].variations? | select(.) | keys[]]'),
                   ("$[].service.environment_variables",
                    '[.[].service? | select(.) | .environment_variables? | select(.) | keys[]]')]:
    ks, _ = q(prog + ' | unique | length')
    n, _ = q(prog + ' | length')
    print(f"    {path:36} {ks[0]:>3} distinct keys over {n[0]:>6,} occurrences")
print("    The probe DECLINES the first two as vocabularies and calls four other")
print("    sites data. jq supplies every ingredient of that judgement and makes none.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl, _ = q('[.[] | {name, desc, homepage}] | length')
print(f"\nQ8  {tbl[0]:,} rows x 3 cols, one expression")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
kept, _ = q('[.[] | {name, executables: (.executables // null)}] '
            '| map(select(.executables != null)) | length')
print(f"\nQ9  executables non-null on {kept[0]:,} of {len(doc):,}; `//` keeps every row")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
res, t = q('[.[] as $f | $f.patches[]? | .resolves[]? | {name: $f.name, id, type}] | length')
print(f"\nQ10 patches[].resolves[] flattened to {res[0]:,} rows x 3 cols, {t:.1f}s")
deep, _ = q('[.[] | .variations[]? | .head_dependencies? | select(.) '
            '| .uses_from_macos[]? | select(type == "object") | keys[]] | length')
print(f"Q10 the DEEPEST array is variations.<key>.head_dependencies.uses_from_macos[]:")
print(f"    {deep[0]} object entries at depth 8. jq reaches it with `[]` and no level names.")

# ── Q11. Find every path whose value matches something. ──────────────────────
naive, t = q('[paths(type == "string" and startswith("http")) '
             '| map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
strict, t2 = q('[paths(type == "string" and test("^https?://")) '
               '| map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
named, _ = q('[.[] | .name | select(startswith("http"))] | length')
print(f"\nQ11 startswith(\"http\"): {naive[0]} distinct paths, {t:.1f}s")
print(f"Q11 test(\"^https?://\"):  {strict[0]} distinct paths, {t2:.1f}s")
print(f"    The {naive[0] - strict[0]} paths that drop are package-NAME paths — name, full_name,")
print(f"    dependencies[], executables[], oldnames[] — because {named[0]} formulae are")
print("    literally named http*: httpd, httpie, http-server, httpx. A prefix")
print("    test reports them as URLs. THAT IS A PROPERTY OF THE PREDICATE, NOT")
print("    THE TOOL, and it lands identically in all thirteen attempts.")
folded_urls, _ = q('[paths(type == "string" and test("^https?://")) '
                   '| map(if type=="number" then "[]" else . end) | join(".")] | unique')
import re as _re
fu = sorted({_re.sub(r"\.files\.[a-z0-9_]+\.", ".files.<key>.",
                     _re.sub(r"\.variations\.[a-z0-9_]+\.", ".variations.<key>.", p))
             for p in folded_urls[0]})
print(f"Q11 and folding keys-as-data takes {strict[0]} -> {len(fu)}:")
for p in fu:
    print(f"      {p}")
print("    Question 11 has THREE answers on this document — 65, 48, 9 — and the")
print("    tool gives you whichever predicate and folding you happened to pick.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 jq has no `to_table`. `[.[] | to_entries]` is honest and is not flat;")
print("    `flatten` works on arrays only. Building the 447-column frame means")
print("    naming the columns, which is question 3's cost with extra steps. PARTLY.")
