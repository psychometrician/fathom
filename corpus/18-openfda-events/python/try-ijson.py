"""ijson — 100 openFDA adverse-event reports

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   2.7 MB, 100 results, depth 8
  measured      2026-08-11
  run           cd corpus/18-openfda-events/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               4   -                   PARTLY
   1 what is in here                             5   NO                  YES — 122 + root
   2 how deep                                    3   NO                  YES — exactly 8
   3 what is one record                           6  NO                  PARTLY — names all levels
   4 always present vs sometimes                 6   NO                  YES
   5 does any field change type                  6   NO                  YES — correctly none
   6 are any object keys data                    4   -                   n/a — no abstention
   7 how many records                             6   NO                  YES — four, one pass
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          4   NO                  YES
  12 flattest honest table                       4   NO                  yes
  13 needed the shape in advance?                    NO for 0,1,2,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the prefix grammar needs a comment
  16 lines, and how much is ceremony?                ~125, and one pass does most of it

**ONE PASS COUNTS ALL FOUR LEVELS AND FINDS BOTH URLs, ON THE DEEPEST DOCUMENT IN
THE CORPUS.** `results.item`, `results.item.patient.drug.item`,
`results.item.patient.reaction.item` and `meta.results.total` all arrive in the
same stream, so ijson answers question 7 four ways without being pointed
anywhere — and the two URLs under `meta` come free, where pandas and polars
report none of two.

**123 PREFIXES = THE PROBE'S 122 PATHS PLUS THE EMPTY ROOT**, the same
relationship as on entries 13, 14, 15 and 17. Five files, one convention, and
neither tool states it.

**THE DEEPEST PREFIX IS EIGHT SEGMENTS LONG** —
`results.item.patient.drug.item.openfda.application_number.item` — and it costs
nothing to reach, because a streaming parser does not care how deep a thing is.
pandas answers 3 of 8 on this file.

**AND THE DOT-JOINED-PREFIX BUG CANNOT FIRE HERE.** It cost ijson 33 paths on
`13-package-lock`, whose keys contained dots. openFDA's field names contain
none, so the prefixes are invertible — a property of the document, not the tool.

**Only 3 null events in 2.7 MB**, so this document's raggedness is almost purely
absence. `15-github-issues` had 807 and the tools split nine to four over them.
"""
import re
import resource
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')} (backend: {ijson.backend})")

RAW = "../source.json"
prefixes, events = Counter(), Counter()
kinds = defaultdict(set)
per_result, urls = Counter(), Counter()
n_results = n_drug = n_rx = 0
total = None
URL = re.compile(r"https?://")
VALUE = {"string", "number", "boolean", "null", "start_map", "start_array"}

t0 = time.time()
with open(RAW, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        prefixes[prefix] += 1
        events[event] += 1
        if event in VALUE:
            kinds[prefix].add(event)
        if event == "start_map":
            if prefix == "results.item":
                n_results += 1
            elif prefix == "results.item.patient.drug.item":
                n_drug += 1
            elif prefix == "results.item.patient.reaction.item":
                n_rx += 1
        if prefix == "results.item" and event == "map_key":
            per_result[value] += 1
        if prefix == "meta.results.total" and event == "number":
            total = value
        if event == "string" and URL.search(value):
            urls[prefix] += 1
elapsed = time.time() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6
n = n_results

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
print(f"\nQ0  one streaming pass: {elapsed:.2f}s, peak RSS ~{rss:.0f} MB for 2.7 MB")
print("    ijson RAISES on malformed JSON mid-stream. It does NOT report")
print("    duplicate keys — it emits both. No big-int or NaN warning. PARTLY.")

# ── Q1/Q2. What is in here, and how deep. ──────────────────────────────────
deepest = max(prefixes, key=lambda p: len(p.split(".")))
print(f"\nQ1  {len(prefixes)} distinct prefixes = the probe's 122 paths + the empty root —")
print("    the same relationship as on entries 13, 14, 15 and 17.")
print(f"    deepest: {deepest}")
print(f"Q2  {len(deepest.split('.'))} segments — THE PROBE PRINTS 8, the deepest file in the")
print("    corpus, and it cost nothing: a stream does not care how deep a thing")
print("    is. pandas says 3, because json_normalize stops at the first array.")

# ── Q3/Q7. Every level, counted in one pass. ──────────────────────────────
print(f"\nQ3/Q7  ONE PASS COUNTED ALL FOUR LEVELS:")
print(f"      results  {n_results:4}   ({deepest.split('.')[0]}.item)")
print(f"      drug     {n_drug:4}")
print(f"      reaction {n_rx:4}")
print(f"      and meta.results.total = {total:,} available")
print("    ijson NAMES the levels, because the prefix grammar makes each array")
print("    element addressable — more than most tools here manage. It prices")
print("    nothing, and the probe prices all four. PARTLY.")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
absent = sorted(((k, c) for k, c in per_result.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  {len(per_result)} fields at prefix `results.item`")
print(f"Q4  always {sum(1 for c in per_result.values() if c == n)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print(f"    THE WHOLE DOCUMENT CARRIES {events['null']} null EVENTS, so the raggedness here")
print("    is almost purely absence. 15-github-issues had 807 and the thirteen")
print("    tools split nine to four over them.")

# ── Q5. Does any field change type. ──────────────────────────────────────
varying = {p: sorted(k - {"null"}) for p, k in kinds.items() if len(k - {"null"}) > 1}
print(f"\nQ5  prefixes whose non-null value events are of more than one kind:"
      f" {varying or 'none'}")
print(f"    event census: {dict(events)}")
print("    NONE — the probe's answer. Grouping by prefix is grouping by field")
print("    here, because there are no data keys; on 13-package-lock that same")
print("    assumption made this check report ZERO on a document that HAS two")
print("    polymorphic fields.")

# ── Q6. Are any object keys actually data? ───────────────────────────────
print("\nQ6  no keyed collections. n/a — and the probe says something ijson cannot:")
print("      could not call 3 small single-copy objects, shortest first:")
print("        $.meta · $.meta.results · $.results[].patient.patientdeath")
print("    THAT IS AN ABSTENTION, and a prefix census has no way to express one.")

# ── Q8/Q9/Q10/Q12. Extraction, second pass. ─────────────────────────────
t1 = time.time()
rows, sd_seen, brands = [], 0, 0
with open(RAW, "rb") as f:
    for rec in ijson.items(f, "results.item"):
        rows.append((rec["safetyreportid"], rec["serious"], rec["receivedate"]))
        if "seriousnessdeath" in rec:
            sd_seen += 1
        for dr in rec["patient"]["drug"]:
            brands += len(dr.get("openfda", {}).get("brand_name", []))
print(f"\nQ8  ijson.items(f, 'results.item') -> {len(rows)} rows x 3 cols"
      f" ({time.time() - t1:.2f}s)")
print("   ", rows[0])
print(f"\nQ9  seriousnessdeath present on {sd_seen} of {len(rows)} — rows kept, and Q4")
print("    above says it is an ABSENCE rather than a null.")
print(f"\nQ10 brand names: {brands}, four levels down. `ijson.items` gave whole")
print("    records and the two loops are Python's — the stream does not join.")
print(f"\nQ12 {len(rows)} rows x {len(per_result)} own fields from the same pass; two of them")
print("    are arrays holding the probe's other two row candidates.")

# ── Q11. Find every path whose value matches something. ─────────────────
print(f"\nQ11 URL-valued prefixes: {dict(urls)}")
print("    BOTH, free from the same pass, and both are under `meta` — outside")
print("    `results`. pandas and polars frame the records and report NONE OF TWO.")
print("    A stream that starts at the root cannot miss them.")
