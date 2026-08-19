# 27 — Grafana dashboard, "Node Exporter Full"

## Provenance

**Fetched 2026-08-12** from `grafana.com/api/dashboards/1860/revisions/37/download`.
683,275 bytes. `fetch.sh` is committed beside `source.json`.

**Dashboard 1860 is one of the most-installed dashboards in existence**, and this
is the exported form the library serves — the form a person actually receives
when they click Download JSON. It was not edited, trimmed or reformatted.

## Why this file

**Deeply nested BY DESIGN, which is the property under test.** A dashboard is
panels inside rows, each panel carrying queries, field configuration, overrides,
thresholds and legend options, each of those an object of objects. Nothing in
the corpus is nested for this reason: `09-stripe-openapi` is deep because a
schema language recurses, `10-wikidata` because a data model does, and
`13-package-lock` because a dependency tree does. **A dashboard is deep because a
person built a user interface out of boxes**, which is a different cause and the
most ordinary one there is.

**It is also a held-out run for two builds that have never had one.**
`design/probe.py` was re-frozen twice — `ecf70b91…` for defect 27 and
`2b0fa4d1…` for defect 28 — and **no unseen document has met either.** Both
repairs were designed against documents the corpus already held. Defect 28's in
particular was fitted to the only two files that carry the fold's `<key>` marker.

> **What this file CANNOT do, stated so it is not claimed later.**
> `corpus/README.md` wants *a broken or truncated document, a real one rather
> than a damaged copy*, and this is not one — it is valid JSON. **That gap stays
> open.** Truncating a good file and calling it real would be manufacturing the
> evidence, which is the one thing this corpus refuses.

## Predictions, committed 2026-08-12 BEFORE the probe was run

**Written from what a Grafana dashboard is, not from reading this one.** The
only things looked at first were its size, that it parses, and that it has 25
top-level keys. Rule 1: write down what you expect before you measure it.

| # | prediction |
|---|---|
| 1 | **The partition fires on `type`** at the panel site — a graph, a stat, a table and a row panel share almost nothing, and `type` is the discriminator |
| 2 | **Recursion IS present** — a row panel contains `panels[]`, so `a node at any depth` appears in the menu |
| 3 | **Ragged by absence is high**, over 100 fields at the panel site with most absent from most panels |
| 4 | **keys-as-data is 0 or near it.** A dashboard names its fields; it does not use them as data |
| 5 | **No positional alignment.** Nothing here stores a table in parallel arrays |
| 6 | **Depth ≥ 9** |
| 7 | **The biggest row candidate is `an item of panels` or `an item of targets`** |
| 8 | **At least one polymorphic field** — dashboard schemas changed across versions and exports carry the sediment |
| 9 | **Sound**: no duplicate keys, no NaN or Infinity, no integers past 2^53 |
| 10 | **The description is under 1% of the input** — a few KB against 683 KB |

**Two predictions about the OPEN DEFECTS, which is why this document was run at
all:**

| # | prediction |
|---|---|
| 11 | **Defect 28's repair stays untested.** No `.*` label appears, because prediction 4 says there is no keys-as-data site — so the repair frozen at `2b0fa4d1…` will still have met no unseen document |
| 12 | **Defect 29 does NOT fire here.** If recursion is only `panels` inside `panels`, `a node at any depth (N levels)` is printed once and the label is unambiguous |

## The grades, measured 2026-08-12

Cold run against `design/probe.py` at **`2b0fa4d1…`**, verified before the run.

| axis | measured |
|---|---|
| bytes | 683,275 · depth **12** · paths 325 · fields 125 · explosion 2.6 |
| recursion | **0** · polymorphic **7** · heterogeneous 6 |
| keys-as-data | **2**, and one of them is `$` |
| ragged by absence | **104/250** · ragged by null 3 |
| path variance | 77 · row shapes 8 |
| column-oriented | 0 sites |
| description | 10,952 bytes, **1.6029%** of the input |

## Prediction scorecard: six of twelve, and the misses are the reason to have run it

| # | predicted | outcome |
|---|---|---|
| 1 | the partition fires on `type` | **WRONG, and it is defect 24.** See below |
| 2 | recursion is present | **WRONG.** 0. A row's `panels[]` does not canonicalise to the top-level list |
| 3 | ragged, over 100 fields at the panel site | **PARTLY.** 104/250 ragged and 8 key-sets over 40 objects, but 24 fields, not 100 |
| 4 | keys-as-data is 0 or near it | **WRONG, and the most useful miss. The ROOT is keys-as-data** |
| 5 | no positional alignment | **right.** 0 sites |
| 6 | depth ≥ 9 | **right.** 12 |
| 7 | biggest candidate is `panels` or `targets` | **right.** `an item of targets`, 225 rows |
| 8 | at least one polymorphic field | **right.** 7 |
| 9 | sound | **right.** No duplicate keys, no NaN, no big ints |
| 10 | description under 1% | **WRONG.** 1.60% |
| 11 | defect 28's repair stays untested | **WRONG — and this is what the run was for** |
| 12 | defect 29 does not fire | **right.** Eight candidates, eight distinct labels |

## DEFECT 30, found by this document: the repair for 28 DELETED a candidate

**`__inputs`, `__requires`, `panels`, `templating`, `annotations` … the root's 25
keys are treated as data**, so the fold writes `$.<key>` and the paths below it
become `$.<key>[]`. **No corpus document had ever done that.**

`_above_marker()` walks a trailing run of markers up to the nearest real name.
Here there is none — the run reaches the root — so it returns `$`, and both
loops in `candidates()` skip on `$`. **The comment in that function says the
branch is untested; the first unseen document reached it.**

**Measured against the build before the repair, `ecf70b91…`:**

```
before defect 28    an entry of <key>    6 rows x 2 cols
after  defect 28    (the line is gone)
```

**That is precisely the failure the repair claimed to avoid.** Its own comment
reads *"the bare name one level up was tried first and it DELETES THE LINE …
trading an untypeable candidate for a missing one is worse"* — and the `$`
fallback does exactly that whenever the marker run reaches the root.

**Three sites are unnamed**, and the largest is the one that matters:

| path | |
|---|---|
| `$.<key>[]` | **40 objects, 24 distinct fields** — the top-level panel and row list, the most important structure in a dashboard |
| `$.<key>.<key>` | 24 items, 5 objects |
| `$.<key>` | 5 copies, 6 values — the line that used to print |

> **Recorded, not repaired.** Rule 5. `probe.py` stays at `2b0fa4d1…`.

## DEFECT 24 HAS ITS SECOND DOCUMENT, and the obvious repair is still wrong

**Prediction 1 failed because the partition declined**, and the numbers say it
should not have. At `$.<key>[]`, splitting on `type`:

```
40 objects, 9 kinds        unsplit 0.6438 empty     the bar is 0.3219
  WORST group  0.3750      REJECTED   <- the rule today
  WEIGHTED     0.0348      would pass <- defect 24's proposed rule

  row 16 · gauge 5 · stat 5 · panel 4 · timeseries 4 · datasource 2 · link 2 …
  six of the nine groups are 0% empty
```

**A split that takes a 64% empty table to 3.5% is rejected because one
TWO-OBJECT group is 37.5% empty.** That is defect 24's shape exactly, and
`CLAUDE.md` has been holding the repair open *waiting for a second document to
justify it*. **This is that document.**

**But the obvious repair is still not right, and this run measured that too.**
Swapping the maximum for the weighted average against `05-fhir-bundle`'s two
recorded false positives:

| | worst, today | weighted, proposed |
|---|---|---|
| `identifier[].system` | 0.3137 **reject** | 0.0770 — **ACCEPTS a known false positive** |
| `item[].sequence` | 0.4643 **reject** | 0.3900 **reject**, correctly |

> **This REFINES what `CLAUDE.md` records.** It says the proposed rule *"also
> accepts `05-fhir-bundle`'s two known false positives"*; measured, it accepts
> **one** and still rejects the other. **So the problem now has two documents and
> the proposed solution still has one counterexample** — which is a smaller gap
> than before and not a closed one.
>
> Worth a second look while deciding: a FHIR `identifier.system` is a URI
> namespace, and whether it is a *kind* is a judgement this project recorded as
> settled and might reasonably revisit.

## Regraded 2026-08-12 after defect 31's repair, at `70d6c159…`

**The grades above are left alone**: they record what the frozen probe said on
the day, which is what a cold run is for. These are what it says once the root
is no longer misclassified.

| axis | cold run | after | |
|---|---|---|---|
| keys-as-data | 2 | **0** | both were artifacts of the misclassification |
| polymorphic | 7 | **3** | **four of the seven "fields that change type" were the pooling** |
| ragged by absence | 104/250 | 79/246 | |
| fields | 125 | 146 | the pool had been hiding them |
| row shapes | 8 | **12** | |
| explosion | 2.6 | 2.2 | |

**PREDICTION 1 WAS RIGHT AND THE PROBE WAS WRONG.** The scorecard above marks it
WRONG because the frozen probe printed no split on `type`, and that is the
correct way to score a cold run — it records what the instrument did. Once the
root is classified correctly the partition fires exactly as predicted:

```
an item of panels    31 rows x 68 cols   67% empty
  └─ or 5 tables, split on type — 2% empty: row 16, gauge 5, stat 5, timeseries 4, +1 more
```

**The document's principal structure is named and priced for the first time**,
and `__inputs`, `__requires`, `links` and `templating.list` are four separate
candidates rather than one pool of 41 items that could not be priced at all.

> **The misclassification was manufacturing evidence in three places**, which is
> the reason it was worth chasing: a fake instance of defect 24, four fake
> polymorphic fields, and an unpriceable principal structure.

## What this file disconfirmed

**That a deeply nested document is deep in an interesting way.** Depth 12, 325
paths, and **zero recursion** — a dashboard is deep because a person nested
boxes inside boxes, not because anything self-references. It defeats every
axis that expects structure to be generative.

**That the description ratio holds under 1% on a medium file.** 1.60% is the
second-largest in the corpus, and the cause is that 24 of its 51 record shapes
are near-identical panel configuration blocks — the fold has little to fold.


## Defect 34 was found here, 2026-08-13, and repaired the same day

**Found by asking the question this entry's tool comparison was going to be
built around: how many panels are in this dashboard?**

| the menu said | the document has |
|---|---|
| `an item of panels` — **31** | **132** — 31 top-level, 101 inside `row` panels |
| `an item of targets` — **225** | **269** — 225 nested, 44 top-level |

**The two came from OPPOSITE levels by lexicographic accident.** `$.panels`
sorts before `$.panels[].panels`, so the outer collection won;
`$.panels[].panels[].targets` sorts before `$.panels[].targets` — `p` before
`t` — so the inner one did.

**Repaired at `c3b3f04d…`**, and this entry gains six lines:

```
an item of panels     31 rows x 68 cols   67% empty
  └─ 101 more at panels.*.panels — not counted above
an item of targets   225 rows x 14 cols   37% empty
  └─ 44 more at panels.*.targets — not counted above
```

> **This entry has now produced four defects — 30, 31, 34 and the withdrawal of
> a fake 24 — and it is still not graded in fourteen tools.** The attempt files
> were deferred twice because a repair would have staled them. That is the right
> order and it is worth saying: **a document that keeps finding defects is not
> yet ready to be a measurement.**

## Tool predictions, committed 2026-08-13 BEFORE any of the fourteen was run

**Rule 1.** Not one of the fourteen attempt files existed when this section was
written and none had been run. What WAS known first, and is not a prediction:
the document has **132 panels** — 31 at the top level and 101 inside the 16
`row` panels, with the nesting exactly one level deep — and **269 targets**, 44
top-level and 225 nested. Those were counted in twelve lines of `json` before
any tool was chosen, because the comparison has to have a right answer to be
scored against.

**The question every attempt is built around: how many panels are in this
dashboard?** It is the question a person actually arrives with, it has a naive
answer that is wrong and looks right, and the gap between 31 and 132 is a `row`
panel nesting its own `panels` — a fact no schema in the file declares.

| # | tool | predicted |
|---|---|---|
| 1 | **jq** | **132, one expression.** `..` is jq's headline verb and this is what it is for |
| 2 | **jqr** | **132**, the same expression through R — the two are one language and should not disagree |
| 3 | **ijson** | **132** by counting the event prefix. `panels.item.panels.item` and `panels.item` are both prefixes, so both depths are visible without a schema, in constant memory |
| 4 | **duckdb** | **132** via `json_tree`, which entry 28 established is the melt built in |
| 5 | **rrapply** | **132** via `how = "melt"` and a count over the `L` columns |
| 6 | **tidyjson** | **132** via `json_structure()`, filtering the node list on the name |
| 7 | **tidyr** | **31 naively, 132 only if you already know to unnest twice.** Q13 fails in the tool that is fathom's closest prior art |
| 8 | **purrr** | works, but **the recursion is mine** — same as entry 28 |
| 9 | **jsonlite** | **PARTLY. 31 rows and a `panels` list-column**, because `simplifyDataFrame` will rectangle the outer array and stop |
| 10 | **pandas** | **31.** `json_normalize(record_path=['panels'])` is the obvious call and it is the wrong answer; 132 needs a second call and a concat |
| 11 | **polars** | **FAILS**, and on schema inference rather than entry 28's name collision — 31 panels of 5 types with ~68 distinct fields is a struct it must unify |
| 12 | **glom** | **CANNOT.** No recursive descent in the spec language |
| 13 | **jmespath** | **CANNOT.** The language has no `..` at all |
| 14 | **pydash** | works, but **the recursion is mine** |

**Three predictions about the comparison as a whole**, which are the ones worth
being wrong about:

| # | prediction |
|---|---|
| 15 | **Six of the fourteen surface the nesting without being told it exists** — the melt tools, because enumerating every path puts `panels.panels` in front of you whether or not you asked |
| 16 | **At least three return 31, silently, and look correct.** That is the failure this entry exists to demonstrate and it is why the question was chosen |
| 17 | **None of the fourteen says "31 or 132, and here is what each costs."** Unchanged across 28 entries — but here the alternatives are not two readings of an ambiguous document, they are one right answer and one wrong one, which is a harder test of the claim than any previous entry has put to it |

## ALL FOURTEEN TOOLS, 2026-08-13 — fourteen of seventeen predictions

**All fourteen written, RUN, and every line of prose corrected against what
printed.** 6 R + 8 Python. **This entry is now graded in all fourteen tools.**

**Eleven tools independently agree on the ground truth**: 11,063 leaves, 231
distinct paths, depth 12, 132 panels, 269 targets, `description` absent from 84
of 132, 255 leaves carrying a template variable. Where a tool could answer at
all, it agreed.

### Q7, the question the entry was built around: how many panels?

| | tool | the naive call | reaches 132 | how |
|---|---|---|---|---|
| **without being told the nesting exists** | **tidyjson** | — | **yes** | `parent.id` join. **No depth appears in the expression at all** |
| | **ijson** | — | **yes** | the prefix `panels.item.panels.item` is simply emitted; it shows up in the Q1 output of someone who asked only "what is in here" |
| | **rrapply** | — | **yes** | `how = "melt"` puts each level in its own column, so "which levels hold the word `panels`" is a two-line loop |
| **with a pattern that assumes repetition** | **jq** / **jqr** | `.panels\|length` = 31 | **yes** | `[.. \| objects \| select(has("gridPos"))] \| length`, one expression |
| | **duckdb** | — | **yes** | `regexp_matches(fullkey, '^\$(\.panels\[\d+\])+$')` — the `+` is depth-agnostic |
| **only by enumerating each depth by hand** | **glom** | — | 31 + 101 | `Coalesce('panels', default=[])`, no `**` in the language |
| | **jmespath** | — | 31 + 101 | no `..` at all; the sum is an addition I performed |
| | **pydash** | — | 31 + 101 | `_.get(p,'panels',[])` in a comprehension |
| | **purrr** | `length(doc$panels)` = 31 | 31 + 101 | `pluck(.default=list())`; no `map_deep` exists |
| | **polars** | — | 31 + 101 | **only after pre-flattening in plain Python** |
| **returns 31 and looks finished** | **pandas** | `json_normalize(record_path=['panels'])` = 31 | after a `KeyError` | `record_path=['panels','panels']` **raises**; needs a list comprehension to work around |
| | **tidyr** | `unnest_wider(p)` = 31 | after a 2nd unnest | the closest prior art fathom has, and Q13 fails |
| | **jsonlite** | `nrow(doc$panels)` = 31 | **the 101 are already in the object** | see below |

### jsonlite is the near-miss of the whole corpus

`fromJSON()` with no arguments returns a 31 x 15 data frame — the only tool of
the fourteen that rectangles by default, with no path named and no verb called.
**And its `panels` column is a list of data frames holding the other 101, fully
parsed.** jsonlite did the recursive work, built the nested tables, and returned
an object whose `nrow()` is 31.

**That is a different failure from pandas' and tidyr's.** They never reached the
101. jsonlite is holding them. Its own `flatten()` widens 15 columns to 68 by
lifting nested objects into dotted names and explicitly does not descend into
list-columns of frames, so the verb that looks like it finishes the job cannot.

### Three tools erase an empty container, and one of them deletes a whole field

**`links` is present on 115 of the 132 panels and every single value is `[]`.**

| | reports `links` present on |
|---|---|
| jq, tidyjson, purrr, ijson | **115** |
| tidyr's `unnest_wider` table | **0** |

An empty array in a list-column is stored as `NULL`, indistinguishable from a
key that was never there, so a field carried by 87% of the records vanishes
from the table completely. `jsonlite`'s simplification and polars' structs
perform the same erasure; **rrapply's melt performs it too and differently** —
`__elements` is `{}`, a melt has one row per leaf, so the melt shows 24 of the
25 root keys and never mentions the missing one.

> **This is the ragged-edge question — Q4 — being destroyed by the verb that
> builds the table**, in four tools, in two languages, silently.

### Two defects found in tools, both by disagreement rather than by reading

**1. jq's `paths(scalars)` silently drops every `false` and every `null`.**
`select` emits its input when the filter's OUTPUT is truthy, and `scalars`
returns the value itself, so a leaf that *is* `false` fails its own filter.

| | |
|---|---|
| `[paths(scalars)] \| length` | **10,363** |
| `[path(.. \| select(type != "object" and type != "array"))] \| length` | **11,063** |

**700 rows and 26 of the 231 distinct paths, gone without a word** — 6.3% of the
document. **This is the idiom entry 28 recorded and scored**, where it cost
nothing because a translation catalogue is all strings. It cost 6.3% here, and
it was caught only because a plain Python walk disagreed.

**2. duckdb has an 880x query-form cliff on `json_tree`.**

| | |
|---|---|
| `CREATE TEMP TABLE tree AS SELECT t.* FROM read_json_objects(…) r, json_tree(r.json) t` | **0.24s** |
| `SELECT count(*) FROM read_json_objects(…) r, json_tree(r.json) t` | **211s** |

Same file, same connection, same 17,676 nodes. Seven timed runs of the direct
form measured 55s, 55s, 63s, 70s, 78s, 178s and 211s; one did not return. **The
slow form is the obvious one and is what entry 28's attempt uses throughout.**

> **A first draft of `try-duckdb.py` concluded "duckdb is enormously slow on
> this document". That was wrong** — it is slow on that *query shape* — and the
> only reason it was caught is that restructuring the file made the measured
> time drop to 0.2s while the prose still said a minute.

### polars cannot read this document at all, for the second entry running

Four routes, four failures: `read_json` raises `ComputeError`, `DataFrame`
raises `TypeError`, and `strict=False` — **which the error message itself
recommends** — raises too, as does `infer_schema_length=None`.

The cause is one field: `fieldConfig.overrides[].properties[].value` is an
object at 614 sites, a string at 33 and an integer at 18. **Type variation is
fatal rather than reportable**, so the answer to Q5 is not "no" but "the
question cannot be reached". Everything else in that attempt runs on a frame
pre-flattened in Python.

> Entry 28 failed on a `DuplicateError` from a name collision. **Two entries,
> two completely different hard failures, and polars is the one tool of fourteen
> that cannot get started on either.**

### Prediction scorecard: fourteen of seventeen

| # | predicted | outcome |
|---|---|---|
| 1–8, 14 | jq, jqr, ijson, duckdb, rrapply, tidyjson reach 132; tidyr needs two unnests; purrr's and pydash's recursion is mine | **all right** |
| 9 | jsonlite PARTLY — 31 rows and a `panels` list-column | **right, and it is the entry's best finding** |
| 10 | pandas returns 31 | **right, and WORSE than predicted** — the second `record_path` raises rather than returning nothing |
| 11 | polars fails on schema inference | **right, and worse** — it cannot read the file by any of four routes |
| 12 | **glom CANNOT** | **WRONG.** It reaches 132 by enumeration; `Coalesce(default=[])` makes it tidy |
| 13 | **jmespath CANNOT** | **WRONG.** Same — `length(panels[?panels] \| [].panels[])` works |
| 15 | **six tools surface the nesting unprompted** | **WRONG, it is three.** tidyjson, ijson and rrapply. jq's `..` and duckdb's `+` both encode "I am looking for something that repeats", which is the suspicion already formed |
| 16 | at least three return 31 silently | **right.** pandas, tidyr, purrr, jsonlite, and jq's naive form |
| 17 | none names both readings and prices them | **right, and unchanged across 29 entries** |

**The two CANNOT predictions were wrong in the same way and it is worth saying
how.** glom and jmespath both lack recursive descent, which is why I predicted
failure — but neither needs it when the depth is known to be two, and by the
time I wrote those files six other tools had told me it was. **A "cannot" that
becomes a "can" once you already know the answer is not a capability**, and the
attempt files score both by enumeration for that reason. The prediction was
wrong about the outcome and right about the language.

## What this file disconfirmed, second pass

**That the exploring/extracting split runs between tools. It runs THROUGH
them.** tidyjson answers Q7 at any depth with a `parent.id` join and then its
own extraction verb — `enter_object("panels") |> gather_array()` — takes a
literal path and returns 31. One package, both halves of this project's thesis,
and the two halves do not talk to each other.

**That "no tool does this" is the interesting claim.** Three tools DO surface
the nesting unprompted, which is more than any previous entry found, and the
claim that survives is narrower and better: **none of the fourteen names the two
readings and prices them.** Every one will answer 31 or 132 — whichever you
asked for — and not one says the other exists or what it would cost.

> **The sharpest version of the finding.** On the other 28 entries the
> alternative row shapes were defensible readings of an ambiguous document.
> Here one answer is right and one is wrong. **Thirteen of the fourteen have a
> natural one-line call that returns 31** — the fourteenth is polars, which
> cannot read the file at all — **and not one of the thirteen says that 132
> exists.** Six of them will also produce 132 if asked the right way, which
> makes the point rather than softening it: the capability is there and nothing
> connects it to the question.
