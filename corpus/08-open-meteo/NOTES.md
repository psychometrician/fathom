# 08 — an Open-Meteo hourly forecast

## The expectation, written 2026-08-09 before `source.json` was saved

Frozen at the moment this was written:

```
design/probe.py   473fe0f1e0b0e6f93419734d7b384db12af76e9c
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Disclosure, and it is larger than file 06's

**More of this document was seen before the predictions were written than for any
other corpus entry**, because it was chosen by structure rather than by topic and
checking the structure meant looking. Seen: the nine top-level keys, the five keys
under `hourly` and their lengths (**336 each**), and the contents of
`hourly_units`. Not seen: any value in any column, the probe's output, `rows()`'s
output, or any graded axis.

The predictions below are therefore about **what the tools do**, not about what
the document contains, and no prediction about document content is claimed.

### Why this file, and why it is a stand-in

**Raised by the author from a Reddit thread** — *"Using Python to Parse a JSON
Object"*, r/PythonLearning — in which a retired hobbyist scrapes a DOT weather
station and writes:

> *"Sometimes I feel like I'm beating data into submission rather than processing
> it."*

Their document is Synoptic's Mesonet API: `STATION[0].OBSERVATIONS` holding
`date_time`, `air_temp_set_1`, `wind_speed_set_1` — **parallel arrays aligned by
position**, which is `06-espn-qbr`'s structure found in the wild by a user rather
than chosen by this project. Their entire solution is `zip()`.

**Synoptic could not be fetched**: the documented demo token returns
`403 Invalid request per token rules`, and the thread's own token is redacted.
Open-Meteo is a free, unauthenticated API returning the **same column-oriented
shape**, and is used as a structural stand-in. **This is recorded as a
substitution, not passed off as the thread's file.**

### What the thread adds independently of the file

Five replies: `marshmallow`, `pydantic` (three times), and
`pandas.json_normalize`. **Every one presupposes the shape.** pydantic requires
the fields to be declared before it will parse; that is question 1 and question 3
supplied by the user as input. Nobody suggested a way to *find* the shape.

### What is predicted

**1. `ALIGNED BY POSITION` fires, and this is the point.** Five arrays of
identical length under `hourly`. This is the **second specimen ever** for that
feature and the **first not chosen by its author** — `06-espn-qbr` was picked
because it had the property.

**2. It finds no name row, correctly.** `looks_like_names()` wants a single
instance of all-distinct short strings. This document has no such array: the
column names are the **keys of `hourly`**, and the units are the keys of
`hourly_units`. Predicted: the alignment is reported with **no `<- the names`
marker**, which is right, and the probe says nothing about where the names
actually are.

> **This is the control for `06-espn-qbr`.** ESPN named its columns by POSITION,
> in a `labels` array, with a same-length decoy sorted differently that yields
> `TQBR = -7.4` for the league's best quarterback. Open-Meteo names its columns
> by KEY, which cannot be mis-joined. **Same shape, one safe and one dangerous,
> and the probe currently reports the alignment identically for both.** If that
> holds it is a real gap: the feature says "these are aligned" without saying
> whether the names are safe.

**3. `hourly` is reported as keys-as-data, or undecided.** Its keys —
`temperature_2m`, `wind_speed_10m` — are variable names, and its values are
columns. Predicted: `classify()` calls it **undecided** rather than data, because
the values are homogeneous arrays and sibling overlap is meaningless at one copy.

**4. Under 40 lines.** 12 KB, no recursion, no heterogeneity.

**5. `rows("hourly.*")` is the wrong answer and will show it.** Predicted: **5
rows** — one per variable — each with a 336-element list-column, because `*` over
an object yields one row per key. **The useful table is 336 rows × 5 columns and
is the transpose.** `rows()` has no operator for that, which would make this the
third file to strain the god seam and the first to strain it by needing a
transpose rather than an unnest.

**6. keys-as-data ≈ 1, depth 3, recursion 0.**

---

## Provenance

| | |
|---|---|
| what | Open-Meteo hourly forecast, Salt Lake City, 7 past days + forecast |
| source | `api.open-meteo.com/v1/forecast`, see `fetch.sh`. Free, no token |
| fetched | 2026-08-09 |
| size | 12,198 bytes, committed |
| stands in for | Synoptic Mesonet, from the r/PythonLearning thread; its demo token 403s |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 12,198 · depth **3** · paths 24 · fields 14 · explosion 1.7 |
| recursion | 0 · polymorphic 0 · heterogeneous 0 |
| keys-as-data | **0** |
| ragged by absence | **0/0** · ragged by null **0** |
| path variance | 5 · row shapes **1** |

**`0/0` ragged and one row shape.** By every axis this corpus grades, the file is
trivial. It is here because the axes do not have a column for the thing that is
hard about it.

> **Regraded 2026-08-11: row shapes is now 2.** The line above is left at 1
> because it records what was measured on the day, and the sentence it supports
> is still true of every axis that predates the regrade.
>
> **The second shape is the document.** Defect 27's repair added `a position in
> $.hourly` — **336 rows x 5 cols** — to `ONE ROW COULD BE`, which until then
> held exactly one line: `the whole document, 1 rows x 9 cols`. **The probe had
> printed the five aligned paths four lines earlier and then answered *what is
> one row* with the wrapper.**
>
> **This does not make the file non-trivial; it makes one axis stop lying.**
> The thing that is hard here is still what `corpus/README.md` says it is, and
> the column-oriented axis added on 2026-08-11 is still the one that measures
> it. See `FINDINGS.md`, 2026-08-11.

## Prediction scorecard: four of six

| # | predicted | outcome |
|---|---|---|
| 1 | `ALIGNED BY POSITION` fires | **confirmed.** 5 paths of 336 |
| 2 | it finds **no** name row, correctly | **WRONG, and far worse than wrong — see below** |
| 3 | `hourly` undecided, not keys-as-data | **confirmed.** "could not call 2 small single-copy objects" |
| 4 | under 40 lines | **confirmed.** 25 |
| 5 | `rows("hourly.*")` gives 5 rows, transpose needed | **confirmed. 5 rows x 2 cols**, each a 336-element list |
| 6 | keys-as-data ≈ 1 | **wrong. 0** |

## What the file established

### 1. `looks_like_names()` mistakes a timestamp column for a header row

```
$.hourly.time    2026-08-02T00:00, 2026-08-02T01:00, 20   <- the names
to name the others, zip them in order against time
```

**The probe is advising a reader to name four weather variables using 336 ISO
timestamps.** `looks_like_names()` asks for one instance, all strings, all
distinct, all 40 characters or fewer. A timestamp column satisfies every clause —
and a timestamp column is the single most common thing a columnar document
carries.

> **Predicted: "it will correctly find no names." Actual: it invented one, and
> the advice it printed is actively harmful.** This is the most damaging single
> line the probe has produced on any corpus file, because a reader following it
> gets a table, not an error.

The feature is one day old and this is its **first specimen not chosen by its
author**. It survived `06-espn-qbr`, where `labels` genuinely was a header row,
because that file happened to contain one.

### 2. It cannot tell a safe alignment from a dangerous one

This document names its columns by **key** — the names are the keys of `hourly`,
and `hourly_units` is an object keyed identically. There is nothing to mis-join.
`06-espn-qbr` names its columns by **position**, with a same-length decoy that
yields `TQBR = -7.4` for the league's best quarterback.

**Two files, opposite risk, and the probe prints the same warning for both** —
*"NOT against another array found elsewhere: same length is not same order."* On
ESPN that sentence is the finding. Here it is noise, attached to the wrong array.

### 3. The only row it can offer is the whole document

```
ONE ROW COULD BE
  the whole document    1 rows x 9 cols
```

`RECORD SHAPES, FOLDED` is **empty** — there are no sibling objects anywhere. The
useful table is **336 rows × 5 columns** and the probe cannot propose it, because
every operation it has folds *objects* and this document has almost none.

`rows("hourly.*")` returns **5 rows**, one per variable, each holding a
336-element list. The answer is the transpose and there is no operator for it.

> **Operation 1 — fold sibling instances — is the load-bearing idea and it has
> nothing to fold here.** A column-oriented document is the case where the whole
> design has no purchase, and it took a file found by a stranger on Reddit to
> produce one.

## What it disconfirmed

**That the corpus's axes describe what makes a document hard.** Every axis here
is 0 or 1 — no raggedness, no recursion, no polymorphism, one row shape — and the
document defeats the tool completely. `corpus/README.md`'s "Wanted" list has no
entry for *column-oriented*, and it should.

## The R half — predictions, written 2026-08-10 BEFORE the tools were run

**Committed as its own change, before any file exists in `r/` beyond the tidyr
attempt.** Rule 1.

**This is the document that defeats the whole design**, and the entry above says
so plainly: *"Operation 1 — fold sibling instances — is the load-bearing idea and
it has nothing to fold here."* Every axis reads 0 or 1. The useful table is
**336 × 5** and the probe can only offer *the whole document, 1 row × 9 cols*.

**1. AND R SHOULD FIND IT TRIVIAL, which is the prediction that matters.** A
data frame *is* a named list of equal-length vectors — R's native model is
column-oriented, and `hourly` is exactly that: five arrays of 336 under five
keys. Predicted: **`as.data.frame(fromJSON(...)$hourly)` gives 336 × 5 in one
expression**, with no verb chosen and no transpose written.

> **If that holds it is the sharpest result in the corpus against Phase 2.** The
> file that has no purchase for fathom's central operation is the file R already
> handles, because the shape fathom finds hardest is the shape R is built on.

**2. The transpose `rows()` has no operator for is free.** `rows("hourly.*")`
returns 5 rows each holding a 336-element list, and `NOTES.md` records that the
answer is a transpose with no operator. Predicted: in R this is not an operation
at all — it is what `as.data.frame` on a list of equal-length vectors means.

**3. The name join here is SAFE and should be easy to prove safe.**
`hourly_units` is keyed identically to `hourly`, so the columns are named by
**key**, not by position. Predicted: joining units to variables is `units[names(
hourly)]` — no positional risk, and the exact opposite of `06-espn-qbr`, where
the same-length decoy gives `TQBR = -7.4`. **Two documents, opposite risk, and
the probe prints the same warning on both.**

**4. rrapply's melt will be HIGH — above 150%**, and probably near the top of the
seven-file table. The corrected statistic says the ratio tracks path length
against value size. This document is the extreme case: values are short numbers
like `23.4` under long repeated paths like `hourly.temperature_2m.335`.

**5. jq can express the transpose but will not volunteer it.** `to_entries` and
`transpose` exist. Predicted: expressible in one expression once asked, and no
tool proposes the 336-row table unprompted.

**A prediction that would hurt.** If R does NOT produce the 336 × 5 table
easily, then columnar JSON is hard for everyone and this file is evidence FOR
building something. If R does produce it in one line, the file is evidence that
the hardest case for fathom's design is the easiest case for the ecosystem it
would ship into — and that belongs in `VERDICT.md` whether or not it is welcome.

## The R half, run 2026-08-10 — five of five, and the result argues against Phase 2

**All five R tools run; the entry is done.** Predictions were committed in
`6ec17ac`, before any file in `r/` existed beyond the tidyr attempt.

| # | predicted | outcome |
|---|---|---|
| 1 | `as.data.frame(hourly)` gives **336 × 5** | **confirmed. One expression, 0.001 s** |
| 2 | the transpose is free in R | **confirmed** — it is not an operation at all |
| 3 | the units join is safe, by KEY | **confirmed.** `hourly_units` keyed identically |
| 4 | melt **above 150%** | **confirmed and exceeded. 356% — the corpus high** |
| 5 | jq can transpose but will not volunteer | **confirmed.** A builtin, one expression |

### 1. The document that defeats the design is the one R handles in one line

The section above is unambiguous: *"Operation 1 — fold sibling instances — is the
load-bearing idea and it has nothing to fold here."* No sibling objects,
`RECORD SHAPES, FOLDED` empty, the probe offering *the whole document, 1 row × 9
cols*, `rows()` returning five rows each holding a 336-element list, and the
answer being *"a transpose and there is no operator for it."*

```r
as.data.frame(fromJSON(path)$hourly)     # 336 x 5, 0.001 s
```

**One expression, no verb chosen, nothing known in advance.** In R the transpose
is not an operation — a data frame *is* a named list of equal-length vectors, so
a column-oriented document is already in R's native shape.

> **This is the sharpest thing the corpus has said against Phase 2 and it is
> recorded rather than softened.** The case where fathom's central operation has
> no purchase is the case the ecosystem it would ship into finds easiest. A tool
> cannot claim to help most where its host language needs no help.

**The honest counterweight**: this works because R got lucky about its data
model, not because jsonlite understood anything. It does not say `hourly` is the
interesting key, does not mention the arrays are equal-length, and would build
the same frame from five arrays that matched by coincidence. **It is right for no
reason** — and on `06-espn-qbr` that same absence of checking is what makes the
decoy dangerous.

### 2. The operator exists in three of the five tools

`NOTES.md` says *"there is no operator for it."* That is true of `rows()` and not
of the ecosystem:

| tool | the transpose |
|---|---|
| base R / jsonlite | **not an operation** — `as.data.frame` on a named list of equal-length vectors |
| purrr | **`list_transpose()`** — 336 named rows |
| jq | **`transpose`** — a builtin, one expression |

**And none of the three checks anything.** jq's `transpose` pads ragged arrays
with null; `list_transpose(list(a=1:3, b=1:2))` returns 3 rows with no error;
`as.data.frame` recycles. All three are correct here because the document is
well-formed, not because any of them verified it.

### 3. The collision test from `06-espn-qbr` stays silent — which is the point

```
hourly vs hourly_units, by KEY:  {"same_set": true}
the five arrays:                 {"arrays_of_equal_length": true, "n": 336}
```

The columns are named by **key** and `hourly_units` is keyed identically, so
`units[names(tbl)]` cannot be wrong. The jq expression that fires on ESPN — two
arrays, same length, same set, different **order** — finds nothing here.

> This entry faults the probe for printing `same length is not same order` on
> both files, where it is the finding on one and noise on the other. **A test
> that separates them is two expressions**: are the names KEYS of the same
> object, or a parallel ARRAY somewhere else? The warning is not wrong; it is
> undiscriminating, and the discrimination is cheap.

### 4. Melt is 356% — the corpus high, on the corpus's smallest file

| `04` 52% | `05` 60% | `06` 140% | `09` 141% | `10` 173% | `07` 204% | `03` 226% | **`08` 356%** |
|---|---|---|---|---|---|---|---|

**7.2-byte values under 25.6-character paths.** `hourly.wind_direction_10m.335`
costs four times what `118` does. The corrected statistic is now confirmed at
both extremes: `04-gharchive` has the corpus's highest path variance and severe
raggedness and lists at **52%** because its values are SHAs and commit messages;
this file has depth 3 and every axis at 0 and lists at **356%**.

**Nothing about raggedness, keyed sites or depth orders that table.**

And melt answers the wrong question here, which no other corpus file made it do:
1,692 rows is 336 × 5 cells plus twelve scalars — every number present, the shape
inside out. Melt is the correct flattening of a **tree**, and this is a table
stored column-wise. Recovering the real 336 × 5 needs a `reshape` on two level
columns.

### 5. tidyjson fits worst here and best on `04-gharchive` — the pair is the result

On NDJSON, tidyjson's model — *a table of documents* — matched so exactly that
`as.tbl_json(readLines(...))` gave 37,883 records with nothing known in advance.
**Here the same model has nothing to hold**: `gather_array` turns ONE array into
rows, so the real table takes **five `gather_array` calls and four merges** — the
longest route of any tool in this directory.

**That is the exact mirror of what happens to fathom.** Both tools are organised
around the assumption that a document is a collection of *things*, and this
document is a collection of *columns*.

`json_schema` is correct and useful at 12 KB — the third file confirming that its
losses are about heterogeneity, not about the function.

### An R hazard worth recording: `enter_object` NSE fails silently

`enter_object(k)` with a character **variable** looks for a field literally named
`k`, finds none, and returns **0 rows with no error or warning**; the literal
`enter_object("temperature_2m")` returns 336. Measured: variable **0**, `!!k`
**336**, `!!sym(k)` **336**, `do.call` **336**. The first draft of
`try-tidyjson.R` looped with the variable and printed a confident `0 × 6` table
with the right column names and no rows — **an answer rather than an error**,
which is the class of failure this corpus exists to record.

## Status

**R half complete 2026-08-10** — purrr, jsonlite, tidyjson, rrapply, jqr, plus
tidyr. Python is 8 attempts. Under `CLAUDE.md`'s definition this entry is done,
and **the first ten corpus entries are now all done.**
