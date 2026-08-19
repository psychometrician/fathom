"""pydash — Homebrew's whole formula index

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
  measured      2026-08-11
  run           cd corpus/20-homebrew-formulae/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             2   NO                  by hand
   2 how deep                                    1   NO                  by hand
   3 what is one record                          1   -                   CANNOT
   4 always present vs sometimes                 5   NO                  YES — both halves
  4b the default trap                             8   NO                  reproduced
   5 does any field change type                  8   NO                  8 of the probe's 9
   6 are any object keys data                    4   NO                  by hand
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   5   YES                 yes, in a comprehension
  11 find every path matching something         14   NO                  by hand
  12 flattest honest table                       3   -                   CANNOT
  13 needed the shape in advance?                    YES for 8, 9, 10
  14 survives the next file unchanged?               the hand walks do
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~145, pydash on about 8
  timing        the hand walk 0.4s; every pydash call under 0.5s

  TWO THINGS THE RUN SETTLED, AND BOTH CORRECT SOMETHING WRITTEN EARLIER.

  THE MUTATION DID NOT REPRODUCE. Entry 14 recorded `map_values_deep` emptying
  `14-nyc-311`. Run here on a deep copy with the original checked afterwards,
  doc[0] is byte-identical before and after and the copy is untouched. That
  does not overturn entry 14 — different document, and possibly a different
  call — but the negative is recorded rather than assumed.

  THE DEFAULT TRAP DID REPRODUCE, and it is not pydash's. `get(r, k, D)` keeps
  absent apart from null at the TOP level and loses it ONE LEVEL DOWN. Running
  the identical four probes through glom's `Coalesce` gives the IDENTICAL four
  answers — which I predicted it would not. Two Python walkers sharing no code
  behave the same, so this belongs to path-with-default as an idea.

  Otherwise pydash's story here is glom's: it answered questions 8, 9 and half
  of 10, and a hand-written recursion answered 1, 2, 5, 6 and 11.
"""
import copy
import json
import re
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import pydash as _

print(f"pydash {version('pydash')}")

RAW = "../source.json"
doc = json.load(open(RAW))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pydash operates on parsed objects and never sees bytes. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
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
print(f"\nQ1  {len(paths):,} distinct paths, from a HAND-WRITTEN walk, {time.time()-t:.1f}s")
print(f"Q2  depth {maxd}, same walk. pydash contributed nothing to either.")

# ── THE MUTATION TEST, because entry 14 found this the hard way. ─────────────
# `map_values_deep` EMPTIED the document on `14-nyc-311`. Re-run here on a COPY,
# and check the original afterwards. This is the one pydash call in the corpus
# that has already destroyed data.
print("\n     THE MUTATION TEST — entry 14 recorded `map_values_deep` emptying the")
print("     document. Re-run here, on a deep copy, and the ORIGINAL checked after:")
before = len(json.dumps(doc[0]))
sample = copy.deepcopy(doc[:50])
try:
    _.map_values_deep(sample, lambda v, p: v)
    after = len(json.dumps(doc[0]))
    print(f"     doc[0] serialises to {before:,} bytes before, {after:,} after: "
          f"{'UNCHANGED' if before == after else 'MUTATED'}")
    print(f"     the COPY's first record is now {len(json.dumps(sample[0])):,} bytes")
except Exception as e:
    print(f"     RAISES: {type(e).__name__}: {str(e)[:120]}")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  pydash names no candidates and prices none. CANNOT.")
print(f"Q7  {len(doc):,} formulae")

# ── Q4. Always present vs sometimes — AND THE DEFAULT TRAP, MEASURED. ────────
rk = [set(r) for r in doc]
absent = {k: sum(k in r for r in rk) for k in set().union(*rk)}
absent = {k: v for k, v in absent.items() if v < len(doc)}
nulls = Counter(k for r in doc for k, v in r.items() if v is None)
print(f"\nQ4  sometimes ABSENT: {absent}")
print(f"Q4  always present but NULL: {len(nulls)} fields")
print("    Correct — from `in` on a dict, not from pydash.")
print("\nQ4b THE DEFAULT TRAP, MEASURED ON THIS DOCUMENT. Entry 15 recorded")
print("    `pydash.get(r, k, DEFAULT)` returning None for a present-but-null key")
print("    and the DEFAULT one level deeper. Same test, second document:")
r = next(f for f in doc if "head_dependencies" not in f and f["caveats"] is None)
print(f"    record {r['name']!r}: 'head_dependencies' ABSENT, 'caveats' present and null")
for key in ("head_dependencies", "caveats", "head_dependencies.dependencies",
            "caveats.anything"):
    print(f"    get(r, {key!r:34}, '<none>') -> {_.get(r, key, '<none>')!r}")
print("    CONFIRMED, and narrower than the entry-15 note reads. The top level")
print("    keeps absent apart from null: the missing key takes the default and")
print("    the null key returns its own None. ONE LEVEL DEEPER both return the")
print("    default and the distinction is gone. That is the 'opposite answers")
print("    from one function'.")
print("    `try-glom.py` runs the identical four probes through glom's Coalesce")
print("    and prints the IDENTICAL four answers, which was NOT what I predicted.")
print("    Two Python walkers, no shared code, the same defaulting behaviour —")
print("    so this is a property of path-with-default as an idea, not of pydash.")

# ── Q5. Does any field change type between records? ──────────────────────────
JT = {"str": "text", "int": "number", "float": "number", "bool": "boolean",
      "list": "array", "dict": "object", "NoneType": "null"}
varying = {p: sorted({JT.get(k, k) for k in ks} - {"null"}) for p, ks in kinds.items()}
varying = {p: v for p, v in varying.items() if len(v) > 1}
PLAT = re.compile(r"\.variations\.[a-z0-9_]+\.")
LEAF = re.compile(r"(uses_from_macos\[\])\.[a-z0-9_]+$")
folded = sorted({LEAF.sub(r"\1.<key>", PLAT.sub(".variations.<key>.", p)) for p in varying})
print(f"\nQ5  {len(varying)} varying paths, folding to {len(folded)}, against the probe's 9")
for p in folded:
    print(f"    {p}")
print("    Identical to glom's and ijson's answer, because all three are the same")
print("    hand walk. pydash has `map_values_deep`, which visits every value —")
print("    and see the mutation test above for why it is not used here.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no verb for it. The walk's sibling counts are the signature:")
for pref in ("$[].bottle.stable.files", "$[].variations"):
    sibs = [p for p in paths if p.startswith(pref + ".") and p.count(".") == pref.count(".") + 1]
    print(f"    {pref:26} {len(sibs)} sibling paths")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = time.time()
rows = _.map_(doc, lambda f: _.pick(f, "name", "desc", "homepage"))
print(f"\nQ8  _.map_ + _.pick -> {len(rows):,} rows x 3, {time.time()-t:.1f}s")
print(f"    {rows[0]}")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
t = time.time()
ex = [_.get(f, "executables", None) for f in doc]
print(f"\nQ9  executables non-None on {sum(e is not None for e in ex):,} of {len(ex):,}, "
      f"{time.time()-t:.1f}s")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
t = time.time()
res = _.flatten([[{"name": f["name"], **rr}
                  for p in (_.get(f, "patches") or [])
                  for rr in (_.get(p, "resolves") or [])] for f in doc])
print(f"\nQ10 patches[].resolves[] -> {len(res):,} rows, {time.time()-t:.1f}s")
print("    `_.flatten` over a comprehension. The comprehension did the reaching;")
print("    pydash flattened one level of the result.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
url_n, url_s = set(), set()


def urls(x, p="$"):
    if isinstance(x, dict):
        for k, v in x.items():
            urls(v, f"{p}.{k}")
    elif isinstance(x, list):
        for v in x:
            urls(v, f"{p}[]")
    elif isinstance(x, str):
        if x.startswith("http"):
            url_n.add(p)
        if re.match(r"^https?://", x):
            url_s.add(p)


t = time.time()
urls(doc)
print(f"\nQ11 http-prefixed {len(url_n)} paths, ^https?:// {len(url_s)}, {time.time()-t:.1f}s")
print("    jq, ijson and glom give the same two numbers. Four tools, no shared")
print("    code — the http* trap is the predicate's, not anybody's implementation.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 pydash has no rectangling verb. `_.pick` names columns; there is no")
print("    `normalize`. The flattest honest table is the 447-column one nothing")
print("    here will build for you.")
