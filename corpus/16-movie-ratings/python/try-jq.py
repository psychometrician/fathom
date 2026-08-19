"""jq (via the `jq` Python binding) — movie ratings, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
  measured      2026-08-10
  run           cd corpus/16-movie-ratings/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  yes
   2 how deep                                    1   NO                  yes
   3 what is one record                          5   NO                  PARTLY
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  5   NO                  yes
   6 are any object keys data                    4   NO                  PARTLY
   7 how many records                            1   NO                  YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   1   -                   n/a
  11 find every path matching something          5   NO                  yes
  12 flattest honest table                       5   YES                 yes
  13 needed the shape in advance?                    NO for 1-7 and 11
  14 survives the next file unchanged?               the describe half does
  15 readable a week later?                          yes, short expressions
  16 lines, and how much is ceremony?                ~35, dense not ceremonial
"""
import json
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq binding {version('jq')}")
doc = json.load(open("../source.json"))
q = lambda e: jq.compile(e).input(doc).all()

print("\n1. folded path shapes (array indices -> []):")
for s in q('[paths(scalars)|map(if type=="number" then "[]" else . end)|join(".")]'
           '|group_by(.)|map({p:.[0],n:length})|sort_by(-.n)')[0][:6]:
    print(f"     {s['p']:44} {s['n']:>4}")
print("   The movie TITLES are in these paths — `[].12 Strong.Genre` — because")
print("   jq folds array indices and has no notion of folding keys. 38 titles")
print("   x 3-to-6 fields is why the listing is longer than the fold suggests.")

print(f"\n2. deepest path: {q('[paths|length]|max')[0]} segments")
print(f"\n7. {q('.[0]|length')[0]} movies.")

print("\n6. PARTLY. the keyed object's keys, which ARE data:")
print(f"   {q('.[0]|keys|length')[0]} keys, e.g. {q('.[0]|keys|.[0:3]')[0]}")
print("   `keys` lists them and jq cannot say they are film titles rather than")
print("   field names. It presents them exactly as `Genre` is presented.")

print("\n4. field presence across the 38 movies, nothing named:")
for r in q('[.[0]|.[]|keys[]]|group_by(.)|map({k:.[0],n:length})|sort_by(-.n)')[0]:
    print(f"     {r['k']:18} {r['n']:>3} of 38")
print("   NOTHING is on all 38. The 23 lowercase movies and the 15 Title Case")
print("   ones share NO FIELD, so `keys` over the union is two disjoint sets.")
print("   jq shows this plainly and does not remark on it.")

print("\n5. fields taking more than one type:")
for r in q('[.[0]|to_entries[]|.value|to_entries[]|{k:.key,t:(.value|type)}]'
           '|group_by(.k)|map({k:.[0].k,t:(map(.t)|unique)})'
           '|map(select(.t|length>1))')[0]:
    print(f"     {r['k']:18} {r['t']}")
print("   `Popcorn Score` and `Tomato Score` are number-or-string. The strings")
print("   are the SENTINELS, and jq is the only tool here that gets to them")
print("   without a hand-written type loop:")
for r in q('[.[0]|.[]|to_entries[]|select(.value|type=="string")'
           '|select(.value|test("^unk"))|.key]|group_by(.)'
           '|map({k:.[0],n:length})')[0]:
    print(f"     {r['k']:18} {r['n']:>3} sentinel values")
print("   17 of the 159 present cells. Every emptiness measure counts them as")
print("   filled, so 54% empty is really 58%.")

print("\n3. one movie per row, and TWO tables inside it:")
for r in q('[.[0]|to_entries[]|{k:(if .value.rating then "lowercase" '
           'else "TitleCase" end),n:(.value|keys|length)}]|group_by(.k)'
           '|map({k:.[0].k,rows:length,cols:(map(.n)|max)})')[0]:
    print(f"     {r['k']:15} {r['rows']:>3} rows x {r['cols']} cols, no holes")
print("   54% to 0% — and the test above is `if .value.rating`, which I chose.")
print("   There is NO DISCRIMINATOR VALUE to split on: the groups share no key,")
print("   so what separates them is the CASE OF THE FIELD NAMES.")

rows = q('[.[0]|to_entries[]|{title:.key,Rating:.value.Rating,rating:.value.rating}]')[0]
print(f"\n8. three fields: {len(rows)} rows, e.g. {rows[0]}")
print(f"\n9. `Rating` null on {sum(1 for r in rows if r['Rating'] is None)} of "
      f"{len(rows)}, all kept.")

print("\n10. n/a — no nested array.")
hits = q('[paths(strings) as $p|select(getpath($p)|test("^unk"))'
         '|($p|map(if type=="number" then "[]" else . end)|join("."))]|length')[0]
print(f"\n11. values matching /^unk/: {hits}, found without naming a FIELD.")
print("   ALL SEVENTEEN, including the five in `Gross` — and the comparison")
print("   with design/probe.py is the point rather than the score:")
print("     jq          17 of 17, because it was given the PATTERN `^unk`")
print("     the probe   12 of 17, because it was given NOTHING")
print("   The probe's detector is structural — a field that is a NUMBER on some")
print("   records and one of very few STRINGS on others — so it catches")
print("   `Popcorn Score` and `Tomato Score` and cannot see `Gross`, which is")
print("   text on all 15. VERDICT.md defect 18 records that 2-of-3 coverage.")
print("   **jq's 17 needs a word list and this project refuses word lists**, so")
print("   the two numbers are not comparable as scores. What jq shows is that a")
print("   value-matching verb is the right SHAPE of tool for the question; what")
print("   the probe shows is how much of it survives without domain knowledge.")

merged = q('[.[0]|to_entries[]|{title:.key,rating:(.value.Rating // .value.rating)}]'
           '|map(select(.rating!=null))|length')[0]
print(f"\n12. flattest: 38 x 9. `.Rating // .rating` fills {merged} of 38 in one")
print("   expression — with both spellings typed by hand. jq has no verb for")
print("   `these two names are one field`.")
print("   WHAT IS LOST: nothing jq touched. It is the most complete answer on")
print("   this document and it volunteers none of the three findings.")
