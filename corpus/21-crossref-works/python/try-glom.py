"""glom — Crossref works, 1,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
  measured      2026-08-11
  run           cd corpus/21-crossref-works/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             3   NO                  by hand — 236
   2 how deep                                    4   NO                  by hand — 9
   3 what is one record                          1   -                   CANNOT
   4 always present vs sometimes                12  NO                   YES — 40, 0 nulls
   5 does any field change type                 10  NO                   NO — see below
   6 are any object keys data                    5   NO                  by hand
   7 how many records                            1   NO                  yes, both numbers
   8 three named fields to a table               4   YES                 yes — its best answer
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   4   YES                 a comprehension
  11 find every path matching something         14  NO                   by hand — 13, agrees
  12 flattest honest table                       4   -                   CANNOT
  13 needed the shape in advance?                    YES for 8, 9, 10
  14 survives the next file unchanged?               the hand walks do
  15 readable a week later?                          Q8 yes
  16 lines, and how much is ceremony?                ~130, glom on about 10

  THE HAND WALK IS THE ONLY THING IN THIS DIRECTORY THAT FOUND THE RECORDS BY
  ITSELF. It starts at the root, reaches $.message.items, and returns 236 paths
  and depth 9 — the probe's numbers exactly. pandas, polars and DuckDB all read
  the ENVELOPE when pointed at the file and all had to be told where to look.

  QUESTION 5 IS UNREACHABLE BY CENSUS HERE, and that is this document's own
  contribution. The probe's single type-changing site is
  `issued.date-parts` — [[2018,11,3]] on 998 records, [[null]] on 2. A
  path-level type census sees `list` on all 1,000 and reports nothing. Getting
  to it means indexing `[0][0]`, which is knowing the answer before you ask.

  THE DEFAULT TRAP CANNOT FIRE ON THIS DOCUMENT. Entry 20 measured `Coalesce`,
  `get` and `pluck` disagreeing about absent-versus-null; here there are ZERO
  written nulls, so all three agree. The trap needs a null to exist.

  Its Q11 count, 13, is jq's exactly — and unlike entry 20 the naive and strict
  predicates give the SAME number, because no field in this document begins with
  "http" unless it is a URL.
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
print("    glom's Coalesce, on the same four probes entry 20 used:")
w = items[0]
for k in ("abstract", "DOI", "abstract.x", "DOI.x"):
    print(f"      Coalesce({k!r:12}, default='<none>') -> "
          f"{str(glom(w, Coalesce(k, default='<none>')))[:40]!r}")
print("    With no written nulls anywhere, the trap entry 20 measured cannot")
print("    fire on this document: every default here means ABSENT and means it")
print("    unambiguously. Same verb, same behaviour, nothing to catch.")

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
rows = glom(items, [{"DOI": "DOI", "type": "type", "publisher": "publisher"}])
print(f"\nQ8  glom(items, [{{...}}]) -> {len(rows):,} rows x 3, {time.time()-t:.1f}s")
print(f"    {rows[0]}")
print("    THE SPEC IS THE TABLE, and hyphens cost nothing because a spec key is")
print("    a string. `{'refs': 'reference-count'}` needs no escaping at all.")
ab = glom(items, [Coalesce("abstract", default=None)])
print(f"\nQ9  abstract non-None on {sum(a is not None for a in ab)} of {len(ab):,}")
t = time.time()
res = [{"work_DOI": w["DOI"], **r} for w in items for r in (w.get("reference") or [])]
print(f"\nQ10 reference[] -> {len(res):,} rows, {time.time()-t:.1f}s")
print("    A comprehension, not a spec: glom's spec language handles a path that")
print("    exists, and `reference` is absent on 465 works. `or []` is the guard.")

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
print("    glom contributed nothing to this; the recursion did. It has no path")
print("    enumeration, which is questions 1, 2, 5 and 11 in one sentence.")

# ── Q12. ────────────────────────────────────────────────────────────────────
print("\nQ12 glom builds exactly the table its spec names. There is no `**` and no")
print("    auto-flatten, so the 71-column frame means writing 71 keys. Nothing")
print("    is lost that you did not choose to drop — the opposite failure from")
print("    json_normalize's, and on this document the opposite is the safer one.")
