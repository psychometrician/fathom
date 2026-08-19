"""Diff the Rust core against design/probe.py, stage by stage, on every file.

    cargo build --release && uv run test/parity.py
    uv run test/parity.py -v     # show more than the first difference per file

**This is a stronger check than `check.py --rust` and the difference matters.**
The manifest records which damage flags should FIRE, not what they should
COUNT, so both implementations can pass all 198 cases while disagreeing about
how many replacement characters a truncated document earned. That disagreement
is precisely what `design/implementation.md` predicted would bite, so scoring it
by pass/fail would have hidden the one measurement the prediction was about.

**It scores the STAGES and then the finished page, and it needs both.**

The last stage is the criterion `design/implementation.md` set: the probe's
product is a rendered report, and a port is finished when the diff is empty.
Nothing weaker will do, because a report that is right in substance and
different in layout is still a different report — and this book's own
`coverage.py` reads the page back as a set of claims, telling a shape header
from a `SPLIT ON` from a wrapped continuation by indentation alone.

But a byte diff alone can only say "this document differs" and leave which of
the walk, the fold, the classifier, the pricing or the renderer produced it to
be guessed. So every stage is also dumped and diffed as structured data. The
stages say WHERE; the page says WHETHER.

**It imports `design/probe.py` and does not modify it**, which is the same
arrangement `design/axes.py`, `design/growth.py` and `design/coverage.py`
already have with it. The probe is frozen; an instrument that reads it is not a
freeze event.
"""
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "design"))
import probe  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = ROOT / "test" / "cases"
BIN = ROOT / "target" / "release" / "fathom"

# Every health field the port claims to reproduce. `error` is compared too: the
# report prints it verbatim for a file it cannot read, so its wording is output.
FIELDS = ("format", "bytes", "dupes", "negzero", "nonfinite", "bigints",
          "encoded", "bad_bytes", "empty", "truncated", "bom", "records",
          "lines", "sampled", "compressed", "packed_bytes", "error")


def targets():
    """The synthetic cases AND every corpus file, because rule 3 says every
    file gets asked the same questions. The suite is exhaustive about damage
    nobody has; the corpus is the only place real documents answer.
    """
    for line in open(CASES / "manifest.jsonl"):
        yield CASES / json.loads(line)["path"]
    for d in sorted((ROOT / "corpus").iterdir()):
        if (d / "source.json").exists():
            yield d / "source.json"


def ask(verb, path):
    args = [str(BIN), verb, str(path)]
    if verb == "health":
        args.insert(2, "--json")
    r = subprocess.run(args, capture_output=True, text=True)
    if r.returncode != 0:
        return None, r.stderr.strip()[:120]
    return json.loads(r.stdout), None


def structure_py(doc):
    """The same stages, out of the frozen probe."""
    inst, arrs, types = probe.containers(doc)
    pairs = lambda m: [[p, len(v)] for p, v in m.items()]           # noqa: E731
    tal = lambda m: [[p, [[s, n] for s, n in c.items()]]            # noqa: E731
                     for p, c in m.items()]
    walk = {"inst": pairs(inst), "arrs": pairs(arrs), "types": tal(types)}
    finst, farrs, rec, ftypes = probe.fold_recursion(inst, arrs, types)
    fold = {"inst": pairs(finst), "arrs": pairs(farrs), "types": tal(ftypes),
            "rec": [[p, n] for p, n in rec.items()]}
    cls = [[p, *probe.classify(objs)] for p, objs in finst.items()]

    # The measures and the split, on the same lists the renderer will use —
    # `main()` drops empty dicts before it prints or prices anything.
    measures, splits = [], []
    for p, objs in finst.items():
        live = [o for o in objs if o]
        measures.append([p, probe.emptiness(live), probe.variation(live)])
        found = probe.discriminator(objs)
        if found is None:
            splits.append([p, None, None])
        else:
            field, groups = found
            splits.append([p, field, [[str(v), len(g)] for v, g in groups.items()]])
    # The row pricing. `candidates()` returns the tuples `main()` prints, and
    # the split it carries is computed on the priced RECORDS rather than on the
    # inst path, so it is compared here as well as above.
    cands = []
    for label, rows, cols, holes, dup, found, more in probe.candidates(
            doc, finst, farrs, rec):
        cands.append([label, rows, cols, holes,
                      [dup[0], dup[1]] if dup else None,
                      [found[0], len(found[1])] if found else None,
                      [more[0], more[1], more[2]] if more else None])

    return {"walk": walk, "fold": fold, "classify": cls,
            "measures": measures, "splits": splits, "candidates": cands}


def diff(a, b, where=""):
    """First differences between two JSON-shaped values, with a path."""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            sa, sb = {json.dumps(x[:1]) for x in a if isinstance(x, list)}, \
                     {json.dumps(x[:1]) for x in b if isinstance(x, list)}
            extra = [json.loads(x)[0] for x in sorted(sb - sa)][:3]
            missing = [json.loads(x)[0] for x in sorted(sa - sb)][:3]
            note = f"{where}: {len(a)} entries in probe, {len(b)} in rust"
            if missing:
                note += f" | rust lacks {missing}"
            if extra:
                note += f" | rust adds {extra}"
            return [note]
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out += diff(x, y, f"{where}[{i}]")
            if len(out) >= 4:
                break
        return out
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for k in a:
            out += diff(a[k], b.get(k), f"{where}.{k}")
            if len(out) >= 4:
                break
        return out
    if a != b:
        return [f"{where}: probe={a!r} rust={b!r}"]
    return []


# The extract half. Same nineteen sentences `design/parity.py` puts to Python
# and to R, put to the core — so the three are held to one contract rather than
# to two overlapping ones.
#
# Row counts alone are a weak test: two path implementations can agree on how
# many things they found and disagree about WHICH. The first match's captured
# keys are what `rows()` turns into columns, so comparing them catches a
# disagreement about ordering or about what `*` captures.
ROW_CASES = [
    ("01-npm-registry", "versions.*"), ("01-npm-registry", "versions.*.dependencies.*"),
    ("02-hn-thread", "children.*"), ("02-hn-thread", "children**"),
    ("03-natural-earth", "features.*"), ("05-fhir-bundle", "entry.*.resource"),
    ("15-github-issues", "*"), ("16-movie-ratings", "*.*"),
    ("17-openlibrary", "docs.*"), ("19-chicago-salaries", "*"),
    ("05-fhir-bundle", "."),
]
WHERE_CASES = [
    ("01-npm-registry", "url"), ("01-npm-registry", "email"),
    ("02-hn-thread", "date"), ("05-fhir-bundle", "url"),
    ("07-graphql-introspection", "empty"), ("10-wikidata", "url"),
    ("13-package-lock", "url"),
    # Matches nothing, and the nothing IS the assertion: this file's missingness
    # is the string "unknown", defect 18. A predicate looking for nulls finding
    # zero is that defect restated by a second instrument.
    ("16-movie-ratings", "empty"),
]

# An unknown test name. BOTH HALVES MUST REFUSE — the assertion is the refusal,
# not any output, so it cannot live in WHERE_CASES with the cases that compare
# numbers.
#
# **This branch was unreachable by this harness until 2026-08-14**, because
# every case above passes one of the four valid names, and the port's
# `matches()` ended in `_ => false`. So `fathom where <file> urls` printed
# `0 0 -` and exited 0 — byte-identical to the honest zero asserted directly
# above it, and on the same file a typo would most plausibly be made.
#
# **A diff over inputs that cannot reach a branch says nothing about that
# branch.** That is defect 30's lesson, and it cost a repair asserted from a
# clean corpus diff; here it cost a whole verb's error handling. The fix and
# this case were written the same day.
UNKNOWN_TESTS = ["urls", "URL", "", "http", "is_url"]


def vocabulary(diffs):
    """`rows` and `where`, Python against the core, on the same sentences."""
    sys.path.insert(0, str(ROOT / "design"))
    from rows import match, parse                                   # noqa: E402
    from where import where                                         # noqa: E402
    n = 0
    for entry, expr in ROW_CASES:
        src = ROOT / "corpus" / entry / "source.json"
        if not src.exists():
            continue
        doc = json.loads(src.read_bytes().decode("utf-8", "replace"))
        got = list(match(doc, parse(expr)))
        py = [len(got), "|".join(str(k) for k in got[0][0]) if got and got[0][0] else "-"]
        r = subprocess.run([str(BIN), "rows", str(src), expr],
                           capture_output=True, text=True)
        p = r.stdout.strip().split(None, 1)
        rs = [int(p[0]), p[1].strip() if len(p) > 1 else "-"] if p else [-1, "!"]
        n += 1
        if py != rs:
            diffs.append((f"{entry} rows({expr})", f"probe={py} rust={rs}"))
    for entry, pred in WHERE_CASES:
        src = ROOT / "corpus" / entry / "source.json"
        if not src.exists():
            continue
        doc = json.loads(src.read_bytes().decode("utf-8", "replace"))
        h = where(doc, pred)
        if not h:
            py = [0, 0, "-"]
        else:
            t = min(h.items(), key=lambda kv: (-kv[1], kv[0]))
            py = [len(h), sum(h.values()), f"{t[0]}|{t[1]}"]
        o = subprocess.run([str(BIN), "where", str(src), pred],
                           capture_output=True, text=True).stdout.strip().split(None, 2)
        rs = [int(o[0]), int(o[1]), o[2] if len(o) > 2 else "-"] if o else [-1, -1, "!"]
        n += 1
        if py != rs:
            diffs.append((f"{entry} where({pred})", f"probe={py} rust={rs}"))
    # The refusals. A pass here is BOTH raising, and the wording is deliberately
    # not compared: the oracle raises a Python exception and the core exits with
    # a message, so the two agree in kind rather than in bytes. What must never
    # happen again is one of them answering the question.
    src = ROOT / "corpus" / "01-npm-registry" / "source.json"
    if src.exists():
        doc = json.loads(src.read_bytes().decode("utf-8", "replace"))
        for pred in UNKNOWN_TESTS:
            try:
                where(doc, pred)
                py = "answered"
            except ValueError:
                py = "refused"
            r = subprocess.run([str(BIN), "where", str(src), pred],
                               capture_output=True, text=True)
            rs = "refused" if r.returncode != 0 else "answered"
            n += 1
            if py != "refused" or rs != "refused":
                diffs.append((f"where({pred!r}) unknown test",
                              f"probe={py} rust={rs}"))
    return n


def main(verbose=False):
    if not BIN.exists():
        print(f"no binary at {BIN} — run `cargo build --release` first")
        return 1
    hdiffs, sdiffs, rdiffs = [], [], []
    n_h = n_s = n_r = 0
    for path in targets():
        name = str(path.relative_to(ROOT))
        py, doc = probe.health(path)

        rs, err = ask("health", path)
        if err is not None:
            hdiffs.append((name, f"CRASH: {err}"))
            continue
        n_h += 1
        for f in FIELDS:
            a, b = py.get(f), rs.get(f)
            # Python omits a key where Rust writes null, and absent and null
            # mean the same thing to every reader of this summary.
            if a is None and b is None:
                continue
            if a != b:
                hdiffs.append((name, f"{f}: probe={a!r} rust={b!r}"))
        if len(py.get("bad_lines") or []) != len(rs.get("bad_lines") or []):
            hdiffs.append((name, "bad_lines count"))

        if doc is None:
            continue
        rstruct, err = ask("structure", path)
        if err is not None:
            sdiffs.append((name, f"CRASH: {err}"))
            continue
        n_s += 1
        for d in diff(structure_py(doc), rstruct)[:(99 if verbose else 2)]:
            sdiffs.append((name, d))

        # **THE CRITERION.** Every stage above is compared as structured data,
        # which is what tells you WHICH stage is wrong. This compares the thing
        # the probe actually produces — the rendered page, byte for byte.
        # `design/implementation.md`: a port is finished when the diff is empty.
        n_r += 1
        want = subprocess.run(["uv", "run", "design/probe.py", str(path)],
                              capture_output=True, text=True, cwd=ROOT).stdout
        got = subprocess.run([str(BIN), "probe", str(path)],
                             capture_output=True, text=True, cwd=ROOT).stdout
        if want != got:
            wl, gl = want.splitlines(), got.splitlines()
            if len(wl) != len(gl):
                rdiffs.append((name, f"{len(wl)} lines from probe, {len(gl)} from rust"))
            for i, (a, b) in enumerate(zip(wl, gl)):
                if a != b:
                    rdiffs.append((name, f"line {i + 1}\n        probe: {a!r}"
                                         f"\n        rust : {b!r}"))
                    break

    def report(label, n, diffs, fields):
        print(f"\n{label}: {n} documents{fields}")
        if not diffs:
            print("  no differences")
            return 0
        shown = {}
        for path, why in diffs:
            shown.setdefault(path, []).append(why)
        print(f"  {len(diffs)} differences across {len(shown)} documents:")
        for path, whys in list(shown.items())[:12]:
            print(f"  {path}")
            for w in whys[:3]:
                print(f"      {w}")
        if len(shown) > 12:
            print(f"  ... and {len(shown) - 12} more documents")
        return 1

    bad = report("HEALTH", n_h, hdiffs, f", {len(FIELDS)} fields each")
    bad |= report("STRUCTURE", n_s, sdiffs,
                  ", walk + fold + classify + measures + splits + pricing")
    bad |= report("REPORT", n_r, rdiffs, ", the rendered page, byte for byte")
    vdiffs = []
    n_v = vocabulary(vdiffs)
    bad |= report("VOCABULARY", n_v, vdiffs, ", rows + where on the parity sentences")
    return bad


if __name__ == "__main__":
    sys.exit(main(verbose="-v" in sys.argv))
