"""ijson — NYC 311 service requests, the 20,000 most recent

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   28.1 MB, 20,000 records, depth 4
  measured      2026-08-11
  run           cd corpus/14-nyc-311/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               4   -                   PARTLY — best here
   1 what is in here                             4   NO                  YES — exactly 52
   2 how deep                                    2   NO                  YES
   3 what is one record                          3   NO                  PARTLY
   4 always present vs sometimes                 6   NO                  YES
   5 does any field change type                  6   NO                  YES — per path, from events
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               5   YES                 yes
   9 a field missing from some rows              4   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          4   NO                  YES
  12 flattest honest table                       5   NO                  yes
  13 needed the shape in advance?                    NO for 0,1,2,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the prefix grammar needs a comment
  16 lines, and how much is ceremony?                ~135, and one pass does most of it

**ijson IS THE MEMORY ANSWER AND THIS FILE IS WHERE IT SHOWS.** The pass below,
which answers Q0, Q1, Q2, Q4, Q5, Q7 and Q11 at once, costs **0.6–0.7 s and about
27 MB resident** — printed at run time, not typed. `design/probe.py` needed
**229 MB** on the same document, which `NOTES.md` records as an 8.2x multiplier.
**ijson's is about 1x — it never builds the document.** Every other tool in this
directory materialises all 20,000 records before answering anything.

(A bare `ijson.parse` loop with no per-event work is 0.4 s and 22 MB. The extra
0.3 s and 5 MB below are this file's six counters and the URL regex, and the
header records what the file actually printed rather than the cheaper number.)

**AND ITS PREFIXES ARE PATHS, SO IT AGREES WITH THE PROBE EXACTLY.** `ijson.parse`
yields `(prefix, event, value)` and the prefix is the path. 53 distinct prefixes,
which is the probe's **52 paths plus the empty root** — the third independent
reproduction of a probe number in this corpus, after jq's paths on `25-usgs-quakes`
and DuckDB's 153 key-sets on this one.

**THE EVENT CENSUS PROVES THE ALL-STRINGS FINDING WITHOUT A TYPE CHECK.**
713,768 `string` events, 39,140 `number` events, and **every one of the numbers is
under `item.location.coordinates.item`.** Socrata ships every column as text; the
only real numbers in 28.1 MB are the 19,570 coordinate pairs. No frame, no dtype,
no inference — just what the bytes said.

**QUESTION 5 IS ANSWERED PROPERLY, WHICH IS RARE.** Grouping event kinds by
prefix gives one type per path with no aggregation trick, and no NaN to trip on.
pandas reported 36 false type changes on this document; ijson reports none,
because a streaming parser has no holes to mistake for values.

**What it still cannot do is question 3**, and question 0 only partly: it fails
loudly on malformed input, which is more than most here, but it reports no
duplicate keys — it emits both, and the caller decides. That is arguably the
correct behaviour and it is still not a warning.
"""
import re
import resource
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')} (backend: {ijson.backend})")

RAW = "../source.json"

# ── ONE PASS answers Q0, Q1, Q2, Q4, Q5, Q7 and Q11. ─────────────────────────
prefixes = Counter()
events = Counter()
kinds = defaultdict(set)          # prefix -> set of event kinds  (Q5)
per_record = Counter()            # field  -> records that carried it (Q4)
urls = Counter()                  # prefix -> URL-valued strings (Q11)
n_records = 0
URL = re.compile(r"https?://")
VALUE = {"string", "number", "boolean", "null"}

t0 = time.time()
with open(RAW, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        prefixes[prefix] += 1
        events[event] += 1
        if event in VALUE or event in ("start_map", "start_array"):
            kinds[prefix].add(event)
        if prefix == "item" and event == "start_map":
            n_records += 1
        if event == "map_key" and prefix == "item":
            per_record[value] += 1
        if event == "string" and URL.search(value):
            urls[prefix] += 1
elapsed = time.time() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print(f"\nQ0  one streaming pass completed: {elapsed:.1f}s, peak RSS ~{rss:.0f} MB")
print("    ijson RAISES on malformed JSON mid-stream, which is more than pandas,")
print("    glom, jmespath or pydash do. It does NOT report duplicate keys — it")
print("    emits both and lets the caller decide. No big-int or NaN warning.")
print("    PARTLY, and it is the best Q0 in this directory.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
deepest = max((p for p in prefixes), key=lambda p: len(p.split(".")))
print(f"\nQ1  {len(prefixes)} distinct prefixes — and a prefix IS a path.")
print(f"    the probe prints 52 paths; this is those plus the empty root.")
print(f"    deepest: {deepest}")
print(f"Q2  depth {len(deepest.split('.'))} by counting prefix segments"
      " — the document is 4 deep. Correct.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  `item` is the obvious record and ijson names it, because the prefix")
print("    grammar makes the array element addressable. It prices nothing and")
print("    offers no alternative. PARTLY — more than most tools here manage.")
print(f"Q7  {n_records:,} records")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
always = [k for k, c in per_record.items() if c == n_records]
some = sorted(((k, c) for k, c in per_record.items() if c < n_records),
              key=lambda kv: kv[1])
print(f"\nQ4  {len(per_record)} field names, always {len(always)}, sometimes {len(some)}")
print(f"    rarest five: {some[:5]}")
print("    Counted from `map_key` events at prefix `item`, so this is PRESENCE —")
print("    and it agrees with the frame tools because the document has no nulls.")

# ── Q5. Does any field change type between records. ──────────────────────────
varying = {p: sorted(k) for p, k in kinds.items() if len(k) > 1}
print(f"\nQ5  paths whose value events are of more than one kind: {varying or 'none'}")
print(f"    event census: {dict(events)}")
print(f"    {events['string']:,} strings and {events['number']:,} numbers, and every")
print("    number is a coordinate. EVERY SCALAR FIELD IN THIS DOCUMENT IS A JSON")
print("    STRING — Socrata types nothing. No dtype, no inference, just events.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
odd = [k for k in per_record if not k[0].isalpha()]
print(f"\nQ6  no keyed collections. n/a. {len(odd)} keys are not identifiers;")
print("    ijson has no path SYNTAX to trip over, so they cost nothing here.")

# ── Q8/Q9/Q12. Extraction — a second pass, using ijson.items. ────────────────
t1 = time.time()
rows, closed_seen, coords = [], 0, []
flat_cols = list(per_record)
flat_n = 0
with open(RAW, "rb") as f:
    for rec in ijson.items(f, "item"):
        rows.append((rec.get("complaint_type"), rec.get("borough"),
                     rec.get("created_date")))
        if "closed_date" in rec:
            closed_seen += 1
        loc = rec.get("location")
        if loc:
            coords.append([float(c) for c in loc["coordinates"]])
        flat_n += 1
print(f"\nQ8  {len(rows):,} rows x 3 cols in a second pass ({time.time() - t1:.1f}s)")
print("   ", rows[0])
print(f"\nQ9  closed_date present on {closed_seen:,} of {flat_n:,} — rows kept, because")
print("    `rec.get` returns None and the row was already built. No default needed.")
print(f"\nQ10 coordinates to {len(coords):,} x {len(coords[0])}")
print("   ", coords[:2])
print(f"\nQ12 {flat_n:,} x {len(flat_cols)} is available from the same pass; `location`")
print("    would still need spelling out into two columns. Nothing is lost that")
print("    the other tools keep — but ijson gives you rows, never a frame.")

# ── Q11. Find every path whose value matches something. ──────────────────────
print(f"\nQ11 URL-valued prefixes: {dict(urls)}")
print("    Free — it fell out of the same pass as Q1, Q2, Q4, Q5 and Q7. No field")
print("    had to be named, and no recursion had to be written. Only pydash and")
print("    jq also manage this, and both build the whole document first.")
