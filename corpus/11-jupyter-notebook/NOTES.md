# 11 — a Jupyter notebook

## The expectation, written 2026-08-09 before anything was run

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   c7b4aef4b166c9c078c1b0e8bb4061d5f1f7ae4c
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

**Disclosure, two kinds, because both bias a prediction.**

*Of the specimen.* Four notebooks were loaded and reduced to four numbers each to
pick the richest: top-level keys (`cells, metadata, nbformat, nbformat_minor` —
identical in all four), cell count, `cell_type` counts, `output_type` counts.
**Advent-2021** has 272 cells (140 markdown, 132 code) and 107 outputs across
three types (execute_result 63, stream 27, display_data 17). Nothing below that
has been looked at: **no `source`, no `execution_count`, no `data`, no `metadata`,
and no value of any kind in this file has been seen.**

*Of the instrument.* `discriminator()`, `disorder()`, `variation()` and the
`encoded` health check were read in `design/probe.py` before predictions 1, 2 and
4 were written. The predictions are therefore sharp on purpose and a reader should
discount them accordingly: they are about **whether the guards fire**, which is a
weaker thing to get right than guessing the document. Predictions 3, 5, 6 and 7
are about the document and were formed without that.

### Why this file

**The probe's own docstring names Jupyter as a format it knows nothing about**,
and eleven files in, the corpus has never had one. Three further reasons:

**1. `corpus/README.md` says model output is the *only remaining candidate* for
the polymorphism gap.** That is an assertion nobody measured, and it is the
fourth time this list has claimed something about a file in advance. A notebook
tests it directly, because `nbformat` permits `source` and `text` to be **either
a string or a list of strings** and both are legal — polymorphism that no
specification engineered out, which is exactly what FHIR turned out to have done.
If a notebook delivers, the polymorphism gap has a specimen that does not depend
on the open agent-trace decision.

**2. It is the corpus's first document with a value that is itself an encoded
document.** `README.md` lists that under *silent* damage, the half it says is
worth owning, and no corpus file has ever had a real instance. `image/png`
outputs are base64.

**3. It has two nested partition candidates in one file**, one level apart:
`cells[]` discriminated by `cell_type`, and `outputs[]` by `output_type`. The
partition operation was re-frozen yesterday and has no held-out evidence at all.

### What is predicted

**1. `SPLIT ON output_type` fires on `outputs[]`, 3 kinds, and this is the
clean case.** By hand from nbformat: a `stream` is `{output_type, name, text}`,
an `execute_result` is `{output_type, execution_count, data, metadata}`, a
`display_data` is `{output_type, data, metadata}`. Union of 6 fields, so the fold
should be about **40% holes** — (27·3 + 63·2 + 17·3)/(107·6) — and each group
should be completely full. Three distinct key-sets clears `shapes < 3`, 40%
clears the 0.2 floor, and a worst group near 0% clears the halving rule.
**Predicted: fires, and every group at or near 0% empty.**

**2. `cells[]` lands inside the gap the 0.2 disorder floor was fitted into, and
no corpus file has ever done that.** A markdown cell is `{cell_type, metadata,
source}` and a code cell adds `execution_count` and `outputs`, so 140 of 272
cells miss 2 of 5 fields: **20.6% holes**. The floor is 0.2, fitted yesterday in
the gap between `04-gharchive`'s 8% and `02-hn-thread`'s 23%, and `FINDINGS.md`
says *"the gap it sits in is the whole evidence for it"*. **This document sits in
that gap, half a point above the line.** Predicted: it fires, barely — and
whichever way it goes is the first held-out evidence about a fitted constant.

> If prediction 1 fires and 2 does not, the probe will have split the *outputs*
> of a document while refusing to split the *cells* that hold them, which is the
> sharper result and the one to hope for.

**3. `source` is polymorphic — `str` on some cells and `list[str]` on others —
or it is not, and the corpus README is right.** This is the genuine unknown and
the reason the file was chosen. Predicted **weakly: no**, because a notebook
written by one tool in one sitting will be internally consistent, and the
polymorphism lives *across* notebooks rather than within one. **If that is what
happens it is the same lesson as FHIR arriving by a different road**, and it says
the polymorphism gap needs a document assembled from several sources.

**4. The health check reports `encoded: 0` and the document contains base64
images anyway.** `encoded` requires a string that parses as JSON *and* starts
with `{` or `[`. A base64 PNG does neither. **Predicted: a real instance of the
silent damage `README.md` names, sitting in the file, unreported** — and a
correct miss rather than a defect, since a base64 blob is not an encoded *JSON*
document. What it would establish is that the category is wider than the check.

**5. Keys-as-data at the mime types, reported undecided.** `data` is keyed by
`text/plain`, `image/png`, `application/json`. That is a **closed** vocabulary,
which `VERDICT.md` records as the classifier's one permanent structural limit —
`data{text/html, text/plain}` is named there explicitly as the miss. Predicted:
undecided rather than data, and a second real instance of a known limit rather
than a new defect. `metadata` keyed by cell id would be data if present.

**6. Recursion 0, polymorphism at `data`, depth about 7.** Notebooks do not
nest into themselves. The `data` object's values differ by mime type — a list of
strings for `text/plain`, a single string for `image/png` — so predicted
polymorphic ≥ 1 there even if prediction 3 fails.

**7. `ONE ROW COULD BE` names one cell per row, 272 rows.** The fourth
held-out test of *the parent is the table*, and `outputs[].data` gives the
alignment rule a chance to misfire on same-length string arrays. Predicted:
`ALIGNED BY POSITION` silent.

**8. Under 150 lines.** Wikidata was 75 at 1.4 MB, Stripe 226 at 7.6 MB. This is
1.1 MB with far fewer distinct paths than either.

---

## Provenance

| | |
|---|---|
| what | Peter Norvig, **"Advent of Code 2021"**, `pytudes/ipynb/Advent-2021.ipynb` |
| source | `raw.githubusercontent.com/norvig/pytudes/main/…`, see `fetch.sh` |
| fetched | 2026-08-09 |
| size | 1,114,184 bytes, committed |
| chosen from | Advent-2021, fastbook `01_intro` (364 KB), Norvig `Economics` (920 KB), PDSH matplotlib intro (110 KB) |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers.
**0.53 s, 83 MB resident** for a 1.1 MB file. **17 values reported as themselves
encoded JSON**, and that report is discussed below — it is not what it sounds
like.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 1,114,184 · depth **7** · paths **37** · fields 25 · explosion **1.5** |
| keys-as-data | **0** · ragged by absence 8/13 · ragged by null 1 |
| recursion | 0 · polymorphic **0** · heterogeneous 2 · path variance 4 · row shapes 3 |

**The lowest path explosion in the corpus, by a distance.** 1.5 against npm's 353
and Wikidata's 398.9. Thirty-seven distinct paths in a 1.1 MB file: this is a
regular document, and everything interesting in it happens anyway.

## Prediction scorecard: four of eight, and the misses are the value

| # | predicted | outcome |
|---|---|---|
| 1 | `SPLIT ON output_type`, 3 kinds, ~40% → ~0% | **confirmed, to the digit. 40% folded, 0% after, all three groups 0% empty** |
| 2 | `cells[]` sits in the 0.2 gap and fires barely | **WRONG, twice over — see below. The floor was never in play** |
| 3 | `source` not polymorphic within one notebook | **confirmed. polymorphic 0** |
| 4 | `encoded: 0`, base64 missed | **WRONG. `encoded: 17`, and not one of them is an encoded document** |
| 5 | mime-type keys reported undecided | **partly wrong. Not called data, not called undecided — silently read as field names** |
| 6 | recursion 0, depth ~7, polymorphism at `data` | **two of three.** depth **7** ✓, recursion **0** ✓, `data` polymorphism ✗ |
| 7 | 272 rows one-cell-per-row, alignment silent | **confirmed, both. Fourth held-out pass for *the parent is the table*** |
| 8 | under 150 lines | **confirmed. 30 lines** |

**The thing hoped for in prediction 2 is what happened**: the probe split the
*outputs* of this document and refused to split the *cells* that hold them.

## What the file established

### 1. Two correct repairs compose into a new defect — the fifth instance of one root cause

**This is the finding.** `cell_type` is a textbook two-way discriminator: present
in every cell, scalar, two values, and splitting takes markdown to **0%** disorder.
The probe refuses it. Measured rather than reasoned:

```
cells[]      272   emptiness 0.2066   variation 0.40   disorder 0.40   keysets 3
  markdown   140   disorder 0%
  code       132   disorder 40%     <- worst group
  worst 0.40 > disorder/2 = 0.20   ->  refused
```

**Every guard passed except the halving rule.** Three filled key-sets clears
`shapes < 3`; `cell_type` clears scalar, presence and cardinality. The split is
refused because the code group stays at 40%.

**And the 40% is not real.** The code group's *emptiness* is **0.0015** — code
cells fill everything. All 40% is `variation()`, and it comes from exactly two
fields:

```
outputs   ['array', 'array[1] object']      <- empty list vs non-empty list
source    ['array', 'array[1] text']        <- empty list vs non-empty list
```

> **An empty array and a non-empty array are being counted as two different
> types.** That is emptiness wearing a shape's clothes, and it is the one
> confusion this project has already repaired twice.

The lineage matters, because no single change here was wrong:

| | |
|---|---|
| `a316ac68…` | taught `shape()` to report what an array holds, so `array[1] text` ≠ `array[1] object`. **Correct, and DuckDB found the bug it fixed.** |
| `c7b4aef4…` | priced a split by type variation as well as holes, because `10-wikidata` had no holes. **Correct, and it recovered `03-natural-earth`'s polymorphism.** |
| **together** | `variation()` became load-bearing for the first time, sitting on a `shape()` that calls `[]` a different type from `["x"]`. **Neither repair was ever run against the other.** |

`VERDICT.md` says of the `shape()` repair: *"It was the fourth instance of one
root cause and the sharpest… the fix for one proxy introduced another."* **This
is the fifth**, and it is also the third route by which emptiness has re-entered
a calculation that was supposed to have one definition. Defect 5 made `filled()`
the single answer to *is this empty*. **`shape()` was never put through it**, so
emptiness came back as a type.

### 2. `encoded: 17`, and every one of them is a false positive

Predicted `0`. The probe found 17, and measuring what they are:

```
'[376.0, 490.543]'
'[[[[6,3],7],0],[[7,0],0]]\n'
'[[[4,7],[6,[6,5]]],[4,[[6,5],[9,1]]]]\n'
```

Advent of Code 2021 day 18 is *Snailfish*, whose puzzle input **is** nested
integer lists, printed as cell output. The first is a Python `repr` of a list of
floats. All 17 genuinely parse as JSON and genuinely start with `[`, so the check
is correct by its own definition and wrong about the world: **nothing upstream
double-encoded anything.** `CLAUDE.md` names this failure mode already — *a `NaN`
detector that fired ten times on legitimate prose* — and the health verb has now
produced it a second time, on a real file.

**The coincidence a reader would otherwise make a meal of: this notebook contains
exactly 17 base64 PNGs, and they are not the same 17.** Verified — no
`image/png` value is among the encoded set, because base64 neither parses as JSON
nor starts with a bracket.

> So both halves of prediction 4 were wrong in opposite directions at once. The
> real encoded payloads are invisible and seventeen `repr`s are reported in their
> place. **The category is wider than the check on one side and narrower on the
> other.**

### 3. `execution_count` is reported as a type change when it is ragged by null

The probe prints it under **FIELDS THAT CHANGE TYPE**:

```
$.cells[].execution_count      number x131, null x1
```

`axes.py` grades the same file **polymorphic 0, ragged-by-null 1**, and `axes.py`
is right — `README.md` split those two axes apart on 2026-08-08 precisely because
they are orthogonal. One unexecuted cell in 272 is not a field changing type.
**The two instruments disagree about the same document**, which is the shape of
defect 5 all over again, and it is the only polymorphism this file reports.

### 4. The polymorphism gap is still open, and the corpus README was right

**Predicted, and confirmed: `source` is a list of strings on every cell.**
`nbformat` permits a bare string and this notebook never uses one, because a
notebook is written by one tool in one sitting. **A format loose enough to allow
polymorphism still does not produce it within a single document** — which is
FHIR's lesson arriving by the opposite road. FHIR engineered it out by
specification; a notebook simply never varies because there is only one writer.

That is now **four candidates that have failed** the polymorphism gap, and it
sharpens what the gap actually needs: not a permissive format, but a document
**assembled from more than one producer**. `corpus/README.md`'s claim that model
output is the only remaining candidate survives this file intact.

### 5. Keys-as-data at the mime types, and the probe said nothing at all

`$.cells[].outputs[].data` is keyed by `text/plain` and `image/png`, and was
folded as a record with those as field names. It is not called data, and — unlike
the five single-copy `metadata` objects — it is **not listed as undecided
either**. `VERDICT.md` records this as the classifier's permanent structural limit
and names `data{text/html, text/plain}` as the example. **Here is that exact
example, in a real file, and it passes in silence.** The limit is real; the
silence is a reporting choice worth revisiting.

## The thirteen tool attempts, 2026-08-10

**The entry's other half, added a day after the probe run.** Five R tools, eight
Python, plus the `tidyr` attempt that was already here. Every file prints the
version it actually ran on.

### The counts every tool agrees on

**272 cells · 107 outputs · 233 `text/plain` lines · 53 values containing a URL.**
Thirteen tools, two languages, no disagreement — which is what makes the places
they *do* differ worth reading.

### 1. `json_schema` discarded on the document chosen because it should not have to

**The sharpest result, and it contradicts the prediction in `try-tidyjson.R`'s own
header.** `VERDICT.md` records `tidyjson::json_schema` silently picking one shape
and dropping the rest on `03`, `05`, `07` and `10`, always blaming heterogeneity.
This document is the corpus's most regular — explosion 1.5, 37 paths — so it was
run expecting the function to be right for once.

```
json_schema outputs shape:  {"name": "string", "output_type": "string", "text": ["string"]}
```

That is the **`stream`** shape, held by **27 of the 107 outputs**. The other 80
carry `data`, `execution_count` and `metadata`, and **none of the three appears**.

| | |
|---|---|
| true union of `outputs[]` keys | **6** — data, execution_count, metadata, name, output_type, text |
| `json_schema` names | **3** — name, output_type, text |
| coverage | **50% of key names, 25% of the outputs** |

**It picked the minority shape.** `metadata: {}` one level up is the same failure:
right for 271 cells, silent about the one that carries `tags`. **Fifth document,
fifth silent discard, and this was supposed to be the counterexample.**

### 2. jq's `paths(scalars)` cannot see a null, in both bindings

```
paths(scalars) at execution_count   194
paths          at execution_count   195
```

`paths(f)` is `paths|select(getpath|f)`, and **`select(null)` is false in jq**, so
every null value is silently absent from the standard path listing. The one
missing path is the one null. **The idiomatic phrasing is the blind one**, and
`try-jq.py` and `try-jqr.R` reproduce it identically — they are one language
through two doors and a control rather than two witnesses.

**This also makes Q1's folded path listing short by exactly one** in both files,
which is stated there rather than quietly corrected.

### 3. Absence versus null splits the thirteen tools five to eight

`execution_count` is **absent on 140 markdown cells and explicitly null on 1** of
the 132 code cells. Whether a tool can tell those apart is not a matter of effort:

| reads **132** (presence) | reads **131** or **141 NA** (collapsed) |
|---|---|
| jq, jqr, purrr, tidyjson, ijson | pandas, polars, duckdb, jsonlite, jmespath, glom, pydash |

**The five that get it right all walk keys; the eight that do not all build a
frame or a schema first.** Once a row exists, an absent key and a null key are
the same hole. `tidyjson` is the only tool in either language that *prints* both
— `number x131, null x1` — which is what `design/probe.py` also does and had to
be repaired to stop calling a type change.

### 4. Three failures that are specific to this document's raggedness

**`pandas.json_normalize(record_path="outputs")` RAISES**, because 140 cells have
no such key, and **`errors="ignore"` governs `meta` and not `record_path`** — the
ragged case has no flag at all. The 140 must be filtered out by hand, so Q3's
deeper row is unreachable without Q4's answer. It is the better failure: it
refused rather than quietly returning 107 rows.

**`ijson`'s prefix tally reports `outputs` as 0**, because a leaf-only count
cannot see a field whose value is a container — the same blindness `VERDICT.md`
records in jq's `paths(scalars)` dropping `children` from `02-hn-thread`. Both
columns are printed in `try-ijson.py` so the zero is not read as an absence.

**`rrapply`'s melt costs 608,888,988 characters to PRINT**, because R pads every
row to the widest value in the column and the widest value is a 22,732-character
base64 PNG. That is a printing artifact and not a description size — the
comparable statistic, the path listing, is **72,780 chars, 7% of the file** — but
it is what a person who types `m` at the console actually gets.

### 5. Two facts about the file that the probe run did not record

**The 17 base64 PNGs are 878,924 characters — 79% of the file.** This document is
mostly images, and every flat table in all thirteen attempts either drops them or
carries them whole.

**53 source lines CONTAIN a URL and zero source values ARE one.** They are
markdown prose, so a predicate anchored at the start of a value — which is what
`design/where.py` uses — finds nothing here. Q11 is answerable by jq, jqr,
rrapply and ijson without naming a path; everything else needs a hand-written
recursion or cannot do it at all.

### What this half cost the corpus's claims

**Nothing was overturned.** The O(data) claim survives in an unusual direction:
this is the document where the path-listing tools are *small*. `ijson`'s prefix
listing is **under 1% of the file** where npm is 111% and Stripe 174%, and
`pydash`'s name walk answers **25** where npm's answered 3,126. **The walkers did
not get better; the document has no keys-as-data of any size.** That is the
controlled comparison `VERDICT.md` builds from `07` and `08`, arriving on a
twelfth file without being sought.

## What it disconfirmed

**That a partition operation which fires is an operation that works.** This
document contains the cleanest two-way discriminator in the corpus and the
cleanest three-way one, one nesting level apart. The probe found the three-way
split perfectly and refused the two-way split completely, **and the same
`disorder()` call decided both.** A reader of the output sees a confident,
correct-looking split on `outputs` and has no way to tell that the operation
silently declined a better one on the enclosing array.

**And that low grades mean an easy document.** Every raggedness axis here is
mild — explosion 1.5, 37 paths, polymorphic 0, recursion 0, depth 7 — and the
file still exposed a composite defect that ten harder documents did not.
`08-open-meteo` made this point once already. **This is the second time a file
the axes call trivial has been the one that broke something**, which is evidence
about the axes rather than about the files.

