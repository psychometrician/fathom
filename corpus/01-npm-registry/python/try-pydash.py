"""pydash — npm registry metadata for `express`

Scoring header follows ../r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   804,956 bytes, 288 versions, 25,044 paths
  measured      2026-08-09
  run           cd corpus/01-npm-registry/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   no                  WRONG
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 yes
  13 needed the shape in advance?                    YES, for everything

WHAT THIS FILE IS FOR. pydash is the lodash port, and it does have one function
that walks a whole document — `pydash.objects.to_paths` style flattening via
`pydash.helpers`. It is the closest thing in the Python set to rrapply's
`how="melt"`, so it is the fairest Python comparison for R's list-walkers.
"""
import json
import sys
from importlib.metadata import version

import pydash

print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")

doc = json.load(open("../source.json"))

# ── 1. what is in here ───────────────────────────────────────────────────────
# `pydash.omit_by` and friends operate one level at a time. The one whole-document
# walk available is a manual recursion over `pydash.get` paths, which is the same
# thing rrapply does and lands in the same place for the same reason.
def leaf_names(node, acc):
    if isinstance(node, dict):
        for k, v in node.items():
            acc.add(k)
            leaf_names(v, acc)
    elif isinstance(node, list):
        for v in node:
            leaf_names(v, acc)
    return acc

names = leaf_names(doc, set())
print(f"\n1. distinct key names anywhere: {len(names):,}")
print(f"   jq says 3,100. rrapply says 3,112. ijson says 2,852. The true answer")
print(f"   is about 40, and every tool that walks without deciding which keys are")
print(f"   data lands in the same wrong neighbourhood.")
print(f"   pydash contributed nothing to that walk — it is nine lines of plain")
print(f"   recursion, because pydash has no recursive descent either.")

# ── 7 ────────────────────────────────────────────────────────────────────────
print(f"\n7. versions: {len(pydash.get(doc, 'versions'))}")

# ── what pydash IS good at ───────────────────────────────────────────────────
# `pydash.get` takes a dotted path with a default, which is question 9's shape.
print("\n(9, previewed) pydash.get with a default, and the dotted-key question:")
print(f"     'versions.4.17.1.dist.tarball' -> "
      f"{str(pydash.get(doc, 'versions.4.17.1.dist.tarball'))[:52]}")
print(f"     'versions.4.17.1.nonesuch'     -> "
      f"{pydash.get(doc, 'versions.4.17.1.nonesuch', 'MISSING')}")
# Measured rather than asserted: does pydash resolve a dotted KEY, or does it
# split on every dot and fail? The answer above decides which sentence in the
# closing note is true, so it is printed rather than assumed.
print(f"     direct dict access, for comparison -> "
      f"{str(doc['versions']['4.17.1']['dist']['tarball'])[:52]}")

print("""
2, 3, 4, 5, 6. cannot.

  pydash's dotted-path interface has the same defect ijson's does and the same
  one this project shipped on day one: `versions.4.17.1.dist` is ambiguous,
  because the keys ARE dotted version numbers.

  MEASURED, not assumed, and the first draft of this note guessed wrong. pydash
  does NOT resolve the dotted key by trying longer prefixes. It splits on every
  dot, looks for a key `4` under `versions`, finds nothing, and returns **None**
  — the same value it returns for a field that is genuinely absent. The tarball
  is right there and plain dict access retrieves it.

  So the most popular Python path language cannot address 288 of this document's
  records at all, and says so by returning the same answer it gives for missing
  data. `design/rows.py` requires quoting for exactly this reason; the note there
  calls it "required, not decorative", and this is the measurement behind it.

  Everything else is the usual answer. It is a fetching library, and all five
  refusals reduce to question 3: nothing here knows what a record is.
""")
