# 06 — ESPN QBR, the file with a published answer

## The expectation, written 2026-08-09 before `source.json` was saved

**Committed as its own change, before the file exists in the repository.** The
grading sections are filled in after the cold runs.

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   c0a607d86088d64d4a2e110d31dd4d5fe39885f7   <- REPAIRED since file 05
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703   <- unchanged, second cold run
```

**Disclosure, because "before measuring" has to mean it.** Two things were already
seen before this was written. The endpoint was checked live on 2026-08-09 to
confirm it still answers — **HTTP 200, 180,604 bytes, `athletes` of length 28** —
and its seven top-level keys were listed: `athletes`, `categories`,
`currentSeason`, `currentValues`, `glossary`, `pagination`, `requestedSeason`.
Nothing below that level has been looked at. The rest of what informs these
predictions comes from the published tutorial, which is the whole point of the
file.

### Why this file, when it is the easiest thing in the corpus

Raised by the author. Tom Mock, *Parsing JSON in R with jsonlite*,
themockup.blog, 2020-05-22. **Its value is not difficulty**, and `VERDICT.md`
carries the argument at length. In short:

1. **It is the only fair fight available.** Rule 6 exists because the probe was
   once benchmarked against tools given one attempt each. Here the competing
   solution is already written, by an R educator, polished for publication, after
   four documented approaches. A frozen probe getting one cold run against that
   inverts the bias rather than controlling for it.
2. **It has a ground truth.** No other corpus file has a known-correct output.
3. **It states the thesis independently**, in 2020, by someone with no stake:
   *"I highly recommend that you DON'T blindly call `str()` on JSON objects —
   you'll get several pages of stuff output."*

**The row count moved and that is recorded before it can become a wrong number.**
The post reports 30 quarterbacks. The same URL today returns **28**. The ground
truth is therefore the *shape and the path*, never the count.

### What is predicted

**1. The probe proposes the row the human chose.** `ONE ROW COULD BE` should
name **`an item of athletes` at 28 rows**. This is the ground-truth test and the
reason the file is here. Anything else at the top is a miss.

**2. Nothing splits.** `SPLIT ON` must **not** fire anywhere. One homogeneous
`athletes` array is exactly the case folding already handled, and the partition
operation was implemented four commits ago against a single file. **A split here
is a false positive in a repair that has never been held out**, and it is the
outcome that would matter most.

**3. No recursion, and none reported.** The repaired detector requires
reachability. A flat API response should produce nothing.

**4. Depth about 7**, from the tutorial's own description of the nesting.

**5. Short — under 60 lines.** Four files gave 73, 25, 31 and ~10, and file 05
gave 393. This is a small normalised API response and folding should work
perfectly on it. **If this runs long, the probe is verbose on easy documents,
which would be a worse finding than any of file 05's**, because it would mean the
tool only pays for itself on pathological input.

**6. The hard part is that the column names are not next to the values, and I
predict the probe cannot say so.** The tutorial's extraction is
`pluck("athletes", n, "categories", 1, "totals")`, and the ten statistics come out
as a bare vector — `TQBR`, `PA`, `QBP`, `TOT`, `PAS`, `RUN`, `EXP`, `PEN`, `QBR`,
`SAC` are supplied from elsewhere in the document, not from the object holding the
numbers.

> **This is a structure the corpus has never held: a table stored as parallel
> arrays, where the names live in one place and the values in another, related
> only by position.** Predicted: the probe reports an array of ten numbers, says
> nothing about what they are, and offers no candidate that recovers the labels.
> `keys-as-data` will not fire, because the keys are not keys anywhere — they are
> *elements of a different array*.

If that holds it is a **new axis**, and arguably a fifth operation. It is written
here before the run so that it cannot be claimed afterwards as something the
design anticipated.

**7. keys-as-data: 0 or 1.** `glossary` is the only plausible site.

---

## Provenance

| | |
|---|---|
| what | ESPN NFL Quarterback Rating, 2019 regular season, qualified passers |
| source | `site.web.api.espn.com/apis/fitt/v3/sports/football/nfl/qbr`, see `fetch.sh` |
| fetched | 2026-08-09 |
| size | 180,604 bytes, committed |
| why | Tom Mock, *Parsing JSON in R with jsonlite*, themockup.blog, 2020-05-22 |
| drift | the post reports **30** quarterbacks; the endpoint now returns **28** |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no integers past 2^53.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 180,604 |
| depth | **7** |
| recursion | 0 |
| distinct paths | 131 |
| fields | 72 |
| explosion | 1.8 |
| keys-as-data | 0 |
| ragged by absence | **0/56** |
| ragged by null | 0 |
| polymorphic | 0 |
| heterogeneous | 0 |
| path variance | 17 |
| row shapes | 7 |

**Every raggedness axis is zero.** This is the regular, normalised, API-served
document the corpus did not have, and its being easy is the point.

> **Regraded 2026-08-11: row shapes is now 9.** The table above is left at 7
> because it records what was measured on the day. **Defect 27's repair added
> the two positionally aligned tables to `ONE ROW COULD BE`** — `a position in
> $.categories[]`, 10 x 4, and `a position in $.athletes[].categories[]`,
> 280 x 2 — and this file is one of only two in the corpus that has any.
>
> **What the menu used to offer instead is the finding.** `an item of glossary`,
> 10 rows x 2 cols, was in the list; the 10 x 4 was not. **`glossary` is the
> decoy this entry exists to document** — the same ten names in a different
> order, whose join reports the league's best quarterback at -7.4 — and the
> probe was naming the trap and withholding the table. See `FINDINGS.md`,
> 2026-08-11.

## Prediction scorecard: seven of seven

| # | predicted | outcome |
|---|---|---|
| 1 | proposes `an item of athletes` at 28 rows | **confirmed**, second candidate listed, `28 rows x 32 cols` |
| 2 | nothing splits | **confirmed. 0 splits** |
| 3 | no recursion reported | **confirmed. 0** |
| 4 | depth about 7 | **confirmed. exactly 7** |
| 5 | under 60 lines | **confirmed. 44** |
| 6 | cannot connect names to values | **confirmed, and understated — see below** |
| 7 | keys-as-data 0 or 1 | **confirmed. 0** |

**Seven of seven is a weaker result than file 05's three of six, and saying so is
the point.** The predictions were made with the tutorial in hand, on a regular
document. A scorecard is only evidence when it can come out badly.

## What the file established

### 1. The repair holds. This is the first held-out evidence for it.

The partition operation and the reachability fix were both fitted against files
01–05 four commits earlier and had **no held-out evidence at all**. On a document
with one homogeneous array and no recursion:

- **`SPLIT ON` fires zero times.** The operation stays silent when there is nothing
  to split, which is the false positive that would have mattered most.
- **`RECURSIVE` appears zero times.**

### 2. It named the row a human chose, which nothing else here has been scored on

`ONE ROW COULD BE` offers **`an item of athletes  28 rows x 32 cols`**. The
tutorial's answer is one row per quarterback. **No other corpus file has a
known-correct output, so this is the first time the row proposal has been scored
against a human's published choice rather than against whether it looked
sensible.**

The tutorial keeps 14 columns where the probe offers 32. That is not a
disagreement — the probe proposes the row and the person picks columns, which is
what `take` is for.

### 3. The failure: the document's schema is a single-copy object, and the fold cannot see it

**The probe never mentions `labels`. Zero occurrences in 44 lines.**

`$.categories[0]` holds four parallel arrays of length 10 that name and explain
every statistic in the file:

```
labels        TQBR  PA  QBP  TOT  PAS  RUN  EXP  PEN  QBR  SAC
names         schedAdjQBR  qbpaa  actionPlays  cwepaTotal  …
displayNames  TOTAL QBR  Points Added  QB PLAYS  TOTAL EPA  …
descriptions  "Adjusted Total Quarterback Rating, which values …"
```

and each aligns by position with the ten values in every
`athletes[].categories[].totals`. **`labels` is exactly the tutorial's column
order**, and `totals[0] = 83.0` is that quarterback's Total QBR.

The probe reports `$.categories[]` only inside *"could not call 9 small
single-copy objects"*. It is skipped by `len(objs) < 2` in the folding loop.

> **The load-bearing idea has a blind spot exactly where documents keep their
> schemas.** Folding sibling instances is what makes output proportional to
> structure, and a document's description of itself characteristically appears
> **once**. The probe has always summarised single-copy objects as noise — file 01
> summarised 17 of them. Here the single-copy object was the most important thing
> in the document.

### 4. And there is a decoy, which is why this is a trap rather than a gap

`$.glossary` is an array of **10** objects carrying the **same ten
abbreviations**, and the probe *does* report it — both as a record shape and as a
row candidate, `an item of glossary  10 rows x 2 cols`. It is the only naming
information the probe surfaces.

**It is in a different order.** `glossary` is sorted alphabetically:

```
glossary   EXP  PA  PAS  PEN  QBP  QBR  RUN  SAC  TOT  TQBR
labels     TQBR PA  QBP  TOT  PAS  RUN  EXP  PEN  QBR  SAC     <- the real order
```

Joining `totals` against `glossary` by position — the obvious move, and the only
one the probe's output supports — reports **`TQBR = -7.4`** for the top-rated
quarterback in the league, whose Total QBR is **83.0**.

> **Two arrays of the same length holding the same names in different orders, one
> of which is correct.** The wrong join produces plausible numbers, in the right
> range, with no error, and the probe points at the wrong array. This is the
> failure mode the project exists to care about: not a crash, an answer.

### 5. `rows()` produces list-columns, which the god seam refuses

Second cold run for `rows.py`, hash verified beforehand:

```
rows('athletes.*')                    28 rows x 3 cols
rows('athletes.*.categories.*')       28 rows x 6 cols
    totals   ['83.0', '66.7', '613', '103.7', …]
    ranks    ['1', '-', '-', '-', …]
```

`totals` and `ranks` arrive as **list-columns**. `CLAUDE.md` records that god's
spec refuses nested data as a value and that the seam between the projects is a
data frame, so **the natural extraction from this file produces something god
cannot accept**. Expanding it needs the names, and the names are in the
single-copy object `rows()` was never pointed at.

This is the first corpus file to put pressure on the seam rather than on fathom
alone.

## What it disconfirmed

**That an easy document is an uninformative one.** Every raggedness axis is zero
and the file was chosen for its published answer, not its difficulty. It produced
the first held-out evidence for the partition repair, the first scoring of a row
proposal against a human's choice, and a new failure that five hard files did not
surface — because they were all chosen for raggedness, and this one was chosen for
having an answer.

## The R half — predictions, written 2026-08-10 BEFORE the tools were run

**Committed as its own change, before any file exists in `r/` beyond the tidyr
attempt.** Rule 1.

**This is the only fair fight in the corpus and the reason is rule 6.** Every
other entry compares a probe revised against the document with tools given one
attempt. Here the competing solution is *already written*, by an R educator, for
publication, after four documented approaches — Tom Mock's
`raw_json %>% purrr::pluck("athletes", n, "categories", 1, "totals")` — and it
uses **purrr and jsonlite**, two of the five tools being run. The bias runs
against this project for once.

**1. purrr will look better here than on any other corpus file.** `0/56` ragged
by absence, `0` by null, no recursion, no keys-as-data. Predicted: question 8
needs **no `%||%` anywhere**, as on `03-natural-earth`, and reads shorter than
the published `pluck` chain because `pluck` walks one athlete at a time.

**2. THE DECOY WILL FOOL THE RECTANGLE-BUILDERS TOO, and this is the prediction
worth running.** `$.glossary` is 10 objects of `{abbreviation, description}` —
tabular, and `jsonlite` should turn it into a clean **10 × 2 data frame**.
`$.categories[0].labels` is a bare character vector of 10 nested two levels
down, and it is **the correct order**. Predicted: **simplification surfaces the
wrong array and buries the right one**, for the same reason the probe did — one
looks like records and the other looks like a vector. If a `10 × 2` frame appears
in `str()` at level 3 while `labels` needs level 5 or deeper, that is the
measurement.

**3. But `str()` and `json_schema` do NOT fold, so they should SHOW the
single-copy object the probe skipped.** The probe misses `labels` entirely
because `len(objs) < 2` drops single-copy objects from the fold. jsonlite and
tidyjson have no such rule. Predicted: **`labels` is visible in `str()` output**,
which would make this the third time an existing tool surfaces something the
probe's own load-bearing idea discards — after `jqr` and `rrapply` on
`03-natural-earth`.

**4. Ground truth on question 3.** Predicted: `jsonlite::fromJSON` returns
`athletes` as a **28-row data frame** with no verb chosen, and `tidyjson`'s
`gather_array` gives 28 rows, both matching the row a human published. The
tutorial keeps 14 columns; the tools will offer more, which is `take`'s job and
not a disagreement.

**5. Question 7a is CIRCULAR and will not be scored.** `QUESTIONS.md` marks it
as added the same session the probe gained the feature that answers it. The
alignment between `labels` and `totals` is measured below as a FACT about the
document, not as a score against any tool.

**A prediction that would hurt.** If an R tool volunteers the `labels`/`totals`
alignment unprompted, then "nobody helps you explore" is wrong on the one
document where the corpus has a published human answer to check against.

## The R half, run 2026-08-10 — the fair fight, scored

**All five R tools run; the entry is done.** Predictions were committed in
`5b665ef`, before any file in `r/` existed beyond the tidyr attempt.

| # | predicted | outcome |
|---|---|---|
| 1 | purrr needs **no `%||%`** anywhere | **confirmed.** 28 × 3 in three lines, no defaults |
| 2 | simplification **buries** the right array | **HALF WRONG** — it does not bury it, it makes the *wrong* one inviting |
| 3 | `str()` **shows** the single-copy `labels` | **confirmed.** Visible from level 2, where the probe never mentions it |
| 4 | jsonlite gives a **28-row** athletes frame | **confirmed**, unprompted, matching the published row |
| 5 | 7a not scored (circular) | **honoured** — recorded as a fact about the document |

**The prediction that would have hurt did not happen**: no R tool volunteers the
`labels`/`totals` alignment.

### 1. purrr wins the extraction outright, against a published purrr answer

`README.md` calls purrr *"the best answer that exists"*, and this is the only
document where that meets an expert's polished solution using the same tool.

```
tutorial   raw_json %>% pluck("athletes", n, "categories", 1, "totals")   one athlete
map_dfr    28 x 3, no %||% anywhere, all 28 at once
```

**Nothing this project could build would improve on that.** `NOTES.md` grades
`0/56` ragged and `0` null, so purrr has nothing to work around — the contrast
with `05-fhir-bundle`, where the same three lines need a default on every field
but two, is the document rather than the tool.

### 2. The decoy fools the rectangle-builders — but not the way I predicted

I predicted simplification would **bury** `labels`. It does not: `str()` shows
both `glossary` and `labels` from level 2. What it does is make the **wrong one
inviting**:

```
$glossary           data.frame: 10 x 2      <- ready to join
$categories$labels  list of 10, inside a 1-row frame   <- must be unlisted first
```

**Equally visible, not equally usable, and the usable one is alphabetical.**
The correction is sharper than the prediction was.

```
Lamar Jackson's ten totals   83  66.7  613  103.7  55  39.1  0  2.2  82.3  -7.4
join against labels    (correct)   TQBR = 83.0
join against glossary  (decoy)     TQBR = -7.4
```

**And the wrong join is partly right, which is why it survives**: position 2 is
`PA` in both orders, so `PA = 66.7` is correct either way. A join producing some
correct values, plausible numbers for the rest, and no error.

### 3. The trap is EXPRESSIBLE — which is a weaker and truer claim

jq states the collision in one expression, with no knowledge of football:

```
{"same_length": true, "same_set": true, "same_order": false}
```

Two arrays of equal length holding the same set of strings in a different order
is exactly the condition under which a positional join is a coin flip. And
`.categories[0].labels as $L` then names the columns **from the document** —
strictly better than the published tutorial's `totals[1]`, a magic number that
is correct because its author checked.

rrapply reaches it sideways: in a melted frame, **18 of 23 non-numeric values
appearing under more than one top-level branch are `glossary + categories`** —
all ten abbreviations and their display names. The filter is the whole
difficulty: unrestricted, the test returns 29 hits dominated by small integers
and finds nothing; restricted to non-numeric it is unmissable.

> **So the honest form of this file's finding is not *no existing tool can do
> this*.** The test is one line, the fix is one clause, and **nothing looks
> unprompted**. That is a smaller claim than *nobody helps you explore*, and it
> is the one the evidence supports — and a more useful specification, because
> the thing to build is not a new capability, it is the *looking*.

### 4. `str()` shows what the probe's fold discards

The probe never mentions `labels` in 44 lines, because `len(objs) < 2` drops
single-copy objects. jsonlite has no such rule, so the most important object in
the document is simply present from `str()` level 2. **Third time an existing
tool surfaces what the load-bearing idea throws away**, after `jqr` and
`rrapply` on `03-natural-earth`.

### 5. `json_schema` passes cleanly here, and that settles what the claim is about

**72 true key names, 72 named in the schema, 100% covered**, 1.3% of the file,
14.7 s. The coverage instrument needed a case where the tool is right, and this
is it.

| file | `json_schema` | what was lost |
|---|---|---|
| `03-natural-earth` | small, constant | a nesting level, order-dependently |
| `05-fhir-bundle` | small, constant | key names — coverage 100% → 36% |
| `10-wikidata` | **grew** with data | a type, in both orders |
| `07-graphql` | 100% covered | a generality — recursion flattened to a bound |
| `04-gharchive` | **did not finish** | CANNOT, 25.5 KB/s |
| **`06-espn-qbr`** | **100% covered** | **nothing measurable** |

**The losses are about HETEROGENEITY, not about the function.** Given one shape
it describes that shape; given several it picks one and says nothing about
having chosen.

### 6. And the melt ratio confirms the corrected statistic a third time

**140%** — mid-table, on the file `NOTES.md` calls the easiest in the corpus.

| `04` 52% | `05` 60% | **`06` 140%** | `09` 141% | `10` 173% | `07` 204% | `03` 226% |
|---|---|---|---|---|---|---|

Under the reading used until this week — that the percentage tracks how badly a
tool fails to fold — the easiest document should be the cheapest and is not.
Under the correction `07-graphql-introspection` forced, `flat, regular, short
values under short paths` puts it exactly here. 7,121 leaves fold to **95 path
shapes**, a 75× fold at 1.5%.

## Status

**R half complete 2026-08-10** — purrr, jsonlite, tidyjson, rrapply, jqr, plus
tidyr. Python is 8 attempts. Under `CLAUDE.md`'s definition this entry is done.

## Corrected 2026-08-13: 53 → 56 leaf names

**The grades above are left alone.** `paths(scalars)` drops every `false` and
`null` leaf — see `01-npm-registry`. The three invisible names were
**`isExternal`**, **`isPremium`** and **`week`**.

**THE FINDING IS UNCHANGED**: 56 against `NOTES.md`'s 72 fields is still UNDER.
