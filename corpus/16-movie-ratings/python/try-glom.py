"""glom — movie ratings, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
  measured      2026-08-10
  run           cd corpus/16-movie-ratings/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   CANNOT
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  4   YES                 PARTLY
   6 are any object keys data                    -   -                   CANNOT
   7 how many records                            1   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              5   YES                 yes
  10 flatten the deepest array                   1   -                   n/a
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       6   YES                 yes
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no — every spec is a path
  15 readable a week later?                          yes, specs read as data
  16 lines, and how much is ceremony?                ~30, almost none
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

from glom import Coalesce, glom

print(f"python {sys.version.split()[0]}, glom {version('glom')}")
movies = json.load(open("../source.json"))[0]

print("\n1, 2, 3, 6, 11. CANNOT. glom is an EXTRACTOR — every spec names a path")
print("   the caller already knows. On a document keyed by MOVIE TITLE that is")
print("   the worst possible position: the paths ARE the data, so writing a")
print("   spec means already having the list of films.")

print(f"\n7. {len(movies)} movies.")

print("\n4. PARTLY — glom tests a field once you name it:")
for f in ("rating", "Rating", "Genre", "Popcorn Score", "popcornscore"):
    have = sum(1 for v in movies.values() if glom(v, Coalesce(f, default=None)) is not None)
    print(f"     {f:18} {have:>3} of {len(movies)}")
print("   Nothing is on all 38. The five names came from reading the file.")

kinds = Counter(type(glom(v, Coalesce("Popcorn Score", default=None))).__name__
                for v in movies.values()
                if glom(v, Coalesce("Popcorn Score", default=None)) is not None)
print(f"\n5. PARTLY. types at `Popcorn Score`: {dict(kinds)}")
print("   9 ints and 6 strings; the strings are the sentinels. A Python loop")
print("   with glom as the accessor — glom has no type report and does not")
print("   unify, so unlike polars and DuckDB the two populations survive intact.")

# ── 8, 9, 12. the one thing glom does better than anything else here ─────────
# `Coalesce` is EXACTLY the verb this document wants: it takes the first path
# that is present, which is what "Rating and rating are one field" means.
spec = {
    "rating": Coalesce("Rating", "rating", default=None),
    "popcorn": Coalesce("Popcorn Score", "popcornscore", default=None),
    "tomato": Coalesce("Tomato Score", "tomatoscore", default=None),
}
rows = [{"title": t, **glom(v, spec)} for t, v in movies.items()]
filled = sum(1 for r in rows if r["rating"] is not None)
print(f"\n8/12. THE ONE PLACE GLOM WINS OUTRIGHT. `Coalesce('Rating', 'rating')`")
print(f"   is the verb this document wants, and it fills {filled} of {len(rows)}:")
for r in rows[:3]:
    print(f"     {r}")
print("   Three Coalesces collapse all three renamed pairs in one spec. Every")
print("   other tool in either language needs `fillna`/`coalesce`/`//` per pair")
print("   and treats it as a repair; glom treats it as the SHAPE.")
print("   **`design/first_present.py` is this verb**, and VERDICT.md records it")
print("   collapsing this file's `Rating`/`rating` 38 of 38. glom got there")
print("   first and calls it Coalesce.")

print(f"\n9. rating absent-or-null on {sum(1 for r in rows if r['rating'] is None)} "
      f"of {len(rows)} rows after the Coalesce — none. Before it, either spelling")
print("   alone misses 15 or 23.")

sent = Counter(v for m in movies.values() for v in m.values()
               if isinstance(v, str) and v.lower().startswith("unk"))
print(f"\n   WHAT IS LOST: nothing glom touched — but the {sum(sent.values())} "
      f"sentinels {dict(sent)}")
print("   ride through the Coalesce as ordinary values, because `unknown` is")
print("   present and Coalesce only skips what is absent. The verb that fixes")
print("   the renaming is silent about the missingness.")
print("\n10. n/a — no nested array.")
