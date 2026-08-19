"""pandas — 200 OpenLibrary search results

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   64 KB, 200 docs, depth 4
  measured      2026-08-11
  run           cd corpus/17-openlibrary/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    3   NO                  NO — says 1
   3 what is one record                          14   YES                 NO — misses the SPLIT
   4 always present vs sometimes                 5   NO                  YES — no nulls to confuse
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                            2   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          5   NO                  NO — finds ZERO
  12 flattest honest table                       4   NO                  yes
  13 needed the shape in advance?                    NO for 4, 5, 7
  14 survives the next file unchanged?               Q4/Q5 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~115

**THIS IS THE FIRST FILE IN FOUR WHERE THE PROBE'S FOURTH OPERATION FIRES, AND
IT IS THE ONE THING pandas HAS NO WORD FOR.** `design/probe.py` prints:

    an item of docs        200 rows x 17 cols   34% empty
      └─ or 4 tables, split on ebook_access — 16% empty

`pd.json_normalize(doc["docs"])` builds the **200 x 17 at 34.2% empty** exactly —
and stops there. It does not report the cost, does not look for a discriminator,
and has no verb that would. **`groupby("ebook_access")` produces the four tables
in one line ONCE YOU KNOW THE FIELD**, and nothing in pandas tells you which of
the six always-present fields to try. Priced below: `edition_count` makes it
WORSE (35%), `public_scan_b` changes nothing (34%), and two fields tie at 16%.

**QUESTION 11 IS A ZERO, AND THAT IS THE MOST USEFUL FAILURE HERE.** The document
contains exactly **one** URL — `$.documentation_url` — and it sits at the TOP
LEVEL, outside `docs`. A frame built from the records cannot see it. `25-usgs-quakes`
recorded the same shape of miss on `metadata.url`; this file is the extreme case,
because the frame-shaped answer is not "two of three" but **none of one**.

**Everything else it gets right, and cheaply**, because this document has **zero
nulls** in the records: 6 fields always present, 11 sometimes absent, no type
variation, and no keys-as-data. It is `14-nyc-311`'s easy profile at 1/450th the
size — and it still hides a split that halves the emptiness.
"""
import json
from collections import Counter
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))
docs = doc["docs"]
n = len(docs)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pandas has no opinion; json.load read it and is silent on duplicate")
print("    keys by design. No big-int or NaN report from either. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
whole = pd.json_normalize(doc)
norm = pd.json_normalize(docs)
print(f"\nQ1  json_normalize(doc)        -> {whole.shape}")
print(f"Q1  json_normalize(doc['docs']) -> {norm.shape}")
print(f"    top-level keys: {list(doc)}")
print("    PARTLY: `docs` had to be named. The probe prints 31 distinct paths.")
print(f"Q2  deepest dotted name has {max(c.count('.') for c in whole.columns) + 1} segment(s);"
      " the document is 4 deep.")
print("    json_normalize stops at `docs`, which is a list, so it never enters")
print("    the records at all from the top. NO.")

# ── Q3. THE SPLIT — and pandas has no word for it. ──────────────────────────
holes = norm.isna().sum().sum() / (norm.shape[0] * norm.shape[1])
print(f"\nQ3  the obvious record is a doc: {norm.shape[0]} rows x {norm.shape[1]} cols,"
      f" {holes:.1%} empty")
print("    THE PROBE PRINTS EXACTLY THAT — `200 rows x 17 cols 34% empty` — AND")
print("    THEN A SECOND LINE pandas has no verb for:")
print("      └─ or 4 tables, split on ebook_access — 16% empty")
print("\nQ3  what a split on each always-present field would cost:")
allf = sorted({k for r in docs for k in r})
always = [k for k in allf if sum(k in r for r in docs) == n]
for f in always:
    vals = Counter(str(r[f]) for r in docs)
    if len(vals) < 2 or len(vals) > 24:
        print(f"      {f:16} {len(vals):3} kinds  — too many to be a discriminator")
        continue
    worst = 0.0
    for v in vals:
        g = [r for r in docs if str(r[f]) == v]
        fs = sorted({k for r in g for k in r})
        worst = max(worst, sum(1 for r in g for k in fs if k not in r) / (len(g) * len(fs)))
    verdict = "WORSE" if worst > holes - 0.01 else "better"
    print(f"      {f:16} {len(vals):3} kinds  worst group {worst:5.1%}  {verdict}")
print("    `groupby('ebook_access')` gives the four tables in ONE LINE — once you")
print("    know the field. Nothing in pandas searched for it, priced it, or")
print("    suggested it. That search is the probe's fourth operation. NO.")
for kind, g in norm.groupby("ebook_access"):
    g = g.dropna(axis=1, how="all")
    h = g.isna().sum().sum() / (g.shape[0] * g.shape[1])
    print(f"      {kind:16} {g.shape[0]:3} x {g.shape[1]:3} cols  {h:4.0%} empty")

# ── Q7. How many records. ────────────────────────────────────────────────────
print(f"\nQ7  {n} docs in the array — and the document says numFound ="
      f" {doc['numFound']:,}")
print(f"    and num_found = {doc['num_found']:,}, with start = {doc['start']}.")
print("    SO THE QUESTION HAS TWO RIGHT ANSWERS: 200 records are here, and")
print("    30,427 exist. This is a PAGE, and the only thing that says so is a")
print("    top-level field no frame built from `docs` ever sees.")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
present = norm.notna().sum()
always_c = [c for c in norm.columns if present[c] == n]
some = sorted(((c, int(present[c])) for c in norm.columns if present[c] < n),
              key=lambda kv: kv[1])
nulls = sum(1 for r in docs for v in r.values() if v is None)
print(f"\nQ4  always {len(always_c)}, sometimes {len(some)} — matches the probe")
print(f"    rarest five: {some[:5]}")
print(f"    CORRECT, and it is free: the records contain {nulls} nulls, so every")
print("    NaN is a genuine absence. 15-github-issues had 709 and this same code")
print("    conflated 5 absences with 8 nulls there.")

# ── Q5. Does any field change type between records? ──────────────────────────
kinds = {c: norm[c].map(lambda v: type(v).__name__).value_counts().to_dict()
         for c in norm.columns}
real = {c: k for c, k in kinds.items() if len(k) > 2}
print(f"\nQ5  columns holding more than TWO python types: {list(real) or 'none'}")
print("    NONE — the probe's answer. The five list-valued fields are lists")
print("    wherever they appear; the second 'type' in the others is NaN.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA")
print("    section is empty for this file.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
t = norm[["title", "edition_count", "ebook_access"]]
print(f"\nQ8  {t.shape[0]} rows x {t.shape[1]} cols")
print(t.head(3).to_string(max_colwidth=34))
print(f"\nQ9  cover_i present on {int(present['cover_i'])} of {n}; rows kept, gaps NaN")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
names = norm[["key", "author_name"]].explode("author_name").dropna(subset=["author_name"])
print(f"\nQ10 author_name exploded to {names.shape[0]} rows")
print(names.head(2).to_string(max_colwidth=30))
print("    349 author names over 200 docs, and one doc has none. FIVE fields are")
print("    list-valued — author_name, author_key, language, ia, ia_collection —")
print("    and every one of them is ALSO sometimes absent.")

# ── Q11. Find every path whose value matches something — here, a URL. ───────
in_frame = {c: int(norm[c].astype("string").str.contains("http", na=False).sum())
            for c in norm.columns}
found = {c: v for c, v in in_frame.items() if v}
print(f"\nQ11 URLs in the 200 x 17 frame: {found or 'NONE'}")
print(f"    The document holds exactly ONE URL: documentation_url ="
      f" {doc['documentation_url']}")
print("    IT IS OUTSIDE `docs`, so a frame built from the records cannot see it.")
print("    25-usgs-quakes recorded this shape of miss on `metadata.url` — two of")
print("    three paths found. Here the frame answer is NONE OF ONE.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
lists = [c for c in norm.columns if norm[c].map(lambda v: isinstance(v, list)).any()]
print(f"\nQ12 {norm.shape[0]} x {norm.shape[1]}, {holes:.1%} empty, and what is lost:")
print(f"    {len(lists)} list-columns remain: {lists}")
print("    and the SEVEN top-level fields — numFound, q, documentation_url and")
print("    the rest — are not in this table at all. The probe names `the whole")
print("    document 1 rows x 8 cols` as a candidate precisely because they exist.")
