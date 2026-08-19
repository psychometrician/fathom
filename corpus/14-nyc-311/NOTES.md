# 14 — NYC 311 service requests

## The expectation, written 2026-08-09 before the probe was run

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   a9e17af043495be40867a277485a4287385d94b8
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Disclosure

*Of the specimen.* **Two facts and no more: it is a JSON array, and it holds
20,000 objects.** No field name in this document has been read, no value seen,
no key counted. This is the blindest the corpus has been since file 10.

*Of the instrument.* None read for this file.

*Of prior knowledge, which is the real exposure here.* I know roughly what a
311 service request contains without looking — a complaint type, an agency, a
borough, dates, and address fields — and Socrata's export conventions. The
predictions below lean on that and should be discounted accordingly. It is
weaker than file 13's disclosure and stronger than none.

### Why this file — chosen to be ORDINARY, and that is the point

**`13-package-lock` was chosen as an adversary and it worked, and that is
exactly why file 14 must not be.** An adversarially-chosen document is
guaranteed to find something, so it can never measure convergence — and
`design/implementation.md`'s gate is *three consecutive corpus files that do not
change the probe's output*. **If every file is picked to break the newest
constant, the gate can never close, and the gate is what decides Phase 2.**

So this one is picked for being *representative*: the most-used open-data
endpoint in the world, a raw municipal export that nobody tidied for human
consumption, of the kind a working analyst actually meets. `corpus/README.md`
asks for documents no API has normalised; a Socrata export is about as close as
a public source gets, since it is a database table shipped as JSON rather than a
designed response.

**It fills no "Wanted" gap, and that is stated rather than glossed.** The two
open gaps are *broken/truncated* and *scale*, and this is neither. Its job is to
be a fair test.

### What is predicted

**1. Ragged by absence high, ragged by null near zero.** Socrata omits a column
from a record rather than emitting a null. Predicted: the reverse of
`07-graphql-introspection`, and one of the sharper absence readings in the
corpus.

**2. A split fires, and `KIND_MAX = 24` gets its first fair test.** This is the
prediction that matters. A 311 record carries several low-cardinality fields
present on every row — agency, borough, status — and one very-high-cardinality
one, complaint type, which runs to a couple of hundred values. **The cap was set
at 24 this morning against a corpus whose largest genuine split was 20, and it
has never met a document that naturally exceeds it.**

- If the probe splits on a low-cardinality field, the cap did its job.
- **If complaint type is the answer a human would want and the cap blocks it,
  the cap is wrong and this file says so** — which is the whole reason to run an
  ordinary document rather than another adversary.

**3. keys-as-data 0.** Socrata ships fixed column names. `VOCAB_GROWTH` should
have nothing to decline.

**4. Depth 3 or 4, recursion 0, polymorphism 0.** A flat table with perhaps one
nested location object. Socrata types its columns, so a field should not change
type between records.

**5. One row shape that matters: a record, 20,000 rows.** If the probe offers
more than two or three candidates on a flat export, the row pricing is finding
structure that is not there.

**6. Memory between 400 MB and 700 MB.** `04-gharchive` cost **968 MB** for 50 MB
and 20,000 sampled records, an 18.8× multiplier that `VERDICT.md` records as the
probe's worst axis. This is 29 MB and the same record count. **This is the
`scale` axis getting a second reading**, and if the multiplier is far off 18.8×
then that number was about record count rather than bytes.

**7. Under 100 lines, and no `└─ or N tables` join unless prediction 2 fires.**

**8. `rows("*")` returns 20,000 rows** with no key column, since the document is
an array rather than a keyed object — `rows()`'s plainest case, and the one where
its list-column defect should NOT appear.

---

## Provenance

| | |
|---|---|
| what | **NYC 311 service requests**, the 20,000 most recent |
| source | `data.cityofnewyork.us/resource/erm2-nwe9.json`, see `fetch.sh` |
| fetched | 2026-08-09 |
| size | **29,435,797 bytes, 20,000 records — NOT committed**, over the 5 MB rule |
| chosen from | this and Chicago crimes (19.2 MB); NYC for being the more ragged of the two |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers, no
encoded documents. **10.8 s, 229 MB resident, 17 lines of output.**

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 29,435,797 · depth **4** · paths 52 · fields 50 · explosion **1.0 — the floor** |
| keys-as-data | **0** · ragged by absence **35/50** · ragged by null **0** |
| recursion | 0 · polymorphic 0 · heterogeneous 1 · path variance **0** · row shapes **1** |

## Prediction scorecard: six of eight, and both misses are the probe being better than predicted

| # | predicted | outcome |
|---|---|---|
| 1 | absence high, null near zero | **confirmed, exactly. 35/50 and 0** |
| 2 | a split fires; `KIND_MAX` gets a fair test | **WRONG — no split, and the silence is correct. The cap never came into play** |
| 3 | keys-as-data 0 | **confirmed. The section is empty** |
| 4 | depth 3–4, recursion 0, polymorphism 0 | **confirmed. Depth 4, both zero** |
| 5 | one row shape, 20,000 rows | **confirmed. Exactly one candidate** |
| 6 | 400–700 MB | **WRONG. 229 MB — 8.2×, not the 18.8× gharchive cost** |
| 7 | under 100 lines | **confirmed. 17** |
| 8 | `rows("*")` → 20,000 rows, no list-columns | **confirmed. 20,000 × 49** |

## What the file established

### 1. NO DEFECT — the second such file in fourteen, and the first since `10-wikidata`

**Nothing here needs repairing**, which makes this the **first of the three
consecutive quiet files** `design/implementation.md` requires before the Rust
port. The last one was file 10, four documents ago.

### 2. The silence on splitting is correct, and it is provable

Prediction 2 said a split would fire. It did not, and **the probe is right**.
Every candidate discriminator fails the halving rule, measured:

```
fold disorder 25.6%  ->  a split must leave the worst group at 13% or less

agency                  13 kinds   worst group 28%
borough                  6 kinds   worst group 55%
status                   6 kinds   worst group 23%
complaint_type         139 kinds   worst group 34%
open_data_channel_type   4 kinds   worst group 26%
```

**311 raggedness is not explained by any categorical field.** It is driven by
whether a complaint has an address, coordinates and a closing date, and that cuts
*across* agency, borough and complaint type alike. There is no partition of these
records under which the fold produces a good shape, so declining is the answer.

> That is `VERDICT.md`'s stated kill-test — *when the fold produces a bad shape,
> is there a partition of the instances under which it produces a good one?* —
> **answered "no" for the first time, on a document where the honest response is
> to say so rather than to split anyway.**

### 3. `KIND_MAX` was NOT tested, and saying it was would be false

This file was chosen partly to give the 24-kind cap a fair test, and it did not
get one. `complaint_type` has **139 kinds** and would have been excluded by the
cap — **but it also fails the halving rule at 34%**, so it never reached the cap
and the cap decided nothing. **The constant set this morning is still untested
against a document that naturally exceeds it.**

### 4. The `scale` multiplier tracks nesting, not record count

`04-gharchive` cost **968 MB** for 50 MB and 20,000 records — 18.8×, which
`VERDICT.md` records as the probe's worst axis and one of two justifications for
the Rust port. This file is **28.1 MB, the same 20,000 records, and cost 229 MB
— 8.2×.**

| | bytes | records | depth | peak RSS | multiplier |
|---|---|---|---|---|---|
| `04-gharchive` | 50 MB | 20,000 sampled | 7 | **968 MB** | 18.8× |
| `14-nyc-311` | 28.1 MB | 20,000 | **4** | **229 MB** | **8.2×** |

**Same record count, half the multiplier, and the variable that moved is depth.**
The cost is per *Python object built*, and a flat record builds far fewer of them
than a nested one. `design/implementation.md`'s memory argument is unchanged in
direction and its number was about the shape of gharchive's records rather than
about JSON.

## What it disconfirmed

**That an ordinary document is an easy one for the corpus and a boring one for
the probe.** Explosion **1.0** — the theoretical floor, 52 paths for 50 fields —
no recursion, no polymorphism, no keys-as-data, one row shape. By every axis this
corpus grades it is the least interesting file in it, and it produced the most
useful negative result the probe has yet given: **a document that genuinely
should not be split, correctly refused.**

Every earlier file was chosen for being hard, and `06-espn-qbr` was noted as the
corpus's only ordinary document. **This is the second, and it is the one that
showed the fourth operation knowing when to stay quiet.**

---

## Grading

**The thirteen attempt files are DONE, 2026-08-11** — 5 R + 8 Python, one per
tool, each with its scoring header filled in against what actually printed. The
probe was frozen at `d595d1d2…` throughout and was not run again; this is the
tool half of an entry the probe graded on 2026-08-09.

**At 28.1 MB this is the largest SINGLE JSON DOCUMENT the tool comparison has run
on, which is not the same as the largest file.** `04-gharchive` is 52.2 MB and
graded, but it is **NDJSON — 37,883 objects, one per line** — so every tool there
reads a line at a time. **28.1 MB in one array has no line boundary to stop at.**
That is the scale reading this entry adds.

### The document has ZERO nulls, and that is what makes the entry worth having

Confirmed three ways independently of the probe: tidyjson's `json_structure`
reports **0 nulls at every level**, ijson's event census has **no `null` event in
752,908 leaves**, and jq's `[..|scalars|type]` returns only `string` and
`number`.

> **All thirteen tools therefore agree on question 4 — 13 always, 35 sometimes.**
> Entry 25 split the same thirteen **seven to six** on that question. **This entry
> splits them zero to thirteen**, and the only variable that moved is the
> document. Item 22's line was never frames-versus-walkers: it was nulls.

pandas reports 13 and **36**, which is the same answer over 49 dotted columns
because `json_normalize` splits `location` in two. polars, DuckDB, jsonlite,
purrr, rrapply, tidyjson, glom, jmespath, pydash, jq, jqr and ijson all say 35.

### What the tools agreed with the probe about

| number | probe | who else reproduced it, unprompted |
|---|---|---|
| **153 distinct key-sets** | 153 | **DuckDB, jq, jqr** — and this is the raggedness measure |
| **52 distinct paths** | 52 | jq, jqr, purrr and glom by hand; ijson gets 52 + an empty root |
| **4 levels deep** | 4 | ten of the thirteen |
| **752,908 leaves** | — | ijson from bytes, rrapply's melt from a list |
| **every scalar is a string** | — | ijson, jq, jqr, tidyjson: 713,768 strings, 39,140 numbers, all coordinates |

**Four tools arriving at `153 distinct key-sets` unprompted is the most
independent agreement any single entry has recorded, and it does not overturn
item 23i** — it supports it. Four tools can count the key-sets; **not one names a
row candidate or prices it.**

### The disagreements, which are the entry

| | |
|---|---|
| **polars REFUSES the file** | `ComputeError: extra field in struct data: bridge_highway_direction` — and that field is on **46 of 20,000 records (0.23%)**, one of the six rarest here. Better than `04-gharchive`'s `expected null in json value, got object`, which named nothing. `infer_schema_length=None` fixes it in 0.1 s — **a flag you only know to pass once you know question 4's answer** |
| **polars' column order is NOT STABLE between runs** | `unique_key` came back at position **16, 8, then 11** on three consecutive runs of one unchanged line. The rare tail stays put; the common fields shuffle |
| **pandas invents 36 type changes out of 49 columns** | on a document with **none**. All 36 are `str` against the `float` that is NaN. Entry 25's `alert` defect, thirty-six times, because raggedness here is 35 fields deep |
| **no frame tool invented a type**, which was not predicted | Socrata ships `latitude` as `"40.68…"`, and pandas, polars, DuckDB and jsonlite all kept it as text. The standing assumption that inference is where frames go wrong on JSON does not hold here |
| **pydash's `map_values_deep` MUTATES IN PLACE** | It is a mapper, not a walker. A survey callback returning `None` — `set.add` does — **emptied all 752,908 leaves**, printed a perfect question 1, and left every later question reading nulls. Nothing raised |
| **R's `$` partial-matches `location` → `location_type`** | 199 of the 430 records without `location` carry `location_type`, so `r$location` returns the string `"Street/Sidewalk"`. `keep(!is.null(r$location))` gives **19,769 instead of 19,570**. Three prefix pairs exist; **only the ragged one can fire** |
| **`colSums(!is.na(df))` is wrong on jsonlite's frame** | returns **49 values for 48 columns** — `!is.na()` expands the nested `location` frame — names misalign, `naive["location"]` is `NA`, and always-present comes out **14 against the true 13** |
| **jmespath drops a quarter of the document silently** | `[].closed_date` returns **10,739 of 20,000**; the multiselect hash returns all 20,000 with nulls. Two natural idioms, no warning. `contains()` also **raises** on the absent field, needing a `!= null &&` guard |
| **jmespath cannot address 4 of the 48 fields** | `:@computed_region_*` is a **ParseError at column 0**. glom, pydash, purrr, rrapply and ijson take the same string unquoted; jq and R need quoting but their errors name the key |
| **rrapply's `bind` is the only list-column-free table** | **20,000 x 50 in 0.2 s**, coordinates as two **numeric** columns. Every other tool leaves a list-column, which is what god's spec refuses — see item A2. The cost is that `.1`/`.2` are **positions**, which is question 7a from the other side |
| **rrapply's `melt` loses every type** | all 752,908 leaves come back `character`, so question 5 is unanswerable from it. Harmless here, and the instrument could not have said so |
| **tidyjson types all 48 fields and gets none wrong** | against **five wrong** on `25-usgs-quakes`. Same code, same tool — entry 25's five were present-and-null, and this document has no nulls to mistype |
| **the same jq program is 2.8x faster from R** | paths **3.6–3.8 s** in jqr against **9.9 s** in the Python binding; depth 0.7 vs 2.1; key-sets 0.9 vs 2.5. **The conversion hypothesis was tested and is wrong** — `input_text()` is 11.2 s, no faster. Different libjq builds. First time this corpus has priced one program in both languages |
| **question 3: thirteen of thirteen still cannot** | jsonlite, tidyjson, rrapply and ijson each **choose** a row shape silently; **none names an alternative or prices one.** No tool printed `25% empty` |

### Scale, which is what this file was for

| | time | peak RSS |
|---|---|---|
| ijson, one pass answering Q0,1,2,4,5,7,11 | **0.6 s** | **~27 MB** |
| polars `read_json` | 0.1 s | — |
| DuckDB `read_json` | 0.3 s | — |
| jsonlite `fromJSON` | 0.3–0.8 s | ~33 MB |
| **`design/probe.py`, the whole description** | **10.8 s** | **229 MB** |
| tidyjson `json_structure` | 10–12 s | — |
| python `jq`, all twelve answers | 38.8 s | — |

**The two tools that answer question 1 properly cost about what describing the
whole document costs.** ijson is the exception and it is a large one: seven
questions in 0.6 s and 27 MB, against the probe's 229 MB. That is an argument
`design/implementation.md`'s memory section should have, since ijson is doing in
Python what the Rust port was justified by.


## The fourteenth tool, 2026-08-11 — `try-tidyr.R`

**This is the document where `unnest_auto` is simply right**, and that matters as
much as the failures. *"Elements have 13 names in common"* — thirteen genuinely
shared fields — and **20,000 x 48** is the one defensible row shape.

> **A rule that is wrong in principle is right whenever the document is easy,
> which is the condition under which nobody notices it is wrong.** Entries 12,
> 13, 16 and 24 all found the same rule deciding keys-as-data on evidence that
> has nothing to do with the question.

**All 48 columns come back character**, including every date and numeric, so
question 5 is *no variation* in the strongest and least useful sense: **the
document's types were gone before the rectangling began.**

**The third instance in the corpus of the name-collision failure, and the only
one where the documented repair manufactures it.** `unnest_wider(location,
names_sep = "_")` produces `location_type`, **which is already a 311 field** —
and the error then advises `names_sep`, which is what produced it. Only
`names_repair` gets through, at 20,000 x 49. After entry 01's `version` and
`design/rows.py`'s `children**`.

**And `location` is an object**, so `unnest_longer` gives **39,140 rows** — the
19,570 records that have one times its 2 fields, not one row per location. It
drops the 430 that have none.
