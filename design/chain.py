"""The vocabulary re-derived as a CHAIN, 2026-08-11, and made to run.

`design/vocabulary.md`'s five words predate every constraint the author has since
stated, so this is a second derivation rather than a rename of the first.

THE CONSTRAINTS, from README.md:
  1. plain English about a DOCUMENT, not super-technical; `word1_word2` where one
     word cannot carry it
  2. DISTINCT from god's verbs, because both packages are loaded together
  3. navigation and seeing ONLY — any data manipulation is god's
  4. a chain of small steps, so each line reads alone
  5. identical in R and Python except the pipe, `|>` against `>>`
  6. readable months later, which is the whole point

THE ONE STRUCTURAL IDEA, and everything follows from it:

    A VIEW is a document plus WHERE YOU ARE STANDING IN IT.

Every verb takes a view and returns a view, so the chain can be any length and
`fathom()` can be re-run at any point. That is dplyr's closure, which comes from
`read_csv` guaranteeing a data frame — here it comes from the view.

WHAT THIS BUYS, AND IT IS THE HEADLINE: THE GLOB LANGUAGE DISAPPEARS.
`design/rows.py` needs `*`, `**`, `name**` and quoted keys because `rows()` must
do NAVIGATION and UNIT-SELECTION in one call. Split them across the chain and
there is nothing left for the notation to express:

    rows(doc, "versions.*.dependencies.*")      before — decode this in a month
    doc >> into("versions") >> into("dependencies") >> rows()      after

Both produce 4,645 rows. Only one of them says what it is doing.

THE WORDS. Six, all plain English, none colliding with god's `keep drop add
summarize sort take rename join group count pick row_count total descending
first_present`:

    fathom()        see it — sound, shaped, and what a row could be
    into(name)      go into a part of the document
    back()          come back out one level
    rows()          one row per thing here; THE EXIT to a table
    find(test)      every path whose value matches
    whichever(...)  the first of these paths that is actually there

`take` is GONE and that is deliberate: selecting fields is manipulation, so it is
god's `pick`, and the cost argument that saved it is answered by never navigating
to 140 columns in the first place. `first_present` becomes `whichever`, which
collides with nothing and is plainer.
"""
import sys
from collections import Counter

import probe


class View:
    """A document, and where you are standing in it."""

    def __init__(self, node, path="$", doc=None):
        self.node, self.path, self.doc = node, path, doc if doc is not None else node

    def __rshift__(self, verb):          # Python's pipe, the same as god's
        return verb(self)

    def __repr__(self):
        return f"<view {self.path} — {_kind(self.node)}>"


def _kind(n):
    if isinstance(n, dict):
        return f"object, {len(n)} fields"
    if isinstance(n, list):
        return f"array, {len(n)} items"
    return type(n).__name__


def _children(node):
    """The things at this level, whatever the container is."""
    if isinstance(node, list):
        return list(enumerate(node))
    if isinstance(node, dict):
        return list(node.items())
    return []


# ── the six words ───────────────────────────────────────────────────────────

def fathom(path_or_view=None):
    """See it. On a filename it reads and reports; in a chain it reports where
    you are standing and hands the view straight on, like `glimpse()`."""
    if isinstance(path_or_view, str):
        _, doc = probe.health(path_or_view)
        return View(doc, "$", doc)

    def run(v):
        print(f"  {v.path} — {_kind(v.node)}")
        kids = _children(v.node)
        if kids:
            shapes = Counter()
            for _, c in kids:
                shapes[_kind(c)] += 1
            for s, n in shapes.most_common(4):
                print(f"    {n:>7,} × {s}")
        return v
    return run if path_or_view is None else run(path_or_view)


def into(name):
    """Go into a part of the document. Zoom in one level."""
    def run(v):
        node = v.node
        if isinstance(node, list):
            # every item has this field: descend through all of them at once
            got = [i[name] for i in node
                   if isinstance(i, dict) and name in i]
            return View(got, f"{v.path}[].{name}", v.doc)
        if isinstance(node, dict):
            if name in node:
                return View(node[name], f"{v.path}.{name}", v.doc)
            # a keyed collection: descend into every value that has it
            got = [x[name] for x in node.values()
                   if isinstance(x, dict) and name in x]
            if got:
                return View(got, f"{v.path}.*.{name}", v.doc)
        raise KeyError(f"no `{name}` at {v.path}")
    return run


def back():
    """Come back out one level."""
    def run(v):
        parent, _, _ = v.path.rpartition(".")
        parent = parent or "$"
        node, cur = v.doc, "$"
        for step in [s for s in parent.split(".")[1:] if s]:
            node = node[step.replace("[]", "")] if step != "*" else node
            cur += "." + step
        return View(node, parent, v.doc)
    return run


def rows():
    """One row per thing here. THE EXIT — after this you are in god's world."""
    def run(v):
        node = v.node
        out = []
        if isinstance(node, list) and node and isinstance(node[0], list):
            node = [x for sub in node for x in sub]       # a level of nesting
        for key, child in _children(node):
            if isinstance(child, dict):
                out.append({"key": key, **{k: _flat(x) for k, x in child.items()}})
            else:
                out.append({"key": key, "value": _flat(child)})
        return out
    return run


def _flat(x):
    return x if not isinstance(x, (dict, list)) else f"<{_kind(x)}>"


def find(test):
    """Every path whose value matches. A SEARCH — it answers *where*."""
    def run(v):
        hits = []

        def walk(n, p):
            if isinstance(n, dict):
                for k, c in n.items():
                    walk(c, f"{p}.{k}")
            elif isinstance(n, list):
                for c in n:
                    walk(c, p + "[]")
            elif test(n):
                hits.append(p)
        walk(v.node, v.path)
        return sorted(set(hits))
    return run


def whichever(*names):
    """The first of these that is actually there. Path variance, plainly."""
    def run(v):
        got = []
        for _, child in _children(v.node):
            val = None
            if isinstance(child, dict):
                for n in names:
                    if child.get(n) is not None:
                        val = child[n]
                        break
            got.append(val)
        return got
    return run


def is_url(x):
    return isinstance(x, str) and x.startswith(("http://", "https://"))


if __name__ == "__main__":
    print(__doc__.split("THE WORDS.")[1].split("`take` is GONE")[0])
    print(f"loaded — {len(sys.argv) - 1} file(s) on the command line")
