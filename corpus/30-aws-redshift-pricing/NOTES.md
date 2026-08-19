# 30 — AWS Redshift, the public price list

## Provenance

**Fetched 2026-08-18** from
`pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRedshift/20260814134227/index.json`.
**4,027,133 bytes**, 8 top-level keys — `formatVersion`, `disclaimer`,
`offerCode`, `version`, `publicationDate`, `products`, `terms`,
`attributesList`. Offer version `20260814134227`, published
`2026-08-14T13:42:27Z`.

**COMMITTED**, at 4.0 MB, under the corpus threshold — and **this is the first
entry in the corpus whose fetch is exactly reproducible.** AWS publishes every
price list under a pinned version as well as under `current`, so `fetch.sh`
returns these bytes tomorrow. Every other entry that fetches a live endpoint
gets a later file and reproduces only the shape.

**This is the file every AWS cost tool reads.** Nobody chooses to open it.

## Why this file, and it is a TARGETED test of defect 36

**`corpus/README.md`'s "Wanted" list asks for exactly one shape and has asked
since 2026-08-14**: a second document where an outer container's keys are data
**and the inner containers' keys are data too**, with the inner ones holding few
enough keys — roughly **3 to 15** — that each looks like a record on its own
evidence. `29-mdn-browser-compat` is the only instance the corpus has, and one
document cannot justify the repair.

**The AWS price list format is that shape by construction, and I know it from
the format rather than from measuring this file.** AWS documents `terms` as

```
terms.<termType>.<sku>.<sku>.<offerTermCode>.priceDimensions.<sku>.<offerTermCode>.<rateCode>
```

— four levels of keys that are data, each nested directly inside the last, which
is entry 29's `api.<feature>.<subfeature>` mechanism with two more floors on top.

**Reserved pricing is why this service and not a cheaper one.** A Reserved SKU
carries one offer term per purchase option — 1-year and 3-year, crossed with No
/ Partial / All Upfront — so `terms.Reserved.<sku>` should hold **a handful** of
keys rather than the single key an On-Demand SKU has. That handful is the 3-to-15
band the specification asks for.

> **Selected by what the format is, not by measuring it. Rule 1.** Only the size,
> that it parses, the 8 top-level key names, and the two version fields were
> looked at before the predictions below were written and committed.

**It is a different domain from entry 29 on purpose.** A compat matrix and a
price list share no producer, no tooling and no conventions, so if the mechanism
shows up in both it is a property of the shape rather than of MDN.

**It is also a cold run for three repairs that have never met an unseen
document** — defects **34**, **33** and **26**, all marked *NO COLD RUN YET* in
`CLAUDE.md`'s hash table.

## Predictions, committed 2026-08-18 BEFORE the probe was run

**Scored after the run, unrepaired, per rule 5.** The probe is frozen at
`6dd6f45f…` and the hash was checked immediately before the run.

### The qualifying property — does this document earn defect 36 a second instance?

1. **`terms.Reserved` exists**, and is keyed by SKU. **RISK: if Redshift
   publishes exactly one reserved term per SKU, the inner containers hold one
   key, the 3-to-15 band is missed, and the specimen does not qualify.** This is
   the prediction most likely to be wrong and the whole entry turns on it.
2. **Each `terms.Reserved.<sku>` holds 4 to 12 keys.** Six is the natural
   number — two lease lengths times three upfront options.
3. **Every inner key is globally unique**, being `<sku>.<offerTermCode>`. So the
   union across SKUs equals the total count, and **100% of the folded paths
   cover a single value** — against entry 29's 79.8%. **This document should be
   a more extreme instance of defect 36 than the one that found it**, because
   MDN's subfeature names at least repeat across features and a SKU-term key
   repeats nowhere.
4. **`terms.OnDemand.<sku>` holds exactly 1 key** — the degenerate case, below
   the band, and present in the same document as the qualifying one.
5. **The fold therefore names thousands of paths where about four are right**
   (`terms.OnDemand.*.*`, `terms.Reserved.*.*`, and their `priceDimensions`).

### The three repairs that have never run cold

6. **Defect 34** — a candidate saying how many more items of its name live at
   other paths — **FIRES**. `priceDimensions`, `sku` and `attributes` all occur
   under more than one parent.
7. **Defect 33** — `FIELDS THAT CHANGE TYPE` capping at `SHOW` — **DOES NOT
   FIRE.** I predict fewer than 40 polymorphic fields, so the cap is not
   reached.
8. **Defect 26** — `ids, sources, types are lists packed into text` — **DOES NOT
   FIRE.** No sibling group here should share a wrapping character.

### Shape and health

9. **Health is clean**: one valid JSON document, not NDJSON, not truncated, no
   duplicate keys, no `NaN` or `Infinity`, **no integer past 2^53** and
   `encoded` 0. Prices are decimal **strings** — `"0.2500000000"` — which is the
   format's own defence against exactly the damage the health verb hunts.
10. **Polymorphism is near zero — 0 to 2 fields.** One machine producer, like
    `11-jupyter-notebook`, which measured 0. A price list is generated, not
    written.
11. **`products` folds correctly**: keyed by SKU, thousands of keys, values a
    uniform record of `sku` / `productFamily` / `attributes`.
12. **`attributesList` is the misclassification risk.** It is keyed by attribute
    name, a **closed schema vocabulary** of perhaps 20 to 40 names, sitting
    right on `KEYED_MIN` = 20. **I predict the probe folds it and is wrong to**,
    the same error `27-grafana-dashboard`'s root produced for defect 31.
13. **Depth 7 or 8.**
14. **No positional alignment.**
15. **The description ratio is poor — under 0.5%** — for the reason defect 36
    describes: the page is spent naming SKU-keyed paths.

### What would disconfirm the choice

**Prediction 1 failing makes this a file somebody downloaded.** If Reserved
terms are one-per-SKU, this document is another instance of the degenerate
1-key case and **not** a second instance of the 3-to-15 case defect 36 needs,
and it must be recorded as the fifth time the "Wanted" list was wrong about a
file in advance.

## Results — the cold run, 2026-08-18

**Run once, unmodified, against `6dd6f45f…`**, hash checked immediately before.
11.8 seconds. The report is **56 lines / 3,742 bytes**. **The Rust port agrees
byte-for-byte on a document it had never seen.**

**Thirteen of fifteen predictions confirmed. Of the two misses, one is mine and
one found a new defect.**

| | prediction | outcome |
|---|---|---|
| 1 | `terms.Reserved` exists, keyed by SKU | ✓ 301 SKUs |
| 2 | 4–12 keys per Reserved SKU, six natural | ✓ **min 4, median 6, max 6** |
| 3 | inner keys globally unique, 100% of paths cover one value | ✓ **1,728 of 1,728 distinct; 3,300 paths for 3,300 values** |
| 4 | `terms.OnDemand.<sku>` holds exactly 1 key | ✓ min 1, median 1, max 1 |
| 5 | thousands of paths where about four are right | ✓ **3,300 where 3 are right** |
| 6 | defect 34's modifier fires | ✗ **MISS — and it is the probe's. See defect 39** |
| 7 | defect 33's cap does not fire | ✓ no `FIELDS THAT CHANGE TYPE` section at all |
| 8 | defect 26's packed-list rule does not fire | ✓ silent |
| 9 | health clean, `encoded` 0 | ✓ `no duplicate keys · no NaN or Infinity · no ints past 2^53` |
| 10 | polymorphism 0–2 fields | ✓ **0** |
| 11 | `products` folds correctly | ✓ 1,571 copies · 3 fields · 1 key-set |
| 12 | `attributesList` folds and the probe is wrong to | ✗ **MISS, and it is MINE** — the key is an **empty object**, and the probe's silence is correct |
| 13 | depth 7 or 8 | ✓ **8** |
| 14 | no positional alignment | ✓ silent |
| 15 | description ratio under 0.5% | ✓ **0.0929%** |

### THE QUALIFYING PROPERTY HOLDS, and this document is more extreme than the one that found defect 36

**`corpus/README.md` asked for inner containers of roughly 3 to 15 keys. This
document's median is 6.** The specification is met on its own terms.

```
where date   3,300 paths   3,300 values     <- entry 30
where url   11,320 paths  35,392 values     <- entry 29, the defect's first document
```

**Every path here covers exactly one value — 100%, against entry 29's 79.8%.**
The paths are unfolded at the inner level and folded at the outer, which is
defect 36's mechanism seen twice:

```
terms.OnDemand.<key>.PUK8YEXSK6PKD9SV.JRTCKXETXF.effectiveDate
terms.OnDemand.<key>.KF7KUV5VCSN2M6FU.JRTCKXETXF.effectiveDate
              ^^^^^ folded                       ^ and 3,297 more
```

**Three paths are right** — `publicationDate`, `terms.OnDemand.<key>.<key>.effectiveDate`
and `terms.Reserved.<key>.<key>.effectiveDate`. The probe names 3,300, a ratio
of **1,100 to 1** against entry 29's 64 to 1.

**The consequence a reader meets is in the menu**, which prices tables one column
per unfolded key:

```
an entry of Reserved       301 rows x 28134 cols   100% empty
an entry of OnDemand     1,571 rows x 16214 cols   100% empty
an entry of Reserved.*   1,728 rows x 17772 cols   100% empty
```

**Defect 36 now has its second document, from a different domain and a different
producer, and it is the sharper of the two.**

### DEFECT 39, found here: defect 34 was repaired on one of the two loops

**Prediction 6 was wrong because the modifier could not fire — this document
offers no array candidates at all — and looking at why exposed the defect.**

`candidates()` runs two loops that both de-duplicate on the bare name and both
keep the FIRST path in sorted order, dropping the rest silently. **Defect 34 gave
the array loop a `more` modifier saying what it left out. The keyed loop
immediately above it never got one**, and the defect-34 comment sits between
them, describing only the loop below.

Entry 30's instance:

```
priceDimensions   KEPT     $.terms.OnDemand.<key>.<key>.priceDimensions   1,643
                  dropped  $.terms.Reserved.<key>.<key>.priceDimensions   2,862
```

The menu prints `an entry of priceDimensions — 1,643 rows`. **The document holds
4,505, and the dropped path is the bigger one** — which is defect 34's own worst
instance restated (`04-gharchive` printed `an item of labels — 5 rows` where the
document held 1,944).

**Measured corpus-wide, and it does not need a second document because it already
has five**: of **161** keyed candidate names, **50 hide a second path** and **38
of those drop the bigger one**, across **`09-stripe-openapi`, `20-homebrew-formulae`,
`28-home-assistant-i18n`, `29-mdn-browser-compat` and this file**. Defect 34's
own survey counted 159 self-nested names and 34 bigger-dropped — **all of them
arrays**. This is a separate population that was never counted.

> **A second facet, and it has ONE document, so it is recorded and not repaired.**
> The two loops share a single `seen` set, so a name the keyed loop claims makes
> the array loop skip that name entirely — no candidate, and no modifier either,
> because the modifier lives in the loop that never runs. **16 array candidates
> are suppressed this way on `29-mdn-browser-compat` and nowhere else.**

**Left unrepaired, per rule 5.**

## The fourteen tools, graded 2026-08-18

**All fourteen ran.** Six R, eight Python, one attempt file each, versions
printed at run time. Every count below agrees with the probe's.

**What this document does that the other twenty-nine do not: it puts the
separator inside the keys.** A reserved term is keyed `<SKU>.<OFFERTERMCODE>`
and a rate `<SKU>.<OFFERTERMCODE>.<RATECODE>` — **7,804 keys containing a dot**,
against 714 on `01-npm-registry` and 543 on entry 29. **Three of the fourteen
break on it, in three different ways:**

| tool | what a dotted key does |
|---|---|
| **glom** | **raises `PathAccessError`.** The escape is to abandon the path language for `T[...]`, which is Python subscripting |
| **jmespath** | **returns `None` unquoted**, resolves correctly when quoted. It is the only one with an escape inside the language |
| **pydash** | **returns `None`, silently** — the same value `get` returns for a genuinely missing field, so the failure is indistinguishable from absence. The quietest of the three, in the tool people reach for most |
| **ijson** | **answers depth 11 where the truth is 8**, because it counts separators in a prefix whose keys contain them |

**fathom does not break, and the reason is the fold rather than any care taken.**
The description names those levels `<key>`, so no literal dotted key reaches the
page. `find` output does embed them — see the defect below.

**Where the fourteen actually land on this file**, and it is the same shape as
every other entry: the extraction half is well served and the exploration half
is not.

- **Q6 — are any object keys data?** Four tools have a verb for it and none has
  an answer: `gather_object` (tidyjson), `json_each` (duckdb), `kvitems` (ijson),
  `to_entries` (jq). **All four must be AIMED.** On a document with five keyed
  levels, knowing where to point them is the whole question.
- **Q3 — what is one record?** **Fourteen of fourteen CANNOT.** No tool but
  fathom names a candidate or prices one.
- **The two that answer Q1 completely are unreadable.** duckdb's
  `json_structure` is **2,061,805 characters** on a 4 MB document; polars infers
  a struct of **1,571 fields** and will build the 1×1,571 table without
  complaint. Both are correct and neither can be read.
- **jq's path machinery buys nothing here**: **60,663 leaf paths collapse to
  60,663 shapes**, because `paths` collapses array indices and this document's
  repetition is entirely in its keys.
- **Q10 splits the tools cleanly and nobody gets it right.** The only arrays are
  4,505 `appliesTo`, **all empty**. pandas and polars **invent** a null row per
  empty array; rrapply, tidyr, tidyjson, duckdb and jq **drop** them. **ijson
  alone can tell an empty array from an absent one**, because `start_array` and
  `.item` are separate events. No tool says *there were 4,505 and all were
  empty*.
- **The key is repeated inside its own record** (`products.<SKU>.sku == <SKU>`),
  and two tools noticed: **tidyr ABORTS** on the name collision, **tidyjson warns
  and renames to `sku.2`**. Opposite policies, same document.

## DEFECT 40, found by the tool sweep and REAL but with NO corpus instance

**fathom joins path segments with `.` and does not escape keys that contain
one.** Demonstrated on a constructed document:

```json
{"a": {"b.c": {"x": 1}, "b": {"c": {"x": 2}}}}
```

```
RECORD SHAPES, FOLDED
  $.a.b.c   2 copies · 1 fields · 1 distinct key-set
```

**There are not 2 copies of one path. There are two different locations** —
`a["b.c"]` and `a["b"]["c"]` — **given one spelling and merged.**

**Measured across the corpus, and this is why it is recorded rather than
repaired:** five documents contain dotted keys — `01-npm-registry` 714,
`09-stripe-openapi` 72, `13-package-lock` 88, `29-mdn-browser-compat` 543 and
this file 7,804 — and **the number that actually collide is ZERO.** A dotted key
only misleads when both routes exist, and no real document here does that.

> **So this is the mirror of defects 24 and 36.** Those are defects with ONE
> document and no second. This is a defect **demonstrated exactly** and with
> **no document at all** — the corpus cannot justify repairing it, and cannot
> show it is safe either. **What it costs today is nothing. What it costs is a
> path printed by `find` that a reader cannot reliably type back**, on a
> document that has not arrived.

## What this file disconfirmed

**The `attributesList` prediction, and the miss is instructive.** I predicted the
probe would fold a closed schema vocabulary sitting near `KEYED_MIN` and be
wrong to. The key holds an **empty object** — so there was nothing to fold, and
the probe saying nothing is right. **The prediction was about a document I had
imagined rather than the one I had**, which is what rule 1 exists to expose.

**It also disconfirmed my reading of defect 34's repair.** I recorded it as *a
candidate says how many more items of its name live at other paths* and predicted
it would fire. It fires for `an item of` and never for `an entry of`, and no
document before this one made the difference visible — because the four corpus
files that already carry the defect all offer array candidates too, so the menu
never looked obviously incomplete.

**What it did NOT disconfirm: defect 32's rule held again.** A price list whose
`terms` nest four levels of data keys produced **zero** polymorphic fields and no
misclassification of the `products` record. The rule that survived entry 29
survived a document with a completely different producer.

