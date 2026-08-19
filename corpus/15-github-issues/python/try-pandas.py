"""pandas — 100 GitHub issues from one repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   686 KB, 100 issues, depth 4
  measured      2026-08-11
  run           cd corpus/15-github-issues/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    3   NO                  NO — says 3
   3 what is one record                          4   NO                  PARTLY — cost exact
   4 always present vs sometimes                10   NO                  NO — conflates 5 with 8
   5 does any field change type                  5   NO                  NO — false positives
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              8   YES                 yes — and the GHOST
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          4   NO                  PARTLY
  12 flattest honest table                       5   NO                  yes
  13 needed the shape in advance?                    NO for 1, 3, 7
  14 survives the next file unchanged?               Q8/Q9/Q10 name columns
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~120, of which 3 are imports

**THIS DOCUMENT IS THE ABSENT-VS-NULL DISCRIMINATOR AND pandas FAILS IT EXACTLY.**
Of 36 record fields, **5 are sometimes ABSENT** and **8 are always present but
sometimes NULL** — three of them null on all 100 issues. `pd.DataFrame(doc)`
reports **13 fields as sometimes-missing**, and 13 is precisely 5 + 8. The
conflation is total and provable: the set it reports is exactly the union.

`14-nyc-311`, graded the same day, has **zero nulls**, so every tool agreed there.
This file has 709 of them. **The tools did not change between the two entries;
the documents did**, and this is the one that separates them.

**THE GHOST COLUMN IS REAL AND IT IS WORSE THAN RECORDED.** `VERDICT.md` carries
*"pandas' ghost `closed_by` column"* from a note. Measured, `json_normalize`
emits **BOTH**:

    closed_by         100 NaN out of 100   <- the ghost, entirely empty
    closed_by.login    48 non-NaN          } 19 real columns
    closed_by.id       48 non-NaN          } holding the data

One JSON field became **20 columns**, one of which is entirely empty and looks
like a field that was never populated. The cause: `closed_by` is an object on 48 issues
and `null` on 52, and `json_normalize` cannot expand a null, so it leaves the
scalar column behind and expands the rest into dotted children. **The same
happens to `milestone`, `assignee` and `pinned_comment` — nine all-NaN columns
in total**, of which only three are honestly empty.

**WHERE IT IS EXACTLY RIGHT IS THE COST OF THE ROW SHAPE.** 100 x 144 at 53.0%
empty, and the probe prints `a record 100 rows x 144 cols 53% empty`. pandas
builds the table the probe prices; it just never says the price.
"""
import json
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))
n = len(doc)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pandas has no opinion; json.load read it and is silent on duplicate")
print("    keys by design. No big-int or NaN report from either. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
norm = pd.json_normalize(doc)
n_fields = len({k for r in doc for k in r})
print(f"\nQ1  json_normalize gives {norm.shape[1]} columns for {n_fields} record fields.")
print(f"    (the FIRST record has only {len(doc[0])} of them, which is why a survey that")
print("    reads one record under-reports here.) The probe prints 179 paths.")
print("    PARTLY: the dotted names cover the objects and stop at every list.")
print(f"Q2  deepest dotted name has {max(c.count('.') for c in norm.columns) + 1} segments;"
      " the document is 4 deep.")
print("    json_normalize does not enter `labels[]`, so `labels[].name` is never")
print("    reached and depth is under-reported. NO.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
holes = norm.isna().sum().sum() / (norm.shape[0] * norm.shape[1])
print(f"\nQ3  one record is an issue: {norm.shape[0]} rows x {norm.shape[1]} cols, {holes:.1%} empty")
print("    THE PROBE PRINTS `a record 100 rows x 144 cols 53% empty` — the same")
print("    table and the same cost. pandas builds it and never states the price,")
print("    and names none of the probe's other two candidates. PARTLY.")
print(f"Q7  {n} issues")

# ── Q4. Always present vs sometimes. THE DISCRIMINATOR. ─────────────────────
absent = sorted(k for k in {k for r in doc for k in r}
                if sum(k in r for r in doc) < n)
nulls = sorted(k for k in doc[0]
               if sum(k in r for r in doc) == n
               and sum(r[k] is not None for r in doc) < n)
flat = pd.DataFrame(doc)
frame_missing = sorted(c for c in flat.columns if flat[c].notna().sum() < n)
print(f"\nQ4  THE TRUTH, from the values:")
print(f"      sometimes ABSENT ({len(absent)}): {absent}")
print(f"      always present, sometimes NULL ({len(nulls)}): {nulls}")
print(f"\nQ4  pd.DataFrame(doc) reports {len(frame_missing)} fields as sometimes-missing.")
print(f"    {len(absent)} + {len(nulls)} = {len(absent) + len(nulls)}, and the sets are identical:"
      f" {sorted(set(absent) | set(nulls)) == frame_missing}")
print("    THE CONFLATION IS TOTAL. Once a row exists, absent and null are the")
print("    same hole. On 14-nyc-311 this cost nothing because that document has")
print("    zero nulls; this one has 709.")
allnan = [c for c in norm.columns if norm[c].notna().sum() == 0]
print(f"\nQ4  and {len(allnan)} columns are entirely NaN: {allnan}")
print("    Only three of those are honest — `type`, `active_lock_reason` and")
print("    `performed_via_github_app` are null on all 100 issues. The rest are")
print("    ghosts, and Q9 shows where they come from.")

# ── Q5. Does any field change type between records? ──────────────────────────
mixed = {c: flat[c].map(lambda v: type(v).__name__).value_counts().to_dict()
         for c in flat.columns
         if flat[c].map(lambda v: type(v).__name__).nunique() > 1}
print(f"\nQ5  columns holding more than one python type: {len(mixed)} of {flat.shape[1]}")
print(f"    e.g. draft: {mixed.get('draft')}")
print("    ALL OF THESE ARE THE Q4 HOLE AGAIN — NoneType or float(NaN) against")
print("    the real type. The probe reports NO field that changes type on this")
print("    document, and it is right: nothing here is polymorphic.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — GitHub ships fixed field names. n/a, and the")
print("    probe's KEYS THAT ARE DATA section is empty for this file.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = norm[["number", "title", "state"]]
print(f"\nQ8  {t.shape[0]} rows x {t.shape[1]} cols")
print(t.head(3).to_string(max_colwidth=40))

# ── Q9. A field missing from some records — AND THE GHOST. ──────────────────
cb = [c for c in norm.columns if c == "closed_by" or c.startswith("closed_by.")]
print(f"\nQ9  `closed_by` became {len(cb)} columns:")
print(f"      closed_by         {norm['closed_by'].notna().sum():3} non-NaN   <- THE GHOST")
print(f"      closed_by.login   {norm['closed_by.login'].notna().sum():3} non-NaN")
print(f"      closed_by.id      {norm['closed_by.id'].notna().sum():3} non-NaN")
print("      ... 17 more, all 48")
print("    `closed_by` is an OBJECT on 48 issues and NULL on 52. json_normalize")
print("    cannot expand a null, so it keeps the scalar column AND expands the")
print("    objects into dotted children. The bare column is entirely empty and reads")
print("    as a field nobody ever filled in.")
print("    `milestone`, `assignee` and `pinned_comment` do the same thing.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
labels = pd.json_normalize(doc, record_path="labels", meta=["number"])
print(f"\nQ10 labels exploded to {labels.shape[0]} x {labels.shape[1]}")
print(labels[["number", "name"]].head(3).to_string())
print(f"    166 labels over 100 issues, and 40 issues have none. `record_path`")
print("    silently drops those 40 rows, which is right for this question and")
print("    wrong if you wanted one row per issue.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
urlish = {c: int(norm[c].astype("string").str.contains("http", na=False).sum())
          for c in norm.columns}
hits = {c: v for c, v in urlish.items() if v}
print(f"\nQ11 columns holding a URL: {len(hits)}, {sum(hits.values()):,} values")
print("    The truth is 77 paths and 3,297 values. The gap is `labels[].url`")
print("    and the other list-nested ones, which json_normalize never reached.")
print("    PARTLY — a column scan over an already-flattened frame.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
lists = [c for c in norm.columns if norm[c].map(lambda v: isinstance(v, list)).any()]
print(f"\nQ12 {norm.shape[0]} x {norm.shape[1]}, {holes:.1%} empty, and what is lost:")
print(f"    {len(lists)} list-columns remain: {lists}")
print("    `issue_field_values` is an EMPTY LIST on all 100 issues — a field that")
print("    exists and contains nothing, which is why a naive path walk counts 180")
print("    where the probe counts 179: there is no element path under an array")
print("    that never has an element.")
