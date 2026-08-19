"""glom — 200 OpenLibrary search results

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   64 KB, 200 docs, depth 4
  measured      2026-08-11
  run           cd corpus/17-openlibrary/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                            10   NO                  by hand
   2 how deep                                    2   NO                  by hand
   3 what is one record                          11  YES                 NO — misses the SPLIT
   4 always present vs sometimes                 5   NO                  YES
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                             4   NO                  yes — both answers
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes — Coalesce
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          9   NO                  YES — by hand
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 4, 5, 7, 11
  14 survives the next file unchanged?               Q4/Q5/Q11 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~115, and the two walks are 19

**THE PROBE'S FOURTH OPERATION FIRES ON THIS DOCUMENT AND glom HAS NO WORD FOR
IT** — nor does any other tool in this directory. `design/probe.py` prints
`an item of docs 200 rows x 17 cols 34% empty` and then
`└─ or 4 tables, split on ebook_access — 16% empty`. glom names no candidate at
all, so it does not even reach the point where a split could be missed.

**READING VALUES RATHER THAN A FRAME IS FREE HERE**, because the records hold
**zero nulls**: 6 fields always present, 11 sometimes absent, no type variation.
On `15-github-issues` that distinction was the whole entry; here it costs nothing
and glom gets question 4 right the same way DuckDB's route B does.

**AND IT FINDS THE ONE URL, WHICH TWO OF THE THREE FRAMES DO NOT.** The document
holds exactly one — `documentation_url`, a TOP-LEVEL field outside `docs`. A
hand-written walk starts at the root, so it sees it. pandas and polars build a
200-row frame from the records and report **none of one**.

**The cost is the usual one**: questions 1, 2 and 11 are nineteen lines of
recursion, for the fifth file running.
"""
import json
import re
from collections import Counter
from importlib.metadata import version

from glom import Coalesce, glom

print(f"glom {version('glom')}")

RAW = "../source.json"
doc = json.load(open(RAW))
docs = doc["docs"]
n = len(docs)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  glom never sees bytes; json.load parsed and reported nothing. CANNOT.")

# ── Q1/Q2. What is in here, and how deep — by hand. ─────────────────────────
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
        if x:                       # an empty array has no element path
            paths.add(f"{p}[]")
        for v in x:
            walk(v, f"{p}[]", d + 1)


walk(doc)
print(f"\nQ1  {len(paths)} distinct paths — THE PROBE PRINTS 31. A hand-written")
print("    recursion, not glom, and it starts at the ROOT rather than at `docs`.")
print(f"Q2  depth {maxd} — same recursion, and it agrees with the probe.")

# ── Q3. THE SPLIT. ──────────────────────────────────────────────────────────
allf = sorted({k for r in docs for k in r})
holes = sum(1 for r in docs for k in allf if k not in r) / (n * len(allf))
print(f"\nQ3  glom names NO row candidates and prices none. CANNOT.")
print(f"    The probe names two and prices both: `the whole document 1 x 8` and")
print(f"    `an item of docs {n} x {len(allf)} {holes:.0%} empty` — and then a third line:")
print("      └─ or 4 tables, split on ebook_access — 16% empty")
print("\nQ3  what a split on each always-present field would cost:")
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
    print(f"      {f:16} {len(vals):3} kinds  worst group {worst:5.1%}"
          f"  {'WORSE' if worst > holes - 0.01 else 'better'}")
print("    Two fields tie at 16.4%, and the probe reports `ebook_access` — the")
print("    finer of the two, since `has_fulltext` is exactly its coarsening.")
print("    Nothing in glom searched, priced or chose. That is the fourth operation.")

# ── Q7. How many records. ───────────────────────────────────────────────────
print(f"\nQ7  {glom(docs, len)} docs in the array — and the document says numFound ="
      f" {doc['numFound']:,},")
print(f"    num_found = {doc['num_found']:,}, start = {doc['start']}.")
print("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. This is a PAGE.")

# ── Q4. Always present vs sometimes. ────────────────────────────────────────
present = Counter()
nonnull = Counter()
for r in glom(docs, [dict]):
    present.update(r.keys())
    nonnull.update(k for k, v in r.items() if v is not None)
absent = sorted(k for k, c in present.items() if c < n)
nullish = sorted(k for k in present if present[k] == n and nonnull[k] < n)
print(f"\nQ4  {len(present)} distinct fields; always {len(present) - len(absent)},"
      f" sometimes {len(absent)}")
print(f"      present but NULL: {nullish or 'none'}")
print(f"      rarest five: {sorted(((k, c) for k, c in present.items()), key=lambda kv: kv[1])[:5]}")
print("    Matches the probe. `k in record` and `record[k] is None` are two tests")
print("    and this document only needs one — the records hold no nulls at all.")
print("    DuckDB's `unnest` route MANUFACTURES 1,164 nulls here and then reports")
print("    every field as always present; reading the values cannot do that.")

# ── Q5. Does any field change type between records? ─────────────────────────
kinds = {}
for r in docs:
    for k, v in r.items():
        kinds.setdefault(k, set()).add(type(v).__name__)
varying = {k: v for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields with more than one python type: {varying or 'none'}")
print("    NONE — the probe's answer. The five list-valued fields are lists")
print("    wherever they appear. DuckDB's STRUCT route reports ELEVEN varying,")
print("    all of them NULL against the real type, all of them invented.")

# ── Q6. Are any object keys actually data? ──────────────────────────────────
print("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA")
print("    section is empty for this file.")

# ── Q8/Q9. Extraction. ──────────────────────────────────────────────────────
t = glom(docs, [{"title": "title", "editions": "edition_count",
                 "access": "ebook_access"}])
print(f"\nQ8  {len(t)} rows x 3 cols")
print("   ", t[0])
cov = glom(docs, [Coalesce("cover_i", default=None)])
print(f"\nQ9  cover_i present on {sum(x is not None for x in cov)} of {n} —"
      " `Coalesce(default=None)` keeps the row")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────────
names = [{"key": r["key"], "author": a}
         for r in docs for a in r.get("author_name", [])]
print(f"\nQ10 author_name flattened to {len(names)} rows")
print(f"    {sum(1 for r in docs if 'author_name' not in r)} doc has none and contributes nothing.")
print("    FIVE fields are lists — author_name, author_key, language, ia,")
print("    ia_collection — and every one is ALSO sometimes absent, which is the")
print("    combination this entry adds to the corpus.")

# ── Q11. Find every path whose value matches something — by hand. ──────────
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
print("    ONE URL IN THE WHOLE DOCUMENT, and it is at the TOP LEVEL. The walk")
print("    starts at the root so it finds it; pandas and polars build a frame")
print("    from `docs` and report NONE OF ONE. Nine lines of recursion, and")
print("    glom's Match/Regex can only test a path you already name.")

# ── Q12. The flattest honest table, and what was lost. ─────────────────────
flat = glom(docs, [{c: Coalesce(c, default=None) for c in allf}])
print(f"\nQ12 {len(flat)} x {len(allf)}, {holes:.0%} empty")
print("    The five list fields stay lists — five list-columns, which is what")
print("    god's spec refuses. And the SEVEN top-level fields are not here at")
print("    all, which is why the probe names the whole document as a candidate.")
