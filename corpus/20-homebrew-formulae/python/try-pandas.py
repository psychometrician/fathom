"""pandas — Homebrew's whole formula index

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
  measured      2026-08-11
  run           cd corpus/20-homebrew-formulae/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             4   NO                  PARTLY
   2 how deep                                    2   NO                  NO — says 5 of 8
   3 what is one record                          5   YES                 PARTLY
   4 always present vs sometimes                12   NO                  NO — 18 of 20, and
                                                                          drops 2 of the 3
                                                                          genuinely-absent
   5 does any field change type                 14   NO                  NO — wrong both ways
   6 are any object keys data                    6   NO                  NO — it BUILDS them
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                  22   YES                 NO — see below
  11 find every path matching something          8   NO                  PARTLY
  12 flattest honest table                       4   NO                  yes, at a price
  13 needed the shape in advance?                    for 3, 8, 9, 10 — yes, and for Q10
                                                     you need it to stop the call RAISING
  14 survives the next file unchanged?               no: Q8/Q9/Q10 name columns
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~150, of which 3 are imports
  timing        json_normalize builds 8,536 x 447 in 0.3s. Nothing here is slow.

  THE RUN CORRECTED THREE THINGS AND ONE OF THEM IS THE ENTRY'S HEADLINE.

  Q10 HAS THREE ROUTES AND THE MIDDLE ONE IS THE DANGEROUS ONE.
  `record_path=["patches","resolves"]` RAISES, and `errors="ignore"` does not
  suppress it — that flag covers missing META keys, not a missing record_path.
  The obvious fix, keeping only formulae whose patches all carry `resolves`,
  runs clean, warns about nothing and returns 409 rows against a true 557 —
  27% SHORT, because 73 formulae mix patches that resolve with patches that do
  not and the filter drops them whole. Flattening `patches` by hand first gives
  the right 557 and loses `name`, because detaching the patches detached them
  from their formulae.

  Q4 DROPS TWO FIELDS ENTIRELY, and they are two of the three genuinely-absent
  ones. `head_dependencies` and `vulnerabilities` are objects where present and
  absent where not, so json_normalize spent them on dotted children and neither
  is a column. You cannot ask pandas about a field it turned into a prefix.

  Q5 IS WRONG IN BOTH DIRECTIONS AT ONCE — 10 false positives that are NaN
  beside a string, and none of the probe's nine real sites, because a list
  column types as `list` whatever is inside it.
"""
import json
import time
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pandas never sees the bytes; json.load did, and is silent on")
print("    duplicate keys, big ints and NaN by design. Answered CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
t = time.time()
norm = pd.json_normalize(doc)
t_norm = time.time() - t
print(f"\nQ1  json_normalize gives {norm.shape[1]:,} columns in {t_norm:.1f}s")
seg = max(c.count(".") for c in norm.columns) + 1
print(f"Q2  deepest dotted name has {seg} segments. The document is 8 deep.")
print("    json_normalize stops at the first ARRAY, so everything under")
print("    patches[], requirements[], post_install_steps[] is invisible to it.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
holes = norm.isna().sum().sum() / (norm.shape[0] * norm.shape[1])
print(f"\nQ3  a formula: {norm.shape[0]:,} rows x {norm.shape[1]:,} cols, {holes:.0%} NaN")
print("    The probe prices the same candidate at 8,536 x 447, 85% empty, and")
print("    names ten others. pandas names one and prices it only if you ask.")
print(f"Q7  {len(doc):,} formulae")

# ── Q4. Always present vs sometimes. THE ONE IT GETS WRONG, TWICE. ───────────
present = norm.notna().sum()
flat_cols = [c for c in norm.columns if "." not in c]
some = sorted([c for c in flat_cols if present[c] < len(norm)])

# the truth, taken from the parsed document rather than the frame
root_keys = [set(r) for r in doc]
allk = set().union(*root_keys)
truly_absent = sorted(k for k in allk if sum(k in r for r in root_keys) < len(doc))
null_only = sorted(k for k in allk
                   if k not in truly_absent
                   and any(r.get(k) is None for r in doc))
print(f"\nQ4  the document: {len(truly_absent)} fields sometimes ABSENT, "
      f"{len(null_only)} always present but NULL")
print(f"    absent: {truly_absent}")
union = set(truly_absent) | set(null_only)
print(f"Q4  pandas: {len(some)} of {len(flat_cols)} un-dotted columns not always filled,")
print(f"    against a true union of {len(union)}. A key that is present-and-null and a")
print("    key that is missing are both NaN once a frame exists — ENTRY 15's")
print("    DISCRIMINATOR AT SCALE, on eight thousand records instead of a hundred.")
missing = sorted(union - set(some))
print(f"Q4  AND THE {len(missing)} IT DROPS ALTOGETHER ARE THE INTERESTING ONES: {missing}")
print("    Both are OBJECTS where present and ABSENT where not, so json_normalize")
print("    spent them on dotted children — head_dependencies.dependencies,")
print("    vulnerabilities.open — and the field itself is not a column at all.")
print("    Two of the three genuinely-absent fields in this document cannot be")
print("    asked about in pandas, because it turned each of them into a prefix.")

# ── Q5. Does any field change type between records? ──────────────────────────
mixed = []
for c in flat_cols:
    kinds = norm[c].map(lambda v: type(v).__name__).value_counts()
    kinds = kinds[kinds.index != "NoneType"]
    if len(kinds) > 1:
        mixed.append((c, kinds.to_dict()))
print(f"\nQ5  un-dotted columns holding more than one python type: {len(mixed)}")
for c, k in mixed[:6]:
    print(f"    {c}: {k}")
nan_only = [c for c, k in mixed if set(k) == {"float", "str"}
            and norm[c].map(lambda v: isinstance(v, float)).sum() == norm[c].isna().sum()]
print(f"Q5  of those {len(mixed)}, {len(nan_only)} are float-vs-str where every float is NaN.")
print("    THOSE ARE FALSE POSITIVES BY THIS CORPUS'S OWN RULE — defect 11 and")
print("    `design/axes.py` both say a null is not a type — and it is the same")
print("    false positive entry 25 recorded on `properties.alert`.")
print("    Meanwhile the probe's NINE real sites are all invisible here: pandas")
print("    types a list-valued column `list` whatever is inside it, so")
print("    `uses_from_macos` — strings on 1,163 records, objects on 632 — reads")
print("    as one type on every row. WRONG IN BOTH DIRECTIONS AT ONCE:")
print("    it reports variation that is not there and misses all that is.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
files_cols = [c for c in norm.columns if c.startswith("bottle.stable.files.")]
var_cols = [c for c in norm.columns if c.startswith("variations.")]
print(f"\nQ6  pandas does not answer this. It BUILDS the keys into column names:")
print(f"    bottle.stable.files.* -> {len(files_cols):,} columns")
print(f"    variations.*          -> {len(var_cols):,} columns")
print(f"    those two are {(len(files_cols)+len(var_cols))/norm.shape[1]:.0%} of the frame, and they are")
print("    16 and 15 platform names respectively. The probe folds both to one")
print("    path each and declines to call them data. pandas turns the data into")
print("    schema, which is the failure mode this question exists to catch.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl = norm[["name", "desc", "homepage"]]
print(f"\nQ8  {tbl.shape[0]:,} rows x {tbl.shape[1]} cols")
print(tbl.head(2).to_string())

# ── Q9. A field missing from some records, keeping those rows. ───────────────
print(f"\nQ9  executables filled on {int(present['executables']):,} of {len(norm):,}")
print("    The row is kept and the hole is NaN — right answer, wrong reason:")
print("    185 of those are genuinely absent and pandas cannot say which.")

# ── Q10. Flatten the deepest array into rows. THE ONE THAT RAISED. ───────────
# FIRST DRAFT RAISED, and `errors="ignore"` did not save it:
#   KeyError: "Key 'resolves' not found. If specifying a record_path, all
#              elements of data should have the path."
# Only 508 of 1,185 patches carry `resolves`. The documented `errors="ignore"`
# covers missing META keys and NOT a missing record_path — so the flag that
# looks like it handles raggedness does not handle the raggedness that is here.
try:
    pd.json_normalize(doc, record_path=["patches", "resolves"], meta=["name"],
                      errors="ignore")
    print("\nQ10 record_path=['patches','resolves'] SUCCEEDED — rewrite this note")
except KeyError as e:
    print(f"\nQ10 record_path=['patches','resolves'] RAISES: {str(e)[:60]}…")
    print("    and errors='ignore' does NOT suppress it — that flag is for meta.")
# The obvious fix — keep only formulae whose patches all carry `resolves` —
# runs clean and is WRONG. "All elements of data should have the path" means
# EVERY patch, so a formula with two patches and one `resolves` is dropped whole.
keep = [f for f in doc if (f.get("patches") or [])
        and all("resolves" in p for p in f["patches"])]
res = pd.json_normalize(keep, record_path=["patches", "resolves"], meta=["name"])
true = sum(len(p["resolves"]) for f in doc
           for p in (f.get("patches") or []) if "resolves" in p)
print(f"Q10 filter to the {len(keep)} formulae where EVERY patch resolves: "
      f"{res.shape[0]} x {res.shape[1]}")
print(f"    THE TRUE COUNT IS {true}. This runs clean, warns about nothing, and is")
print(f"    {true - res.shape[0]} rows — {(true-res.shape[0])/true:.0%} — SHORT, because 73 formulae mix patches")
print("    that resolve with patches that do not, and the filter drops them whole.")
# The correct route: flatten one level yourself, and lose the parent key doing it.
patches = [p for f in doc for p in (f.get("patches") or []) if "resolves" in p]
res2 = pd.json_normalize(patches, record_path=["resolves"])
print(f"Q10 flatten patches yourself, then normalize: {res2.shape[0]} x {res2.shape[1]} — correct,")
print("    and `name` is gone: detaching the patches detached them from formulae.")
print("    Threading the parent back is a python loop, not a pandas call.")
print("    THREE ROUTES: raises, silently short, or right-but-detached — and only")
print("    the middle one looks like success. jq's `.patches[]?.resolves[]?` with")
print("    `.name` in scope is one expression that does all of it.")
print("    The genuinely deepest array — variations.<key>.head_dependencies.")
print("    uses_from_macos[] — cannot be named at all, because <key> is data.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
naive, strict = [], []
for c in norm.columns:
    s = norm[c].astype("string")
    if s.str.startswith("http").fillna(False).any():
        naive.append(c)
    if s.str.match(r"^https?://").fillna(False).any():
        strict.append(c)
print(f"\nQ11 columns with any http-prefixed value: {len(naive)}")
print(f"Q11 columns matching ^https?:// :          {len(strict)}")
print(f"    dropped: {sorted(set(naive) - set(strict))}")
print("    Fifteen formulae are NAMED http* — httpd, httpie, http-server — so")
print("    the prefix test reports `name` as a URL column. Same trap as jq's.")
print("    PARTLY, and for a second reason: this is a COLUMN scan. Every URL")
print("    inside patches[] is in a list-cell and invisible.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
listcols = [c for c in norm.columns if norm[c].map(lambda v: isinstance(v, list)).any()]
print(f"\nQ12 {norm.shape[0]:,} x {norm.shape[1]:,}, {holes:.0%} NaN")
print(f"    {len(listcols)} columns still hold python lists — list-columns, which")
print("    god's spec refuses. What was lost: nothing, and that is the problem —")
print("    the price was paid in width, not in loss.")
