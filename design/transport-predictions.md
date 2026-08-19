# Transport: predictions, committed 2026-08-13 before any table was emitted

**Rule 1.** No NDJSON has been produced when this is written. `fathom rows
--candidate` still prints a shape line and nothing else.

## The decision being tested

`design/implementation.md:107-110` proposes **Arrow IPC** for the extract half
and marks it **undecided**. This plan rejects Arrow on the project's own stated
dependency policy and proposes **NDJSON — one JSON object per row** — written
with `fathom_core::escape`, the 17-line escaper already in the core.

**The recorded objection is the thing to measure**, `implementation.md:98`:

> *"fathom's extract half would ship data, and a large data frame through
> stdout is the one place this architecture strains."*

**Strain has to mean something measurable or it cannot be answered.** Taken here
as: the extract costs more than reading the file it came from, in wall time or in
peak memory, by enough that a person would notice.

## What is known first, and is not a prediction

- `price::table()` already builds every row and every cell; `main.rs:83-84`
  prints three numbers and drops the rest.
- `Cell` is `Node(u32) | Key(u32)` — node ids and string-table spans. **No cell
  has ever been materialised**, in Rust or across the boundary.
- No corpus document contains a NaN, an Infinity or a negative zero
  (`health --json` reports `nonfinite: 0` on every one).

## Predictions

| # | prediction |
|---|---|
| 1 | **NDJSON for the largest extract is SMALLER than its source document.** A table is one candidate's rows, not the whole file, and the keys repeat but the untaken structure is gone |
| 2 | **`09-stripe-openapi`'s 2,542 × 393 table is the worst case in the corpus** — 998,406 cells — and it is the one most likely to strain |
| 3 | **Wall time is dominated by parsing the source, not by writing the rows.** Emitting is a linear walk over a table already in memory; the parse already happened |
| 4 | **Peak RSS does not rise materially over the shape-line run**, because the table is already built either way. The only new allocation is the output string |
| 5 | **Under 5 seconds and under 1 GB RSS for every corpus extract except `26-gharchive-scale`** (912 MB, and skipped by every other harness for the same reason) |
| 6 | **stdout does NOT strain, and `--out <file>` will prove unnecessary.** The objection was written when the extract half had no design at all and no measurement behind it |
| 7 | **The 17-of-19 list-column figure is STALE.** It was measured over 19 entries and the corpus is 29. Re-measured it will still be a large majority — **over 80%** — because nothing about the documents changed |

## Two things this must get right, and neither is performance

| # | prediction |
|---|---|
| 8 | **A non-finite number must NOT cross as a bare token.** `NaN` and `Infinity` are invalid JSON; Python's `json.loads` accepts them by default and R's `jsonlite` refuses, so a bare token would make **the two languages disagree** — the one thing the architecture exists to prevent. They will be emitted as JSON **strings**, and `test/bindings.py` would have caught it if they were not |
| 9 | **A nested cell crosses natively and this settles decision A.** NDJSON carries an array or an object in a cell without flattening, so `rows()` may return a table with nested cells, and `README.md:302-306` already says what that means — the rectangular ones flow to god, the rest are terminal. **No `hoist` is needed at the exit and nobody has to own it** |

> **The prediction most likely to be wrong is 6.** It contradicts a written
> design document, and the honest position is that the document was written
> without a measurement and this replaces it with one — not that it was careless.
