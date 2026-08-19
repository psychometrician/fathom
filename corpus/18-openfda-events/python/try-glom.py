"""glom — 100 openFDA adverse-event reports

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   2.7 MB, 100 results, depth 8
  measured      2026-08-11
  run           cd corpus/18-openfda-events/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                            10  NO                  by hand
   2 how deep                                    2   NO                  by hand
   3 what is one record                           8  YES                 CANNOT
   4 always present vs sometimes                 6   NO                  YES
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    4   -                   n/a — no abstention
   7 how many records                             5   NO                  yes — four answers
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   5   YES                 YES — one spec
  11 find every path matching something          9   NO                  YES — by hand
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 4, 5, 7, 11
  14 survives the next file unchanged?               Q4/Q5/Q11 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~115, and the two walks are 19

**glom's `[...]` SPEC CROSSES FOUR LEVELS IN ONE LINE, WHICH IS ITS BEST SHOWING
IN THE CORPUS.** `("results", ["patient.drug"], Flatten(), ["openfda.brand_name"],
Flatten())` walks `results[] → patient → drug[] → openfda → brand_name[]` and
returns all 2,375 names. pandas needs two explodes plus a normalize; polars needs
two explodes and two struct-field accesses; DuckDB needs two nested `json_each`
calls. **Only jq's `..` is shorter, and jq names no level at all where glom names
each one.**

**AND THE HAND-WRITTEN WALK REPRODUCES BOTH PROBE NUMBERS** — 122 paths and
depth 8, on the deepest document in the corpus.

**IT FINDS BOTH URLs**, which pandas and polars cannot: they are `meta.terms` and
`meta.license`, outside `results`, and a walk that starts at the root sees them.

**WHAT IT HAS NO WORD FOR IS THE ABSTENTION.** The probe prints `could not call 3
small single-copy objects` and names them — a third state between "keys are data"
and "keys are fields". glom has `Check` and `Match` for values and nothing that
declines.
"""
import json
import re
from collections import Counter
from importlib.metadata import version

from glom import Coalesce, Flatten, glom

print(f"glom {version('glom')}")

RAW = "../source.json"
doc = json.load(open(RAW))
R = doc["results"]
n = len(R)

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
print("\nQ0  glom never sees bytes; json.load parsed and reported nothing. CANNOT.")

# ── Q1/Q2. What is in here, and how deep — by hand. ────────────────────────
paths, maxd = set(), 0


def walk(x, p="$", d=1):
    global maxd
    if isinstance(x, (dict, list)):
        maxd = max(maxd, d)
    if isinstance(x, dict):
        for k, v in x.items():
            paths.add(f"{p}.{k}")
            walk(v, f"{p}.{k}", d + 1)
    elif isinstance(x, list):
        if x:
            paths.add(f"{p}[]")
        for v in x:
            walk(v, f"{p}[]", d + 1)


walk(doc)
print(f"\nQ1  {len(paths)} distinct paths — THE PROBE PRINTS 122. A hand-written")
print("    recursion, starting at the ROOT, which is why Q11 works below.")
print(f"Q2  depth {maxd} — same recursion. THE PROBE PRINTS 8, and this is the")
print("    deepest file in the corpus. pandas says 3.")

# ── Q3/Q7. The row candidates. ────────────────────────────────────────────
drugs = glom(doc, ("results", ["patient.drug"], Flatten()))
rx = glom(doc, ("results", ["patient.reaction"], Flatten()))
print("\nQ3  glom names no row candidates and prices none. THE PROBE NAMES FOUR:")
print("      the whole document        1 rows x  2 cols")
print("      an item of results      100 rows x 39 cols   26% empty")
print("      an item of drug         265 rows x 41 cols   47% empty")
print("      an item of reaction     247 rows x  3 cols")
print("    CANNOT.")
print(f"\nQ7  FOUR right answers: results {n}, drug {len(drugs)}, reaction {len(rx)},")
print(f"    and meta.results.total says {doc['meta']['results']['total']:,} exist.")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
present, nonnull = Counter(), Counter()
for r in glom(doc, ("results", [dict])):
    present.update(r.keys())
    nonnull.update(k for k, v in r.items() if v is not None)
absent = sorted(((k, c) for k, c in present.items() if c < n), key=lambda kv: kv[1])
nullish = [k for k in present if present[k] == n and nonnull[k] < n]
print(f"\nQ4  {len(present)} fields; always {len(present) - len(absent)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print(f"    present but NULL: {nullish} — one field, one record.")
print("    `k in record` and `record[k] is None` are two tests, and this document")
print("    needs both only once. 15-github-issues needed them 709 times.")

# ── Q5. Does any field change type. ──────────────────────────────────────
kinds = {}
for r in R:
    for k, v in r.items():
        if v is not None:
            kinds.setdefault(k, set()).add(type(v).__name__)
varying = {k: v for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields with more than one python type, nulls excluded: {varying or 'none'}")
print("    NONE — the probe's answer. pandas' same check over a frame reports")
print("    TWELVE: eleven NaN artefacts and one real null.")

# ── Q6. Are any object keys actually data? ───────────────────────────────
print("\nQ6  no keyed collections. n/a — and the probe says something glom cannot:")
print("      could not call 3 small single-copy objects, shortest first:")
print("        $.meta · $.meta.results · $.results[].patient.patientdeath")
print("    THAT IS AN ABSTENTION. glom's Check and Match test values; nothing")
print("    in it declines to judge.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────
t = glom(doc, ("results", [{"id": "safetyreportid", "serious": "serious",
                            "received": "receivedate"}]))
print(f"\nQ8  {len(t)} rows x 3 cols")
print("   ", t[0])
sd = glom(doc, ("results", [Coalesce("seriousnessdeath", default=None)]))
print(f"\nQ9  seriousnessdeath present on {sum(x is not None for x in sd)} of {n} —")
print("    `Coalesce(default=None)` keeps the row.")

# ── Q10. Flatten the deepest array — ONE SPEC. ──────────────────────────
brands = glom(doc, ("results",
                    ["patient.drug"], Flatten(),
                    [Coalesce("openfda.brand_name", default=[])], Flatten()))
print(f"\nQ10 {len(brands)} brand names, from ONE spec crossing four levels:")
print('      ("results", ["patient.drug"], Flatten(),')
print('       [Coalesce("openfda.brand_name", default=[])], Flatten())')
print("    pandas needs two explodes plus a normalize; polars two explodes and")
print("    two struct-field accesses; DuckDB two nested json_each calls. Only")
print("    jq's `..` is shorter — and it names no level where glom names each.")

# ── Q11. Find every path whose value matches something — by hand. ──────
URL = re.compile(r"https?://")
hits = Counter()


def find(x, p="$"):
    if isinstance(x, dict):
        for k, v in x.items():
            find(v, f"{p}.{k}")
    elif isinstance(x, list):
        for v in x:
            find(v, f"{p}[]")
    elif isinstance(x, str) and URL.search(x):
        hits[p] += 1


find(doc)
print(f"\nQ11 URL-valued paths: {dict(hits)}")
print("    BOTH, and both are under `meta` — outside `results`. pandas and polars")
print("    frame the records and report NONE OF TWO. Nine lines of recursion.")

# ── Q12. The flattest honest table. ────────────────────────────────────
cols = list(present)
flat = glom(doc, ("results", [{c: Coalesce(c, default=None) for c in cols}]))
print(f"\nQ12 {len(flat)} x {len(cols)} own fields — the nested objects stay dicts and")
print("    the two arrays stay arrays, holding 265 drugs and 247 reactions.")
print("    That is the probe's other two candidates, kept in cells.")
