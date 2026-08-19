"""Measure every grading axis for a document, the same way every time.

`corpus/README.md` requires a measured number in every grading row that can carry
one. Doing that by hand is how `01-npm-registry` ended up with a depth of 9 that
was really 6, an `engines` that was not keys-as-data, and a 2,648-key object
nobody noticed. This script is the instrument, so that two corpus entries are
graded identically rather than similarly.

    uv run design/axes.py <file> [<file> ...]

It reuses design/probe.py rather than reimplementing the walk — one engine, for
the same reason design/implementation.md gives for one Rust core.
"""
import sys
from collections import Counter, defaultdict

import probe


def _column_sites(doc):
    """Objects holding two or more sibling arrays of scalars, all the same length.

    A record-oriented document puts one object per row and repeats the field
    names once per record. A column-oriented one puts one array per FIELD, writes
    each name once, and makes a row a POSITION shared across siblings. That is
    the whole of the definition, and it is deliberately written without reference
    to any corpus file.

    Returns {path: (width, length, consistency)} — how many parallel arrays, how
    long, and at what FRACTION of the instances of that path the property holds
    at all. It decides nothing: a reader given the three can judge for
    themselves. `corpus/README.md` records the reason to refuse the guess —
    `06-espn-qbr` sits a same-length DECOY beside the real name array, and
    nothing structural separates them.

    **CONSISTENCY WAS ADDED AFTER THE FIRST RUN AND THAT IS RECORDED RATHER THAN
    HIDDEN.** Width and length alone fired on 9 of 25 corpus documents and most
    of those were one instance of a path coinciding — `20-homebrew-formulae`
    reported `5x43` from a property true of **8.6%** of its formulae, while
    `18-openfda-events` reported a comparable site true of **91.3%** of its
    instances. The two are indistinguishable without this third number, and
    asking whether a property is TYPICAL or an OUTLIER is the same question every
    other axis in this file already asks. See `design/shape-axis-predictions.md`.
    """
    sites, seen = {}, defaultdict(lambda: [0, 0])  # path -> [hits, instances]

    def scalars(v):
        return (isinstance(v, list) and len(v) >= 2
                and not any(isinstance(i, (dict, list)) for i in v))

    def walk(node, path="$"):
        if isinstance(node, dict):
            seen[path][1] += 1
            by_len = defaultdict(list)
            for k, v in node.items():
                if scalars(v):
                    by_len[len(v)].append(k)
            if by_len:
                n, names = max(((n, ks) for n, ks in by_len.items()),
                               key=lambda t: (len(t[1]), t[0]))
                if len(names) >= 2:
                    seen[path][0] += 1
                    w, l, _ = sites.get(path, (0, 0, 0))
                    sites[path] = (max(w, len(names)), max(l, n), 0)
            for k, v in node.items():
                walk(v, f"{path}.{k}")
        elif isinstance(node, list):
            for i in node:
                walk(i, path + "[]")

    walk(doc)
    return {p: (w, l, seen[p][0] / seen[p][1]) for p, (w, l, _) in sites.items()}


def axes(path):
    h, doc = probe.health(path)
    if doc is None:
        return {"file": path.split("/")[-1], "unreadable": h.get("error", "?")}
    inst, arrs, rec, types = probe.fold_recursion(*probe.containers(doc))

    shapes = {p: [o for o in objs if o] for p, objs in inst.items()}
    shapes = {p: objs for p, objs in shapes.items() if objs}
    keyed = {p for p, objs in shapes.items() if probe.classify(objs)[0] == "data"}
    records = {p: objs for p, objs in shapes.items() if p not in keyed}

    # raggedness BY ABSENCE: a key present in some copies of a record and not others
    absent = present = 0
    for objs in records.values():
        if len(objs) < 2:
            continue
        c = Counter()
        for o in objs:
            c.update(o.keys())
        present += len(c)
        absent += sum(1 for n in c.values() if n < len(objs))

    # raggedness BY NULL: the key is always there and the value sometimes is not.
    # 02-hn-thread scores "none" on absence and is riddled with this, which is
    # why the two are counted apart.
    nulled = sum(1 for c in types.values() if "null" in c and len(c) > 1)

    # Polymorphism, real against merely optional or merely empty. Counts a field
    # that is `array[3]` here and `array[4]` there, which type alone cannot see.
    real_poly = sum(1 for c in types.values()
                    if len({t for t in probe.varies(c) if t != "null"}) > 1)

    # Heterogeneous arrays: one array holding more than one shape. Compares
    # OBJECT key-sets and ARRAY nesting alike — the first version looked only at
    # dicts, so it reported 0 on a GeoJSON file holding 65 mixed arrays.
    het = 0
    for p, lists in arrs.items():
        for items in lists:
            sigs = {frozenset(i) if isinstance(i, dict) else probe.shape(i)
                    for i in items}
            if len(sigs) > 1:
                het += 1
                break

    # path variance: one field name living under more than one container
    where = defaultdict(set)
    for tp in types:
        holder, _, field = tp.rpartition(".")
        where[field].add(holder)
    variance = sum(1 for f, hs in where.items() if len(hs) > 1)

    fields = len(where)
    paths = len(probe._paths(doc))
    rows = probe.candidates(doc, inst, arrs, rec)

    # document SHAPE: record-oriented or column-oriented. Every other axis here
    # measures how ragged a document is; corpus/README.md's `column-oriented`
    # note records that 08-open-meteo graded trivial on all of them and still
    # defeated the probe, because the question it poses is what the document is
    # shaped LIKE.
    cols = _column_sites(doc)
    # Rank by the site a reader would care about: consistent first, then long.
    widest = max(cols.values(), key=lambda t: (t[2] >= 0.5, t[1], t[0]),
                 default=(0, 0, 0))
    solid = {p: t for p, t in cols.items() if t[2] >= 0.5 and t[1] >= 4}

    return {
        "file": path.split("/")[-1],
        "bytes": h["bytes"],
        "format": h["format"],
        "depth": probe._depth(doc),
        "recursion": (max(rec.values()) + 1) if rec else 0,
        "paths": paths,
        "fields": fields,
        "explosion": round(paths / fields, 1) if fields else 0,
        "keys_as_data": len(keyed),
        "ragged_absent": f"{absent}/{present}" if present else "0/0",
        "ragged_null": nulled,
        "polymorphic": real_poly,
        "heterogeneous": het,
        "path_variance": variance,
        "row_shapes": len(rows),
        "col_sites": len(cols),
        "col_solid": len(solid),
        "col_widest": (f"{widest[0]}x{widest[1]}@{widest[2]:.0%}"
                       if widest[0] else "-"),
    }


COLS = ["file", "bytes", "format", "depth", "recursion", "paths", "fields",
        "explosion", "keys_as_data", "ragged_absent", "ragged_null",
        "polymorphic", "heterogeneous", "path_variance", "row_shapes",
        "col_sites", "col_solid", "col_widest"]

if __name__ == "__main__":
    rows = [axes(p) for p in sys.argv[1:]]
    w = {c: max(len(c), *(len(str(r.get(c, "-"))) for r in rows)) for c in COLS}
    print("  ".join(c.ljust(w[c]) for c in COLS))
    print("  ".join("-" * w[c] for c in COLS))
    for r in rows:
        print("  ".join(str(r.get(c, "-")).ljust(w[c]) for c in COLS))
