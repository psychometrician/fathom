# Contributing to fathom

fathom is one Rust engine with thin R and Python packages over it. The rules
below are the ones most likely to be broken by accident, and each exists because
something went wrong once.

## The shape of the thing

```
fathom-core/     the engine — the walk, the fold, the classifier, the pricing
fathom-cli/      the single entry point both packages invoke as a subprocess
r-pkg/fathom/    the R package. No dependencies
py-pkg/fathom/   the Python package. No dependencies
design/          the ORACLE, and the instruments that read it
corpus/          thirty real JSON documents, graded the same way
test/            the six scorers. NOT the corpus
book/            the manual, which computes its numbers rather than quoting them
```

## `design/probe.py` is the oracle, and it is frozen

**The Rust core is *defined* as agreeing with `design/probe.py`.** A
disagreement is the core's fault by construction — that is what makes
`test/parity.py` a test rather than a comparison of two opinions.

The probe is committed at a recorded hash, and changing it is a deliberate event.
`git hash-object design/probe.py` must match what the project's record says, and
a check in CI compares them.

**Why it matters to a contributor:** if you change behaviour, you change the
probe *and* the core, and `parity.py` is what proves you changed them the same
way.

## A binding is not a place to put behaviour

Anything either package does beyond finding the engine and handing back its bytes
is a second implementation of the report — which is the thing this architecture
exists to prevent.

**And a binding may not parse JSON**, which is stronger than it sounds. Base R
cannot represent JSON's number range: `jsonlite` reads `9007199254740993` as
`…992` where Python's `json` is exact. A parser in each binding would make the
two languages disagree about exactly the value the health verb exists to warn
about. The document goes to the engine; the way to look inside a nested cell is
`into()`.

## The six scorers, and what each one is blind to

```bash
cargo build --release
uv run test/versions.py      # the three version declarations agree
uv run test/check.py         # the health verb, generated cases
uv run test/check.py --rust  #   ... and the core
uv run test/parity.py        # the core against the oracle, four stages
uv run test/pipe.py          # every verb against a reader that stops reading
uv run test/streaming.py     # the streaming read against the oracle
uv run test/candidates.py    # every row shape the menu NAMES, rebuilt
uv run test/bindings.py      # R and Python against the binary
```

**`bindings.py` is slow on purpose — do not trim it to make it quick.** It found
a 370× defect that nothing faster would have: a binding returning correct data
for 22 seconds on a table that fits in one line.

**Each of these is blind to something, and the blindness is the point of having
six.** `candidates.py` resolves the labels the menu *prints*, so a label the menu
fails to print is invisible to it — twice now, a missing candidate was found by a
separate instrument rather than by a scorer. `bindings.py` confirms the two
languages agree, which makes it blind by design to both agreeing and both being
wrong; that is why `fathom-test/versions.py` asks each binding and its engine for
a version directly.

**A skip is not a pass.** Where a check cannot run — a document over the size cap,
a table wider than any language can hold — it says so by name rather than
counting it green.

## Adding a word

The vocabulary is seven words and it is closed until something earns an eighth.
**A word belongs only if removing it makes one of the questions in
`QUESTIONS.md` unanswerable on at least one real corpus file** — and the question
and the file are both named when it is added. That is the stopping rule, and it
is why the list is fixed rather than growing.

A word that exists in one language is a broken promise rather than half a
feature: both bindings and `test/bindings.py` move together, in the same commit.

## The corpus takes real files only

Toy JSON is hard in ways nobody suffers from. Every entry has provenance with a
date, a measured number in every grading row that can carry one, and one attempt
file per tool in each language.

**A tool that cannot answer a question records that, with the reason.** "Cannot"
is the most useful cell in the grid and an empty cell is the least.

## Commits

- Say **what was found and why it matters**, not which files moved.
- Stage explicit paths. Never `git add -A`, `git add .`, or `git stash`.
- No `Co-Authored-By:` trailer.
- **A push to `main` republishes the R package** on r-universe, with no tag and
  no approval. There is no staging step between a commit here and what a new user
  installs. `.github/RELEASING.md` has the rest, including the six things that
  keep the r-universe checks clean.

## Before you open a pull request

Run the six scorers above. Then, if you touched either package, run the clean
room in the `fathom-test` bed — it installs the built artifacts with **no Rust
reachable**, no `FATHOM_BIN`, and no checkout, which is the only way to find out
whether a stranger can use what you changed.

## License

Apache 2.0. By contributing you agree your contribution is licensed under it.
