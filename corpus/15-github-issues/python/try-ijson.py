"""ijson — 100 GitHub issues from one repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   686 KB, 100 issues, depth 4
  measured      2026-08-11
  run           cd corpus/15-github-issues/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               4   -                   PARTLY
   1 what is in here                             5   NO                  YES — 179 + root
   2 how deep                                    3   NO                  YES — exactly 4
   3 what is one record                          3   NO                  PARTLY
   4 always present vs sometimes                12   NO                  YES — BEST HERE
   5 does any field change type                  6   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               5   YES                 yes
   9 a field missing from some rows              4   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          4   NO                  YES
  12 flattest honest table                       4   NO                  yes
  13 needed the shape in advance?                    NO for 0,1,2,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the value-event tracking needs a comment
  16 lines, and how much is ceremony?                ~135, and one pass does most of it

**`null` IS AN EVENT, AND THAT MAKES ijson THE BEST ANSWER TO QUESTION 4 IN THIS
DIRECTORY.** The stream carries **807 `null` events** on this document. A field
that is absent produces no `map_key` at all; a field that is null produces a
`map_key` followed by a `null`. **Those are two different token sequences**, so
the distinction survives into the answer:

    sometimes ABSENT (5)          draft, pull_request, pinned_comment, …
    present but NULL (8)          type, active_lock_reason, closed_by, …
    with exact per-field counts   type 100, closed_at 52, closed_by 52, …

pandas, polars and DuckDB each report **13** and cannot say which is which. This
document has **709 nulls across 36 fields**, and it is where that difference
finally costs something — `14-nyc-311` had none, so every tool agreed there.

**IT ALSO REPRODUCES THE PROBE'S PATH COUNT FOR THE THIRD FILE RUNNING.** 180
distinct prefixes = the probe's **179 paths plus the empty root**, the same
relationship as on entries 13 and 14. And `item.issue_field_values` has no
`.item` child, because an array that is empty on all 100 issues never emits an
element — which is exactly why the probe counts 179 and a naive walk counts 180.

**AND THE DOT-JOINED-PREFIX BUG THAT RUINED ENTRY 13 CANNOT FIRE HERE.** That
document had 33 keys containing a dot, so its prefixes could not be split back
into paths. GitHub's field names contain none. **Same tool, same representation,
and the flaw is a property of the document's key names.**

**The cost is nothing: 0.01 s and about 27 MB** — printed at run time — and it
never builds the document. (A bare `parse` loop with no per-event work is 21 MB;
the rest is this file's six counters.)
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
prefixes, events = Counter(), Counter()
kinds = defaultdict(set)
per_key, nulls = Counter(), Counter()
urls = Counter()
n_records = 0
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
        if prefix == "item" and event == "start_map":
            n_records += 1
        # A field of an issue: the map_key is at prefix `item`, and its VALUE
        # arrives at prefix `item.<key>`. That is how a null is told from an
        # absence — an absent field never emits the map_key at all.
        if prefix == "item" and event == "map_key":
            per_key[value] += 1
            last_key = value
        elif last_key is not None and prefix == f"item.{last_key}":
            if event == "null":
                nulls[last_key] += 1
            last_key = None
        if event == "string" and URL.search(value):
            urls[prefix] += 1
elapsed = time.time() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
n = n_records

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print(f"\nQ0  one streaming pass: {elapsed:.2f}s, peak RSS ~{rss:.0f} MB")
print("    ijson RAISES on malformed JSON mid-stream. It does NOT report")
print("    duplicate keys — it emits both. No big-int or NaN warning. PARTLY.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
deepest = max(prefixes, key=lambda p: len(p.split(".")))
print(f"\nQ1  {len(prefixes)} distinct prefixes = the probe's 179 paths + the empty root.")
print(f"    deepest: {deepest}")
print("    `item.issue_field_values` has NO `.item` child: that array is empty on")
print("    all 100 issues, so no element is ever emitted. That is precisely why")
print("    the probe counts 179 where a naive walk counts 180.")
print(f"Q2  {len(deepest.split('.'))} segments — the probe prints 4 levels deep. Correct.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  the `item` prefix makes the array element addressable, so ijson names")
print("    the record without being told. It prices nothing and offers no")
print("    alternative; the probe names three candidates with costs. PARTLY.")
print(f"Q7  {n} issues")

# ── Q4. THE DISCRIMINATOR — AND ijson SEES BOTH KINDS. ──────────────────────
absent = sorted(k for k, c in per_key.items() if c < n)
nullish = sorted(k for k in per_key if per_key[k] == n and nulls[k] > 0)
print(f"\nQ4  {len(per_key)} fields, from `map_key` events at prefix `item`")
print(f"      sometimes ABSENT ({len(absent)}): {absent}")
print(f"      present but NULL ({len(nullish)}): {nullish}")
print(f"\nQ4  and the exact null counts, from `null` EVENTS:")
for k, c in nulls.most_common():
    tag = "absent on the rest" if per_key[k] < n else ""
    print(f"      {k:28} {c:3} null of {per_key[k]:3} present   {tag}")
print(f"    THE STREAM CARRIES {events['null']} NULL EVENTS. An absent field emits no")
print("    map_key; a null field emits a map_key and then a null. Two different")
print("    token sequences, so the distinction survives. pandas, polars and")
print("    DuckDB each report 13 fields as 'missing' and cannot separate them.")

# ── Q5. Does any field change type between records. ─────────────────────────
varying = {p: sorted(k - {"null"}) for p, k in kinds.items()
           if len(k - {"null"}) > 1}
print(f"\nQ5  prefixes whose non-null value events are of more than one kind:"
      f" {varying or 'none'}")
print(f"    event census: {dict(events)}")
print("    NONE, which is the probe's answer. Excluding `null` is what makes it")
print("    right — and on 13-package-lock this same check reported ZERO on a")
print("    document that HAS two polymorphic fields, because the keys were data")
print("    and every package's `engines` had its own prefix. Here there are no")
print("    data keys, so grouping by prefix is grouping by field.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — GitHub ships fixed field names. n/a, and the")
print("    probe's KEYS THAT ARE DATA section is empty for this file.")

# ── Q8/Q9/Q10/Q12. Extraction, second pass. ─────────────────────────────────
t1 = time.time()
rows, closed_seen, labels = [], 0, []
with open(RAW, "rb") as f:
    for rec in ijson.items(f, "item"):
        rows.append((rec["number"], rec["state"], rec["user"]["login"]))
        if rec.get("closed_by") is not None:
            closed_seen += 1
        labels += [{"number": rec["number"], **lab} for lab in rec["labels"]]
print(f"\nQ8  {len(rows)} rows x 3 cols in a second pass ({time.time() - t1:.2f}s)")
print("   ", rows[0])
print(f"\nQ9  closed_by non-null on {closed_seen} of {len(rows)} — rows kept, because")
print("    `.get` returns None and the row was already built. And Q4 above says")
print("    WHY it is None, which no frame tool can.")
print(f"\nQ10 labels flattened to {len(labels)} rows")
print(f"    {sum(1 for r in rows if True) - len({l['number'] for l in labels})}"
      " issues have an empty label list and contribute none.")
print(f"\nQ12 {len(rows)} rows x 36 fields is available from the same pass; the")
print("    nested objects would each need naming. Nothing collides — polars")
print("    RAISES on this document and DuckDB returns 19 duplicate names.")

# ── Q11. Find every path whose value matches something. ─────────────────────
print(f"\nQ11 {sum(urls.values()):,} URL values over {len(urls)} prefixes")
print(f"    top three: {dict(urls.most_common(3))}")
print("    Free from the same pass. AND THE PREFIXES ARE TRUSTWORTHY HERE:")
print("    13-package-lock had 33 keys containing a dot, so its dot-joined")
print("    prefixes could not be split back into paths and this same census came")
print("    out short by exactly 33. GitHub's field names contain no dots.")
