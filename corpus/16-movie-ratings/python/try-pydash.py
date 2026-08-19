"""pydash — movie ratings, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
  measured      2026-08-10
  run           cd corpus/16-movie-ratings/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  WRONG
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   NO                  yes
   5 does any field change type                  3   YES                 PARTLY
   6 are any object keys data                    3   NO                  WRONG
   7 how many records                            1   NO                  YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   1   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 yes
  13 needed the shape in advance?                    NO for 1, 4, 7
  14 survives the next file unchanged?               Q1 does
  15 readable a week later?                          yes, it is lodash
  16 lines, and how much is ceremony?                ~30, little
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = json.load(open("../source.json"))
movies = doc[0]


def leaf_names(node, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            acc.add(k)
            leaf_names(v, acc)
    elif isinstance(node, list):
        for v in node:
            leaf_names(v, acc)
    return acc


names = leaf_names(doc, set())
print(f"\n1/6. distinct key names anywhere: {len(names)}")
print("   WRONG, and the arithmetic says why: 38 film titles + 9 real fields =")
print(f"   {len(names)}. The walk cannot tell a title from a field, so 81% of")
print("   its answer is data. npm's version of this is 3,126 against a true 40;")
print("   this is the same failure at a scale you can check by hand.")

print("\n2, 3, 11. CANNOT. No depth verb, no row-shape proposal, no search over")
print("   unknown paths — the recursion above is mine.")

print(f"\n7. {len(movies)} movies.")

present = Counter(k for v in movies.values() for k in v)
print("\n4. field PRESENCE across the 38 films:")
for k, n in present.most_common():
    print(f"     {k:18} {n:>3} of {len(movies)}")
print("   Nothing is on all 38 — the two key-sets are disjoint.")

kinds = Counter(type(v.get("Popcorn Score")).__name__ for v in movies.values()
                if "Popcorn Score" in v)
print(f"\n5. PARTLY. types at `Popcorn Score`: {dict(kinds)}")
print("   9 ints, 6 strings. The Counter is mine; pydash has no type report and")
print("   does not unify, so both populations survive.")

rows = pydash.map_values(movies, lambda v: {
    "rating": pydash.get(v, "Rating") or pydash.get(v, "rating"),
    "popcorn": pydash.get(v, "Popcorn Score") or pydash.get(v, "popcornscore"),
})
filled = sum(1 for r in rows.values() if r["rating"] is not None)
print(f"\n8/12. `pydash.get(v,'Rating') or pydash.get(v,'rating')` fills "
      f"{filled} of {len(rows)}")
print(f"     e.g. {list(rows.items())[0]}")
print("   `or` is Python's first-present, and it is the THIRD spelling of the")
print("   same word this entry has met: glom's `Coalesce`, jmespath's `||`,")
print("   pydash-plus-`or`. `design/first_present.py` is a fourth.")
print("   **And `or` is the WRONG one**: it treats 0 as absent. `popcornscore`")
print("   is a score and a film scoring 0 would silently take the other")
print("   spelling's value. Coalesce and `||` do not have that bug.")

print(f"\n9. rating None on {sum(1 for r in rows.values() if r['rating'] is None)} "
      f"of {len(rows)} after the fallback — none.")
sent = Counter(v for m in movies.values() for v in m.values()
               if isinstance(v, str) and v.lower().startswith("unk"))
print(f"   WHAT IS LOST: the {sum(sent.values())} sentinels {dict(sent)} ride")
print("   through as ordinary values, and the film titles survive only because")
print("   `map_values` keeps the key — which is pydash's one advantage here.")
print("\n10. n/a — no nested array.")
