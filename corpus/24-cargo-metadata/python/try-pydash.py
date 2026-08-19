"""pydash — cargo metadata for this repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   27 KB, 8 packages, depth 8
  measured      2026-08-11
  run           cd corpus/24-cargo-metadata/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             3   NO                  by hand — 143
   2 how deep                                    1   NO                  by hand — 8
   3 what is one record                          3   -                   CANNOT
   4 always present vs sometimes                 8   NO                  YES — four always-null
   5 does any field change type                  8   NO                  ZERO, with the rule
   6 are any object keys data                   12   NO                  the ingredients only
   7 how many records                             2  NO                  yes — two questions
   8 three named fields to a table                3 YES                 yes
   9 a field missing from some rows                3 YES                 yes
  10 flatten the deepest array                     6 YES                 yes
  11 find every path matching something           14 NO                  by hand — 5
  12 flattest honest table                         3 -                   CANNOT
  13 needed the shape in advance?                    YES for 8, 9, 10
  14 survives the next file unchanged?               the hand walks do
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~112, pydash on about 5

  pydash's story is glom's on the last entry as on the first four: the hand
  recursion answers 1, 2, 5, 6 and 11 and the library answers 8 and 9.

  WHAT THIS DOCUMENT ADDS is that its keys-as-data site's keys are ALSO its
  hyphenated names — 14 of 28 feature names contain one. A walker pays nothing
  for either, which is why it neither breaks nor decides.

  `_.get(p, "description", D)` returns the NULL, not the default, on the two
  packages that write one — the behaviour glom shares and purrr does not.
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
pkgs = doc["packages"]

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
print(f"\nQ1  {len(paths)} distinct paths — hand-written recursion, {time.time()-t:.3f}s")
print(f"Q2  depth {maxd} — the probe says 143 paths and depth 8, in 27 KB.")
print(f"Q1  the root is an OBJECT of {len(doc)} keys")

# ── Q6. THE CENTREPIECE. ───────────────────────────────────────────────────
feats = Counter(k for p in pkgs for k in p["features"])
once = [k for k, n in feats.items() if n == 1]
hy = [k for k in feats if "-" in k]
print(f"\nQ6  $.packages[].features — THE PROBE CALLS THESE KEYS DATA.")
for p in pkgs:
    print(f"    {p['name']:16} {len(p['features']):>2} features")
print(f"Q6  {len(feats)} distinct feature names over {len(pkgs)} packages;"
      f" {len(once)} appear ONCE")
print(f"Q6  {len(hy)} of them contain a HYPHEN — {sorted(hy)[:4]} …")
print("    THE ESCAPING HAZARD AND THE KEYS-AS-DATA SITE ARE THE SAME KEYS.")
print("    Entries 21 and 23 met hyphens on genuine FIELD names; here they are")
print("    VALUES. A walker pays nothing for either — a dict key is a string —")
print("    which is exactly why it also states no verdict.")

# ── Q3/Q4/Q5/Q7. ───────────────────────────────────────────────────────────
print(f"\nQ3  no candidates named and none priced. CANNOT.")
print(f"    the probe prices NINE; its widest is 8 x 57 at 63% empty, and 28 of")
print(f"    those 57 columns would be feature names.")
rk = [set(p) for p in pkgs]
absent = [k for k in set().union(*rk) if sum(k in p for p in rk) < len(pkgs)]
nulls = {k: sum(1 for p in pkgs if p.get(k) is None) for k in set().union(*rk)}
alln = sorted(k for k, v in nulls.items() if v == len(pkgs))
print(f"\nQ4  fields sometimes ABSENT: {len(absent)} — every package has all {len(rk[0])} keys")
print(f"Q4  written NULL: {len([k for k, v in nulls.items() if v])}; "
      f"NULL ON ALL {len(pkgs)}: {alln}")
print("    FOUR FIELDS `cargo metadata` ALWAYS EMITS AND NEVER FILLS. A field")
print("    that is never anything but null has ONE type — entries 20, 22 and 23")
print("    pinned that, and this document has four.")

JT = {"str": "text", "int": "number", "float": "number", "bool": "boolean",
      "list": "array", "dict": "object", "NoneType": "null"}
loose = {p: sorted({JT.get(k, k) for k in ks} - {"null"}) for p, ks in kinds.items()}
loose = {p: v for p, v in loose.items() if len(v) > 1}
tight = {p: v for p, v in loose.items()
         if len([x for x in v if x != "array"]) > 1 or "array" not in v}
print(f"\nQ5  paths with more than one non-null type: {len(loose)}")
print(f"Q5  + AN EMPTY ARRAY IS NOT A TYPE:                 {len(tight)}")
print("    ZERO, and the probe says NONE. Everything the loose census flags is")
print("    an optional list that is sometimes empty. ENTRY 20's LADDER ON A")
print("    DOCUMENT WITH NOTHING ELSE TO FIND — the rule does all of the work.")
print(f"\nQ7  {len(pkgs)} packages, {len(doc['workspace_members'])} workspace members,"
      f" {len(doc['resolve']['nodes'])} resolve nodes — two questions, not three")

# ── Q8/Q9/Q10/Q11/Q12. ─────────────────────────────────────────────────────
t = time.time()
rows = _.map_(pkgs, lambda p: _.pick(p, "name", "version", "edition"))
print(f"\nQ8  _.map_ + _.pick -> {len(rows)} rows x 3, {time.time()-t:.3f}s")
d = [_.get(p, "description", "<absent>") for p in pkgs]
print(f"\nQ9  `description`: {sum(x is None for x in d)} None, "
      f"{sum(x == '<absent>' for x in d)} defaulted, of {len(d)}")
print("    THE DEFAULT NEVER FIRES — every package HAS the key and two write")
print("    null. `../r/try-purrr.R` runs the same test and `pluck` returns the")
print("    DEFAULT instead. Fourth document on which the two disagree.")
deep = [(n["id"], dk) for n in doc["resolve"]["nodes"]
        for d in n["deps"] for dk in d["dep_kinds"]]
tg = [(p["name"], t_["name"]) for p in pkgs for t_ in p["targets"]]
print(f"\nQ10 targets[] -> {len(tg)} rows; the DEEPEST array is")
print(f"    resolve.nodes[].deps[].dep_kinds[] at {len(deep)} rows, depth 6 —")
print("    and it is NOT under `packages`, so a frame built from packages")
print("    cannot reach it at all.")

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
print(f"\nQ11 {len(url)} distinct URL paths: {sorted(url)}")

print("\nQ12 no rectangling verb here. The honest table is question 3's, and")
print("    this document's widest candidate is 63% empty because `features`")
print("    spreads into a column per feature name — question 6 paid in width.")
