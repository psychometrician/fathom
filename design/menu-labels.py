"""Is a menu label a navigable name? — 2026-08-14.

**An instrument, like `axes.py`, `coverage.py` and `find-tests.py`.** It runs
the shipped binary and modifies nothing. Running it is not a freeze event.

`design/vocabulary.md` records that `rows()` takes any label the menu prints
while `into()` takes only a field of where you stand, and that the report does
not say which is which. Three repairs are recorded there and none was measured.
Predictions first, in `design/menu-label-predictions.md`.

## What is measured

**Navigability.** For every candidate on every document, the name after `of` is
handed to `--at`, which is exactly what `into()` invokes. Success means a reader
who typed `into(<that name>)` would get somewhere; failure means the label named
a row shape they cannot navigate to.

**The width a path would cost.** Candidate A prints the path beside the label.
The paths are not in the report, so they are recovered by walking the document
for the name — the same question `rows.py` answers — and the resulting line
length is compared against `report.rs`'s `WIDTH = 92`.

**Ambiguity.** Candidate B has `into()` accept a label and jump. That is only
specifiable if a label names ONE place. Defect 34 already found 159 self-nested
names corpus-wide, so this counts how many labels resolve to more than one path.
"""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIN = ROOT / "target" / "release" / "fathom"
WIDTH = 92                      # report.rs:205
MAX_RECORDS = 20_000            # the sampling contract, for the NDJSON entries


def documents():
    for d in sorted((ROOT / "corpus").iterdir()):
        if not d.is_dir():
            continue
        for name in ("source.json", "source.json.gz", "source.jsonl"):
            if (d / name).exists():
                yield d.name, d / name
                break


def candidates(path):
    """`[(label, rows, cols, more)]` from the shipped binary."""
    r = subprocess.run([str(BIN), "structure", str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return []
    return [(c[0], c[1], c[2], c[6]) for c in json.loads(r.stdout)["candidates"]]


NAME = re.compile(r"^(?:an entry of|an item of|a node at any depth in|a node at any depth) ?(.*)$")


def name_of(label):
    """The word a reader would type into `into()`.

    The menu's labels are English — `an entry of versions`, `an item of
    contributors`, `the whole document`, `a node at any depth (13 levels)`. The
    name is what follows `of`, with any parenthetical stripped.
    """
    if label == "the whole document":
        return None                      # nothing to navigate to; it IS the root
    m = NAME.match(label)
    if not m:
        return None
    n = re.sub(r"\s*\([^)]*\)\s*$", "", m.group(1)).strip()
    return n or None


def navigable(path, name):
    """Exactly what `into(name)` invokes: `--at name`, from the root."""
    r = subprocess.run([str(BIN), "probe", str(path), "--at", name],
                       capture_output=True, text=True)
    return r.returncode == 0


def load(path):
    import gzip
    raw = gzip.open(path, "rb").read() if path.suffix == ".gz" else path.read_bytes()
    text = raw.decode("utf-8", "replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        out = []
        for ln in text.split("\n"):
            if ln.strip():
                out.append(json.loads(ln))
                if len(out) == MAX_RECORDS:
                    break
        return out


def paths_of(doc, name):
    """Every path at which `name` is a key, in `rows.py`'s language.

    A container whose keys are data is written `*`, matching how the report
    already writes the `more` line defect 34 added.
    """
    found = []

    def walk(node, parts):
        if isinstance(node, dict):
            for k, v in node.items():
                if k == name:
                    found.append(".".join(parts + [k]))
                walk(v, parts + [k])
        elif isinstance(node, list):
            for v in node:
                walk(v, parts + ["*"])

    walk(doc, [])
    # collapse paths that differ only by which key they went through, which is
    # the fold's own idea: `versions.a.deps` and `versions.b.deps` are one path.
    seen = {}
    for p in found:
        seen[p] = seen.get(p, 0) + 1
    return seen


def fold(paths):
    """Collapse literal paths to SHAPES, the fold's own idea.

    A position becomes `*` when more than one distinct segment appears there
    across paths of the same length — which is exactly `versions.a.deps` and
    `versions.b.deps` being one path and not 288.

    **A first draft rewrote every segment not in the top level as `*`**, which
    turned `versions.express.dependencies` into `versions.*.*` and collapsed
    genuinely different paths together — under-counting the ambiguity this
    measurement exists to find.
    """
    by_len = {}
    for p in paths:
        by_len.setdefault(len(p.split(".")), []).append(p.split("."))
    shapes = set()
    for segs_list in by_len.values():
        n = len(segs_list[0])
        out = []
        for i in range(n):
            distinct = {s[i] for s in segs_list}
            out.append(next(iter(distinct)) if len(distinct) == 1 else "*")
        shapes.add(".".join(out))
    return shapes


def main():
    docs = list(documents())
    print(f"{len(docs)} documents\n")
    total = nav = notnav = 0
    per_doc = []
    all_paths = []
    ambiguous = 0
    amb_docs = set()

    print("  entry                        cands  navigable  not  worst path")
    for entry, path in docs:
        cands = candidates(path)
        if not cands:
            print(f"  {entry:<28} (no candidates / unreadable)")
            continue
        doc = load(path)
        n_nav = n_not = 0
        worst = ""
        for label, rows_, cols_, more in cands:
            total += 1
            nm = name_of(label)
            if nm is None:
                n_nav += 1          # `the whole document` needs no navigation
                nav += 1
                continue
            if navigable(path, nm):
                n_nav += 1
                nav += 1
            else:
                n_not += 1
                notnav += 1
            hits = paths_of(doc, nm)
            folded = fold(hits)
            if len(folded) > 1:
                ambiguous += 1
                amb_docs.add(entry)
            if folded:
                w = max(folded, key=len)
                all_paths.append(len(w))
                if len(w) > len(worst):
                    worst = w
        per_doc.append((entry, len(cands), n_nav, n_not, worst))
        print(f"  {entry:<28} {len(cands):>5} {n_nav:>10} {n_not:>4}  "
              f"{worst[:40]}{'…' if len(worst) > 40 else ''}")

    print(f"\n  TOTAL {total} candidates: {nav} navigable, {notnav} NOT "
          f"({100*notnav/total:.0f}%)")
    docs_with = sum(1 for _, _, _, nn, _ in per_doc if nn > 0)
    print(f"  documents with at least one non-navigable label: {docs_with} of {len(per_doc)}")

    if all_paths:
        all_paths.sort()
        med = all_paths[len(all_paths) // 2]
        print(f"\n  path length behind a candidate: median {med}, max {all_paths[-1]}")
        # Candidate A: the label column is padded to 36 in the report, then
        # `NNN rows x NNN cols`. A path appended costs its own length plus a space.
        over = [e for e, _, _, _, w in per_doc if w and 36 + 22 + 1 + len(w) > WIDTH]
        print(f"  documents where a printed path would pass WIDTH={WIDTH}: "
              f"{len(over)} — {', '.join(over[:6])}{'…' if len(over) > 6 else ''}")

    print(f"\n  CANDIDATE B: labels whose name resolves to MORE THAN ONE folded path: "
          f"{ambiguous}, across {len(amb_docs)} documents")
    if amb_docs:
        print(f"    {', '.join(sorted(amb_docs)[:8])}{'…' if len(amb_docs) > 8 else ''}")


if __name__ == "__main__":
    main()
