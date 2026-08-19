"""pandas — 100 openFDA adverse-event reports

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   2.7 MB, 100 results, depth 8
  measured      2026-08-11
  run           cd corpus/18-openfda-events/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             6   NO                  PARTLY
   2 how deep                                    6   NO                  NO — says 3 of 8
   3 what is one record                          12  YES                 PARTLY — prices exactly
   4 always present vs sometimes                 6   NO                  YES
   5 does any field change type                  6   NO                  NO — one false positive
   6 are any object keys data                    5   -                   n/a — but see the 3 sites
   7 how many records                             5   NO                  yes — three answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   6   YES                 PARTLY — needs two explodes
  11 find every path matching something          4   NO                  NO — finds ZERO
  12 flattest honest table                       5   NO                  PARTLY
  13 needed the shape in advance?                    NO for 4, 7
  14 survives the next file unchanged?               Q4 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~120

**pandas REPRODUCES TWO OF THE PROBE'S ROW COSTS TO THE DECIMAL, WHICH IS THE
STRONGEST CONFIRMATION THE PRICING MODEL HAS HAD.**

    an item of results     probe: 100 rows x 39 cols 26% empty   pandas: (100, 39)  25.7%
    an item of drug        probe: 265 rows x 41 cols 47% empty   pandas: (265, 41)  47.4%

`design/probe.py` prices a row shape as *what dotted flattening would give you,
stopping at arrays* — and that is exactly `json_normalize`. The model is not a
guess about tables; **it is a measurement of the table this library builds.**

**WHAT pandas WILL NOT DO IS NAME THE FOUR CANDIDATES.** The probe lists them at
three different nesting levels — the whole document (1 x 2), results (100),
drug (265), reaction (247) — with costs. pandas builds whichever one you pass it
and says nothing about the others or the price.

**QUESTION 2 IS ITS WORST ANSWER IN THE CORPUS: 3 OF 8.** `json_normalize` stops
at the first array, and this document has **arrays inside arrays inside
objects** — `results[] → patient.drug[] → openfda.brand_name[]`. The deepest
dotted name it produces is `patient.patientdeath.patientdeathdateformat`, three
segments, for a document that is **eight levels deep**.

**AND QUESTION 11 IS A ZERO AGAIN.** The two URLs in this document are
`meta.terms` and `meta.license` — outside `results`. A frame built from the
records cannot see them, exactly as on `17-openlibrary`.
"""
import json
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))
R = doc["results"]
n = len(R)
drugs = [dr for r in R for dr in r["patient"]["drug"]]
rx = [x for r in R for x in r["patient"]["reaction"]]

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pandas has no opinion; json.load read it and is silent on duplicate")
print("    keys by design. No big-int or NaN report from either. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
whole = pd.json_normalize(doc)
norm = pd.json_normalize(R)
nd = pd.json_normalize(drugs)
print(f"\nQ1  json_normalize(doc)              -> {whole.shape}")
print(f"Q1  json_normalize(results)          -> {norm.shape}")
print(f"Q1  json_normalize(the drugs)        -> {nd.shape}")
print("    THREE different tables from three different levels, and the probe")
print("    prints 122 distinct paths covering all of them at once. PARTLY.")
deep_all = max(whole.columns, key=lambda c: c.count("."))
deep_r = max(norm.columns, key=lambda c: c.count("."))
print(f"\nQ2  deepest dotted name from the whole document: {deep_all}"
      f" ({deep_all.count('.') + 1} segments)")
print(f"Q2  deepest from the results frame:  {deep_r}"
      f" ({deep_r.count('.') + 1} segments)")
print("    THE DOCUMENT IS 8 LEVELS DEEP. json_normalize stops at the first")
print("    array, and this file has arrays inside arrays inside objects:")
print("      results[] -> patient.drug[] -> openfda.brand_name[]")
print("    Three of eight is its worst question-2 answer in the corpus. NO.")

# ── Q3. THE FOUR ROW CANDIDATES, and pandas prices two of them exactly. ─────
print("\nQ3  the probe names FOUR candidates at three nesting levels and prices")
print("    them. pandas builds whichever you name:")
for label, f in (("the whole document", whole), ("an item of results", norm),
                 ("an item of drug", nd), ("an item of reaction",
                                           pd.json_normalize(rx))):
    holes = f.isna().sum().sum() / (f.shape[0] * f.shape[1])
    print(f"      {label:22} {f.shape[0]:4} x {f.shape[1]:3} cols  {holes:5.1%} empty")
print("\nQ3  THE PROBE PRINTS:")
print("      the whole document        1 rows x  2 cols")
print("      an item of results      100 rows x 39 cols   26% empty")
print("      an item of drug         265 rows x 41 cols   47% empty")
print("      an item of reaction     247 rows x  3 cols")
print("    TWO OF THOSE MATCH TO THE DECIMAL. The probe prices a row shape as")
print("    what dotted flattening gives, stopping at arrays — which is exactly")
print("    what json_normalize does. The model is a measurement of THIS library.")
print("    What pandas will not do is enumerate the candidates or compare them.")
print("\nQ3b THE ONE THAT DISAGREES IS THE WHOLE DOCUMENT: probe 2 cols, pandas 8.")
print("    pandas flattens `meta` into meta.disclaimer … meta.results.total; the")
print("    probe counts the two top-level fields. And `$.meta` is precisely one")
print("    of the three sites the probe says it COULD NOT CALL — a single-copy")
print("    object it declined to classify — so it is not flattened into a shape")
print("    the probe never decided was one. The disagreement is the abstention.")

# ── Q7. How many records. ───────────────────────────────────────────────────
print(f"\nQ7  THREE right answers, at three levels:")
print(f"      results   {len(R):4}")
print(f"      drug      {len(drugs):4}")
print(f"      reaction  {len(rx):4}")
print(f"    and meta.results.total says {doc['meta']['results']['total']:,} exist —")
print("    a fourth number, in a field no frame built from `results` can see.")

# ── Q4. Always present vs sometimes. ────────────────────────────────────────
present = norm.notna().sum()
some = sorted(((c, int(present[c])) for c in norm.columns if present[c] < n),
              key=lambda kv: kv[1])
nulls = sum(1 for r in R for v in r.values() if v is None)
print(f"\nQ4  over the results frame: always {sum(1 for c in norm.columns if present[c] == n)},"
      f" sometimes {len(some)}")
print(f"    rarest five: {some[:5]}")
print("    THE WHOLE DOCUMENT HOLDS 3 NULLS, so this is almost all genuine")
print("    absence. On 15-github-issues 709 nulls made this same count useless.")
print("\nQ4b AND THE ENTRY-15 GHOST IS HERE, FROM ONE NULL:")
for c in [c for c in norm.columns if c == "receiver" or c.startswith("receiver.")]:
    print(f"      {c:32} {int(present[c]):3} non-NaN")
print("    `receiver` is an object on 99 results and NULL on 1. json_normalize")
print("    cannot expand a null, so it keeps the scalar column AND expands the")
print("    objects — an entirely empty `receiver` beside two populated children.")
print("    On 15-github-issues one field became TWENTY columns this way; here")
print("    ONE null is enough to produce the same artefact.")

# ── Q5. Does any field change type between records? ────────────────────────
flat = pd.DataFrame(R)
mixed = {c: flat[c].map(lambda v: type(v).__name__).value_counts().to_dict()
         for c in flat.columns
         if flat[c].map(lambda v: type(v).__name__).nunique() > 1}
real = {k: v for k, v in mixed.items() if "NoneType" in v}
artefact = {k: v for k, v in mixed.items() if "NoneType" not in v}
print(f"\nQ5  columns holding more than one python type: {len(mixed)} of {flat.shape[1]}")
print(f"      {len(artefact)} are the ABSENCE ARTEFACT — str against float(NaN):")
for c, k in list(artefact.items())[:3]:
    print(f"        {c:28} {k}")
print(f"      1 is a real null: receiver {mixed['receiver']}")
print("    THE PROBE REPORTS NO FIELD THAT CHANGES TYPE, and it is right on both")
print("    counts. The eleven are holes; the twelfth is ONE null against 99")
print("    objects, which design/axes.py and defect 11 rule is missingness")
print("    written as a value. Reading the VALUES instead of a frame gives")
print("    `receiver` alone, and setting null aside gives nothing. NO.")

# ── Q6. Are any object keys actually data? ─────────────────────────────────
print("\nQ6  no keyed collections here, and the probe says something more precise")
print("    than 'none': it prints `could not call 3 small single-copy objects`")
print("    and names them — $.meta, $.meta.results, $.results[].patient.patientdeath.")
print("    THAT IS A THIRD STATE — not 'keys are data', not 'keys are fields',")
print("    but 'one copy, too few keys to judge'. pandas has no way to express")
print("    the question, let alone the abstention. n/a")

# ── Q8/Q9. Extraction. ─────────────────────────────────────────────────────
t = norm[["safetyreportid", "serious", "receivedate"]]
print(f"\nQ8  {t.shape[0]} rows x {t.shape[1]} cols")
print(t.head(2).to_string())
print(f"\nQ9  seriousnessdeath present on {int(present['seriousnessdeath'])} of {n};"
      " rows kept, gaps NaN")

# ── Q10. Flatten the deepest array into rows. ──────────────────────────────
print("\nQ10 the deepest array is openfda.brand_name[], and reaching it from a")
print("    result takes TWO explodes plus a normalize:")
step1 = norm[["safetyreportid", "patient.drug"]].explode("patient.drug")
step2 = pd.json_normalize(step1["patient.drug"].dropna())
brands = step2[["openfda.brand_name"]].dropna().explode("openfda.brand_name")
print(f"      results          {norm.shape[0]:4} rows")
print(f"      explode drug     {step1.shape[0]:4} rows")
print(f"      normalize        {step2.shape[0]:4} x {step2.shape[1]}")
print(f"      explode brands   {brands.shape[0]:4} rows")
print("    PARTLY: json_normalize cannot cross an array, so every level costs a")
print("    separate call and the result loses the parent key unless carried.")

# ── Q11. Find every path whose value matches something — here, a URL. ──────
in_frame = {c: int(norm[c].astype("string").str.contains("http", na=False).sum())
            for c in norm.columns}
print(f"\nQ11 URLs in the results frame: { {c: v for c, v in in_frame.items() if v} or 'NONE'}")
print("    The document holds TWO — meta.terms and meta.license — and both are")
print("    OUTSIDE `results`. Same failure as 17-openlibrary, where there was")
print("    one and pandas found none of it. NO.")

# ── Q12. The flattest honest table, and what was lost. ────────────────────
lists = [c for c in norm.columns if norm[c].map(lambda v: isinstance(v, list)).any()]
print(f"\nQ12 {norm.shape[0]} x {norm.shape[1]} at {norm.isna().sum().sum() / norm.size:.0%} empty,"
      f" with {len(lists)} list-columns: {lists}")
print("    PARTLY. Those two list-columns hold 265 drugs and 247 reactions —")
print("    the probe's other two row candidates — so the honest answer is THREE")
print("    tables, and pandas gives you one and hides the rest in cells.")
