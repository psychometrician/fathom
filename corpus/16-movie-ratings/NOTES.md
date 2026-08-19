# 16 — daily movie ratings, with a published walkthrough

## The expectation, written 2026-08-09 before the probe was run

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   a9e17af043495be40867a277485a4287385d94b8
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Disclosure — the largest in the corpus, and unavoidable

The author supplied this file, so choosing it involved reading it. **Seen before
these predictions were written:** the notebook's whole JSON section, the two
key-sets and their intersection, two sample records, and the first 30 lines of
the collector. **These predictions are correspondingly cheap and are scored as
such.** What has not been done is run the probe, `axes.py` or `rows.py`.

### Why this file — and it costs the gate, stated up front

**`14-nyc-311` and `15-github-issues` both found nothing and the gate counter is
at 2 of 3.** A third quiet file would close it. **This file will almost certainly
not be quiet**, so running it now spends the counter.

**That is the right trade and the reason is the method itself.** Choosing an easy
file to close a counter is the same error as validating a guard against fitted
documents — which `13-package-lock` had just demonstrated costs more than it
saves. The corpus's job is to find out what is true, not to close a counter, and
a document that exposes a real gap is worth more than a document that lets the
Rust port start on a design that still has one.

**What it is.** Rachael Tatman's *Data Cleaning Challenge: .json, .txt and .xls*
(Kaggle, 2018), and the "Ratings vs Gross" dataset it teaches from — three daily
scrapes and the collector that produced them.

**Three things the corpus cannot get elsewhere:**

**1. It is the second ground truth, after `06-espn-qbr`.** `VERDICT.md` argues
for these at length: rule 6 exists because the probe was once benchmarked against
tools given one attempt each, and a published tutorial is an expert's polished,
unlimited-attempt answer. It also states two of this project's claims
independently, in 2018, by someone with no stake in it:

> *"If we did want to convert this to a tabular data structure, we'd need to have
> a column for every single different value recorded for each observation. This
> might lead to having a very large data frame that's mostly empty!"*

That is **operation 3** — pricing a candidate row shape, and naming holes as its
cost — written by an R educator six years before this repository existed. And:

> *"It's much simpler to represent this dataset with a hierarchical data
> structure of nested lists instead."*

which is `README.md`'s **"a table is the shape of your answer, never the shape of
the document"**, reached independently.

**2. It makes question 14 answerable for the first time.** *"Does the code
survive the next file of nominally the same kind, unchanged?"* has been in
`QUESTIONS.md` since the start and **no corpus entry has ever had a second file
of the same kind.** Three daily runs of one collector is exactly that, so
`next-2018-2-7.json` and `next-2018-2-8.json` are committed alongside.

**3. It is a second producer document.** `11-jupyter-notebook` established that
polymorphism needs more than one producer. `collector.py` scrapes **IMDB and
Rotten Tomatoes** and merges them, which is why the same movie set carries two
different key-sets.

### What is predicted

**1. `always (none)` — no field present in every record.** The two key-sets are
`{Genre, Gross, IMDB Metascore, Popcorn Score, Rating, Tomato Score}` on 15
movies and `{popcornscore, rating, tomatoscore}` on 23, and **their intersection
is empty.** That is `04-gharchive`'s exact signature.

**2. No split, and `discriminator()` cannot even start.** It needs a field
present in every instance; there is none. Predicted: silence, and correct
silence — but silence on a document where the split is obvious to a human and
would pay handsomely. **Third document with this signature**, after gharchive and
`12-agent-trace`'s two sites.

**3. Path variance by renaming — the SECOND instance, and the second file to
demand `first_present`.** `Rating`/`rating`, `Popcorn Score`/`popcornscore`,
`Tomato Score`/`tomatoscore` are the same logical field twice. `VERDICT.md`
records that the word's case rests on `05-fhir-bundle` alone; this would make it
two documents from unrelated domains — a specification and a scraper.

**4. Keys-as-data on the movie titles.** One copy, 38 keys, so the single-copy
branch and `KEYED_MIN` should call it data.

**5. Genuine polymorphism at the scores.** `Popcorn Score` is the number `72` on
one movie and the string `"unknown"` on another. Predicted: reported, and not
labelled an artifact.

**6. THE ONE I EXPECT THE PROBE TO MISS, and it is a new category.**
Missingness is encoded as the **string `"unknown"`** — and on one record as
`"unkown"`, misspelled. Every emptiness measure in the probe counts a key with a
value as filled, so a record reading `Gross: "unknown", Popcorn Score: "unknown",
Tomato Score: "unkown"` is **100% full by every number the probe prints.**

> `README.md`'s health section lists duplicate keys, big integers, `NaN` and
> encoded documents as the silent damage worth owning. **A sentinel string
> standing in for a missing value is not on that list and is probably more
> common than all four**, and the misspelling means even a sentinel-aware tool
> would miss one of the three here.

**7. Depth 3, recursion 0, and under 40 lines** on a 6,975-byte file.

**8. `rows()` on the inner object returns 38 rows** with the title as the key
column — and the two key-sets should give it a table that is about half holes.

---

## Provenance

| | |
|---|---|
| what | **"Ratings vs Gross"**, daily IMDB + Rotten Tomatoes scrape, 38 movies |
| ground truth | Rachael Tatman, *Data Cleaning Challenge: .json, .txt and .xls*, Kaggle 2018 — committed as `ground-truth.ipynb` |
| supplied by | the author, 2026-08-09, as a `kaggle/` folder |
| `source.json` | `2018-2-4.json`, **6,975 bytes, 38 movies** — the file the notebook walks through |
| also committed | `next-2018-2-7.json` (36 movies), `next-2018-2-8.json` (38) for question 14; `collector.py`, the scraper that produced all three |

**The smallest file in the corpus**, at 6,975 bytes against `08-open-meteo`'s
12,198. Kept because it is real, has a published answer, and is dense rather than
large — `corpus/README.md` bans toy JSON, not small JSON.

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers, no
encoded documents. **22 lines of output** for a 6,975-byte file.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 6,975 · depth **3** · paths 198 · fields 10 · explosion **19.8** |
| keys-as-data | **1** · ragged by absence **9/9 — every field, the maximum** · ragged by null 0 |
| recursion | 0 · polymorphic **2** · heterogeneous 0 · path variance 0 · row shapes 2 |

## Prediction scorecard: eight of eight — and they were cheap

**Every prediction landed, and the disclosure section says why that is worth
little**: the file was supplied by the author and choosing it meant reading it.
Scored anyway, because the record has to be comparable.

| # | predicted | outcome |
|---|---|---|
| 1 | `always (none)` | **confirmed, exactly** |
| 2 | no split; `discriminator()` cannot start | **confirmed** |
| 3 | path variance by renaming, second `first_present` demand | **confirmed structurally — but `axes.py` grades it 0, see below** |
| 4 | keys-as-data on the titles | **confirmed. `{38 keys} one copy, 38 keys — not a field list`** |
| 5 | polymorphism at the scores | **confirmed. `Popcorn Score number x9, text x6`, no artifact label** |
| 6 | the `"unknown"` sentinel is invisible | **confirmed, and worse than predicted — see below** |
| 7 | depth 3, under 40 lines | **confirmed. Depth 3, 22 lines** |
| 8 | `rows()` → 38 rows | **confirmed. 38 × 11** |

## What the file established

### 1. QUESTION 14 IS ANSWERED, for the first time in the corpus, and the answer is yes

*"Does the code survive the next file of nominally the same kind, unchanged?"*
has been in `QUESTIONS.md` since the first day and **no entry has ever had a
second file of the same kind.** Three daily runs of one collector:

| | records | fields | key-sets | always | spellings |
|---|---|---|---|---|---|
| `2018-2-4` | 38 | 9 | 2 | none | 23 / 15 |
| `2018-2-7` | 36 | 9 | 2 | none | 22 / 14 |
| `2018-2-8` | 38 | 9 | 2 | none | 22 / 16 |

**The description is structurally identical on all three. Only the counts move.**
Same nine fields, same two key-sets, same `always (none)`, same two spellings,
same polymorphic pair. `rows('*.*')` returns 38 / 36 / 38 rows × 11 columns.

> **This is the clearest demonstration the corpus has produced of *output
> proportional to structure rather than to data*.** Three different documents,
> one description, and the only things that changed were the numbers that should
> change. It is also the first evidence that a fathom expression written for one
> file would still run on the next one — which is the retention bar `README.md`
> sets and the thing `QUESTIONS.md` question 14 exists to test.

### 2. DEFECT — missingness encoded as a string, and every number the probe prints is wrong by it

Predicted, and worse than predicted. Measured:

```
17 of 159 present cells are sentinels     "unknown" x11   "unkown" x6
probe says 54% empty        the truth is 58% empty
```

**The misspelling is systematic, not a slip: `"unkown"` appears six times.** So a
tool that special-cased the string `"unknown"` would still miss a third of them.

`README.md`'s health section owns duplicate keys, integers past 2^53, `NaN` and
encoded documents. **A sentinel string standing in for a missing value is not on
that list, and on this document it is more common than all four combined — they
score zero.** Every emptiness measure in the probe counts a key with a value as
filled, so a record reading `Gross: "unknown", Popcorn Score: "unknown", Tomato
Score: "unkown"` is **100% full by every number printed.**

**This is a new health category and the corpus's first specimen of it.**

### 3. The `always (none)` signature, third document

`$[].<key>` has **9 fields and no field present in every record**, because the
two key-sets are disjoint. `discriminator()` requires a field present in every
instance and there is none, so it cannot start.

**Third document with `04-gharchive`'s signature**, after gharchive itself and
`12-agent-trace`'s two sites. The split here is obvious to a human — 15 records
with one vocabulary, 23 with another — and would pay handsomely.

### 4. `axes.py` grades path variance 0 on the corpus's cleanest example of it

`Rating`/`rating`, `Popcorn Score`/`popcornscore`, `Tomato Score`/`tomatoscore`
are the same logical field under two spellings, which is exactly what
`05-fhir-bundle`'s `value[x]` is and what `corpus/README.md` records path
variance as meaning. **`axes.py` measures 0.**

Its rule finds one *value* living at different paths; this is one *field* under
different names, and FHIR scored 44 because the spellings share a stem
(`valueQuantity`, `valueString`) while these do not. **The axis is measuring a
narrower thing than its own description**, and this file is the counterexample.

**It is still the second document to demand `first_present`**, and the case is
now a specification and a scraper — two unrelated causes for one word.

## What it disconfirmed

**That a document needs to be large to be hard.** 6,975 bytes — the smallest in
the corpus — and it produced a new health category, the third instance of the
open parent-discriminator case, a counterexample to an axis's own definition, and
the first answer to question 14. `08-open-meteo` made this point once at 12 KB;
this makes it at half the size.

**And that the ground-truth argument only pays in the way it was argued for.**
`VERDICT.md` predicted these files would be valuable as a *fair fight* against an
expert's answer. What actually paid here was different: the tutorial's own
sentence — *"a very large data frame that's mostly empty"* — names operation 3
independently, and the **three daily files**, which were incidental to the
tutorial, answered a question the corpus had never been able to ask.


## The thirteen tool attempts, 2026-08-10

Five R tools, eight Python. All thirteen agree: **38 films, 9 fields, two
DISJOINT key-sets (23 lowercase + 15 Title Case sharing no field at all), 17
sentinel values across three fields, 159 present cells.**

### 1. This document breaks tools in a way no other corpus entry does

It is an array of ONE object keyed by FILM TITLE, so the keys-as-data failure
arrives before anything else — and on a 7 KB file the ratios are the corpus's
worst:

| | description | % of file |
|---|---|---|
| `tidyjson::json_schema` | 4,628 chars | **66%** |
| `polars` schema | 4,556 chars | **65%** |
| `rrapply` melt path listing | — | **over 100%** |
| `ijson` prefix listing | — | **over 100%** |

`pandas`, `DuckDB` and `jsonlite` all turned the 38 films into 38 **columns**.
`pydash`'s key walk answers **47 = 38 titles + 9 fields**, so **81% of its
answer is data** — npm's 3,126-against-40 failure at a scale checkable by hand.

### 2. `json_schema` failed the OTHER way, and the trigger is structural

Six documents record it silently picking one shape and discarding the rest.
**Here it discards nothing and enumerates all 38 films instead.** Seven
documents, and the function has now been wrong in both directions:

```
varying records as siblings in an ARRAY    -> picks one, DISCARDS   (03,05,07,10,11,19)
varying records as values of a KEYED OBJECT -> ENUMERATES every key  (16, and npm at 61%)
```

**Which failure you get depends on whether the shapes are numbered siblings or
named ones** — `README.md`'s operation 1 against operation 2, and `json_schema`
does neither.

### 3. Two outright refusals, and DuckDB's is the most alarming in the corpus

**`tidyjson::spread_all` will not run**: *"Columns `Popcorn Score` and `Tomato
Score` don't exist"*. Each is number ×9 and string ×6; the verb builds one column
per (name, type) pair and then cannot find what it promised. **The one tidyjson
verb that needs no field names is defeated by exactly the polymorphism this
document was chosen for.** `spread_values` works and requires every field named
*and typed* — six decisions the reader must already have.

**DuckDB identifiers are CASE-INSENSITIVE, so `rating` collided with `Rating`
and arrived renamed to `rating_1`:**

```
SELECT "Rating"  -> R, unrated        non-null 15
SELECT rating    -> R, unrated        <- the SAME column
SELECT rating_1  -> NULL, NULL        non-null 23
```

**Typing the field name that is in the document returns the other population's
data, silently.** The first version of the attempt's group-by said `WHEN rating
IS NOT NULL` and reported the two groups exactly backwards — 23 Title Case, 15
lowercase — with numbers that looked entirely plausible. `Popcorn
Score`/`popcornscore` do *not* collide, because the space makes them distinct
identifiers, so the hazard is present on one renamed pair and absent on two:
**unpredictable rather than uniform.**

### 4. Five tools already have `first_present`, under five names

`glom.Coalesce`, jmespath's `||`, jq's `//`, R's `%||%`, and Python's `or` (which
is the buggy one — it treats a score of 0 as absent). `design/first_present.py`
is a sixth. All five collapse `Rating`/`rating` 38 of 38 in one expression.

> **This bears directly on `QUESTIONS.md`'s stopping rule** — *a word belongs in
> fathom only if removing it makes one of these questions unanswerable on at
> least one corpus file.* On this file it does not: four other tools answer Q8
> and Q12 with a verb they already ship. **What none of them has is a way to
> KNOW that `Rating` and `rating` are the pair to hand it.** The word is not the
> contribution; the detection is.

### 5. `ijson` reports zero polymorphic fields, and it is a false negative

Every other tool finds `Popcorn Score` as number-or-string. ijson finds none —
because each film has its own prefix, so **no single prefix ever sees both
types**. Its type report is defeated by the keys-as-data it could not fold. The
two failures compound rather than sitting side by side.

### 6. Where the sentinels are, and what a word list buys

jq and jqr find **all 17** including the five in `Gross`; `design/probe.py`'s
structural detector finds **12 of 17**, because `Gross` is text on all 15 records
and nothing about its type is unusual. **The two numbers are not comparable as
scores**: jq was handed the pattern `^unk`, which is a word list, and this
project refuses word lists. What jq shows is that a value-matching verb is the
right *shape* of tool for the question; what the probe shows is how much survives
without domain knowledge.

## The fourteenth tool, 2026-08-11 — `try-tidyr.R`

**This entry is the counterexample that inverts entry 24, and it is the whole
value of the tidyr sweep.**

`unnest_auto` says *"elements are named, but have no names in common"* and melts
the inner keys into a column — **159 rows of `Genre`, `Rating`, `popcornscore`
treated as values.** They are ordinary FIELD NAMES, not data. **And the 38 film
titles, which really are keys-as-data, appear nowhere in the output at all.**

> Entry 24 got the **same** empty intersection, made the **same** decision, and
> was **right**, because Cargo's feature names are data. **One rule, two
> documents, opposite correctness** — so the intersection carries no information
> about whether keys are data, and entry 24's success was luck.

**What empties the intersection is the RENAMING**, the axis `README.md` records
as having no instrument: every field is spelled one way on 15 films and the
other on 23, so no field is on all 38.

**`unnest_wider` gives TEN COLUMNS FOR SEVEN FIELDS**, in two contiguous blocks:

| | on | class |
|---|---|---|
| `Genre` `Gross` `IMDB Metascore` `Popcorn Score` `Rating` `Tomato Score` | 15 of 38 | mixed — `Popcorn Score` is a **list** |
| `popcornscore` `rating` `tomatoscore` | 23 of 38 | `popcornscore` and `tomatoscore` are **integer** |

**The two spellings of one field disagree on TYPE**, and the duplication is laid
out for a human to see at a glance.

> **That is a display, not a detector, and this file does NOT supply the missing
> instrument.** `Genre` and `popcornscore` sit in complementary blocks too and
> are not the same field — which is exactly the never-co-occur rule `README.md`
> already rejected. Complementarity is a property of the two SOURCES.
