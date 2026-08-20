# What a push does, and how a release is cut

fathom ships to two places and they behave very differently. **One of them
releases on every push and the other cannot release without a tag and a human.**

| | registry | what starts it | can it be undone |
|---|---|---|---|
| **R**, as `fathom` | r-universe | **any push to `main`** | the build, yes; a number a user already installed, no |
| **Python**, as `fathom-json` | PyPI | a `py-v*` tag, then approving an environment | **no** |

## A push to `main` cannot publish a wheel

`python-wheels.yml` builds five wheels on a push and uploads them as artifacts.
It has no PyPI credential and no `id-token` permission, so there is nothing it
could upload with. Only `python-release.yml` publishes, only a `py-v*` tag starts
it, and its last job waits on a reviewer.

## A push to `main` DOES republish the R package

r-universe clones this repository, runs `r-pkg/fathom/.prepare`, builds
`r-pkg/fathom` for every platform, and serves the result. There is no tag and no
approval.

**And it rebuilds at exactly the version in `DESCRIPTION`, replacing the previous
build at the same number.** So while `DESCRIPTION` says `0.0.1`, every push
changes what a new user installs while `update.packages()` reports nothing to do
— it compares numbers, and `0.0.1` is not newer than `0.0.1`. Two people can both
hold "0.0.1" and have different code, with no way to tell.

**The R convention that fixes this is the fourth component**, `0.0.1.9000`,
`.9001`, which r-universe is built around. Adopting it means letting `DESCRIPTION`
drift from the other two declarations, which `test/versions.py` currently
forbids. **That decision is open and should be made deliberately rather than by
drift.** It is the same one the sibling records as unmade.

## Keeping r-universe at 8 OK, 1 FAIL

**That is the target and it is achievable: eight platforms OK, and one expected
FAIL.** Both siblings sit at WARNING on their eight; fathom reached clean on
2026-08-20 and the things that got it there are easy to undo by accident, so they
are listed.

| what | why it matters |
|---|---|
| **`.prepare` does NOT vendor by default** | `cargo vendor` writes `.cargo-checksum.json` and `.cargo_vcs_info.json` beside each of the six crates — twelve dotfiles that `R CMD check` reports as hidden files. That was one NOTE on every platform, which the page rendered as **7 NOTE**. Turn vendoring on only with `FATHOM_VENDOR=1`, and only for a CRAN submission that needs an offline build |
| **`.prepare` deletes `inst/bin` before staging** | otherwise a tarball built from a tree that was installed once carries the engine, and the check reports an undeclared executable — a WARNING |
| **`Title:` is in R's title case, has no trailing period, and does not start with `fathom`** | all three are separate check complaints. `toTitleCase` treats short words like *is* as minor and wants them lowercase; the card renders `fathom - <Title>`, so a Title beginning with the package name reads the name twice |
| **`man/figures/logo.png` exists** | not a check, but it is what puts the hex on the page. r-universe reads that path and nothing else |
| **`r-pkg/fathom/README.md` exists** | r-universe renders the PACKAGE readme. Without one it falls back to the repository README, which is not written for somebody installing a package |
| **GitHub repo topics are set** | the tags on the card are the repository's topics. Unset, r-universe shows only `rust` and `cargo`, which it derives from `Cargo.toml` and which say nothing about what fathom does |

**`wasm-release` FAILs on purpose and must not be "fixed".** `configure` refuses
a WebAssembly host up front, because R compiled to WebAssembly cannot start a
subprocess and this package answers by running the engine as one. There is no
engine that could be bundled for that target, so an install which appeared to
succeed would produce a package that cannot describe anything. gog fails the same
job for the same reason.

**Two complaints appear locally and never on r-universe**, so do not chase them:
`checkbashisms` is not installed on most developer machines, and *checking CRAN
incoming feasibility* is a CRAN check that r-universe does not run.

**Check the result rather than assume it**, because a push republishes without
asking:

```bash
curl -s https://psychometrician.r-universe.dev/api/packages/fathom |
  python3 -c "import json,sys;from collections import Counter;d=json.load(sys.stdin);\
print(dict(Counter(j['check'] for j in d['_jobs'])))"
```

## The three declarations

The version is written by hand in three files and CI never assigns it:

```
Cargo.toml                     [workspace.package] version
r-pkg/fathom/DESCRIPTION       Version:
py-pkg/fathom/pyproject.toml   [project] version
```

`uv run test/versions.py` checks they agree, and checks that Python's
`description` is R's opening sentence — the two prose fields drift as easily as
the numbers, and did: R's said *"One verb"* for days after the vocabulary reached
seven words.

The release workflow re-checks the same three against the tag, **before anything
is built**, because a number spent on a failed release is spent for good.

## Before the first automated release

Two GitHub Environments must exist, and their rules are the gate on the
irreversible step: **`pypi` with a required reviewer, `testpypi` open.**

The other half of the handshake lives on PyPI and has to be set up through their
websites. It is invisible from this repository, and its absence looks like a
green build that fails on its last step.

| Where | What to register |
|---|---|
| pypi.org → publishing → add a **pending publisher** | project `fathom-json`, owner `psychometrician`, repo `fathom`, workflow `python-release.yml`, environment `pypi` |
| test.pypi.org → the same | project `fathom-json`, owner `psychometrician`, repo `fathom`, workflow `python-release.yml`, environment `testpypi` |

A *pending* publisher is the form to use for a name that has never been
published: it creates the project on first upload. Once `fathom-json` exists, the
same settings live under the project itself.

**Do not rename `python-release.yml`.** A trusted publisher binds to the
filename, so a rename silently invalidates it.

## Cutting a release

1. **Decide the number.** It is never chosen for you. While the series stays at
   `0.0.x`, every release reads as breaking to every resolver — which is what
   `0.0.x` means, and is a reason to move to `0.1.0` when the words settle.

2. **Write it into all three declarations**, in one commit, and run
   `uv run test/versions.py`.

3. **Check the tree before spending a number:**

   ```bash
   cargo build --release && uv run test/parity.py
   uv run test/versions.py
   uv run test/candidates.py
   uv run test/bindings.py
   ```

   Then, in `fathom-test`, against artifacts built from *this* tree:

   ```bash
   python3 versions.py        # the bindings and their engines agree
   python3 clean_room.py      # no Rust, no FATHOM_BIN, no checkout
   ```

4. **Push.** This republishes the R package immediately. There is no later chance
   to correct the tarball r-universe compiles from, so the tree must already be
   the one you mean to ship.

5. **Tag, for Python only:**

   ```bash
   git tag py-v0.0.1 && git push origin py-v0.0.1
   ```

6. **Watch the rehearsal, then approve.** Four jobs run unattended; `pypi` waits
   on the environment's reviewer. Read the TestPyPI job before approving — it is
   the last place a metadata problem is free.

## What cannot be taken back

- **A PyPI version.** The number is spent whether or not the upload was what you
  meant. `fathom-json 0.0.1` can be *yanked*, which hides it from resolvers, but
  it can never be re-uploaded.
- **A version a user has installed.** r-universe replacing a build does not reach
  anyone who already has it, and at `0.0.x` with no fourth component they cannot
  ask for the newer one.
- **A tag that has been pushed**, in practice: deleting it does not un-run the
  workflow it started.

## What needs no version at all

The book. `book.yml` republishes it on every push, so prose, examples and
corrections reach readers immediately without a release. That covers a large
share of what would otherwise feel like a patch.
