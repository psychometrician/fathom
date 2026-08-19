# 05 — FHIR bundle

## The expectation, written 2026-08-09 before the file was fetched

**Nothing below this heading was written after seeing the document.** It is
committed as its own change, before `source.json` exists in the repository, so
that the order is checkable rather than asserted. The grading sections are absent
on purpose and get filled in after the held-out runs.

Both frozen at the moment this was written, and both must still match when the
runs happen:

```
design/probe.py   324b1c5d942ea607e66c45df69d77e5dbfad5e16
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Why this file was chosen

**Path variance**, the last axis with no specimen chosen for it, and
**heterogeneous arrays**, which `03-natural-earth` was briefly credited with and
does not have. FHIR is the rare format that supplies both from one document:

- **`value[x]`.** An Observation's value is `valueQuantity`, `valueString`,
  `valueCodeableConcept` or `valueBoolean` — the type is encoded in the *field
  name*. The same semantic value therefore lives at a different path in every
  record, which is path variance in its purest available form.
- **`entry[].resource`.** One Bundle's entry array holds Patient, Observation,
  Encounter, Condition, MedicationRequest and more — genuinely different shapes in
  one array, which is what the corpus has been missing.

### What is predicted, in falsifiable form

Recorded as specific numbers so that being wrong is visible rather than
re-narratable.

**1. The probe reports polymorphism ≈ 0, and that is a failure, not a reading.**
`value[x]` is polymorphism expressed as *renaming*, so a probe that compares types
observed at a path sees `valueQuantity` and `valueString` as two unrelated fields
that each hold one type consistently. **This is the same defect `03-natural-earth`
found** — there the polymorphism was in nesting depth, here it is in the field
name, and both are invisible to an instrument that compares types at a path. If
this prediction holds it is the second instance of one root cause, which is a
stronger finding than a new defect would be.

**2. Path variance is high but the probe has no way to say the paths are one
field.** Expect it to count the variance and still list `valueQuantity`,
`valueString`, `valueCodeableConcept` as separate fields. Counting is not
describing.

**3. The description is materially longer than anything so far, and this is the
prediction that bears on the verdict.** Four files produced 73, 25, 31 and ~10
lines. Predicted here: **over 100 lines**, because folding sibling instances —
`VERDICT.md`'s single load-bearing idea — has never met an array whose siblings
are genuinely different things. `entry.*` folds a Patient and an Observation into
one shape with almost no always-fields and an enormous sometimes-list.

> **`VERDICT.md` names exactly this as the thing that would kill Phase 2**: "a
> document where folding sibling instances is the *wrong* move". This is the first
> file with a real chance of being it. The prediction is recorded before the run
> precisely because that conclusion is the one most tempting to argue away.

**4. `rows.py` on `entry.*.resource` produces a wide sparse table and cannot say
it should be several tables.** Predicted **over 100 columns**, most of them empty
for most rows. `rows()` has one output shape and this document wants several,
which is a design question rather than a bug.

**5. Keys-as-data ≈ 0.** FHIR names its fields; nothing here is a registry keyed
by version string. If the probe reports keys-as-data sites, the prediction is
wrong and worth understanding.

**6. Recursion ≈ 0, ragged-by-absence high.** Most FHIR fields are optional, so
raggedness should be the highest yet or close to it. Recursion is possible via
`contained` but unlikely in a patient bundle.

### The provenance caveat, stated before it can look like a defence

FHIR bundles come from servers, and `corpus/README.md` warns that **an API
normalises on ingest** — it cost the corpus its polymorphism specimen twice
already. FHIR is a partial exception because `value[x]` and the mixed `entry`
array are mandated by the *specification*, not left to a server's discretion, so
they survive normalisation. That reasoning is recorded here so it can be checked
against what actually arrives rather than assumed.

**If the file turns out to be synthetic**, that is recorded in provenance and is
not fatal on the same argument `corpus/README.md` makes for scrubbing an agent
trace: every graded axis here is structural, and synthetic FHIR is structurally
what the specification requires. Synthetic *data* inside a real *shape* grades
identically. What it cannot support is any claim about values.

---

## Provenance

| | |
|---|---|
| what | one Synthea patient bundle, FHIR R4 `Bundle` of type `transaction` |
| source | `synthea_sample_data_fhir_latest.zip`, `synthetichealth.github.io/synthea-sample-data` |
| fetched | 2026-08-09 |
| file in archive | `Sharolyn456_Huels583_5b24c87b-6223-f5b4-51e9-82051159bd1d.json` |
| archive | 111 bundles, 405 MB uncompressed, 30 MB zipped, dated 2026-07-22 |
| this file | 2,024,911 bytes, committed |
| licence | Synthea output, Apache 2.0 |

**How this file was chosen, stated because "richest" would have been
cherry-picking.** The rule was *the first bundle in the archive under the 5 MB
commit threshold*, applied before any of them was opened. It happened to be the
first entry outright. No bundle was inspected and rejected.

**It is synthetic, and that is a real limitation rather than a formality.** Synthea
generates statistically plausible patients, so nothing here supports a claim about
values, distributions or real-world messiness. Every axis graded below is
structural, and the structure is what the FHIR specification mandates — which is
the same argument `corpus/README.md` makes for scrubbing an agent trace. The
attempt to use a live server is recorded under *What was tried first*.

**What was tried first.** `hapi.fhir.org`'s public R4 endpoint, which is real and
served. Its `$everything` bundles ran 3–106 entries across 3–5 resourceTypes,
mostly patients named `*-syn-*`. It is a sandbox, and a 3-entry bundle cannot
exercise a heterogeneous array. Synthea gave 564 entries across 20 resourceTypes
from a generator rather than an endpoint, which is what `corpus/README.md` asks
for anyway.

### Soundness, established before grading

Valid JSON, whole, parses in one pass. **No duplicate keys, no `NaN` or
`Infinity`, no integers past 2^53.** Read whole at 89 MB resident for a 1.9 MB
file, a 47× multiplier — high, but this file is small enough that it does not
matter, and `04-gharchive` already owns that axis.

## The grades, re-measured 2026-08-09 after the probe was repaired

**The instrument changed three times after this file was first graded, so these
numbers are not the ones the held-out run produced.** Where they differ the
original is named in the row, because `CLAUDE.md` gives this table ownership of
this file's grades and a number that silently drifts is the failure this project
has now suffered six times. Changed since the first grading: `recursion 2 → 0`
(false positives repaired), `polymorphic 3 → 4` (`category` became visible when
`shape()` learned to report element type), `ragged by absence 153/442 → 153/446`
and `row shapes 47 → 45` (both from the `filled()` change).

Produced by `uv run design/axes.py`, which grades every file identically.

| axis | measured | note |
|---|---|---|
| bytes | 2,024,911 | |
| format | JSON | one `Bundle`, `entry` array of 564 |
| depth | 11 | deepest yet |
| recursion | **0** | the probe said 2 on the day; both were false positives, repaired — see below |
| distinct paths | 580 | |
| fields | 174 | |
| explosion | 3.3 | |
| keys-as-data | **0** | FHIR names its fields |
| ragged by absence | 153/446 | 34%, against npm's 43% |
| ragged by null | 0 | FHIR omits rather than nulls |
| polymorphic | **4 — all four artifacts** | 3 on the day; `category` became visible 2026-08-09, see below |
| **heterogeneous arrays** | **9** | **first non-zero in the corpus** |
| **path variance** | **44** | the axis this file was chosen for |
| row shapes | 45 | |

### The `entry` array, which is what this file was for

564 resources, **20 resourceTypes**, in one array:

```
131 Observation   93 Procedure   64 DiagnosticReport   54 Claim
 54 ExplanationOfBenefit   48 Encounter   48 DocumentReference   19 Condition
 12 Immunization   10 SupplyDelivery    9 AllergyIntolerance    6 MedicationRequest
  5 Device          3 ImagingStudy      2 CareTeam   2 CarePlan
  1 Patient   1 Medication   1 MedicationAdministration   1 Provenance
```

**97 keys in the union, 42 distinct key-sets, and exactly two fields present in
all 564: `id` and `resourceType`.**

### `value[x]`, the path variance this file was chosen for

Eight spellings of one field, and the probe reports each as a separate field:

```
valueQuantity(127)  valueCodeableConcept(105)  valueReference(12)  valueString(9)
valueDecimal(4)     valueCoding(2)             valueAddress(1)     valueCode(1)
```

`medication[x]` does the same with `medicationCodeableConcept`(6) and
`medicationReference`(1).

**A caveat on how these were counted, because the instrument over-matched.**
Detecting choice types by the naming convention — a known stem plus a capitalised
type suffix — also catches `reasonCode`/`reasonReference` and
`procedureSequence`/`procedureReference`, which are *separate fields* in R4 rather
than variants of one. So even the naming convention does not identify choice types
reliably, which matters: it is the obvious way a tool would try to solve this.

## What the file disconfirmed

### 1. Folding sibling instances is not wrong. Folding at the wrong *scope* is.

`VERDICT.md` names one thing that would kill Phase 2: *"a document where folding
sibling instances is the wrong move, so the one load-bearing idea does not
generalise."* **This file was a real candidate and it is not that document, and
the distinction was measured rather than argued.**

Folding all 564 resources into one shape, which is what the frozen probe does:

```
564 rows x 97 cols   87% empty   42 key-sets   always: id, resourceType
```

Partitioning first on `resourceType` — a field the probe **already reports in the
always-list** — then folding within each group:

```
20 tables, 239 columns total, worst table 22% empty, eleven of them 0% empty
  131 x 14   22% empty   Observation          48 x 13    0% empty   DocumentReference
   93 x 11   16% empty   Procedure            19 x 12    3% empty   Condition
   64 x 13   12% empty   DiagnosticReport     12 x 10    0% empty   Immunization
   54 x 18   15% empty   Claim                10 x  7    0% empty   SupplyDelivery
   54 x 22    3% empty   ExplanationOfBenefit  9 x 12    5% empty   AllergyIntolerance
   48 x 13    1% empty   Encounter             6 x 15   21% empty   MedicationRequest
```

> **The fold is right. The scope was wrong, and the document said so in the output
> of the fold itself.** 42 distinct key-sets over 564 instances is the tool
> reporting that it has merged things that are not the same. Nothing consumes that
> number.

**A discriminator is discoverable without knowing FHIR**: a field present in every
instance whose value partitions the key-sets. `resourceType` is one of two
always-fields here and it partitions 42 key-sets into 20 groups averaging 1.9.
This is a **fourth operation** to sit beside the three in `VERDICT.md`, and it is
the first one the corpus has demanded rather than confirmed.

### 2. All three reported polymorphisms are manufactured by the fold

```
$.entry[].resource.type       object x171, array[1] x48, text x9
$.entry[].resource.location   object x108, array[1] x48
$.entry[].resource.total      object x54,  array[1] x54
```

Every one is polymorphic **only across resourceTypes**. Within any single
resourceType each is one type, always:

| field | array | object | string |
|---|---|---|---|
| `type` | Encounter | Claim, Device, DocumentReference, ExplanationOfBenefit, SupplyDelivery | AllergyIntolerance |
| `location` | Encounter | ImagingStudy, Immunization, Procedure | — |
| `total` | ExplanationOfBenefit | Claim | — |

Partitioning removes all three. **The probe reports polymorphism where the
document has none, and misses the place FHIR actually puts it** — `value[x]`,
which is polymorphism expressed as renaming and appears in the output as eight
unrelated fields. Wrong in both directions from one cause.

### 3. Both recursion readings are false positives, and the mechanism is exact

`fold_recursion` folds a descendant into an ancestor when the path descends by at
least one field step **and their key-sets are equal**. The docstring defends the
field-step test — it is what stopped package-lock being called recursive — but
key-set equality is the part that fails here:

- `total` is `{value, currency}`; `total[].amount` is `{value, currency}`. Folded.
  54 + 54 = **108, which is the count printed**, labelled `RECURSIVE, 2 levels`.
- `location` is `{reference, display}`; `location[].location` is
  `{reference, display}`. Folded. 108 + 48 = **156, the count printed**.

Verified directly: **`total` never contains a `total` — zero occurrences.**

> **Key-set equality is not identity, and in a format built from reusable element
> types it is not even rare.** FHIR's `Money` is `{value, currency}` and its
> `Reference` is `{reference, display}`, and both appear all over the tree at
> unrelated places. Any two of them in an ancestor/descendant relation trip the
> detector.

**This is the third instance of one root cause**, and that is the finding rather
than the bug: depth was measured by splitting a dotted string and reported 9 for a
document of depth 6; polymorphism was measured by comparing types at a path and
missed `03-natural-earth`'s nesting-depth case; recursion is measured by key-set
equality and fires on documents with none. **Each time the instrument measured a
cheap proxy for the property instead of the property.**

### 4. `rows()` reaches one spelling of `value[x]` and cannot ask for the field

First cold run of `rows.py`, hash verified before it ran:

```
rows('entry.*')                            564 rows x  4 cols
rows('entry.*.resource')                   564 rows x 98 cols
rows('entry.*.resource.valueQuantity')     103 rows x  5 cols
```

The third works and is the problem: it gets `valueQuantity` and there is no way to
say *the value, whatever it is called*. **This is the first concrete case demanding
`first_present`**, which `design/vocabulary.md` proposes and justifies against
npm's 18 path-variance sites. FHIR's case is a different mechanism and a stronger
one — npm varies the *depth* of one name, FHIR varies the *name* at one depth —
and it wants `first_present(valueQuantity, valueString, valueCodeableConcept, …)`
over eight alternatives, not two.

**The key column for an array `*` is the index, and it is not data.** `entry.*`
names its key column `entry` and fills it 0, 1, 2, …. The rule that earned the
feature — the key at every `*` is data and must survive — was derived from npm,
where the key is a version string. For an array the index is positional, and the
column is honest but empty of meaning.

## Prediction scorecard

**Three of six right.** Recorded so the misses are as visible as the hits.

| # | predicted | outcome |
|---|---|---|
| 1 | polymorphism ≈ 0, and wrongly so | **wrong on the number, right on the cause.** It reported 3, all artifacts, and did miss `value[x]` exactly as predicted |
| 2 | path variance high, `value[x]` listed as separate fields | **confirmed.** 44 sites, eight spellings listed separately |
| 3 | description over 100 lines | **confirmed. 393 lines**, against 73, 25, 31 and ~10 |
| 4 | `rows()` over 100 columns | **wrong. 98**, missed by two |
| 5 | keys-as-data ≈ 0 | **confirmed. 0** |
| 6 | recursion ≈ 0, raggedness highest yet | **split.** The document has no recursion, as predicted, but the probe reports 2; raggedness is 35%, **below** npm's 43% |

**Prediction 1 is the one worth keeping.** It predicted a number and got it wrong
while naming the right mechanism, and being wrong is what exposed the far more
interesting failure: the probe finds polymorphism that the fold created and misses
the polymorphism the format ships with. A prediction of "0" that had come out as
"0" would have hidden that entirely.

## The five R tools, run 2026-08-09 — and jq reproduces the fourth operation

**The R half was `tidyr` alone until 2026-08-09.** `purrr`, `jsonlite`,
`tidyjson`, `rrapply` and `jqr` were run that day. This entry and
`03-natural-earth` are the first outside `01`/`02` with a complete R column, and
they were chosen as a contrasting pair: GeoJSON is regular and varies by nesting
depth, FHIR is ragged and varies by key-set.

### Four tools, four routes, one set of numbers

Every tool was asked question 4 independently and they agree exactly:

| | |
|---|---|
| resources | 564 |
| union of keys under `resource` | **97** |
| distinct key-sets | **42** |
| present in ALL 564 | **`resourceType`, `id`** — and nothing else |
| folded table | **87.2% empty** |

`purrr` got there with four `map_` calls, `tidyjson` with `gather_object`,
`rrapply` from the melted frame, `jq` with `all(has($k))`. **That agreement is a
check on the numbers rather than on any one tool**, and it confirms the probe's
own reading of this file.

### 1. jq expresses the fourth operation, in ten lines, with no field named

`VERDICT.md` calls operation 4 *"the first operation the corpus demanded rather
than confirmed"* and records the probe's answer as **87% empty folded, 22% worst
split**. jq reproduces both:

```
fields present in EVERY resource, with cardinality:
  [{"field":"id","distinct":564},{"field":"resourceType","distinct":20}]

folded into one table:        12% filled  ->  88% EMPTY
partitioned on resourceType:  78% filled  ->  22% EMPTY   (worst group)
```

**Two candidates, and cardinality separates them cleanly**: `id` takes 564
distinct values on 564 records and is an identifier; `resourceType` takes 20 and
is a kind. No knowledge of FHIR is involved.

> **This does not refute the operation — it corrects how the operation is
> described.** The contribution is not arithmetic nobody could perform. It is
> knowing the question is worth asking and asking it unprompted. Nothing here
> volunteers that `entry[]` is twenty tables wearing one coat.

**It also answers open defect 13**, which wants a structural tiebreak between a
kind and an identifier and says one *"exists and is not written"*. Cardinality
among the always-present fields is that tiebreak: **20 against 564 is not a
close call**, and it is one expression.

### 2. `value[x]` has a structural signature, and it is clean

The naming convention `^value[A-Z]` finds all eight spellings — matching the
counts above exactly — but `NOTES.md` already records that the convention
over-matches, since `reasonCode`/`reasonReference` are separate R4 fields.
Measured instead, at every depth:

```
objects carrying a value* field:  261
objects carrying MORE than one:     0
```

**261 is the sum of the eight spelling counts, so every site is accounted for.**
Mutually exclusive sibling fields sharing a stem is what a choice type *is*, and
the test needs no word list and no knowledge of FHIR. This is the strongest
evidence in the corpus that **`first_present` could have a detected trigger
rather than a hand-written list of alternatives.**

### 3. `tidyjson::json_schema` describes 36% of this document and the share falls

The same failure `03-natural-earth` found, at full strength and with a number:

| resources | kinds | schema | true top-level keys | named | covered |
|---|---|---|---|---|---|
| 1 | 1 | 1,114 c | 14 | 14 | **100%** |
| 3 | 3 | 1,114 c | 25 | 16 | 64% |
| 10 | 9 | 1,879 c | 59 | 28 | 47% |
| 25 | 10 | 1,879 c | 65 | 29 | 45% |
| 50 | 15 | 2,029 c | 84 | 30 | **36%** |

**Coverage falls as the array becomes more heterogeneous**, which is the opposite
of a union. Fields present at n=1 — `name`, `birthDate`, `address`, the
Patient's — are gone by n=25. By `VERDICT.md`'s O(data) test the tool passes
easily at 2.14%, **and it passes because it decided there is less structure than
there is.**

> **Size of description is not sufficient, and this is the second unrelated
> document to show it in one day.** A describer that silently discards shapes
> always looks proportional to structure. `VERDICT.md` measures description size
> and never measures description *coverage*.

### 4. `jsonlite` performs the exact move operation 4 exists to refuse

`fromJSON()` returns `entry$resource` as a **564 × 97 data frame** — twenty kinds
folded into one shape, 87.2% holes, no warning — **and the discriminator is
sitting in the frame it just built, as a column.** On `03-natural-earth` the same
simplification rule was the *safe* choice and preserved a polymorphism polars
erased. One rule, two documents, opposite verdicts.

### 5. purrr's `%||%` converts a partition into missing data

`map_dfr` over the resources needs a default on every field but two. The rows
where `status` is `NA` are not scattered records:

```
Condition x19, AllergyIntolerance x9, Patient x1, Provenance x1
```

**Four whole resourceTypes, complete.** The idiom that makes purrr pleasant on
ragged JSON is the same idiom that hides why the JSON is ragged — the probe finds
this partition and reports it; purrr finds it, spells it `NA`, and moves on.

### 6. rrapply's melt is the third point on the size line, and its depth test fails here

| file | melt size | keyed sites | note |
|---|---|---|---|
| `01-npm-registry` | 3,112 chars | 6 | |
| `09-stripe-openapi` | 141% | 47 | |
| `03-natural-earth` | **226%** | 0 | 99,566 coordinate points |
| **`05-fhir-bundle`** | **60%** | 0 | short arrays — the cheapest of the four |

The document with neither cause is the cheapest, which is the controlled version
of a claim `VERDICT.md` states with one cause.

**And the instrument that beat the probe on `03` finds nothing here.** Counting
the level-columns a field's leaves fill found GeoJSON's Polygon/MultiPolygon
split exactly; FHIR's heterogeneity is in *which keys a record has*, not in
depth, so the same arithmetic returns 32 fields of ordinary nesting variation and
nothing about `value[x]`. **An instrument that finds polymorphism-by-depth is not
an instrument that finds polymorphism**, and this file is what keeps `03`'s
result from being over-read.

## Status

**The R half is complete** as of 2026-08-09: `purrr`, `jsonlite`, `tidyjson`,
`rrapply`, `jqr`, plus `tidyr`. The Python half is 8 attempts, unchanged. Under
`CLAUDE.md`'s definition this entry is done.

## Corrected 2026-08-13: 74 → 75 leaf names

**The grades above are left alone.** `paths(scalars)` drops every `false` and
`null` leaf — see `01-npm-registry`. The invisible name was
**`multipleBirthBoolean`**, which is a FHIR boolean and therefore `false` at
every site that carries it — the purest possible instance of the defect.

**THE FINDING IS UNCHANGED**, and Q11's URL search is exact either way: it
filters to strings, and a dropped `null` or `false` was never a candidate.
