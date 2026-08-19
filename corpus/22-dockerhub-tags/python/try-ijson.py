"""ijson — Docker Hub tags, 100 tags

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   476 KB, 100 tags under $.results, depth 5
  measured      2026-08-11
  run           cd corpus/22-dockerhub-tags/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   PARTLY
   1 what is in here                             1   NO                  yes — 33
   2 how deep                                    2   NO                  yes — 5
   3 what is one record                          3   NO                  CANNOT
   4 always present vs sometimes                 8   NO                  YES — all three states
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                    1   -                   n/a
   7 how many records                            2   NO                  yes, both numbers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   3   YES                 yes — 1,388
  11 find every path matching something          3   NO                  yes — 1, from the pass
  12 flattest honest table                       2   -                   n/a
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 11
  14 survives the next file unchanged?               yes
  15 readable a week later?                          the parse loop needs its comment
  16 lines, and how much is ceremony?                ~95, one pass is 30

  THE NESTED CONTROL, and ijson is the only tool here that answers ALL THREE
  states of empty from one pass — absent, null, and empty string are three
  different events. The probe counts the first two and pandas counts only the
  null; ijson can count each separately because it never builds anything that
  has to choose.
"""
import re
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')} (backend {ijson.backend})")

RAW = "../source.json"
print("\nQ0  ijson is a parser and reports no health. It WOULD raise on")
print("    truncation, which is more than the frames can say. PARTLY.")

t = time.time()
paths, types = Counter(), defaultdict(set)
dmax = dnow = ntags = nimages = 0
tag_keys = Counter()
img_null, img_empty, img_keys = Counter(), Counter(), Counter()
url = set()
this_tag, this_img = set(), set()
TAG, IMG = "results.item", "results.item.images.item"
for prefix, event, value in ijson.parse(open(RAW, "rb")):
    if event in ("start_map", "start_array"):
        dnow += 1
        dmax = max(dmax, dnow)
    elif event in ("end_map", "end_array"):
        dnow -= 1
    if event == "map_key":
        continue
    if prefix:
        paths[prefix] += 1
        types[prefix].add(event)
    if prefix == IMG and event == "start_map":
        nimages += 1
    if prefix == TAG and event == "start_map":
        this_tag = set()
    elif prefix == TAG and event == "end_map":
        ntags += 1
        tag_keys.update(this_tag)
    if prefix.startswith(TAG + ".") and prefix.count(".") == TAG.count(".") + 1:
        this_tag.add(prefix.rsplit(".", 1)[1])
    if prefix.startswith(IMG + ".") and prefix.count(".") == IMG.count(".") + 1:
        k = prefix.rsplit(".", 1)[1]
        img_keys[k] += 1
        if event == "null":
            img_null[k] += 1
        elif event == "string" and value == "":
            img_empty[k] += 1
    if event == "string" and isinstance(value, str) and re.match(r"^https?://", value):
        url.add(prefix)
t_pass = time.time() - t

print(f"\n     ONE PASS over 476 KB: {t_pass:.2f}s, nothing retained but counters.")
print(f"\nQ1  {len(paths)} distinct prefixes — the probe says 33")
print(f"Q2  depth {dmax} — the probe says 5")
# paths[IMG] counts start_map AND end_map, so it is 2x the object count — the
# first draft printed 2,776 images and 2,776 as the Q9 denominator. Counted on
# `start_map` instead.
nimg = nimages
print(f"\nQ3  no candidates named and none priced. CANNOT.")
print(f"Q7  {ntags} tags, {nimg:,} images — both counted in the same pass")

print(f"\nQ4  tag keys not on every tag: "
      f"{[k for k, c in tag_keys.items() if c < ntags]}")
print(f"Q4  image keys ABSENT anywhere:  "
      f"{[k for k, c in img_keys.items() if c < nimg]}")
print(f"Q4  image keys written NULL:     {dict(img_null)}")
print(f"Q4  image keys written \"\":       {dict(img_empty)}")
print("    ALL THREE STATES, SEPARATELY, FROM ONE PASS. A missing key emits no")
print("    event, a null emits `null`, an empty string emits `string` with a")
print("    zero-length value. ijson is the only tool in this directory that")
print("    never has to collapse any pair of them, because it builds nothing.")
print(f"    the probe's `16% empty` counts the nulls only; all three would be "
      f"{(sum(img_null.values())+sum(img_empty.values()))/(nimg*11):.0%}.")

EV = {"start_map": "object", "start_array": "array"}
kinds = {p: {EV.get(t, t) for t in ts if t not in ("end_map", "end_array", "map_key")} - {"null"}
         for p, ts in types.items()}
print(f"\nQ5  prefixes with more than one non-null kind: "
      f"{len([p for p, k in kinds.items() if len(k) > 1])} — the probe says NONE")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")

t = time.time()
rows = [(x["name"], x["full_size"], x["last_updated"])
        for x in ijson.items(open(RAW, "rb"), "results.item")]
print(f"\nQ8  {len(rows)} rows x 3, streamed in {time.time()-t:.2f}s")
nv = sum(1 for x in ijson.items(open(RAW, "rb"), "results.item")
         for im in x["images"] if im.get("variant") is not None)
print(f"\nQ9  `variant` non-null on {nv:,} of {nimg:,}; every image HAS the key")
t = time.time()
res = [(x["name"], im["architecture"], im["os"])
       for x in ijson.items(open(RAW, "rb"), "results.item") for im in x["images"]]
print(f"\nQ10 images[] -> {len(res):,} rows x 3, {time.time()-t:.2f}s, parent kept")
print(f"\nQ11 FROM THE SAME PASS: {len(url)} URL prefix — {sorted(url)}")
print("    the pagination link, outside the records. pandas and polars, built")
print("    from `results`, report NONE OF ONE.")
print(f"\nQ12 no table, only events — and on a 476 KB file that costs {t_pass:.2f}s")
print("    and holds nothing. The honest table is question 3's, unchosen.")
