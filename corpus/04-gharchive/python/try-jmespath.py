"""jmespath — one hour of public GitHub events

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json.gz   10.6 MB gzipped, 50 MB / 37,883 records raw
  measured      2026-08-09
  run           cd corpus/04-gharchive/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 -   -                   cannot
   1 what is in here                             2   no                  PARTLY
   2 how deep                                    -   -                   cannot
   3 what is one record                          -   -                   cannot
   4 always present vs sometimes                 3   YES                 partly
   5 does any field change type                  -   -                   cannot
   6 are any keys actually data                  -   -                   cannot
   7 how many records                            1   no                  YES
   9 a field missing from some records           3   YES                 YES

WHY THIS FILE. On 02-hn-thread the missing recursive descent made jmespath unable
to read the document at all. This file is FLAT — seven levels, no recursion — so
it is where jmespath should do best, and the comparison is only fair if the file
that suits a tool is graded as carefully as the file that breaks it.
"""
import gzip
import json
import resource
import sys
from importlib.metadata import version

import jmespath

print(f"python {sys.version.split()[0]}, jmespath {version('jmespath')}")

def rss():
    r = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return r / 1e6 if sys.platform == "darwin" else r / 1e3

with gzip.open("../source.json.gz", "rt") as fh:
    docs = [json.loads(line) for line in fh if line.strip()]

print(f"\n7. records: {len(docs):,}")
print(f"1. keys(@) on one record: "
      f"{sorted(jmespath.search('keys(@)', docs[0]))}")
print("   one level, and no expression reaches the next without naming it.")

# ── 4 / 9 — flat data is where jmespath is comfortable ───────────────────────
n_org = len(jmespath.search("[?org].id", docs))
print(f"\n4. records carrying `org`: {n_org:,} of {len(docs):,}")
print("   a filter expression, and a good one: this is jmespath at its best.")

pulls = jmespath.search("[].payload.pull_request.number | [?@]", docs)
issues = jmespath.search("[].payload.issue.number | [?@]", docs)
print(f"\n9. `payload.pull_request.number`: {len(pulls or []):,} found")
print(f"   `payload.issue.number`:         {len(issues or []):,} found")
print("   two expressions, because jmespath has no Coalesce — glom does this in")
print("   one. Both required knowing the two paths in advance.")

print(f"\n   peak RSS: {rss():,.0f} MB")

print("""
0, 2, 3, 5, 6. cannot.

  This is jmespath's best file in the corpus and the grid barely moves. Being
  flat removed the failure that made 02-hn-thread unreadable; it did not add a
  describer. Every answer above names a path that a person supplied, and the
  document graded `path variance 76` is exactly the one where knowing the paths
  in advance is the thing you do not have.
""")
