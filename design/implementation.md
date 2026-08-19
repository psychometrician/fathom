# How fathom would be built, if it is built

**Recorded 2026-08-08 as a decision pending evidence.** Phase 2 has not been
earned and this document does not open it. It exists because the question was
asked while the answer was cheap, and because a decision taken later under
pressure is taken worse.

---

## The decision

> **One Rust core, one CLI, and thin R and Python packages that invoke it as a
> subprocess. No FFI.**

This is god's architecture, unchanged.

## What god actually does, measured 2026-08-08

Worth writing down, because the obvious guess is wrong. god is **not** bound
through extendr or PyO3.

| | |
|---|---|
| `god-core` | 12,342 lines of Rust across 19 files |
| `god-cli` | the single entry point |
| `r-pkg/god` | calls `system2()`, with `configure` and `configure.win` |
| `py-pkg/god` | calls `subprocess.run()`, ships the binary at `god/bin/god-cli` |
| `parity/` | the same corpus written as `corpus.god`, `corpus.R` and `corpus.py`, diffed by `check.py` |

gog goes further off one core — `gog-core`, `gog-cli`, `gog-wasm`, `jl-pkg`,
`js-pkg` — which is the evidence that this scales past two targets.

**So the hard part of shipping Rust to CRAN has already been solved once in this
household.** That is the largest single cost of this decision, and it is paid.

## Why it fits fathom

**One implementation of the part that drifts.** The walk, the fold, the
keys-as-data classifier and the row pricing are intricate, and today they changed
three times in two hours. Two hand-written copies would diverge, and
`CLAUDE.md` already names invisible drift as the danger with a word shared
between projects. One core makes divergence impossible rather than merely
tested-for.

**Parity becomes almost free.** god's `parity/` exists because a sentence has to
mean the same thing in both bindings. With one core and subprocess wrappers,
both languages run identical code, so the only thing left to test is rendering.
That is a much smaller harness than god needs.

### `design/fathom.R` is scaffolding and gets DELETED at port time

**Added 2026-08-09, because without it a later session would mistake that file
for the beginning of the R package, which is the opposite of this decision.**

`design/fathom.R` is a hand-written R re-implementation of the path language,
`rows`, `first_present` and `take`. It is exactly the "second hand-written copy"
the paragraph above rules out, and it is written on purpose, once, to answer a
question the Rust core **cannot**:

> One core makes the two languages agree by construction. That proves the
> plumbing. **It cannot tell you whether the vocabulary is right** — if
> `rows("versions.*")` reads naturally in Python and awkwardly in R, a shared
> core delivers the awkward reading to R users faithfully and forever. The port
> does not test that assumption, it locks it in.

The only way to test it is to have the words re-derived from the written notation
by another route and see whether they land in the same place.
`design/parity.py` reported **11 of 11 sentences agreeing** on row counts and
captured keys, 2026-08-09. That is the assumption checked before it is frozen
into an architecture.

**At port time:**

| | |
|---|---|
| `design/fathom.R` | **deleted.** Its job is finished the moment the core exists |
| `design/parity.py` | **kept and retargeted** from *two implementations* to *two bindings of one core*, which is what god's `parity/` already is |

**The distinction the decision rests on:** two hand-written copies must never be
*shipped*, because they drift invisibly. Writing one as a probe and throwing it
away costs nothing and buys the one piece of evidence the architecture assumes.

**No FFI toolchain, per language, forever.** No ABI compatibility, no compiling
on a user's machine, no maturin, no extendr. A binary and a pipe.

**The probe is subprocess-shaped by nature.** You are not passing live R objects
back and forth; you are asking "describe this file" and getting a small answer.
FFI would buy nothing here.

**Performance is genuinely in scope, unlike for a grammar.** god compiles to SQL
and lets the database do the work. fathom *is* the work — walking a 10 GB NDJSON
file, deciding truncation without loading it, streaming. That belongs in
`serde_json` or `simd-json`, not in R.

## Where fathom differs from god, and it matters

**god never ships a large table across the boundary.** It emits SQL and the
engine does the rest, so a pipe carrying a few KB is always enough. **fathom's
extract half would ship data**, and a large data frame through stdout is the one
place this architecture strains.

So the boundary is two-shaped:

| call | crosses as |
|---|---|
| **probe** | the rendered report on stdout |
| **extract** | **TSV on stdout, every CELL a JSON value** — `rows --candidate <label> --tsv` |

> **DECIDED 2026-08-13, and it replaces a proposal that was never measured.**
> This table used to read *"Arrow IPC to a file or pipe"*, with the note *"Arrow
> rather than FFI keeps the no-linking property intact"* and **Marked
> undecided**. It stayed undecided for two days and blocked `rows()` in both
> bindings the whole time.

### Why Arrow was REJECTED

**The no-linking claim is true of the core and false of the bindings**, which is
where the reading happens. Arrow fails every clause of the dependency policy
written in `Cargo.toml`:

| the policy | Arrow |
|---|---|
| one runtime dependency, `flate2`, pure Rust, six packages in `Cargo.lock` | `arrow-rs` pulls `chrono`, `half`, `num`, `hashbrown`, … |
| *"vendors without argument for CRAN"* | it does not |
| *"No compiling on a user's machine"* | R's `arrow` needs libarrow; Python needs `pyarrow` |
| **both bindings have ZERO dependencies** | Arrow puts one in each |

### Why TSV-of-JSON-cells, and not NDJSON

NDJSON was the obvious choice and `--ndjson` ships as well, because it is the
right thing for a pipe into `jq`. **It cannot be the binding format, and the
first reason recorded here was the weak one.**

The weak reason: base R has no JSON parser, so an R binding reading NDJSON would
need `jsonlite`.

> ### THE REAL REASON: A BINDING THAT PARSES JSON IS A SECOND PARSER
>
> The architecture's promise is *one core, so the languages agree by
> construction*. **A JSON parser in each binding is two implementations of the
> one thing the core exists to do**, and they do not agree. Measured
> 2026-08-13 on a document with an integer past 2^53:
>
> | | `9007199254740993` | `123456789012345678901234567890` |
> |---|---|---|
> | the core emits | exact | exact |
> | Python `json.loads` | 9007199254740993 | 123456789012345678901234567890 |
> | R `jsonlite` | **9007199254740992** | **1.2345678901234568e+29** |
>
> **`rows()` would return different numbers in the two languages for the same
> document** — and on exactly the class of value the health verb exists to
> report, and one of the four reasons the JSON parser here is hand-written
> rather than `serde_json`.
>
> So cells cross as **TEXT**, byte for byte as the core wrote them, and neither
> binding interprets them. Text is the only form both languages carry through
> unchanged.
>
> **This is what makes `into()` load-bearing rather than a convenience.** The
> way to look inside a nested cell is to navigate into it with the core —
> `into("keywords") |> rows()` — not to parse the string. The chain is how a
> user reaches depth without a second parser existing anywhere.

TSV where every cell is a JSON value is read by `read.delim` in R and by
`str.split` in Python, **with no dependency on either side**, and it buys three
things that are worth stating:

1. **The delimiter is safe without quoting rules.** A JSON-encoded value cannot
   contain a raw tab or newline, so there is nothing for the two languages to
   disagree about.
2. **Absent and null stay apart.** An empty field means the cell was ABSENT; the
   four characters `null` mean it was there and null. Four defects in this
   project have turned on that difference.
3. **A nested cell crosses intact**, which decides the flattening question
   below.

### The flattening question, decided by the same choice

**17 of 19 corpus extracts carry a list-column** and `design/extract.py` recorded
that *"the two halves of this repository's stated chain — fathom → god — do not
currently meet."* The wire format answers it: **a nested cell crosses as its
JSON, and `rows()` may return a table containing one.**

`README.md` already says what that means and needs no change — an extract may be
any shape, the rectangular ones flow onward into god, and non-rectangular
extracts are terminal. **No `hoist` is needed at the exit and nobody has to own
it.** The user parses the column they care about, with whatever they already use.

> **Picking the transport picked the flattening policy.** The two open decisions
> were one decision seen from two ends, and no document said so.

### A closed reader is `head`, not a failure — decided 2026-08-15

**Picking a transport picked one more thing: what happens when the far end stops
reading.** `--ndjson` exists for a pipe into `jq`, and a `jq` that has seen
enough closes the pipe — as do `head` and `less`. Rust ignores SIGPIPE at
startup, so that arrives as a write error, and `println!` unwraps it into a
panic.

**The rule: every stdout write goes through one helper, and a failed write exits
0.** Not an error, not 141, and no message — the reader asked to stop and there
is nobody left to tell.

**Restoring the default SIGPIPE disposition is the conventional Unix answer and
it was rejected here**, for a reason specific to this binary rather than a
general one. `SIG_DFL` kills the process at the write, so the two row writers'
existing handlers — which return normally, exit 0, and carry a comment saying
why — would become unreachable, and `rows --ndjson | head` would exit 141 where
it exits 0 today. **A repair that makes a committed decision unreachable is not
a repair.** It also wants `unsafe` and a raw `extern "C"` or a `libc`
dependency, against a `Cargo.toml` that spends twenty lines justifying its
single one.

> **The cost, stated so it is not mistaken for free.** Under `set -o pipefail` a
> shell cannot distinguish fathom stopping because its reader left from fathom
> finishing. That is the same trade `ripgrep` makes and the opposite of the one
> `bat` makes; both ship. The deciding argument was internal consistency, not
> convention.

`FINDINGS.md` 2026-08-15 owns the measurements, including why `probe` never
panicked and `where --tsv` did.

### The strain was measured rather than assumed

The claim above — *a large data frame through stdout is where this architecture
strains* — was written before the extract half had any design. Measured on
2026-08-13 across the corpus:

| | |
|---|---|
| worst case, `29-mdn-browser-compat` `an entry of api.*` | **154,551,447 cells**, 13.3 MB out |
| emitting it | **3.50s**, against **3.45s** to print the shape line alone |
| peak RSS | **685 MB**, which is the parsed document either way |

**Writing 13.3 MB of rows costs 0.05 seconds on top of a parse that had to happen
anyway.** Stdout does not strain, and `--out <file>` was predicted unnecessary
and proved unnecessary. `design/transport-predictions.md` holds the predictions,
committed before a single row was emitted.

### The payload size is a test of the thesis

The probe's summary is a few KB whatever the document weighs — that is what
"output proportional to the structure" *means*, expressed as an API contract. If
the core ever needed to return something proportional to the data, subprocess
would be the wrong boundary **and the project's central claim would be false at
the same moment.** Worth watching, because it fails loudly.

## Why not yet

**Today is the argument.** The classifier went from one signal, to a key-count
fallback, to a conjunction of two signals, inside two hours. The defect that took
the output from 1,239 lines to 73 was found only by running it. None of that
happens at the speed it needs to through a compile step and two packaging layers.

> **Prototype in the host language. Port when the design stops moving.**

**The gate**, stated so it is testable rather than a feeling:

> **Port to Rust when the probe's output stops changing across three consecutive
> corpus files.**

**THE GATE IS CLOSED, 2026-08-09.** Files **17-openlibrary**,
**18-openfda-events** and **19-chicago-salaries** each ran cold against
`981a45f0…` and none required a repair. The counter had never previously got
past one.

**All three were chosen to be ORDINARY, and that rule is part of the result.**
`14-nyc-311` established it: a document picked to break the newest constant is
guaranteed to find something and therefore cannot measure convergence. Choosing
easy files to close a counter would be the same error in the other direction, so
they were picked as representative documents — a search result, a deeply nested
regulatory record, a flat municipal payroll — and two of the three contradicted a
prediction made in advance.

*The earlier state, kept because the contrast is the evidence:* the counter was
reset to zero on the same day, when files 05, 06 and 07 each changed the probe —
05 added the partition operation, 06 added positional alignment, 07 found the
two-definitions-of-emptiness defect.

> **Closing the gate is not earning Phase 2**, and `VERDICT.md` owns that
> distinction. The gate says the design held still for three unseen documents.

### A second reason to port, measured 2026-08-09, and it narrows the first

The architecture argument above is about distribution. This one is about memory,
and it says something the architecture argument does not: **speed is not the
problem and a faster parser will not fix it.**

50 MB of NDJSON, 37,883 records, each in a clean process:

| | time | peak RSS |
|---|---|---|
| `json` (stdlib) | 0.27 s | 372 MB |
| `orjson` | 0.11 s | 330 MB |
| `ujson` | 0.15 s | 389 MB |
| `ijson`, streaming | — | **71 MB** |
| DuckDB | — | 133 MB |
| **`design/probe.py`** | — | **968 MB, on a 20,000-record SAMPLE** |

**A 2.5× faster parser bought 11% of the memory, and `ujson` used *more* than the
standard library.** All three build the same Python object graph and that is
where the bytes are. `json.loads` materialises all 37,883 records in 372 MB while
the probe needed 968 MB for 20,000 — so most of the probe's footprint is its own
bookkeeping, not the document.

### This argument was QUALIFIED TWICE on 2026-08-09, and the headline number did not survive

**The 18.8× multiplier is about `04-gharchive`'s record shape, not about JSON.**

| | bytes | records | depth | peak RSS | multiplier |
|---|---|---|---|---|---|
| `04-gharchive` | 50 MB | 20,000 sampled | 7 | **968 MB** | 18.8× |
| `14-nyc-311` | 28.1 MB | **20,000** | **4** | **229 MB** | **8.2×** |

**Same record count, half the multiplier, and the variable that moved is depth.**
The cost is per Python object built, and a flat record builds far fewer than a
nested one.

**And below about 10 MB the multiplier means nothing at all.**
`15-github-issues` at 702 KB cost 84 MB; `18-openfda-events` at 2.87 MB cost
92.7 MB. **Roughly 80 MB is the interpreter-and-pandas floor**, so openFDA's
marginal cost is about 9 MB. Reporting 32× would be arithmetically true and
completely misleading.

> **What survives is the direction, not the size.** Building a Python object per
> record is the expensive thing, and a Rust core avoids it. What does not survive
> is quoting 18.8× as though it were a property of the tool: it is a property of
> that document, measured on one file, and the corpus now has better numbers.

**So the honest case for porting is distribution and one implementation of the
part that drifts** — the argument at the top of this document — with memory as a
real but smaller supporting reason than it looked on 2026-08-08.

> **The win a core would deliver is not parsing faster. It is never handing the
> host language a per-record object graph.** `ijson` reaches 71 MB in pure Python
> by streaming and DuckDB 133 MB by keeping values on its own side. A Rust core
> that parses at 2 GB/s and then returns 37,883 dicts to Python inherits the
> 372 MB floor and most of the problem.

**Confirmed independently the same day.** pythonspeed.com's *Faster Python JSON
parsing* measures a ~25 MB file at `json` 136 MB, `orjson` 114 MB, `ijson` **14
MB**, `msgspec` 39 MB, and concludes the bottleneck is unnecessary object
instantiation. That is the paragraph above, reached from different data.

**And it names the one option a describer cannot take.** `msgspec` gets its
memory by *"defining schemas for only the fields you need"* — building nothing for
fields you will not read. **A describer does not know the fields; finding them is
question 1.** The saving is bought with the answer. This is the memory-shaped
version of the pydantic replies in the r/PythonLearning thread, and it means the
floor for a describer is **streaming or a non-host representation**, not a schema.

**This is a constraint on the design of the core, not an argument for building it
now.** The gate above is unchanged. `yyjson` (MIT, ANSI C, immutable document,
R and Python bindings) is the reference point for what that representation looks
like if the core is ever written, and is recorded here rather than in the tool
grid because **it is a parser and answers none of the nineteen questions.**

`design/probe.py` is the prototype and is explicitly not the package. It lives in
`design/` for that reason.

## The bindings, written 2026-08-12 — and the architecture's promise is now tested

> **`r/` and `python/` exist and ship `fathom()` alone.** No FFI, no ABI,
> nothing compiled on a user's machine: each finds the binary, runs
> `fathom probe <file>`, and hands back the bytes. **Neither has a dependency.**
>
> **The promise this page makes — *one core, so the languages agree by
> construction* — was only ever half true, and the untested half was the
> wrappers.** A binding that reformats or re-encodes the page is a second
> implementation of the report, which is exactly what the architecture was
> chosen to prevent. `test/bindings.py` now asserts the other half directly:
> **25 corpus documents, R and Python against the binary, byte for byte, no
> differences.**
>
> | decision | why it is not arbitrary |
> |---|---|
> | `fathom()` RETURNS, both languages | R auto-prints at the console and is silent under assignment; Python matches it with a `repr` rather than an eager `print`, because `design/vocabulary.md` requires the two to **differ by the pipe alone** — and an eager print would show the page twice at a REPL |
> | the Python report is a `str` subclass | `print`, slicing, `in` and `splitlines()` work with no new type to learn |
> | `$FATHOM_BIN` → `PATH` → walk upward | an explicit override wins, an installed binary is next, the dev build is last. Walking up is what `uv run` does, and for the same reason: everything here runs from deep subdirectories |
> | a broken `$FATHOM_BIN` is an ERROR | it was set on purpose. Silently running a different binary is how a measurement gets attributed to the wrong build |
>
> **`design/fathom.R` is STILL NOT DELETED and the instruction below is now
> narrower rather than met.** It says the file goes at port time; the R package
> exists and does not replace it, because `design/parity.py`'s 19 sentences
> exercise `rows` and `where` while the binding ships `fathom()` alone.
> **Deleting it today would retire a working check and put nothing in its
> place.** The real condition is: **it goes when the R binding implements
> `rows`.**

## The port, begun and finished 2026-08-10

> **DONE. `fathom probe <file>` is byte-identical to `design/probe.py` on all
> seventeen corpus files that carry a `source.json`.** The criterion below was
> written before any Rust existed and it is met.
>
> **How the six predictions came out**, kept in full below because a prediction
> that is quietly dropped once it is wrong was never a prediction:
>
> | predicted | outcome |
> |---|---|
> | `pandas.json_normalize` is the largest risk | **right that it was the hardest, wrong that it would break.** Two of its behaviours had to be measured because the guess was wrong; ported exactly |
> | `bad_bytes` diverges on the truncation ladder | **wrong.** 145 cases agree byte for byte |
> | the parser must be hand-written | **right, and for a fourth reason nobody listed** — CPython's `\u` handling does not match its own documented guard |
> | `-0` survives only in the token | **right** |
> | `i64` is not enough for `bigints` | **right** |
> | an unordered map reorders the output | **right, and cheap to prevent** — `ordermap.rs` exists for it |
>
> **The last defect in the entire port was one missing space**, in the
> aligned-arrays block. Every stage comparison had already passed on both
> affected files; every FINDING was correct and the page was still wrong. That
> is the argument for the byte diff being the criterion rather than a
> structured comparison, and it is why `test/parity.py` now runs both: **the
> stages say WHERE, the page says WHETHER.**

**The author decided A1 on 2026-08-10.** The gate had been closed since
2026-08-09 and the decision was the only thing left. This section is the record
of what was predicted **before the first line of Rust was written**, because
rule 1 applies to a port exactly as it applies to a document: a difficulty
discovered and then described reads as foresight, and is worth nothing.

**The oracle is `design/probe.py` at `dcd6ec8b…`, and the criterion is a diff.**
Its output on the seventeen corpus files that carry a `source.json` — 1,190
lines — was captured before any Rust existed. **A port is finished when the
diff is empty**, not when it looks right. `test/check.py`'s 198 health cases are
the same argument at a smaller scale and already have a scorer, so health is
ported first.

> **The port reproduces the probe's DEFECTS as well as its findings.** Item 21's
> single-copy blindness and the list-column problem are ported faithfully and
> repaired afterwards, deliberately, with a freeze. A port that improves what it
> is copying cannot be verified against it, and the improvement and the
> regression become the same diff.

**Where the port is predicted to hurt, worst first.** Each of these is a claim
that can be wrong:

1. **`pandas.json_normalize`, and it is the largest risk by a distance.**
   `price()` builds a table with it and reads three things off it — the shape,
   the `isna()` fraction, and the per-column `nunique()` of `astype(str)`. The
   Rust core has to reproduce pandas' flattening rule and its NaN semantics
   exactly or every `% empty` and `repeated Nx` figure in `ONE ROW COULD BE`
   moves. **Prediction: this is where the first real divergence appears.**
2. **`bad_bytes`, and this one is predicted to bite on the 145 truncate cases.**
   Python counts `U+FFFD` after an `errors="replace"` decode. Rust's lossy
   decode also emits `U+FFFD`, but the two disagree about how many replacement
   characters a given ill-formed sequence earns, and UTF-16 is a second rule
   again. **Prediction: a nonzero number of the truncation ladder disagrees on
   the count while agreeing that the file is damaged.**
3. **Python's `json` accepts `NaN`, `Infinity` and `-Infinity` bare**, and
   overflows `1e400` to `inf` rather than erroring. `serde_json` does neither.
   **Prediction: the parser is hand-written, not a dependency** — which also
   buys the duplicate-key hook, the `-0` token and the arena below.
4. **`-0` survives only in the token text.** `json.loads("-0")` returns `int` 0
   and the sign is gone, which is why the probe hooks `parse_int`. Flagging must
   read the token, never the value.
5. **Python integers are arbitrary precision**, so `abs(v) > 2**53` is exact for
   a 200-digit literal. **Prediction: `i64` is not enough and the comparison is
   made on the token.**
6. **Key order is load-bearing and is not obviously so.** Python dicts preserve
   insertion order, and the probe leans on it in at least three places —
   `Counter.most_common()` ties in the polymorphism report, `groups` iteration
   in `discriminator()`, and the `types` accumulator in `_walk()`. **Prediction:
   an unordered map reorders output on files with tied counts**, which is a
   diff that looks like a bug in the fold and is not.

**And the one thing the port must not lose, because it is the measured half of
the case for doing it at all**: the core must never build a per-record object
graph. `design/probe.py` needs 968 MB where `jsonlite::stream_in` needs 427 MB,
and a Rust core that parses fast and then materialises the same graph inherits
the whole problem. **The representation is a flat arena of nodes addressed by
index**, which is `yyjson`'s design and is named above for that reason. This is
a prediction too: it is expected to cost less memory than the prototype on
`04-gharchive`, and that number is not yet measured.

## The caution

**A Rust core makes domain parsers easier, which is exactly the temptation this
project decided against.** More room and more speed is how `parse_geojson` gets
in. The deletion test applies to the core as much as to the vocabulary: a word, or
a code path, belongs only if removing it makes one of the fixed questions
unanswerable on some corpus file.

The evidence for holding that line is already measured. `engines` is structural in
the npm registry document and data in a `package-lock`, and both readings are
correct — **data-ness is a property of the document, not of the format**, so a
format table would be wrong on one of the two files while a domain-blind
measurement is right on both.
