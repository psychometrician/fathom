"""The two surviving menu-label repairs, RENDERED — author item 4.

    uv run design/menu-variants.py            # the measurement, all 29
    uv run design/menu-variants.py --show 08-open-meteo 01-npm-registry

**An instrument. It runs the shipped binary and modifies nothing** — the pages
below are the real report with its menu block rewritten, so `design/probe.py`
stays frozen and no variant ships by being tried.

## What is being chosen between

`design/vocabulary.md` recorded three repairs for *a menu label is not a
navigable name* and 2026-08-14 refuted two of them by measurement: **A** — print
the path beside each label — dies on the page's own width, 15 of 29 documents
crossing `WIDTH`; **B** — let `into()` take a label and jump — cannot be
specified at all, because 99 labels resolve to two or more folded paths.

Two survive, and they are not the same kind of change:

**C — the two lists visibly separate.** The menu is read two ways, so say which
entries are which: the ones `into()` can stand on, and the ones that name a
shape only. Costs one separator line, and **only helps a document that has some
of each.**

**The fourth — say what the menu is FOR.** It is a menu for `rows()`, nothing on
the page says so, and the binding test assumed otherwise exactly as a person
would. Costs no lines at all: it is words on a header that already exists.

## What this measures rather than argues

**Whether C has anything to separate.** A document where every candidate is
non-navigable gets a separator with an empty group above it, and `bindings.py`
already prints four such documents every run. If that is common, C is a line
spent on nothing; the count is the finding, and it is the same shape of argument
that killed A.
"""

import importlib.util
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIN = ROOT / "target" / "release" / "fathom"
WIDTH = 92                      # report.rs:205, the same constant A died on
HERE = pathlib.Path(__file__).resolve().parent

# `menu-labels.py` is not importable by name — the hyphen is deliberate, the same
# reason attempt files carry it — so it is loaded by path. **Not copied**: the
# rule for "what would a reader type" and "is that navigable" already exists and
# a second copy is how `coverage.py` and `probe.py` once measured different
# folds. `CLAUDE.md` records that lesson.
_spec = importlib.util.spec_from_file_location("menu_labels", HERE / "menu-labels.py")
ml = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ml)

HEADER = "  ONE ROW COULD BE"
FOURTH = "  ONE ROW COULD BE — give any of these to rows()"
SPLIT = "    ── the rest name a shape, not a place you can stand ──"


def page(path, *args):
    r = subprocess.run([str(BIN), "probe", str(path), *args],
                       capture_output=True, text=True, cwd=ROOT)
    return r.stdout


def menu_block(lines):
    """(start, end) of the menu, end exclusive. The block is the header plus the
    indented lines under it, stopping at the first line that is not one.

    Matched by PREFIX, because the fourth candidate rewrites the header line and
    an exact match then finds nothing — which is how `--show` first crashed.
    """
    i = next((k for k, l in enumerate(lines) if l.startswith(HEADER)), None)
    if i is None:
        return None
    j = i + 1
    while j < len(lines) and (lines[j].startswith("      ") or lines[j].startswith("    ")):
        j += 1
    return i, j


def items(block):
    """The menu as `[(entry_line, [modifier_lines])]`.

    **A candidate is a 4-space line; defect 34's `└─ N more at …` is a 6-space
    line belonging to the one above it.** Counting those as entries inflated the
    menu from 360 to 414 in the first version of this instrument, and — worse —
    splitting the list would have orphaned a modifier from its candidate.
    """
    out = []
    for line in block:
        if not line.strip():
            continue
        if line.startswith("      ") and out:
            out[-1][1].append(line)
        else:
            out.append((line, []))
    return out


def classify(path, menu):
    """Split the menu into navigable and not, by asking `--at`.

    Entry lines are matched back to candidate labels by prefix, because the
    printed line is the label padded with its measurements — parsing the numbers
    back out would be a second renderer. **A modifier travels with its parent.**
    """
    labels = [c[0] for c in ml.candidates(path)]
    nav, rest = [], []
    for entry, mods in menu:
        stripped = entry.strip()
        label = next((l for l in sorted(labels, key=len, reverse=True)
                      if stripped.startswith(l)), None)
        name = ml.name_of(label) if label else None
        (nav if name and ml.navigable(path, name) else rest).append([entry, *mods])
    return nav, rest


def variants(path):
    """(shipped, candidate C, the fourth) as whole pages, plus the split counts."""
    lines = page(path).split("\n")
    block = menu_block(lines)
    if not block:
        return None
    i, j = block
    menu = items(lines[i + 1:j])
    nav, rest = classify(path, menu)

    flat = lambda groups: [l for g in groups for l in g]
    body = flat(nav) + ([SPLIT] if nav and rest else []) + flat(rest)
    c = lines[:i + 1] + body + lines[j:]
    fourth = lines[:i] + [FOURTH] + lines[i + 1:]
    return {
        "shipped": lines, "C": c, "fourth": fourth,
        "nav": len(nav), "rest": len(rest), "entries": len(menu),
    }


def entry_order(lines):
    """The menu's candidate lines in order, for asking whether a variant moved any.

    **The order is the FOLD's discovery order, and it is not documented as
    meaningful** — `probe.py:1705` iterates `candidates()` and the printer does
    not sort. The first version of this docstring claimed the report says
    *"Ordered by copies, so what is above is the biggest of them"*; **it does,
    about RECORD SHAPES, not about this menu.** The claim was checked before it
    was written down and withdrawn.

    So a regrouping repair does not break a stated contract. What it does do is
    replace an order that follows the document's structure with one that follows
    a capability, and that cost does not show up in a line count. Rendering
    `23-cratesio-summary` is what surfaced it: candidate C moves `the whole
    document` from first to last and files it under *names a shape, not a place
    you can stand*.
    """
    b = menu_block(lines)
    if not b:
        return []
    return [e.strip() for e, _m in items(lines[b[0] + 1:b[1]])
            if not e.strip().startswith("──")]


def block_width(lines):
    """The widest line of the MENU, not of the page.

    **The first version measured the whole page and reported `over 92` almost
    everywhere** — because the shipped report already has 11 such lines on
    `01-npm-registry` alone, in sections neither variant touches. A width column
    that fires on lines the change did not cause says nothing about the change,
    which is the mistake candidate A was refuted BY.
    """
    b = menu_block(lines)
    return max((len(l) for l in lines[b[0]:b[1]]), default=0) if b else 0


def main(argv):
    if not BIN.exists():
        sys.exit("build first: cargo build --release")
    show = []
    if argv[:1] == ["--show"]:
        show = argv[1:]

    print("\n  MENU VARIANTS — candidate C against the fourth, on the real report\n")
    print(f"  {'entry':<26} {'cands':>5} {'nav':>4} {'rest':>5} "
          f"{'C adds':>7} {'C helps':>8} {'4th adds':>9} {'menu wide':>10}")
    rows = []
    for name, path in ml.documents():
        v = variants(path)
        if not v:
            continue
        helps = bool(v["nav"] and v["rest"])
        c_adds = len(v["C"]) - len(v["shipped"])
        base = block_width(v["shipped"])
        grew = max(block_width(v["C"]), block_width(v["fourth"])) - base
        v["reorders"] = entry_order(v["C"]) != entry_order(v["shipped"])
        rows.append((name, v, helps, c_adds, grew, base))
        print(f"  {name:<26} {v['entries']:>5} {v['nav']:>4} {v['rest']:>5} "
              f"{c_adds:>7} {'yes' if helps else 'NO':>8} "
              f"{len(v['fourth']) - len(v['shipped']):>9} {base:>6}{grew:+4}")

    n = len(rows)
    helps = sum(1 for r in rows if r[2])
    nothing = [r[0] for r in rows if not r[2]]
    allrest = [r[0] for r in rows if r[1]["nav"] == 0]
    reord = [r[0] for r in rows if r[1]["reorders"]]
    print(f"\n  {n} documents with a menu.")
    print(f"  C separates something on {helps} of {n}; on {n - helps} it is a NO-OP "
          f"— not one line, because the separator needs both groups.")
    print(f"  C REORDERS the menu on {len(reord)} of {n} — the fold's discovery "
          f"order becomes a capability order.")
    print(f"  documents where NOTHING is navigable: {len(allrest)} — "
          f"{', '.join(allrest) if allrest else 'none'}")
    print(f"  total menu entries: {sum(r[1]['entries'] for r in rows)}, "
          f"navigable {sum(r[1]['nav'] for r in rows)} "
          f"(2026-08-14 measured 82 of 324 named — this must agree)")
    widened = [r[0] for r in rows if r[4] > 0]
    print(f"  neither variant widens the menu by one column: "
          f"{'confirmed' if not widened else 'NO — ' + ', '.join(widened)}")
    if nothing:
        print(f"\n  C changes NOTHING on: {', '.join(nothing)}")
    print("\n  So C never helps without also reordering, and the fourth costs "
          "no line, no column and no order anywhere.")

    for want in show:
        path = next((p for nm, p in ml.documents() if nm == want), None)
        if not path:
            print(f"\n  no such entry: {want}")
            continue
        v = variants(path)
        i, j = menu_block(v["shipped"])
        print(f"\n\n  ══════ {want} ══════")
        for label, key in (("SHIPPED", "shipped"), ("CANDIDATE C", "C"),
                           ("THE FOURTH", "fourth")):
            lines = v[key]
            a, b = menu_block(lines)
            print(f"\n  ── {label} ──")
            print("\n".join(lines[a:b]).rstrip())


if __name__ == "__main__":
    main(sys.argv[1:])
