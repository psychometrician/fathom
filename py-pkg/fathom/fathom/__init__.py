"""The Python half of fathom. It is deliberately thin.

`design/implementation.md` decided one Rust core and two bindings that invoke a
binary and read a pipe — no FFI, no ABI, nothing compiled on a user's machine.
Everything intricate lives in `fathom-core`, so this module has no opinion about
JSON at all.

**THE TEST OF THIS MODULE IS THAT IT ADDS NOTHING.** `test/bindings.py` diffs
what `fathom()` returns against what the binary printed, byte for byte, on every
corpus document, and diffs it against the R binding at the same time. A binding
that reformats, re-wraps or re-encodes is a second implementation of the report,
which is the thing the architecture exists to prevent.
"""

from __future__ import annotations

import atexit
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

__all__ = [
    "read_json", "fathom", "into", "back", "find", "whichever", "rows",
    "binary", "Report", "View", "FathomError",
]

# Documents written from `text=` live until the process ends, which is the
# same lifetime R's session temp directory gives them.
_TEMPORARY: list[str] = []


@atexit.register
def _clean_temporary() -> None:  # pragma: no cover - process teardown
    for name in _TEMPORARY:
        try:
            os.unlink(name)
        except OSError:
            pass


class FathomError(RuntimeError):
    """The binary is missing, or it refused the document."""


class Report(str):
    """The printed description of a document.

    A `str` subclass, so `print(report)`, slicing, `in` and `.splitlines()` all
    work without anybody learning a new type — and its `repr` is the report
    itself, so a REPL or a notebook shows the page rather than
    `<Report object at 0x…>`.

    **That is the same behaviour as the R binding**, where `fathom(f)` at the
    console auto-prints and `x <- fathom(f)` is silent. `design/vocabulary.md`
    requires R and Python to differ by the PIPE alone, so an eager `print()`
    here would be a second difference — and at a REPL it would print twice.
    """

    __slots__ = ()

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return str(self)


# What the engine is called here. `setup.py` decides the same thing for the same
# reason and the two have to agree: that is the name the wheel packs, and this is
# the name that looks for it. A Windows wheel built under one spelling and read
# under the other installs perfectly and then cannot find the engine it carries.
_EXE = "fathom.exe" if os.name == "nt" else "fathom"


def binary(error: bool = True) -> str | None:
    """Locate the fathom engine.

    Four places, in order, and **the R binding resolves the same way** — the
    order is a contract between the two, not a preference of either.

    An explicit override always wins. A DEVELOPMENT BUILD outranks the bundled
    copy, because the engine inside a wheel is exactly as old as that wheel;
    preferring it is how a harness spends a day measuring a stale engine while
    every check passes. The bundled engine is the installed package's own
    answer. The `PATH` is last: a `fathom` on it has no reason to match this
    copy of the binding.
    """
    override = os.environ.get("FATHOM_BIN", "")
    if override:
        # An override that does not exist is an error rather than a fallback. It
        # was set on purpose, and quietly running a different binary than the
        # one asked for is how a measurement gets attributed to the wrong build.
        if not Path(override).is_file():
            raise FathomError(
                f"FATHOM_BIN is set to a file that does not exist: {override}"
            )
        return override

    dev = _dev_binary()
    if dev is not None:
        return str(dev)

    # **This is what makes an installed copy self-contained**, and nothing else
    # in the package ever creates that file: `setup.py` puts it there while the
    # wheel is built. Without this branch the lookup falls through to a
    # development checkout, which is fine on the machine that built it and
    # useless anywhere else.
    bundled = Path(__file__).resolve().parent / "bin" / _EXE
    if bundled.is_file():
        return str(bundled)

    installed = shutil.which(_EXE)
    if installed:
        return installed

    if not error:
        return None
    raise FathomError(
        "cannot find the `fathom` engine. It is looked for in four places:\n"
        "  1. $FATHOM_BIN, if set\n"
        "  2. target/release/fathom, in this directory or any above it\n"
        "  3. bundled inside the installed package\n"
        "  4. `fathom` on your PATH\n"
        "An installed package carries its own engine. In a checkout, build one "
        "with `cargo build --release` from the project root, or set FATHOM_BIN "
        "to a copy you already have."
    )


def _dev_binary(start: Path | None = None) -> Path | None:
    """Walk UP from the working directory looking for a cargo build.

    The same trick `uv run` uses, and for the same reason: attempts and scripts
    in this project are run from deep subdirectories, so anything resolved
    relative to the caller has to search upward or it works only from the root.
    Resolving it relative to the INSTALLED package would be wrong in the other
    direction — once installed there is no project above it, which is exactly
    when PATH is the right answer.
    """
    here = (start or Path.cwd()).resolve()
    for directory in (here, *here.parents):
        candidate = directory / "target" / "release" / "fathom"
        if candidate.is_file():
            return candidate
    return None


class View:
    """A source, and where you are standing in it.

    A view cannot hold the parsed document — that lives in the core and ends
    with the call — so it holds the source and a path. That is what makes
    `into()` and `back()` free, and what makes a chain possible at all.
    """

    __slots__ = ("source", "at", "health")

    def __init__(self, source: str, at: tuple[str, ...], health: str) -> None:
        self.source, self.at, self.health = source, at, health

    def __repr__(self) -> str:
        where = "$." + ".".join(self.at) if self.at else "$"
        return f"<view {where}>\n  {self.health}"

    def __rshift__(self, verb):
        """The pipe. `design/vocabulary.md` requires R and Python to differ by
        this and nothing else, so `>>` here does what `|>` does there: hand the
        view to the next word."""
        return verb(self)


def _view_of(x: object) -> View:
    """Every verb takes either a view or a bare path.

    A bare path becomes a view WITHOUT running the health check, because
    `fathom()` is about to report soundness anyway and paying twice would be the
    one waste this design set out to avoid.
    """
    if isinstance(x, View):
        return x
    if not isinstance(x, (str, os.PathLike)):
        raise FathomError("give a path or a view from `read_json()`")
    file = Path(x)
    if not file.exists():
        raise FathomError(f"no such file: {file}")
    return View(str(file), (), "")


def _source_of(x: object) -> str:
    return _view_of(x).source


def _at_args(v: View) -> list[str]:
    """`--at name` once per name. The binding never resolves anything: it hands
    the core the names in order and the core decides what each one means."""
    return [a for name in v.at for a in ("--at", name)]


def into(name: str):
    """Go into a part of the document.

    Does not read anything — a view is a source and a path, so navigating is
    list arithmetic and costs nothing until you ask a question.

    **Going in is how you make the expensive question cheap.** The walk, the
    fold, the classifier and the pricing all run on what you are standing on:
    measured, standing in one part of an 18 MB document is 66x faster than
    describing the whole of it.

    **It is also how you look inside a nested cell**, because `rows()` hands
    nested values back as JSON text rather than parsing them — a parser in the
    binding would be a second implementation, and the two languages' parsers do
    not agree.
    """
    if not isinstance(name, str):
        raise FathomError("`name` must be a single name to go into")

    def go(view: View) -> View:
        v = _view_of(view)
        return View(v.source, v.at + (name,), v.health)

    return go


def back():
    """Come back out one level."""

    def go(view: View) -> View:
        v = _view_of(view)
        if not v.at:
            raise FathomError(
                "already at the top of the document; there is nowhere to go back to"
            )
        return View(v.source, v.at[:-1], v.health)

    return go


# `find` and `rows` tell the two forms apart by ARITY, and `whichever` by TYPE.
#
# **Never by guessing whether a string is a path.** The first draft did, with
# `Path(x).exists()`, and it read a COLUMN NAME as a file the moment a document
# had a column called `test` and the test ran from the repository root. That is
# the same "a string that might be either" wart `read_json` avoids with named
# arguments, reappearing where a heuristic replaced them.
#
# The direct/chain distinction exists only in Python, because `>>` needs a
# callable where `|>` passes its left side. That IS the pipe difference the
# design allows, and it is the whole of it.


def _tsv_verb(v: View, argv: list[str]) -> list[dict[str, str]]:
    """Every table-returning verb reads the same way: run the binary with
    --tsv, and read what it printed. Splitting on the tab rather than using
    `csv`, because every cell is a JSON value so none can contain one."""
    exe = binary()
    assert exe is not None
    done = subprocess.run([exe, *argv, "--tsv", *_at_args(v)], capture_output=True)
    if done.returncode != 0:
        detail = done.stderr.decode("utf-8", "replace").strip()
        raise FathomError(
            detail or f"the fathom binary exited with status {done.returncode}"
        )
    text = done.stdout.decode("utf-8")
    lines = [ln for ln in text.split("\n")]
    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return []
    names = lines[0].split("\t")
    # Same rule as `rows`: absent is None, `null` is the four characters, and
    # every row carries every column.
    return [
        {n: (val if val != "" else None) for n, val in zip(names, ln.split("\t"))}
        for ln in lines[1:]
    ]


def find(x=None, test: str | None = None):
    """Find every path whose value matches. It answers *where*.

    Paths come back FOLDED, with a count: the unfolded answer on a real document
    is thousands of rows, which is the cost-proportional-to-data failure this
    project exists to name, committed by fathom's own word. **A word that
    answers a question by printing the data has not answered it.**

    The test is a NAME — `url`, `email`, `date`, `empty` — and not a function.
    A function cannot cross a subprocess boundary, and could not be the same
    function in both languages if it did. A regular expression would need a
    regex engine in a core that has one dependency on purpose.
    """
    if test is None:
        # The chain form: `v >> find("url")`. One argument can only be the test,
        # because a search always needs one.
        if not isinstance(x, str):
            raise FathomError('`test` must be one of "url", "email", "date", "empty"')
        label = x
        return lambda view: find(view, label)
    if not isinstance(test, str):
        raise FathomError('`test` must be one of "url", "email", "date", "empty"')
    v = _view_of(x)
    return _tsv_verb(v, ["where", v.source, test])


def whichever(*args):
    """The first of these names that is actually there, per thing.

    Path variance, plainly: a document that spells the same field `Rating` in
    some records and `rating` in others is answered by asking for both. A null
    counts as absent, because a field that is present and null has not told you
    anything.
    """
    if args and isinstance(args[0], View):
        v, names = args[0], [str(a) for a in args[1:]]
        if not names:
            raise FathomError("give at least one name to try")
        return _tsv_verb(v, ["whichever", v.source, *names])
    names = [str(a) for a in args]
    if not names:
        raise FathomError("give at least one name to try")
    return lambda view: whichever(view, *names)


def read_json(
    source: str | os.PathLike[str] | None = None,
    text: str | None = None,
) -> View:
    """Read a JSON source, and say whether it is sound.

    The first word. Everything else takes what this returns.

    **It reports damage rather than raising on it.** A truncated file gives you
    a view that says so; it does not throw. `fathom()` on that view still prints
    the full diagnosis with the parser's line and column. Refusing would replace
    a good report with a worse exception.

    Checking costs about 1% of a `fathom()` — a parse is 0.05s on 18 MB, where
    describing the same document is 4.7s — so soundness is answered up front and
    the expensive question is asked only when you ask it.

    Give exactly one of `source` (a path) or `text` (a JSON document already in
    memory). Named rather than guessed, because a string that might be either is
    the wart every other reader has.
    """
    if (source is None) == (text is None):
        raise FathomError(
            "give exactly one of `source` (a path) or `text` (a JSON string)"
        )

    if text is not None:
        if not isinstance(text, str):
            raise FathomError("`text` must be a single string")
        # The core reads files, so a document already in memory is written to
        # one. Handing bytes to a subprocess is plumbing, not behaviour.
        handle, name = tempfile.mkstemp(prefix="fathom-source-", suffix=".json")
        with os.fdopen(handle, "wb") as f:
            f.write(text.encode("utf-8"))
        _TEMPORARY.append(name)
        path = name
    else:
        path = _source_of(source)

    # The health line as TEXT, not as JSON. A binding that parsed JSON would be
    # a second parser, and the two languages' parsers do not agree.
    exe = binary()
    assert exe is not None
    done = subprocess.run([exe, "health", path], capture_output=True)
    health = (
        done.stdout.decode("utf-8", "replace").strip()
        if done.returncode == 0
        else "could not be read"
    )
    return View(path, (), health)


def fathom(path: str | os.PathLike[str] | View | None = None):
    """Describe a JSON document.

    Reads a JSON, NDJSON or gzipped file and returns what is in it: whether it
    is sound, the shapes it holds folded to their structure, the fields that
    change type, and what one row could be with every candidate priced.

    The output is proportional to the STRUCTURE, not to the data. That is the
    whole claim, and it is why this is worth running on a file too large to
    open.
    """
    if path is None:
        return fathom  # `v >> fathom()` and `v >> fathom` both work
    v = _view_of(path)

    exe = binary()
    assert exe is not None  # `binary()` raises rather than returning None here

    done = subprocess.run(
        [exe, "probe", v.source, *_at_args(v)],
        capture_output=True,
    )
    if done.returncode != 0:
        detail = done.stderr.decode("utf-8", "replace").strip()
        raise FathomError(
            detail or f"the fathom binary exited with status {done.returncode}"
        )

    # Decoded exactly, and never re-wrapped. The report's column widths and its
    # wrap at 92 characters are load-bearing: `design/coverage.py` reads the
    # page back as a set of claims and tells a shape header from a continuation
    # line by indentation alone.
    return Report(done.stdout.decode("utf-8"))


def rows(path=None, candidate: str | None = None):
    """Take a table out of a JSON document.

    `fathom()` prints a menu under `ONE ROW COULD BE`, with every candidate
    priced. `rows()` takes one of those labels, verbatim, and returns that
    table. The label is the whole argument — you are not guessing at a path,
    you are naming a row shape the report just showed you and priced.

    Every cell holds a JSON value, as text: a string arrives quoted, a number
    bare, a nested array or object as JSON. That is deliberate. 17 of 19 corpus
    extracts carry a column whose values are nested, and fathom hands one to you
    intact rather than flattening it behind your back. `json.loads` the columns
    you care about.

    **A missing key means the field was ABSENT. A cell reading `null` means the
    field was there and null.** Those are different and this keeps them apart.

    **The same bytes reach R**, which has no JSON parser in base and therefore
    no way to read NDJSON without a dependency. `test/bindings.py` asserts the
    two languages return the same rows.
    """
    if candidate is None:
        # The chain form: `v >> rows("an entry of versions")`. One argument can
        # only be the label, because a table always needs one.
        label = path
        if not isinstance(label, str):
            raise FathomError("`candidate` must be one label, as the report printed it")
        return lambda view: rows(view, label)
    v = _view_of(path)
    if not isinstance(candidate, str):
        raise FathomError("`candidate` must be one label, as the report printed it")

    exe = binary()
    assert exe is not None

    done = subprocess.run(
        [exe, "rows", v.source, "--candidate", candidate, "--tsv", *_at_args(v)],
        capture_output=True,
    )
    if done.returncode != 0:
        detail = done.stderr.decode("utf-8", "replace").strip()
        raise FathomError(
            detail or f"the fathom binary exited with status {done.returncode}"
        )

    # Split on the tab, and NOT with the `csv` module. Every cell is a JSON
    # value, so no cell can contain a raw tab or a raw newline — that is what
    # encoding them bought, and it makes the delimiter unambiguous without any
    # quoting rules to agree on.
    #
    # `csv` was the first draft and it FAILED on `02-hn-thread`: its default
    # field-size limit is 131,072 characters and one nested cell is the whole
    # thread. R's `read.delim` read the same bytes without complaint, so the two
    # languages disagreed — the one thing this architecture exists to prevent.
    # Raising the limit would have been a global mutation in a library; not
    # needing a limit is better.
    #
    # Decoding a declared wire format is the only thing a binding may do.
    # Reshaping or re-typing would be a second implementation.
    text = done.stdout.decode("utf-8")
    if not text:
        return []
    lines = text.split("\n")
    if lines and lines[-1] == "":
        lines.pop()
    if not lines:
        return []
    names = lines[0].split("\t")
    # An absent cell is an EMPTY FIELD and arrives as None; a cell holding JSON
    # `null` is the four characters "null" and survives as itself. Both are
    # kept, so every row carries every column.
    #
    # **The key is NOT dropped**, which an earlier draft did on the grounds that
    # it showed the reader the same ragged edge the document has. It also lost
    # the COLUMN: a `whichever` that matches nothing returned rows with no
    # `value` key at all, so Python could not tell the column had ever existed
    # while R showed it empty. `test/bindings.py` caught the two languages
    # disagreeing about it.
    return [
        {n: (v if v != "" else None) for n, v in zip(names, line.split("\t"))}
        for line in lines[1:]
    ]
