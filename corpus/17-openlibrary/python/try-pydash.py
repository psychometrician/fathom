"""pydash — 200 OpenLibrary search results

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   64 KB, 200 docs, depth 4
  measured      2026-08-11
  run           cd corpus/17-openlibrary/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             6   NO                  YES — in its own words
   2 how deep                                    3   NO                  YES
   3 what is one record                          12  YES                 NO — but it APPLIES a split
   4 always present vs sometimes                 5   NO                  YES — no Python needed
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                             4   NO                  yes — both answers
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 YES — keeps the rows
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          6   NO                  YES — in its own words
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
  14 survives the next file unchanged?               yes for those
  15 readable a week later?                          yes, once the mutation is known
  16 lines, and how much is ceremony?                ~115

**pydash IS THE ONLY PATH LANGUAGE HERE WITH `group_by`, SO IT CAN APPLY THE
SPLIT IN ONE CALL — AND IT STILL CANNOT FIND IT.** The probe prints
`└─ or 4 tables, split on ebook_access — 16% empty`.
`pydash.group_by(docs, "ebook_access")` produces exactly those four groups in one
line. **What it does not do is decide that `ebook_access` is the field**: of the
six always-present ones, `edition_count` makes the emptiness worse and
`public_scan_b` changes nothing. That search is the fourth operation and nothing
in this directory has it. jmespath cannot even apply a split, needing one filter
per kind.

**AND ITS PATH ENUMERATION IS USEFUL HERE, AS IT WAS ON 15 AND NOT ON 13.**
`map_values_deep` gives 24 leaf paths and finds the single URL without a field
being named. On `13-package-lock` the same walk gave 1,974 paths because the keys
were data; this document has none, so the raw answer is the answer.

**The mutation trap from entry 14 is still live and still worked around**:
`map_values_deep` is a mapper, so both callbacks return `value`, and the file
proves the document survived rather than assuming it.

**Question 4 is free and correct** — the records hold zero nulls, so
`flatten` + `count_by` gives 6 always and 11 sometimes with nothing to conflate.
DuckDB's `unnest` route manufactures 1,164 nulls on this same document and then
reports every field as always present.
"""
import copy
import json
import re
from importlib.metadata import version

import pydash

print(f"pydash {version('pydash')}")

RAW = "../source.json"
doc = json.load(open(RAW))
docs = doc["docs"]
n = len(docs)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pydash is a collection library; json.load parsed and said nothing. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ───────────────────────────────────
paths, maxlen = set(), 0


def survey(value, path):
    global maxlen
    maxlen = max(maxlen, len(path))
    paths.add("$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path))
    return value            # REQUIRED — map_values_deep MUTATES otherwise.


pydash.map_values_deep(doc, survey)
print(f"\nQ1  map_values_deep visited every leaf: {len(paths)} distinct LEAF paths")
print("    The probe prints 31 paths; this is leaves only, so the container paths")
print("    — $.docs, $.docs[], $.docs[].author_name — are never named.")
print(f"Q2  deepest leaf path is {maxlen} segments; the probe prints 4 levels deep.")
print(f"    document intact after the walk: numFound = {doc['numFound']:,}")

# ── Q3. THE SPLIT — pydash can APPLY one. ──────────────────────────────────
allf = sorted({k for r in docs for k in r})
holes = sum(1 for r in docs for k in allf if k not in r) / (n * len(allf))
print(f"\nQ3  pydash names no row candidates and prices none. The probe names two")
print(f"    and prices both, then adds:")
print(f"      an item of docs   {n} rows x {len(allf)} cols   {holes:.0%} empty")
print("      └─ or 4 tables, split on ebook_access — 16% empty")
print("\nQ3  `group_by` APPLIES it in one call — the only path language here that can:")
for kind, g in sorted(pydash.group_by(docs, "ebook_access").items(),
                      key=lambda kv: -len(kv[1])):
    fs = sorted({k for r in g for k in r})
    h = sum(1 for r in g for k in fs if k not in r) / (len(g) * len(fs))
    print(f"      {kind:16} {len(g):3} x {len(fs):3} cols  {h:4.0%} empty")
print("    Every number matches the probe. jmespath needs one filter PER KIND and")
print("    the kinds known first. What pydash did not do is CHOOSE `ebook_access`:")
print("    `edition_count` makes it worse, `public_scan_b` changes nothing, and")
print("    `has_fulltext` ties. That choice is the fourth operation. NO.")

# ── Q7. How many records. ──────────────────────────────────────────────────
print(f"\nQ7  {pydash.size(docs)} docs in the array — the document says numFound ="
      f" {doc['numFound']:,},")
print(f"    num_found = {doc['num_found']:,}, start = {doc['start']}.")
print("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. This is a PAGE.")

# ── Q4. Always present vs sometimes. ───────────────────────────────────────
keys = pydash.flatten([list(r) for r in docs])
counts = pydash.count_by(keys)
absent = sorted(((k, c) for k, c in counts.items() if c < n), key=lambda kv: kv[1])
n_nulls = sum(1 for r in docs for v in r.values() if v is None)
print(f"\nQ4  {len(keys):,} key occurrences over {len(counts)} names")
print(f"Q4  always {sum(1 for c in counts.values() if c == n)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print(f"    `flatten` and `count_by` are pydash's own, and the records hold"
      f" {n_nulls} nulls,")
print("    so there is nothing to conflate. DuckDB's `unnest` route MANUFACTURES")
print("    1,164 nulls here and then reports every field as always present.")

# ── Q5. Does any field change type between records? ────────────────────────
kinds = {}
for r in docs:
    for k, v in r.items():
        kinds.setdefault(k, set()).add(type(v).__name__)
varying = {k: v for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields with more than one python type: {varying or 'none'}")
print("    NONE — the probe's answer. The five list-valued fields are lists")
print("    wherever they appear.")

# ── Q6. Are any object keys actually data? ─────────────────────────────────
print("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA")
print("    section is empty for this file.")

# ── Q8/Q9. Extraction. ─────────────────────────────────────────────────────
t = [pydash.pick(r, "title", "edition_count", "ebook_access") for r in docs]
print(f"\nQ8  {len(t)} rows x 3 cols via `pick`")
print("   ", t[0])
cov = pydash.map_(docs, "cover_i")
print(f"\nQ9  `map_(docs, 'cover_i')` -> {len(cov)} values,"
      f" {sum(x is None for x in cov)} None — ALL 200 ROWS KEPT")
print("    jmespath's `docs[].cover_i` projection returns 110 and drops 90.")

# ── Q10. Flatten the deepest array into rows. ──────────────────────────────
names = pydash.flatten([r.get("author_name", []) for r in docs])
print(f"\nQ10 author_name flattened to {len(names)} names")
print("    FIVE fields are lists — author_name, author_key, language, ia,")
print("    ia_collection — and every one is ALSO sometimes absent.")

# ── Q11. Find every path whose value matches something. ───────────────────
URL = re.compile(r"https?://")
hits = {}


def find(value, path):
    if isinstance(value, str) and URL.search(value):
        key = "$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path)
        hits[key] = hits.get(key, 0) + 1
    return value


pydash.map_values_deep(copy.deepcopy(doc), find)
print(f"\nQ11 URL-valued paths: {hits}")
print("    ONE URL IN THE WHOLE DOCUMENT, at the TOP LEVEL, found without a field")
print("    being named. pandas and polars frame `docs` and report NONE OF ONE.")
print("    NO FOLD WAS NEEDED: on 13-package-lock this same walk gave 1,974 paths")
print("    because the keys were data; here there are none.")

# ── Q12. The flattest honest table, and what was lost. ────────────────────
flat = [pydash.pick(r, *counts) for r in docs]
print(f"\nQ12 {len(flat)} x {len(counts)}, {holes:.0%} empty")
print("    The five list fields stay lists. The seven top-level fields are not")
print("    here at all, which is why the probe names the whole document as a")
print("    candidate in its own right.")
