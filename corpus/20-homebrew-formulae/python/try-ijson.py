"""ijson — Homebrew's whole formula index

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
  measured      2026-08-11
  run           cd corpus/20-homebrew-formulae/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   PARTLY
   1 what is in here                             2   NO                  yes — 1,132
   2 how deep                                    4   NO                  yes — 8
   3 what is one record                          2   NO                  CANNOT
   4 always present vs sometimes                 5   NO                  YES — both halves
   5 does any field change type                 20   NO                  8 of the probe's 9
   6 are any object keys data                   10   NO                  by hand
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 YES — presence, not NaN
  10 flatten the deepest array                   6   YES                 yes — 557, correct
  11 find every path matching something          6   NO                  yes — from the SAME pass
  12 flattest honest table                       3   -                   n/a, and honestly so
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 6, 7, 11
  14 survives the next file unchanged?               yes — the survey loop is generic
  15 readable a week later?                          the parse loop needs its comment
  16 lines, and how much is ceremony?                ~150, of which the one pass is 45
  timing        ONE PASS over 29.6 MB in 0.8s. Q8 0.2s, Q10 0.2s, all streamed

  ijson IS THE ONLY TOOL HERE THAT NEVER HOLDS THE DOCUMENT. Questions 1, 2, 4,
  5, 6, 7 and 11 all fall out of ONE 0.8-second pass in constant memory, and it
  is the only Python tool in this directory that read 29.6 MB without building
  anything. Its path count, 1,132, is the probe's exactly, and so is its depth.

  Q5 IS EIGHT OF THE PROBE'S NINE, after folding `variations.<platform>` by
  hand. The one it misses is `conflicts_with_reasons` — array vs array-of-text
  vs array-of-null — because ijson types by EVENT and an array of strings and
  an array of nulls are both `array`. Element typing is the resolution it does
  not have; everything coarser than that, it gets.

  ENTRY 13's DOT DEFECT DOES NOT FIRE HERE, and the negative is worth as much
  as the positive was. ijson's prefixes are dot-joined, so a key containing a
  dot is indistinguishable from nesting — measured at exactly 33 lost paths on
  `13-package-lock`. This document has ZERO keys containing a dot, and ijson's
  census is exact. THE DEFECT IS A PROPERTY OF THE DOCUMENT'S KEYS AND NOT OF
  THE TOOL'S SIZE OR THE FILE'S.
"""
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')} (backend {ijson.backend})")

RAW = "../source.json"

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  ijson is a PARSER and so is the only tool here that could answer")
print("    this. It does not: no duplicate-key report, no big-int report. It")
print("    would raise on truncation, which is more than pandas can say. PARTLY.")

# ── ONE PASS. Everything below comes out of this loop. ───────────────────────
t = time.time()
paths = Counter()          # folded prefix -> occurrences
types = defaultdict(set)   # folded prefix -> json types seen
depth_max = 0
depth_now = 0
n_records = 0
root_keys = Counter()      # key -> how many records carry it
root_nulls = Counter()     # key -> how many records write it as null
url_naive = Counter()
url_strict = Counter()
this_record = set()
dotted_keys = set()

import re
URL = re.compile(r"^https?://")

for prefix, event, value in ijson.parse(open(RAW, "rb")):
    if event in ("start_map", "start_array"):
        depth_now += 1
        depth_max = max(depth_max, depth_now)
    elif event in ("end_map", "end_array"):
        depth_now -= 1

    if prefix == "item" and event == "start_map":
        this_record = set()
    elif prefix == "item" and event == "end_map":
        n_records += 1
        root_keys.update(this_record)

    if event == "map_key":
        if "." in value:
            dotted_keys.add(value)
        continue

    if prefix:
        paths[prefix] += 1
        types[prefix].add(event)

    # root-level keys: prefix is exactly "item.<key>"
    if prefix.startswith("item.") and prefix.count(".") == 1:
        k = prefix.split(".", 1)[1]
        this_record.add(k)
        if event == "null":
            root_nulls[k] += 1

    if event == "string" and isinstance(value, str):
        if value.startswith("http"):
            url_naive[prefix] += 1
            if URL.match(value):
                url_strict[prefix] += 1

t_pass = time.time() - t
print(f"\n     ONE PASS over 29.6 MB: {t_pass:.1f}s, and nothing was retained but counters.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
print(f"\nQ1  {len(paths):,} distinct folded prefixes")
print(f"Q2  depth {depth_max} — counted from start_map/start_array nesting.")
print("    The probe says 8. ijson counts containers as it opens them, which is")
print("    the same definition, and it is the only tool here that gets depth")
print("    without either a schema or a hand-written recursion.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  ijson names no candidates and prices none. It COUNTS any you name.")
print(f"Q7  {n_records:,} formulae, counted while streaming")

# ── Q4. Always present vs sometimes — and null vs absent. ────────────────────
absent = {k: c for k, c in root_keys.items() if c < n_records}
print(f"\nQ4  root keys seen on fewer than every record: {absent}")
print(f"Q4  root keys written as null at least once: {len(root_nulls)}")
print("    BOTH, FROM ONE PASS, WITHOUT LOADING THE DOCUMENT. ijson sees the")
print("    `null` EVENT, so a written null and a missing key are different")
print("    things to it in a way they can never be to a frame.")

# ── Q5. Does any field change type between records? ──────────────────────────
# FIRST DRAFT DISCARDED start_map/start_array before comparing and reported 0,
# which blamed ijson for a filter I wrote. Container events ARE type information.
EV = {"start_map": "object", "start_array": "array"}
kinds = {p: {EV.get(t, t) for t in ts
             if t not in ("end_map", "end_array", "map_key")} - {"null"}
         for p, ts in types.items()}
varying = {p: sorted(k) for p, k in kinds.items() if len(k) > 1}
print(f"\nQ5  prefixes holding more than one non-null kind: {len(varying)}")
# ijson does NOT fold keys-as-data, so the same site is reported once per
# platform. Folding by hand — the probe does this itself — collapses them:
PLAT = re.compile(r"\.variations\.[a-z0-9_]+\.")
LEAF = re.compile(r"(uses_from_macos\.item)\.[a-z0-9_]+$")
folded = sorted({LEAF.sub(r"\1.<key>", PLAT.sub(".variations.<key>.", p))
                 for p in varying})
for p in folded:
    print(f"    {p}")
print(f"    {len(varying)} prefixes fold to {len(folded)}, against the probe's NINE, and")
print("    the fold is entirely `variations.<platform>` — the same keys-as-data")
print("    collapse the probe does and ijson's prefix scheme cannot.")
print("    THE ONE IT MISSES is `conflicts_with_reasons`, which the probe reports")
print("    as array vs array[1] text vs array[1] null. ijson types by EVENT, so")
print("    an array of strings and an array of nulls are both `array` — element")
print("    typing is exactly the resolution it does not have. Everything else in")
print("    the probe's list, including the headline uses_from_macos object-vs-")
print("    string, ijson finds — one level DOWN, at the element rather than the")
print("    field, which is where the change actually is.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  ijson folds array indices into `item` and does NOT fold object keys,")
print("    so a keyed collection appears as one prefix PER KEY. That is the")
print("    signature, and reading it is the analyst's job:")
fam = defaultdict(int)
for p in paths:
    m = re.match(r"^(item\.bottle\.stable\.files)\.([^.]+)$", p)
    if m:
        fam[m.group(1)] += 1
    m = re.match(r"^(item\.variations)\.([^.]+)$", p)
    if m:
        fam[m.group(1)] += 1
for k, v in sorted(fam.items()):
    print(f"    {k:34} {v} sibling prefixes — one per platform name")
print("    The probe folds each to a single `<key>` path and states a verdict.")

# ── THE DOT TEST, which is entry 13's defect. ────────────────────────────────
print(f"\n     KEYS CONTAINING A DOT: {len(dotted_keys)}")
if dotted_keys:
    print(f"     {sorted(dotted_keys)[:6]}")
    print("     Each of these is INDISTINGUISHABLE from nesting in a prefix, which")
    print("     is what cost ijson exactly 33 paths on `13-package-lock`.")
else:
    print("     NONE. Homebrew formula names are dot-free, so ijson's prefixes are")
    print("     invertible on this document and entry 13's defect does not fire.")
    print("     THE DEFECT IS A PROPERTY OF THE DOCUMENT'S KEYS, NOT THE FILE SIZE.")

# ── Q8/Q9/Q10. Extraction, streaming. ────────────────────────────────────────
t = time.time()
rows = [(f.get("name"), f.get("desc"), f.get("homepage"))
        for f in ijson.items(open(RAW, "rb"), "item")]
print(f"\nQ8  {len(rows):,} rows x 3, streamed in {time.time()-t:.1f}s")

t = time.time()
n_exec = sum(1 for f in ijson.items(open(RAW, "rb"), "item") if "executables" in f)
print(f"\nQ9  executables PRESENT on {n_exec:,} of {n_records:,} — `in` on the streamed")
print("    dict is presence, so ijson keeps the absent/null distinction here too.")

t = time.time()
res = [(f["name"], r["id"], r["type"])
       for f in ijson.items(open(RAW, "rb"), "item")
       for p in (f.get("patches") or [])
       for r in (p.get("resolves") or [])]
print(f"\nQ10 patches[].resolves[] -> {len(res):,} rows x 3, {time.time()-t:.1f}s")
print("    A python comprehension over streamed records. `or []` is the whole of")
print("    the raggedness handling, and it is what pandas needed a pre-filter for.")

# ── Q11. Find every path whose value matches something. ──────────────────────
print(f"\nQ11 FROM THE SAME PASS: {len(url_naive)} prefixes hold an http-prefixed string,")
print(f"    {len(url_strict)} hold a ^https?:// one. The {len(url_naive)-len(url_strict)} difference is the")
print("    formulae NAMED http* — httpd, httpie, http-server — and ijson falls")
print("    into it exactly as jq, pandas, polars and DuckDB do.")
print(f"    dropped: {sorted(set(url_naive) - set(url_strict))[:6]}")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 ijson has no table. It has EVENTS, and turning them into a table is")
print("    the loop above. What it buys is the only honest answer in this")
print(f"    directory to 'how much memory did that cost': {t_pass:.1f}s and no document.")
