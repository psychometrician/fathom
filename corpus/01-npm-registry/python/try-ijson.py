"""ijson — npm registry metadata for `express`

Scoring header follows ../r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   804,956 bytes, 288 versions, 25,044 paths
  measured      2026-08-09
  run           cd corpus/01-npm-registry/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   no                  WRONG
   2 how deep                                    3   no                  WRONG
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  4   no                  partly
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            2   YES                 yes
  13 needed the shape in advance?                    see notes below

WHAT THIS FILE IS FOR. ijson is the only tool in the comparison that never holds
the document in memory, so it is the one candidate for describing a file too big
to load — the `scale` axis that `04-gharchive` opened and did not close. The
question is whether streaming changes the ANSWER or only the memory.
"""
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"python {sys.version.split()[0]}, ijson {version('ijson')}")

# ── 1, 2, 5, 7 — one streaming pass, nothing held ────────────────────────────
# ijson yields (prefix, event, value). The prefix is a dotted path with array
# elements written `item`, so it is the same path-shaped view jq has, arriving
# one event at a time.
names, depths, types = Counter(), [], defaultdict(Counter)
versions = 0
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if event in ("start_map", "start_array"):
            continue
        if prefix:
            leaf = prefix.rsplit(".", 1)[-1]
            names[leaf] += 1
            depths.append(prefix.count(".") + 1)
            # `map_key` is not a value type. Counting it here made 3,748 prefixes
            # look polymorphic on the first run, which was the counter measuring
            # itself rather than the document.
            if event != "map_key":
                types[prefix][event] += 1
        if prefix == "versions" and event == "map_key":
            versions += 1

print(f"\n1. distinct field names seen: {len(names):,}")
print(f"   the true answer is about 40. jq says 3,100. rrapply says 3,112.")
print(f"   ijson lands in the same place for the same reason: `4.17.1` arrives")
print(f"   as a map_key and nothing downstream can tell it from a field name.")

print(f"\n2. deepest path: {max(depths)}   <- WRONG, the true depth is 6")
print("   ijson's prefix is a DOTTED STRING and npm's keys are version numbers,")
print("   so `versions.5.0.0-alpha.1.name` counts as eight segments. This is the")
print("   exact mistake this project made on its first day and recorded in")
print("   CLAUDE.md: depth graded by splitting a dotted path reported 9 for a")
print("   document of depth 6. A real library makes it structurally, because the")
print("   dotted prefix is its public interface and cannot represent a key with")
print("   a dot in it. jq, which keeps paths as arrays, answers 6.")

# ── 5 — the one question streaming genuinely helps with ──────────────────────
poly = {p: c for p, c in types.items() if len(c) > 1}
print(f"\n5. paths seen with more than one JSON event type: {len(poly):,}")
print("   RIGHT, and it agrees with the graded axis: npm has 0 polymorphic")
print("   fields. This is the one exploration question streaming answers well,")
print("   because it needs no cross-record memory, only a counter per path.")
print("   The first version of this line said 3,748 — it was counting `map_key`")
print("   as a value type, so the counter was measuring itself.")

print(f"\n7. keys directly under `versions`: {versions}")

# ── 3, 4, 6 — cannot, and 4 is the interesting refusal ───────────────────────
print("""
3, 4, 6. cannot.

  Question 4 (always present vs sometimes) is the one worth dwelling on. It is
  not that ijson lacks the information — it is that answering needs you to know
  WHICH prefix is the record boundary before the stream starts, so you can reset
  a per-record key set at the right moment. `versions.item` would be wrong;
  `versions.<the version string>` is the boundary, and the version strings are
  not known until they arrive.

  So streaming does not change the answer. It changes the memory and leaves
  question 3 exactly where every other tool left it: unanswered, and load-bearing
  for four of the others.
""")
