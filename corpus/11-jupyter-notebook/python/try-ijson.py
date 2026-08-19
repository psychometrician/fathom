"""ijson — Jupyter notebook, Norvig Advent-2021, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
  measured      2026-08-10
  run           cd corpus/11-jupyter-notebook/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             6   NO                  yes
   2 how deep                                    4   NO                  yes
   3 what is one record                          -   -                   CANNOT
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  5   NO                  yes
   6 are any object keys data                    4   NO                  PARTLY
   7 how many records                            3   NO                  yes
   8 three named fields to a table               -   -                   CANNOT
   9 a field missing from some rows              -   -                   CANNOT
  10 flatten the deepest array                   3   YES                 PARTLY
  11 find every path matching something          4   NO                  yes
  12 flattest honest table                       -   -                   CANNOT
  13 needed the shape in advance?                    NO for 1-7 and 11
  14 survives the next file unchanged?               YES — nothing is named
  15 readable a week later?                          event loops are fiddly
  16 lines, and how much is ceremony?                ~45, mostly bookkeeping
"""
import re
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

# ── 1, 2, 4, 5, 6, 7, 11 in ONE pass ─────────────────────────────────────────
# ijson is the only tool in the Python set that answers the exploration half
# WITHOUT being told a single field name — every counter below is driven by the
# event stream. It is also the only one that never builds the document.
prefixes, types, depths, containers = Counter(), defaultdict(Counter), [], Counter()
cells = outputs = 0
url = re.compile(r"https?://")
url_at, url_in = Counter(), 0
mime = Counter()

with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
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
        if prefix == "cells.item.cell_type":
            cells += 1
        if prefix == "cells.item.outputs.item.output_type":
            outputs += 1
        if prefix == "cells.item.outputs.item.data" and event == "map_key":
            mime[value] += 1
        if event == "string" and url.search(value or ""):
            url_in += 1
            url_at[prefix] += 1

print(f"\n1. {len(prefixes)} distinct prefixes, listing them costs "
      f"{len(str(sorted(prefixes))):,} chars "
      f"({100 * len(str(sorted(prefixes))) / 1114184:.2f}% of the file)")
for p, n in prefixes.most_common(9):
    print(f"     {p:44} {n:>6,}")
print("   Under 1% of the file, unlike npm (111%) and Stripe (174%). This")
print("   document has no keys-as-data of any size, so the prefix listing")
print("   stays proportional to structure — the one case where it does.")

print(f"\n2. deepest prefix: {max(depths)} segments")
print("   `cells.item.outputs.item.data.text/plain.item` — and `item` is how")
print("   ijson writes an array element, so a document with a field CALLED")
print("   `item` is ambiguous in this notation. This one has none.")

# ── 4, 7 ─────────────────────────────────────────────────────────────────────
print(f"\n7. {cells} cells, {outputs} outputs — counted from the stream, with")
print("   no field named in advance beyond the two whose counts they are.")

print("\n4. counts per prefix ARE the always/sometimes answer, unasked:")
for f in ("cell_type", "source", "metadata", "execution_count", "outputs"):
    k = f"cells.item.{f}"
    print(f"     cells.item.{f:16} {prefixes.get(k, 0):>5} leaf  "
          f"{containers.get(k, 0):>5} container")
print("   `cell_type` 272 against `execution_count` 132: present-vs-absent,")
print("   with the 1 explicit null counted as present. ijson is the only tool")
print("   here that separates absence from null, because a null is an EVENT.")
print("   AND `source`, `metadata` and `outputs` count ZERO as leaves, because")
print("   their values are containers. A leaf-only tally cannot see a field")
print("   whose value is an array — the same blindness VERDICT.md records in")
print("   jq's `paths(scalars)` dropping `children` from 02-hn-thread. Both")
print("   columns are printed here so the count is not read as an absence.")

# ── 5 ────────────────────────────────────────────────────────────────────────
poly = {p: c for p, c in types.items() if len(c) > 1}
print(f"\n5. prefixes taking more than one event type: {len(poly)}")
for p, c in poly.items():
    print(f"     {p:44} {dict(c)}")
print("   `execution_count` is number x131, null x1 — and this is ragged BY")
print("   NULL rather than a type change, which the raw event count cannot")
print("   distinguish. The same reading design/probe.py had to be repaired for.")

# ── 6 ────────────────────────────────────────────────────────────────────────
print(f"\n6. PARTLY. mime keys seen under outputs[].data: {dict(mime)}")
print("   ijson reports them as `map_key` events, which is more than most tools")
print("   give — a key ARRIVING as a value-like event. But it says nothing")
print("   about whether they are data, and the prefix folds them all to")
print("   `cells.item.outputs.item.data.text/plain`, a field name.")

# ── 11. every path whose value matches ───────────────────────────────────────
print(f"\n11. {url_in} string values contain a URL, at {len(url_at)} prefixes:")
for p, n in url_at.most_common():
    print(f"     {p:44} {n:>4}")
print("   Found without naming a path, which is the question's point. Note")
print("   these values CONTAIN a URL and none IS one — they are markdown prose")
print("   — so a predicate anchored at the start of the value finds nothing.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
print(f"\n10. PARTLY. text/plain lines: "
      f"{prefixes.get('cells.item.outputs.item.data.text/plain.item', 0)}")
print("   The count is free; the ROWS are not. ijson yields events, so")
print("   assembling them into a table is a hand-written state machine.")

# ── 3, 8, 9, 12 ──────────────────────────────────────────────────────────────
print("\n3, 8, 9, 12. CANNOT. ijson has no notion of a record, a row or a")
print("   table. Everything above is a counter over an event stream; anything")
print("   that must hold two related values at once is the caller's problem,")
print("   and writing that state machine is writing the extractor by hand.")
