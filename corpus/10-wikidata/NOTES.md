# 10 — a Wikidata entity

## The expectation, written 2026-08-09 before `source.json` was saved

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   2a811f50a2dbac766639720beeb2188e62d4d394
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

**Disclosure.** Q42's twelve top-level keys were listed while checking the
endpoint answers — `aliases, claims, descriptions, id, labels, lastrevid,
modified, ns, pageid, sitelinks, title, type` — and four entities were sized to
pick the richest: Q30 at **1,466,078 bytes with 469 claim properties**, against
Q145's 977 KB, and Q1 and Q5 at ~200 KB. Nothing below the top level has been
looked at, and no snak, value or datatype has been seen in this file.

### Why this file

**Two repairs are sitting on `2a811f50…` with no held-out evidence** — *the parent
is the table*, and ordered-and-capped output — and
`design/implementation.md`'s gate wants three consecutive files that do not change
the probe's output. The last four all changed it.

Wikidata was chosen because it is **keys-as-data at four levels in a document
people genuinely suffer from**, and because its polymorphism has a discriminator
sitting *inside* the record, which is operation 4's textbook case arriving in a
real file rather than a specification:

- `labels`, `descriptions`, `aliases` keyed by **language code**
- `claims` keyed by **property ID** — 469 of them here
- `sitelinks` keyed by **wiki**
- every snak carries `datatype` and `snaktype`, and `datavalue.value` is a
  **string for one datatype and an object for another**

### What is predicted

**1. The partition fires on `datatype` or `snaktype`, and this is the point.**
A snak is `{snaktype, property, hash, datavalue, datatype}`, and what
`datavalue.value` holds is decided entirely by `datatype` — a bare string for
`external-id`, `{amount, unit}` for `quantity`, `{time, precision, calendar}` for
`time`, `{latitude, longitude}` for `globe-coordinate`. **That is `05-fhir-bundle`'s
`resourceType` in a document nobody specified for this project.** Predicted:
`SPLIT ON datatype` or `SPLIT ON snaktype` at the snak path.

**2. Genuine polymorphism at `datavalue.value`.** Predicted `text` against
`object`, and **not** carrying the *"not really — an artifact of folding"* label,
because the values genuinely differ. `09-stripe-openapi` gave the corpus its
first real polymorphism; this would be the second, and from a different cause.

**3. `ALIGNED BY POSITION` stays silent.** Nothing here is a table stored in
columns. **Third held-out false-positive test for the repaired rule**, and the
first since *the parent is the table* replaced the length threshold.

**4. Under 200 lines.** `09-stripe-openapi` is 226 at 7.6 MB with 47 keyed sites.
This is 1.5 MB. If the cap works, output should be bounded well below Stripe's;
if it runs long, the cap is not doing what it was written for.

**5. Recursion 0, and correctly.** Qualifier snaks have the same key-set as
`mainsnak`, so the *old* key-set-equality detector would very likely have called
this recursive. The repaired one wants the first field step of the descent to be
a key the ancestor carries, and a `mainsnak` has no `qualifiers`. **Predicted: no
recursion reported, and that is the reachability fix earning its keep on a
document built to trip the old rule.**

**6. Keys-as-data ≥ 5 sites**, and `labels`/`descriptions`/`aliases` reported as
data rather than undecided — language codes are an open vocabulary, unlike the
closed `get`/`post` that `classify()` cannot decide.

**7. `rows("entities.Q30.claims.*")` returns 469 rows**, one per property, with
the key column carrying the property ID. `rows()`'s best case for the third time.


---

## Provenance

| | |
|---|---|
| what | Wikidata entity **Q30** (United States), full JSON |
| source | `wikidata.org/wiki/Special:EntityData/Q30.json`, see `fetch.sh` |
| fetched | 2026-08-09 |
| size | 1,466,078 bytes, committed |
| chosen from | Q30, Q145 (977 KB), Q1 and Q5 (~200 KB) — the richest |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers.
**0.83 s, 92 MB resident** for a 1.4 MB file.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 1,466,078 · depth **13** · paths **19,149** · fields 48 · explosion 398.9 |
| keys-as-data | **7** · ragged by absence 54/89 · ragged by null 0 |
| recursion | 0 · polymorphic **3** · heterogeneous 1 · path variance 28 · row shapes 10 |

> **Regraded 2026-08-12: row shapes is now 13.** The line above records what was
> measured on the day and is left alone.
>
> **This entry is where defect 28 was found and it cost more than a label.** The
> menu printed one line, `an item of <key> — 707 rows x 2 cols`, for **four**
> keys-as-data sites: `aliases` at 707 items, `claims` at **1,724**, its
> `qualifiers` at 1,271 and their `snaks` at 1,413. `<key>` is the same string
> at every site, so the de-duplication treated them as one name and kept the
> first in sorted order — **the smallest, and the only one that is not the point
> of the document.**
>
> After the repair the four are named `aliases.*`, `claims.*`, `qualifiers.*`
> and `snaks.*`, and **`an item of claims.*` prices at 1,724 rows x 98 cols,
> 88% empty** — the shape a reader of this file most needs and could not
> previously see. See `FINDINGS.md`, 2026-08-12.

## Prediction scorecard: six of seven

| # | predicted | outcome |
|---|---|---|
| 1 | **the partition fires on `datatype`/`snaktype`** | **WRONG. 0 splits — see below** |
| 2 | genuine polymorphism at `datavalue.value` | **confirmed. 3 fields, `object x1,210, text x512`, no artifact label** |
| 3 | `ALIGNED BY POSITION` silent | **confirmed** |
| 4 | under 200 lines | **confirmed. 75 lines, 4.5 KB, widest line 131** |
| 5 | recursion 0, correctly | **confirmed on the number, wrong on the reason — see below** |
| 6 | keys-as-data ≥ 5, languages called data | **confirmed. 7 sites** |
| 7 | `rows()` 469 rows, key column carries the property ID | **confirmed. 469 × 2, first key `P2924`** |

## What the file established

### 1. No new defect — the first such file in five

`09-stripe-openapi`, `08-open-meteo`, `07-graphql-introspection` and
`05-fhir-bundle` each broke something. **This one did not.** Every repair on
`2a811f50…` behaved: the alignment rule stayed silent on its third held-out
document, output stayed bounded at 75 lines where Stripe's 943 became 226, and
nothing needed fixing.

**`design/implementation.md`'s gate wants three consecutive corpus files that do
not change the probe's output. This is the first.**

### 2. The partition failed — and the reason recorded here on the day was WRONG

`datatype` is on the **snak**; the polymorphism is at
`mainsnak.datavalue.value`, one level below. So:

```
…claims.<key>[].mainsnak            1724 copies · 5 fields · 2 distinct key-sets
  always     datatype hash property snaktype
…claims.<key>[].mainsnak.datavalue  1722 copies · 2 fields · 1 distinct key-set
  always     type value
```

**Corrected 2026-08-09, after measuring instead of reasoning from the printed
output.** The entry first written here said *"the discriminator is on the
grandparent"*, matching `probe.py`'s documented `04-gharchive` limit. **That is
not what is happening.**

`datavalue` is `{type, value}` and **`type` is inside the record**, taking six
values, each of which fixes the shape of `value` exactly:

```
wikibase-entityid  822   value shapes: [object]     string    512   [text]
quantity           218   [object]                   monolingualtext 157  [object]
globecoordinate      7   [object]                   time        6   [object]
```

**A perfect split, and the operation cannot see it**, because:

| guard | needs | this document |
|---|---|---|
| distinct filled key-sets | ≥ 3 | **1** — every datavalue has both keys |
| worst group's emptiness | ≤ half the fold's | fold is **0% empty** |

> **Operation 4 prices a split by HOLES, and this document has none. Its disorder
> is TYPE VARIATION.** Every record has the same two keys; what differs is the
> shape of a value. The discriminator is present, in the record, with the right
> cardinality — and the measure the operation uses is blind to the thing it would
> fix.

**`04-gharchive` is the genuine parent case and this is not**, so the two open
problems are distinct: gharchive's payloads have **no field present in every
payload at all**, and its `type` really does sit on the enclosing event.

And the evidence is on screen and unconnected, exactly as on
`07-graphql-introspection`: the probe reports `datavalue.value  object x1,210,
text x512` in one section and `always datatype` in another, and nothing joins
them.

### 3. A prediction that was right for the wrong reason, checked rather than claimed

Prediction 5 said recursion would be 0 **and** that the old key-set-equality
detector would have called this recursive, because qualifier and reference snaks
share `mainsnak`'s key-set — making this a test of the reachability repair.

**Measured, by running the original probe on this file: it also reports 0.** The
snak paths are not in an ancestor/descendant relation, so the old rule never
applied. **This document does not test the reachability fix at all**, and the
claim that it did would have been a plausible, unverified, and wrong thing to
write down.

## What it disconfirmed

**That a document with an inside-the-record discriminator is enough.** Wikidata
has `datatype` on every snak and the partition still cannot use it, because
"inside the record" has to mean *inside the record whose shapes vary* — and here
those are one level apart. The operation's stated precondition is narrower than
it reads.

## The R half — predictions, written 2026-08-10 BEFORE the tools were run

**Committed as its own change, before any R attempt file exists in this
directory**, so the order is checkable rather than asserted. Rule 1.

This file is being used to test three claims made on 2026-08-09 by the R
backfill of `01`, `02`, `03`, `05` and `09`. Each rests on the files that
produced it, and this document is unlike all five: it has the corpus's **highest
path explosion (398.9)**, **7 keys-as-data sites whose keys are identifiers**,
and **genuine polymorphism by TYPE** — `datavalue.value` is `object x1,210,
text x512` — where `03` tested depth and `05` tested key-sets.

**1. jq's distinct-leaf-name count will be SMALL — under 100.** The two-cause
claim says the key reaches a leaf only when a keyed object's values are SCALARS.
Wikidata's keys are P-numbers and language codes holding OBJECTS, so they should
be invisible to `paths(scalars)|last` exactly as Stripe's 1,440 schema names
were. **If this comes back in the thousands the refinement is wrong**, because
this file has 7 keyed sites and an explosion of 398.9 and ought to be the worst
case for it.

**2. `tidyjson::json_schema` will report ONE of `string`/`object` for
`datavalue.value` and silently drop the other.** On `03` it dropped a nesting
level; on `05` its coverage fell to 36%; on the synthetic control `["a",{"b":1}]`
the string vanished in both orders. **This is the first GENUINE type
polymorphism in real corpus data it has been asked about**, and the coverage
claim predicts it answers rather than declines.

**3. rrapply's melt will exceed 100% of the file.** 19,149 distinct paths for 48
fields is the keys-as-data cause at its strongest in the corpus.

**4. jsonlite's simplification will be INERT** on `claims` and `labels` — the
`01`/`09` outcome, a named list and no table — because both are keyed by data.
It should NOT produce the misleading per-level frames it produced on `02`.

**A prediction that would hurt.** If tidyjson unions the two types correctly
here, claim 2 is limited to depth polymorphism and the phrase "silently discards
shapes" is too strong for its own evidence.

## The R half, run 2026-08-10 — prediction scorecard: four of four

**All five R tools run; the entry is done.** The predictions above were committed
in `1a70cb8`, before any file in `r/` existed.

| # | predicted | outcome |
|---|---|---|
| 1 | jq's distinct-leaf-name count **under 100** | **confirmed. 34**, and **0 of 469** P-numbers ever reach a leaf |
| 2 | `json_schema` reports one of string/object and drops the other | **confirmed, in the strongest form** — the object wins in **both** orders |
| 3 | rrapply's melt **over 100%** of the file | **confirmed. 173%**, and jq's every-leaf listing agrees to within 0.1% |
| 4 | jsonlite's simplification **inert** on the keyed sites | **confirmed** on all five — claims 469, labels 393, descriptions 180, aliases 246, sitelinks 425, no tables |

**The prediction that would have hurt did not happen.** It was written down: if
`json_schema` had unioned string and object correctly, the coverage claim would
have been limited to depth polymorphism.

### 1. The two-cause claim survives its worst case — and gains a remedy clause

This is the corpus's most path-exploded document — **19,149 paths for 48 fields,
ratio 398.9** — with 7 keyed sites. If jq's leaf-name count tracked keys-as-data
it would be enormous. It is **34**, because Wikidata's keys hold objects.

| file | jq leaf names | keyed sites | keys hold |
|---|---|---|---|
| `01-npm-registry` | **3,100** | 6 | **scalars** |
| `03-natural-earth` | 63 | 0 | — |
| `09-stripe-openapi` | 29 | 47 | objects |
| **`10-wikidata`** | **34** | 7 | objects |

**And the two causes need two different folds**, which the 2026-08-09 statement
named without saying:

```
raw melt                        46,704 paths   173.04%
fold ARRAY INDICES to []        12,265 shapes   43.66%
+ fold KEYED NAMES as well         968 shapes    2.73%
```

On `03-natural-earth` folding indices *alone* went 226% → **0.05%**, because that
document's repetition is numbered. Here it barely helps, because this one repeats
by NAME. **Operation 1 folds numbered siblings; operation 2 folds named ones; a
describer with only one fails on half the corpus.** The probe's own answer here
is 75 lines, 4.5 KB, 0.3%.

### 2. `json_schema` absorbs the scalar — no ordering reveals it

`datavalue.value` is `object ×3,049, text ×1,352` counting every datavalue at any
depth (the grades above count 1,210/512 for the three named fields — a narrower
denominator for the same property).

```
text alone      {"type":"string","value":"string"}
object alone    {"type":"string","value":{"entity-type":…,"id":…,"numeric-id":…}}
[text,object]   [{… "value":{"entity-type":…}}]     <- object
[object,text]   [{… "value":{"entity-type":…}}]     <- object
```

**31% of the records are described as something they are not.** On `03` the
answer at least depended on input order, which leaves a trace; here there is no
ordering that reveals the loss.

### 3. A correction to the coverage claim, forced by a measurement that disagreed

The 2026-08-09 claim was *a small description is not evidence of a good one*.
Measured here, `json_schema`'s output **grows** roughly in step with the input —
2,151 → 27,991 chars for a 13.5× larger slice — because 469 property ids each
mint a schema entry. And **coverage of the mainsnak key names is 100%**, since a
mainsnak has five keys.

> **So on this document `size` fails, `coverage-of-key-names` passes, and a third
> of the records are still typed wrongly. Neither instrument catches it.** The
> claim is not wrong; the instrument sketched for it was the weaker half.
> **Coverage has to be measured over TYPES, not only over key names.**

Three documents, three distinct failures from one function:

| | schema size | coverage | what is lost |
|---|---|---|---|
| `03-natural-earth` | small, constant | — | a nesting level, order-dependently |
| `05-fhir-bundle` | small, constant | **100% → 36%** | key names, as kinds arrive |
| `10-wikidata` | **grows with data** | 100% | **the type**, in both orders |

### 4. The level-count test has a false-positive mode

`03-natural-earth`'s notes credit rrapply's melt with finding the
Polygon/MultiPolygon split that every type-based check missed. Third trial, third
outcome:

| file | level-count test |
|---|---|
| `03-natural-earth` | two populations, exactly right — **true positive** |
| `05-fhir-bundle` | silent — variation is by key-set |
| **`10-wikidata`** | **six populations where the split is two — misleading** |

`datavalue` appears in mainsnaks, qualifiers and references, so its leaves bottom
out at six depths and the type difference is smeared across all of them. **Any
document repeating one field at several nesting levels will do this.** The credit
stands for what it found on `03`; it is not a general polymorphism detector.

### 5. One rule, five documents, four behaviours, and no signal which fired

| file | what jsonlite's simplification did | |
|---|---|---|
| `03-natural-earth` | builds the frame, **preserves** the depth split | SAFE |
| `05-fhir-bundle` | builds it, folds 20 kinds into 87% holes | WRONG |
| `01-npm-registry` | builds nothing — keys are data | INERT |
| `09-stripe-openapi` | builds nothing, at 10× the size | INERT |
| **`10-wikidata`** | **builds nothing — keys are identifiers** | **INERT** |
| `02-hn-thread` | builds one per level, none compose | MISLEADING |

**Nothing in the output says which happened.** That is the criticism in its
sharpest form — not that any one behaviour is wrong, but that a person cannot
tell a preserved polymorphism from a folded one from a refused fold.

### 6. Raggedness turned out to be a partition again

purrr's question 9: exactly one of 469 mainsnaks lacks `datavalue` — **`P2997`,
and its `snaktype` is `somevalue`**, Wikidata asserting a property whose value is
unknown. On `05-fhir-bundle` the rows missing `status` were four whole
resourceTypes. **Twice now on unrelated documents, apparent raggedness is a
partition wearing a disguise, and `%||% NA` hides it both times.**

**What purrr does best here is `imap_dfr`** — it hands the function the key
alongside the value, so 469 property ids arrive as a column rather than becoming
addresses. It is the shortest correct answer any R tool gives on this file, and
it is equally happy where the name is *not* data. **The mechanism for operation 2
is in every one of these tools; the diagnosis is in none.**

## Status

**R half complete 2026-08-10** — purrr, jsonlite, tidyjson, rrapply, jqr, plus
tidyr. Python is 8 attempts. Under `CLAUDE.md`'s definition this entry is done.

## Corrected 2026-08-13: 34 → 35 leaf names

**The grades above are left alone.** `paths(scalars)` drops every `false` and
`null` leaf — see `01-npm-registry`. The invisible name was **`altitude`**,
which Wikidata writes as `null` on every coordinate.

| | recorded | corrected |
|---|---|---|
| distinct leaf names | **34** | **35** |
| every-leaf character total | **2,535,600** | **2,536,104** |

**THE FINDING IS UNCHANGED**: 35 against 48 true fields is still UNDER, still
because seven keyed sites hold objects. Q11's URL search is exact either way.
