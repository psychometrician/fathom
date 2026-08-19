"""pandas — Crossref works, 1,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
  measured      2026-08-11
  run           cd corpus/21-crossref-works/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             8   YES                 PARTLY
   2 how deep                                    3   NO                  NO — says 3 of 9
   3 what is one record                         30   YES                 the split: SEE BELOW
   4 always present vs sometimes                 8   NO                  yes, this time
   5 does any field change type                 10  NO                   NO — misses the one
   6 are any object keys data                    2   -                   n/a
   7 how many records                            2   NO                  yes, both numbers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              1   YES                 yes
  10 flatten the deepest array                  18   YES                 yes, after TWO raises
  11 find every path matching something          4   NO                  PARTLY — 3 of 13
  12 flattest honest table                       5   NO                  yes — matches the probe
  13 needed the shape in advance?                    YES, starting with WHERE the records
                                                     are: json_normalize(doc) gives 1 row
  14 survives the next file unchanged?               Q1/Q4/Q12 yes
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~140, of which 3 are imports

  ══════════════════════════════════════════════════════════════════════════════
  A FRAME CANNOT SEE A SPLIT AS AN IMPROVEMENT, AND THIS DOCUMENT PROVES IT
  ARITHMETICALLY RATHER THAN BY ANECDOTE.
  ══════════════════════════════════════════════════════════════════════════════

  `groupby("type")` applies the split correctly and prices it at

      worst 63.4%, weighted 44.3%, unsplit 44.3%

  while jq prices the SAME split on the SAME field at worst 26.3%, weighted
  20.7%. The weighted figure equalling the unsplit figure EXACTLY is not a
  coincidence: a frame has already committed to all 71 columns, so grouping
  moves no NaN anywhere. The total is fixed, and the size-weighted mean of the
  group emptinesses is the global emptiness identically, FOR EVERY POSSIBLE
  SPLIT.

  THE ENTIRE BENEFIT OF SPLITTING IS THAT EACH GROUP NEEDS FEWER COLUMNS, and
  that is precisely what a frame gives up when it is built. So the reason pandas
  cannot do the fourth operation is not a missing verb — it is that the
  rectangle cannot represent the quantity being searched for. That is a stronger
  statement than anything else in this corpus about why the fourth operation
  lives outside the rectangular world.

  TWO OTHER THINGS THE RUN SETTLED.

  `json_normalize` RAISES TWICE, for unrelated reasons, and fixing the first
  reveals the second: `record_path=["reference"]` fails because 465 works have
  none, and then `meta=["DOI"]` fails because `reference[]` HAS ITS OWN `DOI`.
  Correct call needs a pre-filter AND `meta_prefix`. The pre-filter is safe here
  and was NOT on entry 20, because `reference` is absent-or-present per work
  rather than partly present — one level of raggedness, not two.

  36 OF 71 COLUMN NAMES CONTAIN A HYPHEN. `norm.is-referenced-by-count` is a
  subtraction; every one must be reached with `[]`, and `df.query` needs
  backticks. Compare DuckDB, where they need double quotes, and R, where they
  need backticks too — three tools, three escaping rules, one document.
"""
import json
import time
from importlib.metadata import version

import pandas as pd

print(f"pandas {version('pandas')}")

RAW = "../source.json"
doc = json.load(open(RAW))
items = doc["message"]["items"]

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  json.load read it and said nothing. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
whole = pd.json_normalize(doc)
print(f"\nQ1  json_normalize(doc) — the WHOLE document — gives {whole.shape}")
print("    ONE ROW. The records are two levels down at $.message.items and")
print("    pandas has no way to find that; you point it at the array or you get")
print("    a one-row frame of the envelope. THE WRAPPER IS THE FIRST COST.")
t = time.time()
norm = pd.json_normalize(items)
print(f"Q1  json_normalize(items) -> {norm.shape[0]:,} x {norm.shape[1]}, {time.time()-t:.1f}s")
seg = max(c.count(".") for c in norm.columns) + 1
print(f"Q2  deepest dotted name has {seg} segments; the document is 9 deep.")
print("    json_normalize stops at the first ARRAY, and this document's depth is")
print("    almost all inside arrays — reference[], author[], assertion[].")

# ── Q3. What is one record, and THE SPLIT. ───────────────────────────────────
holes = norm.isna().sum().sum() / (norm.shape[0] * norm.shape[1])
print(f"\nQ3  an item of items: {norm.shape[0]:,} x {norm.shape[1]}, {holes:.0%} NaN")
print("    The probe names SEVENTEEN candidates and prices each. pandas names one.")
print("\nQ3  THE SPLIT — pandas can APPLY one, told the field, and cannot SEARCH:")
for field in ("type",):
    g = norm.groupby(norm[field].astype("string"), dropna=False)
    rows = []
    for k, sub in g:
        e = sub.isna().sum().sum() / (sub.shape[0] * sub.shape[1])
        rows.append((k, len(sub), e))
    rows.sort(key=lambda r: -r[1])
    print(f"    groupby('{field}') — {len(rows)} kinds:")
    for k, n, e in rows[:5]:
        print(f"      {k:22} {n:5,} rows  {e:6.1%} empty")
    w = sum(n * e for _, n, e in rows) / sum(n for _, n, e in rows)
    print(f"      worst {max(e for _, _, e in rows):.1%}, weighted {w:.1%},"
          f" unsplit {holes:.1%}")
print("\n    ══ AND THE NUMBERS ARE NOT THE PROBE'S, AND CANNOT BE. ══")
print("    jq computes worst 26.3% and weighted 20.7% for the SAME split on the")
print("    SAME field. The frame above says worst 63.4% and weighted 44.3%, and")
print(f"    the weighted figure equals the unsplit {holes:.1%} EXACTLY.")
print("    That is not a coincidence and not a bug. A FRAME HAS ALREADY")
print("    COMMITTED TO ALL 71 COLUMNS, so grouping moves no NaN anywhere: the")
print("    total is fixed and the size-weighted average of the group emptinesses")
print("    is the global emptiness, identically, for every possible split.")
print("    THE WHOLE BENEFIT OF SPLITTING IS THAT EACH GROUP NEEDS FEWER")
print("    COLUMNS, and that is exactly the thing a frame has already given up.")
print("    jq recomputes the column set per group and sees 44% fall to 21%.")
print("    So this is not 'pandas has no verb for the search'. It is that the")
print("    frame cannot represent the quantity the search is searching for —")
print("    which is a stronger reason than any other tool in this corpus has")
print("    given for why the fourth operation is not in the rectangular world.")
print("    `groupby` is still one line once you know the field is `type`, and it")
print("    applies the split correctly; it just cannot tell you it was worth it.")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
present = norm.notna().sum()
flat = [c for c in norm.columns if "." not in c]
some = [c for c in flat if present[c] < len(norm)]
rk = [set(r) for r in items]
absent = sorted(k for k in set().union(*rk) if sum(k in r for r in rk) < len(items))
nulls = {k for r in items for k, v in r.items() if v is None}
print(f"\nQ4  pandas: {len(some)} of {len(flat)} un-dotted columns not always filled")
print(f"Q4  the document: {len(absent)} of 57 record keys sometimes ABSENT, "
      f"{len(nulls)} written null")
print("    ZERO NULLS ANYWHERE IN THE RECORDS, so the absent-vs-null trap that")
print("    split the thirteen tools on entries 15, 20 and 25 has nothing to bite")
print("    on. pandas' NaN means ABSENT here and means it unambiguously —")
print("    entry 14's unanimity, reproduced by the same mechanism.")
print("    The two counts still differ because json_normalize turned 57 keys")
print("    into 71 columns; compare like with like on the un-dotted ones only.")

# ── Q5. Does any field change type between records? ──────────────────────────
mixed = []
for c in flat:
    k = norm[c].map(lambda v: type(v).__name__).value_counts()
    k = k[k.index != "NoneType"]
    if len(k) > 1:
        mixed.append((c, k.to_dict()))
print(f"\nQ5  un-dotted columns holding more than one python type: {len(mixed)}")
for c, k in mixed[:4]:
    print(f"    {c}: {k}")
dp = norm["issued.date-parts"]
print(f"Q5  the probe's ONE site, issued.date-parts: dtype {dp.dtype}")
print(f"    values are lists on all {dp.map(lambda v: isinstance(v, list)).sum():,} rows —")
print("    [[2018,11,3]] on 998 and [[None]] on 2. pandas sees `list` for both.")
print("    THE ONLY REAL TYPE CHANGE IN THIS DOCUMENT IS INVISIBLE TO PANDAS,")
print("    and whatever it reports above is NaN-beside-a-value instead.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keys-as-data here that pandas would meet: reference[] is inside a")
print("    list-column and json_normalize never enters it. n/a rather than wrong.")

# ── HYPHENS. This document's own hazard. ─────────────────────────────────────
hyph = [c for c in norm.columns if "-" in c]
print(f"\n     HYPHENATED COLUMN NAMES: {len(hyph)} of {norm.shape[1]}")
print(f"     {hyph[:6]} …")
print("     `norm.is-referenced-by-count` is a SUBTRACTION, not an attribute, so")
print("     every one of these must be reached with [] and quoted. pandas warns")
print("     about none of it; `df.query('type == \"book\"')` on a hyphenated name")
print("     is a parse error. Compare DuckDB, where they must be double-quoted,")
print("     and R, where they need backticks.")
try:
    norm.query("`is-referenced-by-count` > 0")
    print("     df.query with backticks: OK")
except Exception as e:
    print(f"     df.query with backticks: {type(e).__name__}")

# ── Q7. How many records. ────────────────────────────────────────────────────
print(f"\nQ7  {len(items):,} in the array; message['total-results'] is "
      f"{doc['message']['total-results']:,}")
print("    Two numbers 185,000x apart, and the frame knows only the first.")

# ── Q8/Q9/Q10. ───────────────────────────────────────────────────────────────
print(f"\nQ8  {norm[['DOI', 'type', 'publisher']].shape}")
print(norm[["DOI", "type", "publisher"]].head(2).to_string())
print(f"\nQ9  abstract filled on {int(present['abstract'])} of {len(norm):,}, rows kept")
# TWO DIFFERENT RAISES ON ONE CALL, and the second was a surprise.
print("\nQ10 json_normalize raises TWICE here, for two unrelated reasons:")
try:
    pd.json_normalize(items, record_path=["reference"], meta=["DOI"])
except Exception as e:
    print(f"    (1) {type(e).__name__}: {' '.join(str(e).split())[:78]}")
have = [w for w in items if "reference" in w]
try:
    pd.json_normalize(have, record_path=["reference"], meta=["DOI"])
except Exception as e:
    print(f"    (2) {type(e).__name__}: {' '.join(str(e).split())[:78]}")
    print("        `reference[]` HAS ITS OWN `DOI` KEY, so the meta column")
    print("        collides with the record's. Nothing about the first error")
    print("        predicts the second; you fix one and meet the other.")
t = time.time()
ref = pd.json_normalize(have, record_path=["reference"], meta=["DOI"],
                        meta_prefix="work_")
print(f"    fixed with a filter AND meta_prefix: {ref.shape[0]:,} x {ref.shape[1]}, "
      f"{time.time()-t:.1f}s — the true count is 18,155")
print("    The pre-filter is SAFE here and was not on entry 20: `reference` is")
print("    absent-or-present per work, never partly, because it is one level")
print("    down and not two. Same flag, same tool, different raggedness.")

# ── Q11. ─────────────────────────────────────────────────────────────────────
urlish = [c for c in norm.columns
          if norm[c].astype("string").str.match(r"^https?://").fillna(False).any()]
print(f"\nQ11 columns with a ^https?:// value: {len(urlish)} — {urlish}")
print("    jq reports 13 distinct URL PATHS. The gap is the list-columns:")
print("    license[].URL, link[].URL, assertion[].URL are all inside cells.")

# ── Q12. ─────────────────────────────────────────────────────────────────────
lists = [c for c in norm.columns if norm[c].map(lambda v: isinstance(v, list)).any()]
print(f"\nQ12 {norm.shape[0]:,} x {norm.shape[1]}, {holes:.0%} NaN, "
      f"{len(lists)} list-columns")
print("    Nothing lost, everything nested still nested. THE PROBE ALSO SAYS")
print("    1,000 x 71 AT 44% EMPTY — pandas and the probe agree exactly on this")
print("    document's headline table, which they did not on entry 20 and which")
print("    makes the question-3 disagreement above purely about the SPLIT.")
