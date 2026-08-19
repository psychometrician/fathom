"""Does every verb survive a reader that stops reading?

    uv run test/pipe.py               # exits non-zero on any panic

**Nothing else in `test/` can catch this, and that is why it exists.**
`parity.py`, `candidates.py` and `bindings.py` all capture stdout and read it to
EOF, so the far end never closes early and the failure mode is invisible to
every scorer this project has. Defect 37 lived through all of them.

**What it is.** Rust ignores SIGPIPE at startup, so a closed pipe comes back as
a write error, and `println!` unwraps that into a panic. `head`, `less` and a
`jq` that has seen enough all close early; `design/implementation.md` records
the rule — a closed reader is `head`, not a failure, and the process exits 0.

**Two readers, because output SHAPE decides which one can close.** A
line-bounded reader (`head -3`) never fills its count on `structure`, which is
one 16 MB line, so it reads to the end and nothing fails. A byte-bounded reader
closes mid-line and catches it. Measuring only the first is how `structure`
looked healthy on 2026-08-15 before it was measured properly.

**A verb whose whole output fits in the pipe buffer CANNOT fail** — one write
lands in the buffer before the reader exits. That is not a pass, it is a case
that did not run, so it is reported as `too small` rather than counted. Every
`probe` report in the corpus is under the 64 KB buffer, which is defect 33's
readability cap doing a second job nobody designed.

Shaped like the other scorers: one line per group, non-zero exit on failure.
"""

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "target" / "release" / "fathom"
PIPE_BUF = 65536

# The biggest document that is not the 870 MB one, so the suite stays runnable.
# `where --tsv` on it is 637,697 bytes — the only corpus output that passes the
# pipe buffer, and it is defect 36 seen from the output end.
BIG = ROOT / "corpus" / "29-mdn-browser-compat" / "source.json"
SMALL = ROOT / "corpus" / "01-npm-registry" / "source.json"

# Every stdout-writing path in `fathom-cli/src/main.rs`. A verb added without a
# line here is a verb this check does not cover, which is the gap defect 37 sat
# in for a day.
CASES = [
    ("probe", [BIG, "probe"]),
    ("structure", [BIG, "structure"]),
    ("health", [BIG]),
    ("health --json", [BIG, "health", "--json"]),
    ("where", [BIG, "where", "url"]),
    ("where --tsv", [BIG, "where", "url", "--tsv"]),
    ("where --tsv (no hits)", [SMALL, "where", "email", "--tsv"]),
    ("rows (shape line)", [BIG, "rows", "$.browsers[]"]),
    ("rows --ndjson", [BIG, "rows", "--candidate", "an entry of api.*.*", "--ndjson"]),
    ("rows --tsv", [BIG, "rows", "--candidate", "an entry of api.*.*", "--tsv"]),
    ("whichever", [BIG, "whichever", "browsers", "api"]),
    ("whichever --tsv", [BIG, "whichever", "browsers", "api", "--tsv"]),
]


def argv(case):
    """`fathom <verb> <file> …` — the file is the second word, the case gives the rest."""
    path, *rest = case
    verb = rest[0] if rest and not rest[0].startswith("--") else None
    tail = rest[1:] if verb else rest
    return [str(BIN)] + ([verb] if verb else []) + [str(path)] + [str(x) for x in tail]


def size(case):
    """How much the verb prints when nobody interrupts it."""
    r = subprocess.run(argv(case), capture_output=True)
    return len(r.stdout)


def run_and_close(case, mode):
    """Start the verb, take a little, close the pipe, and see how it took that.

    Returns (panicked, status). The close is the whole point: `stdout.close()`
    on the parent drops the read end, so the child's next write gets EPIPE.
    """
    p = subprocess.Popen(argv(case), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    try:
        if mode == "lines":
            for _ in range(3):
                if not p.stdout.readline():
                    break
        else:
            p.stdout.read(100)
    finally:
        p.stdout.close()
    err = p.stderr.read().decode("utf-8", "replace")
    p.stderr.close()
    status = p.wait()
    return ("panicked" in err or "Broken pipe" in err), status, err


def main():
    if not BIN.exists():
        sys.exit("build first: cargo build --release")
    print("PIPE: every verb against a reader that stops reading")
    failures = []
    exercised = skipped = 0
    for name, case in CASES:
        n = size(case)
        if n <= PIPE_BUF:
            # One write, delivered whole before the reader can exit. Nothing to
            # test, and saying so beats counting it as a pass.
            print(f"  {name:<24} too small — {n:,} B fits the {PIPE_BUF:,} B buffer")
            skipped += 1
            continue
        for mode in ("lines", "bytes"):
            panicked, status, err = run_and_close(case, mode)
            exercised += 1
            if panicked or status != 0:
                failures.append((name, mode, status, err.strip().splitlines()[:2]))
        print(f"  {name:<24} ok — {n:,} B, line-bounded and byte-bounded readers")

    print()
    print(f"  {exercised} runs over {len(CASES) - skipped} verbs; {skipped} too small to test")
    if failures:
        print()
        for name, mode, status, lines in failures:
            print(f"  FAIL {name} ({mode}-bounded reader) exit={status}")
            for ln in lines:
                print(f"       {ln}")
        sys.exit(1)
    print("  no panics")


if __name__ == "__main__":
    main()
