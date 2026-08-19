"""ijson — Grafana "Node Exporter Full", dashboard 1860

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

 ── scoring ──────────────────────────────────────────────────────────────────
  tool          ijson (version and backend printed at run time)
  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
  measured      2026-08-13
  run           cd corpus/27-grafana-dashboard/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               8   NO                  PARTLY
   1 what is in here                             3   NO                  yes
   2 how deep                                    1   NO                  yes — 12
   3 what is one record                          6   -                   CANNOT
   4 always present vs sometimes                 6   NO                  yes
   5 does any field change type                  5   NO                  yes
   6 are any object keys data                    2   NO                  yes, inferred
   7 how many records                            4   NO                  YES — 132
   8 three named fields to a table               8  YES                  yes
   9 a field missing from some rows              2  YES                  yes
  10 flatten the deepest array                   2   NO                  yes
  11 find every path matching something          3   NO                  yes
  12 flattest honest table                       4   NO                  YES, constant memory
  13 needed the shape in advance?                    NO — the prefix IS the shape
  14 survives the next file unchanged?               YES
  15 readable a week later?                          yes, if you know the event model
  16 lines, and how much is ceremony?                ~85

**ijson answers the central question by ACCIDENT, and that is the interesting
part.** It never asks what a panel is. It reports a prefix per event, and
`panels.item` and `panels.item.panels.item` are simply two of the prefixes it
emits. Counting the prefixes it hands you is enough — the nesting shows up as a
row in a frequency table nobody had to think to ask for.

**It is also the only tool of the fourteen that can SEE a duplicate key**,
because it reports every `map_key` event rather than a finished dict.
"""
import re
import sys
import time
from collections import Counter, defaultdict

import ijson

print(f"ijson {ijson.__version__} · backend {ijson.backend} "
      f"· python {sys.version.split()[0]}")

SRC = "../source.json"
t0 = time.time()

# ── Q0. Soundness, and the thing only ijson can do. ───────────────────────
#
# The counter must be per-OBJECT, on a stack. A first draft keyed it on the
# PREFIX and reported 14,967 duplicate keys — because `panels.item` is the same
# prefix for all 31 panels, so every field after the first looked like a repeat.
# Recorded because it is the same class of error as the one this document was
# chosen to expose: a count that is confidently wrong and looks plausible.
stack, dupes, big, widest = [], 0, 0, 0
with open(SRC, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if event == "start_map":
            stack.append(set())
        elif event == "end_map":
            widest = max(widest, len(stack[-1]))
            stack.pop()
        elif event == "map_key":
            if value in stack[-1]:
                dupes += 1
            stack[-1].add(value)
        elif event == "number" and abs(value) > 2**53:
            big += 1
print(f"\nQ0  duplicate keys, counted per object from the EVENT STREAM: {dupes}")
print(f"    integers past 2^53: {big}")
print("    PARTLY, and it is the strongest Q0 in the comparison. Every other tool")
print("    hands back a finished dict where the last duplicate has already won;")
print("    ijson reports each `map_key` as it arrives, so the count is real. It")
print("    does not warn — you write the counter yourself.")

# ── Q1/Q2/Q5/Q12. One pass, four questions, constant memory. ──────────────
prefixes, kinds, depth, table = Counter(), Counter(), 0, []
types_at = defaultdict(set)
with open(SRC, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if event in ("string", "number", "boolean", "null"):
            prefixes[prefix] += 1
            kinds[event] += 1
            types_at[prefix].add(event)
            depth = max(depth, prefix.count(".") + 1)
            table.append((prefix, value))
        elif event in ("start_map", "start_array"):
            prefixes[prefix] += 1

leaf_prefixes = {p for p, _ in table}
print(f"\nQ1  {len(prefixes)} distinct prefixes, one pass, nothing known in advance.")
print(f"    {len(leaf_prefixes)} of them end at a leaf, which is jq's 231 exactly;")
print("    the rest name a container, which jq's `paths` does not report.")
print(f"    the 25 at the root: {', '.join(sorted(p for p in prefixes if p and '.' not in p))[:140]}…")
print(f"\nQ2  {depth}. yes — the prefix depth is the document depth, and it agrees")
print("    with the probe's 12 and with jq's 12.")
print(f"\nQ12 {len(table):,} rows x 2, and the file was never held in memory.")
print(f"    leaf kinds: {dict(kinds)}")
print("    YES. The prefix is already a dotted path, so the honest table is what")
print("    the event stream emits — no recursion, no schema, no second pass.")
print("    WHAT IS LOST: `item` replaces the array index, so a row says a target")
print("    has an `expr` and not which target. Same loss as jq, for the same reason.")

# ── Q7. THE QUESTION, and ijson answers it without being asked. ───────────
panel_prefixes = {p: n for p, n in prefixes.items()
                  if re.fullmatch(r"(panels\.item\.)*panels\.item", p)}
print("\nQ7  THE CENTRAL QUESTION. Prefixes matching a panel, straight from Q1:")
starts = Counter()
with open(SRC, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if event == "start_map" and re.fullmatch(r"(panels\.item\.)*panels\.item", prefix):
            starts[prefix] += 1
for p, n in sorted(starts.items()):
    print(f"      {p:<32} {n:>4}")
total = sum(starts.values())
print(f"      {'TOTAL':<32} {total:>4}")
print("    YES — and note what did not happen: nothing here knows what a panel is.")
print("    `panels.item.panels.item` is a prefix ijson emits because the document")
print("    contains one. The nesting is a ROW IN A FREQUENCY TABLE, visible to")
print("    anyone who printed the prefixes, which Q1 does by default.")

# ── Q3. What is one record. ───────────────────────────────────────────────
print("\nQ3  readings, each a prefix count and none proposed by ijson:")
for label, pat in [("one panel per row (all depths)", r"(panels\.item\.)*panels\.item"),
                   ("one TOP-LEVEL panel per row", r"panels\.item"),
                   ("one target per row", r"(panels\.item\.)*panels\.item\.targets\.item"),
                   ("one template variable per row", r"templating\.list\.item")]:
    n = sum(c for pre, c in starts.items() if re.fullmatch(pat, pre)) or None
    if n is None:
        with open(SRC, "rb") as f:
            n = sum(1 for pre, ev, _ in ijson.parse(f)
                    if ev == "start_map" and re.fullmatch(pat, pre))
    print(f"      {label:<32} {n:>6,}")
print(f"      {'one leaf per row':<32} {len(table):>6,}")
print("    CANNOT. ijson proposes nothing and prices nothing; it is an event stream.")

# ── Q4. Always vs sometimes, over the 132 panels. ─────────────────────────
fields = Counter()
with open(SRC, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if event == "map_key" and re.fullmatch(r"(panels\.item\.)*panels\.item", prefix):
            fields[value] += 1
print(f"\nQ4  fields over the {total} panels, from `map_key` events:")
for k, n in fields.most_common():
    print(f"      {k:<16} {n:>4}  {'always' if n == total else ''}")
print("    yes, and cheaply — a key event carries its prefix, so no join is needed.")

# ── Q5. Type variation. ───────────────────────────────────────────────────
varying = {p: s for p, s in types_at.items() if len(s) > 1}
print(f"\nQ5  prefixes carrying more than one leaf event type: {len(varying)}")
for p, s in sorted(varying.items())[:6]:
    print(f"      {p:<52} {sorted(s)}")
print("    yes. Note these are PATHS, not fields — `null` counts as a type here,")
print("    which is the distinction the probe records as a decision.")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
print(f"\nQ6  no site uses keys as data; the widest object has {widest} keys and they")
print("    are field names. yes, inferred — ijson counts, the judgement is mine.")

# ── Q8/Q9. Three named fields, one row per panel, at BOTH depths. ─────────
# A STACK again, not a single `cur`. A row panel is still open when its children
# start, so one variable is overwritten by the inner panel and the outer row is
# appended twice. That draft reported `description` absent from 78 of 132 where
# jq says 84 — the count was wrong by exactly the 16 row panels.
PANEL = re.compile(r"(panels\.item\.)*panels\.item")
FIELD = re.compile(r"(panels\.item\.)*panels\.item\.(title|type|id|description)")
rows, open_panels = [], []
with open(SRC, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if PANEL.fullmatch(prefix):
            if event == "start_map":
                open_panels.append(
                    {"title": None, "type": None, "id": None, "description": None})
            elif event == "end_map":
                rows.append(open_panels.pop())
        elif open_panels and FIELD.fullmatch(prefix):
            open_panels[-1][prefix.rsplit(".", 1)[1]] = value
missing = sum(1 for r in rows if r["description"] is None)
print(f"\nQ8  {len(rows)} rows x 4. yes — but see the cost: a nine-line state")
print("    machine, because an event stream has no notion of a finished record")
print("    and a row panel is still open while its children stream past.")
print(f"      {rows[0]}")
print(f"\nQ9  `description` absent from {missing} of {len(rows)}; the row keeps its None")
print("    because the dict was pre-seeded. yes, and that is the honest idiom here:")
print("    absence is the key that never arrived, which ijson shows better than most.")

# ── Q10. Flatten the deepest array. ───────────────────────────────────────
deepest = max(prefixes, key=lambda p: p.count("."))
print(f"\nQ10 deepest prefix: {deepest}")
print(f"    {sum(1 for p in prefixes if '.item' in p)} prefixes contain an array step.")
print("    yes — and `panels.item.panels.item…` is right there in the answer again.")

# ── Q11. Find every path matching something. ──────────────────────────────
var = re.compile(r"\$node|\$job|\$__rate_interval")
hits = [(p, v) for p, v in table if isinstance(v, str) and var.search(v)]
print(f"\nQ11 {len(hits)} leaves mention a Grafana template variable. yes — the melt")
print("    is already a list of (path, value), so this is one comprehension.")
print(f"      e.g. {hits[0][0]}")

print(f"\n    ({time.time() - t0:.2f}s, {len(table):,} leaves, constant memory)")

print("""
CONCLUSION. ijson reaches 132 and it is the only tool of the fourteen that does
so without anyone deciding to look for it. The others need a recursive descent
you chose to write (`..`, `json_tree`, `rrapply(how="melt")`); ijson emits
`panels.item.panels.item` as an ordinary prefix, so the nesting appears in the
Q1 output of a person who asked only "what is in here".

That is the strongest single result in this comparison and it should be read
carefully, because it is narrower than it looks. ijson SHOWS the prefix; it does
not say the prefix matters, does not count it against `panels.item`, and does
not warn that one of the two is the answer to the question you asked. The
frequency table has 231 rows and two of them are the finding.

The cost is Q8: eight lines of state machine to reconstruct a record that every
other tool gets for free, because an event stream has no notion of a finished
object. ijson is the best explorer here and the worst extractor, and those are
the two halves this project insists on scoring separately.
""")
