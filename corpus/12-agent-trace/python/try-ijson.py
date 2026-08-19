"""ijson — agent trace, scrubbed, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.jsonl   4.8 MB NDJSON, 1,953 records, 40 top-level keys
  measured      2026-08-10
  run           cd corpus/12-agent-trace/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             6   NO                  yes
   2 how deep                                    3   NO                  yes
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  5   NO                  yes
   6 are any object keys data                    5   NO                  PARTLY
   7 how many records                            3   NO                  yes
   8 three named fields to a table               -   -                   CANNOT
   9 a field missing from some rows              -   -                   CANNOT
  10 flatten the deepest array                   3   YES                 PARTLY
  11 find every path matching something          8   NO   CANNOT (scrubbed)
  12 flattest honest table                       -   -                   CANNOT
  13 needed the shape in advance?                    NO for 1-7 and 11
  14 survives the next file unchanged?               YES — nothing is named
  15 readable a week later?                          the event loop is fiddly
  16 lines, and how much is ceremony?                ~45, mostly bookkeeping
"""
import re
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

# NDJSON is the awkward case for a streaming parser: `ijson.parse` wants ONE
# document. `ijson.items(fh, '', multiple_values=True)` is the NDJSON door and
# it is not the obvious call — the obvious one silently stops after record 1.
prefixes, types, depths, containers = Counter(), defaultdict(Counter), [], Counter()
url = re.compile(r"https?://")
url_at = Counter()
n_rec = 0

with open("../source.jsonl", "rb") as fh:
    for prefix, event, value in ijson.parse(fh, multiple_values=True):
        if not prefix and event == "start_map":
            n_rec += 1
        if event in ("start_map", "start_array"):
            containers[prefix] += 1
            continue
        if event in ("end_map", "end_array"):
            continue
        if prefix:
            prefixes[prefix] += 1
            depths.append(prefix.count(".") + 1)
            if event != "map_key":
                types[prefix][event] += 1
        if event == "string" and url.search(value or ""):
            url_at[prefix] += 1

print(f"\n1. {len(prefixes):,} distinct prefixes, listing them costs "
      f"{len(str(sorted(prefixes))):,} chars "
      f"({100 * len(str(sorted(prefixes))) / 4813294:.0f}% of the file)")
for p, n in prefixes.most_common(8):
    print(f"     {p:52} {n:>6,}")
print("   ONE PER CENT — and that is the surprise. ijson's prefix listing is")
print("   111% of npm and 174% of Stripe; here it is under 1% of a 4.8 MB file.")
print("   The reason is that this document is DEEP and REPETITIVE rather than")
print("   keyed: 1,953 records share about 434 paths, so the listing is")
print("   proportional to structure by accident of the document rather than by")
print("   anything ijson did. The keys-as-data that IS here —")
print("   `snapshot.trackedFileBackups.<a file path>` — mints one prefix per")
print("   tracked file, but there are only 50 of them. Scale the tracked files")
print("   and this number scales with them.")

print(f"\n2. deepest prefix: {max(depths)} segments, +1 for the record object")
print("   itself = 10, which is the true depth. Each NDJSON line is a document")
print("   and ijson's prefix starts inside it.")
print(f"\n7. {n_rec:,} records, counted from the stream with nothing named.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. top-level key counts, leaf and container, straight off the stream:")
top = Counter({k: v for k, v in prefixes.items() if "." not in k})
topc = Counter({k: v for k, v in containers.items() if k and "." not in k})
for k in sorted(set(top) | set(topc), key=lambda k: -(top[k] + topc[k]))[:8]:
    print(f"     {k:26} {top[k]:>5} leaf  {topc[k]:>5} container")
print("   `type` is the only key on all 1,953 records. ijson counts absence and")
print("   null apart, because a null is an EVENT — the frame-shaped tools all")
print("   collapse the two.")

# ── 5. does any field change type ────────────────────────────────────────────
poly = {p: c for p, c in types.items() if len(c) > 1}
mixed = {p: (containers[p], sum(types[p].values())) for p in containers
         if p in types and containers[p] and sum(types[p].values())}
print(f"\n5. prefixes taking more than one scalar event type: {len(poly)}")
for p, c in list(poly.items())[:4]:
    print(f"     {p:52} {dict(c)}")
print(f"   prefixes that are SOMETIMES a container and sometimes a scalar: "
      f"{len(mixed)}")
for p, (a, b) in list(mixed.items())[:4]:
    print(f"     {p:52} container x{a:,}, scalar x{b:,}")
print("   `message.content` and `toolUseResult` are both here. ijson is the")
print("   only tool in the Python set that reports this WITHOUT unifying —")
print("   polars made both columns String, DuckDB made them JSON.")

# ── 6. are any object keys data ──────────────────────────────────────────────
kd = [p for p in prefixes if "trackedFileBackups." in p]
print(f"\n6. PARTLY. prefixes under trackedFileBackups: {len(kd)}")
for p in kd[:3]:
    print(f"     {p[:76]}")
print(f"   **{len(kd)} of the {len(prefixes)} prefixes — {100*len(kd)/len(prefixes):.0f}% "
      f"of the whole listing — are")
print("   under this one key**, and they describe 50 file paths. Each tracked")
print("   FILE PATH is its own prefix, so keys-as-data is over half of ijson's")
print("   answer to Q1 and is reported as structure. The listing is small here")
print("   only because 50 is small; the MECHANISM is npm's exactly.")

# ── 10, 11 ───────────────────────────────────────────────────────────────────
print(f"\n10. PARTLY. content blocks: "
      f"{types.get('message.content.item.type', Counter()).get('string', 0)} "
      f"`type` events under message.content[]")
print("   That is the BLOCK count, not the tool_use count — the stream carries")
print("   the type as a value and ijson has no filter, so telling tool_use from")
print("   tool_result means holding state across events.")
print("   The count is free; the ROWS are not — assembling events into records")
print("   is a hand-written state machine, which is writing the extractor.")

print(f"\n11. CANNOT BE ASKED on this entry. Measured: {sum(url_at.values())}")
print("   values contain a URL — and that ZERO is an artifact of the scrub, not")
print("   a fact about agent traces. `scrub.py` replaced every string longer")
print("   than 32 characters or occurring under 20 times with `x` of the same")
print("   length, so every URL in the original is gone by construction.")
print("   NOTES.md records this as one of the scrub's two stated costs. The")
print("   machinery works — it found 53 URLs on 11-jupyter-notebook — and there")
print("   is nothing here for it to find.")

# ── 3, 8, 9, 12 ──────────────────────────────────────────────────────────────
print("\n3, 8, 9, 12. CANNOT. ijson has no notion of a record, a row or a")
print("   table. Every number above is a counter over an event stream, and")
print("   anything needing two related values at once is the caller's problem.")
