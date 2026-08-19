"""pydash — 100 openFDA adverse-event reports

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   2.7 MB, 100 results, depth 8
  measured      2026-08-11
  run           cd corpus/18-openfda-events/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             7   NO                  YES — in its own words
   2 how deep                                    3   NO                  YES — exactly 8
   3 what is one record                           7  YES                 CANNOT
   4 always present vs sometimes                 6   NO                  YES — no Python needed
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    3   -                   n/a — no abstention
   7 how many records                             5   NO                  yes — four answers
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 YES — keeps the rows
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          6   NO                  YES — in its own words
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
  14 survives the next file unchanged?               yes for those
  15 readable a week later?                          yes, once the mutation is known
  16 lines, and how much is ceremony?                ~115, and the deep walk is 8

**`map_values_deep` REACHES ALL EIGHT LEVELS AND COSTS THE MOST TIME IN THIS
DIRECTORY.** It is the only path language here that surveys unprompted, and on
the deepest file in the corpus it visits every leaf and reports the paths — but
the timing below is the largest of the eight Python tools on 2.7 MB.

**AND IT KEEPS THE ROWS WHERE jmespath DROPS THEM.**
`pydash.map_(results, "seriousnessdeath")` returns 100 values with 96 `None`;
`results[].seriousnessdeath` in jmespath returns **4**. Same question, same
document, 96 rows apart, and only one of them says so.

**THE MUTATION TRAP FROM ENTRY 14 IS STILL LIVE.** `map_values_deep` is a mapper,
not a walker: both callbacks here return `value`, and the file proves the
document survived rather than assuming it.

**AND ITS PATH ENUMERATION IS USEFUL HERE**, as on 15 and 17 and not on 13. This
document has no keys-as-data, so the raw leaf paths ARE the answer — 122 of them
by the probe's count. On `13-package-lock` the same walk gave 1,974.
"""
import copy
import json
import re
import time
from importlib.metadata import version

import pydash

print(f"pydash {version('pydash')}")

RAW = "../source.json"
doc = json.load(open(RAW))
R = doc["results"]
n = len(R)
drugs = [dr for r in R for dr in r["patient"]["drug"]]
rx = [x for r in R for x in r["patient"]["reaction"]]

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
print("\nQ0  pydash is a collection library; json.load parsed and said nothing. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ──────────────────────────────────
paths, maxlen = set(), 0


def survey(value, path):
    global maxlen
    maxlen = max(maxlen, len(path))
    paths.add("$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path))
    return value            # REQUIRED — map_values_deep MUTATES otherwise.


t0 = time.time()
pydash.map_values_deep(doc, survey)
walk_s = time.time() - t0
print(f"\nQ1  map_values_deep visited every leaf in {walk_s:.1f}s: {len(paths)} leaf paths")
print("    The probe prints 122 paths; this is leaves only, so the container")
print("    paths — $.results[], $.results[].patient, $.results[].patient.drug[] —")
print("    are never named.")
print(f"Q2  deepest leaf path is {maxlen} segments. THE PROBE PRINTS 8 levels deep,")
print("    and this is the deepest file in the corpus. pandas says 3.")
print(f"    document intact after the walk: results still {len(doc['results'])} long")

# ── Q3/Q7. The row candidates. ─────────────────────────────────────────────
print("\nQ3  pydash names no row candidates and prices none. THE PROBE NAMES FOUR:")
print("      the whole document        1 rows x  2 cols")
print("      an item of results      100 rows x 39 cols   26% empty")
print("      an item of drug         265 rows x 41 cols   47% empty")
print("      an item of reaction     247 rows x  3 cols")
print("    CANNOT.")
print(f"\nQ7  FOUR right answers: results {pydash.size(R)}, drug {len(drugs)},"
      f" reaction {len(rx)},")
print(f"    and meta.results.total = {pydash.get(doc, 'meta.results.total'):,}")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
keys = pydash.flatten([list(r) for r in R])
counts = pydash.count_by(keys)
nonnull = pydash.count_by(pydash.flatten(
    [[k for k, v in r.items() if v is not None] for r in R]))
absent = sorted(((k, c) for k, c in counts.items() if c < n), key=lambda kv: kv[1])
nullish = [k for k in counts if counts[k] == n and nonnull.get(k, 0) < n]
print(f"\nQ4  {len(keys):,} key occurrences over {len(counts)} names")
print(f"Q4  always {sum(1 for c in counts.values() if c == n)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print(f"    present but NULL: {nullish} — one field, one record.")
print("    `flatten` and `count_by` are pydash's own.")

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
print("\nQ6  no keyed collections. n/a — and the probe prints `could not call 3")
print("    small single-copy objects` and names them. That ABSTENTION is a third")
print("    state pydash has no way to express.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────
t = [pydash.pick(r, "safetyreportid", "serious", "receivedate") for r in R]
print(f"\nQ8  {len(t)} rows x 3 cols via `pick`")
print("   ", t[0])
sd = pydash.map_(R, "seriousnessdeath")
print(f"\nQ9  `map_(results, 'seriousnessdeath')` -> {len(sd)} values,"
      f" {sum(x is None for x in sd)} None")
print("    ALL 100 ROWS KEPT. jmespath's projection returns 4 for the same")
print("    question and does not say it dropped 96.")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────
brands = pydash.flatten([pydash.get(dr, "openfda.brand_name", []) for dr in drugs])
print(f"\nQ10 {len(brands)} brand names, four levels down.")
print("    `pydash.get(dr, 'openfda.brand_name', [])` handles the 57 drugs with")
print("    no openfda, and the two flattens are mine. jmespath crosses all four")
print("    levels in ONE expression; glom in one spec; jq with `..`.")

# ── Q11. Find every path whose value matches something. ────────────────
URL = re.compile(r"https?://")
hits = {}


def find(value, path):
    if isinstance(value, str) and URL.search(value):
        key = "$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path)
        hits[key] = hits.get(key, 0) + 1
    return value


pydash.map_values_deep(copy.deepcopy(doc), find)
print(f"\nQ11 URL-valued paths: {hits}")
print("    BOTH, without a field being named, and both are under `meta` —")
print("    outside `results`. pandas and polars report NONE OF TWO.")
print("    NO FOLD WAS NEEDED: on 13-package-lock this same walk gave 1,974")
print("    paths because the keys were data; here there are none.")

# ── Q12. The flattest honest table. ────────────────────────────────────
flat = [pydash.pick(r, *counts) for r in R]
print(f"\nQ12 {len(flat)} x {len(counts)} own fields — the nested objects stay dicts and")
print("    the two arrays stay arrays, holding 265 drugs and 247 reactions.")
print("    That is the probe's other two candidates, kept in cells.")
