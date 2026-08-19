# 29 — MDN browser-compat-data, the whole bundle

## Provenance

**Fetched 2026-08-12** from `unpkg.com/@mdn/browser-compat-data/data.json`.
**19,905,214 bytes**, 14 top-level keys — `__meta`, `api`, `browsers`, `css`,
`html`, `http`, `javascript`, `manifests`, `mathml`, `mediatypes`, and four more.

**NOT COMMITTED**, at 19.9 MB, over the corpus threshold. `fetch.sh` is
committed and `.gitignore` excludes the file. The package publishes
continuously, so a later fetch gives a LATER file — the shape reproduces, the
bytes do not.

**This is the data behind every "can I use this yet" answer on MDN**, which is
about as real as a JSON document gets.

## Why this file, and it is a TARGETED test of defect 32

**Defect 32 was repaired hours ago and this document is chosen to attack it.**
That repair replaced a homogeneity RATIO with a COUNT: the single-copy branch of
`classify()` now calls a site keys-as-data only when its values are **at most two
distinct non-null types**, stated as *a keyed collection's values are one kind of
thing, or a leaf and a group*.

> **The rule has never met a document with three.** All 47 single-copy sites in
> 28 entries have one or two; the only site with more is `27-grafana-dashboard`'s
> root, which is a real schema and must be refused. **So the rule is untested
> against the case it would get wrong: a genuine keyed collection whose values
> are three or more types.**

**browser-compat-data is the best candidate I know of.** Its `support` maps
browser names to an object OR an array of ranges, and `version_added` is a
**string, a boolean, or null** — a genuinely tri-typed field in a document
people use daily.

**This is also the opposite of entry 28 on scale.** That file was 604 KB and
defeated the fold; this one is 19.9 MB and should be where the central claim
looks its best. Both directions are worth having.

**Selected by what the format is, not by measuring it.** Only its size, that it
parses, and its 14 top-level key names were looked at before the predictions
below. Rule 1.

## Predictions, committed 2026-08-12 BEFORE the probe was run

| # | prediction |
|---|---|
| 1 | **THE TEST: at least one site has three or more distinct value types**, and defect 32's rule refuses it |
| 2 | **And at least one of those is a site a reader would call keys-as-data** — if so, defect 32 is too strict and needs a third look |
| 3 | **keys-as-data fires on many sites** — `api`, `css.properties`, `javascript.builtins` are keyed by feature name, an open vocabulary of thousands |
| 4 | **Deep**: feature paths nest, depth ≥ 10 |
| 5 | **Recursion FIRES.** A feature contains sub-features of the same shape, which is the `02-hn-thread` property in a different costume |
| 6 | **Polymorphism is high** — `version_added` as string/boolean/null is textbook, and the probe should report it without an "artifact of folding" label |
| 7 | **The description ratio is under 0.1%** — the mirror of entry 28, and where the central claim should look its best |
| 8 | **Sound**: no duplicate keys, no NaN, no integers past 2^53 |
| 9 | **The partition fires somewhere**, most likely on a `version_added`-shaped field |
| 10 | **`browsers` is NOT keys-as-data** — about fifteen browser names is a closed vocabulary, and the saturation guard should decline it |

> **Predictions 1 and 2 are the point, and 2 is a prediction against my own
> repair for the second time in a day.** Defect 31 was made on one document and
> broken by the next; defect 32 is the third version of that rule. If a real
> keyed collection here has three value types, the count is wrong too and the
> single-copy branch may not be solvable structurally at all — which
> `classify()`'s own docstring already half-admits.

## The grades, measured 2026-08-12

Cold run against `design/probe.py` at **`30198089…`**, verified before the run.
**72 seconds**, the slowest in the corpus.

| axis | measured |
|---|---|
| bytes | 19,905,214 · depth **12** · paths **838,880** · fields 899 · explosion **933.1** |
| recursion | **0** · polymorphic **1,336** · heterogeneous 485 |
| keys-as-data | **388** |
| ragged by absence | **2,903/8,332** · ragged by null 0 |
| path variance | 129 · row shapes 81 |
| column-oriented | 10 sites, 0 solid |
| description | 176,961 bytes, **0.8890%** · **1,962 lines** |

## Prediction scorecard: five of ten, one half — and the two that matter FAILED WELL

| # | predicted | outcome |
|---|---|---|
| 1 | a site with 3+ value types, refused | **WRONG — zero of 36** |
| 2 | and one is a reader's keyed collection | **WRONG, vacuously. DEFECT 32 SURVIVES** |
| 3 | keys-as-data on many sites | **right.** 388 |
| 4 | depth ≥ 10 | **right.** 12 |
| 5 | recursion fires | **WRONG.** 0 |
| 6 | polymorphism high, unlabelled | **half.** 1,336 fields, but 104 lines carry *not really* |
| 7 | description under 0.1% | **WRONG.** 0.889% |
| 8 | sound | **right** |
| 9 | the partition fires, likely on `version_added` | **right.** 40 splits, all on `version_added` |
| 10 | `browsers` is not keys-as-data | **right.** Not listed; its `.releases` are, correctly |

## DEFECT 32 SURVIVES ITS FIRST HELD-OUT ATTACK, and the reason is structural

**36 single-copy sites past `KEYED_MIN` in a 19.9 MB document with genuinely
tri-typed fields, and every one has ONE OR TWO value types. Zero have three.**

**The document is full of three-way type variation** — `$.api.<key>.<key>.<key>`
is `object x11,014, text x3,162, array[1] text x1,019` — **and none of it is
where defect 32 looks.** That variation lives at FOLDED paths with thousands of
copies, which go through the sibling branch.

> **The structural reason is worth more than the result.** A keyed collection
> with a thousand keys is uniform BY CONSTRUCTION: it is a collection of one kind
> of thing, and that is what makes it a collection. **Heterogeneity lives in the
> RECORDS below it, not in the collection itself** — which is exactly why
> counting value types works on a single copy, and why the ratio did not.
>
> **A rule that survives a document chosen to break it is much stronger evidence
> than one that was never attacked.** Defect 31 died on the first held-out
> document; defect 32 did not.

## DEFECT 33, found instead: one section has no cap and it is 74% of the report

```
FIELDS THAT CHANGE TYPE    1,444 lines
RECORD SHAPES, FOLDED        366      capped at SHOW, says what it dropped
ONE ROW COULD BE              83
KEYS THAT ARE DATA            63      capped at SHOW, says what it dropped
                           ─────
                           1,962 lines · 176,961 bytes
```

**Three sections cap at `SHOW` and name what they dropped. The fourth prints one
line per polymorphic field, and this document has 1,336 of them.**

**The probe's own reasoning already condemns this**, in the comment above the
keyed-site cap: *"`09-stripe-openapi` has 47 sites whose paths run past 180
characters, and an unordered list of 47 is not a description."* **1,336 is not a
description either**, and the section is 74% of the page.

> **Is it proportional to STRUCTURE? Yes — and that is not a defence.** 1,336
> polymorphic fields is a structural fact, so the claim in `README.md` holds
> literally. But a 177 KB report is larger than 24 of the 29 corpus documents in
> their entirety, and the reason a reader wanted a description was not to receive
> a longer document than the one they had.
>
> **Capped like its three neighbours the report would be roughly 520 lines**,
> which is the same shape of repair defect 20 made in the other direction —
> that one un-capped a field list because truncation lost structure; this one
> needs a cap because an unordered 1,336 is not information.
>
> **Recorded, not repaired.** Rule 5. The probe stayed at `30198089…` for the
> cold run.

### Regraded 2026-08-12 after defect 33's repair, at `5b987ef3…`

The grades above are left alone: they record what the frozen probe said on the
day. After the cap:

| | cold run | after |
|---|---|---|
| report lines | **1,962** | **563** |
| report bytes | 176,961 | **39,911** |
| description | **0.8890%** | **0.2005%** |

**Prediction 7 said under 0.1% and is still wrong** — 0.2005% — but it was
wrong by a factor of nine on the day and is wrong by a factor of two now.
**Three quarters of the miss was the defect, and the remaining quarter is the
document honestly having 838,880 distinct paths.**

**All 27 corpus reports predating this entry are byte-identical after the
repair**, because this is the only document in the corpus with more than `SHOW`
polymorphic fields. The next highest are `20-homebrew-formulae` and
`28-home-assistant-i18n` at exactly 40.

## Tool-sweep predictions, committed 2026-08-14 BEFORE any attempt was written

Rule 1, applied to the fourteen-tool comparison rather than to the probe. **The
document is no longer unseen** — it was graded on 2026-08-12 and its structure
is recorded above — so what is being predicted here is TOOL BEHAVIOUR, which
nothing has measured.

**The new variable is SCALE.** `28-home-assistant-i18n` was 604 KB and four
tools beat fathom on it. This is **19.9 MB and 838,880 paths**, 33x larger, and
several of the verbs that won there build one row per node.

| # | prediction |
|---|---|
| 1 | **rrapply's `how = "melt"` still wins the R half**, one call, and produces a table with a column per level — but it will be **slow enough to notice**, over 30 seconds |
| 2 | **tidyjson's `json_structure()` FAILS or is unusable here.** It won on entry 28 at 10,137 nodes; 838,880 is 83x that, and it builds a data frame per node |
| 3 | **duckdb `json_tree` is the Python winner**, and the **880x cliff found on entry 27 bites**: `CREATE TABLE AS` fast, `SELECT count(*)` over the same tree unusably slow |
| 4 | **polars cannot build the honest table**, as on entry 28 — a second failure, and I predict a DIFFERENT cause than the name collision there |
| 5 | **pandas `json_normalize` explodes**, producing a table wider than 100,000 columns or dying trying |
| 6 | **No tool names alternative row shapes and prices them.** 29th entry running |
| 7 | **`version_added` being string, boolean or null is visible to jq, jqr and duckdb** and invisible to pandas and polars, which will coerce it to text |
| 8 | **Q6 — are any object keys data — is CANNOT in at least twelve of the fourteen** |
| 9 | **Q0 is CANNOT in all fourteen.** Every parser here takes the last duplicate key silently |
| 10 | **THE ONE THAT MATTERS: rrapply and duckdb handle the nesting defect 36 fails on**, because a melt names each level as its own column and never has to decide whether a level's keys are data |

> **Prediction 10 is a prediction against fathom and it is the reason this sweep
> is worth running now rather than later.** Defect 36 is fathom naming 11,320
> paths where 166 would do, on this document. **If a melt gets the same
> structure right in one call, defect 36 stops being an internal tidiness
> problem and becomes a competitive one** — which is what entry 28 did to the
> central claim, from the other direction.
>
> **If instead the melt is also unusable at this scale**, the finding is the
> opposite and more comfortable: nothing handles this document well, and
> fathom's failure is the general one.

## ALL FOURTEEN TOOLS, 2026-08-14 — and the news is about DEFECT 36

**All fourteen written, RUN, and their prose corrected against what printed.**
6 R + 8 Python. Every number below is from a run recorded in the attempt file
that produced it.

### Nine tools agree on the shape, which is worth more than any one of them

| | |
|---|---|
| **470,673 leaves** | rrapply, tidyr, jqr, jq, duckdb, tidyjson, ijson, polars, pydash |
| **depth 12** | all fourteen that can answer at all |
| **353,345 string · 117,328 boolean** | jqr, jq, tidyjson, duckdb, ijson, tidyr |
| **`version_added` 228,083 str · 57,103 bool** | jqr, jq, duckdb, tidyjson, ijson, jsonlite |
| **35,392 URL leaves** | rrapply, tidyr, jqr, jq, duckdb, polars, pydash, ijson |

**And a correction to this entry's own selection rationale.** The section above
says `version_added` is *"a string, a boolean, or null"*. **There are no nulls
in it** — and none anywhere in the document: every one of the 470,673 leaves is
a string or a boolean. The tri-typing this file was chosen for is really
two-typing, which does not change what defect 32 survived (the rule is about
counting types, and two is what it saw) but does correct the reason given.

### Q12, the flattest honest table

| tool | | |
|---|---|---|
| **duckdb** `json_tree` | 865,598 rows, ONE QUERY | **0.45 s** |
| **rrapply** `how="melt"` | 470,673 x 13, ONE CALL | **0.4 s** |
| **ijson** event stream | 470,673, one pass, **constant memory** | 0.4 s |
| **tidyjson** `json_structure()` | 865,598 x 10, ONE CALL | 53.7 s |
| **jq / jqr** `[paths, getpath]` | one expression | ~2.4 s |
| **tidyr** | 470,673 x 13 — **in TWELVE calls, loop mine** | 3.8 s |
| **pandas** `json_normalize` | **1 row x 427,019 columns** | 3.5 s |
| **polars** | **CANNOT** — `from_dicts` raises on a list-vs-string column | — |
| **jsonlite, purrr, glom, jmespath, pydash** | CANNOT, or the walk is mine | — |

### THE FINDING: no tool folds keys-as-data, and that reframes defect 36

Defect 36 is fathom naming **11,320 folded paths** for 35,392 URL values here.
The prediction written before the sweep was that rrapply and duckdb would
*"handle the nesting defect 36 fails on"*, making it a competitive problem.
**That is wrong, and the truth is more useful.** Laid out as a spectrum:

| what is folded | URL paths |
|---|---|
| nothing — rrapply, tidyr, duckdb, jq, polars, pydash | **35,392** = one per value |
| arrays only, automatically — ijson's `.item` | ~the same (3.8% off, document-wide) |
| keys-as-data — **fathom, and only fathom** | **11,320** ← defect 36 |
| one hand-written rule over rrapply's level columns | **176** |

**Not one of the fourteen attempts the keys-as-data fold.** Their answer to
*where do the URLs live* is identical to their answer to *list the URLs*.
ijson folds ARRAYS for free and nobody asked it to — worth 3.8% here, because
this document's nesting is overwhelmingly objects whose keys are data.

> **So defect 36 is a bad answer to a question nobody else asks, and the right
> answer is about 176.** Collapsing every level with more than 40 distinct keys
> takes rrapply's melt to 176 shapes in ONE LINE — and an independent
> hand-collapse of fathom's own output gave 166, so the order is confirmed.
> **fathom is wrong by a factor of about 64, at the one thing it does that
> nothing else does.** That is worse than entry 28's finding and also better:
> there is no competitor to lose to here, only a gap between what fathom
> attempts and what it achieves.
>
> **And the 40 is mine.** rrapply proposes no threshold and names no column as
> an open vocabulary; questions 3 and 6 are CANNOT in all fourteen for the 29th
> entry running. The fold is the part no tool supplies, which is exactly why
> getting it wrong matters.

### Q5 separates the fourteen more sharply than Q12 does

This document was chosen for a field that changes type, and the tools split
three ways rather than two:

| | tools |
|---|---|
| **EXACT — `type` is first-class** | **jq, jqr, duckdb, tidyjson, ijson** |
| **preserved but not reported** — you count types yourself, and the count is right | tidyr (list-column), jsonlite, purrr, polars |
| **DESTROYED** | **rrapply** — the melt returns an ATOMIC character vector, so 57,103 booleans arrive as the strings `"TRUE"`/`"FALSE"` |
| **a type INVENTED that the document does not contain** | **pandas** (NaN → float), **glom** (`Coalesce` default), **pydash** (`get` default), **jmespath** (None for an absent path) |

**The four that invent one all report the same wrong shape** — glom, pydash and
jmespath each give `NoneType 103, str 938, bool 49` for `chrome.version_added`
across the 1,090 api records, and the 103 Nones are the tool's fill for a
record that has no chrome entry. The document has no nulls at all.

**The rrapply result is the sharpest single finding of the sweep.** The verb
that wins Q12 in R answers Q5 **wrong, silently**, on the one field this
document exists to test — and `FALSE` is itself a legal `version_added` string,
so the distinction cannot be recovered afterwards. Entry 28 called that melt
*"the single best verb any of the fourteen brings to this document"*; on a
document with real polymorphism it is the only one that destroys it.

**Three tools report a `NoneType` or `NaN` that is their own fill**, not data.
Counting value types over a filled result counts the filling — a mistake two
separate attempt files here made before jq contradicted them.

### Q10 needs the array/key distinction, and twelve tools have thrown it away

*How many leaves sit under an array index?* Truth: **70,420**, confirmed by two
independent walks, in R and in Python.

| | |
|---|---|
| **duckdb** | **70,420** — `fullkey` writes `chrome[0]` and `.chrome` differently |
| **jq / jqr** | **70,420** — a path is an ARRAY OF STEPS; an index is a *number*, a key is a *string* |
| rrapply, pydash | **75,791** — over by 5,371 |
| tidyr | **5,374** — under by 65,046 |
| pandas, polars, glom, jmespath | CANNOT |

**The cause is one property of this document: 1,076 of its object keys are all
digits**, because browser releases are keyed `1`, `10`, `58`. Once a key and an
index are both plain strings in a path column, nothing separates them.
**rrapply and pydash agree exactly at 75,791 and are both wrong** — two tools,
two languages, the same assumption. Agreement is not correctness.

### Three predictions wrong, two half right, five right

| # | predicted | outcome |
|---|---|---|
| 1 | rrapply wins R, **over 30 s** | **half.** Wins; **0.4 s**, wrong by two orders |
| 2 | tidyjson **fails** at this scale | **WRONG.** 53.7 s, and the scaling is **sublinear**, log-log slope 0.77 |
| 3 | duckdb wins; the **880x cliff bites** | **half.** Wins; **no cliff** — inline is 4x *faster*, ratio 0.2x |
| 4 | polars cannot, **different cause** | **right, both halves.** A list-vs-string type conflict, not entry 28's name collision |
| 5 | pandas explodes past 100,000 columns | **right.** 427,019 |
| 6 | no tool names row shapes and prices them | **right**, 29th entry running |
| 7 | the polymorphism is visible to jq/jqr/duckdb | **right, and richer** — tidyjson and ijson too, and three tools invent a type |
| 8 | Q6 CANNOT in ≥12 of 14 | **right** — CANNOT in all fourteen |
| 9 | Q0 CANNOT in all fourteen | **right** |
| 10 | **rrapply and duckdb handle the nesting defect 36 fails on** | **WRONG, and it is the finding.** Neither folds keys-as-data at all |

### ⚠ ENTRY 27's duckdb CLIFF DID NOT REPRODUCE

`27-grafana-dashboard` measured `CREATE TABLE AS` at 0.24 s against
`SELECT count(*)` over the same `json_tree` at 211 s — **880x** — and entry 28's
timings were flagged as worth re-reading because of it. **On duckdb 1.5.5 and
this document: 0.45 s materialised, 0.11 s inline. The inline form is four
times FASTER.** Entry 27's measurement stands for its own document and version;
what does not stand is treating the cliff as a property of duckdb.

### The jq idiom, confirmed on the document that punishes it most

`paths(scalars)` returns **380,049**; the corrected expression returns
**470,673**. **90,624 leaves dropped silently, 19.25%** — the corpus's worst
case, exactly as `VERDICT.md` warned. The reason is visible in the type census:
**every leaf here is a string or a boolean**, so `false` is not an edge case,
it is a quarter of the file. **jq and jqr agree on every number**, which is the
one place in this grid where a disagreement would have meant a binding bug.

### What none of the fourteen does, for the 29th entry running

**No tool names alternative row shapes and prices them.** Q3 and Q6 are CANNOT
in all fourteen. duckdb counts 8,893 children under `$.api` and has no opinion
about whether that makes them data; jq counts 1,090 and likewise. **The count
is available everywhere and the judgement nowhere.**

## What this file disconfirmed

**That deep nesting by feature path means recursion.** BCD nests features inside
features — `api.Document.body` under `api.Document` — and **recursion is 0**,
because a sub-feature is not the same SHAPE as its parent: the parent carries
`__compat` and the child carries its own. Prediction 5 assumed self-similarity
from self-nesting, and they are different things. `02-hn-thread` remains the only
document in the corpus where recursion fires.

**That a 19.9 MB file is where the central claim looks best.** 0.889% is worse
than 22 of the 29 entries, and three quarters of it is defect 33. The claim is
about proportion to structure, and this document simply HAS a great deal of
structure: 838,880 distinct paths and an explosion factor of 933.

