"""jq (via the `jq` Python binding) — Jupyter notebook, Norvig Advent-2021, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
  measured      2026-08-10
  run           cd corpus/11-jupyter-notebook/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  yes
   2 how deep                                    3   NO                  yes
   3 what is one record                          5   NO                  PARTLY
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  4   NO                  yes
   6 are any object keys data                    4   NO                  PARTLY
   7 how many records                            2   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          5   NO                  yes
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 1-7, 11 — YES for 8+
  14 survives the next file unchanged?               the describe half does
  15 readable a week later?                          the short ones; not `paths`
  16 lines, and how much is ceremony?                ~40, jq is dense not ceremonial

jq answers more of the exploration half than any other Python tool here, and
VERDICT.md's note applies: the contribution is asking unprompted, not the
arithmetic. Every expression below had to be written by someone who decided to
ask. Nothing volunteers.
"""
import json
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq binding {version('jq')}")
doc = json.load(open("../source.json"))
q = lambda e: jq.compile(e).input(doc).all()

# ── 1. what is in here ───────────────────────────────────────────────────────
shapes = q('[paths(scalars)|map(if type=="number" then "[]" else . end)|join(".")]'
           '|group_by(.)|map({p:.[0],n:length})|sort_by(-.n)')[0]
print(f"\n1. {len(shapes)} distinct FOLDED path shapes "
      f"(array indices collapsed to []):")
for s in shapes[:9]:
    print(f"     {s['p']:46} {s['n']:>6,}")
print("   Folding the indices by hand is what keeps this a description. Without")
print("   the `map(if type==\"number\")` it is one path per scalar — the O(data)")
print("   failure, in the tool jq shares with rrapply and ijson.")

# ── 2. how deep ──────────────────────────────────────────────────────────────
print(f"\n2. deepest path: {q('[paths|length]|max')[0]} segments, which is the")
print("   true depth. One expression, no field named, and it is the same answer")
print("   design/probe.py prints. jq and polars are the only two tools in the")
print("   Python set that get Q2 from their own output.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. present-count per key across the 272 cells, unprompted:")
for row in q('[.cells[]|keys[]]|group_by(.)|map({k:.[0],n:length})|sort_by(-.n)')[0]:
    print(f"     {row['k']:18} {row['n']:>4} of 272")
print("   `keys` is presence, so this is the ONLY count in the Python set that")
print("   reads execution_count as 132 rather than 131 — the explicit null is")
print("   a present key. jq separates absent from null for free.")

# ── 5. does any field change type ────────────────────────────────────────────
# MEASURED, and it is the sharpest thing this file found about jq. The obvious
# expression uses `paths(scalars)` and reports NOTHING, because `paths(f)` is
# `paths|select(...|f)` and **`select(null)` is FALSE in jq** — so every null
# value is silently dropped from the path list. `paths(scalars)` counts 194
# execution_count paths where `paths` counts 195.
print("\n5. `paths(scalars)` finds 0 paths taking more than one type — and that")
print("   is WRONG. Measured:")
print(f"     paths(scalars) at execution_count: "
      f"{q('[paths(scalars)|select(.[-1]==\"execution_count\")]|length')[0]}")
print(f"     paths          at execution_count: "
      f"{q('[paths|select(.[-1]==\"execution_count\")]|length')[0]}")
print("   `paths(f)` is `paths|select(getpath|f)`, and **select(null) is false**,")
print("   so jq's standard path listing cannot see a null value at all. The one")
print("   difference is the one null. Asking without `scalars`:")
for row in q('[paths as $p|select((getpath($p)|type) as $t|$t!="object" and '
             '$t!="array")|{p:($p|map(if type=="number" then "[]" else . end)'
             '|join(".")),t:(getpath($p)|type)}]|group_by(.p)'
             '|map({p:.[0].p,t:(map(.t)|unique)})|map(select(.t|length>1))')[0]:
    print(f"     {row['p']:46} {row['t']}")
print("   It is ragged by null rather than a type change — the same reading")
print("   design/probe.py was repaired for — but jq had to be ASKED correctly")
print("   before it could be wrong about it. Q1's fold above uses the standard")
print("   `paths(scalars)` and is short by exactly that one null.")

# ── 6. are any object keys data ──────────────────────────────────────────────
MIME = ('[.cells[].outputs[]?.data?|select(.!=null)|keys[]]'
        '|group_by(.)|map({k:.[0],n:length})')
print(f"\n6. PARTLY. mime keys: {q(MIME)[0]}")
print("   jq lists them and cannot say they are data. `?` is doing real work")
print("   here — without it `.outputs[]` errors on the 140 markdown cells,")
print("   which is jq refusing rather than returning null.")

# ── 3, 7. what is one record, and how many ───────────────────────────────────
print(f"\n3. two defensible records, and jq prices neither:")
print(f"     a cell      {q('.cells|length')[0]} rows")
print(f"     an output   {q('[.cells[].outputs[]?]|length')[0]} rows")
print("   The counts are one expression each; the CHOICE between them, and what")
print("   each costs in holes, is not something jq offers to compute.")
print(f"\n7. {q('.cells|length')[0]} cells, "
      f"{q('[.cells[].outputs[]?]|length')[0]} outputs.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
rows = q('[.cells[]|{type:.cell_type,n:.execution_count,lines:(.source|length)}]')[0]
print(f"\n8. three fields, one row per cell: {len(rows)} rows")
for r in rows[:3]:
    print(f"     {r}")
print(f"\n9. n is null on {sum(1 for r in rows if r['n'] is None)} of {len(rows)}, "
      f"all kept — a missing key is null in an object constructor.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
print(f"\n10. text/plain exploded to lines: "
      f"{q('[.cells[].outputs[]?.data?[\"text/plain\"]?[]?]|length')[0]} rows")

# ── 11. every path whose value matches ───────────────────────────────────────
hits = q('[paths(strings) as $p|select(getpath($p)|test("https?://"))'
         '|{p:($p|map(if type=="number" then "[]" else . end)|join("."))}]'
         '|group_by(.p)|map({p:.[0].p,n:length})')[0]
print(f"\n11. values containing a URL: {sum(h['n'] for h in hits)} at "
      f"{len(hits)} folded paths")
for h in hits:
    print(f"     {h['p']:46} {h['n']:>4}")
print("   jq is the only Python-set tool that answers this without a hand-")
print("   written walk, and `paths(strings)` is why. It is also five lines.")

# ── 12. flattest honest table ────────────────────────────────────────────────
flat = q('[.cells[] as $c|$c.outputs[]?|{type:$c.cell_type,n:$c.execution_count,'
         'kind:.output_type,tp:(.data?["text/plain"]?|length)}]')[0]
print(f"\n12. flattest: {len(flat)} rows, {len(flat[0])} cols")
print("   `. as $c` binds the parent, so jq CAN carry `cell_type` down onto")
print("   each output — the join jmespath has no verb for.")
print("   WHAT IS LOST: the 140 markdown cells, which have no output; and the")
print("   17 base64 PNGs, 79% of the file, kept only as a length here.")
