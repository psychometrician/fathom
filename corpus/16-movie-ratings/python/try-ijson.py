"""ijson — movie ratings, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
  measured      2026-08-10
  run           cd corpus/16-movie-ratings/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  WRONG
   2 how deep                                    1   NO                  yes
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  4   NO                  yes
   6 are any object keys data                    4   NO                  WRONG
   7 how many records                            1   NO                  yes
   8 three named fields to a table               -   -                   CANNOT
   9 a field missing from some rows              -   -                   CANNOT
  10 flatten the deepest array                   1   -                   n/a
  11 find every path matching something          4   NO                  yes
  12 flattest honest table                       -   -                   CANNOT
  13 needed the shape in advance?                    NO — and Q1 still wrong
  14 survives the next file unchanged?               YES — nothing is named
  15 readable a week later?                          the event loop is fiddly
  16 lines, and how much is ceremony?                ~35, mostly bookkeeping
"""
import re
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

prefixes, types = Counter(), defaultdict(Counter)
fields, titles = Counter(), set()
unk = Counter()
pat = re.compile(r"^unk", re.I)

with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if event in ("start_map", "start_array", "end_map", "end_array"):
            continue
        if prefix:
            prefixes[prefix] += 1
            if event != "map_key":
                types[prefix][event] += 1
                parts = prefix.split(".")
                if len(parts) >= 3:
                    titles.add(parts[1])
                    fields[parts[-1]] += 1
        if event == "string" and pat.match(value or ""):
            unk[(prefix.split(".")[-1], value)] += 1

print(f"\n1. {len(prefixes)} distinct prefixes, listing them costs "
      f"{len(str(sorted(prefixes))):,} chars "
      f"({100 * len(str(sorted(prefixes))) / 6975:.0f}% OF THE FILE)")
print("   WRONG in the O(data) way, and by the corpus's worst ratio. Every")
print("   prefix carries a MOVIE TITLE — `item.12 Strong.Genre` — so there are")
print("   38 x 3-to-6 of them for 9 real fields. npm's listing is 111% of its")
print("   file; this is a 7 KB document described in more than its own size.")

print(f"\n2. deepest prefix: {max(p.count('.') + 1 for p in prefixes)} segments")
print(f"\n7. {len(titles)} movies — recovered by SPLITTING THE PREFIX on '.',")
print("   which only works because no film title contains a dot. Two of these")
print("   38 do contain a colon; one more comma-or-dot away and the count is")
print("   silently wrong. ijson's prefix is a dotted string and cannot escape.")

print(f"\n6. WRONG. {len(titles)} of the path segments are film titles and ijson")
print("   presents them exactly as `Genre` and `rating`. It reports the keys as")
print("   `map_key` EVENTS, which is more than most tools give — and it still")
print("   has no way to say which keys are values.")

print("\n4. field counts, recovered from the last prefix segment:")
for f, n in fields.most_common():
    print(f"     {f:18} {n:>3} of {len(titles)}")
print("   NOTHING is on all 38 — the 23 lowercase films and the 15 Title Case")
print("   ones share no field at all.")

print("\n5. prefixes taking more than one event type: "
      f"{sum(1 for c in types.values() if len(c) > 1)}")
print("   ZERO, and that is a false negative. `Popcorn Score` really is number")
print("   x9 and string x6 — but each MOVIE has its own prefix, so no single")
print("   prefix ever sees both. **ijson's type report is defeated by exactly")
print("   the keys-as-data it could not fold.** Every other tool here finds it.")

print(f"\n11. values matching /^unk/: {sum(unk.values())}")
for (f, v), n in unk.most_common():
    print(f"     {f:18} {v!r:>12} x{n}")
print("   All 17, and the field names came from the prefix rather than from me.")
print("   The PATTERN came from me, which is the part a structural detector")
print("   would have to do without.")

print("\n3, 8, 9, 12. CANNOT. No record, no row, no table. 10. n/a.")
