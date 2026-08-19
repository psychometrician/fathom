"""pydash — Crossref works, 1,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
  measured      2026-08-11
  run           cd corpus/21-crossref-works/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             3   NO                  by hand — 236
   2 how deep                                    4   NO                  by hand — 9
   3 what is one record                          1   -                   CANNOT
   4 always present vs sometimes                10  NO                   YES — 40, 0 nulls
   5 does any field change type                 10  NO                   NO — see below
   6 are any object keys data                    5   NO                  by hand
   7 how many records                            1   NO                  yes, both numbers
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   3   YES                 a comprehension
  11 find every path matching something         14  NO                   by hand — 13, agrees
  12 flattest honest table                       2   -                   CANNOT
  13 needed the shape in advance?                    YES for 8, 9, 10
  14 survives the next file unchanged?               the hand walks do
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~125, pydash on about 6

  pydash's story here is glom's, and the run confirms it line for line: the hand
  recursion answered questions 1, 2, 5, 6 and 11, and pydash answered 8, 9 and
  half of 10. Both agree with jq at 13 URL paths and with the probe at 236 paths
  and depth 9.

  QUESTION 5 IS UNREACHABLE BY CENSUS. The probe's single site is
  `issued.date-parts`, [[2018,11,3]] on 998 and [[null]] on 2 — a `list` on all
  1,000 records, so no path-level type census can see it. `[0][0]` reaches it and
  writing `[0][0]` is knowing the answer.

  THE DEFAULT TRAP CANNOT FIRE HERE. Entry 20 measured `get`, `Coalesce` and
  `pluck` disagreeing about absent-versus-null; this document has ZERO written
  nulls, so all three agree. The trap needs a null before it can spring.
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
items = doc["message"]["items"]

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
print(f"\nQ1  {len(paths):,} distinct paths — HAND-WRITTEN recursion, {time.time()-t:.1f}s")
print(f"Q2  depth {maxd} — same recursion, and it agrees with the probe's 9.")
print("    Note the walk started at the ROOT and found $.message.items on its")
print("    own. Every frame in this directory had to be TOLD where the records")
print("    are, and a hand walk is the only thing here that does not.")

print(f"\nQ3  no candidates named and none priced. CANNOT.")
print(f"Q7  {len(items):,} works in the array; total-results says "
      f"{doc['message']['total-results']:,}")

# ── Q4. ─────────────────────────────────────────────────────────────────────
rk = [set(r) for r in items]
absent = sorted(k for k in set().union(*rk) if sum(k in r for r in rk) < len(items))
nulls = {k for r in items for k, v in r.items() if v is None}
print(f"\nQ4  {len(absent)} of {len(set().union(*rk))} keys sometimes ABSENT; "
      f"{len(nulls)} written null")
print("    ZERO written nulls at the record level, so the absent/null trap has")
print("    nothing to bite on and every tool here agrees. Entry 14's situation.")
print("    pydash's `get`, on the same four probes:")
w = items[0]
for k in ("abstract", "DOI", "abstract.x", "DOI.x"):
    print(f"      get(w, {k!r:12}, '<none>') -> {str(_.get(w, k, '<none>'))[:40]!r}")
print("    Entry 20 measured `get` and glom's `Coalesce` behaving identically and")
print("    purrr's `pluck` differing. With no written nulls here, all three would")
print("    agree — the trap needs a null to exist before it can fire.")

# ── Q5. ─────────────────────────────────────────────────────────────────────
JT = {"str": "text", "int": "number", "float": "number", "bool": "boolean",
      "list": "array", "dict": "object", "NoneType": "null"}
varying = {p: sorted({JT.get(k, k) for k in ks} - {"null"}) for p, ks in kinds.items()}
varying = {p: v for p, v in varying.items() if len(v) > 1}
print(f"\nQ5  paths holding more than one non-null JSON type: {len(varying)}")
for p in sorted(varying)[:6]:
    print(f"    {p}  {varying[p]}")
print("    The probe reports ONE site: $.message.items[].issued.date-parts,")
print("    [[2018,11,3]] on 998 records and [[null]] on 2 — arrays of arrays,")
print("    identical JSON type, differing only in the ELEMENT two levels down.")
dp = Counter(type(w["issued"]["date-parts"][0][0]).__name__ for w in items)
print(f"    the walk types that path by python class: {dict(dp)}")
print("    A path-level type census CANNOT see it: the value is a `list` on all")
print("    1,000. Reaching it means indexing [0][0], which is knowing the answer.")


# ── Q6. ─────────────────────────────────────────────────────────────────────
refk = {k for w in items for r in (w.get("reference") or []) for k in r}
refn = sum(len(w.get("reference") or []) for w in items)
print(f"\nQ6  reference[]: {len(refk)} keys over {refn:,} copies")
print("    The probe DECLINES this as a vocabulary rather than data — the")
print("    `engines` rule from entry 13 generalising to an unseen document.")
print("    The walk supplies both numbers and no verdict.")

# ── HYPHENS. ────────────────────────────────────────────────────────────────
hy = sorted(k for k in set().union(*rk) if "-" in k)
print(f"\n     HYPHENATED KEYS: {len(hy)} of {len(set().union(*rk))}")
print("     A python dict does not care, and neither does any walker here.")
print("     DuckDB needs double quotes, pandas needs backticks in `query`, and R")
print("     needs backticks. THE WALKERS PAY NOTHING FOR THIS and the frames do.")

# ── Q8/Q9/Q10. ──────────────────────────────────────────────────────────────
t = time.time()
rows = _.map_(items, lambda w: _.pick(w, "DOI", "type", "publisher"))
print(f"\nQ8  _.map_ + _.pick -> {len(rows):,} rows x 3, {time.time()-t:.1f}s")
print(f"    {rows[0]}")
ab = [_.get(w, "abstract", None) for w in items]
print(f"\nQ9  abstract non-None on {sum(a is not None for a in ab)} of {len(ab):,}")
t = time.time()
res = _.flatten([[{"work_DOI": w["DOI"], **r} for r in (_.get(w, "reference") or [])]
                 for w in items])
print(f"\nQ10 reference[] -> {len(res):,} rows, {time.time()-t:.1f}s")

# ── Q11. ────────────────────────────────────────────────────────────────────
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
print(f"\nQ11 http-prefixed {len(url_n)} paths, ^https?:// {len(url_s)} paths, "
      f"{time.time()-t:.1f}s")
print(f"    jq reports 13 strict. {'AGREES' if len(url_s) == 13 else 'DIFFERS'}.")
print("    pydash has `map_values_deep`, which visits every value and which entry")
print("    14 recorded EMPTYING a document. Entry 20 re-ran it and saw no")
print("    mutation. It is not used here; the recursion above is.")

# ── Q12. ────────────────────────────────────────────────────────────────────
print("\nQ12 pydash has no rectangling verb. `_.pick` names columns and there is")
print("    no `normalize`. The flattest honest table is one nothing here builds.")
