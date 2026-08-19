"""pandas — an npm lockfile, 1,657 packages keyed by install path

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   759 KB, 1,657 packages, depth 5
  measured      2026-08-11
  run           cd corpus/13-package-lock/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             8   NO                  NO — 12,153 columns
   2 how deep                                    9   NO                  NO — and ambiguously
   3 what is one record                          9   YES                 NO — three answers, no price
   4 always present vs sometimes                 5   YES                 yes, once told the level
   5 does any field change type                  6   YES                 YES — finds both
   6 are any object keys data                    4   -                   NO — and this is the file for it
   7 how many records                            2   YES                 yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   4   YES                 PARTLY
  11 find every path matching something          5   NO                  NO — 1,656 column names
  12 flattest honest table                       4   YES                 yes — and it is the trap
  13 needed the shape in advance?                    YES for everything but 5
  14 survives the next file unchanged?               no
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~120, and the three normalizes are the point

**THE SAME TOOL GIVES THREE DIFFERENT ANSWERS TO QUESTION 3 AND NOTHING SAYS
WHICH IS RIGHT.** One line each, all natural, all defensible:

    pd.json_normalize(doc)                          ->      1 x 12,153
    pd.json_normalize(list(doc["packages"].values())) ->  1,657 x  1,394   99.5% empty
    pd.DataFrame.from_dict(doc["packages"], orient="index") -> 1,657 x 21   71.5% empty

**`design/probe.py` prints eight row candidates WITH their costs**, including
`an entry of packages 1,657 x 1394 99% empty` — the middle one above, priced.
pandas produces that frame and says nothing about it. **A 99.5%-empty table is
not a table; it is 2.3 million cells holding 12,149 values**, and the only signal
pandas gives is that it took a moment.

**QUESTION 6 IS THE WHOLE REASON THIS FILE IS IN THE CORPUS, AND pandas FAILS IT
LOUDLY.** `packages` is keyed by INSTALL PATH — `node_modules/foo`,
`node_modules/foo/node_modules/bar` — so the keys are data. `json_normalize(doc)`
turns **each of the 1,657 paths into column names**, giving 12,153 columns for a
759 KB file, and the very first one is `packages..name` — **a double dot, because
the root package's key is the empty string.** The probe names seven keyed sites
in a section headed `KEYS THAT ARE DATA`; pandas has no way to say it.

**AND THE ENCODING IS LOSSY, WHICH IS WORSE THAN VERBOSE.** The deepest column is
`packages.node_modules/@nodelib/fs.scandir.dependencies.@nodelib/fs.stat` —
**five dots, of which only three are separators.** The other two are inside npm
package names (`fs.scandir`, `fs.stat`), and **33 package keys and 32 dependency
names contain a dot.** The path cannot be recovered from the column name by
splitting, so question 2 is over-reported by an amount the frame cannot tell you.

**WHERE IT WINS IS QUESTION 5, AND IT IS THE EXACT REVERSE OF `14-nyc-311`.**
Counting python types per column finds `engines` (dict x1050, list x1) and
`funding` (dict x282, list x28) — **both real, and both what the probe reports.**
On entry 14 the same check produced 36 false positives. The difference is that
here the genuine variation is a THIRD type beyond the NaN, so filtering at
"more than two" separates them. That is a hack that happens to work on both
files and is not a rule.
"""
import json
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pandas has no opinion; json.load read it and is silent on duplicate")
print("    keys by design. The probe reports no duplicate keys, no NaN, no big")
print("    ints — none of which pandas asked or answered. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
whole = pd.json_normalize(doc)
print(f"\nQ1  json_normalize(doc) gives {whole.shape[1]:,} COLUMNS for one row.")
print(f"    first six: {list(whole.columns)[:6]}")
print("    THIS IS THE KEYS-AS-DATA FAILURE IN ITS PUREST FORM. Every one of the")
print("    1,657 install paths became part of a column name. Note `packages..name`")
print("    — the double dot is the root package, whose key is the empty string.")
deepest = max(whole.columns, key=lambda c: c.count("."))
print(f"Q2  deepest dotted name splits into {deepest.count('.') + 1} segments"
      " for a document that is 5 deep:")
print(f"      {deepest}")
print("    AND THE NAME IS AMBIGUOUS. Five dots, three of them separators — the")
print("    other two are INSIDE the data: `fs.scandir` and `fs.stat` are package")
print("    names containing dots. 33 package keys and 32 dependency names do.")
print("    So the path CANNOT be recovered from the column name by splitting.")
print("    json_normalize also stops at lists, so `funding[].url` is unreachable.")
print("    Depth is not answered; it is over-reported by an unknowable amount. NO.")

# ── Q3/Q7. What is one record, and how many. THREE ANSWERS. ──────────────────
by_index = pd.DataFrame.from_dict(doc["packages"], orient="index")
by_values = pd.json_normalize(list(doc["packages"].values()))
print("\nQ3  three natural lines, three different tables:")
for label, f in (("json_normalize(doc)", whole),
                 ("json_normalize(packages.values())", by_values),
                 ("from_dict(packages, orient='index')", by_index)):
    holes = f.isna().sum().sum() / (f.shape[0] * f.shape[1])
    print(f"      {label:38} {f.shape[0]:>5,} x {f.shape[1]:<6,}  {holes:5.1%} empty")
print("    The probe prints EIGHT candidates with costs and names this middle one")
print("    `an entry of packages 1,657 x 1394 99% empty`. pandas prices nothing,")
print("    offers no alternative, and hands over whichever line you happened to")
print("    write. NO.")
print(f"Q7  {len(doc['packages']):,} packages — but only once you know `packages`")
print("    is the collection. pandas did not tell you that either.")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
present = by_index.notna().sum()
always = [c for c in by_index.columns if present[c] == len(by_index)]
some = sorted(((c, int(present[c])) for c in by_index.columns
               if present[c] < len(by_index)), key=lambda kv: kv[1])
print(f"\nQ4  over the 21-column frame: always {len(always)} — {always}")
print(f"Q4  sometimes {len(some)}, rarest five: {some[:5]}")
print("    Correct, and it matches the probe. But it is an answer about a frame")
print("    I had to build by choosing orient='index' first — question 3's answer")
print("    is a prerequisite for question 4 here, and the tool gives neither.")

# ── Q5. Does any field change type between records? THE ONE IT WINS. ─────────
kinds = {c: by_index[c].map(lambda v: type(v).__name__).value_counts().to_dict()
         for c in by_index.columns}
real = {c: k for c, k in kinds.items() if len(k) > 2}
print(f"\nQ5  columns holding more than TWO python types: {list(real)}")
for c, k in real.items():
    print(f"      {c:10} {k}")
print("    BOTH ARE REAL, and both are what the probe reports:")
print("      engines  object x1,050, array[1] text x1")
print("      funding  object x282, array[1] object x26, array[1] text x2")
print("    On 14-nyc-311 this same check at 'more than one type' gave 36 FALSE")
print("    positives. Here the genuine variation is a third type beyond the NaN,")
print("    so the threshold separates them. That is luck, not a rule.")

# ── Q6. Are any object keys actually data? THE POINT OF THE FILE. ────────────
print("\nQ6  pandas HAS NO WAY TO ASK THIS, and it is the reason this file exists.")
print("    `packages` is keyed by install path, so its 1,657 keys are DATA. Four")
print("    nested collections are keyed the same way — dependencies, devDependencies,")
print("    optionalDependencies, peerDependencies — by PACKAGE NAME.")
print("    The probe prints a section headed KEYS THAT ARE DATA naming seven sites")
print("    and declining an eighth. pandas turned them into 12,153 column names.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = by_index[["version", "resolved", "license"]]
print(f"\nQ8  {t.shape[0]:,} rows x {t.shape[1]} cols")
print(t.head(3).to_string())

# ── Q9. A field missing from some records, keeping those rows. ───────────────
print(f"\nQ9  license present on {int(present['license']):,} of {len(by_index):,}; rows kept")
print(by_index[["version", "license"]].head(3).to_string())

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
fund = by_index["funding"].dropna()
lists = fund[fund.map(lambda v: isinstance(v, list))]
print(f"\nQ10 the deepest array is `funding[]`: {len(lists)} packages hold a list")
flat = pd.DataFrame([{"pkg": k, **(e if isinstance(e, dict) else {"url": e})}
                     for k, v in lists.items() for e in v])
print(f"    exploded to {flat.shape[0]} x {flat.shape[1]}")
print(flat.head(3).to_string())
print("    PARTLY: `funding` is sometimes an object and sometimes a list, so the")
print("    comprehension has to test each value. json_normalize cannot cross it.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
urlish = {c: int(by_index[c].astype("string").str.contains("http", na=False).sum())
          for c in by_index.columns if by_index[c].dtype != object}
print(f"\nQ11 over the 21-column frame: { {c: n for c, n in urlish.items() if n} }")
print("    Two of the five, 1,664 of the 2,003 values. The truth, folded, is FIVE")
print("    paths: resolved 1,656 · funding.url 282 · funding[].url 53 ·")
print("    deprecated 8 · funding[] 4. THE THREE IT MISSES ARE ALL INSIDE")
print("    `funding`, which is a list-or-object column that `.str` cannot enter.")
print("    Over the WHOLE document pandas would report 1,656 separate column")
print("    names, one per package, because the keys are data. NO.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
holes = by_values.isna().sum().sum() / (by_values.shape[0] * by_values.shape[1])
print(f"\nQ12 json_normalize of the values: {by_values.shape[0]:,} x {by_values.shape[1]:,},"
      f" {holes:.1%} empty")
print("    AND THAT IS THE TRAP RATHER THAN THE ANSWER. The 1,394 columns are")
print("    1,373 dependency NAMES flattened into headers — keys-as-data again, one")
print("    level down. 2.3 million cells hold 12,149 values.")
print("    The honest table is the 21-column one, and the four keyed collections")
print("    inside it are separate tables the probe prices at 2,841, 128, 104 and")
print("    101 rows. pandas will not tell you they exist.")
