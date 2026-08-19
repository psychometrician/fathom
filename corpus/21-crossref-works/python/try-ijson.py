"""ijson — Crossref works, 1,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
  measured      2026-08-11
  run           cd corpus/21-crossref-works/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   PARTLY
   1 what is in here                             1   NO                  yes — 236
   2 how deep                                    4   NO                  yes — 9
   3 what is one record                          1   -                   CANNOT
   4 always present vs sometimes                 4   NO                  YES — both halves
   5 does any field change type                 24  NO                   see below
   6 are any object keys data                    4   NO                  counts, no verdict
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 YES — presence
  10 flatten the deepest array                   5   YES                 yes — 18,155
  11 find every path matching something          4   NO                  yes — 13, from the
                                                                          SAME pass
  12 flattest honest table                       3   -                   n/a, honestly
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 6, 7, 11
  14 survives the next file unchanged?               yes — the pass is generic
  15 readable a week later?                          the parse loop needs its comment
  16 lines, and how much is ceremony?                ~130, the one pass is 40
  timing        ONE PASS over 7.5 MB in 0.2s. Every extraction under 0.1s

  ijson answers questions 1, 2, 4, 5, 6, 7 and 11 out of ONE 0.2-second pass in
  constant memory, on a file every frame in this directory loaded whole. Its 236
  paths and depth 9 are the probe's exactly, and it reached them without being
  told the records live at $.message.items — which pandas, polars and DuckDB all
  had to be told, and all three silently returned the 1-row ENVELOPE instead.

  QUESTION 5 EXPOSES A TENSION IN THE PROBE'S OWN RULES, and this file flags it
  rather than settling it. The probe reports exactly one type-changing site here:
  `issued.date-parts`, as `array[2] number x998, array[2] null x2`. The
  difference is ENTIRELY A NULL. Defect 11 and `design/axes.py` both say a null
  is not a type, and `varies()` discards a bare `array` beside `array[...]` while
  keeping `array[2] null` beside `array[2] number`. Under the corpus's own null
  rule ijson reports ZERO varying prefixes; counting nulls as a kind it reports
  exactly the probe's one site. WHETHER THE PROBE SHOULD REPORT IT IS THE
  AUTHOR'S QUESTION — what is measured here is that the two rules disagree.

  Entry 20 is the mirror. There ijson MISSED `conflicts_with_reasons`, because
  array-of-text against array-of-null is `start_array` either way. The event
  model sees LEAF types and not container contents, and this document happens to
  put its one type change on the side ijson can see.
import re
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')} (backend {ijson.backend})")

RAW = "../source.json"

print("\nQ0  ijson is a PARSER and could answer this; it does not. No duplicate-key")
print("    report, no big-int report. It WOULD raise on truncation. PARTLY.")

# ── ONE PASS. ────────────────────────────────────────────────────────────────
t = time.time()
paths, types = Counter(), defaultdict(set)
depth_max = depth_now = 0
n_records = 0
rec_keys, rec_nulls = Counter(), Counter()
url_n, url_s = set(), set()
this = set()
ITEM = "message.items.item"
URL = re.compile(r"^https?://")

for prefix, event, value in ijson.parse(open(RAW, "rb")):
    if event in ("start_map", "start_array"):
        depth_now += 1
        depth_max = max(depth_max, depth_now)
    elif event in ("end_map", "end_array"):
        depth_now -= 1
    if event == "map_key":
        continue
    if prefix:
        paths[prefix] += 1
        types[prefix].add(event)
    if prefix == ITEM and event == "start_map":
        this = set()
    elif prefix == ITEM and event == "end_map":
        n_records += 1
        rec_keys.update(this)
    if prefix.startswith(ITEM + ".") and prefix.count(".") == ITEM.count(".") + 1:
        k = prefix.rsplit(".", 1)[1]
        this.add(k)
        if event == "null":
            rec_nulls[k] += 1
    if event == "string" and isinstance(value, str):
        if value.startswith("http"):
            url_n.add(prefix)
        if URL.match(value):
            url_s.add(prefix)
t_pass = time.time() - t

print(f"\n     ONE PASS over 7.5 MB: {t_pass:.1f}s, nothing retained but counters.")
print(f"\nQ1  {len(paths)} distinct folded prefixes")
print(f"Q2  depth {depth_max} — the probe says 9, and ijson counts containers as")
print("    it opens them. It is the only tool here that reaches BOTH the answer")
print("    and the records without being told where the records are.")
print(f"\nQ3  ijson names no candidates and prices none. CANNOT.")
print(f"Q7  {n_records:,} works, counted while streaming")

absent = {k: c for k, c in rec_keys.items() if c < n_records}
print(f"\nQ4  {len(absent)} of {len(rec_keys)} record keys not on every work;"
      f" written null: {len(rec_nulls)}")
print("    Both halves from one pass. With zero written nulls the two answers")
print("    coincide, which is why every tool agrees on this document.")

EV = {"start_map": "object", "start_array": "array"}
kinds = {p: {EV.get(t, t) for t in ts if t not in ("end_map", "end_array", "map_key")} - {"null"}
         for p, ts in types.items()}
varying = {p: sorted(k) for p, k in kinds.items() if len(k) > 1}
print(f"\nQ5  prefixes holding more than one non-null kind: {len(varying)}")
for p in sorted(varying)[:6]:
    print(f"    {p}  {varying[p]}")
withnull = {p: sorted(k | ({"null"} if "null" in types[p] else set()))
            for p, k in kinds.items()
            if len(k | ({"null"} if "null" in types[p] else set())) > 1}
print(f"Q5  prefixes holding more than one kind INCLUDING null: {len(withnull)}")
for p in sorted(withnull)[:6]:
    print(f"    {p}  {withnull[p]}")
dpk = types.get("message.items.item.issued.date-parts.item.item", set())
print(f"\n    THE PROBE'S ONE SITE is $.message.items[].issued.date-parts, and it")
print("    reports it as `array[2] number x998, array[2] null x2`.")
print(f"    At the leaf, ijson sees events {sorted(dpk)} — so it FINDS the site,")
print("    and only in the second census above, the one that counts null as a kind.")
print("    ══ AND THAT IS WORTH FLAGGING RATHER THAN SETTLING HERE. ══")
print("    Defect 11 and `design/axes.py` both say A NULL IS NOT A TYPE, and this")
print("    document's ONLY reported type change is a difference that is entirely")
print("    a null: [[2018,11,3]] against [[null]]. The probe's `varies()` discards")
print("    a bare `array` beside `array[...]` and does NOT discard `array[2] null`")
print("    beside `array[2] number`, so the two rules point opposite ways on this")
print("    one site. Whether the probe should report it is the AUTHOR'S question;")
print("    what is measured here is that ijson reproduces it only by counting")
print("    nulls, and reports NOTHING under the rule the corpus otherwise applies.")
print("    Entry 20 is the mirror: there ijson MISSED `conflicts_with_reasons`")
print("    because array-of-text against array-of-null is `start_array` either")
print("    way. THE EVENT MODEL SEES LEAF TYPES AND NOT CONTAINER CONTENTS.")

refk = {p.rsplit(".", 1)[1] for p in paths
        if p.startswith("message.items.item.reference.item.")}
print(f"\nQ6  reference[] has {len(refk)} distinct child prefixes; the probe folds")
print(f"    them to one path at 18,155 copies and DECLINES the site as a")
print("    vocabulary. ijson does not fold object keys and judges nothing.")

t = time.time()
rows = [(w.get("DOI"), w.get("type"), w.get("publisher"))
        for w in ijson.items(open(RAW, "rb"), "message.items.item")]
print(f"\nQ8  {len(rows):,} rows x 3, streamed in {time.time()-t:.1f}s")
n_ab = sum(1 for w in ijson.items(open(RAW, "rb"), "message.items.item") if "abstract" in w)
print(f"\nQ9  abstract PRESENT on {n_ab} of {n_records:,} — `in` is presence")
t = time.time()
res = [(w["DOI"], r.get("key")) for w in ijson.items(open(RAW, "rb"), "message.items.item")
       for r in (w.get("reference") or [])]
print(f"\nQ10 reference[] -> {len(res):,} rows, {time.time()-t:.1f}s")
print("    `or []` is the whole raggedness guard, and the parent DOI is in scope.")
print("    pandas needed a pre-filter AND a meta_prefix and raised twice.")

print(f"\nQ11 FROM THE SAME PASS: {len(url_n)} prefixes hold an http-prefixed string,")
print(f"    {len(url_s)} hold a ^https?:// one. jq reports 13 strict.")
print("    NAIVE AND STRICT AGREE HERE, unlike entry 20 where fifteen formulae")
print("    were NAMED http*. The predicate's trap is a property of the document.")
print(f"\nQ12 no table, only events. What it buys is the honest memory answer:")
print(f"    {t_pass:.1f}s, one pass, no document held — on a file every frame in")
print("    this directory loaded whole.")
