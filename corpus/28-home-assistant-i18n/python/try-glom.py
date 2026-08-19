"""glom — Home Assistant frontend, the English translation catalogue

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

── scoring ──────────────────────────────────────────────────────────────────
 tool          glom (version printed at run time)
 file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
 measured      2026-08-12
 run           cd corpus/28-home-assistant-i18n/python && uv run try-glom.py

 question                                    lines  shape known first?  worked
  0 is this sound                               1   -                   CANNOT
  1 what is in here                             3   NO                  ONE LEVEL — 7
  2 how deep                                    -   -                   CANNOT
  3 what is one record                          2   -                   CANNOT
  4 always present vs sometimes                 -   -                   CANNOT
  5 does any field change type                  -   -                   CANNOT
  6 are any object keys data                    -   -                   CANNOT
  7 how many records                            2  YES                  only what you name
  8 three named fields to a table               5  YES                  YES — this is glom's job
  9 a field missing from some rows              4  YES                  YES — `default` is the point
 10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
 11 find every path matching something          1   -                   CANNOT
 12 flattest honest table                       1   -                   CANNOT
 13 needed the shape in advance?                    YES for everything it did
 14 survives the next file unchanged?               only if the paths survive
 15 readable a week later?                          YES — the spec IS the shape
 16 lines, and how much is ceremony?                ~60

**glom is a restructuring tool, not an exploring one, and this document makes
that unusually clear**: there is nothing here BUT structure to discover, and glom
discovers none of it. Every question it answers, it answers because I told it the
answer first.
"""
import json
import sys

import glom
from glom import Coalesce, glom as G

print(f"glom {glom.__version__} · python {sys.version.split()[0]}")

doc = json.load(open("../source.json"))

print("\nQ0  glom does not parse; json.load did, and said nothing. CANNOT.")

print(f"\nQ1  glom has no listing verb. python's own `list(doc)` gives the top")
print(f"    level, {len(doc)} keys: {', '.join(doc)}")
print("    ONE LEVEL, and not by glom. For the levels below you must already")
print("    know what to ask for.")

print("\nQ2  CANNOT. No depth verb.")
print("\nQ3  CANNOT. glom names no record shapes and prices none.")
print("\nQ4  CANNOT — it has no notion of a population of records to compare.")
print("\nQ5  CANNOT.")
print("\nQ6  CANNOT. Every key in this file is a message id and glom cannot say so.")

print(f"\nQ7  only what you name: len(doc['ui']) = {len(doc['ui'])} sections.")

# ── Q8. Three named fields. This is what glom is for. ─────────────────────
spec = {
    "and": "ui.common.and",
    "loading": "ui.common.loading",
    "logout": "ui.panel.profile.logout",
}
print(f"\nQ8  {G(doc, spec)}")
print("    YES, and it reads well. The spec is the shape of the answer.")

# ── Q9. A missing field. ──────────────────────────────────────────────────
spec2 = {
    "logout": "ui.panel.profile.logout",
    "missing": Coalesce("ui.panel.profile.nope", default=None),
}
print(f"\nQ9  {G(doc, spec2)}")
print("    YES. `Coalesce(..., default=None)` is exactly the case, and it is the")
print("    one place glom is plainly better than a chain of .get() calls.")

print("\nQ10 zero arrays in this document. NOTHING TO FLATTEN.")
print("\nQ11 CANNOT. No search over paths; you bring the path.")
print("\nQ12 CANNOT. glom restructures into a shape you specify and this")
print("    document's honest table has 8,518 rows nobody can specify by hand.")

print("""
CONCLUSION. glom does Q8 and Q9 well and cannot attempt eight of the others.
That is not a criticism — it is a restructuring tool and it says so — but this
document is the sharpest case in the corpus for the distinction the project is
built on. There is nothing here except structure to find out, and glom's entire
interface assumes you already have.

`Coalesce` is worth naming as prior art for `whichever`: same idea, same
default-on-absence behaviour, and it predates the question.
""")
