"""Defect 26's third rule: is a packed list detectable from its SIBLINGS?

    uv run design/packed-lists.py            # every document, all three rules
    uv run design/packed-lists.py --values   # with the values, to judge by eye

**Defect 26 is the only open defect nothing has touched**, and the only
unmeasured thing in it is the rule its own entry proposed and stopped at:

> `types` proves the convention with interior delimiters; `ids` and `sources`
> are siblings on the same records using the same character. **Sibling fields
> sharing a wrapping character is the evidence, and no single field carries
> it.**

`FINDINGS.md` 2026-08-10 scored the other two rules over the 25 documents there
were then — strict is exact and misses two of three, relaxed is complete and
cannot tell `,nc,` from `:hash:`. This scores all three over 29, so the numbers
are comparable and the new one is on the same footing.

**An instrument**: it imports `probe.py` for the walk and modifies nothing.
"""

import os
import re
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, HERE)
import probe                                            # noqa: E402

WRAP = re.compile(r"^([^A-Za-z0-9\s])(.*)\1$", re.S)
MIN_LEN = 3                                             # `,a,` is the shortest real one


def documents():
    d = os.path.join(ROOT, "corpus")
    for e in sorted(os.listdir(d)):
        if not os.path.isdir(os.path.join(d, e)):
            continue
        for n in ("source.json", "source.json.gz", "source.jsonl"):
            p = os.path.join(d, e, n)
            if os.path.isfile(p):
                yield e, p
                break


def strings(doc):
    """(folded path, value) for every string, via the probe's own walk."""
    out = []

    def go(node, path):
        k = probe_kind(doc, node)
        if k == "object":
            for key, val in probe_members(doc, node):
                go(val, f"{path}.{key}")
        elif k == "array":
            for el in probe_elements(doc, node):
                go(el, f"{path}[]")
        elif isinstance(node, str):
            out.append((path, node))

    go(doc, "$")
    return out


# `probe.py` hands back plain Python objects, so the three helpers are trivial —
# they exist so the walk above reads the same as the probe's own.
def probe_kind(_d, n):
    return "object" if isinstance(n, dict) else "array" if isinstance(n, list) else "leaf"


def probe_members(_d, n):
    return n.items()


def probe_elements(_d, n):
    return n


def wrapped(v):
    """The wrapping character, if the value is wrapped in one at both ends."""
    if not isinstance(v, str) or len(v) < MIN_LEN:
        return None
    m = WRAP.match(v)
    return m.group(1) if m else None


# The fold, borrowed rather than rewritten. `design/coverage.py` already keeps
# the probe's keys-as-data fixed point — and `CLAUDE.md` records what it cost the
# last time two files kept their own copy of it. Without folding, mdn's vendor
# prefixes arrive as 1,826 concrete paths where the fold sees a handful, and the
# relaxed column stops being comparable to the 2026-08-10 numbers.
import importlib.util as _ilu                          # noqa: E402
_spec = _ilu.spec_from_file_location("cov", os.path.join(HERE, "coverage.py"))
cov = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(cov)


def folded_paths(doc):
    """concrete path -> folded path, exactly as the probe folds."""
    big = cov.fold_sites(doc)
    canon = cov.recursion_fold(doc, big)
    return big, canon


def fold_one(path, big, canon):
    """Collapse a concrete path through the probe's keys-as-data verdict."""
    out, cur = [], "$"
    for seg in path.split(".")[1:]:
        bare = seg[:-2] if seg.endswith("[]") else seg
        nxt = f"{cur}.{bare}" if cur != "$" else f"$.{bare}"
        out.append("<key>" if cur in big else bare)
        cur = nxt + ("[]" if seg.endswith("[]") else "")
        if seg.endswith("[]"):
            out[-1] += "[]"
    p = "$." + ".".join(out) if out else "$"
    head, _, tail = p.rpartition(".")
    return f"{canon.get(head, head)}.{tail}" if head else p


def classify(doc):
    """Per folded path: the wrapping char it uses, and how often it repeats.

    A path qualifies for a rule only if EVERY value there agrees, because one
    wrapped value among thousands is a coincidence and not a convention.
    """
    chars, inner = defaultdict(set), defaultdict(int)
    counts = defaultdict(int)
    big, canon = folded_paths(doc)
    for raw, v in strings(doc):
        path = fold_one(raw, big, canon)
        counts[path] += 1
        c = wrapped(v)
        chars[path].add(c)
        if c:
            inner[path] = max(inner[path], v.count(c))
    out = {}
    for path, cs in chars.items():
        if len(cs) == 1 and (c := next(iter(cs))) is not None:
            out[path] = (c, inner[path], counts[path])
    return out


def parent(p):
    return p.rsplit(".", 1)[0] if "." in p else "$"


def rules(found):
    """strict / relaxed / sibling, as three sets of paths."""
    relaxed = set(found)
    strict = {p for p, (_c, rep, _n) in found.items() if rep > 2}
    by_parent = defaultdict(list)
    for p, (c, _rep, _n) in found.items():
        by_parent[(parent(p), c)].append(p)
    sibling = {p for group in by_parent.values() if len(group) > 1 for p in group}
    return strict, relaxed, sibling


def main(argv):
    show = "--values" in argv
    print("\n  DEFECT 26 — three rules for a list packed into a string\n")
    print(f"  {'entry':<26} {'strict':>7} {'relaxed':>8} {'SIBLING':>8}")
    tot = [0, 0, 0]
    hits = {"strict": [], "relaxed": [], "sibling": []}
    for name, path in documents():
        try:
            _h, doc = probe.health(path)
        except Exception as e:
            print(f"  {name:<26} unreadable: {str(e)[:40]}")
            continue
        if doc is None:
            continue
        found = classify(doc)
        s, r, sib = rules(found)
        for i, v in enumerate((s, r, sib)):
            tot[i] += len(v)
        for key, v in (("strict", s), ("relaxed", r), ("sibling", sib)):
            hits[key] += [(name, p, found[p]) for p in sorted(v)]
        if s or r or sib:
            print(f"  {name:<26} {len(s):>7} {len(r):>8} {len(sib):>8}")

    print(f"\n  {'TOTAL':<26} {tot[0]:>7} {tot[1]:>8} {tot[2]:>8}")
    print("\n  WHAT THE SIBLING RULE MATCHED\n")
    for name, p, (c, rep, n) in hits["sibling"]:
        print(f"    {name:<24} {p:<52} wrap={c!r} inner={rep} n={n:,}")
    print("\n  MATCHED BY RELAXED BUT NOT BY SIBLING — the ones it rejects\n")
    sibset = {(n, p) for n, p, _ in hits["sibling"]}
    for name, p, (c, rep, n) in hits["relaxed"]:
        if (name, p) not in sibset:
            print(f"    {name:<24} {p:<52} wrap={c!r} inner={rep} n={n:,}")


if __name__ == "__main__":
    main(sys.argv[1:])
