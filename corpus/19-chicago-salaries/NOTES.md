# 19 — Chicago city employee salaries

## The expectation, written 2026-08-09 before the probe was run

```
design/probe.py   981a45f023e8de6f0db5951e33c4a4b4d5d6d75b
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Disclosure

*Of the specimen.* It is a JSON array of 5,000 objects. No field name read.

*Of the instrument.* None read for this file.

*Of prior knowledge.* I know this dataset pays some staff a salary and some an
hourly rate, and that the two are recorded with different columns. **Prediction 2
rests entirely on that** and is the sharpest thing in this entry.

### Why this file

**Third of the three the gate needs.** Chosen ordinary, and deliberately a
**second Socrata export** after `14-nyc-311` rather than a fourth new shape.
`QUESTIONS.md` question 14 asks whether an answer survives the next file of
nominally the same kind, and `16-movie-ratings` answered it for one collector's
daily runs. **This asks the weaker, more common version: two unrelated datasets
from the same platform.**

### What is predicted

**1. Flat, depth 2, explosion near 1.0**, like `14-nyc-311`.

**2. A SPLIT FIRES on the salaried-versus-hourly field, and this is the
prediction that matters.** A salaried employee carries an annual figure and no
hourly rate; an hourly employee carries a rate and typical hours and no annual
figure. **That is a discriminator present in every record whose value genuinely
determines which other fields exist** — operation 4's textbook case, in a
municipal payroll.

> **I have predicted splits wrongly twice in a row** — `17-openlibrary` (said no,
> one fired and was right) and `18-openfda-events` (said yes, none exists). **So
> this one is a real test of whether I can read a document in advance at all**,
> and it is recorded knowing that.

**3. Ragged by absence, and the absence is exactly the split.** Predicted: a
handful of fields, roughly half sometimes-absent, and the missing ones line up
with the two pay types rather than being scattered.

**4. keys-as-data 0, polymorphism 0, recursion 0.**

**5. Under 40 lines**, and the `└─ or N tables` join appearing under the row
candidate if prediction 2 holds.

**6. The sentinel rule stays silent.** Socrata omits.

**7. `rows("*")` returns 5,000 rows, no list-columns** — a flat export is
`rows()`'s clean case, as `14-nyc-311` was.

---

## Provenance

| | |
|---|---|
| what | **Chicago city employee names, positions and salaries**, first 5,000 |
| source | `data.cityofchicago.org/resource/xzkq-xp2w.json?$limit=5000` |
| fetched | 2026-08-09 |
| size | 944,651 bytes, **5,000 records**, committed |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers, no
encoded documents, no sentinel report. **22 lines of output.**

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 944,651 · depth **2** · paths 9 · fields 8 · explosion **1.1** |
| keys-as-data | 0 · ragged by absence **3/8** · ragged by null 0 |
| recursion | 0 · polymorphic 0 · heterogeneous 1 · path variance 0 · row shapes 1 |

## Prediction scorecard: seven of seven

| # | predicted | outcome |
|---|---|---|
| 1 | flat, depth 2, explosion ~1.0 | **confirmed. Depth 2, explosion 1.1** |
| 2 | **a split fires on salaried-versus-hourly** | **confirmed exactly** |
| 3 | absence lines up with the split | **confirmed. 3/8, and they are the three pay fields** |
| 4 | keys-as-data 0, polymorphism 0, recursion 0 | **confirmed, all three** |
| 5 | under 40 lines, the join appears | **confirmed. 22 lines** |
| 6 | sentinel rule silent | **confirmed** |
| 7 | `rows("*")` → 5,000 rows, no list-columns | **confirmed. 5,000 × 9** |

## What the file established

### 1. NO DEFECT — and this is the THIRD consecutive quiet file. The gate is closed

`design/implementation.md` gates the Rust port on *the probe's output ceasing to
change across three consecutive corpus files*. **Files 17, 18 and 19 each ran
cold against `981a45f0…` and none required a repair.** The counter had never
previously got past one.

### 2. The cleanest demonstration of the whole pattern the corpus contains

```
$[]   5000 copies · 8 fields · 2 distinct key-sets
  always     department full_or_part_time job_titles name salary_or_hourly
  sometimes  annual_salary(3938) typical_hours(1062) hourly_rate(1062)
  SPLIT ON   salary_or_hourly — 2 kinds, not one shape. 22% empty folded, 0% after
    SALARY   3938 x 6 cols   0% empty
    HOURLY   1062 x 7 cols   0% empty

ONE ROW COULD BE
  a record          5,000 rows x 8 cols   22% empty
    └─ or 2 tables, split on salary_or_hourly — 0% empty: SALARY 3,938, HOURLY 1,062
```

**Fold, then partition, then price — all four operations in twelve lines, ending
at zero holes.** A salaried employee has an annual figure and no hourly rate; an
hourly employee has a rate and typical hours and no annual figure. The document
says which it is in every record, and the probe reads it, splits on it, and
prices both answers.

**Nothing in the corpus states the thesis more plainly**: one 5,000-record
document, described in 22 lines, with the 22%-empty table and the 0%-empty pair
of tables offered side by side.

### 3. And it settles that a prediction can be made in advance

Three files ago I had predicted splits wrongly twice running — `17-openlibrary`
said no and was wrong, `18-openfda-events` said yes and was wrong. **This entry
recorded the risk before running and then landed seven of seven.** The difference
is that here the prediction rested on a claim about the *document's* structure —
two pay regimes recorded with different columns — rather than on a guess about
what the probe would do with it.

## The thirteen tool attempts, 2026-08-10

Five R tools, eight Python. **Every one agrees**: 5,000 records, 8 fields, 5
always and 3 sometimes, `annual_salary` 3,938 + `hourly_rate` 1,062 = 5,000
exactly, 4,430 values matching `/DEPARTMENT/`, and the split from 22% empty to
0%. That unanimity is what makes the two silences worth reading.

### 1. `json_schema` discarded the majority field — sixth document, sixth discard

**This entry was chosen for the tidyjson attempt as the case where the function
should finally be right**, because both key-sets are FLAT and nothing forces a
choice between nesting levels or between a scalar and an object. It discarded
anyway:

```
json_schema:  department full_or_part_time hourly_rate job_titles
              name salary_or_hourly typical_hours          7 of 8 fields
missing:      annual_salary                                on 3,938 of 5,000
```

**It kept the 1,062-record HOURLY fields and dropped the 3,938-record salaried
one.** That is the second document running where it keeps the minority shape —
`11-jupyter-notebook` kept the 27-output `stream` shape and dropped the other
80. Six documents, six silent discards, and the prediction is left wrong in the
attempt file because the miss is the finding.

### 2. Every tool reports the salaries as text, and every one is right

`annual_salary` holds `"165624"` and `hourly_rate` holds `"9.46"` — **JSON
strings, not numbers.** All thirteen tools type them `string`/`chr`/`VARCHAR`
and none warns, because none is wrong. `max(annual_salary)` returns a
lexicographic maximum in pandas, polars, DuckDB, jsonlite and jq alike, silently.

> **A document that is uniformly wrong about its own types is invisible to a
> type report.** This is not the polymorphism question and no corpus axis
> measures it: the file is perfectly consistent and perfectly misleading.
> `README.md`'s health list owns duplicate keys, big ints, `NaN` and encoded
> documents; **numbers-as-text is a sixth category and no instrument here has
> it.**

### 3. Thirteen tools can all make the split and not one proposes it

`salary_or_hourly` is a discriminator INSIDE the record, two values, perfectly
partitioning. `pandas.groupby`, `polars.group_by`, `pydash.group_by`, SQL's
`GROUP BY`, jq's `group_by`, R's `split` — **six of the thirteen have the verb,
it is one line in each, and nothing in any tool's output suggests the document
wants it.** The corpus's recurring sentence, on the document that states it most
cleanly: the contribution is the looking, not the arithmetic.

### 4. Where the easy document changes the tool rankings

**This is the only corpus entry where `fromJSON(path)` with no arguments is the
whole extraction answer**, and the only one where `pydash`'s key walk is exactly
right — 8 names for 8 fields, against 3,126 for npm's 40. Neither tool improved;
the document has no keys-as-data, no nesting and no arrays for them to get wrong.

**`ijson`'s prefix listing is 0.02% of the file**, the corpus's smallest by a
distance against 111% on npm and 174% on Stripe. Nine prefixes for 5,000
records is what *proportional to structure* looks like when a tool gets it free.

**`rrapply`'s melt is the mirror image**: it turns an already-rectangular
5,000-row table into 38,000 leaf rows and has no verb to put it back, because
`how="bind"` needs the regularity the two key-sets deny it.

## What it disconfirmed

**That the Socrata platform makes documents alike.** `14-nyc-311` is the same
platform, the same export machinery, and no split exists in it at all — its
raggedness is submission completeness cutting across every categorical field.
This one partitions perfectly on the first field you would try. **Two datasets,
one platform, opposite answers to question 3**, which is the strongest available
answer to *"does the code survive the next file of nominally the same kind?"* in
its weaker form: **no, and the reason is the data rather than the format.**


## The fourteenth tool, 2026-08-11 — `try-tidyr.R`

**This entry gives `VERDICT.md`'s sharpest arithmetic its second document, and
it is the one where the loss is total rather than partial.**

`21-crossref-works` found pandas and polars pricing a split at exactly the
unsplit emptiness and called it **necessary rather than coincidental**: a frame
has committed to all its columns, so the size-weighted mean of the group
emptinesses *is* the global emptiness for every possible split. Measured here on
a second document and a third tool:

| as a frame | |
|---|---|
| unsplit emptiness | **0.2235** |
| `HOURLY`, n = 1,062 | 0.1250 |
| `SALARY`, n = 3,938 | 0.2500 |
| size-weighted mean | **0.2235** — equal |
| worst group | 0.2500 |

| recomputing each group's column set, as jq and DuckDB do | |
|---|---|
| `HOURLY` keeps **7** columns | **0.0000** |
| `SALARY` keeps **6** columns | **0.0000** |

> **The split is PERFECT and the frame scores it at zero benefit.** Salaried
> employees have no hourly rate and hourly employees have no annual salary, so
> `salary_or_hourly` partitions the holes completely. **0.2235 → 0.0000
> recomputed, 0.2235 → 0.2235 as a frame.** That is not a tool missing a verb;
> the rectangle cannot represent the quantity the search is for.

**The discriminator is sitting in plain sight as a column**, taking two values,
with every hole on one side of it.

**5,000 x 8 with zero list-columns and all eight columns character** — the one
document of the fourteen where the flattest honest table is the document itself,
and where question 5 answers *no* because `annual_salary` is the string
`"$100,000.00"` and stays one.
