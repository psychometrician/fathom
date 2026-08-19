"""The central claim, measured as a SLOPE rather than as a point.

    uv run design/growth.py <file> <keyed path>
    uv run design/growth.py corpus/09-stripe-openapi/source.json components.schemas

`README.md` makes one sharp claim about every tool that already exists:

> **Every existing describer's output is proportional to the data. What is
> needed is output proportional to the structure.**

**Until 2026-08-09 that was only ever measured at single points** — `str()` at
7,099 lines on npm, `tidyjson::json_schema` at 61% of npm, polars at 60% of the
same file, `pydash` at 157% of Stripe. Each is one document and one number, and a
reader has to take on trust that the ratio means what it is said to mean.

**A ratio is not the claim. The claim is a slope**, and it is falsifiable:

    take one document, describe a growing prefix of its records
      proportional to the DATA       the ratio stays FLAT
      proportional to the STRUCTURE  the ratio FALLS, because the structure
                                     stops growing while the document does not

That is a test the claim could fail, which is the reason to write it. Measured on
`09-stripe-openapi`, the corpus's most keys-as-data document:

     schemas   input bytes   probe chars   % of input
          10        34,724         2,100         6.0%
          50        81,282         3,036         3.7%
         200       306,408         3,265         1.1%
         800     1,074,271         3,980         0.4%
       1,440     1,789,612         4,030         0.2%

**The input grows 52x and the probe's answer grows 1.9x.** Against
`tidyjson::json_schema` on the same prefixes, from
`corpus/09-stripe-openapi/r/try-tidyjson.R`: **42%, 44%, 42%** — flat across a
9x growth in input.

**This is the whole project in one table**, and it is the first form of the
measurement that could have come out the other way.
"""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def prefix_sizes(n):
    """A geometric-ish ladder, so the slope is visible rather than inferred."""
    out = [s for s in (10, 50, 200, 800, 3200, 12800) if s < n]
    return out + [n]


def main(path, keyed):
    with open(path, "rb") as fh:
        doc = json.load(fh)
    for seg in keyed.split("."):
        doc = doc[seg]
    if not isinstance(doc, dict):
        print("  that path is not a keyed object")
        return 1
    keys = list(doc)

    print(f"\n  growth: describing a growing prefix of {keyed}\n")
    print(f"    {'records':>9} {'input bytes':>13} {'probe chars':>12} {'% of input':>11}")
    first = None
    for n in prefix_sizes(len(keys)):
        sub = {k: doc[k] for k in keys[:n]}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(sub, fh)
            tmp = fh.name
        try:
            size = os.path.getsize(tmp)
            out = subprocess.run(["uv", "run", os.path.join(HERE, "probe.py"), tmp],
                                 capture_output=True, text=True).stdout
        finally:
            os.unlink(tmp)
        pct = 100 * len(out) / size
        first = first or (size, len(out))
        print(f"    {n:>9,} {size:>13,} {len(out):>12,} {pct:>10.1f}%")

    grew_in = size / first[0]
    grew_out = len(out) / first[1]
    print(f"\n  input grew {grew_in:.0f}x, the description grew {grew_out:.1f}x")
    print("  Proportional to the data would hold the percentage FLAT.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
