"""glom — Homebrew's whole formula index

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
  measured      2026-08-11
  run           cd corpus/20-homebrew-formulae/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             3   NO                  by hand
   2 how deep                                    2   NO                  by hand
   3 what is one record                          2   -                   CANNOT
   4 always present vs sometimes                14   NO                  YES — both halves
   5 does any field change type                 12   NO                  8 of the probe's 9
   6 are any object keys data                    6   NO                  by hand
   7 how many records                            1   NO                  yes
   8 three named fields to a table               4   YES                 yes — its best answer
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   7   YES                 yes, in lambdas
  11 find every path matching something         14   NO                  by hand
  12 flattest honest table                       4   -                   CANNOT
  13 needed the shape in advance?                    YES for 8, 9, 10 — everything glom
                                                     itself did needed a path spelled
  14 survives the next file unchanged?               the hand walks do; the specs do not
  15 readable a week later?                          Q8 yes, Q10 no
  16 lines, and how much is ceremony?                ~140, and glom is on 12 of them
  timing        the hand walk 2.6s; every glom call under 0.2s

  THE HONEST SUMMARY IS THAT GLOM ANSWERED FOUR QUESTIONS AND THE RECURSION
  ANSWERED FIVE. glom is a SPEC language — "give me this" — and questions 1, 2,
  5, 6 and 11 all ask "what is here". Every one of them is a hand-written walk
  in this file, and that walk is the same twenty lines every Python attempt in
  this corpus keeps rewriting.

  ONE PREDICTION DIED IN THE RUN, TWICE, and it is the most useful line here.
  I first wrote that `Coalesce` collapses absent-vs-null the way entry 15
  measured `pydash.get(r, k, DEFAULT)` doing; the run said it does not. I then
  wrote that glom is therefore the exception among the walkers; running the
  identical four probes through pydash said IT IS NOT — glom and pydash print
  the same four answers.

  WHAT IS ACTUALLY TRUE, measured on one record of this document, in both:
      Coalesce("head_dependencies")             -> '<none>'   (absent)
      Coalesce("caveats")                       -> None       (present, null)
      Coalesce("head_dependencies.dependencies")-> '<none>'
      Coalesce("caveats.anything")              -> '<none>'   <- the distinction dies
  The top level keeps absent apart from null. One level deeper it does not.
  Entry 15 called this "opposite answers from one function" and named pydash
  and purrr; it is glom's behaviour too, and the corpus now has it on a second
  document in two libraries.

  Where glom is genuinely best is question 8: `glom(doc, [{"name": "name", …}])`
  is the table's own shape written down, which nothing else here manages.
  Question 10 is the counter-example — a path missing at two levels drops out
  of the spec language into lambdas and reads worse than a comprehension.

  Its Q11 numbers, 65 and 48, are jq's and ijson's exactly. Three tools, no
  shared code, identical answers, because the http* trap belongs to the
  predicate and not to any of them.
"""
import json
import time
from collections import Counter, defaultdict
from importlib.metadata import version

from glom import Coalesce, glom, Iter, T, SKIP

print(f"glom {version('glom')}")

RAW = "../source.json"
doc = json.load(open(RAW))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  glom is a specification language over an already-parsed object. It")
print("    never sees bytes. json.load did, silently. Answered CANNOT.")

# ── Q1/Q2. What is in here, and how deep — BY HAND. ──────────────────────────
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
print(f"\nQ1  {len(paths):,} distinct paths — from a HAND-WRITTEN recursion, {time.time()-t:.1f}s")
print(f"Q2  depth {maxd} — the same recursion. glom contributed nothing to either.")
print("    glom is a SPEC language, not a survey tool: it answers 'give me this',")
print("    never 'what is here'. Questions 1 and 2 are the Python half's refrain.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  glom names no candidates and prices none. CANNOT.")
print(f"Q7  {len(doc):,} formulae")

# ── Q4. Always present vs sometimes — THE ONE IT IS BUILT FOR. ───────────────
rk = [set(r) for r in doc]
absent = {k: sum(k in r for r in rk) for k in set().union(*rk)}
absent = {k: v for k, v in absent.items() if v < len(doc)}
nulls = Counter(k for r in doc for k, v in r.items() if v is None)
print(f"\nQ4  sometimes ABSENT: {absent}")
print(f"Q4  always present but NULL: {len(nulls)} fields")
print("    Both, correctly, because a dict is a dict and `in` is presence.")
print("    glom's own contribution is `Coalesce`, and entry 15's DEFAULT TRAP")
print("    reproduces here EXACTLY — one function, opposite answers:")
r = next(f for f in doc if "head_dependencies" not in f and f["caveats"] is None)
print(f"    record {r['name']!r}: 'head_dependencies' ABSENT, 'caveats' present and null")
for key in ("head_dependencies", "caveats", "head_dependencies.dependencies",
            "caveats.anything"):
    print(f"    Coalesce({key!r:34}, default='<none>') -> "
          f"{glom(r, Coalesce(key, default='<none>'))!r}")
print("    AT THE TOP LEVEL the default fires only for the MISSING key and a")
print("    present-but-null key returns its own None — so the distinction")
print("    survives. ONE LEVEL DEEPER both return the default, and the")
print("    difference is gone. Same verb, same record, two behaviours.")
print("    `try-pydash.py` runs the identical four probes and prints the")
print("    IDENTICAL four answers. Entry 15 recorded this of pydash and purrr;")
print("    glom has it too, and I predicted glom would be the exception.")

# ── Q5. Does any field change type between records? ──────────────────────────
JT = {"str": "text", "int": "number", "float": "number", "bool": "boolean",
      "list": "array", "dict": "object", "NoneType": "null"}
varying = {p: sorted({JT.get(k, k) for k in ks} - {"null"})
           for p, ks in kinds.items()}
varying = {p: v for p, v in varying.items() if len(v) > 1}
print(f"\nQ5  paths holding more than one non-null JSON type: {len(varying)}")
import re
PLAT = re.compile(r"\.variations\.[a-z0-9_]+\.")
LEAF = re.compile(r"(uses_from_macos\[\])\.[a-z0-9_]+$")
folded = sorted({LEAF.sub(r"\1.<key>", PLAT.sub(".variations.<key>.", p)) for p in varying})
for p in folded:
    print(f"    {p}")
print(f"    {len(varying)} paths fold to {len(folded)}, against the probe's NINE.")
print("    Same shape as ijson's answer and for the same reason: a hand walk")
print("    types by python class, so array-of-text and array-of-null are both")
print("    `array`. glom supplied none of this — the recursion above did.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  glom has no verb for this. The recursion's own path counter shows the")
print("    signature — one sibling path per platform name:")
for pref in ("$[].bottle.stable.files", "$[].variations"):
    sibs = [p for p in paths if p.startswith(pref + ".") and p.count(".") == pref.count(".") + 1]
    print(f"    {pref:26} {len(sibs)} sibling paths")
print("    Reading that as 'the keys are data' is the analyst's job in glom,")
print("    exactly as in jq, ijson and purrr.")

# ── Q8. Three named fields into a table. THE THING IT IS GOOD AT. ────────────
t = time.time()
spec = [{"name": "name", "desc": "desc", "homepage": "homepage"}]
rows = glom(doc, spec)
print(f"\nQ8  glom(doc, [{{...}}]) -> {len(rows):,} rows x 3, {time.time()-t:.1f}s")
print(f"    {rows[0]}")
print("    THE SPEC IS THE TABLE. This is glom's best question and it reads as")
print("    the answer's own shape, which no other tool here manages.")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
t = time.time()
ex = glom(doc, [Coalesce("executables", default=None)])
print(f"\nQ9  executables non-None on {sum(e is not None for e in ex):,} of {len(ex):,}, "
      f"{time.time()-t:.1f}s")
print("    `Coalesce(..., default=None)` keeps every row. Note it cannot tell you")
print("    the 185 are ABSENT rather than null — see Q4.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
t = time.time()
res = glom(doc, (Iter().map(lambda f: (f["name"], f.get("patches") or []))
                 .filter(lambda nf: nf[1]).all(),
                 [lambda nf: [{"name": nf[0], **r}
                              for p in nf[1] for r in (p.get("resolves") or [])]]))
flat = [r for group in res for r in group]
print(f"\nQ10 patches[].resolves[] -> {len(flat):,} rows, {time.time()-t:.1f}s")
print("    Note how much of that is lambdas. glom's spec language handles a path")
print("    that EXISTS; a path that is sometimes missing at two levels falls back")
print("    to python, and the result is less readable than the comprehension.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
naive = sorted({p for p, ks in kinds.items() if "str" in ks})
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
print(f"\nQ11 http-prefixed: {len(url_n)} paths; ^https?://: {len(url_s)}; {time.time()-t:.1f}s")
print(f"    dropped: {sorted(url_n - url_s)[:5]}…")
print("    Fifteen formulae are NAMED http*. Same trap, same numbers as jq and")
print("    ijson — and once again glom did none of the work; the walk did.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 glom builds exactly the table its spec names, so 'the flattest honest")
print("    table' means writing all 447 columns out. There is no `**` and no")
print("    auto-flatten. What it does buy: nothing is lost that you did not")
print("    choose to drop, which is the opposite failure from json_normalize's.")
