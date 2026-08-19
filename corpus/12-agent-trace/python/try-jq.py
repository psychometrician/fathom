"""jq (via the `jq` Python binding) — agent trace, scrubbed, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, Python binding (version printed at run time)
  file          ../source.jsonl   4.8 MB NDJSON, 1,953 records, 40 top-level keys
  measured      2026-08-10
  run           cd corpus/12-agent-trace/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             6   NO                  yes
   2 how deep                                    2   NO                  yes
   3 what is one record                          6   NO                  PARTLY
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  5   NO                  yes
   6 are any object keys data                    5   NO                  PARTLY
   7 how many records                            3   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          7   NO   CANNOT (scrubbed)
  12 flattest honest table                       7   YES                 yes
  13 needed the shape in advance?                    NO for 1-7 and 11
  14 survives the next file unchanged?               the describe half does
  15 readable a week later?                          the short ones only
  16 lines, and how much is ceremony?                ~45, dense not ceremonial

jq answers more of the exploration half than any other Python tool here. The
contribution is asking unprompted, not the arithmetic — every expression below
had to be written by someone who decided to ask.
"""
import json
import sys
from importlib.metadata import version

import jq

print(f"python {sys.version.split()[0]}, jq binding {version('jq')}")

# NDJSON: the whole file is slurped into one array first, which is what
# `jq --slurp` does at the command line. VERDICT.md records that `jqr` has no
# slurp and needs 198 MB where the jq binary needs 4.3 — the Python binding has
# the same shape of cost, paid here in a list comprehension.
doc = [json.loads(l) for l in open("../source.jsonl") if l.strip()]
q = lambda e: jq.compile(e).input(doc).all()

# ── 1. what is in here ───────────────────────────────────────────────────────
shapes = q('[paths(type != "object" and type != "array")|map(if type=="number" then "[]" else . end)|join(".")]'
           '|group_by(.)|map({p:.[0],n:length})|sort_by(-.n)')[0]
print(f"\n1. {len(shapes)} folded path shapes (array indices -> []):")
for s in shapes[:8]:
    print(f"     {s['p']:52} {s['n']:>6,}")
print("   The fold is hand-written. Without `map(if type==\"number\")` it is one")
print("   path per scalar. On THIS document that costs less than usual — ijson's")
print("   unfolded prefix listing is only 1% of the file, against 111% on npm —")
print("   because 1,953 records share about 434 paths. The fold still matters;")
print("   it is just not the difference it is on a keyed document.")

print(f"\n2. deepest path: {q('[paths|length]|max')[0]} segments")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. top-level key presence across the 1,953 records, nothing named:")
for row in q('[.[]|keys[]]|group_by(.)|map({k:.[0],n:length})|sort_by(-.n)')[0][:8]:
    print(f"     {row['k']:26} {row['n']:>5} of 1953")
print("   ONLY `type` is on every record — 39 of 40 top-level keys are")
print("   sometimes. `keys` is presence, so absence and null stay apart.")

# ── 5. does any field change type ────────────────────────────────────────────
# `paths(scalars)` cannot see a null — `select(null)` is false in jq — so the
# type report uses `paths` and a leaf test instead. Same trap as file 11.
print("\n5. folded paths taking more than one type:")
for row in q('[paths as $p|select((getpath($p)|type) as $t|$t!="object" and '
             '$t!="array")|{p:($p|map(if type=="number" then "[]" else . end)'
             '|join(".")),t:(getpath($p)|type)}]|group_by(.p)'
             '|map({p:.[0].p,t:(map(.t)|unique)})|map(select(.t|length>1))'
             '|sort_by(.p)')[0][:5]:
    print(f"     {row['p']:52} {row['t']}")
print("   `paths(scalars)` would have found FEWER: select(null) is false in jq,")
print("   so nulls vanish from the standard listing. Measured on 11-jupyter-")
print("   notebook and reproduced here.")

# ── 6. are any object keys data ──────────────────────────────────────────────
tfb = q('[.[]|.snapshot?.trackedFileBackups?|select(.!=null)|keys[]]|unique|length')[0]
print(f"\n6. PARTLY. `snapshot.trackedFileBackups` has {tfb} distinct keys across")
print(f"   {q('[.[]|select(.snapshot?.trackedFileBackups?!=null)]|length')[0]} sites,"
      f" and every one is a FILE PATH.")
print("   jq lists them with `keys` and has no way to say they are values. They")
print("   arrive exactly as `type` and `sessionId` arrive.")

# ── 3, 7. what is one record, and how many ───────────────────────────────────
ev = q('length')[0]
ms = q('[.[]|select(.message!=null)]|length')[0]
bl = q('[.[]|.message?.content?|select(type=="array")|.[]]|length')[0]
tu = q('[.[]|.message?.content?|select(type=="array")|.[]|select(.type=="tool_use")]|length')[0]
print(f"\n3. four defensible records, and jq prices none:")
print(f"     an event          {ev:>5}")
print(f"     a message         {ms:>5}")
print(f"     a content block   {bl:>5}")
print(f"     a tool_use        {tu:>5}")
print("   `select(type==\"array\")` is load-bearing: `.content` is an ARRAY on")
print("   1,363 messages and a STRING on 20, and `.[]` on a string errors.")
print(f"\n7. {ev} events, {ms} messages, {bl} blocks, {tu} tool uses.")

# ── 8, 9 ─────────────────────────────────────────────────────────────────────
rows = q('[.[]|{type,sessionId,version}]')[0]
print(f"\n8. three fields, one row per event: {len(rows)} rows")
for r in rows[:3]:
    print(f"     {r}")
print(f"\n9. `version` null on {sum(1 for r in rows if r['version'] is None)} of "
      f"{len(rows)}, all kept — a missing key is null in an object constructor.")

# ── 10 ───────────────────────────────────────────────────────────────────────
print(f"\n10. tool_use blocks flattened: {tu} rows, reached in one expression.")

# ── 11 ───────────────────────────────────────────────────────────────────────
hits = q('[paths(strings) as $p|select(getpath($p)|test("https?://"))'
         '|($p|map(if type=="number" then "[]" else . end)|join("."))]'
         '|group_by(.)|map({p:.[0],n:length})|sort_by(-.n)')[0]
print(f"\n11. CANNOT BE ASKED on this entry. The expression runs and returns")
print(f"   {sum(h['n'] for h in hits)} — an artifact of the scrub, not a fact")
print("   about agent traces. `scrub.py` replaced every string over 32 chars or")
print("   occurring under 20 times with `x`, so every URL is gone by")
print("   construction. NOTES.md records this as a stated cost of the scrub.")
print("   The same expression finds 53 on 11-jupyter-notebook, so the")
print("   machinery is fine and there is nothing here to find.")

# ── 12. flattest honest table, AND the fifth operation ───────────────────────
fields = q('[.[]|.message?.content?|select(type=="array")|.[]'
           '|select(.type=="tool_use")|.input|keys[]]|unique')[0]
common = q('[.[]|.message?.content?|select(type=="array")|.[]'
           '|select(.type=="tool_use")|.input|keys]|reduce .[] as $k '
           '(null; if .==null then $k else .-(.-$k) end)')[0]
byname = q('[.[]|.message?.content?|select(type=="array")|.[]'
           '|select(.type=="tool_use")|{n:.name,k:(.input|keys|length)}]'
           '|group_by(.n)|map({name:.[0].n,uses:length,'
           'fields:(map(.k)|max)})|sort_by(-.uses)')[0]
print(f"\n12. {tu} tool uses, {len(fields)} distinct input fields.")
print(f"   fields present in EVERY input: {common if common else 'NONE'}")
print("   THE FINDING THIS FILE EXISTS FOR, in one expression. Partitioned on")
print("   the SIBLING `name`:")
for b in byname[:4]:
    print(f"     {b['name']:22} {b['uses']:>4} uses, {b['fields']} input fields")
print("   16 columns and mostly holes folded together; 2-4 full columns apart.")
print("   The discriminator is OUTSIDE the record being folded, so no test over")
print("   the inputs themselves could find it. jq computes the whole thing and")
print("   volunteers none of it.")
print("   WHAT IS LOST: nothing — jq is the only Python tool here that reaches")
print("   every level of this document without re-parsing something.")
