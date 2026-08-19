"""glom — agent trace, scrubbed, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.jsonl   4.8 MB NDJSON, 1,953 records, 40 top-level keys
  measured      2026-08-10
  run           cd corpus/12-agent-trace/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             -   -                   CANNOT
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 5   YES                 PARTLY
   5 does any field change type                  6   YES                 PARTLY
   6 are any object keys data                    -   -                   CANNOT
   7 how many records                            3   YES                 YES
   8 three named fields to a table               5   YES                 yes
   9 a field missing from some rows              6   YES                 yes
  10 flatten the deepest array                   6   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       6   YES                 PARTLY
  13 needed the shape in advance?                    YES, for everything
  14 survives the next file unchanged?               no — every spec is a path
  15 readable a week later?                          yes, specs read as data
  16 lines, and how much is ceremony?                ~40, almost no ceremony
"""
import json
import sys
from importlib.metadata import version

from glom import Coalesce, Iter, PathAccessError, glom

print(f"python {sys.version.split()[0]}, glom {version('glom')}")
doc = [json.loads(l) for l in open("../source.jsonl") if l.strip()]

# ── 1, 2, 3, 6, 11. what glom does not do ────────────────────────────────────
print("\n1. CANNOT. glom is an EXTRACTOR: every spec names a path the caller")
print("   already knows. On a document with 40 top-level keys of which only ONE")
print("   is universal, that is the worst possible starting position — you")
print("   cannot write a spec for a shape you have not been told about.")
print("\n2, 3, 6, 11. CANNOT, all for the same reason. No describer, no depth")
print("   verb, no row-shape proposal, no recursive search.")

# ── 7. how many records ──────────────────────────────────────────────────────
blocks = glom(doc, ([Coalesce("message.content", default=[])],
                    Iter().filter(lambda c: isinstance(c, list)).flatten().all()))
tu = [b for b in blocks if isinstance(b, dict) and b.get("type") == "tool_use"]
print(f"\n7. {len(doc)} events, {len(blocks)} content blocks, {len(tu)} tool uses.")
print("   `Coalesce(..., default=[])` and an isinstance filter, because")
print("   `message.content` is an ARRAY on 1,363 messages and a STRING on 20.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. PARTLY — glom can TEST a key once you name it, not enumerate:")
for f in ("type", "sessionId", "message", "toolUseResult", "version"):
    have = sum(1 for r in doc if glom(r, Coalesce(f, default=None)) is not None)
    print(f"     {f:18} {have:>5} of {len(doc)}")
print("   The five names came from reading the file. glom found none of them,")
print("   and on this document that is 5 of 40.")

# ── 5. does any field change type ────────────────────────────────────────────
kinds = {}
for r in doc:
    v = glom(r, Coalesce("toolUseResult", default=None))
    if v is not None:
        kinds[type(v).__name__] = kinds.get(type(v).__name__, 0) + 1
print(f"\n5. PARTLY. types at toolUseResult: {kinds}")
print("   452 dicts and 6 strings. glom has no type report — this is a Python")
print("   loop with glom as the accessor — but it does NOT unify, so unlike")
print("   polars the strings are still strings and unlike DuckDB the dicts are")
print("   still dicts. glom's refusal to reshape is what preserves them.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
spec = [{"type": "type",
         "session": Coalesce("sessionId", default=None),
         "version": Coalesce("version", default=None)}]
rows = glom(doc, spec)
print(f"\n8. three fields, one row per event: {len(rows)} rows")
for r in rows[:3]:
    print(f"     {r}")
missing = sum(1 for r in rows if r["version"] is None)
print(f"\n9. version absent on {missing} of {len(rows)} rows, all kept.")
try:
    glom(doc[:5], ["version"])
    print("   expected a PathAccessError and did not get one")
except PathAccessError as e:
    print(f"   WITHOUT Coalesce it RAISES and names the key: "
          f"{str(e).splitlines()[-1][:56]}…")
print("   That is the safety margin: on a document where 39 of 40 keys are")
print("   sometimes, a tool that returns None for a wrong path would let every")
print("   typo through. glom is the only Python tool here that refuses.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
inputs = glom(tu, [{"name": "name", "keys": (Coalesce("input", default={}), list)}])
print(f"\n10. tool inputs flattened: {len(inputs)} rows")
print("   Two Coalesces deep, and `input` itself needs one because a tool_use")
print("   without arguments is legal.")

# ── 12. flattest honest table ────────────────────────────────────────────────
allk = sorted({k for i in inputs for k in i["keys"]})
common = set.intersection(*[set(i["keys"]) for i in inputs]) if inputs else set()
print(f"\n12. {len(inputs)} tool uses, {len(allk)} distinct input fields.")
print(f"   fields present in EVERY input: {common or 'NONE'}")
print("   THE FINDING THIS FILE EXISTS FOR — and glom's version of it is the")
print("   sharpest, because a glom spec is a WRITTEN CLAIM about shape. There")
print("   is no spec you can write for `input` that does not either raise or")
print("   Coalesce away 14 of its 15 fields. The document is telling you, in")
print("   the only language glom speaks, that `input` is not one shape.")
print("   The field that would fix it is `name`, a SIBLING — reachable from the")
print("   enclosing block and not from `input` at all.")
print("   WHAT IS LOST: nothing glom touched. It reshapes nothing, so it")
print("   destroys nothing — and it starts you nowhere.")
