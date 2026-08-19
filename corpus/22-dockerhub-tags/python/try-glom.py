"""glom — Docker Hub tags, 100 tags

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   476 KB, 100 tags under $.results, depth 5
  measured      2026-08-11
  run           cd corpus/22-dockerhub-tags/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             2   NO                  by hand — 33
   2 how deep                                    1   NO                  by hand — 5
   3 what is one record                           4  -                   CANNOT
   4 always present vs sometimes                  8  NO                  YES — three states
   5 does any field change type                   4  NO                  NONE, correctly
   6 are any object keys data                     1  -                   n/a
   7 how many records                              2 NO                  yes, both numbers
   8 three named fields to a table                 4 YES                 yes — its best answer
   9 a field missing from some rows                3 YES                 yes
  10 flatten the deepest array                     4 YES                 yes — 1,388
  11 find every path matching something           14 NO                  by hand — 1
  12 flattest honest table                         3 -                   CANNOT
  13 needed the shape in advance?                    YES for 8, 9, 10
  14 survives the next file unchanged?               the hand walks do
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~120, glom on about 8

  THE NESTED CONTROL, and glom behaves exactly as it did on entries 20 and 21:
  the hand recursion answered questions 1, 2, 5 and 11, and glom answered 8, 9
  and half of 10. Nothing about a regular document changes that division — which
  is the point of running a control.

  What this document adds is THREE STATES OF EMPTY in the images table — absent,
  null, and empty string — and the probe's headline 16% counts only the nulls.
"""
import json
import re
import time
from collections import Counter, defaultdict
from importlib.metadata import version

from glom import Coalesce, glom

print(f"glom {version('glom')}")

RAW = "../source.json"
doc = json.load(open(RAW))
tags = doc["results"]
images = [im for t in tags for im in t["images"]]

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
print(f"\nQ1  {len(paths)} distinct paths — hand-written recursion, {time.time()-t:.1f}s")
print(f"Q2  depth {maxd} — same recursion. The probe says 33 paths and depth 5.")

print("\nQ3  no candidates named and none priced. CANNOT.")
print(f"    the two the probe prices: {len(tags)} tags x 16 at 0% empty, and")
print(f"    {len(images):,} images x 11 at 16% empty with `size` repeated 4x.")
print(f"Q7  {len(tags)} tags on this page; `count` says {doc['count']:,} on the server,")
print(f"    and `next` is a URL — the document says outright that it is a PAGE.")

# ── Q4. THE THREE STATES. ──────────────────────────────────────────────────
tk = [set(t) for t in tags]
absent = [k for k in set().union(*tk) if sum(k in t for t in tk) < len(tags)]
inull = Counter(k for im in images for k, v in im.items() if v is None)
iempty = Counter(k for im in images for k, v in im.items() if v == "")
print(f"\nQ4  tag fields sometimes ABSENT: {len(absent)} — every tag has all 16 keys")
print(f"Q4  image fields written NULL:         {dict(inull)}")
print(f"Q4  image fields written EMPTY STRING: {dict(iempty)}")
print("    THREE STATES, AND THE PROBE COUNTS TWO. Its `16% empty` on the images")
print("    table is exactly the nulls; the 2,776 empty strings count as FILLED.")
print(f"    Counting them too would make it {(sum(inull.values())+sum(iempty.values()))/(len(images)*11):.0%}.")

# ── Q5/Q6. ─────────────────────────────────────────────────────────────────
JT = {"str": "text", "int": "number", "float": "number", "bool": "boolean",
      "list": "array", "dict": "object", "NoneType": "null"}
varying = {p: sorted({JT.get(k, k) for k in ks} - {"null"}) for p, ks in kinds.items()}
varying = {p: v for p, v in varying.items() if len(v) > 1}
print(f"\nQ5  paths with more than one non-null type: {len(varying)} — the probe says NONE")
print("\nQ6  no keyed collections. Every level names its fields, and the probe agrees.")

# ── Q8/Q9/Q10. ─────────────────────────────────────────────────────────────
t = time.time()
rows = glom(tags, [{"name": "name", "full_size": "full_size", "last_updated": "last_updated"}])
print(f"\nQ8  glom(tags, [{{...}}]) -> {len(rows)} rows x 3, {time.time()-t:.1f}s")
print(f"    {rows[0]}")
v = glom(images, [Coalesce("variant", default=None)])
print(f"\nQ9  variant non-None on {sum(x is not None for x in v):,} of {len(v):,}")
print("    AND `Coalesce` CANNOT HELP HERE, because `variant` is always PRESENT")
print("    and sometimes null. The default never fires. Entry 20 measured the")
print("    absent/null difference; this document has only the null half.")
t = time.time()
res = [{"tag": t_["name"], **im} for t_ in tags for im in t_["images"]]
print(f"\nQ10 images[] -> {len(res):,} rows, {time.time()-t:.1f}s — a comprehension")

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
print(f"\nQ11 {len(url)} URL path: {sorted(url)}")
print("    ONE, and it is the pagination link — OUTSIDE the records. A frame")
print("    built from `results` reports NONE OF ONE, which entries 17 and 18")
print("    both recorded and which this document makes the extreme case of.")

print("\nQ12 no rectangling verb here. The honest table is question 3's, and on")
print("    THIS document that choice is the whole question: 100 x 16 with a")
print("    list-column, or 1,388 x 11 with the tag's `size` repeated 4x.")
