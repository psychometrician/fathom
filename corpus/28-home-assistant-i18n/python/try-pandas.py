"""pandas — Home Assistant frontend, the English translation catalogue

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

── scoring ──────────────────────────────────────────────────────────────────
 tool          pandas (version printed at run time)
 file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
 measured      2026-08-12
 run           cd corpus/28-home-assistant-i18n/python && uv run try-pandas.py

 question                                    lines  shape known first?  worked
  0 is this sound                               1   -                   CANNOT
  1 what is in here                             4   NO                  ONE LEVEL — 7
  2 how deep                                    -   -                   CANNOT
  3 what is one record                          6   NO                  CANNOT — see below
  4 always present vs sometimes                 -   -                   CANNOT, no records
  5 does any field change type                  6   NO                  by accident, per column
  6 are any object keys data                    -   -                   CANNOT
  7 how many records                            4   NO                  1, and that is the answer
  8 three named fields to a table               4  YES                  yes
  9 a field missing from some rows              4  YES                  yes, trivially
 10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
 11 find every path matching something          5   -                   yes, by iterating columns
 12 flattest honest table                       5  YES                  1 x 8,518
 13 needed the shape in advance?                    NO for 1, 7, 12
 14 survives the next file unchanged?               yes for 12; nothing else is general
 15 readable a week later?                          yes
 16 lines, and how much is ceremony?                ~90

THIS DOCUMENT HAS NO ARRAYS. 1,619 objects, 8,518 leaves, and not one array
anywhere. `json_normalize` is built to explode arrays into rows and there is
nothing to explode, so the flattest honest table is ONE ROW with 8,518 columns.
That is not a failure of pandas; it is the correct answer, and it is useless.
"""
import json
import sys
import time

import pandas as pd

print(f"pandas {pd.__version__} · python {sys.version.split()[0]}")

doc = json.load(open("../source.json"))

# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  json.load succeeded and said nothing. It cannot report duplicate")
print("    keys, NaN, or integers past 2^53 — the last key silently wins.")
print("    CANNOT.")

# ── Q1/Q2. What is in here, how deep. ─────────────────────────────────────
t = time.time()
print(f"\nQ1  top level, {len(doc)} keys: {', '.join(doc)}")
print("    pandas has no verb for 'the fields at every level'. To go deeper you")
print("    normalize, and then the levels are gone — they become dotted names.")
print("\nQ2  CANNOT. No depth verb.")

# ── Q3/Q7. What is one record, and how many. ──────────────────────────────
flat = pd.json_normalize(doc)
print(f"\nQ3  json_normalize(doc) -> {flat.shape[0]} row x {flat.shape[1]:,} cols")
print("    ONE ROW. pandas' answer to 'what is one record' is 'the document',")
print("    and it is not wrong — there is no array here to make rows from.")
print("    It names no alternative and prices nothing. CANNOT for Q3.")
print(f"\nQ7  {flat.shape[0]} record. Correct, and useless.")

# ── Q5. Type variation, per column. ───────────────────────────────────────
kinds = flat.iloc[0].map(lambda v: type(v).__name__).value_counts()
print(f"\nQ5  the one row's values by python type: {dict(kinds)}")
print("    Every leaf is a string. The type variation the probe reports is")
print("    BETWEEN SIBLINGS at a path — string here, object there — and a")
print("    one-row frame has no siblings to compare. by accident, not by verb.")

# ── Q8/Q9. Named fields, and a missing one. ───────────────────────────────
cols = ["ui.common.and", "ui.common.loading", "ui.panel.profile.logout"]
print(f"\nQ8  three named columns: {flat[cols].iloc[0].tolist()}")
missing = "ui.panel.profile.not_a_real_key"
print(f"\nQ9  a key that is not there: {missing in flat.columns} — pandas gives")
print("    KeyError rather than NA, so the caller must ask first. Trivial here")
print("    because there is exactly one row to keep.")

# ── Q10. The deepest array. ───────────────────────────────────────────────
print("\nQ10 NOTHING TO FLATTEN. Zero arrays in 604 KB.")

# ── Q11. Paths matching something. ────────────────────────────────────────
braces = [c for c in flat.columns if "{" in str(flat.iloc[0][c])]
print(f"\nQ11 columns whose message carries an ICU placeholder: {len(braces):,}")
print(f"    e.g. {braces[0]} = {flat.iloc[0][braces[0]][:52]}")
print("    Done by iterating 8,518 columns in python, not by a pandas verb.")

# ── Q12. The flattest honest table. ───────────────────────────────────────
print(f"\nQ12 {flat.shape[0]} x {flat.shape[1]:,}. Nothing is LOST — every leaf is a")
print("    column and every name is its full dotted path. What is lost is the")
print("    POINT: a 1 x 8,518 frame is the document retyped, not a table.")
print(f"    ({time.time() - t:.1f}s)")

print("""
CONCLUSION. pandas answers Q7 correctly and by accident: there is one record
because there is no array, and json_normalize's whole design is arrays-to-rows.

The honest shape for this document is one row per MESSAGE — 8,518 of them, keyed
by path — and json_normalize produces its exact transpose. pandas has `.T`, and
`flat.T` does give 8,518 rows x 1 column with the paths as the index. That is the
right answer and it arrives by transposing a mistake rather than by asking for it.

And it is worth saying that fathom does badly here too: the probe describes this
file at 5.69% of its input with 39.3% of fields unnamed, its worst in the corpus.
Neither tool is beaten by the other. The document beats both.
""")
