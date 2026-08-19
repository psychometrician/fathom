"""Does the streaming read agree with the oracle on documents big enough to use it?

    uv run test/streaming.py          # exits non-zero on any difference

**Nothing else reaches this code.** `health()` streams NDJSON instead of holding
the file, and the path is taken only when a document is big enough that its
first 50 lines arrive before EOF. `test/generate.py`'s cases are all a few
hundred bytes, so **every one of them takes the fallback**; `test/parity.py`
reaches the streaming path on exactly three corpus documents — `04-gharchive`,
`12-agent-trace`, `26-gharchive-scale` — and none of those carries a blank line,
a CRLF, or a missing trailing newline.

So the line-shapes the slurp path has always handled were, for the streaming
path, untested. This generates them at a size that forces streaming and diffs
the shipped binary against `design/probe.py`, which is the oracle and is
untouched by the change.

**The fallback is tested here too, deliberately.** A document just small enough
to end inside the prefix must take the old path and still agree — that is the
half of the design that says *when in doubt, slurp*, and a check that only
exercised the fast path would not notice if the fallback stopped being reached.

Shaped like the other scorers: one line per case, non-zero exit on failure.
"""

import gzip
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BIN = ROOT / "target" / "release" / "fathom"
ORACLE = ROOT / "design" / "probe.py"

# `stream_ndjson()` gives up if the document ends while it is still collecting
# the first 50 lines, so a case must comfortably exceed that to stream. It also
# must exceed one 256 KB chunk, or the whole thing arrives in a single read and
# the chunk-boundary logic never runs.
BIG = 9_000
SMALL = 3


def record(i, pad=900):
    return json.dumps({"id": i, "name": f"record-{i}", "pad": "x" * pad,
                       "nested": {"a": [1, 2, 3]}})


def plain(n):
    """Ordinary NDJSON, one object per line, trailing newline."""
    return "\n".join(record(i) for i in range(n)) + "\n"


def ragged(n):
    """Every line-shape `other_format()` filters or repairs, at streaming size.

    Blank and whitespace-only lines are NOT lines; a `\\r` is trimmed; a
    malformed line is counted and reported by its position among the non-empty
    ones; and the document ends WITHOUT a newline, which is the case the chunk
    loop handles after its last read rather than inside it.
    """
    out = []
    for i in range(n):
        line = record(i)
        if i % 500 == 7:
            out.append("")
        if i % 700 == 11:
            out.append("   ")
        if i % 1000 == 13:
            out.append('{"broken": ')
        out.append(line + "\r" if i % 3 == 0 else line)
    return "\n".join(out)


def long_line(n):
    """One record far larger than a chunk, so a single line spans several reads."""
    body = [record(i) for i in range(n)]
    body[n // 2] = record(n // 2, pad=3 * 256 * 1024)
    return "\n".join(body) + "\n"


def bom(n):
    """A BOM must send the document to the fallback and still be right."""
    return "﻿" + plain(n)


CASES = [
    ("plain, streaming", lambda d: write(d, "plain.jsonl", plain(BIG))),
    ("ragged lines, streaming", lambda d: write(d, "ragged.jsonl", ragged(BIG))),
    ("line longer than a chunk", lambda d: write(d, "long.jsonl", long_line(200))),
    ("gzip, streaming", lambda d: write_gz(d, "plain.jsonl.gz", plain(BIG))),
    ("gzip ragged, streaming", lambda d: write_gz(d, "ragged.jsonl.gz", ragged(BIG))),
    ("BOM — must fall back", lambda d: write(d, "bom.jsonl", bom(BIG))),
    ("too small — must fall back", lambda d: write(d, "small.jsonl", plain(SMALL))),
    ("not NDJSON — must fall back", lambda d: write(d, "one.json",
                                                    json.dumps([{"a": i} for i in range(BIG)]))),
]


def write(d, name, text):
    p = Path(d) / name
    p.write_text(text, encoding="utf-8")
    return p


def write_gz(d, name, text):
    p = Path(d) / name
    with gzip.open(p, "wt", encoding="utf-8") as f:
        f.write(text)
    return p


def report(cmd, path):
    r = subprocess.run(cmd + [str(path)], capture_output=True, text=True, cwd=ROOT)
    return r.stdout


def main():
    if not BIN.exists():
        sys.exit("build first: cargo build --release")
    print("STREAMING: the binary against design/probe.py, on documents big enough to stream")
    bad = []
    d = tempfile.mkdtemp(prefix="fathom-streaming-")
    try:
        for name, make in CASES:
            p = make(d)
            mine = report([str(BIN), "probe"], p)
            theirs = report(["uv", "run", str(ORACLE)], p)
            size = p.stat().st_size
            if mine == theirs:
                print(f"  {name:<30} ok — {size:>10,} B")
            else:
                bad.append((name, mine, theirs))
                print(f"  {name:<30} DIFFERS — {size:>10,} B")
    finally:
        shutil.rmtree(d, ignore_errors=True)

    print()
    if bad:
        for name, mine, theirs in bad:
            print(f"  FAIL {name}")
            m, t = mine.splitlines(), theirs.splitlines()
            for i in range(max(len(m), len(t))):
                a = m[i] if i < len(m) else "<missing>"
                b = t[i] if i < len(t) else "<missing>"
                if a != b:
                    print(f"       oracle: {b}")
                    print(f"       binary: {a}")
                    break
        sys.exit(1)
    print(f"  {len(CASES)} cases, no differences")


if __name__ == "__main__":
    main()
