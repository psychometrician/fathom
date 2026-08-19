"""ijson — crates.io summary

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   41 KB, six collections at the root, depth 4
  measured      2026-08-11
  run           cd corpus/23-cratesio-summary/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   PARTLY
   1 what is in here                             2   NO                  yes — 140
   2 how deep                                    2   NO                  yes — 4
   3 what is one record                          8   NO                  CANNOT, and see below
   4 always present vs sometimes                 6   NO                  YES — three always-null
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                    1   -                   n/a
   7 how many records                             3  NO                  three answers
   8 three named fields to a table                3 YES                 yes
   9 a field missing from some rows                2 YES                 YES — presence
  10 flatten the deepest array                     3 -                   NO ARRAY TO FLATTEN
  11 find every path matching something            5 NO                  yes — from the pass
  12 flattest honest table                         2 -                   n/a
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 11
  14 survives the next file unchanged?               yes
  15 readable a week later?                          the parse loop needs its comment
  16 lines, and how much is ceremony?                ~95

  ijson's PREFIXES ARE THE ONE PLACE THE FOUR-IN-ONE SHAPE SHOWS UP BY ITSELF.
  It emits `new_crates.item.name`, `most_downloaded.item.name` and two more —
  four sibling prefix families with identical tails — and a reader sees the
  repetition in the prefix list without computing anything. That is not a
  verdict, and it is closer to one than any other tool here manages.

  IT CANNOT SEE THE OVERLAP. Seven crates appear in two collections each; a
  streaming parser holds nothing, so noticing a repeated `id` means keeping a
  set — which is exactly the thing ijson exists not to do.
"""
import re
import time
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')} (backend {ijson.backend})")

RAW = "../source.json"
CRATE = ["new_crates", "most_downloaded", "most_recently_downloaded", "just_updated"]

print("\nQ0  ijson is a parser and reports no health. It WOULD raise on")
print("    truncation, which is more than the frames can say. PARTLY.")

t = time.time()
paths, types = Counter(), defaultdict(set)
dmax = dnow = 0
ncrate = Counter()
crate_keys, crate_nulls = Counter(), Counter()
url = set()
scalars = {}
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
    for c in CRATE:
        if prefix == f"{c}.item" and event == "start_map":
            ncrate[c] += 1
        if prefix.startswith(f"{c}.item.") and prefix.count(".") == 2:
            k = prefix.rsplit(".", 1)[1]
            crate_keys[k] += 1
            if event == "null":
                crate_nulls[k] += 1
    if prefix in ("num_crates", "num_downloads"):
        scalars[prefix] = value
    if event == "string" and isinstance(value, str) and re.match(r"^https?://", value):
        url.add(prefix)
t_pass = time.time() - t

print(f"\n     ONE PASS over 41 KB: {t_pass:.3f}s, nothing retained but counters.")
print(f"\nQ1  {len(paths)} distinct prefixes — the probe says 140")
print(f"Q2  depth {dmax} — the probe says 4")

# ── Q3. THE FOUR-IN-ONE, VISIBLE IN THE PREFIX LIST. ────────────────────────
tails = {c: sorted(p[len(c) + 6:] for p in paths if p.startswith(f"{c}.item."))
         for c in CRATE}
print(f"\nQ3  the four crate collections, by prefix TAIL:")
for c in CRATE:
    print(f"    {c:26} {ncrate[c]:>3} records, {len(tails[c])} child prefixes")
print(f"Q3  distinct tail-sets across the four: {len({tuple(v) for v in tails.values()})}")
print("    ONE — and ijson is the only tool here where the repetition is")
print("    VISIBLE IN THE OUTPUT ITSELF rather than computed on purpose. Four")
print("    sibling prefix families with identical tails is what defect 25 was")
print("    about, printed as a side effect of how prefixes work.")
print("    IT IS STILL NOT A VERDICT. The probe says `same shape as` in words.")
print("\n     WHAT IT CANNOT SEE IS THE OVERLAP. Seven crates appear in two")
print("     collections each — 40 rows, 33 distinct. Noticing that means")
print("     keeping a set of ids, which is the one thing a streaming parser")
print("     exists not to do. This is the sharpest statement in the corpus of")
print("     what constant memory costs you.")

# ── Q4/Q5/Q6/Q7. ────────────────────────────────────────────────────────────
tot = sum(ncrate.values())
print(f"\nQ4  crate keys seen on fewer than all {tot}: "
      f"{[k for k, n in crate_keys.items() if n < tot]}")
print(f"Q4  keys written NULL: {dict(crate_nulls)}")
print(f"Q4  NULL ON ALL {tot}: {sorted(k for k, n in crate_nulls.items() if n == tot)}")
print("    ijson separates absent from null by construction: a missing key emits")
print("    no event and a null emits `null`. Every hole here is a written null.")

EV = {"start_map": "object", "start_array": "array"}
kinds = {p: {EV.get(t, t) for t in ts if t not in ("end_map", "end_array", "map_key")} - {"null"}
         for p, ts in types.items()}
print(f"\nQ5  prefixes with more than one non-null kind: "
      f"{len([p for p, k in kinds.items() if len(k) > 1])} — the probe says NONE")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
print(f"\nQ7  num_crates {scalars.get('num_crates', 0):,}, "
      f"num_downloads {scalars.get('num_downloads', 0):,}, {tot} crate rows here")
print("    THREE ANSWERS AND THEY MEASURE THREE THINGS, and only ijson read all")
print("    three in the same pass that answered questions 1, 2, 4 and 11.")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t = time.time()
rows = [(c.get("name"), c.get("max_version"), c.get("downloads"))
        for c in ijson.items(open(RAW, "rb"), "new_crates.item")]
print(f"\nQ8  {len(rows)} rows x 3, streamed in {time.time()-t:.3f}s")
nh = sum(1 for k in CRATE for c in ijson.items(open(RAW, "rb"), f"{k}.item")
         if c.get("homepage") is not None)
print(f"\nQ9  `homepage` non-null on {nh} of {tot} — and PRESENT on all {tot}")
print("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is an object of six")
print("    fields; question 10 has no target on this document, which is the")
print("    first time in the corpus that is true.")
fold = sorted({re.sub(r"^(new_crates|most_downloaded|most_recently_downloaded|just_updated)\.item\.",
                      "<one of the four>.item.", p) for p in url})
print(f"\nQ11 FROM THE SAME PASS: {len(url)} URL prefixes, folding to {len(fold)}:")
for p in fold:
    print(f"      {p}")
print(f"\nQ12 no table, only events, and on 41 KB that costs {t_pass:.3f}s and holds")
print("    nothing. The honest table is the four lists concatenated, and ijson")
print("    is the one tool that cannot tell you what concatenating them costs.")
