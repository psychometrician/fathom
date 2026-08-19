"""glom — one hour of public GitHub events

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json.gz   10.6 MB gzipped, 50 MB / 37,883 records raw
  measured      2026-08-09
  run           cd corpus/04-gharchive/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 -   -                   cannot
   1 what is in here                             2   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 -   -                   cannot
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   YES                 partly
   9 a field missing from some records           4   YES                 YES

WHY THIS FILE. glom has no describer, established twice already. What 04 adds is
the case glom is genuinely built for: `path variance 76`, the highest in the
corpus, where the same value lives at different paths on different records.
`Coalesce` is the one construct in the comparison aimed straight at that.
"""
import gzip
import json
import resource
import sys
from importlib.metadata import version

from glom import Coalesce, glom

print(f"python {sys.version.split()[0]}, glom {version('glom')}")

def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3

with gzip.open("../source.json.gz", "rt") as fh:
    docs = [json.loads(line) for line in fh if line.strip()]

print(f"\n1/7. {len(docs):,} records, top-level keys: "
      f"{sorted(set().union(*[set(d) for d in docs]))}")
print("     and that is `set().union`. glom has no describer.")

# ── 9. the question glom is built for, on the file that needs it ─────────────
# A pull request's number lives at three different paths depending on the event.
SPEC = Coalesce("payload.pull_request.number", "payload.issue.number",
                "payload.number", default=None)
got = [glom(d, SPEC) for d in docs]
hits = sum(1 for g in got if g is not None)
print(f"\n9. one Coalesce over three paths found a number on {hits:,} of "
      f"{len(docs):,} records")
print("   `payload.pull_request.number` OR `payload.issue.number` OR")
print("   `payload.number`, whichever is present, in one expression.")
print("   This is the cleanest answer to path variance in either language.")
print("   It is also THREE PATHS A PERSON HAD TO KNOW — which is question 1 on")
print("   the file graded `path variance 76`, the highest in the corpus.")

print(f"\n   peak RSS: {rss():,.0f} MB")

print("""
0, 2, 3, 4, 5, 6. cannot.

  glom is the best tool here at using an answer to question 1 and contributes
  nothing to producing one. On this file that gap is at its widest: the thing it
  excels at, reconciling paths that vary, requires the enumeration of varying
  paths that nothing in the ecosystem provides.
""")
