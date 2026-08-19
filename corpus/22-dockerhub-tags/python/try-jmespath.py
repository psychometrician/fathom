"""jmespath — Docker Hub tags, 100 tags

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   476 KB, 100 tags under $.results, depth 5
  measured      2026-08-11
  run           cd corpus/22-dockerhub-tags/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             5   YES                 PARTLY — one level
   2 how deep                                    2   -                   CANNOT
   3 what is one record                          3   YES                 counts both
   4 always present vs sometimes                 8   NO                  YES — and see below
   5 does any field change type                  4   YES                 PARTLY
   6 are any object keys data                    1   -                   n/a
   7 how many records                            2   NO                  yes, both numbers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              4   YES                 yes
  10 flatten the deepest array                   4   YES                 YES — its best answer
  11 find every path matching something          3   YES                 CANNOT
  12 flattest honest table                       3   YES                 CANNOT
  13 needed the shape in advance?                    YES for 5, 6, 10, 11
  14 survives the next file unchanged?               no — every path is named
  15 readable a week later?                          YES
  16 lines, and how much is ceremony?                ~85, one line per query

  THE NESTED CONTROL, AND JMESPATH DOES NOT RAISE ONCE. Entry 20's `keys(null)`
  and entry 21's `length(null)` both killed whole queries; this document has no
  absent key anywhere, so nothing is ever null where a function expects a
  container. THE FAILURES THOSE ENTRIES RECORDED NEED RAGGEDNESS, and here
  there is none.

  Its `[]` flattening is again the shortest correct answer to question 10 —
  `results[].images[]` for the exact 1,388 — and again it drops the parent.
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


def q(e):
    t = time.time()
    return jmespath.search(e, doc), time.time() - t


print("\nQ0  an expression language over a parsed object. CANNOT.")

keys, t = q("results[].keys(@) | []")
print(f"\nQ1  `results[].keys(@) | []` -> {len(keys):,} occurrences, "
      f"{len(set(keys))} distinct, {t:.2f}s")
ik, _ = q("results[].images[].keys(@) | []")
print(f"Q1  one level down, spelled out: {len(set(ik))} image keys")
print("    TWO LEVELS, TWO EXPRESSIONS, and no raise — entry 20's `keys(null)`")
print("    and entry 21's needed a guard because a parent was sometimes absent.")
print("    Every tag here HAS `images`, so the unguarded form is safe.")
print("\nQ2  CANNOT. No recursive descent; the probe says 5.")

n, _ = q("length(results)")
ni, _ = q("length(results[].images[])")
print(f"\nQ3  jmespath counts both candidates and prices neither: {n} tags, {ni:,} images")
print(f"Q7  {n} on this page; `count` says {doc['count']:,} and `next` is a URL")

present = Counter(keys)
ipresent = Counter(ik)
inull, _ = q("results[].images[] | [] | length(@)")
print(f"\nQ4  tag keys not on every tag: {[k for k, c in present.items() if c < n]}")
print(f"Q4  image keys not on every image: "
      f"{[k for k, c in ipresent.items() if c < ni]}")
nulls = {k: sum(1 for t_ in doc["results"] for im in t_["images"] if im[k] is None)
         for k in ipresent}
empt = {k: sum(1 for t_ in doc["results"] for im in t_["images"] if im[k] == "")
        for k in ipresent}
print(f"Q4  written NULL:  {{k: v for k, v in nulls.items() if v}}"
      .replace("{k: v for k, v in nulls.items() if v}",
               str({k: v for k, v in nulls.items() if v})))
print(f"Q4  written \"\":    {str({k: v for k, v in empt.items() if v})}")
print("    `keys(@)` counts PRESENCE and gets the first two lines right. The")
print("    null and empty-string counts needed python: jmespath can test ONE")
print("    named key at a time (`length(results[].images[?variant == null])`)")
print("    and has no way to map that over an unknown key set.")

print("\nQ5  `type()` works on a named path and there is no census:")
for f in ("full_size", "name", "creator"):
    ts, _ = q(f"results[].{f} | [].type(@)")
    print(f"    results[].{f:12} -> {dict(Counter(ts))}")
ts, _ = q("results[].images | [].type(@)")
print(f"    results[].images        -> {dict(Counter(ts))}  <- NOTE: `[]` already")
print("      flattened the arrays, so this types the IMAGE OBJECTS and not the")
print("      `images` field. Typing the field itself needs `results[].[images]`")
print("      or a python loop — the flattening operator gets in its own way.")
print("    The probe reports NO type change anywhere. jmespath can confirm that")
print("    one field at a time, sixteen times, and never discover it.")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")

t8, t = q("results[].{name: name, size: full_size, updated: last_updated}")
print(f"\nQ8  one multiselect-hash -> {len(t8)} rows x 3, {t:.2f}s")
v, _ = q("results[].images[] | [?variant != null] | length(@)")
print(f"\nQ9  `variant` non-null on {v:,} of {ni:,} — a filter, no raise")
print("    and `[?variant != null]` is SAFE here only because `variant` is")
print("    always PRESENT. Entry 21's `[?r != null]` returned everything")
print("    because an absent array flattens to `[]` rather than null.")
res, t = q("results[].images[]")
print(f"\nQ10 `results[].images[]` -> {len(res):,} rows, {t:.2f}s")
print("    THREE TOKENS for the exact 1,388 — the shortest right answer to")
print("    question 10 in either language — AND IT DROPS THE TAG NAME.")
wn, _ = q("results[].{n: name, i: images}")
print(f"    keeping it: {len(wn)} rows and `i` is a LIST-COLUMN, not rows.")
print("\nQ11 CANNOT enumerate paths. The document's one URL is `next`, which is")
u, _ = q("next")
print(f"    reachable by name: {u[:48]}…")
print("    jq, ijson, glom, pydash and rrapply all report it as 1 path found by")
print("    SEARCHING; jmespath found it because I already knew it was there.")
print("\nQ12 a multiselect-hash naming all 16 tag fields would work and stop at")
print("    `images`. No auto-flatten. What is lost is the child table, silently.")
