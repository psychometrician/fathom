"""pandas — agent trace, scrubbed, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pandas (version printed at run time)
  file          ../source.jsonl   4.8 MB NDJSON, 1,953 records, 40 top-level keys
  measured      2026-08-10
  run           cd corpus/12-agent-trace/python && uv run try-pandas.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  PARTLY
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          7   YES                 PARTLY
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  5   YES                 PARTLY
   6 are any object keys data                    4   YES                 CANNOT
   7 how many records                            3   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              4   YES                 yes
  10 flatten the deepest array                   5   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 PARTLY
  13 needed the shape in advance?                    NO for 1, 4, 7
  14 survives the next file unchanged?               1 and 4 do
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~45, little ceremony
"""
import json
import sys
from importlib.metadata import version

import pandas as pd

print(f"python {sys.version.split()[0]}, pandas {version('pandas')}")

# NDJSON is a first-class input here — `lines=True` and nothing else. That is
# more than 04-gharchive needed and it is worth noting which tools have it.
df = pd.read_json("../source.jsonl", lines=True)
print(f"\n1. read_json(lines=True): {df.shape[0]} rows x {df.shape[1]} cols")
print(f"   {len(str(list(df.columns))):,} chars of column list, "
      f"{100 * len(str(list(df.columns))) / 4813294:.2f}% of the file")
print(f"   {list(df.columns)[:12]} …")
print("   PARTLY: 40 top-level columns is a real answer to Q1, and everything")
print("   below the top level is an opaque object in a cell.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. fraction of the 1,953 records where each column is not null:")
pres = (df.notna().sum() / len(df)).sort_values(ascending=False)
for k, v in list(pres.items())[:8]:
    print(f"     {k:26} {v:.0%}")
print(f"     … and {len(pres) - 8} more, lowest {pres.iloc[-1]:.1%}")
print(f"   ONLY `type` is on every record ({pres.iloc[0]:.0%}). 39 of 40 columns")
print("   are sometimes — this is the corpus's raggedest top level, and pandas")
print("   reports it correctly because NDJSON gave it one row per record.")

# ── 2. how deep ──────────────────────────────────────────────────────────────
print("\n2. CANNOT. Every nested value is one `object` cell; pandas descended")
print("   nothing. The true depth is 10.")

# ── 5. does any field change type ────────────────────────────────────────────
tur = df["toolUseResult"].dropna()
kinds = tur.map(lambda v: type(v).__name__).value_counts().to_dict()
print(f"\n5. PARTLY, and there IS a real one here: toolUseResult holds {kinds}")
print("   452 dicts and 6 strings in one column — genuine polymorphism, not")
print("   raggedness. pandas stores both as `object` dtype and says nothing;")
print("   the count above is a hand-written `map(type)`, not a pandas verb.")
print(f"   dtypes overall: {df.dtypes.value_counts().to_dict()}")

# ── 6. are any object keys data ──────────────────────────────────────────────
print("\n6. CANNOT. `snapshot.trackedFileBackups` is keyed by FILE PATH — 50")
print("   distinct keys across 19 sites. json_normalize would turn each path")
print("   into a column name; here it never gets that far, because `snapshot`")
print("   is one opaque cell. Either way nothing marks a key as a value.")

# ── 3, 7. what is one record, and how many ───────────────────────────────────
msgs = df["message"].dropna()
blocks = [b for m in msgs if isinstance(m, dict) and isinstance(m.get("content"), list)
          for b in m["content"]]
tu = [b for b in blocks if isinstance(b, dict) and b.get("type") == "tool_use"]
print("\n3. four defensible records, and NDJSON only proposes the first:")
print(f"     an event          {len(df):>5} rows x {df.shape[1]} cols   "
      f"{100 * df.isna().mean().mean():.0f}% empty")
print(f"     a message         {len(msgs):>5} rows")
print(f"     a content block   {len(blocks):>5} rows")
print(f"     a tool_use        {len(tu):>5} rows")
print("   69% empty on the event row, from 40 columns of which only `type` is")
print("   universal. VERDICT.md item 15 quotes 93% for the same document — that")
print("   is `rows()`'s 319-column FLATTENED table, a different table, and the")
print("   two are not the same number. pandas prints its own and cannot suggest")
print("   the split that would fix it.")
print(f"\n7. {len(df)} events, {len(msgs)} messages, {len(blocks)} blocks, "
      f"{len(tu)} tool uses.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
t = df[["type", "sessionId", "version"]].copy()
print(f"\n8. three fields, one row per event:\n{t.head(3).to_string(index=False)}")
print(f"\n9. `version` is absent on {int(t['version'].isna().sum())} of {len(t)} "
      f"records and all rows are kept.")
print("   Free, because NDJSON made every record a row before any field was")
print("   named. This is the one question that is easier here than on a")
print("   single-document file.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
flat = pd.json_normalize(
    [{"type": r.get("type"), **b} for r in df.to_dict("records")
     if isinstance(r.get("message"), dict)
     and isinstance(r["message"].get("content"), list)
     for b in r["message"]["content"] if isinstance(b, dict)])
print(f"\n10. content blocks flattened: {flat.shape[0]} x {flat.shape[1]}, "
      f"{100 * flat.isna().mean().mean():.0f}% empty")
print("   The comprehension is mine — `record_path=['message','content']` would")
print("   raise on the 570 records with no message, exactly as it did on")
print("   11-jupyter-notebook's markdown cells.")

# ── 11. every path whose value matches ───────────────────────────────────────
print("\n11. CANNOT. No whole-document path search. Everything below the top")
print("   level is an opaque cell, so even `.str.contains` has nothing to see.")

# ── 12. flattest honest table ────────────────────────────────────────────────
inputs = pd.json_normalize([{"name": b.get("name"), **(b.get("input") or {})}
                            for b in tu])
print(f"\n12. flattest for the tool uses: {inputs.shape[0]} x {inputs.shape[1]}, "
      f"{100 * inputs.isna().mean().mean():.0f}% empty")
print("   THE FINDING THIS FILE EXISTS FOR, and pandas shows it by accident:")
print("   16 columns and 76% empty, because NO FIELD IS PRESENT IN EVERY TOOL")
print("   INPUT. Grouping by `name` — a SIBLING of `input`, not a field of it —")
print("   gives Bash 3 columns, Edit 4, Write 2, all full. pandas can do the")
print("   groupby and will never suggest it.")
print("   WHAT IS LOST: everything below `input`, and the 570 non-message")
print("   records, which have no content block to be a row of.")
