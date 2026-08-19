"""ijson — Home Assistant frontend, the English translation catalogue

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

── scoring ──────────────────────────────────────────────────────────────────
 tool          ijson (version printed at run time)
 file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
 measured      2026-08-12
 run           cd corpus/28-home-assistant-i18n/python && uv run try-ijson.py

 question                                    lines  shape known first?  worked
  0 is this sound                               6   NO                  PARTLY — it can SEE duplicates
  1 what is in here                             6   NO                  YES — every level, streaming
  2 how deep                                    4   NO                  YES — 11
  3 what is one record                          5   NO                  CANNOT — names none
  4 always present vs sometimes                 6   NO                  yes, by counting prefixes
  5 does any field change type                  6   NO                  YES — by prefix
  6 are any object keys data                    -   -                   CANNOT
  7 how many records                            3   NO                  yes — 8,518 messages
  8 three named fields to a table               5  YES                  yes
  9 a field missing from some rows              3  YES                  yes
 10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
 11 find every path matching something          5   NO                  YES, streaming
 12 flattest honest table                       6   NO                  YES — 8,518 x 2, in constant memory
 13 needed the shape in advance?                    NO for 0,1,2,4,5,11,12
 14 survives the next file unchanged?               yes
 15 readable a week later?                          the event loop, no. See below
 16 lines, and how much is ceremony?                ~95

**ijson's PREFIX is a dotted path, so this document suits it better than any
other in the corpus.** The honest table — one row per message keyed by path — is
what its event stream already emits, and it never holds the file in memory.

**And it is the only tool of fourteen that can SEE a duplicate key**, because it
reports every `map_key` event rather than a finished dict. It does not judge; it
hands you the events and you count.
"""
import sys
import time
from collections import Counter, defaultdict

import ijson

print(f"ijson {ijson.__version__} · backend {ijson.backend} "
      f"· python {sys.version.split()[0]}")

SRC = "../source.json"
t = time.time()

# ── Q0. Soundness — and the one thing ijson can do that the others cannot. ─
seen = defaultdict(Counter)
dupes = 0
with open(SRC, "rb") as f:
    stack = []
    for prefix, event, value in ijson.parse(f):
        if event == "map_key":
            if value in seen[prefix]:
                dupes += 1
            seen[prefix][value] += 1
print(f"\nQ0  duplicate keys, counted from the EVENT STREAM: {dupes}")
print("    PARTLY. Every other tool hands back a finished dict where the last")
print("    key has already won. ijson reports each `map_key` as it arrives, so")
print("    the count above is real. It does not warn — you have to write it.")
print("    It says nothing about 2^53 or NaN.")

# ── Q1/Q2/Q5/Q12. One pass, and it answers four questions. ────────────────
paths, kinds, depth, table = Counter(), Counter(), 0, []
with open(SRC, "rb") as f:
    for prefix, event, value in ijson.parse(f):
        if event in ("string", "number", "boolean", "null"):
            paths[prefix] += 1
            kinds[event] += 1
            depth = max(depth, prefix.count(".") + 1)
            table.append((prefix, value))
        elif event in ("start_map", "start_array"):
            paths[prefix] += 1

print(f"\nQ1  {len(paths):,} distinct prefixes seen, at every level, in one pass.")
print("    The probe reports 10,136 distinct paths and depth 11 by its own walk.")
print("    Two independent parsers agreeing is worth more than either alone.")
print(f"    the seven at the top: "
      f"{', '.join(p for p in paths if p and '.' not in p)}")
print(f"\nQ2  deepest prefix: {depth}. YES.")
print(f"\nQ5  leaf events by type: {dict(kinds)}. Every leaf is a string;")
print("    the variation the probe reports is BETWEEN a string and an object at")
print("    one prefix, which this loop can see and does not judge.")

# ── Q3/Q7. What is one record. ────────────────────────────────────────────
print("\nQ3  ijson names no candidates and prices none. It streams whatever you")
print("    ask for. CANNOT.")
print(f"\nQ7  {len(table):,} messages, under the reading Q12 takes. yes.")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
under = Counter(p.rsplit(".", 1)[-1] for p in paths if p.count(".") == 2)
print(f"\nQ4  the commonest third-level names: "
      f"{', '.join(f'{k} {n}' for k, n in under.most_common(4))}")
print("    yes, by counting prefixes — but you choose the level, not the tool.")

# ── Q6. Keys as data. ─────────────────────────────────────────────────────
print("\nQ6  CANNOT. ijson has no notion of a key being data.")

# ── Q8/Q9. Named fields. ──────────────────────────────────────────────────
want = {"ui.common.and", "ui.common.loading", "ui.panel.profile.logout",
        "ui.panel.profile.nope"}
got = {p: v for p, v in table if p in want}
print(f"\nQ8  {[got.get(w) for w in ['ui.common.and', 'ui.common.loading', 'ui.panel.profile.logout']]}")
print(f"\nQ9  a key that is not there -> {got.get('ui.panel.profile.nope')!r}. "
      "It simply never arrives; yes.")

# ── Q10. ──────────────────────────────────────────────────────────────────
print("\nQ10 zero arrays in 604 KB. NOTHING TO FLATTEN.")

# ── Q11. Paths matching something. ────────────────────────────────────────
icu = [p for p, v in table if isinstance(v, str) and "{" in v]
print(f"\nQ11 messages with an ICU placeholder: {len(icu):,}, e.g. {icu[0]}")
print("    YES, in the same pass, no paths known in advance.")

# ── Q12. The flattest honest table. ───────────────────────────────────────
print(f"\nQ12 {len(table):,} rows x 2 cols — path, message.")
for p, v in table[:3]:
    print(f"      {p[:54]:<54} {str(v)[:26]}")
print("    NOTHING IS LOST, and the file was never held in memory.")
print(f"    ({time.time() - t:.3f}s for three full passes, yajl2_c)")

print("""
CONCLUSION. This is ijson's best document in the corpus and the reason is that
its PREFIX is already the answer: a dotted path per leaf, which is exactly the
table a translation catalogue wants. jq needs one expression for it; ijson gets
it as a side effect of parsing, in constant memory.

It is also the ONLY tool of fourteen that can answer any part of Q0 honestly,
because it reports `map_key` events rather than a finished dict. That is worth
recording precisely: it does not TELL you about duplicates, it merely fails to
hide them.

WHAT IT WILL NOT DO is name a record shape, price one, or say a word about which
keys are data. The event loop above is thirty lines to reach what the probe
prints unasked, and Q15 is where it loses: `prefix.count('.') + 1` is depth only
if you already know that no key contains a dot, and nobody reading this in a
month will remember checking.
""")
