"""jmespath — 200 OpenLibrary search results

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   64 KB, 200 docs, depth 4
  measured      2026-08-11
  run           cd corpus/17-openlibrary/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    2   -                   CANNOT
   3 what is one record                          11  YES                 NO — and it cannot GROUP
   4 always present vs sometimes                 5   NO                  YES
   5 does any field change type                  5   NO                  PARTLY
   6 are any object keys data                    2   -                   n/a
   7 how many records                             4   NO                  yes — both answers
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows               6   YES                 NO — drops 90 silently
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          4   NO                  NO
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 4, 7
  14 survives the next file unchanged?               Q4/Q7 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~105

**jmespath HAS NO GROUP-BY, SO IT CANNOT EVEN EXECUTE THE SPLIT.** The probe
prints `└─ or 4 tables, split on ebook_access — 16% empty`. Every other tool in
this directory can produce those four tables in one call once told the field —
`groupby`, `partition_by`, `GROUP BY`, `group_by`. jmespath needs **one filter
expression per kind**, and the kinds have to be known first:

    length(docs[?ebook_access=='no_ebook'])       183
    length(docs[?ebook_access=='printdisabled'])   12
    ...

So on this document jmespath fails question 3 twice over: it cannot choose the
discriminator, which nothing here can, **and it cannot apply one either.**

**QUESTION 9 DROPS 90 OF 200 ROWS SILENTLY, for the fourth file running.**
`docs[].cover_i` returns 110 — a projection discards elements lacking the key.
The multiselect hash keeps all 200. Same failure at 9,261 rows on `14-nyc-311`,
923 on `13-package-lock`, 52 on `15-github-issues`, and 90 here.

**Question 4 is free and correct**, because the records hold zero nulls and
`keys(@)` counts presence: 6 always, 11 sometimes.

**Question 11 is a flat NO.** The document holds exactly one URL and it is a
top-level field; jmespath can reach it once named — `documentation_url` — and has
no recursive descent to find it unprompted.
"""
import json
from collections import Counter
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")

RAW = "../source.json"
doc = json.load(open(RAW))
docs = doc["docs"]
n = len(docs)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  jmespath queries an object json.load already built and has no health")
print("    vocabulary at all. CANNOT.")

# ── Q1. What is in here. ────────────────────────────────────────────────────
allkeys = Counter(jmespath.search("docs[].keys(@)|[]", doc))
print(f"\nQ1  top level: {jmespath.search('keys(@)', doc)}")
print(f"Q1  `docs[].keys(@)|[]` -> {sum(allkeys.values()):,} occurrences over"
      f" {len(allkeys)} names")
print("    PARTLY: `docs` had to be named, and jmespath cannot enumerate paths.")
print("    The probe prints 31 distinct paths without being told anything.")

# ── Q2. How deep does it go? ────────────────────────────────────────────────
print("\nQ2  no depth function and no recursive descent operator. CANNOT.")

# ── Q3. THE SPLIT — and jmespath cannot even apply one. ────────────────────
allf = sorted({k for r in docs for k in r})
holes = sum(1 for r in docs for k in allf if k not in r) / (n * len(allf))
print(f"\nQ3  jmespath names no row candidates and prices none. The probe names two")
print(f"    and prices both, then adds a third line:")
print(f"      an item of docs   {n} rows x {len(allf)} cols   {holes:.0%} empty")
print("      └─ or 4 tables, split on ebook_access — 16% empty")
print("\nQ3  AND jmespath HAS NO GROUP-BY. Producing the four tables needs one")
print("    filter per kind, with the kinds known in advance:")
for k in ("no_ebook", "printdisabled", "borrowable", "public"):
    c = jmespath.search(f"length(docs[?ebook_access=='{k}'])", doc)
    print(f"      length(docs[?ebook_access=='{k}'])".ljust(48) + f"{c:4}")
print("    Every other tool in this directory does that in ONE call once told the")
print("    field — groupby, partition_by, GROUP BY, group_by. jmespath fails Q3")
print("    twice: it cannot choose the discriminator, and cannot apply one. NO.")

# ── Q7. How many records. ───────────────────────────────────────────────────
print(f"\nQ7  `length(docs)` = {jmespath.search('length(docs)', doc)} — and the document says")
print(f"    numFound = {doc['numFound']:,}, num_found = {doc['num_found']:,},"
      f" start = {doc['start']}.")
print("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. This is a PAGE.")

# ── Q4. Always present vs sometimes. ───────────────────────────────────────
absent = sorted(((k, c) for k, c in allkeys.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  always {sum(1 for c in allkeys.values() if c == n)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print("    `keys(@)` counts PRESENCE, which is the right question, and the records")
print("    hold no nulls so there is nothing to conflate. On 15-github-issues the")
print("    same call still got the absent half right where the frames got neither.")

# ── Q5. Does any field change type between records? ────────────────────────
print("\nQ5  `type()` works per value and the field must be named:")
for f in ("author_name", "edition_count", "ebook_access"):
    kinds = Counter(x for x in jmespath.search(f"docs[].{f} | [*].type(@)", doc) or [])
    print(f"      {f:16} {dict(kinds)}")
print("    Nothing varies, which is the probe's answer. PARTLY: three answers to")
print("    a question about seventeen fields.")

# ── Q6. Are any object keys actually data? ─────────────────────────────────
print("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA")
print("    section is empty for this file.")

# ── Q8. Three named fields into a table. ───────────────────────────────────
t = jmespath.search("docs[].{title: title, editions: edition_count, "
                    "access: ebook_access}", doc)
print(f"\nQ8  {len(t)} rows x 3 cols — multiselect hash")
print("   ", t[0])

# ── Q9. A field missing from some records. IT DROPS THEM. ─────────────────
proj = jmespath.search("docs[].cover_i", doc)
ms = jmespath.search("docs[].{k: key, c: cover_i}", doc)
print(f"\nQ9  `docs[].cover_i`            -> {len(proj)} values")
print(f"Q9  `docs[].{{k: key, c: cover_i}}` -> {len(ms)} rows,"
      f" {sum(r['c'] is None for r in ms)} null")
print(f"    THE PROJECTION LOST {n - len(proj)} ROWS — 45% of the document — and said")
print("    nothing. Fourth file running: 9,261 rows on 14-nyc-311, 923 on")
print("    13-package-lock, 52 on 15-github-issues, 90 here.")

# ── Q10. Flatten the deepest array into rows. ─────────────────────────────
names = jmespath.search("docs[].author_name[]", doc)
print(f"\nQ10 `docs[].author_name[]` -> {len(names)} names")
print("    FIVE fields are arrays and every one is ALSO sometimes absent. Here")
print("    the row-dropping is CORRECT: a doc with no author_name has no name.")

# ── Q11. Find every path whose value matches something. ───────────────────
print(f"\nQ11 `documentation_url` = {jmespath.search('documentation_url', doc)}")
print("    That is the ONLY URL in the document, and jmespath reaches it only")
print("    because I named it. No recursive descent, so 'every path whose value")
print("    matches' is not expressible. NO.")
print("    Worth noting: it is a TOP-LEVEL field, so pandas and polars — which")
print("    frame `docs` — report none of one. jmespath at least CAN be pointed.")

# ── Q12. The flattest honest table, and what was lost. ────────────────────
spec = "docs[].{" + ", ".join(f'"{k}": "{k}"' for k in allkeys) + "}"
flat = jmespath.search(spec, doc)
print(f"\nQ12 {len(flat)} x {len(allkeys)} — spec built in Python from Q1's key list")
print("    The five array fields stay arrays, and the seven top-level fields are")
print("    not in this table at all — which is why the probe names `the whole")
print("    document 1 rows x 8 cols` as a candidate in its own right.")
