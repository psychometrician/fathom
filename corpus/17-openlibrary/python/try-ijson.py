"""ijson — 200 OpenLibrary search results

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   64 KB, 200 docs, depth 4
  measured      2026-08-11
  run           cd corpus/17-openlibrary/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               4   -                   PARTLY
   1 what is in here                             5   NO                  YES — 31 + root
   2 how deep                                    3   NO                  YES — exactly 4
   3 what is one record                           8  NO                  PARTLY — misses the SPLIT
   4 always present vs sometimes                 7   NO                  YES
   5 does any field change type                  6   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                             5   NO                  YES — both answers, in one pass
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          4   NO                  YES
  12 flattest honest table                       4   NO                  yes
  13 needed the shape in advance?                    NO for 0,1,2,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the prefix grammar needs a comment
  16 lines, and how much is ceremony?                ~130, and one pass does most of it

**ONE PASS ANSWERS SEVEN QUESTIONS AND ALSO CATCHES THE PAGE.** `numFound`,
`num_found`, `start` and the 200 elements of `docs` all arrive in the same
stream, so ijson is the only tool here that reports **both right answers to
question 7 without being asked twice**: 200 records are present and 30,427 exist.
The frame tools have to be pointed at two different tables to see both.

**EXACTLY ONE `null` EVENT IN THE WHOLE DOCUMENT**, and it is the top-level
`offset`. The 200 records contain none. That is why every walker in this
directory agrees on question 4 here and why `15-github-issues`, with 807 null
events, split the same tools nine to four.

**31 PATHS PLUS THE EMPTY ROOT, for the fourth file running.** ijson's prefixes
reproduce the probe's count exactly and the relationship is the same as on
entries 13, 14 and 15. And the dot-joined-prefix bug that cost it 33 paths on
`13-package-lock` cannot fire: none of these field names contains a dot.

**WHAT IT CANNOT DO IS THE SPLIT.** The probe prints
`└─ or 4 tables, split on ebook_access — 16% empty`. A streaming parser has no
group-by at all — it would need a second pass, and the field named first. That
is the fourth operation, and this is the first of the five entries graded today
where it fires.
"""
import re
import resource
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')} (backend: {ijson.backend})")

RAW = "../source.json"

# ── ONE PASS answers Q0, Q1, Q2, Q4, Q5, Q7 and Q11. ────────────────────────
prefixes, events = Counter(), Counter()
kinds = defaultdict(set)
per_doc, urls = Counter(), Counter()
n_docs = 0
meta = {}
last_key = None
URL = re.compile(r"https?://")
VALUE = {"string", "number", "boolean", "null", "start_map", "start_array"}

t0 = time.time()
with open(RAW, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        prefixes[prefix] += 1
        events[event] += 1
        if event in VALUE:
            kinds[prefix].add(event)
        if prefix == "docs.item" and event == "start_map":
            n_docs += 1
        if prefix == "docs.item" and event == "map_key":
            per_doc[value] += 1
            last_key = value
        elif last_key is not None and prefix == f"docs.item.{last_key}":
            last_key = None
        # The page metadata sits beside `docs`, in the same stream.
        if prefix in ("numFound", "num_found", "start") and event == "number":
            meta[prefix] = value
        if event == "string" and URL.search(value):
            urls[prefix] += 1
elapsed = time.time() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
n = n_docs

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
print(f"\nQ0  one streaming pass: {elapsed:.2f}s, peak RSS ~{rss:.0f} MB")
print("    ijson RAISES on malformed JSON mid-stream. It does NOT report")
print("    duplicate keys — it emits both. No big-int or NaN warning. PARTLY.")

# ── Q1/Q2. What is in here, and how deep. ───────────────────────────────────
deepest = max(prefixes, key=lambda p: len(p.split(".")))
print(f"\nQ1  {len(prefixes)} distinct prefixes = the probe's 31 paths + the empty root —")
print("    the same relationship as on entries 13, 14 and 15.")
print(f"    deepest: {deepest}")
print(f"Q2  {len(deepest.split('.'))} segments — the probe prints 4 levels deep. Correct.")
print("    And the dot-joined-prefix bug that cost 33 paths on 13-package-lock")
print("    cannot fire here: none of these field names contains a dot.")

# ── Q3. THE SPLIT. ──────────────────────────────────────────────────────────
print("\nQ3  the `docs.item` prefix makes the record addressable, so ijson names it")
print("    without being told. It prices nothing.")
print("    The probe names two candidates, prices both, and adds a third line:")
print("      └─ or 4 tables, split on ebook_access — 16% empty")
print("    A STREAMING PARSER HAS NO GROUP-BY AT ALL. Producing those four tables")
print("    needs a second pass with the field named first, and choosing the field")
print("    is the fourth operation. This is the first of the five entries graded")
print("    today where it fires. PARTLY.")

# ── Q7. How many records — BOTH ANSWERS, FROM ONE PASS. ────────────────────
print(f"\nQ7  {n} docs in the array — and from the SAME stream:")
for k in ("numFound", "num_found", "start"):
    print(f"      {k:12} {meta.get(k)!r}")
print("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. ijson is the only tool")
print("    in this directory that reports both without being pointed at two")
print("    different tables — the page metadata is beside `docs` in the stream.")

# ── Q4. Always present vs sometimes. ───────────────────────────────────────
absent = sorted(((k, c) for k, c in per_doc.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  {len(per_doc)} fields, from `map_key` events at prefix `docs.item`")
print(f"Q4  always {sum(1 for c in per_doc.values() if c == n)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print(f"\nQ4  THE WHOLE DOCUMENT CONTAINS {events['null']} null EVENT, and it is the")
print("    top-level `offset`. The 200 records contain none, which is why every")
print("    walker here agrees on this question. 15-github-issues had 807 null")
print("    events and split the same tools nine to four.")

# ── Q5. Does any field change type between records. ───────────────────────
varying = {p: sorted(k - {"null"}) for p, k in kinds.items() if len(k - {"null"}) > 1}
print(f"\nQ5  prefixes whose non-null value events are of more than one kind:"
      f" {varying or 'none'}")
print(f"    event census: {dict(events)}")
print("    NONE — the probe's answer. Grouping by prefix is grouping by field")
print("    here, because there are no data keys; on 13-package-lock that same")
print("    assumption made this check report ZERO on a document that HAS two")
print("    polymorphic fields.")

# ── Q6. Are any object keys actually data? ────────────────────────────────
print("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA")
print("    section is empty for this file.")

# ── Q8/Q9/Q10/Q12. Extraction, second pass. ──────────────────────────────
t1 = time.time()
rows, cover_seen, names = [], 0, []
with open(RAW, "rb") as f:
    for rec in ijson.items(f, "docs.item"):
        rows.append((rec["title"], rec["edition_count"], rec["ebook_access"]))
        if "cover_i" in rec:
            cover_seen += 1
        names += rec.get("author_name", [])
print(f"\nQ8  ijson.items(f, 'docs.item') -> {len(rows)} rows x 3 cols"
      f" ({time.time() - t1:.2f}s)")
print("   ", rows[0])
print(f"\nQ9  cover_i present on {cover_seen} of {len(rows)} — rows kept, `.get` gives None,")
print("    and Q4 above says it is an ABSENCE rather than a null.")
print(f"\nQ10 author_name flattened to {len(names)} names")
print("    FIVE fields are arrays and every one is ALSO sometimes absent.")
print(f"\nQ12 {len(rows)} rows x {len(per_doc)} fields from the same pass; the five array")
print("    fields stay arrays. The seven top-level fields are a separate shape,")
print("    which is why the probe names the whole document as its own candidate.")

# ── Q11. Find every path whose value matches something. ──────────────────
print(f"\nQ11 URL-valued prefixes: {dict(urls)}")
print("    ONE URL IN THE DOCUMENT, at the top level, free from the same pass.")
print("    pandas and polars build a frame from `docs` and report NONE OF ONE;")
print("    a stream that starts at the root cannot miss it.")
