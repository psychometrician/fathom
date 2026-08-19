"""pydash — Home Assistant frontend, the English translation catalogue

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

── scoring ──────────────────────────────────────────────────────────────────
 tool          pydash (version printed at run time)
 file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
 measured      2026-08-12
 run           cd corpus/28-home-assistant-i18n/python && uv run try-pydash.py

 question                                    lines  shape known first?  worked
  0 is this sound                               1   -                   CANNOT
  1 what is in here                             3   NO                  ONE LEVEL — keys()
  2 how deep                                    -   -                   CANNOT
  3 what is one record                          2   -                   CANNOT
  4 always present vs sometimes                 -   -                   CANNOT
  5 does any field change type                  4  YES                  only where you look
  6 are any object keys data                    -   -                   CANNOT
  7 how many records                            3  YES                  only what you name
  8 three named fields to a table               4  YES                  yes — `get` with a path
  9 a field missing from some rows              3  YES                  YES — default is the point
 10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
 11 find every path matching something          1   -                   CANNOT
 12 flattest honest table                       5   NO                  PARTLY — see below
 13 needed the shape in advance?                    YES, except Q12
 14 survives the next file unchanged?               yes for Q12; nothing else
 15 readable a week later?                          YES
 16 lines, and how much is ceremony?                ~60

**pydash is the one path-taker of the three with a recursive verb**, and it is
not advertised as one: `flatten_deep` is for lists, but `pydash.objects.to_pairs`
plus a hand-written walk is the usual answer and that is not pydash doing the
work. What it does have is `get` with a dotted path and a default, which is
`whichever` with one argument.
"""
import json
import sys

import pydash as _

print(f"pydash {_.__version__ if hasattr(_, '__version__') else '(installed)'} "
      f"· python {sys.version.split()[0]}")
doc = json.load(open("../source.json"))

print("\nQ0  json.load parsed and said nothing. CANNOT.")

print(f"\nQ1  _.keys(doc) -> {len(_.keys(doc))}: {', '.join(_.keys(doc))}")
print("    ONE LEVEL. pydash has no recursive listing verb for objects.")

print("\nQ2  CANNOT.")
print("\nQ3  CANNOT. No candidates named, none priced.")
print("\nQ4  CANNOT.")

ui = doc["ui"]
strs = _.count_by(ui, lambda v: type(v).__name__)
print(f"\nQ5  types under `ui`, a path I had to name: {dict(strs)}")
print("    only where you look.")

print("\nQ6  CANNOT.")

print(f"\nQ7  only what you name:")
print(f"      len(ui)        {len(ui)}")
print(f"      len(ui.panel)  {len(doc['ui']['panel'])}")

print(f"\nQ8  {[_.get(doc, p) for p in ['ui.common.and', 'ui.common.loading', 'ui.panel.profile.logout']]}")
print("    `_.get` with a dotted path. yes, and it reads well.")

print(f"\nQ9  _.get(doc, 'ui.panel.profile.nope', 'MISSING') -> "
      f"{_.get(doc, 'ui.panel.profile.nope', 'MISSING')!r}")
print("    YES. The default argument is exactly the case, and it is the closest")
print("    thing in the eight to what `whichever` is proposed for.")

print("\nQ10 zero arrays. NOTHING TO FLATTEN.")
print("\nQ11 CANNOT. No search over unnamed paths.")

# ── Q12. The melt, by hand. ───────────────────────────────────────────────
rows = []


def walk(o, prefix=""):
    for k, v in o.items():
        p = f"{prefix}.{k}" if prefix else k
        walk(v, p) if isinstance(v, dict) else rows.append((p, v))


walk(doc)
print(f"\nQ12 {len(rows):,} rows x 2 — and the four lines above are plain python.")
print("    PARTLY, and the qualification is the point: pydash contributed")
print("    nothing to it. `_.to_pairs` is one level; the recursion is mine.")

print("""
CONCLUSION. pydash sits with glom and jmespath: a path-taker, excellent at Q8 and
Q9, unable to start on the exploring half. Its `get(obj, path, default)` is the
clearest prior art in the eight for `whichever`, and it predates the question by
years.

The Q12 melt above is four lines of ordinary python and no pydash. Recorded as
PARTLY rather than YES for that reason — writing the recursion yourself is
always available in every language and says nothing about the tool.
""")
