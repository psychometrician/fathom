"""Does the same sentence give the same answer in R and in Python?

    uv run design/parity.py          # exits non-zero on any mismatch

**This is the project's premise made into a test.** `README.md` wants one way of
seeing and extracting that works the same in R and in Python, and until
2026-08-09 every word that ran was Python. `README.md` also warns, about the word
shared with god:

> a word shared with god needs a **stated owner** and a test on both sides from
> the day it is shared, or the two will drift and the drift will be invisible.

There was no such harness. This is it, for fathom's own two sides.

**It compares two independent implementations, not one behind two doors.**
`design/implementation.md` proposes a Rust core with thin bindings, which would
make the languages agree by construction and prove nothing about the vocabulary.
`design/fathom.R` re-implements the path language from the same written notation,
so a disagreement here is a disagreement about **what the words mean**.

It is deliberately shaped like `test/check.py`: a table of cases, one line per
case, non-zero exit on failure.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from rows import match, parse

HERE = Path(__file__).parent
ROOT = HERE.parent

# (corpus entry, path, what the path exercises)
CASES = [
    ("01-npm-registry", "versions.*", "keys-as-data, one row per key"),
    ("01-npm-registry", "versions.*.dependencies.*", "two stars, edges"),
    ("02-hn-thread", "children.*", "one named step"),
    ("02-hn-thread", "children**", "a named step, repeated"),
    ("03-natural-earth", "features.*", "an array of records"),
    ("05-fhir-bundle", "entry.*.resource", "star then a named field"),
    ("15-github-issues", "*", "a top-level array"),
    ("16-movie-ratings", "*.*", "array then keyed object"),
    ("17-openlibrary", "docs.*", "wrapper then array"),
    ("19-chicago-salaries", "*", "5,000 flat records"),
    ("05-fhir-bundle", ".", "the document itself, one row"),
]

R_DRIVER = r"""
.fathom_sourced <- TRUE
suppressMessages(source(commandArgs(trailingOnly=TRUE)[1]))
a <- commandArgs(trailingOnly=TRUE)
doc <- jsonlite::fromJSON(a[2], simplifyVector = FALSE)
r <- rows(doc, a[3])
k <- if (length(r$keys) && length(r$keys[[1]])) paste(unlist(r$keys[[1]]), collapse="|") else "-"
cat(r$n, k, "\n")
"""

# `where` takes a predicate rather than a path, so it needs its own table and
# its own driver. Added 2026-08-10 with the R implementation, which is the point
# — a word and its parity case arriving together is what `README.md` asks for
# and what the first four words did not do.
WHERE_CASES = [
    ("01-npm-registry", "url", "the O(data) trap: 659 shapes if the fold fails"),
    ("01-npm-registry", "email", "sparse matches under keys-as-data"),
    ("02-hn-thread", "date", "a recursive document, nothing folds"),
    ("05-fhir-bundle", "url", "arrays of records, deep"),
    ("07-graphql-introspection", "empty", "the file that is 51.7% null"),
    ("10-wikidata", "url", "keys-as-data at 13 levels"),
    ("13-package-lock", "url", "many matches, few shapes"),
    # KEPT DELIBERATELY THOUGH IT MATCHES NOTHING, because the nothing is the
    # assertion. `16-movie-ratings` is the corpus's missingness specimen and its
    # missingness is the STRING `"unknown"` — defect 18. A predicate looking for
    # nulls and empty strings finding zero is that defect restated by a second
    # instrument, and both languages have to agree about it.
    ("16-movie-ratings", "empty", "0 — missingness is written as a value"),
]

R_WHERE_DRIVER = r"""
.fathom_sourced <- TRUE
suppressMessages(source(commandArgs(trailingOnly=TRUE)[1]))
a <- commandArgs(trailingOnly=TRUE)
doc <- jsonlite::fromJSON(a[2], simplifyVector = FALSE)
h <- where(doc, a[3])
if (!length(h)) { cat("0 0 -\n") } else {
  # Deterministic on ties in BOTH languages: most matches first, then the path
  # itself. Without the second key a tie is resolved by hash order and the
  # harness reports a disagreement that is not one.
  o <- order(-h, names(h))
  cat(length(h), sum(h), sprintf("%s|%d", names(h)[o[1]], h[o[1]]), "\n")
}
"""


def python_count(path, expr):
    """Count AND the first row's captured keys.

    Counts alone are a weak test: two different path implementations can agree
    on how many things they found and disagree about which. The captured keys
    are what `rows()` turns into columns, so comparing the first row's keys
    catches a disagreement about ordering or about what `*` captures.
    """
    with open(path, "rb") as fh:
        raw = fh.read()
    doc = json.loads(raw.decode("utf-8", errors="replace"))
    got = list(match(doc, parse(expr)))
    keys = "|".join(str(k) for k in got[0][0]) if got and got[0][0] else "-"
    return len(got), keys


def r_count(path, expr):
    driver = HERE / "_parity_driver.R"
    driver.write_text(R_DRIVER)
    try:
        out = subprocess.run(
            ["Rscript", str(driver), str(HERE / "fathom.R"), str(path), expr],
            capture_output=True, text=True, timeout=600)
        if out.returncode != 0:
            return None, out.stderr.strip().splitlines()[-1:] or ["failed"]
        # Split ONCE. A captured key can contain a space — `16-movie-ratings`
        # is keyed by film title, so "12 Strong" was being truncated to "12"
        # and reported as a language disagreement that did not exist.
        parts = out.stdout.strip().split(None, 1)
        return (int(parts[0]), parts[1].strip() if len(parts) > 1 else "-"), None
    finally:
        driver.unlink(missing_ok=True)


def python_where(path, pred):
    """Shapes, total matches, and the biggest shape. Same tiebreak as the R."""
    from where import where
    with open(path, "rb") as fh:
        doc = json.loads(fh.read().decode("utf-8", errors="replace"))
    hits = where(doc, pred)
    if not hits:
        return 0, 0, "-"
    top = min(hits.items(), key=lambda kv: (-kv[1], kv[0]))
    return len(hits), sum(hits.values()), f"{top[0]}|{top[1]}"


def r_where(path, pred):
    driver = HERE / "_parity_where.R"
    driver.write_text(R_WHERE_DRIVER)
    try:
        out = subprocess.run(
            ["Rscript", str(driver), str(HERE / "fathom.R"), str(path), pred],
            capture_output=True, text=True, timeout=900)
        if out.returncode != 0:
            return None, out.stderr.strip().splitlines()[-1:] or ["failed"]
        parts = out.stdout.strip().split(None, 2)
        return (int(parts[0]), int(parts[1]),
                parts[2].strip() if len(parts) > 2 else "-"), None
    finally:
        driver.unlink(missing_ok=True)


def main():
    total = len(CASES) + len(WHERE_CASES)
    print(f"\n  parity: {total} sentences, two independent implementations\n")
    bad = 0
    for entry, expr, why in CASES:
        src = ROOT / "corpus" / entry / "source.json"
        if not src.exists():
            print(f"    {entry:<22} {expr:<28} SKIP  no source.json")
            continue
        py_n, py_k = python_count(src, expr)
        r, err = r_count(src, expr)
        # R indexes arrays from 0 here by construction (see children()), so the
        # captured keys are directly comparable rather than off by one.
        ok = r is not None and r[0] == py_n and r[1] == py_k
        bad += not ok
        mark = "ok" if ok else "MISMATCH"
        got = f"{r[0]:,}" if r is not None else (err[0][:24] if err else "error")
        print(f"    {entry:<20} {expr:<26} py {py_n:>6,}  R {got:>7}  "
              f"keys {py_k[:14]:<15} {mark}")

    print()
    for entry, pred, why in WHERE_CASES:
        src = ROOT / "corpus" / entry / "source.json"
        if not src.exists():
            print(f"    {entry:<22} where({pred}) SKIP  no source.json")
            continue
        py = python_where(src, pred)
        r, err = r_where(src, pred)
        ok = r is not None and tuple(r) == py
        bad += not ok
        mark = "ok" if ok else "MISMATCH"
        got = f"{r[1]:,}" if r is not None else (err[0][:24] if err else "error")
        print(f"    {entry:<20} {'where(' + pred + ')':<26} py {py[1]:>6,}  "
              f"R {got:>7}  {py[0]:>3} shapes  {mark}")
        if not ok and r is not None:
            print(f"      py {py}\n      R  {tuple(r)}")

    print(f"\n  {total - bad} of {total} agree\n")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
