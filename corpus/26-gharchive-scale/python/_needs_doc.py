"""The measurement four Python attempts here share: PARSE THE WHOLE DOCUMENT.

glom, jmespath, pydash and the jq binding all operate on an already-parsed
value. On a 50 MB file that is invisible; on 870 MB it is the entire result, so
it is measured once, honestly, and each attempt reports the same figure rather
than four slightly different ones.
"""
import gzip
import json
import sys
from _budget import Attempt

SRC = "../source.json.gz"


def load(limit=None):
    with gzip.open(SRC, "rt") as fh:
        return [json.loads(l) for i, l in enumerate(fh) if limit is None or i < limit]


if __name__ == "__main__":
    n = None if sys.argv[1] == "all" else int(sys.argv[1])
    docs = []
    with Attempt("load", quiet=True) as a:
        docs = load(n)
    print(f"{a.finished}\t{a.secs:.1f}\t{a.rss:.0f}\t{len(docs)}\t0\t{a.why}")
