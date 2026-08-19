"""ijson — an npm lockfile, 1,657 packages keyed by install path

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   759 KB, 1,657 packages, depth 5
  measured      2026-08-11
  run           cd corpus/13-package-lock/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               4   -                   PARTLY
   1 what is in here                             7   NO                  NO — 16,546 prefixes
   2 how deep                                    3   NO                  YES
   3 what is one record                          3   NO                  CANNOT
   4 always present vs sometimes                 6   NO                  yes
   5 does any field change type                  9   NO                  NO — reports ZERO
   6 are any object keys data                    6   -                   NO
   7 how many records                            2   NO                  yes
   8 three named fields to a table               5   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   4   YES                 PARTLY
  11 find every path matching something          5   NO                  NO — 1,974 paths
  12 flattest honest table                       4   NO                  yes
  13 needed the shape in advance?                    NO for 0,1,2,4,7
  14 survives the next file unchanged?               yes for those
  15 readable a week later?                          the prefix grammar needs a comment
  16 lines, and how much is ceremony?                ~140, and one pass does most of it

**THE FINDING IS A SILENT FALSE NEGATIVE ON QUESTION 5, AND IT IS THE SHARPEST
THING IN THIS DIRECTORY.** Grouping event kinds by prefix is exactly how this
file answered question 5 on `14-nyc-311`, correctly and cheaply. Here it reports:

    prefixes whose value events are of more than one kind ....... 0

**Zero, on a document with two polymorphic fields.** `engines` is an object on
1,050 packages and an array on 1; `funding` is an object on 282 and an array on
28. But **each package's `engines` lives at its own prefix** —
`packages.node_modules/foo.engines` — so no prefix ever sees two kinds. The
census is not wrong about any prefix. It is wrong about the document, and it
says so with a confident zero.

**Folding the keyed collections to `<key>` first turns 0 into 3** — `engines`,
`funding`, and `funding.item` (object on 26, text on 2). That fold is 12 lines
here and is not ijson's; the probe does it unasked and prints both fields under
`FIELDS THAT CHANGE TYPE`.

**AND THE FOLD CANNOT BE WRITTEN CORRECTLY, WHICH IS THE DEEPER PROBLEM.**
An ijson prefix is a **dot-joined string**, and **33 of this document's package
keys contain a dot** — `node_modules/@nodelib/fs.scandir`, `object.assign`,
`bn.js`. So `packages.node_modules/@nodelib/fs.scandir.resolved` splits into
four segments, of which `scandir` looks like a field. **The prefix cannot be
parsed back into the path that produced it.**

The damage is measured below rather than asserted: the folded URL census
reports `resolved` **1,623 times when the truth is 1,656**, and the missing
**33 are exactly the 33 dotted keys**, scattered into invented paths like
`packages.<key>.scandir.resolved`. Question 5's verdict survived this only by
luck — the one array-valued `engines` and all 28 array-valued `funding` sit on
undotted keys, while **37 observations on dotted keys were misfiled**. Had the
single polymorphic `engines` been on a dotted package, the fold would have
reported it as varying nowhere.

**THIS IS THE SAME FAILURE AS pandas' DOTTED COLUMN NAMES, IN A COMPLETELY
DIFFERENT TOOL.** Both join a path with `.`; both meet data containing `.`; both
produce a string nobody can invert. It is a property of the representation, not
of either library.

**QUESTION 1 FAILS THE SAME WAY, LOUDLY INSTEAD OF QUIETLY.** 16,546 distinct
prefixes — the probe's 16,545 raw paths plus the empty root, so ijson is exactly
right and exactly useless. **A prefix grammar with no way to say "this segment
is data" cannot describe a keys-as-data document**, and one whose separator
occurs inside the keys cannot even be repaired downstream.

**WHAT IS STILL EXCELLENT IS THE COST.** One streaming pass answering Q0, Q1,
Q2, Q4, Q7 and Q11 costs about **0.2 s and 24 MB** — printed below — and it
never builds the document. But note what that buys here versus on entry 14:
there, seven correct answers; here, two of the six are the explosion.

**Only ONE number appears in the whole 759 KB file** — `lockfileVersion: 3`.
10,708 strings, 1,526 booleans, one number. The event census says so directly.
"""
import re
import resource
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')} (backend: {ijson.backend})")

RAW = "../source.json"
KEYED = ("dependencies", "devDependencies", "optionalDependencies",
         "peerDependencies", "peerDependenciesMeta", "bin")


def fold(prefix):
    """`packages.node_modules/foo.engines` -> `packages.<key>.engines`."""
    segs, out, i = prefix.split("."), [], 0
    while i < len(segs):
        s = segs[i]
        out.append(s)
        if s == "packages" or s in KEYED:
            if i + 1 < len(segs):
                out.append("<key>")
                i += 1
        i += 1
    return ".".join(out)


# ── ONE PASS answers Q0, Q1, Q2, Q4, Q7 and Q11. ─────────────────────────────
prefixes, events = Counter(), Counter()
kinds, folded_kinds = defaultdict(set), defaultdict(set)
per_package, urls_raw, urls_folded = Counter(), Counter(), Counter()
n_packages = 0
URL = re.compile(r"https?://")
VALUE = {"string", "number", "boolean", "null", "start_map", "start_array"}

t0 = time.time()
with open(RAW, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        prefixes[prefix] += 1
        events[event] += 1
        if event in VALUE:
            kinds[prefix].add(event)
            folded_kinds[fold(prefix)].add(event)
        if event == "map_key" and prefix == "packages":
            n_packages += 1
        if event == "map_key" and prefix.startswith("packages.") \
                and prefix.count(".") == 1:
            per_package[value] += 1
        if event == "string" and URL.search(value):
            urls_raw[prefix] += 1
            urls_folded[fold(prefix)] += 1
elapsed = time.time() - t0
rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print(f"\nQ0  one streaming pass: {elapsed:.1f}s, peak RSS ~{rss:.0f} MB")
print("    ijson RAISES on malformed JSON mid-stream. It does NOT report")
print("    duplicate keys — it emits both. No big-int or NaN warning. PARTLY.")
print("    DuckDB refuses this file outright; ijson reads it without complaint.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
folded_paths = {fold(p) for p in prefixes if p}
print(f"\nQ1  {len(prefixes):,} distinct prefixes — the probe's 16,545 paths plus")
print("    the empty root, so ijson is EXACTLY RIGHT and exactly useless.")
print(f"    folded to <key> by hand: {len(folded_paths)} paths")
print(f"    example: {[p for p in prefixes if p.count('.') >= 3][0]}")
print("    Note the double dot — the root package's key is the empty string.")
print("    A prefix grammar has no way to say 'this segment is data'. NO.")
print("\nQ1  AND THE FOLD ABOVE IS NOT TRUSTWORTHY. A prefix is a DOT-JOINED")
print("    string and 33 package keys contain a dot, so the path cannot be")
print("    recovered by splitting. Q11 below measures the damage exactly.")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
deepest = max(prefixes, key=lambda p: len(p.split(".")))
print(f"\nQ2  deepest prefix has {len(deepest.split('.'))} segments — the probe prints 5. Correct,")
print("    and this is the one survey question keys-as-data does not corrupt,")
print("    because depth counts segments rather than distinguishing them.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  ijson names no candidate here. On 14-nyc-311 the `item` prefix made")
print("    the array element addressable; a keyed collection has no `item`, so")
print("    every package is its own prefix and none of them is 'the record'.")
print("    The probe names EIGHT candidates with costs. CANNOT.")
print(f"Q7  {n_packages:,} packages, counted from map_key events at prefix `packages`")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
always = [k for k, c in per_package.items() if c == n_packages]
some = sorted(((k, c) for k, c in per_package.items() if c < n_packages),
              key=lambda kv: kv[1])
print(f"\nQ4  {len(per_package)} field names over {sum(per_package.values()):,} occurrences")
print(f"Q4  always {len(always)} — {always}")
print(f"Q4  sometimes {len(some)}, rarest five: {some[:5]}")
print("    Correct, and it needed the prefix DEPTH to be filtered by hand —")
print("    `prefix.count('.') == 1` is how you say 'a field of a package'.")

# ── Q5. Does any field change type? THE SILENT FALSE NEGATIVE. ──────────────
raw_varying = {p: sorted(k) for p, k in kinds.items() if len(k) > 1}
fold_varying = {p: sorted(k) for p, k in folded_kinds.items() if len(k) > 1}
print(f"\nQ5  prefixes whose value events are of more than one kind: {len(raw_varying)}")
print("    ZERO, ON A DOCUMENT WITH TWO POLYMORPHIC FIELDS. Each package's")
print("    `engines` sits at its own prefix, so no prefix ever sees two kinds.")
print("    The census is right about every prefix and wrong about the document.")
print(f"\nQ5  after folding the keyed collections: {len(fold_varying)} paths vary")
for p, k in fold_varying.items():
    print(f"      {p:34} {k}")
print("    The probe prints:")
print("      engines  object x1,050, array[1] text x1")
print("      funding  object x282, array[1] object x26, array[1] text x2")
print("    THE FOLD IS WHAT MAKES THE QUESTION ANSWERABLE, and it is not ijson's.")
print("    This same code was CORRECT on 14-nyc-311, which had no keys-as-data.")
print("    AND THE RIGHT ANSWER HERE IS LUCK. The one array-valued `engines` and")
print("    all 28 array-valued `funding` sit on keys WITHOUT a dot; 37")
print("    observations on dotted keys were misfiled into invented paths. Had")
print("    the single polymorphic `engines` been on a dotted package, this line")
print("    would report it as varying nowhere.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  YES — `packages` and four nested collections — and ijson cannot say")
print("    so. It reports the keys as prefix segments, which is the failure")
print("    rather than the answer: 16,546 prefixes for 34 real paths.")
print(f"    events: {dict(events)}")
print(f"    ONLY ONE NUMBER in the whole 759 KB file — lockfileVersion. 10,708")
print("    strings and 1,526 booleans. The census says that outright, and it is")
print("    the one place ijson's flat view beats every frame in this directory.")

# ── Q8/Q9/Q10/Q12. Extraction — a second pass with ijson.kvitems. ───────────
t1 = time.time()
rows, lic_seen, fund_rows = [], 0, []
with open(RAW, "rb") as f:
    for path, rec in ijson.kvitems(f, "packages"):
        rows.append((path or "<root>", rec.get("version"), rec.get("license")))
        if "license" in rec:
            lic_seen += 1
        fu = rec.get("funding")
        if isinstance(fu, list):
            fund_rows += [{"pkg": path, **(e if isinstance(e, dict) else {"url": e})}
                          for e in fu]
print(f"\nQ8  ijson.kvitems(f, 'packages') -> {len(rows):,} rows in {time.time() - t1:.1f}s")
print("   ", rows[1])
print("    `kvitems` IS the right verb for a keyed collection — it yields")
print("    (key, value) pairs, so the install path survives as data. jmespath's")
print("    `values()` loses it entirely.")
print(f"\nQ9  license present on {lic_seen:,} of {len(rows):,} — rows kept, `.get` gives None")
print(f"\nQ10 funding[] -> {len(fund_rows)} rows")
print("   ", fund_rows[0])
print("    PARTLY: the isinstance tests are Python's, because `funding` is")
print("    object-or-array and its elements are object-or-string.")

# ── Q11. Find every path whose value matches something. ──────────────────────
TRUE_URL_PATHS = {"packages.<key>.resolved": 1656, "packages.<key>.funding.url": 282,
                  "packages.<key>.funding.item.url": 53, "packages.<key>.deprecated": 8,
                  "packages.<key>.funding.item": 4}
print(f"\nQ11 {sum(urls_raw.values()):,} URL values")
print(f"    as prefixes:      {len(urls_raw):,} distinct paths")
print(f"    folded by hand:   {len(urls_folded)} paths — and the truth is 5.")
bogus = {p: c for p, c in urls_folded.items() if p not in TRUE_URL_PATHS}
print(f"    of those, {len(bogus)} are INVENTED, holding {sum(bogus.values())} values:")
print(f"      e.g. {list(bogus)[:3]}")
print(f"    `resolved` reports {urls_folded['packages.<key>.resolved']:,} where the truth is 1,656 —")
print(f"    short by exactly {1656 - urls_folded['packages.<key>.resolved']}, which is the number of package keys")
print("    containing a dot. THE PREFIX CANNOT BE SPLIT BACK INTO A PATH.")
print("    Free from the same pass, and 1,974 lines long unfolded — and the fold")
print("    is unsound. Same root cause as pandas' dotted column names. NO.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print(f"\nQ12 {len(rows):,} rows x 21 scalar fields, with the install path as the key")
print("    column — kvitems makes that the natural shape, which is more than")
print("    most tools here manage. The four keyed collections inside are still")
print("    separate tables the probe prices at 2,841, 128, 104 and 101 rows.")
