"""jmespath — NYC 311 service requests, the 20,000 most recent

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   28.1 MB, 20,000 records, depth 4
  measured      2026-08-11
  run           cd corpus/14-nyc-311/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY — 35 of 48
   2 how deep                                    2   -                   CANNOT
   3 what is one record                          2   YES                 CANNOT
   4 always present vs sometimes                 5   NO                  yes, with Python
   5 does any field change type                  2   -                   CANNOT
   6 are any object keys data                    3   -                   n/a — and it CANNOT reach them
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes — multiselect
   9 a field missing from some rows               6   YES                 NO — silently drops 9,261
  10 flatten the deepest array                   2   YES                 yes
  11 find every path matching something          8   NO                  NO — raises, then partial
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 4, 7
  14 survives the next file unchanged?               Q4/Q7 yes; Q1 is first-record-only
  15 readable a week later?                          the guards need a comment
  16 lines, and how much is ceremony?                ~120, and the guards are the ceremony

**THREE FAILURES HERE AND ALL THREE ARE ABOUT RAGGEDNESS, WHICH IS THIS
DOCUMENT'S WHOLE CHARACTER.** 35 of 48 fields are sometimes-absent, and jmespath
meets that three separate ways, none of them good:

  **1. `[].closed_date` RETURNS 10,739 OF 20,000 AND SAYS NOTHING.** A projection
  drops the elements that have no such key. Question 9 asks for the missing field
  *keeping those rows*, and the obvious expression silently answers a different
  question. The multiselect hash `[].{k: unique_key, c: closed_date}` DOES keep
  all 20,000 with nulls — so two jmespath idioms disagree by 9,261 rows and
  nothing tells you which you wrote.

  **2. `contains(resolution_description, 'http')` RAISES.**
  `JMESPathTypeError: invalid type for value: None`. The natural Q11 filter
  crashes on the first record lacking the field. It needs an explicit
  `!= null &&` guard, which you can only know to write after question 4.

  **3. `:@computed_region_*` IS A ParseError AT COLUMN 0.** Four of the 48 fields
  are unreachable by the plain spelling; they need quoting. glom and pydash take
  the same string unquoted. **This is the corpus's first document with keys that
  are not identifiers, and jmespath is the only tool in either language that
  cannot address them without being told.**

**WHAT IT DOES WELL IS QUESTION 8**, where the multiselect hash is the cleanest
extraction in this directory and handles absence correctly by accident.
**Question 1 is PARTLY at best**: `[0]|keys(@)` gives the FIRST record's 35 keys,
and this document has 48 fields over 153 distinct key-sets, so the obvious
survey under-reports by 13 fields and looks complete.
"""
import json
from collections import Counter
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")

RAW = "../source.json"
doc = json.load(open(RAW))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  jmespath queries an object json.load already built. It has no")
print("    health vocabulary at all — no parse, no bytes, no warnings. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
first = jmespath.search("[0]|keys(@)", doc)
allkeys = Counter(jmespath.search("[].keys(@)|[]", doc))
print(f"\nQ1  `[0]|keys(@)` gives {len(first)} keys — the FIRST record's.")
print(f"Q1  `[].keys(@)|[]` gives {sum(allkeys.values()):,} key occurrences over")
print(f"    {len(allkeys)} distinct names. The Counter that turns one into the other")
print("    is Python's; jmespath has no group-by or count-by.")
print(f"    THE OBVIOUS SURVEY UNDER-REPORTS BY {len(allkeys) - len(first)} FIELDS.")

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
print("\nQ2  no depth function, and no recursive descent operator at all. CANNOT.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  jmespath names no row candidates and prices none. CANNOT.")
print(f"Q7  `length(@)` = {jmespath.search('length(@)', doc):,} records")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
n = len(doc)
always = [k for k, c in allkeys.items() if c == n]
some = sorted(((k, c) for k, c in allkeys.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  always {len(always)}, sometimes {len(some)} — correct")
print(f"    rarest five: {some[:5]}")
print("    Right answer, and jmespath supplied only the key lists.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  jmespath has `type()` per value but no way to aggregate over records.")
print("    Any answer here is a Python loop wearing a jmespath hat. CANNOT.")

# ── Q6. Are any object keys actually data — and can it even reach these? ─────
odd = [k for k in allkeys if not k[0].isalpha()]
print(f"\nQ6  no keyed collections. n/a. But {len(odd)} keys are not identifiers:")
print(f"    {odd[0]}")
try:
    jmespath.search(f"[0].{odd[0]}", doc)
    print("    ...and it parsed, which contradicts the recorded claim.")
except Exception as e:
    print(f"    UNQUOTED: {type(e).__name__} — {str(e).splitlines()[0]}")
quoted = f'[0]."{odd[0]}"'
print(f"    QUOTED  : {quoted} -> {jmespath.search(quoted, doc)}")

# ── Q8. Three named fields into a table. THE ONE IT IS GOOD AT. ──────────────
t = jmespath.search("[].{complaint_type: complaint_type, borough: borough, "
                    "created_date: created_date}", doc)
print(f"\nQ8  {len(t):,} rows x 3 cols — multiselect hash, and it is the cleanest here")
print("   ", t[0])

# ── Q9. A field missing from some records, keeping those rows. IT DOES NOT. ──
proj = jmespath.search("[].closed_date", doc)
ms = jmespath.search("[].{k: unique_key, c: closed_date}", doc)
print(f"\nQ9  `[].closed_date`              -> {len(proj):,} values")
print(f"Q9  `[].{{k: unique_key, c: closed_date}}` -> {len(ms):,} rows, "
      f"{sum(r['c'] is None for r in ms):,} null")
print(f"    THE PROJECTION LOST {n - len(proj):,} ROWS AND SAID NOTHING. Both")
print("    expressions are natural, they differ by a quarter of the document,")
print("    and the question asked for the second one.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co = jmespath.search("[].location.coordinates", doc)
print(f"\nQ10 `[].location.coordinates` -> {len(co):,} x {len(co[0])}")
print("    Here the same row-dropping is CORRECT: the 430 records without a")
print("    location have no coordinates to flatten.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
print("\nQ11 the natural filter:")
try:
    jmespath.search("[?contains(resolution_description, 'http')]", doc)
    print("    ...it worked, which contradicts the recorded claim.")
except Exception as e:
    print(f"    {type(e).__name__}: {str(e)[:96]}")
guarded = jmespath.search(
    "[?resolution_description != null && contains(resolution_description, 'http')]", doc)
print(f"    guarded with `!= null &&`: {len(guarded)} records — correct")
print("    But this is a FIELD I had to name. jmespath has no recursive descent,")
print("    so 'every path whose value matches' is not expressible. NO.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
spec = "[].{" + ", ".join(f'"{k}": "{k}"' for k in allkeys) + "}"
flat = jmespath.search(spec, doc)
print(f"\nQ12 {len(flat):,} x {len(allkeys)} — every key quoted, spec built in Python")
print("    `location` stays an object in one cell. The spec is 48 names long and")
print("    came from Q4's Counter, so jmespath flattened a shape Python found.")
