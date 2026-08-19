"""glom — 100 GitHub issues from one repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   686 KB, 100 issues, depth 4
  measured      2026-08-11
  run           cd corpus/15-github-issues/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                            10   NO                  by hand
   2 how deep                                    2   NO                  by hand
   3 what is one record                          3   YES                 CANNOT
   4 always present vs sometimes                 9   NO                  YES — separates both
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows               8   YES                 yes — but see Coalesce
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something         10   NO                  by hand
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 4, 5, 7
  14 survives the next file unchanged?               Q4/Q5 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~125, and the two walks are 20

**READING VALUES INSTEAD OF A FRAME MEANS glom CAN SEPARATE ABSENT FROM NULL,
AND ON THIS DOCUMENT THAT IS THE WHOLE QUESTION.** Of 36 fields, **5 are
sometimes ABSENT** and **8 are always present but sometimes NULL**. pandas,
polars and DuckDB each report **13** and cannot say which is which. `k in record`
and `record[k] is None` are two different tests, and glom's data is a dict, so
both are available.

**`Coalesce` CANNOT MAKE THE DISTINCTION, THOUGH, AND THAT IS WORTH STATING.**
`Coalesce('closed_by.login', default=None)` returns the default on the 52 issues
where `closed_by` is null AND on any issue where the field were absent. It is an
extraction verb: it makes the hole survivable and says nothing about its kind.
The separation above comes from Python, not from a glom spec.

**THE DOCUMENT HAS NO KEYS-AS-DATA AND NO DOTTED KEYS**, so glom's dotted spec —
which broke on 33 of `13-package-lock`'s keys — is untroubled here. Three
documents in, the pattern is that a path language's brittleness is a property of
the document's key names and nothing else.

**AND IT STILL CANNOT SURVEY.** Questions 1, 2 and 11 are twenty lines of
hand-written recursion, for the third file running.
"""
import json
import re
from collections import Counter
from importlib.metadata import version

from glom import Coalesce, glom

print(f"glom {version('glom')}")

RAW = "../source.json"
doc = json.load(open(RAW))
n = len(doc)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  glom never sees bytes; json.load parsed and reported nothing. CANNOT.")

# ── Q1/Q2. What is in here, and how deep — by hand. ──────────────────────────
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
print(f"\nQ1  {len(paths)} distinct paths — a hand-written recursion, not glom.")
print("    THE PROBE PRINTS 179. The `if x:` guard is why: `issue_field_values`")
print("    is an EMPTY LIST on all 100 issues, and an array that never holds an")
print("    element has no element path. Without that guard this counts 180.")
print(f"Q2  depth {maxd} — same recursion, and it agrees with the probe.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  glom names no row candidates and prices none. The probe names three")
print("    and prices them, including `a record 100 rows x 144 cols 53% empty`.")
print("    CANNOT.")
print(f"Q7  {glom(doc, len)} issues")

# ── Q4. Always present vs sometimes. THE DISCRIMINATOR, AND IT PASSES. ──────
present = Counter()
nonnull = Counter()
for r in glom(doc, [dict]):
    present.update(r.keys())
    nonnull.update(k for k, v in r.items() if v is not None)
absent = sorted(k for k, c in present.items() if c < n)
nullish = sorted(k for k in present if present[k] == n and nonnull[k] < n)
print(f"\nQ4  {len(present)} distinct fields")
print(f"      always present, always a value : {len(present) - len(absent) - len(nullish)}")
print(f"      sometimes ABSENT ({len(absent)}): {absent}")
print(f"      present but NULL ({len(nullish)}): {nullish}")
print("    BOTH KINDS, SEPARATELY. pandas, polars and DuckDB each report 13")
print("    fields as 'missing' and cannot say which of the two it is. The test")
print("    is `k in record` versus `record[k] is None`, and a dict has both.")
alwaysnull = sorted(k for k in present if nonnull[k] == 0)
print(f"    and {len(alwaysnull)} fields are NULL EVERYWHERE they appear: {alwaysnull}")

# ── Q5. Does any field change type between records? ──────────────────────────
kinds = {}
for r in doc:
    for k, v in r.items():
        if v is not None:
            kinds.setdefault(k, set()).add(type(v).__name__)
varying = {k: v for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields with more than one python type, nulls excluded: {varying or 'none'}")
print("    NONE, which is the probe's answer. Excluding null is the whole trick:")
print("    pandas' same check counts NoneType as a type and reports 9 changes.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — GitHub ships fixed field names. n/a, and the")
print("    probe's KEYS THAT ARE DATA section is empty for this file.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = glom(doc, [{"number": "number", "state": "state",
                "user": "user.login"}])
print(f"\nQ8  {len(t)} rows x 3 cols")
print("   ", t[0])

# ── Q9. A field missing from some records — AND WHAT Coalesce CANNOT SAY. ───
by_coalesce = glom(doc, [Coalesce("closed_by.login", default=None)])
print(f"\nQ9  Coalesce('closed_by.login', default=None):"
      f" {sum(x is not None for x in by_coalesce)} of {n} non-None")
r_null = next(r for r in doc if r["closed_by"] is None)
print(f"    on an issue where closed_by is NULL     -> "
      f"{glom(r_null, Coalesce('closed_by.login', default='DEFAULT'))!r}")
print("    Coalesce catches the null traversal and returns the default, which is")
print("    correct for extraction and tells you NOTHING about the kind of hole.")
print("    It would give the same answer if `closed_by` were absent. Question 4's")
print("    separation above came from Python, not from a glom spec.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
labels = [{"number": r["number"], **lab} for r in doc for lab in r["labels"]]
print(f"\nQ10 labels flattened to {len(labels)} rows")
print("   ", {k: labels[0][k] for k in ("number", "name")})
print(f"    {sum(1 for r in doc if not r['labels'])} issues have an empty label list and vanish here.")

# ── Q11. Find every path whose value matches something — by hand. ────────────
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
print(f"\nQ11 {sum(hits.values()):,} URL values over {len(hits)} paths")
print(f"    top three: {dict(hits.most_common(3))}")
print("    Ten lines of recursion. No folding was needed — this document has no")
print("    keys-as-data, so 77 paths is a real answer rather than 13-package-lock's")
print("    1,974. glom's Match/Regex test a path you name; there is no way to ask")
print("    for every path.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cols = list(present)
flat = glom(doc, [{c: Coalesce(c, default=None) for c in cols}])
print(f"\nQ12 {len(flat)} x {len(cols)}")
print("    The nested objects stay dicts in their cells, so this is the 36-column")
print("    honest table rather than pandas' 144. Nothing collides, because")
print("    nothing was flattened — polars RAISES on this document for exactly the")
print("    collision glom avoids by not attempting it.")
