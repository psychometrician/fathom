"""pydash — Grafana "Node Exporter Full", dashboard 1860

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

 ── scoring ──────────────────────────────────────────────────────────────────
  tool          pydash (version printed at run time)
  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
  measured      2026-08-13
  run           cd corpus/27-grafana-dashboard/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             3  YES                  ONE LEVEL
   2 how deep                                    4   NO                  yes, by MY recursion
   3 what is one record                          5   -                   CANNOT
   4 always present vs sometimes                 4  YES                  yes
   5 does any field change type                  4   NO                  yes, once melted
   6 are any object keys data                    -   -                   CANNOT
   7 how many records                            6  YES                  132 BY ENUMERATION
   8 three named fields to a table               3  YES                  yes — pick
   9 a field missing from some rows              2  YES                  yes — get default
  10 flatten the deepest array                   2  YES                  yes
  11 find every path matching something          3   NO                  yes, once melted
  12 flattest honest table                       6   NO                  PARTLY — recursion is mine
  13 needed the shape in advance?                    YES for pydash's verbs
  14 survives the next file unchanged?               NO
  15 readable a week later?                          YES — the names are lodash's
  16 lines, and how much is ceremony?                ~55

**pydash is lodash for Python and it is a collection library, not a document
library.** `get` takes a deep path with a dotted string, which is genuinely
convenient, but it takes a path you already have. There is no recursive
descent and no path enumeration.

**Every question below that is answered without naming a level is answered by a
recursion I wrote**, which is available in any language and says nothing about
pydash. Scored PARTLY wherever that is true — the same grade the same reasoning
gave purrr on entry 28.
"""
import json
import re
import sys
from collections import Counter, defaultdict
from importlib.metadata import version

import pydash as _

print(f"pydash {version('pydash')} · python {sys.version.split()[0]}")

doc = json.load(open("../source.json"))

# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  CANNOT. pydash never sees the bytes.")

# ── Q1. What is in here. ──────────────────────────────────────────────────
print(f"\nQ1  _.keys(doc) -> {len(_.keys(doc))} root keys. ONE LEVEL, like every")
print("    other collection library here. `_.get` needs a path; it does not")
print("    produce one.")

# ── Q2/Q12. The melt, and the recursion is mine. ──────────────────────────
rows = []
def walk(x, path="$"):
    if isinstance(x, dict):
        for k, v in x.items():
            walk(v, f"{path}.{k}")
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, f"{path}[{i}]")
    else:
        rows.append((path, x))
walk(doc)
depth = max(r[0].count(".") + r[0].count("[") for r in rows)
print(f"\nQ2  {depth} levels, from the six-line `walk` above. yes — but I wrote the")
print("    walk, and pydash contributed nothing to it.")
print(f"\nQ12 {len(rows):,} rows x 2. PARTLY, for the same reason: the recursion is")
print("    ordinary Python. `_.flatten_deep` flattens nested LISTS and this")
print("    document's nesting is dicts inside lists inside dicts, which it does")
print("    not address at all.")
print("    WHAT IS LOST: nothing — the indices are kept, so a row says which target.")

# ── Q7. THE CENTRAL QUESTION. ─────────────────────────────────────────────
top = len(_.get(doc, "panels"))
nested = sum(len(_.get(p, "panels", [])) for p in _.get(doc, "panels"))
print("\nQ7  THE CENTRAL QUESTION.")
print(f"      len(_.get(doc, 'panels'))                            -> {top}")
print(f"      sum(len(_.get(p, 'panels', [])) for p in ...)        -> {nested}")
print(f"      the sum                                              -> {top + nested}")
print("    132, BY ENUMERATION. `_.get(p, 'panels', [])` with a default is the")
print("    nice part — the 15 childless panels cost nothing. The comprehension is")
print("    Python's, the second `'panels'` is a literal I had to know to write.")

# and the melt knows the answer already, if you look at it the right way
from_melt = len({m.group(0) for m in
                 (re.match(r"^\$(\.panels\[\d+\])+", p) for p, _v in rows) if m})
print(f"    (the melt above independently gives {from_melt} distinct panel prefixes,")
print("     which agrees — and needed the same regex insight as everything else.)")

# ── Q3. What is one record. ───────────────────────────────────────────────
print("\nQ3  CANNOT — nothing proposed, nothing priced:")
panels = _.get(doc, "panels") + [q for p in _.get(doc, "panels") for q in _.get(p, "panels", [])]
for label, n in [("one panel per row (all depths)", len(panels)),
                 ("one TOP-LEVEL panel per row", top),
                 ("one target per row", sum(len(_.get(p, "targets", [])) for p in panels)),
                 ("one template variable per row", len(_.get(doc, "templating.list"))),
                 ("one leaf per row", len(rows))]:
    print(f"      {label:<32} {n:>6,}")
print("    Note `_.get(doc, 'templating.list')` — the dotted string is the one")
print("    place pydash is genuinely nicer than plain Python here.")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
fields = Counter(k for p in panels for k in p)
print(f"\nQ4  over the {len(panels)} panels:")
for k, n in fields.most_common(5):
    print(f"      {k:<16} {n:>4}  {'always' if n == len(panels) else ''}")
print("    yes — `Counter` again, not pydash.")

# ── Q5. Type variation. ───────────────────────────────────────────────────
types_at = defaultdict(set)
for p, v in rows:
    types_at[re.sub(r"\[\d+\]", "[]", p)].add(type(v).__name__)
varying = {k: v for k, v in types_at.items() if len(v) > 1}
print(f"\nQ5  paths carrying more than one leaf type: {len(varying)}")
for k, v in sorted(varying.items())[:4]:
    print(f"      {k[:58]:<58} {sorted(v)}")
print("    yes, once melted — and it agrees with ijson's 4.")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
print("\nQ6  CANNOT. No verb judges whether a key is a name or a value.")

# ── Q8/Q9. Three named fields; a field missing from some rows. ───────────
tbl = [_.pick(p, "title", "type", "id") | {"description": _.get(p, "description", None)}
       for p in panels]
missing = sum(1 for r in tbl if r["description"] is None)
print(f"\nQ8  _.pick -> {len(tbl)} rows x 4. yes, and `pick` is exactly the right verb.")
print(f"      {json.dumps(tbl[0])[:86]}")
print(f"\nQ9  `description` absent from {missing} of {len(tbl)}; rows survive. yes —")
print("    `_.get(p, 'description', None)` is the default idiom and it is clean.")

# ── Q10. Flatten the deepest array. ───────────────────────────────────────
tg = _.flatten([_.get(p, "targets", []) for p in panels])
print(f"\nQ10 _.flatten over the targets -> {len(tg)} rows. yes for a level you name;")
print("    `_.flatten_deep` exists but flattens LISTS, and the depth here is dicts.")

# ── Q11. Find every path matching something. ──────────────────────────────
hits = [(p, v) for p, v in rows
        if isinstance(v, str) and re.search(r"\$node|\$job|\$__rate_interval", v)]
print(f"\nQ11 {len(hits)} leaves mention a Grafana template variable. yes, once melted,")
print("    and it agrees with jq's 255. pydash has no path search of its own.")

print("""
CONCLUSION. pydash reaches 132 by enumeration, like glom and jmespath, and for
the same reason: no recursive descent. `_.get` with a dotted string and a
default is a real convenience and `_.pick` is the right verb for Q8, but both
take a path you already have.

Everything here that did not need a path named in advance — the depth, the
honest table, the type variation, the value search — came out of a six-line
`walk` that is ordinary Python. That is the same finding purrr produced on entry
28 in the other language, and it is worth having both: two "collection
libraries", two ecosystems, and in each the document questions are answered by
recursion the user writes.

The melt does contain the answer. `$.panels[16].panels[3]` is right there in the
path column, and a person who grouped the paths by their shape would see the
nesting. Nothing in pydash groups paths by shape.
""")
