"""pandas — cargo metadata for this repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   27 KB, 8 packages, depth 8
  measured      2026-08-11
  run           cd corpus/24-cargo-metadata/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             6   YES                 PARTLY
   2 how deep                                    2   NO                  NO
   3 what is one record                          6   YES                 one of nine
   4 always present vs sometimes                 8   NO                  PARTLY
   5 does any field change type                  8   NO                  false positives
   6 are any object keys data                   16   NO                  IT BUILDS THEM, AND
                                                                          THE NAMES ARE DATA
   7 how many records                             2  NO                  yes
   8 three named fields to a table                2 YES                 yes
   9 a field missing from some rows                2 YES                 PARTLY
  10 flatten the deepest array                     6 YES                 yes
  11 find every path matching something            4 NO                  PARTLY
  12 flattest honest table                         5 NO                  yes
  13 needed the shape in advance?                    yes — `packages` by name
  14 survives the next file unchanged?               NO, and see below
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~100

  QUESTION 6 IS THIS ENTRY'S POINT AND PANDAS ANSWERS IT BY DOING THE WRONG
  THING VISIBLY. `json_normalize` turns `$.packages[].features` into one column
  per FEATURE NAME — `features.zlib-ng-compat`, `features.rustc-dep-of-std` —
  so the frame's column names are this repository's dependency graph.

  AND THAT IS WHY Q14 IS NO. Add one dependency to `Cargo.toml` and the column
  set changes. Every other corpus document that broke Q14 broke it because the
  ATTEMPT named a column; here the SCHEMA is a function of the data, so nothing
  written against this frame survives a `cargo add`.
"""
import json
import time
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))
pkgs = doc["packages"]

print("\nQ0  json.load read it and said nothing. CANNOT.")

whole = pd.json_normalize(doc)
print(f"\nQ1  json_normalize(doc) -> {whole.shape}")
print("    ONE ROW, the envelope. `packages` is a list in a cell — the same")
print("    shape entries 21, 22 and 23 met.")
t = time.time()
norm = pd.json_normalize(pkgs)
print(f"Q1  json_normalize(packages) -> {norm.shape[0]} x {norm.shape[1]}, {time.time()-t:.3f}s")
print(f"Q2  deepest dotted name has {max(c.count('.') for c in norm.columns)+1} segments;"
      " the document is 8 deep.")
print("    `json_normalize` stops at the first ARRAY, and `targets`,")
print("    `dependencies` and `resolve.nodes` are all arrays.")

# ── Q6. THE CENTREPIECE. ────────────────────────────────────────────────────
fcols = [c for c in norm.columns if c.startswith("features.")]
print(f"\nQ6  THE PROBE CALLS $.packages[].features KEYS THAT ARE DATA.")
print(f"    pandas turned them into {len(fcols)} COLUMNS:")
print(f"    {[c.split('.', 1)[1] for c in fcols[:8]]} …")
filled = norm[fcols].notna().sum()
print(f"Q6  of those {len(fcols)} columns, {(filled == 1).sum()} are filled on exactly ONE")
print(f"    package and {(filled == 0).sum()} on none. THE COLUMN NAMES ARE THIS")
print("    REPOSITORY'S DEPENDENCY GRAPH — `zlib-ng-compat` is not a field, it")
print("    is a Cargo feature that exists because flate2 is in Cargo.toml.")
hy = [c for c in fcols if "-" in c.split(".", 1)[1]]
print(f"Q6  and {len(hy)} of them contain a HYPHEN, so `norm.features.zlib-ng-compat`")
print("    is a subtraction and `df.query` needs backticks — an escaping problem")
print("    that entries 21 and 23 met on genuine FIELD names. HERE THE NAMES ARE")
print("    VALUES, so the escaping hazard is a property of the data.")
print("\nQ6  AND THIS IS WHY QUESTION 14 IS NO. Add one dependency to Cargo.toml")
print("    and the column set changes. Every other corpus document broke Q14")
print("    because the ATTEMPT named a column; here the SCHEMA is a function of")
print("    the data, so nothing written against this frame survives `cargo add`.")

# ── Q3/Q4/Q5/Q7. ────────────────────────────────────────────────────────────
holes = norm.isna().sum().sum() / (norm.shape[0] * norm.shape[1])
print(f"\nQ3  an item of packages: {norm.shape[0]} x {norm.shape[1]}, {holes:.0%} NaN")
print("    the probe prices the same candidate at 8 x 57, 63% empty, and names")
print(f"    eight others. The {len(fcols)} feature columns are {len(fcols)/norm.shape[1]:.0%} of the width.")
flat = [c for c in norm.columns if "." not in c]
present = norm.notna().sum()
some = [c for c in flat if present[c] < len(norm)]
rk = [set(p) for p in pkgs]
absent = [k for k in set().union(*rk) if sum(k in p for p in rk) < len(pkgs)]
nulls = {k: sum(1 for p in pkgs if p.get(k) is None) for k in set().union(*rk)}
alln = sorted(k for k, v in nulls.items() if v == len(pkgs))
print(f"\nQ4  pandas: {len(some)} un-dotted columns not always filled")
print(f"Q4  the document: {len(absent)} ever ABSENT, "
      f"{len([k for k, v in nulls.items() if v])} written null, NULL ON ALL 8: {alln}")
print("    Every hole is a written null; nothing is ever absent. pandas cannot")
print("    say so, and on this document nothing depends on it.")
mixed = [(c, norm[c].map(lambda v: type(v).__name__).value_counts().to_dict())
         for c in flat
         if norm[c].map(lambda v: type(v).__name__).nunique() > 1]
print(f"\nQ5  un-dotted columns with more than one python type: {len(mixed)}")
for c, k in mixed[:4]:
    print(f"    {c}: {k}")
print("    The probe reports NONE, and jq confirms zero once `an empty array is")
print("    not a type` is applied. Whatever is above is NaN beside a value —")
print("    the false positive entries 20, 23 and 25 all recorded.")
print(f"\nQ7  {len(pkgs)} packages, {len(doc['workspace_members'])} workspace members,"
      f" {len(doc['resolve']['nodes'])} resolve nodes")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
print(f"\nQ8  {norm[['name', 'version', 'edition']].shape}")
print(norm[["name", "version", "edition"]].head(2).to_string())
print(f"\nQ9  `description` filled on {int(present['description'])} of {len(norm)}, rows kept")
t = time.time()
tg = pd.json_normalize(pkgs, record_path=["targets"], meta=["name"], meta_prefix="pkg_")
print(f"\nQ10 record_path=['targets'] -> {tg.shape[0]} x {tg.shape[1]}, {time.time()-t:.3f}s")
print("    No raise: every package has `targets`. `meta_prefix` was needed all")
print("    the same, because a target ALSO has a `name` — the collision entry 21")
print("    met with `DOI`, on a second document.")
print("    THE DEEPEST array is resolve.nodes[].deps[].dep_kinds[] and it is not")
print("    under `packages` at all, so this frame cannot reach it.")
urlish = [c for c in norm.columns
          if norm[c].astype("string").str.match(r"^https?://").fillna(False).any()]
print(f"\nQ11 columns with a URL: {urlish}")
print("    jq reports 5 distinct URL PATHS; two of them are under")
print("    `metadata.release.pre-release-replacements[]`, inside a list-column.")
lists = [c for c in norm.columns if norm[c].map(lambda v: isinstance(v, list)).any()]
print(f"\nQ12 {norm.shape[0]} x {norm.shape[1]}, {holes:.0%} NaN, {len(lists)} list-columns")
print("    and 28 of the columns are feature names. THE HONEST TABLE FOR THIS")
print("    DOCUMENT IS NARROWER THAN THE ONE PANDAS BUILDS, and the difference")
print("    is exactly question 6.")
