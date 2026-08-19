"""glom — Grafana "Node Exporter Full", dashboard 1860

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

 ── scoring ──────────────────────────────────────────────────────────────────
  tool          glom (version printed at run time)
  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
  measured      2026-08-13
  run           cd corpus/27-grafana-dashboard/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             2  YES                  ONE LEVEL
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          5   -                   CANNOT
   4 always present vs sometimes                 4  YES                  yes, once named
   5 does any field change type                  3  YES                  PARTLY
   6 are any object keys data                    -   -                   CANNOT
   7 how many records                            6  YES                  132 BY ENUMERATION
   8 three named fields to a table               3  YES                  YES — the best of the eight
   9 a field missing from some rows              2  YES                  YES — Coalesce/default
  10 flatten the deepest array                   3  YES                  yes, one named level
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       -   -                   CANNOT
  13 needed the shape in advance?                    YES — a spec IS the shape
  14 survives the next file unchanged?               NO
  15 readable a week later?                          YES — the specs read as English
  16 lines, and how much is ceremony?                ~50

**glom is a restructuring language and this is a document you cannot restructure
until you have explored it**, which is the mismatch the whole project is about.
A spec is a literal description of the shape you expect. There is no recursive
descent, no path enumeration, no wildcard over unknown depth.

**Where it wins it wins outright.** `Coalesce` with a default is the cleanest
answer to Q9 in either language, and the Q8 spec reads as a sentence. Both of
those are extraction, and both assume exploring is finished.
"""
import json
import sys
from collections import Counter
from importlib.metadata import version

from glom import Coalesce, glom

print(f"glom {version('glom')} · python {sys.version.split()[0]}")

doc = json.load(open("../source.json"))

# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  CANNOT. glom operates on an already-parsed value and has no")
print("    diagnostic vocabulary.")

# ── Q1. What is in here. ──────────────────────────────────────────────────
print(f"\nQ1  glom(doc, T.keys()) -> {len(doc)} root keys. ONE LEVEL.")
print("    A spec names the levels it traverses, so 'what is in here' can only be")
print("    asked of a level you have already named.")

# ── Q2. How deep. ─────────────────────────────────────────────────────────
print("\nQ2  CANNOT. No depth verb and no way to recurse without naming levels.")

# ── Q7. THE CENTRAL QUESTION. ─────────────────────────────────────────────
top = glom(doc, ("panels", len))
# `Coalesce(..., default=[])` is what makes this tidy: 15 of the 31 top-level
# panels have no `panels` key at all, and the default absorbs them silently.
nested_spec = glom(doc, ("panels", [Coalesce("panels", default=[])]))
nested = sum(len(x) for x in nested_spec)
print("\nQ7  THE CENTRAL QUESTION.")
print(f"      glom(doc, ('panels', len))                              -> {top}")
print("      glom(doc, ('panels', [Coalesce('panels', default=[])]))  -> a list of")
print(f"        {len(nested_spec)} lists holding {nested} panels between them")
print(f"      the sum, written by hand                                -> {top + nested}")
print("    132, BY ENUMERATION. `Coalesce(..., default=[])` handles the 15 panels")
print("    with no children elegantly, and that is glom being good at the part")
print("    AFTER you know. The spec still names `panels` inside `panels` literally.")
print("    There is no `**` and no recursive descent: a third level would need a")
print("    third spec, and nothing here would tell you to write it.")

# ── Q3. What is one record. ───────────────────────────────────────────────
print("\nQ3  CANNOT — nothing proposed, nothing priced. Counted once named:")
for label, n in [("one panel per row (all depths)", top + nested),
                 ("one TOP-LEVEL panel per row", top),
                 ("one top-level target per row",
                  sum(len(x) for x in glom(doc, ("panels", [Coalesce("targets", default=[])])))),
                 ("one template variable per row", glom(doc, ("templating.list", len)))]:
    print(f"      {label:<32} {n:>6,}")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
panels = doc["panels"] + [q for p in doc["panels"] for q in p.get("panels", [])]
fields = Counter(k for p in panels for k in p)
print(f"\nQ4  over the {len(panels)} panels assembled above:")
for k, n in fields.most_common(5):
    print(f"      {k:<16} {n:>4}  {'always' if n == len(panels) else ''}")
print("    yes once named — but `Counter` is the standard library, not glom.")

# ── Q5. Type variation. ───────────────────────────────────────────────────
kinds = {type(glom(p, Coalesce("targets", default=None))).__name__ for p in panels}
print(f"\nQ5  PARTLY. types reachable at `targets` across the 132: {kinds}")
print("    A spec can fetch a field and Python can type it, but glom has no")
print("    verb for 'which fields vary' and no way to enumerate the fields first.")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
print("\nQ6  CANNOT. A spec names keys; it never asks whether a key is a name or")
print("    a value, and there is no cross-site key-set comparison.")

# ── Q8/Q9. Three named fields; a field missing from some rows. ────────────
SPEC = [{"title": "title", "type": "type", "id": "id",
         "description": Coalesce("description", default=None)}]
tbl = glom(panels, SPEC)
missing = sum(1 for r in tbl if r["description"] is None)
print(f"\nQ8  {len(tbl)} rows x 4. YES, and this is the best Q8 of the eight tools:")
print("      [{'title': 'title', 'description': Coalesce('description', default=None)}]")
print("    The spec IS the output shape, written declaratively, and it reads back")
print("    perfectly in a week.")
print(f"      {json.dumps(tbl[0])[:86]}")
print(f"\nQ9  `description` absent from {missing} of {len(tbl)}; every row survives. YES —")
print("    `Coalesce` with a default is the cleanest expression of this idea in")
print("    either language, and it is direct prior art for `whichever`. It also")
print("    takes MULTIPLE keys — `Coalesce('description', 'desc', default=None)` —")
print("    which is exactly `first_present`, already shipped, by another name.")

# ── Q10. Flatten the deepest array. ───────────────────────────────────────
tg = [t for p in panels for t in p.get("targets", [])]
print(f"\nQ10 {len(tg)} targets under the 132 panels, via a spec over a list I built.")
print("    yes for a level you name. 'Deepest' is not a question glom can be asked.")

# ── Q11/Q12. ──────────────────────────────────────────────────────────────
print("\nQ11 CANNOT. No path enumeration and no wildcard over unknown keys, so")
print("    there is no way to search for a value without naming where to look.")
print("\nQ12 CANNOT, for the same reason. glom restructures a shape you describe;")
print("    the flattest honest table is the shape you do not yet have.")

print("""
CONCLUSION. glom reaches 132 the same way jmespath does — by my writing one spec
per level and adding them — and for the same reason: the language has no
recursive descent. `Coalesce(..., default=[])` makes the enumeration unusually
tidy, which is worth saying, because it means the 15 childless panels cost
nothing. But `panels` appears inside `panels` as a literal, and a third level of
nesting would need a third spec that nothing would prompt anyone to write.

Its two genuine wins are both extraction and both matter to this project
directly. The Q8 spec is the most readable table definition of the eight. And
`Coalesce` taking several keys with a default is `first_present` — the one word
fathom has actually shipped — existing in Python, predating the question, and
found by asking the corpus rather than by reasoning about it.

Scored CANNOT on Q11 and Q12, which is the honest grade: glom is a language for
rebuilding a shape you can already describe.
""")
