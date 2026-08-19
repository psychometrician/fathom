"""jq — Home Assistant frontend, the English translation catalogue

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

── scoring ──────────────────────────────────────────────────────────────────
 tool          jq, the python binding (version printed at run time)
 file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
 measured      2026-08-12
 run           cd corpus/28-home-assistant-i18n/python && uv run try-jq.py

 question                                    lines  shape known first?  worked
  0 is this sound                               1   -                   CANNOT
  1 what is in here                             5   NO                  YES — every level
  2 how deep                                    3   NO                  YES — 11
  3 what is one record                          8   NO                  names none, counts any
  4 always present vs sometimes                 6   NO                  yes, once you pick a level
  5 does any field change type                  7   NO                  YES — by path
  6 are any object keys data                    -   -                   CANNOT — no notion
  7 how many records                            3   NO                  yes
  8 three named fields to a table               3  YES                  yes
  9 a field missing from some rows              4  YES                  yes — null, not an error
 10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
 11 find every path matching something          4   NO                  YES, and it is one line
 12 flattest honest table                       5   NO                  YES — 8,518 x 2, the RIGHT shape
 13 needed the shape in advance?                    NO for 1, 2, 5, 11, 12
 14 survives the next file unchanged?               yes — nothing is hard-coded
 15 readable a week later?                          `paths(scalars)` yes; the type census no
 16 lines, and how much is ceremony?                ~95

**jq is the best tool in the corpus on this document, and the reason is one
expression.** `paths(scalars)` produces exactly the shape a translation catalogue
wants — one row per message, keyed by its path — and nothing else in either
language offers it without being told the paths first.

**`leaf_paths` is the builtin name for it and this binding does not define it**,
so the expression below is its definition, written out. Recorded because a
reader who types the documented name gets a compile error.
"""
import json
import sys
import time
from collections import Counter

import jq

print(f"jq {jq.__version__ if hasattr(jq, '__version__') else '(python binding)'}"
      f" · python {sys.version.split()[0]}")

raw = open("../source.json").read()
doc = json.loads(raw)


def q(expr):
    return jq.compile(expr).input(doc).first()


# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  jq parses and says nothing. No duplicate-key report, no 2^53 flag.")
print("    CANNOT.")

t = time.time()

# ── Q1. What is in here, at every level. ──────────────────────────────────
print(f"\nQ1  top level: {', '.join(q('keys_unsorted'))}")
n_paths = q("[paths] | length")
n_leaf = q("[paths(scalars)] | length")
print(f"    [paths] | length         -> {n_paths:,} paths at every level")
print(f"    [paths(scalars)] | length -> {n_leaf:,} of them are leaves")
print("    YES. One expression, every level, no shape known in advance.")

# ── Q2. How deep. ─────────────────────────────────────────────────────────
depth = q("[paths | length] | max")
print(f"\nQ2  [paths | length] | max -> {depth}. YES.")

# ── Q3/Q7. What is one record. ────────────────────────────────────────────
print("\nQ3  jq names no candidates and prices none. It counts any unit you name:")
for expr, what in [(".ui | keys | length", "an entry of ui"),
                   ("[paths(scalars)] | length", "one message per row"),
                   ("[paths(type==\"object\")] | length", "one object per row")]:
    print(f"      {what:<26} {q(expr):>6,}   ({expr})")
print("    CANNOT for Q3 — three defensible answers, and jq proposed none of")
print("    them. The probe names 53 and prices each.")
print(f"\nQ7  {n_leaf:,} messages under the reading Q12 takes. YES.")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
sub = q('[.ui.panel.config | .. | objects | keys_unsorted] | flatten')
common = Counter(sub)
print(f"\nQ4  keys under ui.panel.config, by how many objects carry them:")
print(f"      {', '.join(f'{k} {n}' for k, n in common.most_common(4))}")
print("    yes, but only once you have chosen a level to ask about.")

# ── Q5. Does any field change type. ───────────────────────────────────────
# `.first()` takes ONE output, so an expression that streams values gives back
# its first and a Counter then counts that string's characters. Ask for an
# object instead and there is nothing to stream.
kinds = q('[paths as $p | getpath($p)|type] | group_by(.) '
          '| map({(.[0]): length}) | add')
print(f"\nQ5  every path by jq type: {kinds}")
mixed = q('[paths(type=="object") as $p | getpath($p) | to_entries | '
          'map(.value|type) | unique | select(length>1)] | length')
print(f"    objects holding BOTH a string and an object: {mixed:,}")
print("    YES — and this is the number defect 32 turns on. jq finds it in one")
print("    expression and draws no conclusion from it.")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
print("\nQ6  CANNOT. jq has no notion of a key being data rather than a name.")
print("    Every key here IS a message id, which is the whole document.")

# ── Q8/Q9. Named fields; a missing one. ───────────────────────────────────
print(f"\nQ8  {q('[.ui.common.and, .ui.common.loading, .ui.panel.profile.logout]')}")
print(f"\nQ9  a key that is not there -> {q('.ui.panel.profile.nope')} — jq gives")
print("    null rather than an error, so the row survives. yes.")

# ── Q10. The deepest array. ───────────────────────────────────────────────
print(f"\nQ10 arrays in this document: {q('[paths(type==\"array\")] | length')}. "
      "NOTHING TO FLATTEN.")

# ── Q11. Paths matching something. ────────────────────────────────────────
icu = q('[paths(scalars) as $p | select(getpath($p) | test("\\\\{")) | $p|join(".")]')
print(f"\nQ11 messages carrying an ICU placeholder: {len(icu):,}")
print(f"    e.g. {icu[0]}")
print("    ONE EXPRESSION, no paths known in advance. YES.")

# ── Q12. The flattest honest table. ───────────────────────────────────────
table = q('[paths(scalars) as $p | {path: ($p|join(".")), message: getpath($p)}]')
print(f"\nQ12 [paths(scalars) as $p | ...] -> {len(table):,} rows x 2 cols")
for r in table[:3]:
    print(f"      {r['path'][:54]:<54} {r['message'][:26]}")
print("    NOTHING IS LOST. Every message, with its full path as its key.")
print(f"    ({time.time() - t:.1f}s)")

print("""
CONCLUSION. jq is the strongest tool in the corpus on this document and the
reason is `paths(scalars)`. A translation catalogue's honest table is one row per
message keyed by path, and that is one expression — no shape known in advance,
nothing hard-coded, survives the next release of the file unchanged.

pandas produces the exact TRANSPOSE of it, 1 x 8,518, and calls that a frame.

WHAT JQ STILL WILL NOT DO is name the alternatives. Three readings of 'one
record' are defensible here — 8,518 messages, 1,619 objects, or 16 panels — and
jq counts whichever you name while proposing none and pricing none. That gap is
unchanged across all 28 entries.

AND FATHOM DOES BADLY HERE. The probe describes this file at 5.69% of its input
with 39.3% of fields unnamed, the worst in the corpus, because a catalogue of
one-off groups gives the fold nothing to fold. On this document jq's answer is
better than fathom's, and that is worth more written down than argued away.
""")
