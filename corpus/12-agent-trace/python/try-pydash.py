"""pydash — agent trace, scrubbed, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.jsonl   4.8 MB NDJSON, 1,953 records, 40 top-level keys
  measured      2026-08-10
  run           cd corpus/12-agent-trace/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             6   NO                  WRONG
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 4   YES                 yes
   5 does any field change type                  4   YES                 PARTLY
   6 are any object keys data                    5   YES                 CANNOT
   7 how many records                            3   YES                 YES
   8 three named fields to a table               4   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 PARTLY
  13 needed the shape in advance?                    YES for all but Q1
  14 survives the next file unchanged?               Q1 does; nothing else
  15 readable a week later?                          yes, it is lodash
  16 lines, and how much is ceremony?                ~40, little ceremony

WHAT THIS FILE IS FOR. pydash is the corpus's stand-in for a whole-document walk
in Python — the closest thing to rrapply's melt. The walk is nine lines of plain
recursion because pydash has no recursive descent, and that is the finding.
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = [json.loads(l) for l in open("../source.jsonl") if l.strip()]


# ── 1. what is in here ───────────────────────────────────────────────────────
def leaf_names(node, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            acc.add(k)
            leaf_names(v, acc)
    elif isinstance(node, list):
        for v in node:
            leaf_names(v, acc)
    return acc


names = leaf_names(doc, set())
print(f"\n1. distinct key names anywhere: {len(names)}")
print(f"   {sorted(names)[:14]} …")
print("   WRONG, and this document shows the mechanism plainly. The true answer")
print("   is about 150 structural fields; the count above is inflated by the 50")
print("   FILE PATHS under `snapshot.trackedFileBackups`, which are values")
print("   wearing key names. Same failure as npm's 3,126 version numbers,")
print("   smaller only because there are 50 tracked files and not 288 releases.")
print("   And a name list says nothing about WHERE anything is — which is why")
print("   design/coverage.py refuses to score this shape of answer at all.")

# ── 2, 3, 11. what pydash does not do ────────────────────────────────────────
print("\n2, 3, 11. CANNOT. No depth verb, no row-shape proposal, no search over")
print("   unknown paths. The recursion above is mine; pydash contributed none")
print("   of it, and pydash.get needs a path you already know.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. key PRESENCE across the 1,953 records:")
present = Counter(k for r in doc for k in r)
for k, n in present.most_common(6):
    print(f"     {k:26} {n:>5} of {len(doc)}")
print(f"   {sum(1 for v in present.values() if v == len(doc))} of "
      f"{len(present)} top-level keys are on every record.")
print("   `k in r` is Python. `pydash.get(r, k)` returns None for absent AND")
print("   null alike, so it would have given a different, worse answer.")

# ── 5. does any field change type ────────────────────────────────────────────
kinds = Counter(type(pydash.get(r, "toolUseResult")).__name__
                for r in doc if pydash.get(r, "toolUseResult") is not None)
print(f"\n5. PARTLY. types at toolUseResult: {dict(kinds)}")
print("   452 dicts, 6 strings. No pydash verb reports this; the Counter is")
print("   mine. pydash does not reshape, so nothing is lost — and nothing is")
print("   volunteered either.")

# ── 6. are any object keys data ──────────────────────────────────────────────
tfb = {k for r in doc for k in pydash.get(r, "snapshot.trackedFileBackups", {})}
print(f"\n6. CANNOT. `snapshot.trackedFileBackups` has {len(tfb)} distinct keys,")
print(f"   every one a file path: {sorted(tfb)[0][:52]}…")
print("   They are in the Q1 name list above, sitting between `type` and")
print("   `version` with nothing marking them as values. That is the whole of")
print("   the keys-as-data problem in one printed list.")

# ── 7. how many records ──────────────────────────────────────────────────────
blocks = pydash.flat_map(doc, lambda r: (
    c if isinstance(c := pydash.get(r, "message.content"), list) else []))
tu = pydash.filter_(blocks, lambda b: isinstance(b, dict) and b.get("type") == "tool_use")
print(f"\n7. {len(doc)} events, {len(blocks)} content blocks, {len(tu)} tool uses.")
print("   The walrus and the isinstance guard are both needed: `message.content`")
print("   is a list on 1,363 messages and a STRING on 20, and flat_map over a")
print("   string would have spread it one character per row.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
rows = pydash.map_(doc, lambda r: {
    "type": pydash.get(r, "type"),
    "session": pydash.get(r, "sessionId"),
    "version": pydash.get(r, "version")})
print(f"\n8. three fields, one row per event: {len(rows)} rows")
for r in rows[:3]:
    print(f"     {r}")
print(f"\n9. version is None on {sum(1 for r in rows if r['version'] is None)} of "
      f"{len(rows)} rows, all kept — `pydash.get` defaults rather than raising.")

# ── 10, 12. flatten, and the fifth operation ─────────────────────────────────
inputs = pydash.map_(tu, lambda b: {"name": pydash.get(b, "name"),
                                    "keys": sorted(pydash.get(b, "input", {}))})
allk = sorted({k for i in inputs for k in i["keys"]})
common = set.intersection(*[set(i["keys"]) for i in inputs])
byname = Counter(i["name"] for i in inputs)
print(f"\n10. tool inputs flattened: {len(inputs)} rows")
print(f"\n12. {len(allk)} distinct input fields, present in EVERY input: "
      f"{common or 'NONE'}")
for n, c in byname.most_common(4):
    fields = sorted({k for i in inputs if i["name"] == n for k in i["keys"]})
    print(f"     {n:22} {c:>4} uses, {len(fields)} fields: {fields}")
print("   THE FINDING THIS FILE EXISTS FOR. Folded, 15 columns of mostly holes;")
print("   partitioned on the SIBLING `name`, 2-4 full columns each. pydash has")
print("   `group_by` and would have done it in one call — nothing suggested it.")
print("   WHAT IS LOST: nothing reshaped. pydash is an accessor library and it")
print("   accessed exactly what it was told to.")
