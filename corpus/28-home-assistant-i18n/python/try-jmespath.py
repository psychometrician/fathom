"""jmespath — Home Assistant frontend, the English translation catalogue

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

── scoring ──────────────────────────────────────────────────────────────────
 tool          jmespath (version printed at run time)
 file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
 measured      2026-08-12
 run           cd corpus/28-home-assistant-i18n/python && uv run try-jmespath.py

 question                                    lines  shape known first?  worked
  0 is this sound                               1   -                   CANNOT
  1 what is in here                             3   NO                  ONE LEVEL — keys(@)
  2 how deep                                    1   -                   CANNOT
  3 what is one record                          2   -                   CANNOT
  4 always present vs sometimes                 -   -                   CANNOT
  5 does any field change type                  4  YES                  only where you look
  6 are any object keys data                    -   -                   CANNOT
  7 how many records                            3  YES                  only what you name
  8 three named fields to a table               4  YES                  yes
  9 a field missing from some rows              3  YES                  yes — null, not an error
 10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
 11 find every path matching something          1   -                   CANNOT
 12 flattest honest table                       1   -                   CANNOT
 13 needed the shape in advance?                    YES for everything it did
 14 survives the next file unchanged?               only if the paths do
 15 readable a week later?                          YES — the paths are plain
 16 lines, and how much is ceremony?                ~55

**jmespath has no recursive descent at all** — no `..`, no `paths`, no way to ask
about a level you have not named. On a document that is nothing but levels, that
is close to total. It answers the three extraction questions and declines nine.
"""
import json
import sys

import jmespath

print(f"jmespath {jmespath.__version__} · python {sys.version.split()[0]}")
doc = json.load(open("../source.json"))


def q(expr):
    return jmespath.search(expr, doc)


print("\nQ0  json.load parsed and said nothing. CANNOT.")

print(f"\nQ1  keys(@) -> {len(q('keys(@)'))} top-level keys: {', '.join(q('keys(@)'))}")
print("    ONE LEVEL. `keys()` does not recurse and there is no operator that")
print("    does, so every level below has to be named to be seen.")

print("\nQ2  CANNOT. No depth notion, no descent.")
print("\nQ3  CANNOT. jmespath names no record shapes and prices none.")
print("\nQ4  CANNOT. No population of records to compare.")

kinds = {k: type(v).__name__ for k, v in q("ui").items()}
print(f"\nQ5  the types under `ui`, which I had to name: "
      f"{sorted(set(kinds.values()))}")
print(f"    {sum(1 for v in kinds.values() if v == 'str')} strings and "
      f"{sum(1 for v in kinds.values() if v == 'dict')} objects side by side.")
print("    only where you look, and looking is a path you wrote.")

print("\nQ6  CANNOT.")

print(f"\nQ7  only what you name:")
print(f"      length(ui)                 {q('length(ui)')}")
print(f"      length(ui.panel)           {q('length(ui.panel)')}")

print(f"\nQ8  {q('[ui.common.and, ui.common.loading, ui.panel.profile.logout]')}")
print("    yes — a multiselect list, and it reads well.")

print(f"\nQ9  a key that is not there -> {q('ui.panel.profile.nope')}")
print("    null rather than an error, so the row survives. yes.")

print("\nQ10 zero arrays in this document. NOTHING TO FLATTEN.")
print("\nQ11 CANNOT. There is no way to search over paths you have not named.")
print("\nQ12 CANNOT. The honest table is 8,518 rows keyed by path and jmespath")
print("    cannot enumerate a path it was not given.")

print("""
CONCLUSION. jmespath is the weakest of the fourteen on this document and the
reason is structural rather than incidental: it has no recursive descent. jq has
`..` and `paths`, duckdb has `json_tree`, ijson has its prefix, polars has the
schema. jmespath has the path you typed.

That makes it the cleanest illustration in the corpus of the distinction this
project is built on. On a document where you already know the shape it is
pleasant — Q8 is one line and reads perfectly a week later. On a document you
have never seen it cannot start.
""")
