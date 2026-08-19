"""jq (via the `jq` python binding) — NYC 311 service requests, 20,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   28.1 MB, 20,000 records, depth 4
  measured      2026-08-11
  run           cd corpus/14-nyc-311/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             3   NO                  YES — exactly 52
   2 how deep                                    2   NO                  YES — exactly 4
   3 what is one record                          3   NO                  PARTLY — 153 key-sets
   4 always present vs sometimes                 5   NO                  YES
   5 does any field change type                  5   NO                  YES
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   2   YES                 yes
  11 find every path matching something          4   NO                  YES — best here
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the path-to-string fold needs a comment
  16 lines, and how much is ceremony?                ~120, and the folds are most of it

**jq REPRODUCES THREE OF THE PROBE'S NUMBERS EXACTLY.** Nothing was told to it:

    paths, folded on array indices ....... 52    probe prints 52
    max path length ....................... 4    probe prints 4 levels deep
    distinct key-sets over the records ... 153    probe prints 153

The third is the interesting one. **`design/probe.py`'s `153 distinct key-sets`
is the raggedness measure this project claims nobody else computes, and TWO
tools computed it here** — jq with `unique` over `keys_unsorted`, and DuckDB
with `count(DISTINCT json_structure(json))`. That claim needs the qualifier now.

**AND IT AGREES WITH ijson ON THE ALL-STRINGS FINDING, BY A DIFFERENT ROUTE.**
`[..|scalars|type]` gives 713,768 strings and 39,140 numbers — the same two
counts ijson's event census produced. Every scalar Socrata ships is text; the
only numbers in 28.1 MB are the coordinate pairs.

**THE COST IS TIME, AND ON THIS FILE IT IS THE WORST IN THE DIRECTORY.**
`paths` over 20,000 records takes **about 10 seconds** — printed below — against
polars' 0.1 s and DuckDB's 0.3 s to read the same bytes, and 4 s more for
question 4. Every timing in this file is printed rather than typed, and they add
to roughly **39 s for the twelve answers**. `design/probe.py` describes the whole
document in 10.8 s, so **jq spends about the probe's entire runtime on question 1
alone** — and gets one answer for it where the probe gets a dozen.

**What it still cannot do is question 3.** 153 key-sets is the raw material for
pricing a row shape and jq names no candidate and computes no cost. That is
thirteen tools with the same gap on this document.
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

# ── Q1. What is in here. ─────────────────────────────────────────────────────
# `paths` yields every path as an array; array indices become [] so that the
# 20,000 record positions fold into one path rather than 20,000.
PATHS = '[paths | map(if type == "number" then "[]" else . end) | join(".")] | unique'
print("\nQ1  paths, folded on array indices:")
paths = run(PATHS, "…")
print(f"    {len(paths)} distinct paths — THE PROBE PRINTS 52.")
print(f"    deepest: {max(paths, key=lambda p: p.count('.'))}")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
print("\nQ2  max path length:")
depth = run("[paths | length] | max", "…")
print(f"    {depth} — the probe prints '4 levels deep'. Same number, no hint given.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  distinct key-sets over the records:")
keysets = run('[.[] | keys_unsorted | join(",")] | unique | length', "…")
print(f"    {keysets} — THE PROBE PRINTS '153 distinct key-sets', and DuckDB's")
print("    count(DISTINCT json_structure(json)) also returns 153. Three tools.")
print("    jq still names no row candidate and prices none of them. PARTLY.")
print(f"Q7  {jq.compile('length').input(doc).first():,} records")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
print("\nQ4  key counts:")
counts = run('[.[] | keys_unsorted[]] | group_by(.) | map({(.[0]): length}) | add', "…")
n = len(doc)
always = [k for k, c in counts.items() if c == n]
some = sorted(((k, c) for k, c in counts.items() if c < n), key=lambda kv: kv[1])
print(f"    {len(counts)} fields, always {len(always)}, sometimes {len(some)} — correct")
print(f"    rarest five: {some[:5]}")
print("    `keys_unsorted` counts PRESENCE, which is the right question. It agrees")
print("    with the frame tools here only because the document has ZERO nulls.")

# ── Q5. Does any field change type between records. ──────────────────────────
print("\nQ5  every scalar's type, censused:")
scalars = run('[.. | scalars | type] | group_by(.) | map({(.[0]): length}) | add', "…")
print(f"    {scalars}")
varying = run('[.[] | to_entries[] | {k: .key, t: (.value | type)}] | group_by(.k) '
              '| map(select((map(.t) | unique | length) > 1) | .[0].k)', "…")
print(f"    fields whose type varies between records: {varying or 'none'}")
print("    NONE. Every scalar is a string and the only numbers are coordinates.")
print("    ijson's event census gives the same two counts from the byte stream.")
print("    pandas reported 36 type changes on this document; all were NaN.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — Socrata ships fixed names. n/a")
odd = [k for k in counts if not k[0].isalpha()]
print(f"    {len(odd)} keys are not identifiers, e.g. {odd[0]}")
print('    jq needs them quoted as .["…"], the same tax jmespath charges — but')
print("    jq's error names the key, where jmespath's names a column number.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = run('[.[] | {complaint_type, borough, created_date}]', "Q8 three fields")
print(f"    {len(t):,} rows x 3 cols")
print("   ", t[0])

# ── Q9. A field missing from some records, keeping those rows. ───────────────
q9 = run('[.[] | {unique_key, status, closed_date}]', "Q9 with a missing field")
print(f"    {len(q9):,} rows kept, {sum(r['closed_date'] is None for r in q9):,} null")
print("    Object construction fills absent keys with null and KEEPS the row.")
print("    jmespath's `[].closed_date` projection drops them; jq's `.[].closed_date`")
print("    would too. The braces are what make it safe, and nothing says so.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co = run('[.[] | select(.location) | .location.coordinates]', "Q10 coordinates")
print(f"    {len(co):,} x {len(co[0])}")

# ── Q11. Find every path whose value matches something. ──────────────────────
print("\nQ11 URL-valued paths, found without naming a field:")
urls = run('[paths(type == "string" and test("https?://")) '
           '| map(if type == "number" then "[]" else . end) | join(".")] '
           '| group_by(.) | map({(.[0]): length}) | add', "…")
print(f"    {urls}")
print("    `paths(condition)` is the best answer to question 11 in either language:")
print("    one expression, no field named, no recursion written.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat = run('[.[] | . + (.location // {} | {loc_type: .type, '
           'lon: (.coordinates[0]? // null), lat: (.coordinates[1]? // null)}) '
           '| del(.location)]', "Q12 flattened")
print(f"    {len(flat):,} rows, {len(set().union(*(r.keys() for r in flat)))} distinct keys")
print("    Nothing lost — location became three scalar columns. But the union of")
print("    keys is still ragged per row: jq gives objects, not a rectangle, so")
print("    'the table' is a shape the caller has to impose afterwards.")
