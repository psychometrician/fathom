# 18 — openFDA adverse drug event reports

## The expectation, written 2026-08-09 before the probe was run

```
design/probe.py   981a45f023e8de6f0db5951e33c4a4b4d5d6d75b
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Disclosure

*Of the specimen.* Two top-level keys, `meta` and `results`, and `results` is a
list of 100 objects. Nothing inside a result has been seen.

*Of the instrument.* None read for this file.

*Of prior knowledge.* I know FAERS reports are deeply nested — a report contains
a patient, who has drugs and reactions — and that the fields are coded numeric
strings. That informs predictions 1 and 4.

### Why this file

**Second of the three the gate needs**, and chosen **ordinary** on the same rule.
It is deliberately unlike files 14, 15 and 17: NYC 311 is flat, GitHub issues is
shallowly nested with one record kind, OpenLibrary is a wrapper plus a flat array.
**This is the deeply nested case** — 2.87 MB for **100 records**, which is 28 KB
per record and by far the densest document in the corpus.

It is also the ordinary document from a regulated domain, where `05-fhir-bundle`
is the specification-driven one. **A working analyst in health data meets this
shape constantly**, and unlike FHIR nobody designed it to be self-describing.

### What is predicted

**1. The deepest ordinary document so far, depth 6 or more, and arrays of
objects nested inside arrays of objects.** A report has `patient.drug[]` and
`patient.reaction[]`. Predicted: several folded record shapes, not one.

**2. keys-as-data 0.** FAERS uses fixed field names.

**3. Ragged by absence, high.** Adverse-event reports are voluntarily submitted
and mostly incomplete. Predicted absence well above null.

**4. THE ONE THAT MATTERS: numeric codes stored as strings, and no axis sees
it.** FAERS encodes almost everything as a coded string — `"1"`, `"2"` for sex,
occupation codes, outcome codes. **Predicted: polymorphism 0, because everything
is uniformly text**, and the document is nonetheless full of values that are
categories wearing string clothes. If the probe says anything useful about that
it will surprise me.

**5. A split fires, or should.** If there is a coded field present on every
report that drives which other fields exist — a seriousness or outcome code —
operation 4 should find it. Predicted: **at least one split**, and after file 17
I am no longer predicting silence casually.

**6. Memory under 400 MB.** 2.87 MB at file 14's 8.2× is 24 MB, but this is
deeply nested and `14-nyc-311` showed the multiplier tracks nesting. Predicted
higher than 8.2× and well short of gharchive's 18.8×.

**7. Under 150 lines**, and the sentinel rule silent.

**8. `rows("results.*")` returns 100 rows** with list-columns at `patient.drug`.

---

## Provenance

| | |
|---|---|
| what | **openFDA adverse drug event reports** (FAERS), first 100 |
| source | `api.fda.gov/drug/event.json?limit=100` |
| fetched | 2026-08-09 |
| size | 2,870,736 bytes, **100 records**, committed |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers, no
encoded documents, **no sentinel report**. 51 lines, 92.7 MB resident.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 2,870,736 · depth **8** · paths 122 · fields 100 · explosion 1.2 |
| keys-as-data | **0** · ragged by absence **49/89** · ragged by null 1 |
| recursion | 0 · polymorphic **0** · heterogeneous 2 · path variance 1 · row shapes 4 |

## Prediction scorecard: seven of eight

| # | predicted | outcome |
|---|---|---|
| 1 | depth 6+, several folded shapes not one | **confirmed. Depth 8, eleven record shapes** |
| 2 | keys-as-data 0 | **confirmed** |
| 3 | absence high | **confirmed. 49/89 against 1 null** |
| 4 | polymorphism 0 — everything is coded text | **confirmed. 0** |
| 5 | **at least one split** | **WRONG — no split, and the probe is right** |
| 6 | memory under 400 MB, above 8.2× | **92.7 MB — and the multiplier framing breaks down, see below** |
| 7 | under 150 lines, sentinel rule silent | **confirmed. 51 lines, silent** |
| 8 | `rows("results.*")` → 100 rows | **confirmed. 100 × 26** |

## What the file established

### 1. NO DEFECT — the gate counter is at 2 of 3

### 2. The silence is right for the third file running

Prediction 5 said a coded field would drive a split. Measured, **nothing comes
close**:

```
results fold emptiness 19%  ->  worst group must be 9% or less
serious                   2 kinds   worst 16%
fulfillexpeditecriteria   2 kinds   worst 16%
receivedate               4 kinds   worst 18%
```

**`serious` is exactly the field the prediction meant and it leaves 16%.** FAERS
raggedness is driven by how complete a voluntary submission happened to be, which
cuts across every coded field — the same cause as `14-nyc-311`, in a completely
different domain.

**Third consecutive file where a prediction of mine was wrong and the probe was
right** — 15, 17, 18. On 15 the silence had a second correct reason; on 17 a split
I predicted against turned out provable; here a split I expected does not exist.

### 3. The memory multiplier breaks down below about 10 MB

| | bytes | peak RSS |
|---|---|---|
| `17-openlibrary` | 65 KB | — |
| `15-github-issues` | 702 KB | **84 MB** |
| `18-openfda-events` | **2.87 MB** | **92.7 MB** |

**Roughly 80 MB is the interpreter-and-pandas floor**, and the marginal cost of
this document is about 9 MB for 2.87 MB of JSON. Reporting 32× would be
arithmetically true and completely misleading.

> **The 18.8× and 8.2× figures only mean anything well above the floor**, which
> is another qualification on `design/implementation.md`'s memory argument, after
> `14-nyc-311` showed the multiplier tracks nesting rather than record count.

### 4. The densest document in the corpus, described in 51 lines

**28 KB per record** — 2.87 MB for 100 reports — against `14-nyc-311`'s 1.5 KB.
Eight levels deep, eleven folded record shapes, and the description fits on a
screen. Explosion 1.2.

## What it disconfirmed

**That a regulated domain implies a self-describing document.** `05-fhir-bundle`
is a specification with a discriminator in every record, twenty resource types
and a partition that takes 87% to 11%. FAERS is the same field of work with no
such design: one record kind, no discriminator worth the name, and raggedness
that is an artifact of submission completeness rather than of type. **The corpus
now has both, and they are nothing alike.**


---

## Grading

**The thirteen attempt files are DONE, 2026-08-11** — 5 R + 8 Python, one per
tool, each with its scoring header filled in against what actually printed. The
probe was frozen at `d595d1d2…` throughout and was not re-run.

**At 8 levels this is the deepest of the entries graded in thirteen tools, and
NOT the deepest in the corpus** — *corrected 2026-08-11, having first claimed
the latter. Measured: `09-stripe-openapi` 26, `02-hn-thread` 25, `10-wikidata`
and `07-graphql-introspection` 13, `05-fhir-bundle` 11, `21-crossref-works` 9.*
It has **122 paths,
eleven record shapes and four priced row candidates**. Depth is the axis none of
the four entries graded before it stressed: 13 reached 5, and 14, 15 and 17 all
reached 4.

### Depth splits the tools cleanly, and it is about where a verb stops

| answer to question 2 | tools |
|---|---|
| **8 — correct** | jq, jqr, ijson, tidyjson, DuckDB, polars, and the hand-walks in glom, purrr and pydash |
| **CANNOT** | jmespath — no depth function, no recursive descent |
| **3 of 8 — wrong** | **pandas**, because `json_normalize` stops at the first array and this document nests arrays inside arrays inside objects |

`results[] → patient.drug[] → openfda.brand_name[]` is the path that breaks it.

### Question 10 measures depth as a COST, and the spread is the finding

Reaching those 2,375 brand names, four levels down — every tool gets the same
number and pays a different price:

| | |
|---|---|
| **jq / jqr** | `[.. \| .brand_name? // empty \| .[]]` — **one expression, no level named** |
| **jmespath** | `results[].patient.drug[].openfda.brand_name[]` — one expression, every level named |
| **glom** | one spec with two `Flatten()`s |
| **rrapply** | already flattened by `melt`; filter `L7 == "brand_name"` |
| **polars** | two explodes + two struct-field accesses |
| **DuckDB** | two nested `json_each` calls |
| **pandas** | two explodes **plus** a `json_normalize` in between |
| **purrr** | **three nested `map`s and two flattens** — one nesting level per document level |
| **tidyjson** | **four `enter_object`s and two `gather_array`s** |

> **The tools that scale worst with depth are the ones whose verb is "descend one
> level".** purrr and tidyjson are the most readable and the most linear; `..`
> is the only verb in the comparison that does not care how deep the thing is.

### pandas reproduces two of the probe's row costs to the decimal

| | probe | pandas |
|---|---|---|
| an item of results | 100 x 39, 26% empty | **(100, 39), 25.7%** |
| an item of drug | 265 x 41, 47% empty | **(265, 41), 47.4%** |

**The probe prices a row shape as what dotted flattening gives, stopping at
arrays — which is exactly `json_normalize`.** The pricing model is not a guess
about tables; it is a measurement of the table this library builds.

**The one that disagrees is the whole document: probe 2 columns, pandas 8.**
pandas flattens `meta`; the probe declines to, because `$.meta` is one of the
three sites it says it **could not call**. The disagreement is the abstention.

### The abstention is a third state no tool has

The probe prints `could not call 3 small single-copy objects, shortest first`
and names `$.meta`, `$.meta.results` and `$.results[].patient.patientdeath`.
That is neither "keys are data" nor "keys are fields" but **"one copy, too few
keys to judge"**. Thirteen tools, and not one can express an abstention.

### DuckDB manufactures 464 keys, for the second document running

`unnest(results)` builds a STRUCT with the union of all 25 fields, so `::JSON`
writes the absent ones as explicit `null`:

| | key occurrences | Q4 | Q5 varying |
|---|---|---|---|
| `unnest` → STRUCT → `::JSON` | **2,500** | **25 always / 0 sometimes** | **12** |
| `json_each(json, '$.results')` | 2,036 | 14 / 11 | 1 |
| the truth | 2,036 | 14 / 11 | 0 |

`17-openlibrary` measured the same mechanism at **1,164 invented nulls**. Two
documents, one trap, and the obvious route is the wrong one both times.

### rrapply's `bind` produces the worst table in the corpus

**100 x 37,006 at 98.1% NA** — 3.7 million cells holding 69,228 values, with
names like `patient.drug.1.openfda.brand_name.1`. Positional expansion of
variable-length arrays, compounded by depth.

| | | |
|---|---|---|
| `14-nyc-311` | 20,000 x **50** | arrays exactly length 2 — **the hero** |
| `17-openlibrary` | 200 x **36** | length 1–9, depth 4 — 64% NA |
| `18-openfda-events` | 100 x **37,006** | arrays in arrays, depth 8 — **98% NA** |

**The verb never changed.** Three documents, three verdicts, and the variable is
the shape of the arrays.

### Both URLs are outside the records, for the second document running

`meta.terms` and `meta.license`. **pandas and polars report none of two**;
DuckDB finds them by accident of shape; everything that starts at the root finds
them. `17-openlibrary` had one URL and the same split.

### Question 7 has four right answers

100 results, 265 drugs, 247 reactions, and `meta.results.total` says
**20,692,690 exist**. **ijson gives all four from one pass**, because every level
is addressable in the same stream.

### Question 9: jmespath drops 96 of 100, for the fifth file running

9,261 rows on `14-nyc-311`, 923 on `13-package-lock`, 52 on `15-github-issues`,
90 on `17-openlibrary`, **96 here**. The rate is the document's; the silence is
jmespath's. And the flattening that costs it those rows is the same one that
makes its question 10 a one-liner.

### The `$` trap: five pairs, zero exposure

`serious`, `receivedate`, `receiptdate`, `transmissiondate` and `primarysource`
are all prefixes of siblings — **the most any corpus document has** — and all
five are always present, so exposure is **0 of 100**.

| entry | pairs | exposed |
|---|---|---|
| `14-nyc-311` | 1 | **199 of 20,000** |
| `13-package-lock` | 3 | **24 of 1,657** |
| `15-github-issues` | 4 | 0 |
| `17-openlibrary` | 1 | 0 |
| `18-openfda-events` | **5** | **0** |

**Five documents now pin the rule, and this is the sharpest statement of it:
more pairs is not more danger.**

### tidyjson types one field wrong, and the count tracks the nulls

`receiver` — an object on 99 results, null on 1 — comes back carrying two types
because `json_types` counts `null` as one. **Five wrong on `25-usgs-quakes`,
five on `15-github-issues`, none on `17-openlibrary` (no nulls), one here.** The
count is the document's null-bearing field count every time.

## The fourteenth tool, 2026-08-11 — `try-tidyr.R`

**This document splits question 13 cleanly, on one file and in one session: NO
for every exploration question and YES for every extraction one.**

The descent to the drug records is four verbs and **every one names the column
it is descending into**:

| | |
|---|---|
| `select(safetyreportid, patient)` | 100 x 2 |
| `unnest_wider(patient)` | 100 x 10 |
| `unnest_longer(drug)` | 265 x 10 |
| `unnest_wider(drug)` | 265 x 33 |
| `unnest_wider(openfda)` | 265 x 50 |

**The pipeline is a better form than purrr's three nested maps and it is the
same price** — you cannot write the chain without already knowing the path.
tidyr explores without being told the shape and extracts only when it is told.

**`unnest_auto` is right** (*"14 names in common"*, 100 x 25). **Depth is never
stated**: after four calls five list-columns remain, and the document's 8 levels
are learned by running out.

**The object trap, at its most misleading.** `unnest_longer(patient)` returns
**567 rows from 100 reports** — no report has many patients. 567 is the total
field count across the 100 `patient` objects, which carry 9 distinct field names
between them and not the same number each. **A row count that is a sum of field
counts still looks like a credible record count**, which is when it does most
harm.
