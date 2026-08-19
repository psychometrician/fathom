"""jmespath — Grafana "Node Exporter Full", dashboard 1860

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

 ── scoring ──────────────────────────────────────────────────────────────────
  tool          jmespath (version printed at run time)
  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
  measured      2026-08-13
  run           cd corpus/27-grafana-dashboard/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             2  YES                  ONE LEVEL — keys()
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          5   -                   CANNOT
   4 always present vs sometimes                 4  YES                  yes, once named
   5 does any field change type                  3  YES                  PARTLY
   6 are any object keys data                    -   -                   CANNOT
   7 how many records                            5  YES                  132 ONLY BY ENUMERATION
   8 three named fields to a table               2  YES                  yes — multiselect
   9 a field missing from some rows              2  YES                  yes — null
  10 flatten the deepest array                   3  YES                  yes, one level at a time
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       -   -                   CANNOT
  13 needed the shape in advance?                    YES, absolutely
  14 survives the next file unchanged?               NO
  15 readable a week later?                          YES — the syntax is small
  16 lines, and how much is ceremony?                ~45

**jmespath has no recursive descent and that is a language decision, not a gap.**
There is no `..`, no `**`, no `paths()`. Every path expression names a fixed
number of levels, so the central question can only be answered by writing out
each depth you already know about and adding them up.

**It gets 132 and the way it gets there is the finding.** `length(panels) +
length(panels[].panels[])` is correct today and is a hard-coded assertion that
the nesting is exactly one level deep. The document does not say that anywhere,
and jmespath cannot ask.
"""
import json
import sys

import jmespath

print(f"jmespath {jmespath.__version__} · python {sys.version.split()[0]}")

doc = json.load(open("../source.json"))
J = lambda e: jmespath.search(e, doc)

# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  CANNOT. jmespath is a query language over a parsed value; it never")
print("    sees bytes and has no diagnostic vocabulary at all.")

# ── Q1. What is in here. ──────────────────────────────────────────────────
print(f"\nQ1  keys(@) -> {len(J('keys(@)'))} root keys.")
print(f"      {', '.join(sorted(J('keys(@)'))[:10])}, …")
print("    ONE LEVEL. `keys()` does not recurse and there is no way to map it")
print("    over an unknown structure, so level 2 needs a path you already have.")

# ── Q2. How deep. ─────────────────────────────────────────────────────────
print("\nQ2  CANNOT. Depth is not expressible: every expression names a fixed")
print("    number of levels, so measuring depth would require already knowing it.")

# ── Q7. THE CENTRAL QUESTION. ─────────────────────────────────────────────
top = J("length(panels)")
nested = J("length(panels[?panels] | [].panels[])")
print("\nQ7  THE CENTRAL QUESTION.")
print(f"      length(panels)                          -> {top}")
print(f"      length(panels[?panels] | [].panels[])   -> {nested}")
print(f"      the sum, written by hand                -> {top + nested}")
print("    132, BUT BY ENUMERATION. There is no `..`, so each depth is a separate")
print("    expression and the total is an addition I performed. The code asserts")
print("    'the nesting is exactly one level deep' and nothing checks that.")
deeper = J("length(panels[?panels] | [].panels[?panels] | [])")
print(f"    (`panels` three deep: {deeper} — I had to ASK to find out it was 0,")
print("     and on a document where it were not, the answer above is silently short.)")

# ── Q3. What is one record. ───────────────────────────────────────────────
print("\nQ3  CANNOT — nothing proposed, nothing priced. Counted once named:")
for label, expr in [("one TOP-LEVEL panel per row", "length(panels)"),
                    ("one nested panel per row", "length(panels[?panels] | [].panels[])"),
                    ("one top-level target per row", "length(panels[].targets[])"),
                    ("one nested target per row",
                     "length(panels[?panels] | [].panels[].targets[])"),
                    ("one template variable per row", "length(templating.list)")]:
    print(f"      {label:<32} {J(expr):>6,}")
print("    Note the target rows must ALSO be added by hand: 44 + 225.")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
panels = J("panels[]") + (J("panels[?panels] | [].panels[]") or [])
from collections import Counter
fields = Counter(k for p in panels for k in p)
print(f"\nQ4  over the {len(panels)} panels I assembled:")
for k, n in fields.most_common(6):
    print(f"      {k:<16} {n:>4}  {'always' if n == len(panels) else ''}")
print("    yes, once named — but the counting is Python's `Counter`, not")
print("    jmespath's. There is no group-by or frequency verb in the language.")

# ── Q5. Type variation. ───────────────────────────────────────────────────
print("\nQ5  PARTLY. `type()` exists and reports one value's type, so a scan is")
print("    possible over a list you already have:")
kinds = set(J("panels[].type(targets)") or [])
print(f"      panels[].type(targets) -> {kinds}")
print("    but there is no way to ask 'which fields vary' without enumerating the")
print("    fields first, which is question 1 that jmespath could not answer.")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
print("\nQ6  CANNOT. `keys()` returns names; nothing judges whether a name is a")
print("    field or a value, and there is no way to compare key sets across sites.")

# ── Q8/Q9. Three named fields; a field missing from some. ────────────────
tbl = J("panels[].{title: title, type: type, id: id, description: description}")
missing = sum(1 for r in tbl if r["description"] is None)
print(f"\nQ8  multiselect hash -> {len(tbl)} rows x 4. yes, and this is jmespath at")
print("    its best — the projection syntax is genuinely clean and declarative.")
print(f"      {json.dumps(tbl[0])[:86]}")
print(f"\nQ9  `description` is null in {missing} of these {len(tbl)} top-level panels;")
print("    the rows survive. yes — an absent key projects to `null` by definition,")
print("    with no default operator needed. That is the nicest Q9 in the comparison.")

# ── Q10. Flatten the deepest array. ───────────────────────────────────────
print(f"\nQ10 `panels[].targets[]` -> {J('length(panels[].targets[])')} rows, one level.")
print(f"    `panels[?panels] | [].panels[].targets[]` -> "
      f"{J('length(panels[?panels] | [].panels[].targets[])')} rows, the other.")
print("    yes, one level at a time, and 'deepest' is a word jmespath cannot use:")
print("    it can flatten a level you name and cannot find the level for you.")

# ── Q11/Q12. ──────────────────────────────────────────────────────────────
print("\nQ11 CANNOT. There is no path enumeration, no wildcard over unknown keys")
print("    at unknown depth, and no regex. A search for `$node` would have to be")
print("    told every field that might contain one.")
print("\nQ12 CANNOT, for the same reason. The flattest honest table requires")
print("    enumerating paths, which is the one thing the language will not do.")

print("""
CONCLUSION. jmespath reaches 132 and I do not think it should be scored as a
success. It got there because I wrote `length(panels)` and
`length(panels[?panels] | [].panels[])` and added them, having already learned
from other tools that there are exactly two levels. The expression is a
hard-coded assertion about a document shape that the document never states.

The proof is the line that had to be written to check: `panels` three levels
deep returns 0, and I only know that because I asked. On a dashboard that nested
one level further, the identical code returns a number that is quietly short and
looks exactly as authoritative.

Where the language is good it is very good — the multiselect hash in Q8 and
null-for-absent in Q9 are the cleanest of the eight. It is a projection language
that assumes you finished exploring before you arrived, and this document is
about the cost of that assumption.
""")
