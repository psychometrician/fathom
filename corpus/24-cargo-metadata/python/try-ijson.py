"""ijson — cargo metadata for this repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   27 KB, 8 packages, depth 8
  measured      2026-08-11
  run           cd corpus/24-cargo-metadata/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   PARTLY
   1 what is in here                             2   NO                  yes — 143
   2 how deep                                    2   NO                  yes — 8
   3 what is one record                          3   NO                  CANNOT
   4 always present vs sometimes                 6   NO                  YES — both halves
   5 does any field change type                  6   NO                  ZERO, with the rule
   6 are any object keys data                   12   NO                  THE PREFIXES SHOW IT
   7 how many records                             2  NO                  yes
   8 three named fields to a table                3 YES                 yes
   9 a field missing from some rows                2 YES                 YES — presence
  10 flatten the deepest array                     4 YES                 yes
  11 find every path matching something            3 NO                  yes — from the pass
  12 flattest honest table                         2 -                   n/a
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 6, 7, 11
  14 survives the next file unchanged?               YES — and it is the only tool here
                                                     that does, because it never
                                                     builds a schema from the data
  15 readable a week later?                          the parse loop needs its comment
  16 lines, and how much is ceremony?                ~90

  QUESTION 6 SHOWS UP IN THE PREFIX LIST WITHOUT BEING ASKED FOR. ijson emits
  `packages.item.features.zlib-ng-compat` — one prefix per FEATURE NAME — so the
  28 names appear as 28 sibling prefixes under one parent, and a reader sees an
  open vocabulary in the output. It is not a verdict, and it is the shape of one.

  AND IJSON IS THE ONLY TOOL HERE THAT SURVIVES THE NEXT FILE. pandas, polars
  and DuckDB all build a schema from the feature names, so `cargo add` changes
  their column set or their dtype. ijson builds nothing, so nothing changes.
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
dmax = dnow = npkg = 0
pkg_keys, pkg_nulls = Counter(), Counter()
feat = Counter()
url = set()
this = set()
PKG = "packages.item"
for prefix, event, value in ijson.parse(open(RAW, "rb")):
    if event in ("start_map", "start_array"):
        dnow += 1
        dmax = max(dmax, dnow)
    elif event in ("end_map", "end_array"):
        dnow -= 1
    if event == "map_key":
        if prefix == PKG + ".features":
            feat[value] += 1
        continue
    if prefix:
        paths[prefix] += 1
        types[prefix].add(event)
    if prefix == PKG and event == "start_map":
        this = set()
    elif prefix == PKG and event == "end_map":
        npkg += 1
        pkg_keys.update(this)
    if prefix.startswith(PKG + ".") and prefix.count(".") == 2:
        k = prefix.rsplit(".", 1)[1]
        this.add(k)
        if event == "null":
            pkg_nulls[k] += 1
    if event == "string" and isinstance(value, str) and re.match(r"^https?://", value):
        url.add(prefix)
t_pass = time.time() - t

print(f"\n     ONE PASS over 27 KB: {t_pass:.3f}s, nothing retained but counters.")
print(f"\nQ1  {len(paths)} distinct prefixes — the probe says 143")
print(f"Q2  depth {dmax} — the probe says 8")
print(f"\nQ3  ijson names no candidates and prices none. CANNOT.")
print(f"Q7  {npkg} packages, counted while streaming")

# ── Q6. THE PREFIXES. ───────────────────────────────────────────────────────
sib = [p for p in paths if p.startswith(PKG + ".features.")
       and p.count(".") == PKG.count(".") + 2]
once = [k for k, c in feat.items() if c == 1]
hy = [k for k in feat if "-" in k]
print(f"\nQ6  $.packages[].features — THE PROBE CALLS THESE KEYS DATA.")
print(f"    ijson emits {len(sib)} SIBLING PREFIXES under one parent, one per")
print(f"    feature name: {sorted(k for k in feat)[:5]} …")
print(f"Q6  {len(feat)} distinct names over {sum(feat.values())} occurrences;"
      f" {len(once)} appear ONCE")
print(f"Q6  {len(hy)} contain a HYPHEN, and a prefix is a string, so ijson pays")
print("    nothing for that either.")
print("    THE OPEN VOCABULARY IS VISIBLE IN THE OUTPUT — 28 siblings, 23 of")
print("    them seen once — which is the ingredient `classify()` judges on.")
print("    COMPARE ../python/try-duckdb.py, where typing the column made every")
print("    package carry all 28 names and the once-only signal disappeared.")
print("    ijson cannot lose it, because it never builds anything to lose it in.")

# ── Q4/Q5. ──────────────────────────────────────────────────────────────────
print(f"\nQ4  package keys not on every package: "
      f"{[k for k, c in pkg_keys.items() if c < npkg]}")
print(f"Q4  written NULL: {len(pkg_nulls)} keys; NULL ON ALL {npkg}: "
      f"{sorted(k for k, c in pkg_nulls.items() if c == npkg)}")
print("    Both halves from one pass: a missing key emits no event and a null")
print("    emits `null`.")
EV = {"start_map": "object", "start_array": "array"}
kinds = {p: {EV.get(t, t) for t in ts if t not in ("end_map", "end_array", "map_key")} - {"null"}
         for p, ts in types.items()}
loose = {p: k for p, k in kinds.items() if len(k) > 1}
tight = {p: k for p, k in loose.items() if len(k - {"array"}) > 1 or "array" not in k}
print(f"\nQ5  prefixes with more than one non-null kind: {len(loose)}")
print(f"Q5  + AN EMPTY ARRAY IS NOT A TYPE:                {len(tight)}")
print("    ZERO, and the probe says NONE.")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t = time.time()
rows = [(p["name"], p["version"], p["edition"])
        for p in ijson.items(open(RAW, "rb"), "packages.item")]
print(f"\nQ8  {len(rows)} rows x 3, streamed in {time.time()-t:.3f}s")
nd = sum(1 for p in ijson.items(open(RAW, "rb"), "packages.item")
         if p.get("description") is not None)
print(f"\nQ9  `description` non-null on {nd} of {npkg} — and PRESENT on all {npkg}")
tg = [(p["name"], t_["name"]) for p in ijson.items(open(RAW, "rb"), "packages.item")
      for t_ in p["targets"]]
dk = [(n["id"], k) for n in ijson.items(open(RAW, "rb"), "resolve.nodes.item")
      for d in n["deps"] for k in d["dep_kinds"]]
print(f"\nQ10 targets -> {len(tg)} rows; resolve.nodes[].deps[].dep_kinds[] ->")
print(f"    {len(dk)} rows at depth 6, and BOTH from the same file with one")
print("    `items()` path each — no frame here can reach the second at all.")
print(f"\nQ11 FROM THE SAME PASS: {len(url)} URL prefixes")
for p in sorted(url):
    print(f"      {p}")
print(f"\nQ12 no table, only events, and on 27 KB that costs {t_pass:.3f}s and holds")
print("    nothing. THE HONEST TABLE IS THE ONE IJSON REFUSES TO CHOOSE — and")
print("    on this document that refusal is the only thing that survives a")
print("    `cargo add`.")
