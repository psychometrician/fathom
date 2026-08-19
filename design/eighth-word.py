"""What would a step meaning `stand on the members of this collection` buy?

    uv run design/eighth-word.py            # every document
    uv run design/eighth-word.py --paths 16-movie-ratings

**Defect 38 is that there is a level `rows()` can name and no word can stand
on.** This prices the proposed repair before it is argued, because an eighth
word in a seven-word vocabulary is not a small thing.

## The mechanism it models

`extract::at()` consumes a path segment by NAME, and will take **one implicit
hop** — if `name` is not a field where you stand, it descends into every member
or element that has it. So an into-chain consumes `name`, or `<marker>.name`.
**A TRAILING marker cannot be consumed**, and that is the whole defect.

## Why the PARENT is what is measured

`whichever` and `rows` both read the children of where you stand, so reaching a
candidate's parent container is enough to use it. A candidate whose parent is
unreachable is one the eighth word would buy — and nothing else would.

**This is an instrument.** It runs the shipped binary for its paths and modifies
nothing.
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "target" / "release" / "fathom"
MARKERS = ("<key>", "[]")


def documents():
    for d in sorted((ROOT / "corpus").iterdir()):
        if not d.is_dir():
            continue
        for name in ("source.json", "source.json.gz", "source.jsonl"):
            if (d / name).exists():
                yield d.name, d / name
                break


def structure(path):
    r = subprocess.run([str(BIN), "structure", str(path)],
                       capture_output=True, text=True, cwd=ROOT)
    return json.loads(r.stdout) if r.returncode == 0 else None


def segments(p):
    """`$.a.b[].c` → ['a', 'b', '[]', 'c'], markers as their own segment.

    `<key>` is already dot-separated by the fold; `[]` is glued to the name
    before it and has to be split off, or an array level reads as part of a name.

    **The root's own `[]` is the case that broke this.** `$[]` is a document
    whose root IS an array, and dropping the first dot-segment dropped the
    marker with the `$` — so `$[].<key>`, which is `16-movie-ratings` and the
    whole of defect 38, came back reachable. Only the `$` is removed now.
    """
    body = p[1:] if p.startswith("$") else p    # the `$`, and nothing else
    body = body[1:] if body.startswith(".") else body
    flat = []
    for raw in body.split(".") if body else []:
        while raw.endswith("[]"):
            raw = raw[:-2]
            if raw:
                flat.append(raw)
                raw = ""
            flat.append("[]")
        if raw:
            flat.append(raw)
    return flat


def reachable(path):
    """Can an into-chain STAND on this path?

    Walk the segments: a name is consumed on its own; a marker is consumed only
    together with the name that follows it. A marker with nothing after it is
    where the chain stops, which is exactly what the eighth word would fix.
    """
    segs = segments(path)
    i = 0
    while i < len(segs):
        s = segs[i]
        if s in MARKERS:
            if i + 1 < len(segs) and segs[i + 1] not in MARKERS:
                i += 2                        # the implicit hop: marker + name
            else:
                return False                  # trailing or doubled marker
        else:
            i += 1
    return True


def parent(path):
    """The container a candidate's rows come out of."""
    segs = path.split(".")
    return ".".join(segs[:-1]) if len(segs) > 1 else "$"


def sites(doc):
    """Every folded container path the document has, from the fold."""
    f = doc["fold"]
    out = []
    for key in ("inst", "arrs"):
        for p, _n in f.get(key, []):
            out.append(p)
    return out


def main(argv):
    if not BIN.exists():
        sys.exit("build first: cargo build --release")
    show = argv[1] if argv[:1] == ["--paths"] and len(argv) > 1 else None

    print("\n  THE EIGHTH WORD — what a `stand on the members` step would buy\n")
    print(f"  {'entry':<26} {'sites':>6} {'reachable':>10} {'STRANDED':>9} {'root':>18}")
    rows = []
    for name, path in documents():
        d = structure(path)
        if not d:
            continue
        ss = sites(d)
        # **A site is usable if EITHER it or its parent can be stood on**, and
        # this took three tries to state.
        #
        # The words read the CHILDREN of where you stand, so `$.docs[]` needs
        # only `$.docs` — measuring the site alone called every array level
        # stranded, 52% of the corpus, wrong. But measuring only the parent is
        # wrong the other way: `$.results[].images` has an unreachable parent
        # and is itself reached by `into("results") → into("images")`, because
        # the implicit hop consumes `[]` together with the name after it.
        #
        # Checked against the three cases measured by hand: npm's
        # `$.versions.<key>` usable (288 of 288), wikidata's
        # `$.entities.Q30.aliases.<key>` usable, movie-ratings' `$[].<key>`
        # NOT — which is defect 38.
        strand = [p for p in ss if not (reachable(p) or reachable(parent(p)))]
        rows.append((name, ss, strand))
        print(f"  {name:<26} {len(ss):>6} {len(ss) - len(strand):>10} {len(strand):>9}"
              f" {(strand[0][:18] if strand else '-'):>18}")
        if show == name:
            print("\n    stranded paths in full:")
            for p in strand:
                print(f"      {p}")
            print()

    tot = sum(len(s) for _n, s, _st in rows)
    st = sum(len(x) for _n, _s, x in rows)
    withany = [n for n, _s, x in rows if x]
    print(f"\n  {len(rows)} documents, {tot:,} folded container sites.")
    print(f"  {tot - st:,} standable by an into-chain; {st:,} STRANDED ({100*st/max(tot,1):.1f}%).")
    print(f"  documents with at least one stranded site: {len(withany)} of {len(rows)}")
    if withany:
        print(f"    {', '.join(withany)}")

    # **One document owns 98% of the total and it is the one with defect 36.**
    # `29-mdn-browser-compat`'s fold names 11,320 paths where ~176 is right, so
    # counting its sites prices the eighth word against a known over-fold rather
    # than against the vocabulary. Both figures are printed because the
    # difference between them IS the finding.
    worst = max(rows, key=lambda r: len(r[2]))
    rest = [r for r in rows if r[0] != worst[0]]
    rtot = sum(len(s) for _n, s, _st in rest)
    rst = sum(len(x) for _n, _s, x in rest)
    print(f"\n  {worst[0]} alone holds {len(worst[2]):,} of the {st:,} stranded "
          f"({100*len(worst[2])/max(st,1):.0f}%) — it is the defect-36 document.")
    print(f"  WITHOUT it: {rst:,} stranded of {rtot:,} sites ({100*rst/max(rtot,1):.1f}%), "
          f"across {len([r for r in rest if r[2]])} of {len(rest)} documents.")

    # **The criterion recorded before the run**: if `rows()` already names the
    # stranded sites, the data is not stranded at all — only `into` and
    # `whichever` cannot reach it, and the honest repair might be to say so
    # rather than to add a word. A stranded site `X.<key>` or `X[]` is the
    # source of the candidate called `… of X`, so the parent's last NAME is
    # what the menu would have used.
    named = unnamed = 0
    for name, _ss, strand in rest:
        d = structure(dict(documents())[name])
        labels = " ".join(c[0] for c in d["candidates"]) if d else ""
        for p in strand:
            segs = [s for s in segments(parent(p)) if s not in MARKERS]
            if segs and segs[-1] in labels:
                named += 1
            else:
                unnamed += 1
    print(f"\n  of those {rst:,}, the menu already NAMES {named:,} and does not "
          f"name {unnamed:,}.")


if __name__ == "__main__":
    main(sys.argv[1:])
