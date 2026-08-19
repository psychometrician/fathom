# 12 — an agent trace, scrubbed to structure

## The expectation, written 2026-08-09 before the probe was run

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   8123ba47bed34a8fa340ae31d07f787ef3d54e6b
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

**This file carries more than usual.** Two freezes happened on 2026-08-09 and
neither ran cold on anything: `a3ed7db9…` fixed file 11's three defects and broke
`02-hn-thread`, and `8123ba47…` fixed that and gained five more splits. **File 12
tests the `varies()` repair, the `encoded` rule, the null rule and the two-kind
guard at once**, which is the price of repairing a regression the same day.

### Disclosure, and it is larger than file 11's

*Of the specimen.* `scrub.py` prints the vocabulary it keeps, because a scrub
that cannot be audited is not a safeguard. **So the 45 kept string values have
been seen**, and they are the document's discriminators:

```
message assistant user system human  ·  tool_use tool_result text thinking
Bash Edit Write  ·  claude-opus-5 max not_available  ·  attachment
task_reminder file-history-delta queue-operation  ·  cli external standard
direct main mode normal create  ·  and 7 timestamps
```

**What has NOT been seen is the schema.** `scrub.py` walks *values*, never keys,
so no field name in this document has been read, and neither has the probe's
output, `axes.py`, or any record whole. Predictions below are made from the
vocabulary plus general knowledge of the transcript format — that it carries
`type`, `message`, `uuid`, `parentUuid`, `timestamp`, `sessionId` and similar —
and that prior knowledge is itself disclosed.

*Of the instrument.* None. Unlike file 11, no probe function was read to sharpen
these.

### The scrub, and what it costs

**The author chose "scrub the string values and keep the structure" on
2026-08-09**, closing a decision `VERDICT.md` had carried open for two working
days. The rule is structural rather than a list of blessed names:

> a string value is **vocabulary** if it is ≤ 32 characters and occurs ≥ 20
> times; everything else is **content** and becomes `x` of the same length.

That is open defect 13's test — a kind's values recur, an identifier's do not —
used as a scrubbing rule instead of a reporting one. Keys, nesting, array
lengths, types, string *lengths*, numbers, booleans and nulls all survive.

**Two costs, stated now rather than discovered later:**

1. **Question 0's `encoded` reading is destroyed by construction.** Any string
   holding an encoded JSON document is content by the rule above, so it is now
   `xxxx` and no longer parses. A reading of `encoded: 0` on this file is an
   artifact of the scrub and **must not be recorded as a measurement.**
2. **Question 11 cannot be asked** — finding every path whose value matches an
   email or a URL needs the values.

**One thing the rule kept that a reader should know about.** `"what's next?"`
occurs 28 times and is ≤ 32 characters, so it survived as vocabulary. It is a
user prompt, echoed once per turn by a reminder. It is innocuous, and it
demonstrates that the rule can retain short repeated user text. **Tightening it
— requiring no spaces, say — is a decision for the author**, and the audit print
exists so the question is answerable rather than assumed.

### Why this file

**It is the specimen `corpus/README.md` has wanted since the first day, and the
one that four other candidates failed to be.** `01-npm-registry` was chosen as a
polymorphism specimen and had none; `05-fhir-bundle` had it engineered out by
specification; `11-jupyter-notebook` had none because a notebook has **one
writer**. That last failure is what named the requirement:

> The gap does not need a permissive format. It needs a document **assembled
> from more than one producer.**

A transcript is written by a person, a model and a tool harness in turn, none of
them agreeing on anything, which is exactly that. It also fills **plain NDJSON**
— `04-gharchive` is gzipped, so the health verb has never met the bare case —
and it is the only document in the corpus **no API has normalised**, which
`corpus/README.md` argues is the corpus's systematic bias.

### What is predicted

**1. NDJSON, reported as a format and not as damage.** 1,953 records,
4,813,294 bytes. An NDJSON file is not valid JSON, and `README.md` says telling
*broken* from *a different format* is unavoidable. Predicted: format NDJSON,
1,953 records, no truncation claimed, and **no health-check noise at all** —
which `05-fhir-bundle` established as the standard after the gharchive repairs.

**2. Genuine polymorphism at the message content, and this is the point.** In
this format `content` is a bare **string** on user messages and an **array of
blocks** on assistant messages. Predicted: reported as a field changing type,
`text` against `array[...]`, and **not** carrying the *"not really: one type
within each kind"* label, because the disagreement is real.

> **If this fires, the corpus's oldest gap is filled and the fifth candidate is
> the one that worked.** If it does not, the scrub is the first suspect and the
> claim that structure survives it needs re-examining.

**3. `SPLIT ON type` at the top level, and it should be the largest partition
the corpus has seen after FHIR's twenty.** The vocabulary shows at least seven
record kinds — `assistant`, `user`, `system`, `attachment`, `task_reminder`,
`file-history-delta`, `queue-operation` — with genuinely different key-sets.
Predicted: fires, with a large drop.

**4. A second partition one level down, on the content block type.** `text`,
`thinking`, `tool_use` and `tool_result` have different key-sets. Predicted:
`SPLIT ON type` at the content array. **This is the two-kind guard's first
held-out test at a nested path**, and file 11 showed the probe can split a child
while refusing its parent.

**5. Ragged by absence, high; ragged by null, low.** Different record kinds carry
different keys, and a transcript omits rather than nulls. Predicted absence well
above null, the opposite of `07-graphql-introspection`.

**6. keys-as-data 0 or 1.** A transcript uses fixed field names. The one
candidate is a tool's `input`, whose keys differ per tool — `Bash` takes a
command, `Edit` takes three strings — which is a **discriminator on the
parent**, `04-gharchive`'s open case, arriving in a second document. **If that
is what it looks like, the fifth operation stops resting on one file.**

**7. Recursion 0, and for an interesting reason.** A transcript is a flat list;
its `parentUuid` chain threads the records into a tree **by reference, not by
nesting**. The corpus has never held that structure, and no axis grades it.
Predicted: recursion 0, correctly, and a property nothing measures.

**8. Under 200 lines of output on a 4.8 MB document**, and `rows("*")` returning
1,953 rows.

---

## Provenance

| | |
|---|---|
| what | a Claude Code transcript of this project's own sessions, scrubbed |
| source | `~/.claude/projects/…-fathom/873fefe5-….jsonl`, 4.6 MB, via `scrub.py` |
| scrubbed | 2026-08-09 |
| size | 4,813,294 bytes, **1,953 records**, committed |
| chosen from | 396 transcripts, by size; the largest under the 5 MB commit threshold that belonged to this project |

Valid NDJSON, whole, one pass. **1,953 of 1,953 records read**, and the health
line reads *"not one JSON document, and not broken"* — no noise at all.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 4,813,294 · **NDJSON** · depth **10** · paths 452 · fields 151 · explosion 3.0 |
| keys-as-data | **0 — and this is wrong, see defect 1 below** · ragged by absence **168/426** · ragged by null 4 |
| recursion | 0 · **polymorphic 4 — the highest in the corpus** · heterogeneous 1 · path variance 33 · row shapes 5 |

## Prediction scorecard: eight of eight

**The first file in the corpus to confirm every prediction**, which says more
about the predictions being made from a disclosed vocabulary than about the
probe.

| # | predicted | outcome |
|---|---|---|
| 1 | NDJSON reported as a format, no noise | **confirmed. 1,953 of 1,953, "not broken"** |
| 2 | genuine polymorphism at message content | **confirmed. `array[1] object x1,363, text x20`, no artifact label** |
| 3 | `SPLIT ON type`, largest after FHIR's 20 | **confirmed. 10 kinds, 69% → 6%** |
| 4 | a second split at the content array | **confirmed, and a third. 4 kinds 66% → 3%; attachment 7 kinds 83% → 0%** |
| 5 | absence high, null low | **confirmed. 168/426 against 4** |
| 6 | keys-as-data 0 or 1; tool `input` is a parent-discriminator | **confirmed both — and 6 is wrong for a reason worth more than the prediction** |
| 7 | recursion 0 | **confirmed** |
| 8 | under 200 lines | **confirmed. 140 — and 33 record shapes were dropped to get there** |

## What the file established

### 1. THE POLYMORPHISM GAP IS FILLED, on the fifth candidate

**`polymorphic 4`, the highest the corpus has recorded**, against Wikidata's 3
and Natural Earth's 1. The headline field:

```
$[].message.content        array[1] object x1,363, text x20
```

**A bare string on 20 messages and an array of blocks on 1,363**, and the probe
does *not* attach the *"not really: one type within each kind"* label to it — it
attaches that only to `attachment.content`, correctly. This is genuine.

`corpus/README.md` had wanted this since day one and four candidates had failed:
npm was chosen for it and had none; FHIR had it engineered out by specification;
`11-jupyter-notebook` had none because a notebook has **one writer**. That last
failure named the requirement — *a document assembled from more than one
producer* — and this is the first document that is one.

> **The gap was not closed by finding a more permissive format. It was closed by
> understanding why the other four failed**, which is the method working.

### 2. The discriminator-on-the-parent case now rests on three sites, not one

`VERDICT.md` had it down to **one document** and called that *"weaker evidence
for a fifth operation than yesterday's entry claimed."* This file holds two more:

```
$[].message.content[].input   458 copies · 15 fields · 10 distinct key-sets
  always     (none)
$[].toolUseResult             452 copies · 32 fields · 10 distinct key-sets
  always     (none)
```

**`always (none)` is `04-gharchive`'s exact signature** — measured, *zero* fields
present in every `input` — and the field that explains the shape is the sibling
`name`: `Bash` 265, `Edit` 130, `Write` 39. A `Bash` input has `command`, an
`Edit` input has `old_string`; nothing is common to both.

**Two documents, three sites, and one of them is the most ordinary object in
agentic JSON.** The fifth operation's case is now materially stronger than it was
this morning.

### 3. DEFECT — keys-as-data missed, and the miss truncated the report

`$[].snapshot.trackedFileBackups` is keyed by **file path**. Measured: 19 sites,
**50 distinct keys**, `.gitignore` among them, and **1 distinct key-set among the
values** — many children, all one shape, which is the textbook signature. The
probe graded the document `keys-as-data 0` and printed the keys as record shapes:

```
$[].snapshot.trackedFileBackups.corpus/02-hn-thread/python/try-jmespath.py   12 copies
$[].snapshot.trackedFileBackups.corpus/02-hn-thread/python/try-pydash.py     12 copies
… and 33 more record shapes
```

**The harm is concrete and it is not the wrong label.** Those phantom shapes
consumed the output budget, so the cap dropped **33 real record shapes** to stay
under 140 lines. **A keys-as-data miss did not merely mis-describe one site; it
pushed a third of the report off the end.** Operation 2 exists precisely to stop
this, and `01-npm-registry` is in the corpus because of it.

The per-site child counts are `0, 14, 47, 49, 50`, so some sites fall under
`KEYED_MIN = 20` and some sit well above it. Recorded, not diagnosed further,
and **not repaired** — rule 5.

### 4. DEFECT — the partition and the row pricing do not talk to each other

```
  SPLIT ON type — 10 kinds, not one shape. 69% empty folded, 6% after
  …
  ONE ROW COULD BE
    a record       1,953 rows x  319 cols   93% empty
```

**The probe knows the document is ten kinds and then offers a 319-column table
that is 93% empty as the row candidate, without mentioning it.** The two numbers
are computed by the same program from the same fold, twenty lines apart, and
nothing joins them — which is the shape of the `07-graphql-introspection` and
`10-wikidata` findings, where the evidence was on screen and unconnected.

The honest answer to *"what is one row"* here is **ten answers, one per kind**,
and the operation that would produce them has already run.

### 5. A structure the corpus has never held, and no axis grades

A transcript is a flat list whose records thread into a tree by **`parentUuid`
reference, not by nesting**. `02-hn-thread` is a tree because it nests;
this one is a tree and measures `recursion 0`, correctly, because there is no
self-similar nesting to find. **Nothing in `README.md`'s axis table describes
relation-by-reference**, and `QUESTIONS.md` question 7a asks about relation by
*position*, which is a different thing.

## What it disconfirmed

**That filling the polymorphism gap needed a permissive format.** Four candidates
were chosen for permissiveness and all four were regular. What produced
polymorphism was **multiple producers**, and the trace is polymorphic in a format
with no specification at all.

**And that a document nobody has curated is harder than one somebody has.** Every
prediction landed. The failures here are in the probe — a missed keyed site and
two numbers that do not speak — rather than in any exotic property of the file.


## The R half — predictions, written 2026-08-10 BEFORE the tools were run

**Committed as its own change, before any file exists in `r/`.** Rule 1.

**1. The discriminator method returns `[]` for `input`, and the FIX IS
DIFFERENT FROM `04-gharchive`'s — that is what this file is for.** On gharchive
the field explaining the payloads sits on the enclosing EVENT (`type`); section 2
above records that here it sits on a SIBLING (`name`: `Bash` 265, `Edit` 130,
`Write` 39). Predicted: `[keys present in every input]` is **empty**, and
partitioning by the sibling `name` cleans the fold the way `type` did there.

> **If both work, the fifth operation should not be called
> *discriminator-on-the-parent*.** It is *the discriminator is outside the
> record*, and parent and sibling are two cases of one thing. That is a
> correction to how `VERDICT.md` item 15 is worded, earned by a second document.

**2. `json_schema` drops the string form of `message.content`.** It is
`array[1] object ×1,363` against `text ×20`. On `10-wikidata` the object
absorbed the string in **both** input orders. Predicted: the same here, so the
20 string-valued messages are described as arrays — **third document for the
type-drop, and the first where the minority is 1.4% rather than 31%.**

**3. jsonlite's simplification PRESERVES rather than folds**, the
`03-natural-earth` outcome. `message.content` is genuinely two types, so
`stream_in` should leave a list-column rather than coercing. Predicted: a
list-column, and no warning that it means two shapes.

**4. jq's leaf-name count is NOT inflated by `trackedFileBackups`.** Defect 1
above records it as keys-as-data the probe missed — 50 distinct keys, file paths
— but section 14 of `VERDICT.md` records its values as **objects sharing one
key-set**. The scalar-vs-object rule says keys reach a leaf only when their
values are scalars. Predicted: the file paths never appear as leaf names, so the
count stays near the 151 true fields. **Sixth document for that rule.**

**5. Melt comes in LOW — under 100%.** The corrected statistic tracks path length
against value size, and this document's values are long: prose, code, and
scrubbed content that keeps its original length. Predicted: nearer
`04-gharchive`'s 52% than `08-open-meteo`'s 356%.

**A prediction that would hurt.** If partitioning `input` by the sibling `name`
does NOT clean the fold, then this file is not a second instance of gharchive's
case and `VERDICT.md` item 15 still rests on one document.

## The R half, run 2026-08-10 — five of five, and item 15 needs rewording

**All five R tools run.** Predictions were committed in `098dfb7`, before any
file in `r/` existed. **This entry still has no Python attempts**, so it does not
yet meet `CLAUDE.md`'s definition of done.

| # | predicted | outcome |
|---|---|---|
| 1 | `input` has no always-field; the **sibling** cleans the fold | **confirmed, both halves** |
| 2 | `json_schema` drops the string `content` | **confirmed, both orders** |
| 3 | jsonlite **preserves** rather than folds | **confirmed** — a list-column |
| 4 | jq's leaf count **not** inflated by file-path keys | **confirmed. 113 vs 151 fields** |
| 5 | melt **under 100%** | **confirmed. 40% — the corpus low** |

### 1. The fifth operation is not about parents — it is about being outside the record

Section 2 above put the discriminator-on-the-parent case at three sites. Measured
three independent ways — jq over the whole file, purrr over the parsed list,
rrapply over a melted frame, **all agreeing**:

```
458 tool-use blocks carry an `input`, 15 fields in the union
fields present in EVERY input:  NOTHING

folded on input alone        19% filled  ->  81% EMPTY
partitioned on sibling name  Edit 100%, Write 100%, Bash 86%
```

**And 14 of the 15 input fields belong to exactly one tool name** — `command`
is Bash's, `old_string` and `new_string` are Edit's, `content` is Write's.

> **`VERDICT.md` item 15 is worded *discriminator-on-the-parent*, and that is too
> narrow.** On `04-gharchive` the field sits on the enclosing EVENT; here it is
> `name`, a **sibling key of the same object** as `input`. Both are **outside the
> record being folded**, and no test over the records reaches either. **The
> operation is `the discriminator is outside the record`, with parent and sibling
> as two cases of one thing.**

Across five documents the relationship now reads:

| file | discriminator | where it sits |
|---|---|---|
| `05-fhir-bundle` | `resourceType` | **inside** the record |
| `07-graphql` | `kind` | **inside** the record |
| `10-wikidata` | `snaktype` | **inside** the record |
| `04-gharchive` | `type` | on the **parent** |
| **`12-agent-trace`** | **`name`** | a **sibling** |

**The scrub supports the reading rather than undermining it.** Two groups are
`xxxx` (12) and `xxxxxxxx` (10) — tool names below the scrub's 20-occurrence
vocabulary threshold — and they partition as cleanly as `Bash` and `Edit`. The
split is structural, not a reading of the words.

### 2. The type-drop's third document, and the hardest to catch

`message.content` is `array ×1,363` against `string ×20`. `json_schema` reports
the **array form in both input orders** and the twenty strings vanish —
absorption, as on `10-wikidata`, not order-dependence as on `03-natural-earth`.

**What is new is the dose.** On wikidata the discarded minority was **31%** of
records. Here it is **1.4%** — twenty of 1,383. *A description that is wrong
about one record in seventy reads as a description that is right.* This entry
grades the file **polymorphic 4, the highest in the corpus**, and the schema
reports none of it.

On the whole file `json_schema` does not return at all — the second NDJSON
document after `04-gharchive` where it is scored **CANNOT** rather than WRONG.

### 3. jsonlite preserved, and neither tool can tell you

`stream_in` leaves `content` as a list-column holding `data.frame ×1,363,
character ×20, NULL ×570` — the `03-natural-earth` outcome, where the same rule
kept a polymorphism polars had erased.

**And nothing says so.** A list-column is what a nested single-shape column looks
like *and* what a two-shape column looks like. So of the two tools, **the one
that preserved the fact cannot report it, and the one that would have reported it
got it wrong.**

Six documents, one rule, four behaviours, no signal which fired: SAFE here and on
`03`, WRONG on `05`, INERT on `01`/`09`/`10`, MISLEADING on `02`.

### 4. The scalar-vs-object rule holds on a sixth document

Defect 1 above records `trackedFileBackups` as keys-as-data the probe missed —
50 distinct keys, file paths. Its values are **objects**, so those keys never
reach a leaf and jq's count is **113 against 151 true fields** — under, not
inflated.

| `01` 3,100 vs ~40 | `03` 63 vs 63 | `04` 254 vs 235 | `09` 29 vs 1,440+ | `10` 34 vs 48 | `12` 113 vs 151 |
|---|---|---|---|---|---|
| OVER, keys→scalars | RIGHT, flat | OVER 8%, keys→scalars | UNDER, keys→objects | UNDER, keys→objects | UNDER, keys→objects |

**Six documents, one rule, no exceptions.** The melted frame shows the same
thing without reporting it: 2,252 rows sit under `trackedFileBackups` with a
file path in the path column, as though it were a field name.

### 5. Melt is 40% — the corpus low, on the most polymorphic document

| **`12` 40%** | `04` 52% | `05` 60% | `06` 140% | `09` 141% | `10` 173% | `07` 204% | `03` 226% | `08` 356% |
|---|---|---|---|---|---|---|---|---|

**Average value 76.9 bytes under an average path of 30.5 characters** — prose,
code and scrubbed content that keeps its original length. **Eight documents, and
the table is ordered by value length**: not by raggedness (the raggedest file is
the cheapest), not by keyed sites, not by depth, not by polymorphism.

## Status

**R half complete 2026-08-10** — purrr, jsonlite, tidyjson, rrapply, jqr. **No
Python attempts and no tidyr attempt**, so this entry is NOT done under
`CLAUDE.md`'s definition. It is the first entry outside `01`–`10` with any tool
attempts at all.

## The fourteenth tool, 2026-08-11 — `try-tidyr.R`

**This entry is the sharpest case in the corpus for what `unnest_auto`'s rule is
worth.** Ten record kinds, **seventeen distinct key-sets**, and the intersection
across all 1,953 records is **exactly one key: `type`**. It reports *"elements
have 1 names in common"* and widens to **1,953 x 40, of which 31.4% is filled**;
18 of the 40 columns are filled on under 5% of rows.

> **The field whose entire job is to say these records are not one kind is the
> whole of the evidence for treating them as one.** Entry 24 found the rule
> ignores the vocabulary; this document shows it can read the strongest
> available evidence AGAINST widening as the reason to widen.

**And question 5 is answered better here than by any other tool of the
fourteen.** `unnest_longer(toolUseResult)` refuses and names both records and
both types:

```
Can't combine `..1$toolUseResult` <list> and `..426$toolUseResult` <character>.
```

Not a tally of polymorphic fields — **which two records, and what each one is.**

| | |
|---|---|
| question 0 | CANNOT, and NDJSON had to be recognised by a human before `readLines` was reached for |
| question 3 | attempts it, WRONGLY, and states its reason |
| question 5 | **YES, with row numbers** |
| question 10 | `unnest_longer(message)` → 10,006 rows: the verb counts FIELDS on an object and ELEMENTS on an array, and the call does not say which |

## Corrected 2026-08-13: 113 → 123 leaf names, 349 → 360 path shapes

**The grades above are left alone.** `paths(scalars)` drops every `false` and
`null` leaf — see `01-npm-registry`.

| | recorded | corrected |
|---|---|---|
| distinct leaf names | **113** | **123** |
| folded path shapes | **349** | **360** |
| every-leaf character total | **1,765,733** | **1,911,501** |

The ten invisible names include `diagnostics`, `interrupted`, `isImage` and
`isSidechain` — booleans and nulls, which is the defect exactly.

**THE FINDING IS UNCHANGED**: 123 against 151 true fields is still UNDER, still
because `trackedFileBackups`' 50 file-path keys hold objects.

> **THIS FILE ALREADY KNEW.** Its `try-jq.py` records *"`paths(scalars)` cannot
> see a null — `select(null)` is false in jq"* and correctly uses plain `paths`
> for Q5 to work around it — **and still used the broken expression for three
> other questions in the same file, all three of which measured wrong.** A
> defect named in a comment is not a defect repaired.

> **The cross-entry table above carries five other corrected numbers.**
> `01` 3,100 → 3,104 · `03` 63 → **64** · `04` 254 → 272 · `10` 34 → 35.
> **`03`'s "RIGHT, flat" verdict is WITHDRAWN**: its match was two cancelling
> errors, and the expression is right on no document in the corpus.
