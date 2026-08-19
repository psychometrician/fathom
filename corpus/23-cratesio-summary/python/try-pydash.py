"""pydash — crates.io summary

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   41 KB, six collections at the root, depth 4
  measured      2026-08-11
  run           cd corpus/23-cratesio-summary/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             3   NO                  by hand — 140
   2 how deep                                    1   NO                  by hand — 4
   3 what is one record                          14  NO                  computed, not volunteered
   4 always present vs sometimes                  8  NO                  YES — three always-null
   5 does any field change type                   4  NO                  NONE, correctly
   6 are any object keys data                     1  -                   n/a
   7 how many records                              2 NO                  THREE answers
   8 three named fields to a table                 3 YES                 yes
   9 a field missing from some rows                4 YES                 yes
  10 flatten the deepest array                     5 -                   NO ARRAY TO FLATTEN
  11 find every path matching something           14 NO                  by hand — 11, folds to 3
  12 flattest honest table                         3 -                   CANNOT
  13 needed the shape in advance?                    YES for 8, 9
  14 survives the next file unchanged?               the hand walks do
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~118, pydash on about 5

  THE DEFECT-25 DOCUMENT, and pydash's story is glom's: the hand recursion
  answers 1, 2, 5 and 11, the library answers 8 and 9, and the four-collections-
  one-shape fact has to be computed on purpose.

  THE OVERLAP IS THE THING NOBODY REPORTS: 40 crate rows, 33 distinct crates,
  seven crates in two collections each — and the probe does not report it either.

  QUESTION 10 HAS NO TARGET: there is no array below the collections at all.
"""
import json
import re
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import pydash as _

print(f"pydash {version('pydash')}")

RAW = "../source.json"
doc = json.load(open(RAW))
CRATE = ["new_crates", "most_downloaded", "most_recently_downloaded", "just_updated"]
crates = [c for k in CRATE for c in doc[k]]

print("\nQ0  operates on a parsed object; json.load read the bytes silently. CANNOT.")

paths, kinds = Counter(), defaultdict(set)
maxd = 0


def walk(x, p="$", d=0):
    global maxd
    maxd = max(maxd, d)
    if isinstance(x, dict):
        for k, v in x.items():
            paths[f"{p}.{k}"] += 1
            kinds[f"{p}.{k}"].add(type(v).__name__)
            walk(v, f"{p}.{k}", d + 1)
    elif isinstance(x, list):
        for v in x:
            paths[f"{p}[]"] += 1
            kinds[f"{p}[]"].add(type(v).__name__)
            walk(v, f"{p}[]", d + 1)


t = time.time()
walk(doc)
print(f"\nQ1  {len(paths)} distinct paths — hand-written recursion, {time.time()-t:.2f}s")
print(f"Q2  depth {maxd} — the probe says 140 paths and depth 4.")
print(f"Q1  the root is an OBJECT of {len(doc)} keys: {list(doc)}")

# ── Q3. THE FOUR-IN-ONE, and the overlap. ──────────────────────────────────
sigs = {k: tuple(sorted(doc[k][0])) for k in CRATE}
print(f"\nQ3  distinct key-sets across the four crate collections: {len(set(sigs.values()))}")
allsig = {tuple(sorted(c)) for c in crates}
print(f"Q3  over all {len(crates)} crate records: {len(allsig)} distinct key-set(s)")
print("    ONE. The four collections are one shape, and computing that took a")
print("    deliberate `set` of sorted key tuples. The probe prints")
print("    `same shape as $.new_crates[]` unasked — defect 25's repair — and")
print("    NO TOOL IN THIS DIRECTORY VOLUNTEERS IT.")
ids = [c["id"] for c in crates]
dups = sorted(n for n, k in Counter(c["name"] for c in crates).items() if k > 1)
print(f"\n     THE OVERLAP: {len(ids)} rows, {len(set(ids))} DISTINCT crates.")
print(f"     appearing twice: {dups}")
print("     Seven crates are in more than one collection, so concatenating the")
print("     four — the obvious move once you know they share a shape — silently")
print("     double-counts them. THE PROBE DOES NOT REPORT THIS EITHER.")

# ── Q4. ────────────────────────────────────────────────────────────────────
rk = [set(c) for c in crates]
absent = [k for k in set().union(*rk) if sum(k in c for c in rk) < len(crates)]
nulls = Counter(k for c in crates for k, v in c.items() if v is None)
allnull = sorted(k for k, n in nulls.items() if n == len(crates))
print(f"\nQ4  crate fields sometimes ABSENT: {len(absent)} — every crate has all 23")
print(f"Q4  written NULL: {dict(nulls)}")
print(f"Q4  NULL ON ALL {len(crates)}: {allnull}")
print("    Three fields the API always returns and never fills. A field with")
print("    ONE type — null — is exactly the case entry 20 found tidyjson")
print("    turning on, and this document has three of them.")

# ── Q5/Q6. ─────────────────────────────────────────────────────────────────
JT = {"str": "text", "int": "number", "float": "number", "bool": "boolean",
      "list": "array", "dict": "object", "NoneType": "null"}
varying = {p: sorted({JT.get(k, k) for k in ks} - {"null"}) for p, ks in kinds.items()}
varying = {p: v for p, v in varying.items() if len(v) > 1}
print(f"\nQ5  paths with more than one non-null type: {len(varying)} — the probe says NONE")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
print(f"\nQ7  num_crates {doc['num_crates']:,}; num_downloads {doc['num_downloads']:,};")
print(f"    {len(crates)} crate rows here, of which {len({c['id'] for c in crates})} are DISTINCT.")

# ── Q8/Q9/Q10. ─────────────────────────────────────────────────────────────
t = time.time()
rows = _.map_(doc["new_crates"], lambda c: _.pick(c, "name", "max_version", "downloads"))
print(f"\nQ8  _.map_ + _.pick -> {len(rows)} rows x 3, {time.time()-t:.2f}s")
hp = [_.get(c, "homepage", "<absent>") for c in crates]
print(f"\nQ9  `homepage`: {sum(h is None for h in hp)} None, "
      f"{sum(h == '<absent>' for h in hp)} defaulted, of {len(hp)}")
print("    THE DEFAULT NEVER FIRES — every crate HAS the key and 19 write null,")
print("    so `get` returns the null itself. `../../22-dockerhub-tags/r/`")
print("    measured purrr's `pluck` doing the OPPOSITE on the same test; this")
print("    is the third document on which the two disagree.")
print("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. The deepest structure is")
print("    `links`, an object of six fields. Question 10 has no target on this")
print("    document, which is the first time in the corpus that is true.")
links = [{"crate": c["name"], "link": k, "url": v} for c in crates for k, v in c["links"].items()]
print(f"    flattening `links` instead: {len(links)} rows x 3")

# ── Q11. ───────────────────────────────────────────────────────────────────
url = set()


def urls(x, p="$"):
    if isinstance(x, dict):
        for k, v in x.items():
            urls(v, f"{p}.{k}")
    elif isinstance(x, list):
        for v in x:
            urls(v, f"{p}[]")
    elif isinstance(x, str) and re.match(r"^https?://", x):
        url.add(p)


urls(doc)
# The walk builds `$.just_updated[].homepage`, so the fold must match the `[]`
# too. The first draft's pattern ended at the dot and folded nothing — 11 -> 11.
fold = sorted({re.sub(r"^\$\.(new_crates|most_downloaded|most_recently_downloaded|just_updated)\[\]\.",
                      "$.<one of the four>[].", p) for p in url})
print(f"\nQ11 {len(url)} distinct URL paths, folding to {len(fold)} once the four")
print(f"    identical collections are collapsed: {fold}")
print("    pydash has `map_values_deep`, which entry 14 recorded EMPTYING a")
print("    document and entry 20 could not reproduce. Not used here.")

print("\nQ12 no rectangling verb here. The honest table is the four lists")
print("    concatenated — 40 rows holding 33 distinct crates — or four tables of")
print("    ten that nothing will tell you are the same shape.")
