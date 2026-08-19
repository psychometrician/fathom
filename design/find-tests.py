"""`find`'s test set, argued against the whole corpus — 2026-08-14.

**An instrument, like `axes.py` and `coverage.py`.** It imports `design/where.py`
and modifies nothing. Running it is not a freeze event.

`VERDICT.md` carries the question: the four tests `url`, `email`, `date`, `empty`
came from `where.py` on 2026-08-09 and **have never been run against the corpus
as a set**. `test/parity.py` passes individual names to check that two
implementations agree, which is a different question from whether the names are
the right ones.

Predictions are in `design/find-tests-predictions.md`, recorded first.

## Two numbers, and the second is the one nobody has looked at

**Coverage** — on how many documents does the test fire at all. A test that never
fires is dead weight.

**Discrimination** — how many FOLDED PATHS it names when it does fire. `where_`'s
own docstring sets the standard: the naive answer on `01-npm-registry` is
thousands of paths, *"the O(data) failure this project exists to name, committed
by fathom's own word"*. The fold repaired that for `url`. Whether it repaired it
for all four has not been asked, and it cannot repair a test whose paths really
are distinct.

**Values matched is recorded and is NOT a criterion.** 806 URLs at 10 paths is an
answer; 806 URLs at 806 paths is a data dump.

## Why the four go through the CLI and the candidates go through `where.py`

The CLI is the shipped thing and it is fast enough to run on 30 MB documents.
`where.py` takes a CALLABLE as well as a name — that is the oracle's contract and
not the port's — so a candidate test can be measured by the same fold, on the
same documents, without being built into anything first.

**Mixing the two is licensed by `test/parity.py`**, which holds them byte
identical on the four names. `--check` re-establishes that here rather than
citing it.
"""
import json
import gzip
import pathlib
import re
import statistics
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIN = ROOT / "target" / "release" / "fathom"
sys.path.insert(0, str(ROOT / "design"))

from where import where  # noqa: E402

TESTS = ["url", "email", "date", "empty"]

# The NDJSON sampling contract, stated in `design/probe.py` and in
# `fathom-core/src/health.rs`. It is copied rather than imported because
# importing `probe` here would make this instrument depend on the frozen file
# to read a constant; `--check` is what proves the two agree.
MAX_RECORDS = 20_000


def documents():
    """Every corpus entry, INCLUDING the three with no `source.json`.

    `test/parity.py` takes `source.json` alone and so covers 26. The gzip and
    the JSONL variants read fine — `04-gharchive` is why `flate2` is a
    dependency — and leaving three documents out of a survey about coverage
    would be choosing the sample to suit the answer.
    """
    for d in sorted((ROOT / "corpus").iterdir()):
        if not d.is_dir():
            continue
        for name in ("source.json", "source.json.gz", "source.jsonl"):
            if (d / name).exists():
                yield d.name, d / name
                break


def load(path):
    """The document as Python. JSONL is a list of its lines, which is what the
    core does with it too — that agreement is checked by `--check`.

    **JSONL is detected by CONTENT and not by the name**, because
    `04-gharchive/source.json.gz` is a gzipped JSONL: it is named `.json.gz`,
    it decompresses to one object per line, and a suffix rule read it as JSON
    and died on `Extra data: line 2`.
    """
    raw = gzip.open(path, "rb").read() if path.suffix == ".gz" else path.read_bytes()
    text = raw.decode("utf-8", "replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # `split("\n")` AND NOT `splitlines()`, which is not a nicety.
        # `splitlines()` also breaks on U+2028, U+0085 and four other
        # separators, and `04-gharchive` carries them inside commit messages —
        # so it cut a record in half and died with `Unterminated string`.
        # The core splits on `\n` alone, which is why the CLI read the same
        # file without complaint.
        #
        # **AND IT STOPS AT `MAX_RECORDS`**, which is the sampling contract
        # both `probe.py` and `fathom-core/src/health.rs` state as 20,000.
        # Reading the whole file here made this instrument measure MORE
        # document than the shipped tool does: on `04-gharchive` it found
        # 268,269 URLs against the binary's 114,519, over 37,883 records
        # against 20,000. The candidate columns would have been priced on a
        # document the four were never asked about.
        out = []
        for ln in text.split("\n"):
            if ln.strip():
                out.append(json.loads(ln))
                if len(out) == MAX_RECORDS:
                    break
        return out


def cli(path, test):
    """`{folded path: count}` from the shipped binary."""
    r = subprocess.run([str(BIN), "where", str(path), test, "--tsv"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        raise SystemExit(f"fathom refused {test!r} on {path}: {r.stderr.strip()}")
    hits = {}
    for line in r.stdout.splitlines()[1:]:
        if "\t" in line:
            p, n = line.rsplit("\t", 1)
            # THE PATH IS A JSON STRING on the wire — `escape()` in the CLI —
            # so it arrives quoted. Keeping the quotes made `--check` report a
            # disagreement on every document at first run, which was this
            # reader and not the port: the counts were identical throughout.
            hits[json.loads(p)] = int(n)
    return hits


# ── The candidate fifth tests ────────────────────────────────────────────────
#
# Each is a guess and the point of measuring is that most should be wrong. They
# take the raw VALUE, because `where.py` offers containers to the predicate too.

SEMVER = re.compile(r"^\d+\.\d+(\.\d+)?([-+][0-9A-Za-z.-]+)?$")
NUMERAL = re.compile(r"^[+-]?(\d+\.?\d*|\.\d+)([eE][+-]?\d+)?$")
UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)
HEXID = re.compile(r"^[0-9a-f]{16,}$", re.I)
PREFIXED = re.compile(r"^(sha\d*|md5|blake\d*)[-:]", re.I)
RFC2822 = re.compile(r"^[A-Z][a-z]{2}, \d{1,2} [A-Z][a-z]{2} \d{4}")


def is_number(v):
    """A NUMERAL WRITTEN AS A STRING, which is a defect in the document rather
    than a category of content. `"1.4"` where `1.4` was meant."""
    return isinstance(v, str) and bool(NUMERAL.match(v)) and not SEMVER.match(v)


def is_when(v):
    """A time in ANY notation — widening `date` rather than joining it.

    An epoch is judged by RANGE and that is a real weakness, written down: an
    integer between 1e9 and 2e9 is a plausible second count and is also a
    plausible anything else. It is offered as a measurement, not a rule.
    """
    if isinstance(v, bool):
        return False
    if isinstance(v, str):
        if re.match(r"^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2})?", v) or RFC2822.match(v):
            return True
        v = int(v) if v.isdigit() else v
    if isinstance(v, int):
        return 1_000_000_000 <= v < 2_000_000_000 or 1_000_000_000_000 <= v < 2_000_000_000_000
    return False


def is_packed_strict(v):
    """DEFECT 26's neighbourhood: a list or an object inside a string, where the
    string parses as JSON and yields a container."""
    if not isinstance(v, str) or len(v) < 2:
        return False
    if v[0] not in "[{":
        return False
    try:
        return isinstance(json.loads(v), (list, dict))
    except Exception:
        return False


def is_packed_naive(v):
    """The same idea by the test a person would write first: a separator and no
    sentence. **The gap between this and the strict one is the finding** —
    defect 26 says the probe calls these fields text because they ARE text, so
    an over-firing test is the predicted outcome rather than a bug in it."""
    if not isinstance(v, str) or len(v) < 3 or v.endswith("."):
        return False
    for sep in (", ", ",", "; ", "|"):
        parts = [p for p in v.split(sep) if p]
        if len(parts) >= 2 and all(len(p) < 40 and p.count(" ") <= 2 for p in parts):
            return True
    return False


def is_id(v):
    """An opaque identifier: uuid, long hex, or a prefixed digest."""
    return isinstance(v, str) and bool(
        UUID.match(v) or HEXID.match(v) or PREFIXED.match(v))


def is_version(v):
    return isinstance(v, str) and bool(SEMVER.match(v))


def is_text(v):
    """Prose rather than a token. Predicted to look good and to be rejected for
    `empty`'s reason: a test that fires everywhere has answered nothing."""
    return isinstance(v, str) and len(v) >= 40 and v.count(" ") >= 2


CANDIDATES = {
    "number": is_number,
    "when": is_when,
    "packed!": is_packed_strict,
    "packed?": is_packed_naive,
    "id": is_id,
    "version": is_version,
    "text": is_text,
}


def summarise(name, per_doc, n_docs):
    """One row: coverage, then the discrimination numbers that decide it."""
    fired = {d: h for d, h in per_doc.items() if h}
    paths = sorted(len(h) for h in fired.values())
    vals = sum(sum(h.values()) for h in fired.values())
    if not paths:
        return f"  {name:<9} {0:>3}/{n_docs}  {'—':>7} {'—':>7} {'—':>9}"
    med = statistics.median(paths)
    return (f"  {name:<9} {len(fired):>3}/{n_docs}  {med:>7.0f} {max(paths):>7} "
            f"{vals:>9,}")


def main(check=False):
    docs = list(documents())
    print(f"{len(docs)} documents\n")

    shipped = {t: {} for t in TESTS}
    for entry, path in docs:
        for t in TESTS:
            shipped[t][entry] = cli(path, t)

    print("THE FOUR THAT EXIST — via the shipped binary")
    print(f"  {'test':<9} {'fires':>6}  {'med':>7} {'max':>7} {'values':>9}")
    for t in TESTS:
        print(summarise(t, shipped[t], len(docs)))

    # Per-document paths for the four, so a reader can see WHICH document is
    # doing the over-reporting rather than only that some document is.
    print("\n  paths per document, the four")
    print(f"  {'entry':<26} " + " ".join(f"{t:>7}" for t in TESTS))
    for entry, _ in docs:
        cells = " ".join(f"{len(shipped[t][entry]):>7}" for t in TESTS)
        print(f"  {entry:<26} {cells}")

    print("\nTHE CANDIDATES — via design/where.py, same fold, same documents")
    cand = {c: {} for c in CANDIDATES}
    for entry, path in docs:
        doc = load(path)
        if check:
            for t in TESTS:
                if where(doc, t) != shipped[t][entry]:
                    print(f"  !! {entry}/{t}: where.py disagrees with the binary")
        for c, fn in CANDIDATES.items():
            cand[c][entry] = where(doc, fn)
    print(f"  {'test':<9} {'fires':>6}  {'med':>7} {'max':>7} {'values':>9}")
    for c in CANDIDATES:
        print(summarise(c, cand[c], len(docs)))

    print("\n  paths per document, the candidates")
    names = list(CANDIDATES)
    print(f"  {'entry':<26} " + " ".join(f"{c:>7}" for c in names))
    for entry, _ in docs:
        cells = " ".join(f"{len(cand[c][entry]):>7}" for c in names)
        print(f"  {entry:<26} {cells}")

    # `date` against `when`: the documents where a time is present and the
    # shipped test does not find it. This is the sharpest single comparison
    # here, because it is a MISS rather than a preference.
    print("\n  where `when` finds a time and `date` finds nothing")
    for entry, _ in docs:
        d, w = len(shipped["date"][entry]), len(cand["when"][entry])
        if w and not d:
            print(f"    {entry:<26} date 0   when {w}")
    print("\n  where `when` finds strictly more paths than `date`")
    for entry, _ in docs:
        d, w = len(shipped["date"][entry]), len(cand["when"][entry])
        if d and w > d:
            print(f"    {entry:<26} date {d:<4} when {w}")


if __name__ == "__main__":
    main(check="--check" in sys.argv)
