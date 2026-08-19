# 07 — a GraphQL introspection result

## The expectation, written 2026-08-09 before `source.json` was saved

**Committed as its own change, before the file exists in the repository.**

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   473fe0f1e0b0e6f93419734d7b384db12af76e9c
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

**Disclosure.** Three public endpoints were POSTed `{__schema{types{name kind}}}`
on 2026-08-09 to confirm they answer, which returned counts of 23, 25 and 108
types. The 108 was chosen as the richest. Nothing below that level has been
looked at, and no introspection field beyond `name` and `kind` has been seen.

### Why this file

**It is the first specimen chosen to test repairs rather than to fill an axis.**
Three changes landed on 2026-08-09 with no held-out evidence at all:

| change | what should happen here |
|---|---|
| reachability in `fold_recursion` | `ofType` is genuinely self-similar — it should fire, correctly |
| partition on a discriminator | `types[]` holds six kinds, discriminated by `kind`, inside the record |
| `ALIGNED BY POSITION` | there are no parallel arrays — it should stay **silent** |

A GraphQL introspection result is also what `corpus/README.md` asks for on
provenance: **written by a server describing itself**, not curated by an API
designer for human consumption.

### What is predicted

**1. Recursion fires on `ofType`, and correctly.** A type reference is
`{kind, name, ofType}` and `ofType` holds another one — `NON_NULL` wrapping
`LIST` wrapping `NON_NULL` wrapping a named type. The repaired detector requires
the first field step of the descent to be a key the ancestor carries, and
`ofType` is exactly that. Predicted: `RECURSIVE` on the type-reference path, at
3–5 levels.

**2. `ALIGNED BY POSITION` stays silent.** Nothing here is a table stored in
columns. This is the false-positive test for the newest feature and the outcome
that would matter most if it went wrong.

**3. THE PARTITION WILL NOT FIRE, AND IT SHOULD.** This is the prediction worth
writing down.

> GraphQL introspection gives **every** type the **same key set** — `name`,
> `kind`, `description`, `fields`, `inputFields`, `interfaces`, `enumValues`,
> `possibleTypes` — and expresses "this is a SCALAR, not an OBJECT" by setting
> the irrelevant ones to **`null`** rather than omitting them.

`discriminator()` requires **3 or more distinct key-sets** before it will look for
a discriminator, and it measures a split's worth by `emptiness()`, which counts
**absent keys**. If every type carries every key, there is one key-set, zero
emptiness, and the function returns `None` at its first guard — on a document
whose records are *six genuinely different kinds* with the discriminator sitting
in plain sight.

**Predicted: 0 splits, and that is a defect rather than a correct silence.** The
fold measures raggedness by absence and this document is ragged by null. If the
partition *does* fire, the operation is more robust than its author thinks and
that is worth knowing too.

**4. Ragged-by-null high, ragged-by-absence near zero.** Same cause as 3.

**5. keys-as-data: 0.** GraphQL names its fields.

**6. Under 120 lines.** 108 types folding into a handful of shapes is exactly what
operation 1 is for. Four files gave 73, 25, 31 and ~10; file 05 gave 393 because
the fold had no scope; file 06 gave 55.

**7. `rows("__schema.types.*")` returns 108 rows**, with `fields`, `enumValues`
and `possibleTypes` as list-columns — the same god-seam problem `06-espn-qbr`
raised, in a second document.

---

## Provenance

| | |
|---|---|
| what | the SpaceX public GraphQL API describing its own schema |
| source | `https://spacex-production.up.railway.app/`, see `fetch.sh` and `query.graphql.json` |
| fetched | 2026-08-09 |
| size | 143,376 bytes, committed |
| chosen from | three public endpoints answering introspection: 23, 25 and **108** types |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no integers past 2^53.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 143,376 |
| depth | **13** — deepest in the corpus |
| recursion | **4** |
| distinct paths | 94 |
| fields | 22 |
| explosion | 4.3 |
| keys-as-data | 0 |
| ragged by absence | **0/46** |
| ragged by null | **21** |
| polymorphic | 0 |
| heterogeneous | 0 |
| path variance | 9 |
| row shapes | 11 |

**`0/46` absent and `21` null is the whole story of this file**, and it is the
first document in the corpus with that shape. Compare `04-gharchive` at 53/727
absent and 33 null, or `05-fhir-bundle` at 153/442 absent and **0** null.

## Prediction scorecard: seven of seven

| # | predicted | outcome |
|---|---|---|
| 1 | recursion fires on `ofType`, correctly, 3–5 levels | **confirmed.** 4 sites, at 2 and 4 levels, all on `{kind, name, ofType}` |
| 2 | `ALIGNED BY POSITION` stays silent | **confirmed. 0** |
| 3 | **the partition will not fire, and that is a defect** | **confirmed. 0 splits** |
| 4 | ragged-by-null high, by-absence near zero | **confirmed. 0/46 and 21** |
| 5 | keys-as-data 0 | **confirmed** |
| 6 | under 120 lines | **confirmed. 71** |
| 7 | `rows()` 108 rows with list-columns | **confirmed. 108 x 9**, `fields` a list-column |

**Seven of seven is only worth anything because of number 3**, which predicted a
failure in the newest operation, named its cause, and was written before the file
existed.

## What the file established

### 1. The two repairs work

**Reachability.** `ofType` is genuinely self-similar — a type reference is
`{kind, name, ofType}` holding another type reference — and the repaired detector
fires on it at four sites, correctly. This is the first held-out confirmation
that the fix did not break what it was written to preserve.

**`ALIGNED BY POSITION` stays silent** on a document with no parallel arrays.
First held-out false-positive test for the newest feature.

### 2. The partition operation fails, exactly as predicted, and the probe already holds the number that would fix it

```
$.data.__schema.types[]   108 copies · 8 fields · 1 distinct key-set
  always     description enumValues fields inputFields interfaces kind name possibleTypes
```

Every type carries all eight keys. GraphQL says *"this is a SCALAR, not an
OBJECT"* by setting the irrelevant ones to **`null`**, not by omitting them. So
`discriminator()` sees one key-set, bails at its `shapes < 3` guard, and never
looks at `kind` — which is sitting in the always-list, holding
**`OBJECT` 68, `INPUT_OBJECT` 20, `SCALAR` 12, `ENUM` 8**.

**The mechanism is sharper than the prediction. The probe computes emptiness
twice, by two incompatible definitions, and the two disagree by 52 points on this
table:**

| | measure | on `types[]` |
|---|---|---|
| `price()`, in the row-pricing | `pandas.isna()` — **a null is a hole** | **52% empty** |
| `emptiness()`, used by `discriminator()` | `set(o) & cols` — **a null key is present** | **0% empty** |

> **The probe prints `an item of types  108 rows x 8 cols  52% empty` in its own
> output and then declines to split, because the function that decides uses the
> other definition.** The number that would justify the operation is already on
> screen. Nothing routes it to the function that needs it.

**This is the fifth instance of one root cause**: depth by splitting a dotted
string, polymorphism by comparing types at a path, recursion by key-set equality,
array shape by nesting depth alone, and now **raggedness by key presence rather
than by whether there is a value**.

### 3. And it says the fields are polymorphic instead

The report does contain the evidence, in the wrong section:

```
$.data.__schema.types[].fields        array[1] x68, null x40
$.data.__schema.types[].inputFields   null x88, array[1] x20
$.data.__schema.types[].enumValues    null x100, array[1] x8
$.data.__schema.types[].interfaces    array x68, null x40
```

`fields` is an array on exactly the 68 OBJECT types and null on the other 40.
**That is the partition, reported as four separate polymorphic fields.** A reader
who cross-referenced those counts against `kind` would recover the split by hand;
the probe presents them as unrelated type variations.

### 4. `rows()` produces list-columns again

```
rows('data.__schema.types.*')   108 rows x 9 cols
  fields   [{'name': 'address', 'description': None, 'args': [], …
```

Second file after `06-espn-qbr` where the natural extraction yields nested data
as a value, which `CLAUDE.md` records that god's spec refuses. **Two of seven
files now put pressure on the seam**, which makes it a pattern rather than an
incident.

### 5. A number this entry got wrong, caught 2026-08-09 while writing the Python grid

**This file has four kinds of type, not six.** Measured:

```
OBJECT 68   INPUT_OBJECT 20   SCALAR 12   ENUM 8      = 108
```

There is no `INTERFACE` and no `UNION` in this schema. The expectation block
above says *six* twice, and `VERDICT.md` repeated it as measured fact until this
was caught — a number living in two places and stale in one, for the sixth time.

**The expectation block is left exactly as written**, because rule 1 makes it a
record of what was believed beforehand and editing it would destroy the only
thing it is for. The correction lives here and in `VERDICT.md`.

**It does not change the finding.** The defect was that the partition could not
see a discriminator sitting in plain sight, and four kinds discriminated by
`kind` is that defect unchanged. What it does change is a reader's sense of how
carefully the advance description was checked: it was not, and *six* was
plausible enough that nobody counted for a day.

**Two more numbers, measured at the same time and both relevant to the repairs
that have landed since:** `types[]` has **1** distinct key-set and **8** distinct
*filled* key-sets. The prediction above reasoned that the operation would stop at
its first guard because there was one key-set. After the null-aware emptiness
repair that guard counts filled key-sets, so it now passes at 8 — which is why
`FINDINGS.md` records graphql as splitting once today.

## What it disconfirmed

**That raggedness is one axis.** The corpus has graded absence and null
separately since `01-npm-registry`, and until now no file made the distinction
consequential. This one is `0/46` absent and `21` null, and the operation that
would have described it correctly is blind to exactly that half.

## The R half — predictions, written 2026-08-10 BEFORE the tools were run

**Committed as its own change, before any R attempt file exists in this
directory**, so the order is checkable rather than asserted. Rule 1, following
`05-fhir-bundle`'s precedent.

**This file is the CONTROL for the two-cause O(data) claim.** That claim, made
2026-08-09 and sharpened 2026-08-10, says a describer's output explodes when it
refuses to fold repeated siblings — numbered (array elements) or named
(keys-as-data). This document has **keys-as-data 0** and **explosion 4.3**, the
lowest in the corpus after `03-natural-earth`. It also has **depth 13**, graded
"deepest in the corpus", and **genuine recursion at `ofType`**.

**So the two hypotheses make opposite predictions here, which is what makes it
worth running.** `VERDICT.md` says depth is not the driver; if depth mattered
this document would be expensive.

**1. rrapply's melt will come in UNDER 100% of the file, and should be the
cheapest of the five measured.** The running table is npm 3,112 chars ·
Stripe 141% · natural-earth 226% · FHIR 60% · wikidata 173%. **If depth drives
the blowup this will be high**, because 13 levels of `ofType` make long paths
over short values. If repetition drives it, this is the cheap case.

**2. jq's distinct-leaf-name count will be UNDER 40, and roughly equal to the
true field count of 22.** On `03-natural-earth`, which also has keys-as-data 0,
the same expression returned 63 against 63 real property fields — correct. This
predicts the expression is *accurate* when nothing is there to confuse it,
which is the other half of the npm/Stripe result.

**3. jsonlite's simplification will BUILD A FRAME over `types[]` and fold the
kinds together** — the `05-fhir-bundle` WRONG outcome in mild form, not the
INERT one, because `types` is an ARRAY and not a keyed object. Expect ~108 rows
with real NA. **This is the first time the four-outcome taxonomy is used to
predict rather than to summarise**, and getting it wrong would mean the taxonomy
is a post-hoc label.

**4. rrapply's level-count test will FIRE AND MISLEAD**, as it did on
`10-wikidata`. `ofType` is self-similar at 2 and 4 levels, so its leaves sit at
several depths for reasons of position rather than type. NOTES.md grades this
file `polymorphic 0`, so **any population structure it reports is a false
positive** — the cleanest available test of the failure mode found yesterday.

**5. `tidyjson::json_schema` coverage will be HIGH here** — 22 fields, no
heterogeneity — so this is the case where the coverage instrument passes
honestly. **The prediction that would be interesting is a third kind of loss:**
that the recursive `ofType` is reported to whatever fixed depth happened to be
in the input, so the schema states a bounded nesting where the document's rule
is unbounded. Not a dropped type, not dropped keys — a dropped generality.

**A prediction that would hurt.** If melt comes back high on a document with
keys-as-data 0 and small arrays, the two-cause claim is incomplete and depth
belongs in it after all.

## The R half, run 2026-08-10 — prediction scorecard: three, a half, and a miss

**All five R tools run; the entry is done.** Predictions were committed in
`ece63f5`, before any file in `r/` existed.

| # | predicted | outcome |
|---|---|---|
| 1 | melt **under 100%**, cheapest of five | **FALSIFIED. 203.6%** — second-highest in the corpus |
| 2 | jq leaf names under 40, **≈ 22** | **HALF.** 7 — under 40, but a third of the field count |
| 3 | jsonlite **builds a frame** and folds the kinds | **confirmed. 108 × 8**, four kinds folded |
| 4 | level-count test **fires and misleads** | **confirmed. Six populations on a `polymorphic 0` file** |
| 5 | coverage high; recursion flattened to a bound | **confirmed, both halves** |

**A falsified prediction and a half-miss are worth more here than five hits**,
and both corrected something.

### 1. The melt percentage is a bad instrument, and this file proves it

Prediction 1 said this document would be cheap: keys-as-data **0**, explosion
**4.3**. It came in at **203.6%**, above Stripe and Wikidata.

```
average value size    22.0 bytes per leaf
average path length   44.9 chars per leaf
```

The ratio is path-characters over file-bytes, so it rises when paths are **long**
and values are **short**. This document is 13 levels deep with names like
`possibleTypes` and `deprecationReason`, holding mostly nulls and short enum
strings. **The percentage measures verbosity as much as failure to fold.**

**The claim survives on the statistic that actually states it** — the fold factor:

```
6,504 leaves  ->  73 path shapes by folding array indices alone
                  an 89x fold, 2.57% of the file
```

That is the same behaviour as `03-natural-earth`, whose repetition is also
numbered, and unlike `10-wikidata`, where the names had to be folded too. **So
this document IS the control it was chosen to be; the measurement that
disagreed was the wrong one.**

> **What should change:** `VERDICT.md`'s O(data) percentages are fair evidence
> for *this tool's answer is bigger than the document*, which is what they are
> cited for. They are **not** evidence for *this document needs more folding*.

### 2. jq's expression is accurate only on a flat document

**7 leaf names against 22 fields.** `paths(scalars)|last` can only see a field
whose value is a SCALAR, and every structural field here — `types`, `fields`,
`args`, `interfaces`, `ofType` — holds an object or an array.

| file | jq answer | truth | |
|---|---|---|---|
| `01-npm-registry` | **3,100** | ~40 | OVER by 75× — keys are leaves |
| `03-natural-earth` | 63 | 63 | **CORRECT** — flat document |
| `09-stripe-openapi` | 29 | 1,440+ | UNDER — keys hold objects |
| `10-wikidata` | 34 | 48 | UNDER — keys hold objects |
| **`07-graphql`** | **7** | **22** | **UNDER by 3×** — fields hold structure |

**Right exactly once, on the one flat document.** That is the third narrowing of
the npm 3,100 in two days.

### 3. THE NULLS ARE THE PARTITION — exactly, and it explains this entry's own defect

Measured four independent ways (jq, jsonlite, purrr, tidyjson — all agreeing):

```
absent:  0 of 864 cells        <- 0% empty, and the only test jsonlite can run
null:    447 of 864 cells      <- 51.7% empty, the truth

fields 68, interfaces 68   <-  OBJECT        68
inputFields 20             <-  INPUT_OBJECT  20
enumValues 8               <-  ENUM           8
possibleTypes 0            <-  nothing at all
```

**`kind` predicts every null in the document.** Fourth instance in three days of
raggedness turning out to be a partition wearing a disguise — after
`05-fhir-bundle`'s four whole resourceTypes and `10-wikidata`'s `somevalue`
snak — and the **second where the disguise is `null` rather than absence.**

> **And this is why the probe finds nothing here.** The expectation above
> predicted *the partition will not fire, and that is a defect*, and confirmed 0
> splits. The reason is now measured: **emptiness by key PRESENCE is 0% on this
> document**, so no split can ever look worthwhile, while emptiness counting
> nulls is 51.7% and splits perfectly on `kind`. That is `VERDICT.md` defect 5 —
> two definitions of empty — in the one place it still bites.

`possibleTypes` is null on all 108: a field every record carries and none fills,
the same shape as `03-natural-earth`'s `woe_id` at `-99` on all 241 rows.

### 4. The level-count test fires on a document with nothing to find

Fourth trial, fourth outcome:

| file | level-count test |
|---|---|
| `03-natural-earth` | two populations, exactly right — **true positive** |
| `05-fhir-bundle` | silent — variation is by key-set |
| `10-wikidata` | six where the split is two — misleading |
| **`07-graphql`** | **six where there is NO split — false positive** |

`ofType` is genuinely self-similar, so its leaves bottom out at six depths for
reasons of **position**. This file is graded `polymorphic 0`, so every population
is wrong by construction. **Its one success on `03` required a document with no
recursion**, where depth could only mean shape — a narrow condition. purrr, asked
the same question here, correctly reports none.

### 5. A fourth distinct loss from `json_schema`

Coverage is **100%** here and honest — 22 fields, nothing to discard — which
matters, because an instrument that fails on every input measures nothing. What
is lost instead is the **generality**: `ofType` is reported to a fixed number of
levels, whatever the deepest chain in the input happened to be, where GraphQL's
rule is unbounded. Measured chains: `0 ×362, 1 ×56, 2 ×5, 3 ×9`.

| file | what json_schema lost |
|---|---|
| `03-natural-earth` | a nesting level, order-dependently |
| `05-fhir-bundle` | key names — coverage 100% → 36% |
| `10-wikidata` | a type, in both input orders |
| **`07-graphql`** | **a generality — recursion flattened to a bound** |

**tidyjson also gives the best question-4 answer in the corpus**:
`gather_object() |> json_types()` reports **`null` as a type**, so the 51.7% that
every presence-based test misses is simply a column of the result.

### A measurement error of my own, recorded because it is the corpus's own mistake

The first draft of `try-tidyjson.R` round-tripped through
`toJSON(..., auto_unbox = TRUE)` **without `null = "null"`**. jsonlite converts R
`NULL` to `{}`, so every JSON null became an empty object and the table reported
`possibleTypes: object ×108` for a field that is null on all 108 — crediting
tidyjson with a distinction it had not been given the chance to make.

**This is the error `03-natural-earth`'s NOTES.md already names**: *"Deriving a
verdict from something adjacent to the data rather than from the data. Measure
the thing, with the instrument that will be used for the real reading."* Fixed;
the corrected table cross-validates the jsonlite and purrr null counts exactly.

## Status

**R half complete 2026-08-10** — purrr, jsonlite, tidyjson, rrapply, jqr, plus
tidyr. Python is 8 attempts. Under `CLAUDE.md`'s definition this entry is done.

## Corrected 2026-08-13: 7 → 13 leaf names, the largest correction in the corpus

**The grades above are left alone.** `paths(scalars)` drops every `false` and
`null` leaf — see `01-npm-registry`.

| | |
|---|---|
| recorded | **7** leaf names against 22 fields |
| corrected | **13** leaf names against 22 fields |

**The six that were invisible are the document's most structural names** —
`enumValues`, `fields`, `inputFields`, `interfaces`, `ofType`, `possibleTypes`.
GraphQL writes `null` rather than omitting them, and the old expression could
not see a null at all.

**THE DIRECTION SURVIVES AND THE FORCE HALVES.** 13 < 22 is still UNDER, but a
68% undercount is really a 41% undercount. **The sentence above — *"7 leaf names
against 22 fields"* — is wrong as written and right as argued.**

**And the mechanism is sharper than this entry stated.** It said `fields`,
`interfaces` and `ofType` cannot be counted because they hold objects or arrays.
They ARE counted now, because they are `null` somewhere: **a field that is null
anywhere is a scalar-valued field.** Only `types` and `args` are never scalar.

> **The cross-entry table in this entry carries five other corrected numbers.**
> `01` 3,100 → 3,104 · `03` 63 → 64 · `04` 254 → 272 · `10` 34 → 35 · `12`
> 113 → 123. **And `03`'s "RIGHT, flat" verdict is withdrawn** — see that entry.
