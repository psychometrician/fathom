"""glom — npm registry metadata for `express`

Scoring header follows ../r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   804,956 bytes, 288 versions, 25,044 paths
  measured      2026-08-09
  run           cd corpus/01-npm-registry/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   1 what is in here                             2   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 yes
  13 needed the shape in advance?                    YES, for everything
  16 lines, and how much is ceremony?                see notes below

WHAT THIS FILE IS FOR. glom is the Python library most often recommended for
"handling nested JSON", so a reader could reasonably expect it to answer these.
It has exactly one describer, `glom.Inspect`, and the point of this file is to
record precisely what that does and does not do — "cannot" with a reason is the
most useful cell in the grid, and an empty one is the least.
"""
import json
import sys
from importlib.metadata import version

from glom import Coalesce, glom

print(f"python {sys.version.split()[0]}, glom {version('glom')}")

doc = json.load(open("../source.json"))

# ── 1. what is in here ───────────────────────────────────────────────────────
# glom has no schema describer. `glom.Inspect` prints one value mid-spec for
# debugging; it does not enumerate structure. The best available answer is the
# top-level keys, which is `dict.keys()` and owes nothing to glom.
print(f"\n1. top-level keys: {len(doc)} — {', '.join(sorted(doc))}")
print("   and that is `dict.keys()`. glom adds nothing here: it is a library for")
print("   FETCHING a path you can already name, not for finding out which paths")
print("   exist. Its own docs describe it as 'restructuring data', which presumes")
print("   you know the structure.")

# ── 7. how many records ──────────────────────────────────────────────────────
print(f"\n7. versions: {glom(doc, 'versions')and len(glom(doc, 'versions'))}   "
      f"(only because a person named `versions`)")

# ── what glom IS good at, recorded so the comparison is fair ─────────────────
# Question 9 territory: a field missing from some records, kept rather than
# dropped. This is glom's real strength and it should be on the record.
tarballs = glom(doc, ("versions", lambda v: list(v.values())[:5],
                      [Coalesce("dist.tarball", default=None)]))
print(f"\n(9, previewed) five tarballs via Coalesce, missing ones kept as None:")
for t in tarballs:
    print(f"     {str(t)[:70]}")

print("""
2, 3, 4, 5, 6. cannot, and the reason is one sentence.

  glom is a path language with no describer. Every one of these questions asks
  what is in a document you have not seen, and glom's entire interface takes a
  path you already know as its input. `Inspect` shows you one value in flight;
  it does not enumerate.

  This is not a criticism of glom, which is good at the thing it does — see the
  Coalesce line above, which answers question 9 in one expression and is the
  cleanest answer to it in either language so far. It is a statement about which
  half of this project's questions the Python ecosystem has tools for.
""")
