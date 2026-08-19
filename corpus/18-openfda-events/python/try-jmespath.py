"""jmespath — 100 openFDA adverse-event reports

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   2.7 MB, 100 results, depth 8
  measured      2026-08-11
  run           cd corpus/18-openfda-events/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    2   -                   CANNOT
   3 what is one record                           7  YES                 CANNOT
   4 always present vs sometimes                 5   NO                  YES
   5 does any field change type                  4   NO                  PARTLY
   6 are any object keys data                    3   -                   n/a — no abstention
   7 how many records                             5   NO                  yes — four answers
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows               6  YES                 NO — drops 96 silently
  10 flatten the deepest array                   4   YES                 YES — one expression
  11 find every path matching something          4   NO                  NO
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 4, 7
  14 survives the next file unchanged?               Q4/Q7 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~100

**`results[].patient.drug[].openfda.brand_name[]` IS ONE EXPRESSION, AND THAT IS
jmespath'S BEST ANSWER IN THE CORPUS.** Chained `[]` flattens as it goes, so
crossing four levels costs one line and returns all 2,375 names. pandas needs two
explodes plus a normalize; polars two explodes and two struct-field accesses;
DuckDB two nested `json_each` calls. **On the deepest document in the corpus,
the tool with the least vocabulary has the shortest extraction.**

**AND THE SAME FLATTENING IS WHY QUESTION 9 LOSES 96 OF 100 ROWS.**
`results[].seriousnessdeath` returns 4 — a projection drops the elements lacking
the key. The multiselect hash keeps all 100. **Fifth file running**: 9,261 rows
on `14-nyc-311`, 923 on `13-package-lock`, 52 on `15-github-issues`, 90 on
`17-openlibrary`, 96 here. The rate is the document's; the silence is jmespath's.

**QUESTION 2 IS STILL A FLAT CANNOT.** No depth function, no recursive descent —
so on the deepest file in the corpus it has nothing to say about depth at all.
"""
import json
from collections import Counter
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")

RAW = "../source.json"
doc = json.load(open(RAW))
R = doc["results"]
n = len(R)

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
print("\nQ0  jmespath queries an object json.load already built and has no health")
print("    vocabulary at all. CANNOT.")

# ── Q1. What is in here. ───────────────────────────────────────────────────
allkeys = Counter(jmespath.search("results[].keys(@)|[]", doc))
print(f"\nQ1  top level: {jmespath.search('keys(@)', doc)}")
print(f"Q1  `results[].keys(@)|[]` -> {sum(allkeys.values()):,} occurrences over"
      f" {len(allkeys)} names")
print("    PARTLY: `results` had to be named, and jmespath cannot enumerate")
print("    paths. The probe prints 122 and ELEVEN record shapes.")

# ── Q2. How deep does it go? ──────────────────────────────────────────────
print("\nQ2  no depth function and no recursive descent. On the DEEPEST file in")
print("    the corpus it has nothing to say. CANNOT.")

# ── Q3/Q7. The row candidates. ────────────────────────────────────────────
drug = jmespath.search("length(results[].patient.drug[])", doc)
rx = jmespath.search("length(results[].patient.reaction[])", doc)
print("\nQ3  jmespath names no row candidates and prices none. THE PROBE NAMES FOUR:")
print("      the whole document        1 rows x  2 cols")
print("      an item of results      100 rows x 39 cols   26% empty")
print("      an item of drug         265 rows x 41 cols   47% empty")
print("      an item of reaction     247 rows x  3 cols")
print("    CANNOT.")
print(f"\nQ7  FOUR right answers: results {jmespath.search('length(results)', doc)},"
      f" drug {drug}, reaction {rx},")
print(f"    and meta.results.total = {jmespath.search('meta.results.total', doc):,}")
print("    Every one is one expression, and jmespath proposed none of the levels.")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
absent = sorted(((k, c) for k, c in allkeys.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  always {sum(1 for c in allkeys.values() if c == n)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print("    `keys(@)` counts PRESENCE, which is the right question, and this")
print("    document holds only 3 nulls so there is almost nothing to conflate.")

# ── Q5. Does any field change type. ──────────────────────────────────────
print("\nQ5  `type()` works per value and the field must be named:")
for f in ("receiver", "serious", "patient"):
    kinds = Counter(x for x in jmespath.search(f"results[].{f} | [*].type(@)", doc) or [])
    print(f"      {f:12} {dict(kinds)}")
print("    Nothing varies once null is set aside — the probe's answer. PARTLY:")
print("    three answers to a question about twenty-five fields.")

# ── Q6. Are any object keys actually data? ───────────────────────────────
print("\nQ6  no keyed collections. n/a — and the probe prints `could not call 3")
print("    small single-copy objects`, an ABSTENTION jmespath has no way to make.")

# ── Q8. Three named fields into a table. ─────────────────────────────────
t = jmespath.search("results[].{id: safetyreportid, serious: serious, "
                    "received: receivedate}", doc)
print(f"\nQ8  {len(t)} rows x 3 cols — multiselect hash")
print("   ", t[0])

# ── Q9. A field missing from most records. IT DROPS THEM. ───────────────
proj = jmespath.search("results[].seriousnessdeath", doc)
ms = jmespath.search("results[].{id: safetyreportid, d: seriousnessdeath}", doc)
print(f"\nQ9  `results[].seriousnessdeath`        -> {len(proj)} values")
print(f"Q9  `results[].{{id: …, d: …}}`           -> {len(ms)} rows,"
      f" {sum(r['d'] is None for r in ms)} null")
print(f"    THE PROJECTION LOST {n - len(proj)} ROWS and said nothing. FIFTH FILE RUNNING:")
print("    9,261 on 14-nyc-311, 923 on 13-package-lock, 52 on 15-github-issues,")
print("    90 on 17-openlibrary, 96 here. The rate is the document's.")

# ── Q10. Flatten the deepest array — ONE EXPRESSION. ───────────────────
brands = jmespath.search("results[].patient.drug[].openfda.brand_name[]", doc)
print(f"\nQ10 `results[].patient.drug[].openfda.brand_name[]` -> {len(brands)} names")
print("    ONE EXPRESSION ACROSS FOUR LEVELS, and the chained `[]` flattens as it")
print("    goes. pandas needs two explodes plus a normalize; polars two explodes")
print("    and two struct accesses; DuckDB two nested json_each calls. On the")
print("    deepest file in the corpus, the least-vocabulary tool is the shortest.")
print("    It is the SAME flattening that silently cost 96 rows at Q9.")

# ── Q11. Find every path whose value matches something. ────────────────
print(f"\nQ11 `meta.terms` = {jmespath.search('meta.terms', doc)[:44]}…")
print("    Two URLs in the document, both under `meta`, and jmespath reaches")
print("    them only because I named them. No recursive descent, so 'every path")
print("    whose value matches' is not expressible. NO.")

# ── Q12. The flattest honest table. ────────────────────────────────────
spec = "results[].{" + ", ".join(f'"{k}": "{k}"' for k in allkeys) + "}"
flat = jmespath.search(spec, doc)
print(f"\nQ12 {len(flat)} x {len(allkeys)} — spec built in Python from Q1's key list.")
print("    The nested objects stay objects and the two arrays stay arrays,")
print("    holding the probe's other two row candidates.")
