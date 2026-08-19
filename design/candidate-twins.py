"""DEFECT 39 — how many `an entry of <name>` candidates hide a second path?

**DEFECT 39 WAS REPAIRED 2026-08-18 at `73e08ca6…`, both facets.** This script
describes the code as it was BEFORE that, and it is kept as the repair's
evidence rather than as a live detector: facet 1's names are now exactly the
ones that print a modifier, and facet 2's list is exactly the sixteen candidates
that were being suppressed and now appear. **What it prints is what the repair
had to account for, and it should be read that way.**

`candidates()` runs TWO loops that both de-duplicate on the bare name and both
keep the FIRST path in sorted order, dropping the rest silently:

    seen = set()
    for p, objs in sorted(inst.items()):     # keyed collections -> "an entry of"
        ...
        if name in seen: continue
        seen.add(name)
        price(vals, f"an entry of {name}")   # <- no `more` argument, ever

    for p, lists in sorted(arrs.items()):    # arrays -> "an item of"
        ...
        if name in seen: continue
        seen.add(name)
        price(items, f"an item of {name}", more)   # <- defect 34's repair

**Defect 34 was measured, and repaired, on the ARRAY loop only.** Its survey
counted 159 self-nested names and 34 where the dropped path was bigger — all of
them arrays. The keyed loop above it has the same silent drop and never got the
modifier, and the defect-34 comment sits BETWEEN the two loops describing only
the one below.

Two facets are measured here:

  1. WITHIN the keyed loop — a name at two or more keyed sites. The printed
     count is one path's; the reader reads it as the word's.
  2. ACROSS the loops — `seen` is shared, so a name the keyed loop claims makes
     the array loop skip it entirely. No candidate is offered for the array at
     all, and the modifier never runs because it lives in the skipped branch.

Imports `probe.py` and does not modify it. An instrument, not a freeze event —
same standing as `coverage.py` and `axes.py`.

    uv run design/candidate-twins.py
"""
import os
import sys
from collections import Counter

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe  # FROZEN at 73e08ca6…. Imported and never modified; see CLAUDE.md.

CAP = 200 * 2**20          # `candidates.py`'s cap, for the same reason
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "corpus")

# **THE SOURCE FILE IS RESOLVED, NOT GLOBBED, and this was a defect.** This
# script globbed `*/source.json` until 2026-08-19, so it never saw
# `04-gharchive`'s gzip or `12-agent-trace`'s NDJSON and surveyed 27 of the 29
# readable documents. It mattered: the figure it printed became the comment in
# `probe.py` and `price.rs` saying `10 modifiers against 50`, and the measured
# number is **51** — `04-gharchive` contributes exactly the missing one.
#
# The order matters: `04-gharchive` and `26-gharchive-scale` hold BOTH a `.gz`
# and a `.jsonl`, and the gzip is the committed artifact.
NAMES = ("source.json", "source.json.gz", "source.jsonl")


def sources():
    for entry in sorted(os.listdir(ROOT)):
        d = os.path.join(ROOT, entry)
        if not os.path.isdir(d):
            continue
        for n in NAMES:
            p = os.path.join(d, n)
            if os.path.exists(p):
                yield entry, p
                break


def keyed_names(inst):
    """Every (name -> [(path, n_values)]) the keyed loop would consider, in its
    own order. The loop takes paths[0] and drops the rest."""
    by_name = {}
    for p, objs in sorted(inst.items()):
        if p == "$" or probe.classify(objs)[0] != "data":
            continue
        name = p.split(".")[-1]
        if name == "<key>":
            name = probe._above_marker(p)
        if name == "$":
            continue
        vals = [v for o in objs for v in o.values()]
        if vals:
            by_name.setdefault(name, []).append((p, len(vals)))
    return by_name


def suppressed_arrays(arrs, claimed):
    """Array candidates the keyed loop's `seen` entries make unreachable."""
    out, free = [], set(claimed)
    for p, lists in sorted(arrs.items()):
        stem = p.rstrip("[]")
        name = stem.split(".")[-1]
        if name == "<key>":
            name = probe._above_marker(stem)
        if name == "$" or name not in free:
            continue
        items = [i for l in lists for i in l]
        if items and all(isinstance(i, dict) for i in items):
            out.append((name, p, len(items)))
            free.discard(name)
    return out


def main():
    twins, cross, skipped = [], [], []
    n_names = 0

    for entry, src in sources():
        if os.path.getsize(src) > CAP:
            skipped.append((entry, "over the 200 MB cap"))
            continue
        try:
            h, doc = probe.health(src)
            if h["format"] is None:
                skipped.append((entry, "no format the probe recognises"))
                continue
            inst, arrs, types = probe.containers(doc)
            inst, arrs, rec, types = probe.fold_recursion(inst, arrs, types)
        except Exception as e:                               # noqa: BLE001
            skipped.append((entry, f"unreadable: {type(e).__name__}"))
            continue

        by_name = keyed_names(inst)
        n_names += len(by_name)
        for name, paths in sorted(by_name.items()):
            if len(paths) < 2:
                continue
            kept, kept_n = paths[0]
            dropped = paths[1:]
            twins.append((entry, name, kept, kept_n,
                          sum(n for _, n in dropped), len(dropped),
                          max(n for _, n in dropped) > kept_n))
        for name, p, n in suppressed_arrays(arrs, set(by_name)):
            cross.append((entry, name, p, n))

    print("FACET 1 — a keyed candidate name standing at more than one path\n")
    print(f"  {'entry':<26} {'name':<24} {'printed':>9} {'dropped':>9}  {'':>6}")
    for entry, name, kept, kept_n, drop_n, ndrop, bigger in twins:
        print(f"  {entry:<26} {name:<24} {kept_n:>9,} {drop_n:>9,}  "
              f"{'BIGGER' if bigger else ''}")

    per_doc = Counter(t[0] for t in twins)
    n_big = sum(1 for t in twins if t[6])
    print()
    print(f"  {n_names} keyed candidate names over the corpus")
    print(f"  {len(twins)} hide a second path, across {len(per_doc)} documents")
    print(f"  {n_big} where the DROPPED path is bigger than the one printed")

    print("\nFACET 2 — an array candidate the shared `seen` set makes unreachable\n")
    for entry, name, p, n in cross:
        print(f"  {entry:<26} {name:<24} {n:>9,} items never offered")
    per_doc2 = Counter(c[0] for c in cross)
    print()
    print(f"  {len(cross)} suppressed, across {len(per_doc2)} document"
          f"{'s' if len(per_doc2) != 1 else ''}")

    if skipped:
        print()
        for entry, why in skipped:
            print(f"  not run: {entry} — {why}")


if __name__ == "__main__":
    main()
