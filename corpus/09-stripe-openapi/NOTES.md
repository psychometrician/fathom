# 09 — the Stripe OpenAPI specification

## The expectation, written 2026-08-09 before `source.json` was fetched

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   a316ac6880dccbe8c4bdbaf9cef8b52dfcc06a6f
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

**Disclosure.** One `HEAD` request, for `content-length`: **7,967,776 bytes**.
Nothing else has been seen. The predictions below come from knowing what OpenAPI
is, not from this file.

### Why this file

**Three repairs are sitting on `a316ac68…` with no held-out evidence** — array
element type, null-aware emptiness, names-are-keys — and `implementation.md`'s
gate counter is at zero. This document was chosen to strain all three and to fill
the axis that is still open.

**Polymorphism is the last unfilled axis and OpenAPI actually has it.**
`anyOf`/`oneOf` say a value is one of several shapes, by specification rather
than by accident. `05-fhir-bundle` was chosen for polymorphism and delivered
none: its three reported fields were artifacts of folding twenty resource kinds,
and `corpus/README.md` now records that a format strict enough to be worth
choosing engineers the polymorphism out. **OpenAPI is strict and keeps it,
because describing variation is what the format is for.**

**And it is keys-as-data at four levels, which nothing else here approaches.**
`paths` is keyed by URL, each path by HTTP verb, `responses` by status code, and
`components.schemas` by type name. `01-npm-registry` has 6 sites and is the
current maximum.

### What is predicted

**1. Keys-as-data is the highest in the corpus, and the HTTP verbs are reported
undecided.** More than 10 sites. But `get`/`post`/`delete` is a **closed
vocabulary**, and `classify()`'s known permanent limit is exactly that —
`dist-tags{latest, next}` and `data{text/html, text/plain}` are structurally
records and no structural signal can see them. Predicted: `paths` and
`components.schemas` called data, the verb objects called **undecided**.

**2. THE TWO OPERATIONS WILL CONFLICT, and this is the prediction worth having.**

> Operation 2 names keys that are data. Operation 4 partitions records on a
> discriminator, then folds. **The `RECORD SHAPES, FOLDED` loop skips any path
> `classify()` calls data** — so if `components.schemas` is called data, its
> values are never folded, and never partitioned, and the `type` field sitting
> inside every schema is never used.

Predicted: **0 splits on a document whose schemas are exactly the case operation
4 was built for.** If that holds, the two operations are in tension and neither
`VERDICT.md` nor `design/probe.py` says so anywhere.

**3. Genuine polymorphism, at last — and possibly reported as nothing.** `anyOf`
members are *array elements of different shapes*, which is what the repaired
`shape()` was written to see. Predicted: the polymorphism axis reads **> 0 and
not an artifact of folding**, the first time in the corpus. But if `anyOf` lives
under a path called data, nothing folds it and the count stays 0 — the same
conflict as prediction 2, arriving through a second door.

**4. `ALIGNED BY POSITION` stays silent.** No parallel arrays. False-positive
test for the newest feature, on its third held-out document.

**5. Recursion fires on the schema tree, correctly.** A schema has `properties`
whose values are schemas. The repaired detector wants the first field step to be
a key the ancestor carries, and `properties` is. Predicted: `RECURSIVE`, 3+
levels.

**6. Under 300 lines, and if it is over, the fold lost.** `01-npm-registry` gave
73 lines at 805 KB with 6 keys-as-data sites. This is **ten times the bytes** with
more keyed levels. Output proportional to structure predicts a few hundred lines;
output proportional to data predicts thousands.

**7. Memory under 800 MB.** The probe needed 968 MB for 50 MB of NDJSON, an 18.8×
multiplier, and 8 MB here should cost far less — but `25,043` distinct paths on a
805 KB npm file is the warning, and this document is keyed more deeply.

**8. `rows("components.schemas.*")` returns one row per schema**, with the key
column carrying the type name. That is `rows()`'s best case — npm's `versions.*`
with a different vocabulary — and is predicted to work.

---

## Provenance

| | |
|---|---|
| what | the Stripe API's OpenAPI 3 specification |
| source | `raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json`, see `fetch.sh` |
| fetched | 2026-08-09 |
| size | **7,967,776 bytes — not committed**, over the corpus threshold |
| licence | Stripe publishes it publicly; not redistributed here |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no integers past 2^53.
**4.75 s, 431 MB resident** — a 54× multiplier on a 7.6 MB file.

## The grades, measured 2026-08-09

| axis | measured | |
|---|---|---|
| bytes | 7,967,776 | |
| depth | **26** | **deepest in the corpus**, past `02-hn-thread`'s 25 |
| recursion | 5 | |
| distinct paths | **116,573** | **highest**, against npm's 25,043 |
| fields | 173 | |
| explosion | **673.8** | **highest**, against npm's 352.7 |
| keys-as-data | **47** | **highest by a factor of eight**, against npm's 6 |
| ragged by absence | 568/1092 | |
| ragged by null | 0 | |
| polymorphic | **8** | **the first genuine polymorphism in the corpus** |
| heterogeneous | 47 | |
| path variance | 76 | ties `04-gharchive` |
| row shapes | 21 | |

**It takes the top of five axes at once**, which no other file does.

> **Regraded 2026-08-12: row shapes is now 22.** The table records what was
> measured on the day and is left alone; other rows in it have also been
> overtaken by later repairs.
>
> **This file is the second document carrying defect 28**, which was filed
> against `10-wikidata` alone. It printed `an entry of <key> — 7 rows x 19 cols`,
> now `an entry of additionalProperties.*`, and one further site that the shared
> `<key>` name had been suppressing appears as `an item of items.* — 5 rows x
> 1 col`. **The proposing run looked at one document and the defect was on two**,
> which is the ordinary argument for asking every file the same question. See
> `FINDINGS.md`, 2026-08-12.

## Prediction scorecard: five of eight

| # | predicted | outcome |
|---|---|---|
| 1 | keys-as-data > 10, highest in corpus | **confirmed. 47** |
| 2 | **0 splits — the two operations conflict** | **WRONG. 5 splits, all on `type`** |
| 3 | genuine polymorphism, not an artifact | **confirmed. 8, and 6 are real** |
| 4 | `ALIGNED BY POSITION` stays silent | **WRONG, and it is a false positive — see below** |
| 5 | recursion fires on the schema tree | **confirmed. 8 sites** |
| 6 | under 300 lines | **WRONG. 943** |
| 7 | under 800 MB | **confirmed. 431 MB** |
| 8 | `rows()` one row per schema | **confirmed. 1,440 × 10**, key column carries the name |

## What the file established

### 1. `ALIGNED BY POSITION` false-positives on coincidence, and the repair is one day old

```
22 paths hold arrays of exactly 3 — same length everywhere, so probably one
table stored in columns
  …parameters[].schema.items.properties.tax_amounts.anyOf[].items.required
                                        amount, tax_rate, taxable_amount
  …additionalProperties.<key>.<key>.enum
                                        exclusive, inclusive, unspecified   <- the names
```

**These are unrelated `required` lists and `enum` lists that happen to hold three
elements.** They are not a table stored in columns and nothing relates them. The
probe then marked several `enum` arrays as *the names*.

The guard is `n >= 3` and *"at least two paths share this length"*. On a 7.6 MB
document with thousands of small arrays, **length 3 is a coincidence, not a
signal.** `06-espn-qbr` shares length 10 across 6 paths and `08-open-meteo`
shares 336 across 5; both are meaningful. 22 unrelated paths sharing 3 is not.

> **The feature has now been wrong on its first two held-out documents in two
> different ways** — a timestamp column announced as a header on file 08, and
> coincidental small arrays announced as a table here. `names_are_keys()`
> correctly stayed out of the way; the length threshold is what failed.
> **Recorded, not repaired.**

### 2. The two operations do not conflict, and my model of `classify()` was wrong

Prediction 2 said naming keys as data would stop the values ever being folded, so
the partition could never fire. **It fired five times, all on `type`.**

`classify()` returning "data" makes the probe fold the *keys* into `<key>` and
**still describe the values** — which is the correct behaviour and the opposite
of what the prediction assumed. The two operations compose.

```
SPLIT ON type — 4 kinds, not one shape. 66% empty folded, 11% worst split
SPLIT ON type — 3 kinds, not one shape. 62% empty folded,  0% worst split
```

**And this is the null-aware emptiness repair earning its keep on a held-out
file**: JSON Schema objects are ragged by absence, and the splits are priced
against the columns each group actually fills.

### 3. The first genuine polymorphism in the corpus

```
…properties.<key>.enum                array[1] text x1,021, array[1] boolean x24
…properties.<key>.additionalProperties object x100, boolean x4
```

Both are real: JSON Schema allows an enum of strings or of booleans, and
`additionalProperties` is either a schema or `true`/`false`. **Only two of the
eight carry the "not really" artifact label**, so six survive as genuine.

`05-fhir-bundle` was chosen for this axis and delivered nothing but artifacts.
**A format whose purpose is describing variation is the one that finally has it**,
which is the mirror of `corpus/README.md`'s note that a strict format engineers
polymorphism out.

**And the repaired `shape()` is what made it visible** — `array[1] text` against
`array[1] boolean` was one `array[1]` before 2026-08-09.

### 4. The fold lost, and 943 lines is the measurement

`01-npm-registry` gave **73 lines at 805 KB with 6 keys-as-data sites**. This gave
**943 lines at 7.6 MB with 47**. Ten times the bytes, eight times the keyed
levels, thirteen times the output.

> **Output tracked the number of keyed levels, not the structure.** The paths in
> the report run to 180 characters —
> `$.paths.<key>.<key>.requestBody.content.application/x-www-form-urlencoded.schema.properties.<key>.anyOf[].items.properties.<key>.properties…`
> — and a description whose *path prefixes* are that long is not proportional to
> anything a reader can hold.

This is the clearest case yet for a fifth operation or for a depth budget, and it
is not a defect in any single function.

### 5. `rows()` best case, working

```
rows('components.schemas.*')   1,440 rows x 10 cols
  schemas  'account'    <- the key column carries the schema name
```

Exactly npm's `versions.*` with a different vocabulary, and the one thing on this
file that came out clean.

## What it disconfirmed

**That keys-as-data and the partition are in tension.** They compose, and the
prediction that they would not was wrong for a reason worth keeping: `classify()`
folds keys and still describes values, which is a design decision nothing had
made explicit until a wrong prediction went looking for it.

## The R half completed, 2026-08-09 — and the corpus's core jq number is explained

`try-jsonlite.R` and `try-jqr.R` were added 2026-08-09, joining `purrr`,
`tidyjson`, `rrapply` and `tidyr`. **All five of `README.md`'s R tools are now
present**, so under `CLAUDE.md`'s definition this entry is done.

### jq returns 29 on the most keys-as-data-heavy file in the corpus

`VERDICT.md`'s central evidence for the O(data) claim is that
`[paths(scalars)|map(select(type=="string"))|last]|unique|length` answers
**3,100** on `01-npm-registry` where the truth is about 40 fields, and that
`rrapply` independently answers 3,112. This document has **47 keyed sites against
npm's 6** and 1,440 schemas, so it should be far larger.

```
distinct leaf names:                                    29
schema names ever appearing as the LAST path component:  0   of 1,440
```

**Zero.** Stripe's keyed objects hold OBJECTS, so a schema name is always in the
middle of a path and the leaf is an OpenAPI keyword — `type`, `description`,
`title`. There are only 29 of those. npm's inflation is the opposite case: its
keyed objects hold **scalars**, so `users` (2,648 usernames → booleans) and
`time` (320 version strings → timestamps) plus 40 real fields *are* the 3,100.

> **The expression is wrong high on one document and wrong low on another, for
> one reason.** npm's agreement with rrapply at 3,100/3,112 is a coincidence of
> that file's shape rather than confirmation of a mechanism.

**The claim survives on the honest measure.** Listing every leaf path costs
**11,162,821 chars for a 7,967,776-byte file — 140%** — against rrapply's melt at
**141%**. Two tools, two languages, both enumerating rather than summarising.

### jsonlite: the inert case, confirmed at ten times npm's size

`components$schemas` comes back as a **named list of 1,440**, not a table — the
same non-answer as npm's 288 versions, with eight times the keyed sites. **The
failure does not deepen with scale; only the consequence does.** The signal it
never volunteers: 1,440 children over **9 distinct keys and 7 key-sets**.

**Credit where it is owed:** jsonlite parses this 7.9 MB document in about a
second either way, where `tidyjson::json_schema` runs at a few KB/s elsewhere in
this corpus. Parsing is solved in R; describing is not.

### Four schemas are enough to make the always-present test return nothing

| key | on |
|---|---|
| `properties`, `type` | 1,436 of 1,440 |
| `title` | 1,421 |
| `description` | 1,418 |
| `x-expandableFields` | 1,417 |
| `anyOf`, `x-stripeBypassValidation` | **4** |

The four exceptions are `anyOf` schemas carrying none of the usual fields —
**four records of a different kind hiding among 1,436**. They are enough that no
field is present in *every* schema. **A rule requiring a field on every record is
one outlier away from silence**, which matters for the discriminator test in
`VERDICT.md`'s fourth operation, since that test begins by asking which fields
are present everywhere.

`str(max.level=2)` on this file is 118 lines, instant, and says almost nothing —
six top-level keys. There is no level that describes the document, because the
only describer is parameterised by DEPTH when what needs summarising is BREADTH.

## Corrected 2026-08-13: the leaf-name count holds at 29, the PATH count does not

**The grades above are left alone.** `paths(scalars)` drops every `false` and
`null` leaf — see `01-npm-registry`.

| | recorded | corrected |
|---|---|---|
| distinct leaf NAMES | **29** | **29** — unaffected |
| distinct folded PATHS | **64,264** | **65,425** |
| every-path character total | **11,162,821** | **11,325,092** |

> **This entry is why the 40 sites had to be read one at a time.** It is exactly
> right on one question and wrong by 1,161 on another, in the same file, from
> the same defect. Per-document exposure predicts neither.

**THE FINDING IS UNCHANGED.** 29 leaf names on the corpus's most
keys-as-data-heavy document is still the counterexample this entry exists to be:
Stripe's 1,440 schemas map names to OBJECTS, so no schema name reaches a leaf.
