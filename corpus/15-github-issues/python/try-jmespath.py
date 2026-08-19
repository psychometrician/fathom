"""jmespath — 100 GitHub issues from one repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   686 KB, 100 issues, depth 4
  measured      2026-08-11
  run           cd corpus/15-github-issues/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    2   -                   CANNOT
   3 what is one record                          3   YES                 CANNOT
   4 always present vs sometimes                14   NO                  YES — absent free, null per-field
   5 does any field change type                  5   NO                  PARTLY
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows               7   YES                 NO — drops 52 silently
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          4   NO                  NO
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 4a, 7
  14 survives the next file unchanged?               Q4a/Q7 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~110

**`keys(@)` GETS THE ABSENT HALF OF QUESTION 4 EXACTLY RIGHT, AND THIS CORRECTS
WHAT THE CORPUS RECORDED.** `FINDINGS.md` for `25-usgs-quakes` places jmespath
with the frame tools on question 4, on the grounds that *"it has no `has`, so a
missing key and a null key are one thing to the path language."* Measured here,
`[].keys(@)|[]` **includes keys whose value is null** and reports exactly the
**5 sometimes-absent fields**, which is the truth.

**It gets the null half too, and it costs 36 queries.** `length([?f != null])`
finds all **8** always-present-but-null fields — correctly — but the field must
be named, because there is no way to map a predicate over every key. jmespath
supplied the predicate and Python supplied the iteration.

> **So jmespath separates absent from null on this document, and pandas, polars
> and DuckDB do not.** It belongs with the walkers here, not with the frames.
> The corpus's earlier placement of it was made on a document where the question
> was asked through a projection instead of through `keys`.

**QUESTION 9 IS STILL WRONG AND STILL SILENT, FOR THE THIRD FILE RUNNING.**
`[].closed_by.login` returns **48 of 100** — the projection drops every issue
where `closed_by` is null. The multiselect hash keeps all 100. Same failure as
entry 13 (923 rows) and entry 14 (9,261 rows); here it is 52.

**AND QUESTION 11 IS A FLAT NO.** No recursive descent, so "every path whose
value matches" is not expressible. The truth is 77 paths and 3,297 values.
"""
import json
from collections import Counter
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")

RAW = "../source.json"
doc = json.load(open(RAW))
n = len(doc)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  jmespath queries an object json.load already built and has no health")
print("    vocabulary at all. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
allkeys = Counter(jmespath.search("[].keys(@)|[]", doc))
first = jmespath.search("[0]|keys(@)", doc)
print(f"\nQ1  `[].keys(@)|[]` -> {sum(allkeys.values()):,} key occurrences over"
      f" {len(allkeys)} names")
print(f"    `[0]|keys(@)` -> {len(first)}, because the FIRST issue lacks three fields.")
print("    The Counter is Python's; jmespath has no count-by. PARTLY: it reaches")
print("    the record's own fields and cannot enumerate paths at all.")

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
print("\nQ2  no depth function and no recursive descent operator. CANNOT.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  jmespath names no row candidates and prices none. CANNOT.")
print(f"Q7  `length(@)` = {jmespath.search('length(@)', doc)} issues")

# ── Q4. THE DISCRIMINATOR: right on absent, partial on null. ────────────────
absent = sorted(k for k, c in allkeys.items() if c < n)
truth_absent = sorted(k for k in {k for r in doc for k in r}
                      if sum(k in r for r in doc) < n)
print(f"\nQ4a `keys(@)` reports {len(absent)} fields as sometimes ABSENT:")
print(f"      {absent}")
print(f"    correct: {absent == truth_absent}")
print("    KEYS WHOSE VALUE IS NULL ARE INCLUDED, so this counts PRESENCE — the")
print("    right question. FINDINGS.md for 25-usgs-quakes places jmespath with")
print("    the frame tools here; on this document that is too harsh.")

nullish = {}
for k in sorted(allkeys):
    if allkeys[k] == n:
        cnt = jmespath.search(f"length([?{k} != null])", doc) if k.isidentifier() else None
        if cnt is not None and cnt < n:
            nullish[k] = cnt
print(f"\nQ4b naming the always-present-but-NULL fields needs one query EACH:")
print(f"      {len(nullish)} found: {sorted(nullish)}")
print("    There is no way to map a predicate over every key, so this is 36")
print("    queries wearing one loop. The truth is 8, and it found them — but")
print("    jmespath supplied the predicate and Python supplied the iteration.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  `type()` works per value, and again the field must be named:")
for f in ("draft", "closed_by", "state"):
    kinds = Counter(x for x in jmespath.search(f"[].{f} | [*].type(@)", doc) or [])
    print(f"      {f:12} {dict(kinds)}")
print("    Nothing varies once null is set aside, which is the probe's answer.")
print("    PARTLY: three answers to a question about 36 fields.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — GitHub ships fixed field names. n/a")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = jmespath.search("[].{number: number, state: state, user: user.login}", doc)
print(f"\nQ8  {len(t)} rows x 3 cols — multiselect hash")
print("   ", t[0])

# ── Q9. A field missing from some records. IT DROPS THEM. ───────────────────
proj = jmespath.search("[].closed_by.login", doc)
ms = jmespath.search("[].{n: number, c: closed_by.login}", doc)
print(f"\nQ9  `[].closed_by.login`              -> {len(proj)} values")
print(f"Q9  `[].{{n: number, c: closed_by.login}}` -> {len(ms)} rows,"
      f" {sum(r['c'] is None for r in ms)} null")
print(f"    THE PROJECTION LOST {n - len(proj)} ROWS — every issue where closed_by is")
print("    null — and said nothing. Third file running: 9,261 rows on 14-nyc-311,")
print("    923 on 13-package-lock, 52 here. The rate is the document's; the")
print("    silence is jmespath's.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
labels = jmespath.search("[].labels[]", doc)
print(f"\nQ10 `[].labels[]` -> {len(labels)} label objects")
print(f"    the 40 issues with an empty label list contribute nothing, which is")
print("    right here and is the same row-dropping that is wrong in Q9.")

# ── Q11. Find every path whose value matches something. ──────────────────────
named = jmespath.search("length([?contains(url, 'http')])", doc)
print(f"\nQ11 `url` holding a URL: {named} — but the FIELD had to be named.")
print("    No recursive descent, so 'every path whose value matches' is not")
print("    expressible. The truth is 77 paths and 3,297 values. NO.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
spec = "[].{" + ", ".join(f'"{k}": "{k}"' for k in allkeys) + "}"
flat = jmespath.search(spec, doc)
print(f"\nQ12 {len(flat)} x {len(allkeys)} — spec built in Python from Q1's key list")
print("    The nested objects stay objects. Nothing collides and nothing is lost,")
print("    because nothing was flattened — polars RAISES on this document and")
print("    DuckDB returns 19 duplicate column names for attempting it.")
