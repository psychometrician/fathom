"""THE ARRAY LOOP'S twin rule and name claiming — the question defect 39 left open.

Defect 39 repaired the KEYED loop and deliberately did not touch the array loop
below it. Two things in that loop are worth measuring before anything is decided,
and they are NOT the same question:

  A. THE TWIN RULE. `by_name` records an array site only when its items are ALL
     DICTS — rule A, the rule defect 39 rejected for the keyed loop as an
     artifact of plumbing. Rule B is *any array site of that name*.

     **The array loop is NOT the keyed loop and the argument does not carry.**
     The keyed loop emits candidates for scalar-valued sites too, so defect 39's
     widening related scalars to scalars — 305 relationships, zero mixed. The
     array loop only ever EMITS a record-valued candidate, so every twin rule B
     adds that is not itself record-valued is a MIXED relationship: `an item of
     X — 84 rows` gaining `and 943 more` where those 943 are strings, not rows
     of that table. That is the branch defect 39 recorded as unreachable and
     untested. Here it may be the only branch there is, which is why this is
     measured rather than mirrored.

  B. NAME CLAIMING. The first path in sorted order claims the name whether or
     not it emits anything:

         if name in seen_arrays or name == "$": continue
         seen_arrays.add(name)                    # <- claimed here
         items = [i for l in lists for i in l]
         if items and all(isinstance(i, dict) for i in items):   # <- emitted here
             price(items, f"an item of {name}", more)

     So an array of strings at `$.a.tags[]` claims `tags` and prints nothing,
     and a 900-record `$.b.tags[]` is never offered. This is facet 2 of defect
     39 one loop down — a name claimed by a site that yields no candidate — and
     it is a MISSING LINE rather than a wrong number.

Imports `probe.py` and does not modify it. An instrument, not a freeze event —
same standing as `coverage.py`, `axes.py` and `candidate-twins.py`.

**The source file is resolved rather than globbed.** `candidate-twins.py` globs
`*/source.json` and so cannot see `04-gharchive`'s gzip or `12-agent-trace`'s
NDJSON; its recorded survey is 27 of the 29 readable documents.

    uv run design/array-twins.py
"""
import os
import sys
from collections import Counter, defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import probe  # FROZEN at 73e08ca6…. Imported and never modified; see CLAUDE.md.

CAP = 200 * 2**20          # `candidates.py`'s cap, for the same reason
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "corpus")

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


def array_name(p):
    stem = p.rstrip("[]")
    name = stem.split(".")[-1]
    return probe._above_marker(stem) if name == "<key>" else name


def survey(arrs):
    """Replay the array loop, recording what it emits, what it claims and what
    each twin rule would say. Returns (emitted, claimed_nothing).

    `emitted`  -> (name, path, n_items, twins_a, twins_b)
    `claimed`  -> (name, path, n_items, why, [(path, n) records it hid])
    """
    rule_a, rule_b = defaultdict(list), defaultdict(list)
    for q, qlists in sorted(arrs.items()):
        qname = array_name(q)
        qitems = [i for l in qlists for i in l]
        if not qitems:
            continue
        rule_b[qname].append((q, len(qitems), all(isinstance(i, dict) for i in qitems)))
        if all(isinstance(i, dict) for i in qitems):
            rule_a[qname].append((q, len(qitems)))

    emitted, claimed = [], []
    seen = set()
    for p, lists in sorted(arrs.items()):
        name = array_name(p)
        if name in seen or name == "$":
            continue
        seen.add(name)
        items = [i for l in lists for i in l]
        records = bool(items) and all(isinstance(i, dict) for i in items)
        if records:
            twins_a = [(q, n) for q, n in rule_a[name] if q != p]
            twins_b = [(q, n, r) for q, n, r in rule_b[name] if q != p]
            emitted.append((name, p, len(items), twins_a, twins_b))
        else:
            hid = [(q, n) for q, n, r in rule_b[name] if q != p and r]
            why = "empty" if not items else "items are not all records"
            claimed.append((name, p, len(items), why, hid))
    return emitted, claimed


def keyed_claiming(inst):
    """FACET C — the SAME question asked of the keyed loop.

    Defect 39's repair kept `seen.add(name)` above the emptiness test and said
    so: *an empty site still CLAIMS the name, as before*. That preserved the
    behaviour deliberately, and nobody measured what it costs. **Asking one loop
    a question and not the other is how defect 39 happened**, so it is asked
    here rather than assumed harmless.
    """
    keyed = []
    for q, qobjs in sorted(inst.items()):
        if q == "$" or probe.classify(qobjs)[0] != "data":
            continue
        qname = q.split(".")[-1]
        if qname == "<key>":
            qname = probe._above_marker(q)
        if qname == "$":
            continue
        keyed.append((q, qname, [v for o in qobjs for v in o.values()]))

    by_name = defaultdict(list)
    for q, qname, qvals in keyed:
        by_name[qname].append((q, len(qvals)))

    out, seen = [], set()
    for p, name, vals in keyed:
        if name in seen:
            continue
        seen.add(name)
        if vals:
            continue
        hid = [(q, n) for q, n in by_name[name] if q != p and n]
        if hid:
            out.append((name, p, hid))
    return out


def main():
    mods_a = mods_b = 0
    mixed, same_kind, bigger_mixed = [], 0, 0
    losses, keyed_losses, skipped = [], [], []
    n_emitted = 0

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

        for name, p, hid in keyed_claiming(inst):
            keyed_losses.append((entry, name, p, hid))

        emitted, claimed = survey(arrs)
        n_emitted += len(emitted)
        for name, p, n, twins_a, twins_b in emitted:
            if twins_a:
                mods_a += 1
            if twins_b:
                mods_b += 1
            for q, qn, is_rec in twins_b:
                if is_rec:
                    same_kind += 1
                else:
                    mixed.append((entry, name, p, n, q, qn))
                    if qn > n:
                        bigger_mixed += 1
        for name, p, n, why, hid in claimed:
            if hid:
                losses.append((entry, name, p, n, why, hid))

    print("A — THE TWIN RULE: what rule B would add to the array loop\n")
    print(f"  {'entry':<26} {'name':<22} {'printed':>9} {'twin':>9}  kind")
    for entry, name, p, n, q, qn in mixed:
        print(f"  {entry:<26} {name:<22} {n:>9,} {qn:>9,}  MIXED"
              f"{'  (twin is BIGGER)' if qn > n else ''}")
    print()
    print(f"  {n_emitted} array candidates emitted over the corpus")
    print(f"  rule A — a twin is a RECORD-valued array site : {mods_a} modifiers")
    print(f"  rule B — a twin is ANY array site of the name : {mods_b} modifiers")
    # **The label here was wrong on the first run and the number was not.**
    # `same_kind` is every record-to-record relationship, which rule A ALREADY
    # counts; only the mixed ones are what rule B adds. Printing them as though
    # both were new made a 2-modifier change read as a 773-relationship one.
    print(f"  relationships: {same_kind} record-to-record, which rule A already "
          f"counts")
    print(f"  rule B ADDS {len(mixed)}, and every one of them is MIXED")
    print(f"  {bigger_mixed} of those mixed twins are bigger than the printed count")

    print("\nB — NAME CLAIMING: a name claimed by a site that emits nothing\n")
    for entry, name, p, n, why, hid in losses:
        print(f"  {entry:<26} {name:<22} claimed by {p}")
        print(f"  {'':<26} {'':<22} {why}, {n:,} items")
        for q, qn in hid:
            print(f"  {'':<26} {'':<22} HIDES {q} — {qn:,} records never offered")
    per_doc = Counter(l[0] for l in losses)
    print()
    print(f"  {len(losses)} names claimed by a site that emits nothing while a "
          f"record-valued site of the same name exists,")
    print(f"  across {len(per_doc)} document{'s' if len(per_doc) != 1 else ''}")

    print("\nC — THE SAME QUESTION ASKED OF THE KEYED LOOP\n")
    for entry, name, p, hid in keyed_losses:
        print(f"  {entry:<26} {name:<22} claimed by {p} — no values")
        for q, qn in hid:
            print(f"  {'':<26} {'':<22} HIDES {q} — {qn:,} values never offered")
    per_k = Counter(l[0] for l in keyed_losses)
    print()
    print(f"  {len(keyed_losses)} names claimed by an EMPTY keyed site while a "
          f"site of the same name has values,")
    print(f"  across {len(per_k)} document{'s' if len(per_k) != 1 else ''}")

    if skipped:
        print()
        for entry, why in skipped:
            print(f"  not run: {entry} — {why}")


if __name__ == "__main__":
    main()
