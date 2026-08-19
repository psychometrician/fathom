"""jmespath — agent trace, scrubbed, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.jsonl   4.8 MB NDJSON, 1,953 records, 40 top-level keys
  measured      2026-08-10
  run           cd corpus/12-agent-trace/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   PARTLY              PARTLY
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   YES                 PARTLY
   5 does any field change type                  5   YES                 DANGEROUS
   6 are any object keys data                    4   YES                 CANNOT
   7 how many records                            4   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              6   YES                 DANGEROUS
  10 flatten the deepest array                   5   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 PARTLY
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no, and it will not say so
  15 readable a week later?                          yes, the syntax is compact
  16 lines, and how much is ceremony?                ~35, no ceremony at all
"""
import json
import sys
from importlib.metadata import version

import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")
doc = [json.loads(l) for l in open("../source.jsonl") if l.strip()]

# ── 1. what is in here ───────────────────────────────────────────────────────
print(f"\n1. keys([0]): {jmespath.search('[0]|keys(@)', doc)}")
print(f"   keys([2]): {jmespath.search('[2]|keys(@)', doc)}")
print("   PARTLY, and worse here than anywhere. `keys()` works one object at a")
print("   time and this document has 40 top-level keys of which only `type` is")
print("   universal — so the union across 1,953 records must be assembled by")
print("   the caller, one `keys()` call at a time. Record 0 and record 2 share")
print("   almost nothing.")

# ── 2, 3, 6, 11. what jmespath does not do ───────────────────────────────────
print("\n2, 3, 11. CANNOT. No depth verb, no row-shape proposal, and NO")
print("   RECURSIVE DESCENT AT ALL — there is no `..` in jmespath, so a search")
print("   over unknown paths cannot be written.")
print("\n6. CANNOT. `snapshot.trackedFileBackups` is keyed by file path; keys()")
print("   lists them and presents them exactly as `type` is presented.")

# ── 7. how many records ──────────────────────────────────────────────────────
ev = len(doc)
ms = len(jmespath.search("[?message] | @", doc) or [])
blocks = [b for r in doc if isinstance(r.get("message"), dict)
          and isinstance(r["message"].get("content"), list)
          for b in r["message"]["content"]]
tu = jmespath.search("[].message.content[?type=='tool_use'][]", doc) or []
print(f"\n7. {ev} events, {ms} messages, {len(blocks)} content blocks, "
      f"{len(tu)} tool uses.")
print("   `[].message.content[?...]` flattens and skips silently — which is")
print("   right here and is the same silence as Q9.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. PARTLY — a projection counts what is there, once you name it:")
for f in ("type", "sessionId", "message", "toolUseResult", "version"):
    print(f"     {f:18} {len(jmespath.search(f'[].{f}', doc) or []):>5} of {ev}")
print("   A projection drops both absence and null, so the two collapse — and")
print("   unlike pandas there is not even a NaN left to notice.")

# ── 5, 9. the silent failure, twice ──────────────────────────────────────────
print("\n5. DANGEROUS. `toolUseResult` is an object on 452 records and a STRING")
print("   on 6. jmespath has no type verb, so:")
print(f"     [0].toolUseResult.type       -> "
      f"{jmespath.search('[0].toolUseResult.type', doc)!r}")
print(f"     [0].nosuchfield.anything     -> "
      f"{jmespath.search('[0].nosuchfield.anything', doc)!r}")
print("   A field that is absent, a field that holds a string instead of an")
print("   object, and a field that never existed are ALL None. On a document")
print("   where 39 of 40 top-level keys are optional, every path is a guess and")
print("   jmespath never says which guesses were wrong.")

rows = jmespath.search("[].{type: type, session: sessionId, version: version}", doc)
print(f"\n8. three fields, one row per event: {len(rows)} rows")
for r in rows[:3]:
    print(f"     {r}")
print(f"\n9. version is None on {sum(1 for r in rows if r['version'] is None)} of "
      f"{len(rows)} rows, all kept.")
print("   Correct — the multiselect-hash keeps the row — and indistinguishable")
print("   from a typo in the field name, which would also be None on all 1,953.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
inputs = jmespath.search(
    "[].message.content[?type=='tool_use'][].{name: name, input: input}", doc) or []
print(f"\n10. tool uses flattened: {len(inputs)} rows, one expression.")
print("   The `[]` after the filter is the flatten operator and is easy to")
print("   forget; without it the result is a list of lists and jmespath says")
print("   nothing about the difference.")

# ── 12. flattest honest table ────────────────────────────────────────────────
allk = sorted({k for i in inputs for k in (i["input"] or {})})
common = set.intersection(*[set(i["input"] or {}) for i in inputs])
print(f"\n12. {len(inputs)} tool uses, {len(allk)} distinct input fields.")
print(f"   fields present in EVERY input: {common or 'NONE'}")
print("   THE FINDING THIS FILE EXISTS FOR. jmespath CAN reach it — `name` and")
print("   `input` are siblings and one multiselect takes both — but it has no")
print("   group_by, so partitioning on `name` is Python. And nothing about the")
print("   16-column, mostly-empty result would have told you to.")
print("   WHAT IS LOST: nothing reshaped; jmespath only selects. What is")
print("   missing is any signal that the selection was the wrong shape.")
