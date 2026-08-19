"""pydash — NYC 311 service requests, the 20,000 most recent

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   28.1 MB, 20,000 records, depth 4
  measured      2026-08-11
  run           cd corpus/14-nyc-311/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             8   NO                  YES — in its own words
   2 how deep                                    3   NO                  YES — in its own words
   3 what is one record                          2   YES                 CANNOT
   4 always present vs sometimes                 5   NO                  YES — no Python needed
   5 does any field change type                  5   NO                  YES
   6 are any object keys data                    2   -                   n/a — and it reaches them
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 YES — keeps the rows
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          6   NO                  YES — in its own words
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 11
  14 survives the next file unchanged?               Q1/Q2/Q4/Q5/Q11 yes
  15 readable a week later?                          NO — see the mutation trap below
  16 lines, and how much is ceremony?                ~130, and the deep-copy is the ceremony

**THE FINDING IS A TRAP, AND THE FIRST DRAFT OF THIS FILE FELL STRAIGHT INTO IT.**
`pydash.map_values_deep` is the only recursive walker in any of the three Python
path languages, and it is **not a walker — it is a mapper, and it MUTATES THE
DOCUMENT IN PLACE.** Each leaf is replaced by whatever the callback returns.

A survey callback naturally returns nothing:

    pydash.map_values_deep(doc, lambda v, p: paths.add(fmt(p)))   # set.add -> None

`set.add` returns `None`, so that line **silently overwrote all 752,908 leaves in
the document with `None`.** Q1 printed a perfect answer — 49 paths, 5.2 s — and
then Q4 reported 20,000 nulls, Q8 returned three `None` columns, and Q11 found no
URLs, because by then the document was empty. **Nothing raised. Nothing warned.**
The survey answered its own question correctly and destroyed the evidence for
every question after it.

The fix is to return `value` from the callback, and this file now does. It is
recorded because it is precisely the failure mode this project's method exists to
catch — **the prose was written from a run, and only running the REST of the file
showed the run was poisoned.** Compare `25-usgs-quakes`'s pandas dtype check and
its jq `from_entries`: three files, three silent wrong answers, none catchable by
reading.

**WITH THE TRAP AVOIDED, pydash IS THE BEST PATH LANGUAGE HERE.** It answers
questions 1, 2, 4, 5 and 11 in its own vocabulary; glom and jmespath need
hand-written recursion for 1, 2 and 11, and jmespath cannot express 2 at all.
**And it gets question 9 right where jmespath gets it wrong** — `map_` returns
all 20,000 rows with 9,261 `None`, against jmespath's silent 10,739.

**THE COST IS TIME.** The deep walk takes about 5 s, against 0.1 s for polars and
0.3 s for DuckDB to read the same 28.1 MB — half of `design/probe.py`'s 10.8 s
for the whole description, spent on one question.
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

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pydash is a collection library; json.load parsed and said nothing.")
print("    No health vocabulary on either side. CANNOT.")

# ── Q1/Q2. What is in here, and how deep — IN PYDASH'S OWN VOCABULARY. ───────
# THE CALLBACK MUST RETURN `value`. map_values_deep REPLACES each leaf with the
# return value, in place, in the caller's document. A survey callback that
# returns None empties the document and raises nothing.
paths, maxlen = set(), 0

def survey(value, path):
    global maxlen
    maxlen = max(maxlen, len(path))
    paths.add("$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path))
    return value            # <- REQUIRED. Without this the document is destroyed.

t0 = time.time()
pydash.map_values_deep(doc, survey)
walk_s = time.time() - t0
print(f"\nQ1  map_values_deep visited every LEAF: {len(paths)} distinct leaf paths"
      f" in {walk_s:.1f}s")
print(f"    {sorted(paths)[0]}")
print(f"    {[p for p in paths if 'coordinates' in p][0]}")
print("    The probe prints 52 paths and this is 49: pydash visits LEAVES, so the")
print("    three container paths — $[], $[].location, $[].location.coordinates —")
print("    are never named. Nothing warns you that a container is not a leaf.")
print(f"Q2  deepest leaf path is {maxlen} segments long, and the document is 4 deep.")
print("    Those agree here because the deepest leaf sits directly inside the")
print("    deepest container. It is a leaf count, not a container count, and on a")
print("    document with an empty container at the bottom it would disagree.")

# Proof the walk was non-destructive, since a survey that empties the document
# is the failure this file exists to record.
print(f"    document intact after the walk: doc[0]['agency'] = {doc[0]['agency']!r}")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  pydash names no row candidates and prices none. CANNOT.")
print(f"Q7  {pydash.size(doc):,} records")

# ── Q4. Always present vs sometimes — NO collections.Counter. ────────────────
keys = pydash.flatten([list(r) for r in doc])
counts = pydash.count_by(keys)
n = len(doc)
always = [k for k, c in counts.items() if c == n]
some = sorted(((k, c) for k, c in counts.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  {len(keys):,} key occurrences over {len(counts)} names")
print(f"Q4  always {len(always)}, sometimes {len(some)} — correct")
print(f"    rarest five: {some[:5]}")
print("    `flatten` and `count_by` are pydash's own; glom and jmespath both")
print("    borrow collections.Counter for this line.")

# ── Q5. Does any field change type between records? ──────────────────────────
kinds = {}
for r in doc:
    for k, v in r.items():
        kinds.setdefault(k, set()).add(type(v).__name__)
varying = {k: v for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields holding more than one python type: {varying or 'none'}")
print(f"    types across the document: {sorted(set().union(*kinds.values()))}")
print("    NONE — the truth. Every scalar in this document is a JSON string.")
print("    pandas' same check on its frame reported 36 changes, all of them NaN.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
odd = [k for k in counts if not k[0].isalpha()]
print(f"\nQ6  no keyed collections. n/a. {len(odd)} keys are not identifiers, and")
print(f"    pydash.get takes them unquoted: {odd[0]} -> {pydash.get(doc[0], odd[0])}")
print("    jmespath raises a ParseError on that same string.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = [pydash.pick(r, "complaint_type", "borough", "created_date") for r in doc]
print(f"\nQ8  {len(t):,} rows x 3 cols via `pick`")
print("   ", t[0])

# ── Q9. A field missing from some records, keeping those rows. ───────────────
closed = pydash.map_(doc, "closed_date")
print(f"\nQ9  `map_(doc, 'closed_date')` -> {len(closed):,} values, "
      f"{sum(c is None for c in closed):,} None")
print("    ALL 20,000 ROWS KEPT. jmespath's `[].closed_date` returns 10,739 for")
print("    the same question and does not say it dropped the rest.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co = [c for c in pydash.map_(doc, "location.coordinates") if c is not None]
print(f"\nQ10 `map_(doc, 'location.coordinates')` -> {len(co):,} x {len(co[0])}")
print("   ", co[:2])

# ── Q11. Find every path whose value matches something — IN PYDASH. ──────────
URL = re.compile(r"https?://")
hits = {}

def find(value, path):
    if isinstance(value, str) and URL.search(value):
        key = "$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path)
        hits[key] = hits.get(key, 0) + 1
    return value            # <- same trap, same fix

pydash.map_values_deep(copy.deepcopy(doc), find)
print(f"\nQ11 URL-valued paths: {hits}")
print("    Correct — 19 of 20,000, buried in prose — and the walk is pydash's")
print("    rather than a hand-written recursion. It is the only path language")
print("    in this directory that answers question 11 in its own words.")
print("    The deepcopy is belt-and-braces against the mutation above.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cols = list(counts)
flat = [pydash.pick(r, *cols) for r in doc]
print(f"\nQ12 {len(flat):,} x {len(cols)}")
print("    `location` stays a dict in one cell. The column list came from Q4's")
print("    count_by, which is at least pydash's own answer rather than Python's.")
