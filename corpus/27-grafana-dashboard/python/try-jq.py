"""jq — Grafana "Node Exporter Full", dashboard 1860

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

 ── scoring ──────────────────────────────────────────────────────────────────
  tool          jq, the Python binding (versions printed at run time)
  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
  measured      2026-08-13
  run           cd corpus/27-grafana-dashboard/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             3   NO                  yes
   2 how deep                                    1   NO                  yes — 12
   3 what is one record                          7   -                   CANNOT
   4 always present vs sometimes                 4   NO                  yes
   5 does any field change type                  5   NO                  yes — none
   6 are any object keys data                    2   NO                  yes, inferred
   7 how many records                            5   NO                  YES — 132
   8 three named fields to a table               2  YES                  yes
   9 a field missing from some rows              1  YES                  yes — // null
  10 flatten the deepest array                   3   NO                  yes
  11 find every path matching something          3   NO                  yes
  12 flattest honest table                       2   NO                  YES, once corrected
  13 needed the shape in advance?                    NO — `..` needs no shape
  14 survives the next file unchanged?               YES
  15 readable a week later?                          the `..` line yes, Q12 no
  16 lines, and how much is ceremony?                ~75

**jq answers the central question correctly and in one expression.** `..` walks
every value at every depth, so `[.. | objects | select(has("gridPos"))] | length`
does not need to know that a row panel nests its own panels — it does not need
to know what a panel is.

**AND THIS DOCUMENT BROKE THE IDIOM THE CORPUS HAS BEEN USING FOR Q12.**
`paths(scalars)` silently drops every `false` and every `null` leaf: 700 of
11,063 here, 6.3%, and 26 of the 231 distinct paths with them. See Q12. The
first draft of this file used it and reported 10,363, which disagreed with a
plain Python walk — that disagreement is the only reason it was caught.
"""
import json
import sys
import time
from importlib.metadata import version

import jq

# The module exposes no `__version__`, so distribution metadata is the only
# honest source. Printed rather than typed, for the reason the template gives.
print(f"jq (python binding) {version('jq')} · python {sys.version.split()[0]}")

doc = json.load(open("../source.json"))
Q = lambda expr: jq.compile(expr).input(doc).first()
t0 = time.time()

# The corrected leaf-path expression. `select` tests its INPUT for truthiness,
# so `scalars` — which returns the value itself — fails on `false` and `null`.
# Comparing types instead makes the condition a boolean and the leaf survives.
LEAF = 'path(.. | select(type != "object" and type != "array"))'

# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  json.load parsed and said nothing; jq sees the finished value, so a")
print("    duplicate key has already been lost before any expression runs. CANNOT.")

# ── Q1/Q2/Q12. The melt, and it answers three questions. ──────────────────
leaves = Q(f"[{LEAF}] | length")
distinct = Q(f'[{LEAF} | map(if type == "number" then "[]" else . end) '
             f'| join(".")] | unique | length')
depth = Q(f"[{LEAF} | length] | max")
print(f"\nQ1  {leaves:,} leaves at {distinct} distinct paths, one expression, and")
print("    nothing known in advance. yes.")
print(f"\nQ2  {depth}. yes — one expression, no walk written, and it agrees with the")
print("    probe's 12 exactly.")

# ── Q12, AND THE DEFECT IN THE IDIOM. ─────────────────────────────────────
broken = Q("[paths(scalars)] | length")
broken_d = Q('[paths(scalars) | map(if type == "number" then "[]" else . end) '
             '| join(".")] | unique | length')
kinds = Q(f'[{LEAF} as $p | getpath($p) | type] | group_by(.) '
          f'| map({{(.[0]): length}}) | add')
print(f"\nQ12 {leaves:,} x 2. YES — one expression, nothing known in advance.")
print(f"    {kinds}")
print(f"\n    ⚠ BUT `paths(scalars)`, the idiom entry 28 used, returns {broken:,} —")
print(f"      {leaves - broken} rows short, and {distinct - broken_d} distinct paths short.")
print("      `select(f)` emits its input when f's OUTPUT is truthy, and `scalars`")
print("      returns the value, so a leaf that IS `false` fails its own filter.")
print("      Silently. It is the single most-recommended jq idiom for this job.")
print("    WHAT IS LOST, once corrected: array indices become `[]` so paths compare,")
print("    so the table says a target has an `expr` and not which target.")

# ── Q7. THE QUESTION. How many panels are in this dashboard? ──────────────
naive = Q(".panels | length")
allp = Q('[.. | objects | select(has("gridPos"))] | length')
print("\nQ7  THE CENTRAL QUESTION.")
print(f"      .panels | length                                 -> {naive}")
print(f'      [.. | objects | select(has("gridPos"))] | length  -> {allp}')
print(f"      the difference is {allp - naive} panels inside the 16 `row` panels.")
print("    YES, and `..` is why: it never asked what a panel is or how deep one")
print("    can sit. The naive answer is shorter, obvious, and wrong.")

# ── and the same question for targets, where the trick does NOT work. ─────
tgt_naive = Q("[.panels[].targets // [] | .[]] | length")
tgt_refid = Q('[.. | objects | select(has("refId"))] | length')
tgt_true = Q('[.. | objects | select(has("gridPos")) | .targets // [] | .[]] | length')
print(f"\n    targets, the same shape and a WARNING: {tgt_naive} at the top level,")
print(f'    but `select(has("refId"))` gives {tgt_refid} and the true count is {tgt_true}.')
print(f"    {tgt_refid - tgt_true} `templating.list[].query` objects also carry a `refId`.")
print("    The `gridPos` trick worked because that field happens to be exclusive to")
print("    panels; `refId` is not, and jq cannot tell you which case you are in.")

# ── Q3. What is one record. ───────────────────────────────────────────────
print("\nQ3  jq counts any reading you name and proposes none:")
for label, expr in [("one panel per row (all depths)",
                     '[.. | objects | select(has("gridPos"))] | length'),
                    ("one TOP-LEVEL panel per row", ".panels | length"),
                    ("one target per row",
                     '[.. | objects | select(has("gridPos")) | .targets // [] | .[]] | length'),
                    ("one template variable per row", ".templating.list | length"),
                    ("one leaf per row", f"[{LEAF}] | length")]:
    print(f"      {label:<32} {Q(expr):>7,}")
print("    CANNOT. Five defensible answers, all cheap to count once named, none")
print("    proposed and none priced — and the first two differ by a factor of four.")

# ── Q4. Always vs sometimes, over the 132 panels. ─────────────────────────
print("\nQ4  fields over all 132 panels:")
counts = Q('[.. | objects | select(has("gridPos"))] '
           "| [.[] | keys[]] | group_by(.) | map({k: .[0], n: length}) "
           "| sort_by(-.n)")
for r in counts:
    print(f"      {r['k']:<16} {r['n']:>4}  {'always' if r['n'] == allp else ''}")
print("    yes, once you have the population — which is Q7's answer, not jq's.")

# ── Q5. Type variation. ───────────────────────────────────────────────────
poly = Q('[.. | objects | select(has("gridPos"))] '
         "| [.[] | to_entries[] | {k: .key, t: (.value | type)}] "
         "| group_by(.k) | map({k: .[0].k, t: (map(.t) | unique)}) "
         "| map(select(.t | length > 1))")
print(f"\nQ5  panel fields whose type varies across the 132: {len(poly)}.")
print("    yes — and the answer is none. Every field that appears is the same kind")
print("    everywhere, which is not what a schema with 25 versions of sediment")
print("    predicts. `type` is a built-in; the grouping is four lines of ceremony.")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
widest = Q("[.. | objects | keys | length] | max")
print(f"\nQ6  none. The widest object has {widest} keys and they are field names.")
print("    yes, inferred — jq has no verb that judges this, so the reading is mine")
print("    and only the counting is jq's.")

# ── Q8/Q9. Three named fields; a field missing from some rows. ────────────
tbl = Q('[.. | objects | select(has("gridPos")) '
        "| {title, type, id, description: (.description // null)}]")
missing = sum(1 for r in tbl if r["description"] is None)
print(f"\nQ8  {len(tbl)} rows x 4, one expression, and it reaches both depths.")
print(f"      {json.dumps(tbl[0])[:86]}")
print(f"\nQ9  `description` is absent from {missing} of {len(tbl)} panels; `// null` keeps")
print("    every row. yes — the alternative operator, which is the same idea purrr")
print("    spells `.default` and the one `whichever` is proposed for.")

# ── Q10. Flatten the deepest array. ───────────────────────────────────────
deep = Q(f"[{LEAF}] | max_by(length)")
n_arr = Q("[.. | arrays] | length")
print(f"\nQ10 {n_arr:,} arrays in the document and `.. | arrays` reaches every one.")
print(f"    the deepest leaf: {'.'.join(str(x) for x in deep)}")
print("    yes, and note the path goes through `panels` twice — the document")
print("    itself is telling you about the nesting, if you are reading paths.")

# ── Q11. Find every path matching something. ──────────────────────────────
hits = Q(f'[{LEAF} as $p | getpath($p) | select(type == "string") '
         f'| select(test("\\\\$node|\\\\$job|\\\\$__rate_interval"))] | length')
print(f"\nQ11 {hits} leaves mention a Grafana template variable (`$node`, `$job`,")
print("    `$__rate_interval`). yes — melt-then-grep, and the `as $p | getpath($p)`")
print("    line is the one here I would not read back cleanly in a week.")

print(f"\n    ({time.time() - t0:.2f}s total)")

print("""
CONCLUSION. jq gets the central question right, in one expression, without being
told the shape: `[.. | objects | select(has("gridPos"))] | length` is 132, and it
would still be 132 if Grafana nested rows inside rows tomorrow. Q14 is a clean
YES for the same reason, and no other tool in this comparison needed fewer
characters to reach both depths.

Three things it does not do, and they are the entry's finding.

It does not tell you the question was there. `.panels | length` is shorter,
obvious, and returns 31; jq is equally happy to print either.

It does not tell you when the trick stops working. `gridPos` is exclusive to
panels, so counting by it is exactly right. `refId` is NOT exclusive to targets
— two template variables carry one — so the identical expression over-counts by
two, and nothing distinguishes the two cases at the point of writing.

And its own most-recommended melt idiom drops 6.3% of this document without a
word. `paths(scalars)` was right on entry 28 because a translation catalogue is
all strings; a dashboard is 857 booleans and 28 nulls, and 700 of them vanish.
""")
