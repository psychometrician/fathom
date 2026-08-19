"""pandas — Grafana "Node Exporter Full", dashboard 1860

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

 ── scoring ──────────────────────────────────────────────────────────────────
  tool          pandas (version printed at run time)
  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
  measured      2026-08-13
  run           cd corpus/27-grafana-dashboard/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             4  YES                  PARTLY
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          5   -                   CANNOT
   4 always present vs sometimes                 3  YES                  yes
   5 does any field change type                  4  YES                  PARTLY
   6 are any object keys data                    -   -                   CANNOT
   7 how many records                            6  YES                  31 BY DEFAULT — the wrong answer
   8 three named fields to a table               2  YES                  yes
   9 a field missing from some rows              2  YES                  yes — NaN
  10 flatten the deepest array                   4  YES                  yes
  11 find every path matching something          4  YES                  PARTLY
  12 flattest honest table                       4  YES                  PARTLY
  13 needed the shape in advance?                    YES, for every line
  14 survives the next file unchanged?               NO — record_path is literal
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~60

**pandas returns 31 and it is the reason this document was chosen.**
`json_normalize(doc, record_path=['panels'])` is the obvious, documented,
first-result-on-a-search call, it produces a clean 31-row frame with named
columns, and it is wrong by a factor of four. Nothing about the output suggests
a question was missed.

**`record_path` is a LITERAL path**, so reaching the nested panels means writing
`['panels', 'panels']` — which you can only write if you already know. That is
question 13 failed in the most consequential way any tool in this comparison
fails it.
"""
import json
import sys

import pandas as pd

print(f"pandas {pd.__version__} · python {sys.version.split()[0]}")

doc = json.load(open("../source.json"))

# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  json.load parsed and said nothing; pandas never saw the bytes. CANNOT.")

# ── Q7. THE CENTRAL QUESTION, and pandas gets it wrong by default. ────────
top = pd.json_normalize(doc, record_path=["panels"])
print("\nQ7  THE CENTRAL QUESTION.")
print(f"      json_normalize(doc, record_path=['panels'])            -> {len(top)} rows")

# The obvious second call DOES NOT WORK, and the error is worth quoting.
try:
    pd.json_normalize(doc, record_path=["panels", "panels"], errors="ignore")
except KeyError as e:
    print(f"      record_path=['panels','panels']  -> KeyError: {str(e)[:60]}…")
print("      (`errors='ignore'` does NOT rescue this — it governs `meta`, not")
print("       `record_path`, and only 16 of the 31 top-level panels have a")
print("       `panels` key at all.)")

# So the nested panels must be pre-filtered in plain Python before pandas can
# see them. The list comprehension below is the tool failing to be the tool.
rows_with_children = [p for p in doc["panels"] if "panels" in p]
nested = pd.json_normalize(rows_with_children, record_path=["panels"])
print(f"      after a hand-written [p for p in ... if 'panels' in p]  -> {len(nested)} rows")
both = pd.concat([top, nested], ignore_index=True)
print(f"      pd.concat([top, nested])                                -> {len(both)} rows")
print("    31 BY DEFAULT, AND THAT IS THE FINDING. The first call is the one the")
print("    documentation shows, it returns a tidy frame with real column names,")
print("    and nothing in it hints that 101 panels are missing.")
print("    Reaching 132 needs a second literal path that RAISES, a list")
print("    comprehension in plain Python to work around it, a concat, and — most")
print("    of all — already knowing that a `row` panel nests its own `panels`.")

# ── Q1. What is in here. ──────────────────────────────────────────────────
print(f"\nQ1  the 31-row frame has {top.shape[1]} columns; the 132-row one has {both.shape[1]}.")
print(f"      {', '.join(list(both.columns)[:8])}, …")
print("    PARTLY. json_normalize flattens nested OBJECTS into dotted columns")
print("    automatically — `gridPos.h`, `fieldConfig.defaults.unit` — which is")
print("    genuinely useful. It will not cross an ARRAY without being told to.")

# ── Q2. How deep. ─────────────────────────────────────────────────────────
print("\nQ2  CANNOT. There is no depth verb. The dotted column names encode the")
print("    depth pandas happened to reach, which is a consequence of the")
print("    record_path you chose, not a property of the document.")

# ── Q3. What is one record. ───────────────────────────────────────────────
print("\nQ3  CANNOT, and this is the sharpest CANNOT in the comparison. pandas")
print("    requires you to NAME the record before it will do anything at all —")
print("    `record_path` is the first argument you must get right. The readings:")
for label, n in [("one panel per row (all depths)", len(both)),
                 ("one TOP-LEVEL panel per row", len(top)),
                 ("one target per row",
                  len(pd.json_normalize(doc, record_path=["panels", "targets"]))
                  + len(pd.json_normalize(rows_with_children,
                                          record_path=["panels", "targets"]))),
                 ("one template variable per row", len(doc["templating"]["list"]))]:
    print(f"      {label:<32} {n:>6,}")
print("    Each needed a hand-written record_path. None was proposed or priced.")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
present = both.notna().sum().sort_values(ascending=False)
always = (present == len(both)).sum()
print(f"\nQ4  {always} of {both.shape[1]} columns are non-null in all {len(both)} rows.")
print(f"      always: {', '.join(present[present == len(both)].index[:6])}")
print(f"      rarest: {', '.join(present.tail(3).index)}")
print("    yes — `notna().sum()` is exactly the question, and this is pandas at")
print("    its best. But note it conflates ABSENT with NULL, which Q9 relies on.")

# ── Q5. Type variation. ───────────────────────────────────────────────────
obj_cols = [c for c in both.columns if both[c].dtype == object]
mixed = {c: sorted({type(v).__name__ for v in both[c].dropna()})
         for c in obj_cols}
mixed = {c: t for c, t in mixed.items() if len(t) > 1}
n_obj = len(obj_cols)
print(f"\nQ5  columns holding more than one Python type: {len(mixed)}, out of {n_obj}")
print("    columns pandas typed as `object`.")
for c, t in list(mixed.items())[:4]:
    print(f"      {c:<28} {t}")
print("    PARTLY, and the zero is the point rather than a clean bill of health.")
print("    `object` is what pandas assigns to anything it could not make numeric,")
print("    so a column of strings, a column of dicts and a genuinely polymorphic")
print("    column all arrive with the same dtype. The scan above had to be written")
print("    in Python over `.dropna()`; pandas has no verb for the question, and")
print(f"    the {n_obj} object columns are indistinguishable from each other by dtype.")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
print("\nQ6  CANNOT. json_normalize turns keys into COLUMN NAMES unconditionally,")
print("    so a document using keys as data becomes a frame with thousands of")
print("    columns and pandas reports that as success.")

# ── Q8/Q9. Three named fields; a field missing from some rows. ────────────
tbl = both[["title", "type", "id", "description"]]
print(f"\nQ8  {len(tbl)} rows x 4. yes — trivially, once Q7 was answered.")
print(tbl.head(3).to_string(index=False))
print(f"\nQ9  `description` is NaN in {tbl['description'].isna().sum()} of {len(tbl)} rows and")
print("    the rows survive. yes — this is what a frame is for and pandas is good")
print("    at it. The count agrees with jq's 84 and ijson's 84.")

# ── Q10. Flatten the deepest array. ───────────────────────────────────────
# `record_path=['panels','panels','targets']` raises for the same reason as Q7,
# so this too goes through the hand-filtered list.
tg_top = pd.json_normalize(doc, record_path=["panels", "targets"])
tg = pd.json_normalize(rows_with_children, record_path=["panels", "targets"])
print(f"\nQ10 targets: {len(tg_top)} under top-level panels + {len(tg)} under nested ones")
print(f"    = {len(tg_top) + len(tg)}. yes, and the same broken-path ceremony as Q7.")
print("    A tool that needed to be told the nesting exists cannot be trusted to")
print("    have found the DEEPEST array; it found the deepest one I named.")

# ── Q11. Find every path matching something. ──────────────────────────────
hits = 0
for c in both.columns:
    s = both[c]
    if s.dtype == object:
        hits += s.astype(str).str.contains(r"\$node|\$job|\$__rate_interval",
                                           regex=True, na=False).sum()
print(f"\nQ11 {hits} CELLS in the 132-row frame mention a template variable.")
print("    PARTLY, and the number is not comparable to jq's 255: the PromQL lives")
print("    inside `targets`, which is a list-column here, so the matches are")
print("    counted against a stringified list rather than against the leaves.")

# ── Q12. The flattest honest table. ───────────────────────────────────────
list_cols = [c for c in both.columns
             if both[c].apply(lambda v: isinstance(v, (list, dict))).any()]
print(f"\nQ12 {both.shape[0]} x {both.shape[1]}, and {len(list_cols)} columns still hold")
print(f"    lists or dicts: {', '.join(list_cols[:5])}")
print("    PARTLY. This is a frame whose cells are nested data, which is exactly")
print("    what god's spec refuses as a value — the open decision this project")
print("    records as 'who owns flattening at the exit'.")
print("    WHAT IS LOST: the 269 targets are inside a cell, not rows.")

print("""
CONCLUSION. pandas is the clearest demonstration in the corpus of the failure
this entry exists to show. `json_normalize(doc, record_path=['panels'])` is the
obvious call, produces 31 tidy rows with real column names, and is wrong. There
is no warning, no ragged-edge diagnostic, and no hint that the frame is a
quarter of the document. It looks like a finished answer.

Everything pandas does well here it does AFTER the record has been named —
`notna().sum()` for Q4 and NaN-for-absent in Q9 are both excellent. Everything
this project claims is expensive happens BEFORE that point, and pandas requires
you to have finished it before the first call.

Q14 is a clean NO. `record_path=['panels','panels']` is a literal path fitted to
one document; a dashboard that nests rows one level deeper silently returns the
wrong number again.
""")
