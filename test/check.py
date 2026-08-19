"""Score a health verb against test/cases.

    uv run test/generate.py && uv run test/check.py
    uv run test/check.py -v          # list every case, not only the failures
    uv run test/check.py --rust      # score the Rust core instead

Exit status is 1 if anything is wrong, so this can gate a commit.

**What is being scored is what fathom SAID, not whether it parsed.** A parser
suite checks accept/reject. fathom is a reporter, so a case passes only if the
format it named and the damage flags it raised both match the manifest. A flag
that fires when it should not is a failure exactly as loud as one that does not
fire when it should — over-reporting is how a diagnostic gets ignored.

**`--rust` scores `fathom-core` through the CLI, and it is deliberately the SAME
scorer rather than a second one.** The port has an oracle — `design/probe.py`
at `dcd6ec8b…` — and the only claim worth making is that the two agree. A
separate Rust test suite would be free to be wrong in the same direction as the
Rust, which is how two implementations drift while both stay green. Here one
manifest and one set of rules read both, so a disagreement is a failure of
whichever is being scored and cannot hide in the harness.
"""
import json
import pathlib
import subprocess
import sys

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "design"))
import probe  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parent.parent
CASES = pathlib.Path(__file__).parent / "cases"
BIN = ROOT / "target" / "release" / "fathom"
FLAGS = ("dupes", "nonfinite", "bigints", "negzero", "bad_bytes", "encoded")


def by_rust(path):
    """Ask the CLI, and let a crash be a failure rather than an exception."""
    r = subprocess.run([str(BIN), "health", "--json", str(path)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return {"format": f"<exit {r.returncode}: {r.stderr.strip()[:80]}>"}
    return json.loads(r.stdout)


def run(verbose=False, rust=False):
    if rust and not BIN.exists():
        print(f"no binary at {BIN} — run `cargo build --release` first")
        return 1
    man = [json.loads(l) for l in open(CASES / "manifest.jsonl")]
    fails = []
    for m in man:
        if rust:
            h = by_rust(CASES / m["path"])
        else:
            h, _ = probe.health(CASES / m["path"])
        got_flags = sorted(f for f in FLAGS if h.get(f))
        why = []
        if h.get("format") != m["format"]:
            why.append(f"format {h.get('format')!r}, wanted {m['format']!r}")
        if got_flags != m["flags"]:
            missing = set(m["flags"]) - set(got_flags)
            extra = set(got_flags) - set(m["flags"])
            if missing:
                why.append(f"did not report {sorted(missing)}")
            if extra:
                why.append(f"FALSE POSITIVE {sorted(extra)}")
        for k in ("empty", "truncated", "bom", "records", "compressed"):
            if k in m and h.get(k) != m[k]:
                why.append(f"{k}={h.get(k)!r}, wanted {m[k]!r}")
        if "bad_lines" in m and len(h.get("bad_lines") or []) != m["bad_lines"]:
            why.append(f"bad_lines={len(h.get('bad_lines') or [])}, wanted {m['bad_lines']}")
        if why:
            fails.append((m["path"], "; ".join(why), m["note"]))
        elif verbose:
            print(f"  ok   {m['path']}")

    groups = {}
    for m in man:
        groups.setdefault(m["path"].split("/")[0], [0, 0])[0] += 1
    for p, _, _ in fails:
        groups[p.split("/")[0]][1] += 1
    print(f"\n{len(man)} cases · {'fathom-core (Rust)' if rust else 'design/probe.py'}")
    for g, (n, bad) in sorted(groups.items()):
        mark = "ok" if not bad else f"{bad} FAILED"
        print(f"  {g:<12} {n:>4}   {mark}")
    if fails:
        print(f"\n{len(fails)} failures:")
        for path, why, note in fails[:25]:
            print(f"  {path}\n      {why}\n      ({note})")
        if len(fails) > 25:
            print(f"  ... and {len(fails) - 25} more")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(run(verbose="-v" in sys.argv, rust="--rust" in sys.argv))
