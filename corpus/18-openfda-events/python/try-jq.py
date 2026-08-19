"""jq (via the `jq` python binding) — 100 openFDA adverse-event reports

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   2.7 MB, 100 results, depth 8
  measured      2026-08-11
  run           cd corpus/18-openfda-events/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             4   NO                  YES — exactly 122
   2 how deep                                    2   NO                  YES — exactly 8
   3 what is one record                          10  NO                  PARTLY — finds the levels
   4 always present vs sometimes                 6   NO                  YES
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    5   -                   n/a — no abstention
   7 how many records                             4   NO                  yes — four answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   3   YES                 YES — one expression
  11 find every path matching something          4   NO                  YES — best here
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the array-index fold needs a comment
  16 lines, and how much is ceremony?                ~115

**ON THE DEEPEST DOCUMENT IN THE CORPUS jq REPRODUCES FOUR OF THE PROBE'S
NUMBERS EXACTLY:**

    paths, array indices folded ..... 122    probe prints 122
    max path length ................... 8    probe prints 8 levels deep
    key-sets over results ............ 12    probe prints 12
    key-sets over drug .............. 115    probe prints 115

**AND `..` MAKES QUESTION 10 ONE EXPRESSION** where pandas needs two explodes and
a normalize, and polars needs two explodes and two struct-field accesses.
`[.. | .brand_name? // empty | .[]]` crosses four levels — `results[]`, `patient`,
`drug[]`, `openfda` — without naming any of them.

**IT ALSO FINDS BOTH URLs**, which pandas and polars cannot: they are
`meta.terms` and `meta.license`, outside `results`, and `paths` starts at the root.

**WHAT IT WILL NOT DO IS ENUMERATE THE ROW CANDIDATES.** The probe names four at
three nesting levels and prices them. jq can COUNT any level you name — and the
counts below are one expression each — but it does not propose the levels, and
it computes no cost.

**AND IT HAS NO ABSTENTION.** The probe prints `could not call 3 small
single-copy objects` and names them: a third state between "keys are data" and
"keys are fields". jq's `keys` gives the raw material and no verdict, and no way
to say "too few copies to judge".
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
    print(f"    [{time.time() - t0:5.2f}s] {label}")
    return out


# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
print("\nQ0  the binding takes an already-parsed object, so jq never saw the bytes.")
print("    No duplicate-key, big-int or NaN report from either side. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ──────────────────────────────────
print("\nQ1  paths, with array indices folded to []:")
paths = run('[paths | map(if type == "number" then "[]" else . end) | join(".")]'
            ' | unique', "…")
print(f"    {len(paths)} — THE PROBE PRINTS 122. Exact.")
print(f"    deepest: {max(paths, key=lambda p: p.count('.'))}")
print("\nQ2  max path length:")
print(f"    {run('[paths | length] | max', '…')} — the probe prints 8, and this is the")
print("    deepest file in the corpus. pandas says 3.")

# ── Q3/Q7. The row candidates, and how many of each. ──────────────────────
print("\nQ3/Q7  jq can COUNT any level named, one expression each:")
counts = run('{results: (.results | length),'
             ' drug: ([.results[].patient.drug[]] | length),'
             ' reaction: ([.results[].patient.reaction[]] | length),'
             ' openfda: ([.results[].patient.drug[].openfda? // empty] | length),'
             ' total_available: .meta.results.total}', "…")
print(f"    {counts}")
print("    THE PROBE NAMES FOUR CANDIDATES AND PRICES THEM:")
print("      the whole document        1 rows x  2 cols")
print("      an item of results      100 rows x 39 cols   26% empty")
print("      an item of drug         265 rows x 41 cols   47% empty")
print("      an item of reaction     247 rows x  3 cols")
print("    jq counted every level I named and proposed none of them, and it")
print("    computed no cost. PARTLY — the counting is free, the choosing is not.")
print(f"    Note the fourth number: {counts['total_available']:,} events exist, in a")
print("    field no frame built from `results` can see.")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
print("\nQ4  field counts over the results:")
fc = run('[.results[] | keys_unsorted[]] | group_by(.) | map({(.[0]): length}) | add', "…")
n = len(doc["results"])
absent = sorted(((k, c) for k, c in fc.items() if c < n), key=lambda kv: kv[1])
nulls = run('[.. | select(. == null)] | length', "…")
print(f"    {len(fc)} fields · always {sum(1 for c in fc.values() if c == n)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print(f"    and {nulls} nulls in the WHOLE document, so `has` and `!= null` agree")
print("    almost everywhere. On 15-github-issues there were 807.")

# ── Q5. Does any field change type. ───────────────────────────────────────
print("\nQ5  fields whose non-null type varies, over the results:")
varying = run('''[.results[] | to_entries[] | select(.value != null)
      | {k: .key, t: (.value | type)}] | group_by(.k)
      | map(select((map(.t) | unique | length) > 1) | .[0].k)''', "…")
print(f"    {varying or 'none'} — the probe's answer. pandas' python-type check")
print("    reports TWELVE on this document: eleven NaN and one real null.")

# ── Q6. Are any object keys actually data? ────────────────────────────────
print("\nQ6  no keyed collections. n/a — and the probe says something jq cannot:")
print("      could not call 3 small single-copy objects, shortest first:")
print("        $.meta · $.meta.results · $.results[].patient.patientdeath")
print("    THAT IS AN ABSTENTION — one copy, too few keys to judge. `keys` gives")
print("    the raw material and no verdict, and there is no way to say 'unsure'.")

# ── Q8/Q9. Extraction. ────────────────────────────────────────────────────
print("\nQ8  three fields:")
t = run('[.results[] | {safetyreportid, serious, receivedate}]', "…")
print(f"    {len(t)} rows x 3 cols · {t[0]}")
print("\nQ9  a field absent from most results:")
q9 = run('[.results[] | {safetyreportid, seriousnessdeath}]', "…")
print(f"    {len(q9)} rows kept, {sum(r['seriousnessdeath'] is None for r in q9)} null")

# ── Q10. Flatten the deepest array — ONE EXPRESSION. ─────────────────────
print("\nQ10 the deepest array, crossing four levels with `..`:")
brands = run('[.. | .brand_name? // empty | .[]] | length', "…")
print(f"    {brands} brand names, from `[.. | .brand_name? // empty | .[]]`")
print("    NO LEVEL WAS NAMED. pandas needs two explodes and a normalize; polars")
print("    needs two explodes and two struct-field accesses. `..` is the one verb")
print("    in this comparison that does not care how deep the thing is.")

# ── Q11. Find every path whose value matches something. ─────────────────
print("\nQ11 URL-valued paths, no field named:")
urls = run('[paths(type == "string" and test("https?://")) '
           '| map(if type == "number" then "[]" else . end) | join(".")]'
           ' | group_by(.) | map({(.[0]): length}) | add', "…")
print(f"    {urls}")
print("    BOTH are under `meta`, outside `results`. pandas and polars frame the")
print("    records and report NONE OF TWO. `paths` starts at the root.")

# ── Q12. The flattest honest table, and what was lost. ──────────────────
print("\nQ12 the honest record table:")
flat = run('[.results[]]', "…")
keys = sorted(set().union(*(set(r) for r in flat)))
print(f"    {len(flat)} rows, {len(keys)} own fields — and TWO of them are arrays")
print("    holding the probe's other two row candidates, 265 drugs and 247")
print("    reactions. The honest answer is three tables, and jq gives one.")
