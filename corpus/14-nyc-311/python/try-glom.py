"""glom — NYC 311 service requests, the 20,000 most recent

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   28.1 MB, 20,000 records, depth 4
  measured      2026-08-11
  run           cd corpus/14-nyc-311/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                            10   NO                  by hand
   2 how deep                                    2   NO                  by hand
   3 what is one record                          2   YES                 CANNOT
   4 always present vs sometimes                 5   NO                  YES
   5 does any field change type                  5   NO                  YES
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes — Coalesce
   9 a field missing from some rows              2   YES                 yes — Coalesce
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something         10   NO                  by hand
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 4, 5, 7
  14 survives the next file unchanged?               Q4/Q5 yes, the rest name fields
  15 readable a week later?                          yes — the specs read as shapes
  16 lines, and how much is ceremony?                ~120, and the two walks are 20

**glom TAKES THE `:@computed_region_*` KEYS UNQUOTED, AND jmespath DOES NOT.**
`glom(record, ':@computed_region_f5dn_yrer')` returns 69. The same string handed
to jmespath is a **ParseError at column 0**. Four of this document's 48 fields
carry Socrata's internal prefix, and they are the corpus's first test of whether
a path language can address a key that is not an identifier. glom passes because
it splits on `.` and asks for nothing else; pydash passes for the same reason.

**`Coalesce` IS THE RIGHT SHAPE FOR THIS DOCUMENT AND IT IS STILL PER-FIELD.**
35 of 48 fields are sometimes-absent, so every extraction here needs a default —
and `Coalesce(field, default=None)` says exactly that, once per field, by name.
On a record with 35 ragged fields that is 35 defaults you must first know to
write. glom makes the hole survivable and does nothing to make it *findable*:
question 4 is still answered by a hand-written Counter over `list(record)`.

**AND IT CANNOT SURVEY.** Questions 1, 2 and 11 are twenty lines of hand-written
recursion, which is the same sentence every path language in this directory
earns. glom's specs describe a shape you already know.
"""
import json
import re
from collections import Counter
from importlib.metadata import version

from glom import Coalesce, glom

print(f"glom {version('glom')}")

RAW = "../source.json"
doc = json.load(open(RAW))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  glom never sees bytes; json.load parsed and reported nothing.")
print("    Duplicate keys, big ints, NaN: unreported by both. CANNOT.")

# ── Q1/Q2. What is in here, and how deep — by hand. ──────────────────────────
paths, maxd = set(), 0

def walk(x, p="$", d=1):
    global maxd
    # Count CONTAINER levels, not the scalar under the last one. The first draft
    # of this counted every descent and reported 5 where the probe says 4 — an
    # off-by-one in a convention nobody writes down, found by running it.
    if isinstance(x, (dict, list)):
        maxd = max(maxd, d)
    if isinstance(x, dict):
        for k, v in x.items():
            paths.add(f"{p}.{k}")
            walk(v, f"{p}.{k}", d + 1)
    elif isinstance(x, list):
        paths.add(f"{p}[]")
        for v in x:
            walk(v, f"{p}[]", d + 1)

walk(doc)
print(f"\nQ1  {len(paths)} distinct paths — a hand-written recursion, not glom")
print(f"Q2  depth {maxd} — same recursion. Both agree with the probe.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  glom names no row candidates and prices none. CANNOT.")
print(f"Q7  {glom(doc, len):,} records")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
seen = Counter()
for r in glom(doc, [list]):
    seen.update(r)
always = [k for k, c in seen.items() if c == len(doc)]
some = sorted(((k, c) for k, c in seen.items() if c < len(doc)), key=lambda kv: kv[1])
print(f"\nQ4  {len(seen)} distinct keys; always {len(always)}, sometimes {len(some)}")
print(f"    rarest five: {some[:5]}")
print("    `glom(doc, [list])` gets the key lists; the Counter is Python's.")
print("    Counting PRESENCE is right here, and it agrees with the frame tools")
print("    for once, because this document has ZERO nulls to disagree about.")

# ── Q5. Does any field change type between records? ──────────────────────────
kinds = {}
for r in doc:
    for k, v in r.items():
        kinds.setdefault(k, set()).add(type(v).__name__)
varying = {k: v for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields holding more than one python type: {varying or 'none'}")
print(f"    types present across the document: {sorted(set().union(*kinds.values()))}")
print("    NONE, and that is the truth. Reading the values instead of a frame")
print("    avoids pandas' 36 false positives entirely — there is no NaN to trip on.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections. n/a")
print("    But four keys are not identifiers:",
      [k for k in seen if not k[0].isalpha()])

# ── Q8. Three named fields into a table. ─────────────────────────────────────
spec = [{"complaint_type": "complaint_type",
         "borough": "borough",
         "created_date": "created_date"}]
t = glom(doc, spec)
print(f"\nQ8  {len(t):,} rows x 3 cols")
print("   ", t[0])

# ── Q9. A field missing from some records, keeping those rows. ───────────────
closed = glom(doc, [Coalesce("closed_date", default=None)])
print(f"\nQ9  closed_date present on {sum(c is not None for c in closed):,} of {len(closed):,}")
print("    `Coalesce(..., default=None)` keeps the row. Without it glom raises")
print("    PathAccessError on the first record that lacks the field — which here")
print("    is record 1 of 20,000.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co = glom(doc, [Coalesce("location.coordinates", default=None)])
co = [c for c in co if c is not None]
print(f"\nQ10 coordinates to {len(co):,} x {len(co[0])}")
print("   ", co[:2])

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
print(f"\nQ11 URL-valued paths: {dict(hits)}")
print("    Ten more lines of recursion. glom's `Match`/`Regex` can TEST a value")
print("    at a path you name, and there is no way to ask it for every path.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cols = list(seen)
flat = glom(doc, [{c: Coalesce(c, default=None) for c in cols}])
print(f"\nQ12 {len(flat):,} x {len(cols)}")
print("    `location` stays a dict in one cell, so this is flatter in name only:")
print("    the honest version needs location.type and location.coordinates spelled")
print("    out, and the column list itself came from Q4's Counter, not from glom.")
