"""`rows()` and its path language — the extract half, prototyped.

    uv run design/rows.py <file> <path>
    uv run design/rows.py corpus/01-npm-registry/source.json 'versions.*'

**Experiment, not a package**, same status as design/probe.py. Read
design/vocabulary.md first; this is the one word in it that could not be written
down without deciding a notation, and the notation is the design work.

THE LANGUAGE
------------
    .                 the document itself, one row
    name              the field called `name`
    "1.0.0"           a field whose name needs quoting
    *                 every child — object values and array elements alike
    name**            follow `name` repeatedly: the answer for a recursive document
    **                every descendant (a firehose, and rarely what anybody means)

Four requirements, each forced by a corpus file rather than chosen:

**`*` does not care whether the container is an object or an array.** npm's
`versions` is an object keyed by version string and GeoJSON's `features` is an
array, and both are semantically many-of-a-thing. A user asking for one row per
version and one row per feature is asking the same question, and JSON's
object/array distinction is an implementation detail of the document they were
handed. So `versions.*` and `features.*` are the same operation.

**The key at every `*` is data and must survive into the table.** `versions.*` on
npm without its keys throws away "1.0.0", "1.0.1", …, which is the most important
column in the file. Every `*` contributes a column. `versions.*.dependencies.*`
therefore yields version, package and range — a dependency edge, in three columns,
which no path-taking tool gives you without extra work.

**Dots inside a key are not separators.** npm's keys *are* version numbers, so
`versions.1.0.0` cannot mean four segments. This project already paid for that
mistake once: grading depth by splitting a dotted path string reported 9 levels
where there are 6, because `5.0.0-alpha.1` counted as four. Quoting is required,
not decorative.

**Recursion is one step taken again, not every step.** The first `**` meant "every
descendant" and returned 4,690 rows for a 335-comment thread, because it descended
into `author`, `text` and `id` as eagerly as into `children`. `children**` names
the step to repeat. The bare form survives for the rare case that genuinely wants
a firehose.
"""
import json
import re
import sys

SEGMENT = re.compile(r'"((?:[^"\\]|\\.)*)"|([^.]+)')


def parse(path):
    """A path string into segments. `.` alone is the empty path: the document."""
    path = path.strip()
    if path in (".", ""):
        return []
    return [m.group(1) if m.group(1) is not None else m.group(2)
            for m in SEGMENT.finditer(path)]


def children(node):
    """(key, value) for every child, an object's items or an array's positions.

    The unification is the point: a caller asking for one row per version and one
    row per feature is asking one question, and only the document distinguishes
    them.
    """
    if isinstance(node, dict):
        return list(node.items())
    if isinstance(node, list):
        return list(enumerate(node))
    return []


def match(node, segs, keys=()):
    """Yield (captured keys, value) for every match of `segs` against `node`."""
    if not segs:
        yield keys, node
        return
    head, rest = segs[0], segs[1:]
    if head == "*":
        for k, v in children(node):
            yield from match(v, rest, keys + (k,))
    elif head.endswith("**") and len(head) > 2:
        # `children**` — follow a NAMED step repeatedly. The first version made
        # `**` mean "every descendant", which on a comment thread returned 4,690
        # rows for 335 comments: it descended into `author`, `text` and `id` as
        # eagerly as into `children`. A recursive document is not a firehose, it
        # is one step taken again, and the notation has to say which step.
        name = head[:-2]
        stack = [node]
        while stack:
            n = stack.pop()
            if isinstance(n, dict) and name in n:
                for k, v in children(n[name]):
                    yield from match(v, rest, keys + (k,))
                    stack.append(v)
    elif head == "**":
        # Bare `**` is every descendant. Kept, documented as a firehose, and
        # almost never what somebody means.
        stack = list(children(node))
        while stack:
            k, v = stack.pop()
            yield from match(v, rest, keys + (k,))
            stack.extend(children(v))
    elif isinstance(node, dict) and head in node:
        yield from match(node[head], rest, keys + ())
    # a segment that does not match yields nothing, which is the honest answer


def rows(doc, path, take=None):
    """One row per match. Every `*` becomes a column; the value supplies the rest."""
    segs = parse(path)
    stars = [i for i, s in enumerate(segs) if s == "*" or s.endswith("**")]
    names = [(segs[i][:-2] or "item") if segs[i].endswith("**")
             else (segs[i - 1] if i else "item") for i in stars]
    # disambiguate repeats: versions.*.dependencies.* -> versions, dependencies
    seen = {}
    cols = []
    for n in names:
        seen[n] = seen.get(n, 0) + 1
        cols.append(n if seen[n] == 1 else f"{n}{seen[n]}")

    found = list(match(doc, segs))

    # A captured key can collide with a field of the record it came from:
    # `children**` names its key column `children`, and every comment also HAS a
    # `children` field, so the index was silently overwritten by the subtree.
    # Resolved once for the whole table rather than per row, so the columns stay
    # the same shape for every record.
    fields = {k for _, v in found if isinstance(v, dict) for k in v}
    cols = [f"{c}_key" if c in fields else c for c in cols]

    out = []
    for keys, val in found:
        row = dict(zip(cols, keys))
        if isinstance(val, dict):
            for k, v in val.items():
                if take is None or k in take:
                    row[k] = v
        else:
            row["value"] = val
        out.append(row)
    return cols, out


if __name__ == "__main__":
    path = sys.argv[2] if len(sys.argv) > 2 else "."
    with open(sys.argv[1], "rb") as fh:
        raw = fh.read()
    if raw[:2] == b"\x1f\x8b":
        import gzip
        raw = gzip.decompress(raw)
    txt = raw.decode("utf-8", errors="replace")
    try:
        doc = json.loads(txt)
    except json.JSONDecodeError:
        doc = [json.loads(l) for l in txt.split("\n") if l.strip()]

    keycols, out = rows(doc, path)
    allcols = list(dict.fromkeys([c for r in out for c in r]))
    print(f"\n  rows({sys.argv[1].split('/')[-1]!r}, {path!r})")
    print(f"  {len(out):,} rows x {len(allcols)} cols   "
          f"key columns from *: {keycols or '(none)'}")
    if out:
        print(f"  columns: {', '.join(allcols[:12])}{' …' if len(allcols) > 12 else ''}")
        first = out[0]
        print("  first row:")
        for c in allcols[:6]:
            v = repr(first.get(c))
            print(f"    {c:<18} {v[:60]}")
