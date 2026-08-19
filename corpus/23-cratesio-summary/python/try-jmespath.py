"""jmespath — crates.io summary

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   41 KB, six collections at the root, depth 4
  measured      2026-08-11
  run           cd corpus/23-cratesio-summary/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             6   YES                 PARTLY — one level
   2 how deep                                    1   -                   CANNOT
   3 what is one record                          10  YES                 counts, cannot compare
   4 always present vs sometimes                 6   NO                  YES for presence
   5 does any field change type                  4   YES                 PARTLY
   6 are any object keys data                    1   -                   n/a
   7 how many records                             3  NO                  three answers
   8 three named fields to a table                2 YES                 yes
   9 a field missing from some rows                3 YES                 yes
  10 flatten the deepest array                     3 -                   NO ARRAY TO FLATTEN
  11 find every path matching something            5 YES                 CANNOT
  12 flattest honest table                         4 YES                 CANNOT
  13 needed the shape in advance?                    YES — every collection by name,
                                                     four times over
  14 survives the next file unchanged?               no
  15 readable a week later?                          YES
  16 lines, and how much is ceremony?                ~90

  THE DEFECT-25 DOCUMENT, AND JMESPATH IS THE WORST-PLACED TOOL HERE FOR IT.
  Its whole idiom is naming a path, and this document's point is that four
  DIFFERENTLY-NAMED paths hold one shape. Every query below is written four
  times, and the fourfold repetition in the SOURCE is the only place the
  repetition in the DOCUMENT shows up.

  It can compare the four key-sets — `keys(@)` per collection, then compare in
  python — but the comparison is not expressible IN jmespath, because there is
  no set equality and no way to bind two projections together.
"""
import json
import re
import time
from collections import Counter
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")

RAW = "../source.json"
doc = json.load(open(RAW))
CRATE = ["new_crates", "most_downloaded", "most_recently_downloaded", "just_updated"]


def q(e):
    t = time.time()
    return jmespath.search(e, doc), time.time() - t


print("\nQ0  an expression language over a parsed object. CANNOT.")

roots, _ = q("keys(@)")
print(f"\nQ1  `keys(@)` -> {roots}")
allk, t = q("[" + ", ".join(f"{c}[].keys(@)" for c in CRATE) + "] | []")
print(f"Q1  the four collections' keys, in one expression: {len(allk)} occurrences,"
      f" {len(set(k for grp in allk for k in grp))} distinct, {t:.3f}s")
print("    AND THE EXPRESSION NAMES ALL FOUR COLLECTIONS. That is the document's")
print("    own point showing up as repetition in the query text.")
print("\nQ2  CANNOT. No recursive descent; the probe says 4.")

# ── Q3. ─────────────────────────────────────────────────────────────────────
print("\nQ3  jmespath counts each collection and cannot compare them:")
for c in CRATE + ["popular_keywords", "popular_categories"]:
    n, _ = q(f"length({c})")
    print(f"    {c:26} {n:>3} rows")
sets = {c: tuple(sorted(q(f"{c}[0] | keys(@)")[0])) for c in CRATE}
print(f"Q3  distinct key-sets, compared IN PYTHON: {len(set(sets.values()))}")
print("    jmespath produced the four key lists and cannot compare them: there")
print("    is no set equality, and no way to bind two projections together.")
print("    THE COMPARISON LEFT THE LANGUAGE. The probe prints `same shape as`.")
ids, _ = q("[" + ", ".join(f"{c}[].id" for c in CRATE) + "] | []")
names, _ = q("[" + ", ".join(f"{c}[].name" for c in CRATE) + "] | []")
dups = sorted(n for n, k in Counter(names).items() if k > 1)
print(f"\n     THE OVERLAP: {len(ids)} rows, {len(set(ids))} distinct crates — {dups}")
print("     jmespath CAN reach this: `[...] | []` then a python Counter. It")
print("     cannot count distinct values itself — there is no `unique`.")

# ── Q4/Q5/Q6/Q7. ────────────────────────────────────────────────────────────
present = Counter(k for grp in allk for k in grp)
tot = len(ids)
print(f"\nQ4  crate keys not on every crate: {[k for k, n in present.items() if n < tot]}")
nul = {k: sum(1 for c in CRATE for x in doc[c] if x[k] is None) for k in present}
print(f"Q4  written NULL: {{k: v for k, v in nul.items() if v}}"
      .replace("{k: v for k, v in nul.items() if v}", str({k: v for k, v in nul.items() if v})))
print(f"Q4  NULL ON ALL {tot}: {sorted(k for k, v in nul.items() if v == tot)}")
print("    `keys(@)` counts PRESENCE and gets the first line right. The null")
print("    counts needed python: jmespath tests ONE named key at a time.")
print("\nQ5  `type()` on a named path, and no census:")
for f in ("downloads", "homepage"):
    ts, _ = q("[" + ", ".join(f"{c}[].{f}" for c in CRATE) + "] | [] | [].type(@)")
    print(f"    {f:12} -> {dict(Counter(ts))}")
print("    NOTE the counts are short of 40: the `[]` projection DROPS NULLS, so")
print("    a field that is null on some crates simply has fewer entries. That is")
print("    entry 21's finding again — jmespath cannot see a null through `[]`.")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
print(f"\nQ7  num_crates {doc['num_crates']:,}, num_downloads {doc['num_downloads']:,},"
      f" {tot} rows, {len(set(ids))} distinct")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8, t = q("new_crates[].{name: name, version: max_version, downloads: downloads}")
print(f"\nQ8  one multiselect-hash -> {len(t8)} rows x 3, {t:.3f}s")
h, _ = q("[" + ", ".join(f"{c}[].{{n: name, h: homepage}}" for c in CRATE) + "] | []")
print(f"\nQ9  {len(h)} rows kept, `homepage` null on {sum(x['h'] is None for x in h)}")
print("    A multiselect-hash keeps the row where the bare projection drops it.")
print("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is an object of six")
print("    fields; question 10 has no target on this document.")
lk, _ = q("[" + ", ".join(f"{c}[].links" for c in CRATE) + "] | []")
print(f"    reaching `links` instead: {len(lk)} objects of {len(lk[0])} fields each")
print("\nQ11 CANNOT enumerate paths — no recursive descent. Named paths work, and")
print("    each must be written four times:")
for f in ("homepage", "repository"):
    v, _ = q("[" + ", ".join(f"{c}[].{f}" for c in CRATE) + "] | []")
    vals = [x for x in v if isinstance(x, str)]
    print(f"    {f:12} {len(vals):>3} strings, "
          f"{sum(bool(re.match(r'^https?://', x)) for x in vals):>3} URLs")
print("    jq, ijson, glom and pydash report 11 distinct URL PATHS folding to 3.")
print("\nQ12 a multiselect-hash naming all 23 crate fields would work and would")
print("    have to be written four times. No auto-flatten, no union, no `unique`.")
