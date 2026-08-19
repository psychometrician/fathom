"""jmespath — movie ratings, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
  measured      2026-08-10
  run           cd corpus/16-movie-ratings/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             4   PARTLY              PARTLY
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  -   -                   CANNOT
   6 are any object keys data                    3   PARTLY              PARTLY
   7 how many records                            1   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              4   YES                 DANGEROUS
  10 flatten the deepest array                   1   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 yes
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no, and it will not say so
  15 readable a week later?                          yes, compact syntax
  16 lines, and how much is ceremony?                ~30, none
"""
import json
import sys
from importlib.metadata import version

import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = json.load(open("../source.json"))

titles = jmespath.search("[0]|keys(@)", doc)
print(f"\n1/6. keys([0]): {len(titles)} of them, e.g. {titles[:2]}")
print("   PARTLY. `keys()` returns the 38 FILM TITLES, which are data — and")
print("   jmespath presents them exactly as it would present field names. It")
print("   is the same call either way. That is the whole keys-as-data problem,")
print("   and on this document it is the FIRST thing you see.")

print("\n2, 3, 5, 11. CANNOT. No depth verb, no row-shape proposal, no type")
print("   report, and no recursive descent at all — jmespath has no `..`.")

print(f"\n7. {len(titles)} movies.")

print("\n4. PARTLY — a projection counts what is there, once you name it:")
for f in ("rating", "Rating", "Genre", "popcornscore", "Popcorn Score"):
    n = len(jmespath.search(f'[0].*."{f}"', doc) or [])
    print(f"     {f:18} {n:>3} of {len(titles)}")
print("   Nothing is on all 38. The `[0].*` wildcard is what makes this")
print("   reachable without listing the films, and it is jmespath's one good")
print("   answer on this document.")

rows = jmespath.search(
    '[0].* | [].{r: Rating, r2: rating, g: Genre}', doc)
print(f"\n8. three fields: {len(rows)} rows, e.g. {rows[0]}")
print(f"\n9. `Rating` is None on {sum(1 for r in rows if r['r'] is None)} of "
      f"{len(rows)}, all kept. DANGEROUS because the SAME None also means")
print("   `I misspelt the field`, and this document is ABOUT misspelt fields:")
print(f"     [0].*.Ratng      -> {len(jmespath.search('[0].*.Ratng', doc) or [])} results")
print(f"     [0].*.rating     -> {len(jmespath.search('[0].*.rating', doc) or [])} results")
print("   A typo returns 0 and a real-but-partial field returns 23. Both are")
print("   silent, and only counting tells them apart.")

merged = jmespath.search('[0].* | [].{r: Rating || rating}', doc)
print(f"\n12. flattest: {len(merged)} rows. `Rating || rating` is jmespath's")
print(f"   first-present operator and it fills "
      f"{sum(1 for r in merged if r['r'] is not None)} of {len(merged)} —")
print("   the same verb glom calls `Coalesce` and `design/first_present.py`")
print("   calls `first_present`. **Three names for one word, in three tools.**")
print("   WHAT IS LOST: the 17 sentinels ride through `||` as ordinary values,")
print("   because `unknown` is present. And the film titles are gone from the")
print("   result: `[0].*` drops the key it wildcarded over, so the rows have no")
print("   identity unless you zip them back against `keys(@)` yourself.")
print("\n10. n/a — no nested array.")
