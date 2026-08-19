# The first vocabulary, derived and then attacked

**Written 2026-08-09.** `VERDICT.md` names three things that would earn phase 2,
and this is the one never attempted: *a proposed vocabulary that survives the
deletion test at under a dozen words.* Until now there was no word list to run the
test against.

**Nothing here is invented.** `README.md`'s rule is that a word is admitted only
by naming the question it answers and the file that proves it, so the method is to
walk `QUESTIONS.md`, ask what operation each question needs, and keep only what
survives deletion. **A proposal, untested by use.** Writing a sentence is not
running it.

---

## The derivation

**Questions 0 to 7 are one word.** Health, structure, depth, the record, the
always-and-sometimes, the type changes, the data keys, the count — every one is
answered by the same single report, which is the decision recorded on 2026-08-08
and which `design/probe.py` implements.

| question | operation |
|---|---|
| 8 — three named fields, one row per record | say what a row is, then name fields |
| 9 — a field missing from some records | a default; **and**, where the value moved, a priority order |
| 10 — flatten the deepest array | say what a row is, at a finer unit |
| 11 — every path whose value matches something | search by predicate |
| 12 — the flattest honest table, and what was lost | say what a row is, at the finest unit; the loss is question 3's pricing |

Which yields five candidates:

```
fathom(x)                    see it: sound, shaped, and what a row could be
rows(x, <unit>)              state what one row is
take(<fields>)               pull named things out
first_present(a, b, …)       the first of these that is actually there
where(x, <predicate>)        every path whose value matches
```

## The sentences, against all four corpus files

```
fathom("express.json")
rows("versions.*") |> take(version, author.name, dist.tarball)     # 288 x 3
rows("versions.*.dependencies.*")                                  # 4,645 edges
take(first_present(versions.*.author.name, author.name))           # path variance, 18 sites
where(is_url)                                                      # every tarball, repo, homepage

fathom("hn-thread.json")
rows("**")                    |> take(author, text, points)        # 336, at any depth
rows("children.*")            |> take(author)                      #  25, top level only

fathom("countries.geojson")
rows("features.*")            |> take(properties.name, geometry.type)   # 241 x 2

fathom("gharchive.json.gz")
rows("*")                     |> take(type, actor.login, repo.name)     # 37,883 x 3
```

**`rows()` is the hypothesis made into a word.** `README.md` says every existing
tool makes you state paths and lets the row shape fall out as a side effect, and
that this is backwards. `rows("versions.*")` states the row and lets the paths
follow. It is the one word the whole project argues for.

## The deletion test, run

> A word belongs only if removing it makes one of the fixed questions unanswerable
> on at least one corpus file.

| word | remove it and… | verdict |
|---|---|---|
| `fathom` | questions 0–7 are unanswerable on all four files | **keeps** |
| `rows` | 8, 10 and 12 unanswerable; the unit cannot be stated at all | **keeps** |
| `take` | see below — it survives on cost, not on possibility | **keeps, narrowly** |
| `first_present` | question 9 is still answerable; **path variance is not** | **keeps, on different grounds than expected** |
| `where` | question 11 unanswerable on every file | **keeps** |

**`take` nearly failed, and the argument that saves it is the author's own.** If
`rows()` returns every column, then selecting three of them is god's `pick`, and
`take` is a word fathom does not need — the seam is a data frame and selection
lives downstream. What saves it is cost: `rows("versions.*")` alone is **288 × 140
and 60% empty**. Materialising 140 columns to keep 3 is exactly the waste behind
*"it is not even efficient to make every json rectangularized"*. `take` is how you
never build the other 137.

**`first_present` is kept for a reason the question did not name.** Question 9 asks
for a field missing from some records, and a default argument answers that without
a word. What has no other answer is **path variance** — `author` at the top level
*and* inside every version, 18 sites on `01-npm-registry` and 76 on
`04-gharchive`. That is the priority-order case, and it is the word already shared
with god.

## The scope floor, applied

> A word that touches the **data** earns its place by working at more than one
> depth. A word that touches the **medium** earns its place by having no analogue
> at depth one.

| word | depth 1 (data frame) | depth 2 (list-column) | depth N | |
|---|---|---|---|---|
| `take` | select columns | pluck through a list-column | reach into a document | **passes** |
| `first_present` | `coalesce` — god has it | across list-columns | across paths | **passes** |
| `where` | which columns match | which elements match | which paths match | **passes** |
| `rows` | **a data frame already has rows** | unnest a list-column | name the unit | **passes narrowly** |
| `fathom` | `glimpse()` | glimpse with the column unfolded | the probe | **passes** |

**`rows` is the weakest on the floor and it is the most important word.** At depth
one it is a no-op, because a data frame has already answered the question `rows()`
exists to ask. That is not a defect — it is the project's thesis restated: **the
word is vacuous at depth one precisely because depth one is the case where
somebody already did this work for you.**

**`fathom` passes the data clause, which was not expected.** The earlier reasoning
filed it as a medium word justified by the absence of broken data frames. Only its
*health* half is medium-only; its structure half is `glimpse()`, which exists at
depth one and is the thing this whole project is trying to reach at depth N.

## Five words, and what they are not

**Under a dozen, and the test terminated.** Five words answer nineteen questions
across four documents. For comparison, purrr exports about 180 — the difference is
not restraint, it is that purrr answers questions nobody in this corpus asked.

**Two open questions, deliberately not settled.**

**Are `where` and `take` one word?** `take(x, dist.tarball)` selects by path and
`where(x, is_url)` selects by predicate. That is arguably one verb with two
argument styles, which would make it four words. Against: `where` answers *which
paths*, `take` answers *what values*, and they return different shapes. Undecided,
and worth deciding before anything is built.

**~~What is `rows()`'s path language?~~ Specified and running, 2026-08-09.** See
`design/rows.py`; the notation is at the top of it and every row count below was
produced by it, matching the probe's independently.

```
.          the document, one row          name**   follow `name` repeatedly
name       the field called `name`        **       every descendant (a firehose)
"1.0.0"    a key that needs quoting       *        every child, object or array alike
```

| document | sentence | result | |
|---|---|---|---|
| `01-npm-registry` | `rows(doc, "versions.*")` | 288 × 41 | keys become the `versions` column |
| `01-npm-registry` | `rows(doc, "versions.*.dependencies.*")` | **4,645 × 3** | version, package, range |
| `02-hn-thread` | `rows(doc, "children.*")` | 25 | top-level comments |
| `02-hn-thread` | `rows(doc, "children**")` | **335** | the whole thread |
| `03-natural-earth` | `rows(doc, "features.*")` | 241 | one row per feature |
| `04-gharchive` | `rows(doc, "*")` | 37,883 | gzipped NDJSON, read directly |
| `04-gharchive` | `rows(doc, "*.payload.pull_request")` | **3,791** | across three event types |

**The last one is the hypothesis working.** 3,791 is not any event type's count —
it is `PullRequestEvent` 2,571 plus `PullRequestReviewEvent` 634 plus
`PullRequestReviewCommentEvent` 586. Asking for the field found every record
carrying it, without naming where it lives or what `type` those records are.

## `first_present` executed, 2026-08-09 — the second word to run

`design/first_present.py`. It imports `rows.py` unmodified, so **`rows.py` stays
frozen at `109cf022…` with its fifteen cold runs intact** — adding a word is not
a repair.

**Two corpus files demanded it, from unrelated causes**, and both are now
measured:

| document | the spellings | result |
|---|---|---|
| `16-movie-ratings` | `Rating` / `rating` | **38 of 38 rows, 100%** — 15 and 23 |
| `05-fhir-bundle`, component level | `valueQuantity` / `valueCodeableConcept` / `valueString` | **119 of 119, 100%** — 24, 90, 5 |
| `05-fhir-bundle`, resource level | eight `value[x]` spellings | 119 of 564 — **correct**, only Observations carry one |

**The component case is the argument in one line.** Without the word you build
three columns that are 20%, 76% and 4% full and then merge them by hand; with it
you build one column that is 100% full. The FHIR specification and a Kaggle
scraper produced the same problem for entirely different reasons — a spec that
enumerates every variant as its own field name, and two websites merged by a
script that did not agree on capitalisation.

### The scope floor, run rather than argued

`QUESTIONS.md` questions 17 and 18 are Phase 4 — *does one vocabulary answer the
same question at depth one, two and N?* — and **no word had ever been tested
against them.** `first_present` is the first:

```
depth 1, a data frame row      first_present(r, "Rating", "rating")        -> 'R'
depth 2, with a list-column    first_present(r, "meta.*.Rating", …)        -> 'R'
depth N, the document          first_present(doc, '*."12 Strong".Rating')  -> 'R'
```

**One spelling of the word answered all three.** Question 17: *yes, and the
difference is only which path you hand it.*

**And the naming argument survived execution.** `README.md` says `present` means
*the only value skipped is a missing one, so a zero comes back*:

```
first_present({'n': 0}, 'n', default='-')            -> 0      not '-'
first_present({'Rating': None, 'rating': 'G'}, …)    -> 'G'    null is skipped
```

**It does not skip sentinels.** `16-movie-ratings` writes missingness as the
string `"unknown"` and the word returns it, because the policy is *report, never
repair* — the probe reports the sentinel and stepping over it here would destroy
the evidence.

### What it did NOT do

**It does not close open defect 3.** That defect is that `rows()` cannot ask for
the field rather than the spelling, and `rows()`'s `take=` is a name filter that
cannot express a priority order. Wiring the two together is a separate change
needing its own evidence, and doing it here would have meant unfreezing `rows.py`
to ship an unproven word.

## `take` executed, 2026-08-09 — and its cost claim is confirmed

`design/take.py`. **`take` is the only word that failed the deletion test on
possibility and survives on cost alone**, and `VERDICT.md` recorded that the cost
claim was untested. Measured on `01-npm-registry`'s 288 versions:

```
every top-level key      288 x   40 cols   43% empty     11,520 cells
json_normalize           288 x  140 cols   60% empty     40,320 cells
with take                288 x    3 cols                     864 cells

97.9% of json_normalize's cells never built
```

**The 288 x 140 and 60% this document already quoted are `pandas.json_normalize`,
and it never said so** — the same records are 288 x 40 and 43% empty at the
top-level reading. Both are honest and the flattened one is the right one to
cite, because `json_normalize` is what somebody reaching for *"just make it a
table"* actually types. `take.py` now prints both.

**What the measurement does NOT show is a speed win.** `take` took 0.9 ms where
widening took under one; at 288 records the traversal dominates and the saving is
in cells rather than seconds. The claim was always about what gets *built*, and
that is what 864 against 40,320 says.

**It selects by PATH, which is the difference from `rows(take=)`** — that
parameter is a name filter (`if take is None or k in take`), so it can keep
`version` and cannot reach `author.name`.

## `where` executed, 2026-08-09 — and it folds, or it would be the failure it names

`design/where.py`, answering question 11. On `01-npm-registry`:

```
where(url)                                    where(email)
  versions.<key>.<key>.url        325           versions.<key>.contributors.[].email  185
  versions.<key>.<key>.tarball    240           versions.<key>.author.email            48
  versions.<key>.dist.tarball      48           …
  bugs.url · homepage · repository.url          3,389 values at 11 shapes
  806 values matched, at 7 path shapes
```

**Printing 806 matching paths would be the O(data) failure committed by fathom's
own word**, so `where` folds the paths the way the probe folds record shapes: 806
values, **7 shapes**.

**A wrong turn worth recording.** The fold asks *are this container's keys data*,
and the obvious improvement was to hand `probe.classify()` the container's values
as siblings rather than the container itself. **Measured, that takes npm's URL
report from 7 shapes to 659**, printing version numbers literally — because
`versions`' 288 children are records that share their keys, so the sibling test
calls them *structural*. **`classify` asks whether sibling copies share keys;
this walk asks whether a container's keys are data. Different questions, and only
the single-copy branch answers the second.** The cost is that a 40-field record is
called data too, so `versions.<key>.<key>.url` over-folds by one level.

## The words in R, 2026-08-09 — and the premise passes its first test

`design/fathom.R` re-implements the path language, `rows`, `first_present` and
`take`. `design/parity.py` runs both sides on the same sentences:

```
  parity: 11 sentences, two independent implementations

    01-npm-registry      versions.*                 py    288  R     288  keys 1.0.0
    01-npm-registry      versions.*.dependencies.*  py  4,645  R   4,645  keys 1.0.0|connect
    02-hn-thread         children**                 py    335  R     335
    05-fhir-bundle       entry.*.resource           py    564  R     564
    16-movie-ratings     *.*                        py     38  R      38  keys 0|12 Strong
    19-chicago-salaries  *                          py  5,000  R   5,000
    …
  11 of 11 agree
```

**It is a re-implementation, not a binding, and that is the whole point.**
`design/implementation.md` proposes a Rust core with thin bindings, which would
make the two languages agree *by construction* and prove nothing about the
vocabulary. `fathom.R` was written from the same written notation, so agreement
here is agreement about **what the words mean**.

**It compares captured keys, not only counts.** Counts alone are weak — two
implementations can agree on how many things they found and disagree about
which. The keys are what `rows()` turns into columns.

`README.md` warns that a word shared with god needs *"a test on both sides from
the day it is shared, or the two will drift and the drift will be invisible."*
There was no such harness for fathom's own two sides either. Now there is.

### Two harness bugs, both found by the harness tightening

Worth recording because both looked like language disagreements and neither was.
**Sourcing `fathom.R` ran its own CLI block**, so jsonlite tried to parse the R
source as JSON — eleven identical failures that were the driver, not the words.
And **a captured key can contain a space**: `16-movie-ratings` is keyed by film
title, so `"12 Strong"` was truncated to `12` and reported as a mismatch.

## What this does not establish

**`fathom` as a word has still not run**, existing only as `design/probe.py`,
which is a 600-line prototype rather than a verb anybody calls. **`where` has no
R implementation** — three of the four words are on both sides, not four.

**And parity is eleven sentences, not a corpus.** god has a parity corpus that
diffs the same sentence in both bindings; this is a start of one. The obvious
next cases are the ones with no R answer yet: `where`, and `take`'s column
values rather than its row counts.

---

## The readback problem, and why five words is not yet enough — 2026-08-11

**Recorded from the author's statement of the goal, which is narrower and more
demanding than the retention bar in `README.md`:**

> Most JSON packages have functions that are not easy to understand without using
> them regularly. Even if you used one for a couple of months and developed long
> code that successfully parsed a complicated file — **a week later you look at
> your own code and it is nonsense.**
>
> **With dplyr and tidyr and the pipe, months later you can still understand what
> you were trying to do. That is the goal for fathom.**

**This is not the same bar as *still have it after a year*.** That one is about
remembering the TOOL. This is about reading YOUR OWN WORKING CODE — and it is
worse, because you can remember the API perfectly and still not understand what
you wrote. `QUESTIONS.md` question 15 asks the weaker version, *can you read it
back without going to the reference*, and **211 of the 350 attempt files answer
it while `FINDINGS.md` and `VERDICT.md` mention it zero times.** The evidence
exists and has never been synthesised.

### Why dplyr reads back, and it is three things rather than one

**The small vocabulary is the least of them.** Eleven verbs is necessary and
nowhere near sufficient.

| | |
|---|---|
| **closure** | every verb takes a data frame and returns a data frame, so a chain can be ANY LENGTH |
| **no embedded language** | `filter(x, y > 3)` is plain R. There is no notation to decode inside a string |
| **small steps** | one verb does one thing, so **each line is readable alone** and the chain is readable as a sentence |

### fathom, measured against those three, has one of them

**The sentences above are at most TWO steps** — `rows(...) |> take(...)` — and
then the type is a data frame and you have left fathom for dplyr. So:

| | |
|---|---|
| closure | **NO.** `fathom()` returns a report, `rows()` a table, `take()` "any shape — a value, a vector, a list", and `README.md` calls non-rectangular extracts **terminal**. There is no type the verbs share |
| no embedded language | **NO.** `*`, `**`, `name**`, quoted keys — a second language inside a string argument. `rows("versions.*.dependencies.*")` is exactly the `pluck(x, "a", "b", 3)` disease: **the structure is in the argument rather than on the page** |
| small steps | **NO.** One `rows()` call does multi-level navigation AND unit selection at once, because it has to — there is nowhere to put the intermediate step |

> **So fathom has the PIPE without the CLOSURE, and the pipe is the part that
> does not matter on its own.** A two-step chain does not read back better than a
> one-step call; it is the same amount of decoding either way.

### What the author's own words point at, and it is a type rather than a word

**"Zoom out for the whole shape, zoom in for one buried value, at any level"** is
a description of **closure**. It needs a thing to zoom, and that thing is a
**VIEW**: a document plus where you are currently looking.

```
doc |> fathom()            # a view of the whole
    |> into(payload)       # zoom in one level
    |> into(pull_request)  # again
    |> fathom()            # look at where I am NOW
    |> rows()              # leave, deliberately, as a table
```

**Every line is short, every argument is plain, nothing is encoded in a string,
the chain is any length, and `fathom()` can be re-run at any point** — which is
the thing no existing tool offers and the reason the probe is worth having in
the first place. *Fathom first, then parse* becomes *fathom, move, fathom
again.*

### What this costs, stated honestly

- **`rows()`'s path language is the thing at risk.** It is specified, running,
  and produced every row count in this file — and it is **also** the single
  biggest readback liability. Those are both true and the second was never
  weighed.
- **It is more words, not fewer.** A zoom verb is a sixth, and `README.md`'s
  floor demands each word make a fixed question unanswerable. **`into` would fail
  that test**, because every question is already answerable without it. The floor
  measures POSSIBILITY and the author's goal is READABILITY, **and the floor
  cannot see the difference.**
- **That is the decision.** Either the floor gains a second clause about reading
  code back, or the goal stated above cannot be designed for.

## Two constraints on the words, from the author 2026-08-11

**1. Plain English that applies naturally to JSON, and NOT super-technical
terms.** A word somebody would say out loud about a document. **Compounds are
allowed**: where one word is not descriptive enough, `word1_word2` is fine —
`first_present` is the model, since `first` says the arguments are a priority
order rather than a set and `present` says the only value skipped is a missing
one. Two words that each do work beat one word that is nearly right.

**2. DISTINCT from god's vocabulary.** `README.md` owns the reasoning: the two
packages are loaded together so a shared name masks one of them, and fathom
moves around a DOCUMENT while god manipulates a TABLE — different things,
different words. **Disjoint vocabularies make the seam visible in the code**,
which serves the readback goal above rather than costing anything.

### What this does to the five

| | |
|---|---|
| `fathom` | **safe.** Plain English, both senses, and it is the package name |
| `take` | **plain English, but check god.** If god has or wants `take`, it collides |
| `rows` | **plain English, and it presumes the answer is a table** before the user has said so. Worth re-examining against the zoom model above |
| `where` | **plain English, but it is dplyr's and SQL's**, and it names a filter rather than a search. It answers *which paths match*, which is nearer `find` |
| `first_present` | **FAILS ON THE COLLISION ALONE.** God-shared by design, and god has `coalesce`. Its FORM is fine — it is the model compound. The BEHAVIOUR is proven and survives a rename; the name does not |

### The pipe is SHARED, and that is the other half of the decision

**god uses `|>` in R and `>>` in Python. fathom uses the same two.** So a whole
workflow is one continuous sentence:

```r
doc |> <fathom verbs …> |> <god verbs …>
```

> **Shared pipe, distinct verbs, and the two decisions work together.** The pipe
> makes it read as ONE sentence rather than two scripts glued together. The
> disjoint vocabulary makes the SEAM VISIBLE inside that sentence — the moment
> the words change, you have crossed from a document into a table. **A reader
> months later gets both the continuity and the boundary for free, from the code
> itself.** That is the readback goal, served by punctuation and word choice
> rather than by comments.

> **The vocabulary is now an open design question rather than a settled list**,
> and it is the right time for that: `take` and `where` have never executed, so
> nothing is being renamed after the fact except `first_present`.

## R and Python differ by the PIPE ALONE — 2026-08-11

**god has two differences between its bindings**: the pipe (`|>` against `>>`)
and the column reference (bare `region` against `col.region`, because Python has
no NSE).

> **fathom has only the first, and that is a real advantage over its sibling.**
> **fathom does not reference columns — it references PATHS, and a path can be a
> plain string.** `take("author.name")` is valid R and valid Python, character
> for character. There is nothing for a `col.` prefix to do.

So the whole difference between the two bindings is one operator:

```r
doc |> fathom() |> ... |> take("author.name")
```
```python
doc >> fathom() >> ... >> take("author.name")
```

### The tension this creates, and its resolution

**Strings buy the parity and strings are also the readback risk**, and those are
not the same string.

| | |
|---|---|
| `take("author.name")` | **a plain name.** Reads back fine. Identical in both languages |
| `rows("versions.*.dependencies.*")` | **an embedded GLOB LANGUAGE** — `*`, `**`, `name**`, quoted keys. This is the `pluck(x, "a", "b", 3)` disease |

> **So the rule is: strings YES, notation inside strings NO.** What hurts
> readability is not that the path is quoted — it is that the reader has to
> decode `*` against `**` months later. **Multi-level navigation belongs in
> MULTIPLE SMALL STEPS in the chain, which is what makes dplyr readable, not in
> one clever string.**

**That reconciles every constraint at once**: small composing verbs, readable
months later, identical in R and Python, and only the pipe differs.

## MEASURED: two of the five proposed words already collide with god

**Checked against `~/Development/projects/god/README.md` on 2026-08-11**, since
the two packages are to be loaded together.

god's verbs include: `keep` `drop` `add` `summarize` `sort` **`take`** `rename`
`join` `group` `count` `pick` `row_count` `total` `descending`
**`first_present`**.

| fathom's proposal | |
|---|---|
| `fathom` | **clear** |
| `rows` | **clear**, but see the objection above — it presumes a table |
| `where` | **clear of god**, but it is dplyr's and SQL's, and it names a filter when it means a search |
| **`take`** | **COLLIDES.** god's `take(10)` takes the first 10 ROWS; fathom's `take(version, author.name)` selects FIELDS. **Same word, two packages loaded together, opposite meanings** — the exact failure the distinctness rule exists to prevent |
| **`first_present`** | **COLLIDES**, as already recorded |

> **Two of five, and neither was noticed until the sibling's README was actually
> read.** `take` is the worse of the two, because both meanings are plausible on
> a pipeline and nothing would warn a reader which one ran.

## The division of labour, and what it does to `take` — 2026-08-11

> **Most of the time the final outcome of dealing with JSON is a data frame. Any
> DATA MANIPULATION job belongs to god, not fathom.** — the author

**fathom: understand a document, move around inside it, get out with a table.
god: everything after the table.**

### `take` is now the weakest of the five, on two independent grounds

**The deletion test above already found the first one and recorded it as
"keeps, narrowly":**

> If `rows()` returns every column, then selecting three of them is god's
> `pick`, and `take` is a word fathom does not need — the seam is a data frame
> and selection lives downstream. **What saves it is cost**: `rows("versions.*")`
> alone is 288 × 140 and 60% empty.

**That defence is about EFFICIENCY and the new rule is about VOCABULARY.**
Selecting fields is manipulation, manipulation is god's, and "but it would be
wasteful to do it downstream" does not make it fathom's word — it makes it an
argument for `rows()` being lazy, or for a narrowing that happens during
navigation rather than after it.

**And it collides with god's `take` anyway.**

> **Re-argue it rather than rename it.** A rename fixes the collision and leaves
> a word in the vocabulary that the project's own division of labour says is not
> fathom's job. If the cost problem is real — and 288 × 140 at 60% empty says it
> is — **the answer is that you never navigate to 140 columns in the first
> place**, which is what a zoom-then-emit chain does naturally.

### What survives the rule, and it is a coherent set

**Everything about SEEING and GETTING OUT survives; nothing about reshaping
does.**

| job | fathom's? | why |
|---|---|---|
| report what a document is | **yes** | god has no analogue — it is handed a table |
| move to the part you want | **yes** | navigation of a document, not of a table |
| say what one row is | **yes** | this IS the doorway; it is what produces the table |
| find where a value lives when it moves between records | **yes** | path variance is a document property |
| find every path whose value matches | **yes** | search, not filter — it answers *where*, not *keep these* |
| select fields · filter rows · aggregate · sort · join | **NO — god's** | manipulation of a table |

> **This is the strongest argument yet that fathom is SMALL.** Four or five words
> about seeing and leaving, and not one about reshaping, because reshaping
> already has a package.

## The chain, derived again and RUN — 2026-08-11, `design/chain.py`

**The five words predate every constraint the author has since stated**, so this
is a second derivation rather than a rename. **The one structural idea:**

> **A VIEW is a document plus WHERE YOU ARE STANDING IN IT**, and every verb
> takes a view and returns a view.

That is dplyr's closure. In dplyr it comes from `read_csv` guaranteeing a data
frame; here it comes from the view. **Six words, none colliding with god:**

```
fathom()        see it — sound, shaped, and what a row could be
into(name)      go into a part of the document
back()          come back out one level
rows()          one row per thing here; THE EXIT to a table
find(test)      every path whose value matches
whichever(...)  the first of these paths that is actually there
```

**`take` is GONE** — selecting fields is manipulation, so it is god's `pick`, and
the cost argument that saved it is answered by never navigating to 140 columns.
**`first_present` becomes `whichever`**, which collides with nothing and is
plainer.

### THE HEADLINE: the glob language disappears

`design/rows.py` needs `*`, `**`, `name**` and quoted keys **because `rows()` has
to do NAVIGATION and UNIT-SELECTION in one call.** Split them across a chain and
there is nothing left for the notation to express:

```
rows(doc, "versions.*.dependencies.*")                     before
doc >> into("versions") >> into("dependencies") >> rows()  after
```

> **A SECOND EXCEPTION, found 2026-08-15 and it is defect 38.** *"There is
> nothing left for the notation to express"* holds whenever `*` is followed by a
> NAME — `into()` takes one implicit hop, so `versions.*.dependencies` really is
> `into("versions") → into("dependencies")`. **It fails for a BARE `*`.**
> `QUESTIONS.md` records the prototype answering the document-level depth with
> `first_present(doc, '*."12 Strong".Rating')`, a `*` in leading position meaning
> *each member of this collection*, and **no chain expresses that** — `into()`
> has no step that consumes a marker on its own.
>
> **So the glob did not disappear, it was absorbed.** `into()`'s implicit hop IS
> `*`-followed-by-a-name, kept and renamed; the standalone `*` is the one
> operator with no equivalent, and its loss was not recorded as a cost because
> this sentence said there was none. **Restoring it is what defect 38 asks for**,
> which makes that a retreat from this headline rather than a bolt-on.
> `FINDINGS.md` 2026-08-15 has the pricing: 26 sites corpus-wide.

### Run against the corpus, and THREE OF FOUR MATCH THE PROVEN NUMBERS

| document | sentence | got | `rows.py` / `first_present` |
|---|---|---|---|
| `01-npm-registry` | `doc >> into("versions") >> rows()` | **288** | 288 ✓ |
| `03-natural-earth` | `doc >> into("features") >> rows()` | **241** | 241 ✓ |
| `16-movie-ratings` | `doc >> whichever("Rating", "rating")` | **38 of 38** | 38 of 38 ✓ |

> **⚠ THAT ROW NO LONGER REPRODUCES — measured 2026-08-15, and it is defect 38.**
> The shipped word returns **0 of 1** on that exact call, in both bindings and
> the CLI. The row is kept because this table is a dated record of a prototype
> run: `first_present` took PATHS and found the value wherever it lived; the
> built `whichever` reads a field off each child of where you stand. **The
> semantics is not the bug** — `into("versions") → whichever(...)` on npm is
> **288 of 288**, and `into("12 Strong") → whichever(...)` here is **1 of 1**.
> What is missing is a way to stand on all 38 at once. See the limit below.
| `01-npm-registry` | `doc >> into("versions") >> into("dependencies") >> rows()` | **284** | **4,645 ✗** |

### The fourth is a REAL DESIGN GAP and it is worth more than the three that worked

**The chain removed the notation but NOT the ambiguity the notation was
expressing.** In `versions.*.dependencies.*` the trailing `*` says *and then each
ENTRY of that*. `into("dependencies")` leaves you standing on **284 dependency
objects**, and `rows()` honestly gives one row per object. The 4,645 answer is
one row per dependency **edge** — one level further down.

> **So `into()` and `rows()` do not by themselves say whether you mean the
> CONTAINER or its CONTENTS**, and that is exactly the question `rows()` exists
> to answer. Removing `*` removed the *spelling* of the ambiguity, not the
> ambiguity.

**Three candidate resolutions, none taken:**

| | |
|---|---|
| a verb for it | `>> each() >> rows()` — explicit, and adds a seventh word |
| `rows()` takes the depth | `rows(of = "entries")` — no new word, but an argument to decode, which is the glob problem returning as a keyword |
| `into()` never auto-descends | make every level explicit — most honest, most verbose, and the chain gets long |

**This is why the project's rule is that writing a sentence is not running it.**
The vocabulary read perfectly on paper and the third sentence was wrong by a
factor of sixteen.

## The collision rule, settled 2026-08-11: god and gog ONLY

**Checked rather than assumed.** The only names fathom must avoid are its
siblings', because those are the packages loaded alongside it by design.

| | |
|---|---|
| **god** | `keep` `drop` `add` `summarize` `sort` **`take`** `rename` `join` `group` `count` `pick` `row_count` `total` `descending` **`first_present`** |
| **gog** | no verb collisions — its two `into` occurrences are prose |
| **everything else** | **fair game, including jsonlite** |

**`read_json` is jsonlite's and fathom may take it.** Verified: `jsonlite`
appears in `fathom-core` **only in comments** explaining why the parser is
hand-written; the sole Rust dependency is `flate2`. fathom does not use jsonlite
at all, so there is no internal conflict — and if fathom reads your JSON you had
no reason to load jsonlite.

> **The precedent is the strongest one in R: `dplyr` masks `stats::filter` and
> `stats::lag`**, and those are *completely different operations* — time-series
> filtering against row subsetting. Nobody minds, because when dplyr is loaded
> its `filter` is the one you meant. Same here.

**The principled distinction, and it is why god is different from jsonlite:**

| | | |
|---|---|---|
| **god, gog** | **partners** — loaded together by design, fathom hands god a table | **must not collide** |
| jsonlite, purrr, tidyr | **alternatives** — if fathom works you do not load them for this job | **collision is fine** |

### The vocabulary, all seven names cleared

```
read_json(path)   read it in                    free — jsonlite's, and that is fine
fathom()          see it                        free
into(name)        go into a part                free
back()            come back out one level       free
rows()            one row per thing here        free — THE EXIT
find(test)        every path whose value matches free
whichever(...)    the first that is really there free
```

**Only `take` is barred, and it was already going** — god has it, and selecting
fields is manipulation, which is god's job by the division of labour above.

## Two candidate fixes, both RUN, and the ambiguity survived both — 2026-08-11

The gap: `into("versions") >> into("dependencies") >> rows()` gives 284 where
`rows.py` gives 4,645.

| candidate | `01` versions | `01` edges | `02` children | `03` features |
|---|---|---|---|---|
| want | 288 | **4,645** | 25 | 241 |
| **A** — `rows(name)` names the unit | 288 ✓ | **4,645 ✓** | 0 ✗ | — |
| **B** — explicit `each()`, `rows()` bare | 288 ✓ | **4,645 ✓** | **325 ✗** | **723 ✗** |

**Both get the hard case right and neither is correct.** A is *implicit* — one
short call silently iterates 288 versions, descends into each one's
`dependencies`, and iterates those entries, which is the `pluck(x,"a","b",3)`
problem in friendlier clothing. B is explicit and then **breaks the two easy
documents**, because `each()` on a list-of-containers must decide whether it
holds ONE collection of 284 things or 284 collections — and both readings are
valid.

> ### THE AMBIGUITY IS STRUCTURAL, NOT NOTATIONAL, AND THIS IS THE FINDING
>
> **`rows.py`'s glob language may have been right all along.** `*` and `**` are
> not arbitrary punctuation — they encode **how many levels of collection you are
> standing on**, and that is real information the document actually contains.
> Removing the notation removed the *place to say it*, and the ambiguity
> reappeared in every formulation that followed.
>
> **So the readback objection stands and the proposed fix does not.** The glob is
> hard to read a month later AND it is carrying something the chain has nowhere
> to put. Those are both true, and the honest position is that this is unsolved
> rather than that `rows.py` was wrong.

**What is NOT in doubt** — the view type, the closure, `fathom()` re-runnable
mid-chain, the six words clearing god and gog, and `take` being god's job. **The
open question is narrow and precise**: how a chain says *how deep the collection
goes* without a glob, and it may not have a good answer.

## RESOLVED, and by the author: `fathom()` prints the menu, `rows()` picks from it

**The previous section declared the depth question unsolved. It was wrong, and
the error was in how the candidates were TESTED rather than in the candidates.**

> *"To be explicit, we need more info — either fathom's or another function's
> results. Without that help, we can't be explicit."* — the author

**Both candidates were written out of the tester's head instead of from the
report**, which inverts the project's own premise. `README.md`'s motto is *Fathom
first. Then parse.* A user does not guess at depth — they have just been told it.

**The probe already prints the row candidates, in plain English, priced:**

```
ONE ROW COULD BE
  the whole document                      1 rows x   18 cols
  an entry of time                      320 rows x    2 cols
  an entry of versions                  288 rows x  140 cols   60% empty
  an entry of dependencies            4,645 rows x    2 cols
  an entry of devDependencies         3,175 rows x    2 cols
```

**So `rows("dependencies")` is not implicit. It selects a NAMED OPTION from a
menu the user was shown seconds earlier**, and the count it returns is the count
they already read. The implicitness objection assumed guessing; there is none.

| | |
|---|---|
| **explicit?** | **yes** — you name the unit, and the name came from the report |
| **readable in a month?** | **yes** — *"rows of dependencies"* needs no notation decoded |
| **needs a glob?** | **no**, for every candidate the probe enumerates |
| **the project's thesis?** | **exactly** — *state what a row is* and let the paths follow |

> **The report and the vocabulary are one design, not two.** `fathom()` is not a
> preliminary you run and discard — **it is what makes the next line writable.**
> That is why *fathom first, then parse* is a motto rather than a slogan, and it
> is the strongest argument yet for the probe being the centre of the package
> rather than its front door.

**What the glob may still be needed for** is the case the probe does NOT
enumerate — a unit it did not think to price, or one below the shapes it folded.
**That is a much smaller question than the one this section opened with**, and it
no longer blocks the vocabulary.

## The seven words by JOB — and `fathom` is the centrepiece, measured

| job | words | |
|---|---|---|
| **read in** | `read_json` | get the bytes — JSON, NDJSON, gzip, a stream, a `jsonb` column |
| **SEE** | **`fathom`** | **zoom out: the whole shape, sound or not, row candidates priced** |
| **move** | `into` · `back` | change where you are standing |
| **search** | `find` · `whichever` | zoom in: locate a specific thing |
| **exit** | `rows` | leave with a table; god takes it from here |

**Five jobs, seven words, no group empty and none overloaded.** It is the
author's own `read_csv` → `glimpse` → dplyr shape, with **move** and **search**
being what JSON needs and a data frame does not — a data frame has no depth to
move through.

### `fathom` is the centrepiece and there are four independent reasons

1. **It is the only part BUILT.** The Rust core is done, byte-identical to the
   Python oracle, clean on 26 of 26 documents, 912 MB → 9.7 KB.
2. **The deletion test already proved it.** Removing `fathom` makes **questions
   0–7 unanswerable on every file** — eight questions in one word. The other
   four words split five between them.
3. **It is the only word with no analogue.** `rows` ≈ tidyr's `unnest`,
   `whichever` ≈ `coalesce`, `find` ≈ any search. 25 files × 14 tools found
   **nothing** that produces output proportional to STRUCTURE with the row
   candidates named and priced.
4. **The others are only writable BECAUSE it printed the menu**, which is the
   2026-08-11 resolution above. Take it away and every other word goes back to
   guessing.

> **So the package could ship useful with `fathom()` alone**, and the extraction
> vocabulary can earn itself from real use. That sequencing also sidesteps the
> one thing no corpus can test: **whether the fathoming is enjoyable.**

### One word does not sit cleanly, and it has now resisted twice

**`whichever` searches but returns VALUES**, which makes it extraction rather
than search. It was also the awkward one in the original deletion test — kept
*"on different grounds than expected"*, for path variance rather than for the
question it was proposed against. **A word that resists categorisation twice is
saying something; what, is not yet known.**

## The deletion test re-run against ALL 25 entries — 2026-08-11

**The original ran against FOUR documents** (`01`–`04`) and concluded five words
answered nineteen questions. Twenty-one entries had never been asked. Re-run by
walking each hardness axis `design/axes.py` measures and asking *can the seven
words do this*, with a file required to prove each answer.

### What the seven DO cover

| property | worst file | the word |
|---|---|---|
| depth | `09-stripe` 26 levels | `into` · `back` |
| keys-as-data | `09-stripe` 47 sites | `rows` — the key becomes a column |
| raggedness, absence & null | `05-fhir` 144/285 | `rows` gives NA; the rest is god's |
| path variance | `04-gharchive` 76 | `whichever` |
| unit ambiguity | `05-fhir` 45 shapes | `fathom` prices them, `rows` picks one |
| value search | any | `find` |

### FOUR OPERATIONS WITH NO WORD, each proved by a file

| # | operation | proved by | why no word reaches it |
|---|---|---|---|
| **1** | **follow a recursive structure to UNKNOWN depth** | `02-hn-thread` — **13 levels**, 25 top-level comments against **335** for the whole thread | `into("children")` goes one level. The depth is not known when the code is written, and **a chain cannot be of unknown length.** `rows.py` needed `children**` for exactly this |
| **2** | **split an array by its discriminator into SEVERAL tables** | `05-fhir-bundle` — one `entry` array, **20 resourceTypes, 42 key-sets**; one table is 96% empty, four are usable | `rows()` returns ONE table. **god cannot do it either — god is handed one table.** The probe already computes and prints the split |
| **3** | **zip positionally-aligned arrays** | `06-espn-qbr`, `17-openlibrary` — `author_key` and `author_name`, aligned by position and nothing else | `rows("author_key")` yields one column and **drops the pairing**. Question 7a's operation |
| **4** | **unpack a delimited string into rows** | `25-usgs-quakes` — `,nearby-cities,origin,phase-data,` | none of the seven splits text. Defect 26; **tidyr was the only tool of fourteen with a verb for it** |

> ### THE PATTERN, AND IT IS THE FINDING
>
> **On 1 and 2 the probe ALREADY SEES what the vocabulary cannot DO.** `fathom()`
> reports recursion depth, and it prints the split — *"or 4 tables, split on
> ebook_access — 16% empty"*. **The report is ahead of the verbs.**
>
> That is a coherent kind of gap rather than four unrelated omissions: **fathom
> can describe structure it has no way to act on**, and every one of these four
> is a case where the document's shape is known and unreachable.
>
> **3 and 4 are the same shape one level down** — the probe detects positional
> alignment and defect 26 names packed strings, and neither has a verb.

**Seven is not enough, and the gap is not scattered.** Whether these become four
new words, or one word with an argument, or belong to `rows()` as further units
it can name, is a design question — but they are not covered now and each has a
file that proves it.

## Deciding the four: the REPORT'S SHAPE is the VOCABULARY'S SHAPE — 2026-08-11

**Asked of the corpus rather than of taste: does the probe already NAME the
thing? If it does, `rows()` can take it and no word is needed.**

```
02-hn-thread
  ONE ROW COULD BE
    the whole document                      1 rows x 13 cols
    a node at any depth (13 levels)       336 rows x 13 cols   23% empty
      └─ or 2 tables, split on type — 0% empty: comment 335, story 1
    an item of children                    25 rows x 13 cols   23% empty
```

**The menu has TWO LEVELS and so should the verb.** Top-level lines are UNITS;
the `└─` line is a MODIFIER on a unit, not a unit of its own.

| # | gap | verdict | why |
|---|---|---|---|
| **1** | recursion to unknown depth | **NO NEW WORD — it is already a named unit** | the probe prints *"a node at any depth (13 levels) — 336 rows"* as a row candidate beside *"an item of children — 25 rows"*. Both are units; `rows()` picks either. **`children**` was notation for something the report says in English** |
| **2** | split by discriminator | **NO NEW WORD — an ARGUMENT to `rows()`** | it is printed as a `└─` sub-line *under* a unit, because that is what it is: the same unit, emitted as several tables. **Not a new shape — a modifier on one** |
| **3** | zip positional arrays | **UNDECIDED — check whether the probe names it** on `06-espn-qbr`. If it appears in the menu it is a unit like the others; if not, it is a genuine gap |
| **4** | unpack a delimited string | **NOT FATHOM'S — reuse god** | the probe does not name it and should not: it calls those fields text **because they are text**. Splitting a delimited string is an operation on a COLUMN of a table, which is exactly where tidyr's `separate_longer_delim` does it. **By the division of labour it is manipulation, so it is god's** |

> ### THE PRINCIPLE, and it settles more than these four
>
> **Anything `fathom()` names in its menu, `rows()` can take. Anything the report
> prints as a `└─` modifier is an argument. Anything the report does NOT name is
> either not fathom's job, or a defect in the REPORT rather than a missing
> word.**
>
> That is why the report and the vocabulary are one design. **The verbs do not
> need to be able to say anything the report cannot say** — and the report is
> already ahead, which is the safe direction for the gap to run.

**So seven words may be enough after all**, and the earlier finding was measuring
the wrong thing: it counted operations without asking whether `rows()` could
already name them. **The open item is #3 alone**, plus whether `rows()` takes one
argument or two.

## Gap #3 resolved, and it is a REPORT defect — not a missing word

**`06-espn-qbr`, checked.** The row menu offers `an item of categories — 28 rows
x 4 cols` and never offers the zipped stats. **But the report says, in its own
section:**

```
ALIGNED BY POSITION, NOT BY NESTING
```

**The probe SEES the alignment and does not offer it as a row candidate.** By the
principle established above — *anything the report does not name is either not
fathom's job, or a defect in the REPORT rather than a missing word* — and since
positional alignment is unarguably structure the probe already detects, **this is
the second branch.**

> **DEFECT 27, proposed and not repaired.** `design/probe.py` detects positional
> alignment and prints it, but does not add the aligned unit to `ONE ROW COULD
> BE`. On `06-espn-qbr` that unit is the four parallel arrays of length 10 —
> `labels`, `names`, `displayNames`, `descriptions` — which are a **10-row × 4-col
> table the menu never mentions.**
>
> **The probe is frozen at `d595d1d2…` and this is recorded rather than fixed.**
>
> > **REPAIRED 2026-08-11, authorised, and the probe is re-frozen at
> > `ecf70b91…`.** The aligned unit is now a candidate — **one per PARENT**,
> > named by its path, so file 06 gains `a position in $.categories[]` at 10 x 4
> > and `a position in $.athletes[].categories[]` at 280 x 2, and `08-open-meteo`
> > gains the 336 x 5 that is the whole document. **The bare parent name was
> > tried first and collides**: both of file 06's parents end in `categories`,
> > and `an item of categories` was already in the menu. See `FINDINGS.md`,
> > 2026-08-11.
> >
> > **This is the fourth gap resolving exactly as the principle predicted** — a
> > defect in the REPORT, not a missing word. **Seven words still stand.**

### All four gaps resolved, and NO NEW WORD is needed for any of them

| # | gap | resolution |
|---|---|---|
| 1 | recursion to unknown depth | **already a named unit** — `rows()` takes it |
| 2 | split by discriminator | **an argument to `rows()`** — the report prints it as a `└─` modifier |
| 3 | zip positional arrays | **a REPORT defect** — the probe should name the unit; then `rows()` takes it |
| 4 | unpack a delimited string | **god's** — it operates on a column of a table |

> ### SEVEN WORDS STAND
>
> `read_json` · `fathom` · `into` · `back` · `rows` · `find` · `whichever`
>
> **The earlier "seven is not enough" was measuring the wrong thing** — it
> counted operations without asking whether `rows()` could name them, and three
> of the four could or should.
>
> **Two consequences, both small.** `rows()` takes a unit and optionally a split,
> which is two slots matching the menu's two levels. And **the probe gains one
> row candidate**, which is a change to the REPORT and not to the vocabulary.

**The principle held on the one case it had not been tested against**, which is
the only reason to trust it on the next one.

## `rows()` takes TWO slots — tested against the corpus, 2026-08-11

**One slot, against `rows.py`'s known counts: four of five.**

| | got | want | |
|---|---|---|---|
| `01` `rows("versions")` | 288 | 288 | ✓ |
| `01` `rows("dependencies")` | **4,645** | 4,645 | ✓ |
| `03` `rows("features")` | 241 | 241 | ✓ |
| `05` `rows("entry")` | 564 | 564 | ✓ |
| `02` `rows("children")` | **335** | **25** | ✗ |

**Two slots, on entries whose menu prints a split:**

```
19-chicago-salaries   rows("row", split_on="salary_or_hourly") -> 2 tables
     SALARY   3,938 rows x 7 cols
     HOURLY   1,062 rows x 8 cols
```

> ### THE SECOND SLOT IS CONFIRMED, AND THE PROOF IS THE COLUMN COUNTS
>
> **7 columns and 8 columns — different sets per group.** That is exactly the
> thing a frame cannot represent, measured earlier today: as one table the split
> prices at 0.2235 against 0.2235, and with the column set recomputed per group
> it is **0.0000**. **The benefit exists only if the split happens before the
> table is built**, so it must be fathom's and it must be an argument to
> `rows()`. Confirmed by running rather than argued.

### Three things the run found that reasoning had not

**1. `rows()` must take the REPORT'S CANDIDATE NAME, not a bare field name.**
`rows("children")` returned **335**, because "every container named `children`,
anywhere" is the RECURSIVE reading. The probe already distinguishes them —
*"an item of children — 25 rows"* against *"a node at any depth — 336 rows"* —
and **the field name alone cannot.** This closes the loop on the principle:
`rows()` takes what `fathom()` printed, and the earlier `02-hn-thread` failure
had the same cause.

**2. The discriminator can be NESTED.** On `05-fhir-bundle` the split is on
`resource.resourceType`, one level below the entry, so the prototype grouped
everything under `None`. **The second slot takes a PATH, not a field name.**

**3. A split can yield ONE table**, as on `02-hn-thread`, where the `story` node
is not inside `children`. That is a correct answer and the caller must not be
surprised by it.

**None of the three changes the verdict — `rows(unit, split_on = path)`, two
slots — and all three are specification detail that only running produced.**

## The sentences run across ALL 25 entries — 2026-08-11

**Method**: parse each document's own `ONE ROW COULD BE` menu, then ask whether
`rows(<the candidate name the probe printed>)` reproduces the row count the probe
promised. **197 candidates across 25 documents.**

```
  ══ 147 match, 37 miss, 13 not expressible by a candidate name
```

**Eleven entries are perfect** — `03`, `08`, `11`, `13`, `14`, `15`, `17`, `19`,
`22`, `23`, `25` — including `13-package-lock` at 8 of 8 and `21-crossref-works`
at 16 of 17.

### The 37 misses are the PROTOTYPE, not the vocabulary

| | got | want | |
|---|---|---|---|
| `01` `an item of contributors` | 1,596 | **7** | collected every occurrence |
| `05` `an item of coding` | 3,540 | **3** | same |
| `09` `an entry of properties` | 23 | **6,714** | the opposite — collected too few |

**The naive rule was "every container with this name, anywhere."** The probe's is
narrower and comes from its FOLD, which knows which occurrences a candidate
covers. **So `rows()` cannot re-derive the candidate set — it must share the
probe's fold**, which is exactly what "the report and the vocabulary are one
design" means in code. `fathom-core` already has the fold; `rows()` calls it
rather than reimplementing it.

> **That is a finding about the IMPLEMENTATION, not the words.** The candidate
> name is the right argument; a second engine guessing at what it means is not.

### DEFECT 28, proposed: the report prints names a user cannot type

```
10-wikidata     an item of <key>     707 rows
```

**`<key>` is a placeholder, not a name.** If the principle is *`rows()` takes
what `fathom()` printed*, then **every printed candidate must be typeable**, and
this one is not. It is the same class as defect 27 — the report is ahead of the
verbs — and it is a **REPORT** fix, not a vocabulary one. **Recorded, not
repaired**; the probe is frozen at `ecf70b91…` since defect 27.

> **It is on TWO documents, not one.** `09-stripe-openapi` prints
> `an entry of <key> — 7 rows x 19 cols`, which the run that proposed this
> defect did not notice.

> ### REPAIRED 2026-08-12, authorised. The probe is re-frozen at `2b0fa4d1…`
>
> **`<key>` is the fold's spelling of `*`, and `*` is already this vocabulary's
> word for the same thing.** `rows.py` defines it as *every child — object
> values and array elements alike* and requires *the key at every `*` is data
> and must survive into the table*, which is the definition of a keys-as-data
> site. **So the label writes the marker in the external language and invents
> nothing**: `$.entities.Q30.aliases.<key>` is `aliases.*`, one `.*` per marker.
>
> **THE BARE NAME ONE LEVEL UP WAS TRIED FIRST AND MEASURED. It deletes the
> line.** `aliases` is itself keys-as-data, so `an entry of aliases` already
> held the name and the candidate was dropped — an untypeable candidate traded
> for a missing one. **The `.*` is what separates two real units**: an ENTRY of
> `aliases` is one row per language, an ITEM of `aliases.*` is one row per
> alias.
>
> **The defect was hiding three row shapes, which is the larger half.** `<key>`
> is one string at every keyed site, so four sites on `10-wikidata` collapsed to
> one name and the menu kept the smallest. **`an item of claims.* — 1,724 rows
> x 98 cols, 88% empty` had never been printed.**
>
> **This is the fifth gap resolving as the principle predicted** — a defect in
> the REPORT, not a missing word. **Seven words still stand**, and no word was
> added for any of the five.
>
> > **What it does NOT establish.** No candidate name has been round-tripped
> > through a real `rows()`. Typeability is a claim about the label until
> > `rows()` is rebuilt on the probe's fold and resolves `aliases.*` to the 707
> > rows the menu promises. **That is the test, and it has not been run.**

### DEFECT 29, proposed 2026-08-12: a label the menu prints TWICE

**Found by building `rows()`, which is the only thing that could have found
it.** `a node at any depth (N levels)` is not unique — two recursive shapes at
different paths with the same depth print the same line.

```
09-stripe-openapi   a node at any depth (2 levels)   x6
                    4, 415, 748, 6, 3, 2,542 rows
```

**Seven candidates across two documents cannot be selected**, and on `09` the
unreachable set includes the document's largest table, 2,542 x 393. The first
line answers for all six.

> **This is defect 28's class one level up: 28 was a label that was not
> TYPEABLE, 29 is a label that is not DISTINCT.** Both break the same principle
> — *anything `fathom()` names, `rows()` can take* — and **neither was visible
> until something tried to consume the menu.**
>
> **A REPORT defect again, and no new word.** That is now five gaps in a row
> resolving the same way. Recorded, not repaired: `probe.py` stays at
> `2b0fa4d1…`.

### What this settles

- **`rows(unit, split_on = path)` — two slots — stands.** Nothing in 197
  candidates argued against it.
- **The candidate name is the right argument**, confirmed on 147 cases.
- **`rows()` must be built on the probe's fold**, not beside it.
- **Two report defects (27, 28) and no missing words**, which is the same
  direction every check this session has run.

## ALL SEVEN WORDS ARE BUILT — 2026-08-13, both languages

**This document designed them and one existed.** They now all run, in R and in
Python, differing by the pipe alone as required.

```r
read_json(f) |> into("versions") |> into("dependencies") |> rows("an entry of $[]")
```
```python
read_json(f) >> into("versions") >> into("dependencies") >> rows("an entry of $[]")
```

Both return **4,645**, the proven number.

| job | word | what it turned out to be |
|---|---|---|
| read in | `read_json` | source **and soundness**. It reports damage rather than raising |
| SEE | `fathom` | unchanged |
| move | `into` · `back` | **free** — a view is a source and a list of names, so navigating costs nothing until you ask |
| search | `find` · `whichever` | `find` takes a **named test**, never a closure |
| exit | `rows` | unchanged; takes a label off the menu |

### The gap this document left open is CLOSED, and by the menu

Line 676 recorded that `into("versions") >> into("dependencies") >> rows()` gave
**284** where **4,645** was wanted, that two candidate fixes were run and **the
ambiguity survived both**, and that the honest position was *"this is
unsolved."* Standing there now, the menu prints both readings, priced:

```
a record            284 rows x 44 cols    <- one row per dependency object
an entry of $[]   4,645 rows x  2 cols    <- one row per dependency edge
```

**Container-versus-contents is answered by showing both and letting you name
one** — the resolution the author reached the same day for `rows()`, which
nobody had connected back to the chain.

### And the glob question is answered the way this document hoped

Line 697 said the notation was *"carrying something the chain has nowhere to
put."* It has somewhere now: a scoped report prints the **resolved** path.

```
at $.versions.*.dependencies
```

**You type names; you are shown the `*`.** The notation is output, never input,
which is what made it unreadable when it was something to write.

### What was decided by measurement rather than argument

**`into()` is the performance mechanism, not a convenience.** Parsing is 1% of
the cost of describing a document — 0.05s against 5.21s on 18 MB — so scoping
the ANALYSIS is the only saving there is. `--at webassembly` on
`29-mdn-browser-compat` is **66x** faster than the root.

**`find` cannot take a function**, because a closure cannot cross a subprocess
boundary and could not be the same closure in both languages if it did. The
named tests were already in `design/where.py` and already in the core.

**Nothing here required a new word**, which is the test this document applies to
itself.

### One limitation, and it is `into`'s

**`into` descends by NAME only**, so a document that wraps its records in a bare
array cannot be entered: `16-movie-ratings` is `[{38 movies}]`. Its 38 are
reachable through the menu as `an entry of $[]`, and `whichever` reaches them at
**38 of 38** the moment the collection has a name. Whether `into` should be able
to enter an unnamed container is an open question and is **not** answered here.

> **⚠ THE PARAGRAPH ABOVE IS WRONG AND IS CORRECTED BELOW — measured
> 2026-08-14 over all 29 documents.** It is kept as written because this file
> records what was believed as well as what is true.

### CORRECTED 2026-08-14: an unnamed container CAN be entered, and it scopes better

`extract.rs::at` has an array branch that **gathers**: standing on an array,
`into("x")` means every element's `x`. So an array root is not refused, it is
descended THROUGH.

```
fathom probe corpus/16-movie-ratings/source.json --at "12 Strong"
  at $[].12 Strong          7 KB
```

**`into` was refused on ZERO of the 29 documents.** The root is a bare array in
8 of them and every one accepted a name.

| | median saving from `into` |
|---|---|
| object roots (21 documents) | **4.1x** |
| **array roots (8 documents)** | **8.9x** |

**Array roots scope BETTER**, because gathering one field across N records
touches a small fraction of the document: `20-homebrew-formulae` goes 6.90 s to
0.07 s, **99.2x**.

**THE REAL LIMITATION IS DIFFERENT AND NARROWER.** Five documents offer only
**DATA keys** at the root — `14`, `15`, `16`, `20`, `27` — so the name that gets
you in is `"12 Strong"` or a formula's `full_name`. **It works, and it is not a
name anyone can write down in advance**: question 14 failing, where the
paragraph above claimed question 8 was.

> **And it is not an array-root property at all.** `27-grafana-dashboard` is in
> that list and its root is an OBJECT. What matters is whether the root's keys
> are data.
>
> **AND A THIRD LAYER, 2026-08-15 — you can enter ONE member, never the
> collection.** The correction above is right that `into("12 Strong")` works.
> What it does not say is that the name gets you **that one movie** and there is
> no step to the 38 as a set:
>
> | | |
> |---|---|
> | `into("12 Strong") → whichever("Rating","rating")` | **1 of 1** |
> | `whichever("Rating","rating")` at the root | **0 of 1** — the root's one child is the 38-key object |
> | `rows("an entry of $[]")` | **38 rows x 9 cols** |
>
> **`rows()` reaches the level and the movement words cannot.** That is
> defect 38, and the decision recorded 2026-08-15 is to **accept it rather than
> add an eighth word**: it strands 26 sites corpus-wide, the menu already names
> 152 of the 178, and the word would reintroduce the path-stepping that
> `README.md`'s founding hypothesis exists to remove. **The limit is stated here
> instead of repaired**, which is what this project does with limits it has
> priced. `FINDINGS.md` 2026-08-15.
>
> **Two documents succeed and save nothing**: `07-graphql-introspection` at 0.9x
> and `10-wikidata` at 1.0x, because a single wrapper key holds everything.

**The open question changes shape rather than closing.** Not *should `into`
enter an unnamed container* — it does — but **what does a reader type when every
name at the root is data.** `FINDINGS.md`, 2026-08-14.

### OPEN, found 2026-08-14: a MENU LABEL is not a NAVIGABLE NAME

The report prints one list of names and the vocabulary reads it two ways.

```
ONE ROW COULD BE
  an entry of versions                  288 rows x  140 cols
  an entry of dependencies            4,645 rows x    2 cols
```

| | |
|---|---|
| `rows("an entry of dependencies")` | **works from the root.** The label names a row shape ANYWHERE in the document, and the fold resolves it |
| `into("dependencies")` | **refuses at the root.** `dependencies` is not a field of `$`; it lives under `versions`, and `into` walks one level from where you stand |

**Both are right and the report does not say which is which.** A reader who has
just been shown `an entry of dependencies` has no way to tell that the word
after `of` is not something `into()` will take.

**Found by the binding test halting**, because the test had assumed a menu label
was a name it could navigate to — the same assumption a person would make.

> **Not repaired, and the repair is not obvious.** Three candidates, none
> measured: the menu could print the PATH it found each candidate at, so
> `an entry of dependencies` reads `versions.*.dependencies`; or `into()` could
> accept a label and jump; or the two lists could be visibly separate on the
> page. **The first costs width on every line of the most-read output in the
> project**, which is the kind of change `design/probe.py`'s caps exist to
> resist. It wants measuring rather than arguing.

### MEASURED 2026-08-14, and two of the three candidates are refuted

All 29 documents, `design/menu-labels.py`, predictions first in
`design/menu-label-predictions.md`. Numbers in `FINDINGS.md`.

**The defect is the common case: of the 324 candidates that carry a name, 242 —
75% — are NOT navigable by `into()` IN ONE STEP FROM THE ROOT.** Twenty of 29
documents have at least one.

> **The qualifier was added 2026-08-15 and it matters.** `menu-labels.py`'s
> `navigable()` runs `--at <name>` **once, from the root**, so this measures
> *typeable as it stands* and not *reachable at all*. `10-wikidata` scores **0
> navigable** and `into("entities") → into("aliases")` works.
>
> **The defect and its repair are unaffected**, because a label the reader has
> just been shown and cannot type is the defect whether or not some chain
> reaches it. But *"not navigable"* without the qualifier reads as *unreachable*,
> which the eighth-word pricing measured and disproved: excluding the defect-36
> document, only **178 of 2,727** folded sites are unreachable by any chain, and
> the menu already names **152** of those. `FINDINGS.md` 2026-08-15.

| candidate | verdict |
|---|---|
| **A** — print the PATH beside each label | **REFUTED by the page's own width.** Median path 29 characters, longest 262, and the line would pass `WIDTH = 92` on **15 of 29 documents** |
| **B** — `into()` accepts a label and jumps | **CANNOT BE SPECIFIED.** 99 labels across 17 documents resolve to **two or more** folded paths, so there is no basis to choose a destination. Defect 34 found the same property from the other side |
| **C** — the two lists visibly separate | **survives** — it changes what the page CLAIMS rather than what it prints per line |

> **A FOURTH CANDIDATE, not among the recorded three, and the measurement
> argues for it.** The menu is a menu FOR `rows()`. Nothing on the page says
> so; the binding test assumed otherwise and a person would too. **Saying it in
> the page's own words costs one line for the whole report**, where A costs
> width on every line.
>
> **The ambiguity is about KIND, not LOCATION, and that is what the numbers
> settle.** A path tells a reader where a thing lives and never tells them that
> the word after `of` belongs to a different verb.

**Still not repaired.** Choosing between C and the fourth candidate is a
decision about what the page claims, which `README.md` owns.

### RENDERED 2026-08-15, and C is the third of three to fall

Both survivors were rendered on all 29 documents by `design/menu-variants.py`,
which runs the shipped binary and rewrites only the menu block, so nothing was
tried by shipping it. Numbers in `FINDINGS.md`.

**The instrument agrees with the 2026-08-14 measurement — 360 menu entries, 82
navigable — which is the check that says it is looking at the same thing.**

| | rendered result |
|---|---|
| **C** — the two lists visibly separate | **a NO-OP on 9 of 29**, because the separator needs both groups and nine documents have nothing navigable at all. On the other 20 it separates something **and reorders the menu, every time** |
| **the fourth** — say the menu is FOR `rows()` | **no line, no column, no reorder, on any document.** It is words on a header that already exists |

**C never helps without also reordering**, and rendering is the only thing that
showed it. On `23-cratesio-summary` it moves `the whole document` from first to
last and files it under *the rest name a shape, not a place you can stand* —
true, since `into()` cannot navigate to the root, and a strange thing to say
about the most basic entry on the page.

> **The reordering is a real cost and NOT a broken contract, and the difference
> was checked rather than assumed.** This section first claimed the menu's order
> is *"documented as meaningful"*, citing *"Ordered by copies, so what is above
> is the biggest of them"*. **That sentence is about RECORD SHAPES, not this
> menu** — `probe.py:1705` iterates `candidates()` and the printer does not
> sort, so the order is the fold's discovery order. **What C costs is replacing
> an order that follows the document's structure with one that follows a
> capability**, which is a judgement rather than a violation.

**So the measurement argues for the fourth candidate**, as the 2026-08-14 note
suspected it would.

### SHIPPED 2026-08-15, authorised by the author — the defect is CLOSED

```
  ONE ROW COULD BE — give any of these to rows()
```

**`design/probe.py` was unfrozen for it and re-frozen at `0b26038d…`**, with
`fathom-core/src/report.rs` moved in the same commit. `CLAUDE.md`'s freeze block
owns the hash and the diff.

**What it cost, measured over everything**: every report exactly **32 bytes**
longer, `parity.py` clean on all four phases, `design/coverage.py`'s **four
naming columns identical on all 28 documents**. The only column that moves is
description size, upward, on the two smallest files — `08-open-meteo` 8.7% to
9.0% and `16-movie-ratings` 16.6% to 17.0%, where 32 bytes is a visible fraction
of a 7 KB document.

> **The gate counter does not move.** No document forced this: the defect came
> from `test/bindings.py` halting on an assumption a person would also make, and
> the repair was chosen by rendering rather than by a held-out run. It is the
> same rule defects 20, 27 and 28 established.

**Two readers had to learn the header, and they fail in opposite directions.**
`test/candidates.py` matched it by equality and would have found no menu at all,
scoring every document as having no candidates — **a pass**. `design/coverage.py`
would have stopped recognising the section and scored its names as unnamed —
**which reads as the probe getting worse rather than as the instrument
breaking.** Both now match by prefix, and the pair is worth remembering: a
string constant shared between a producer and its scorers has a failure mode in
each direction, and only one of them is loud.

**What is NOT claimed.** This does not make a label navigable, and it does not
tell a reader which labels `into()` will take — 75% still will not. It says what
the list is for, which is the thing nothing on the page said.

## `find`'s four tests were argued against the corpus — 2026-08-14, and they STAY at four

The word has always been *"a named test, never a closure"*, and this document
never said which names or why. `url`, `email`, `date` and `empty` came out of
`design/where.py` on 2026-08-09 by writing down what a person might search for.
**They were run against all 29 documents on 2026-08-14** — predictions first in
`design/find-tests-predictions.md`, numbers in `FINDINGS.md`.

**Nothing was added and nothing retired**, and the reasons are worth keeping
because two of them are not the reasons expected.

| test | why it stays |
|---|---|
| `url` | broadest coverage of the four, and **the one that commits the O(data) failure** — 11,320 folded paths on `29-mdn-browser-compat`. That is defect 36 and it is the fold's, not the test's |
| `email` | the narrowest, and coverage is the wrong axis for it: a document that should carry contact information and does not is a finding |
| `date` | **it is blind to epoch time.** `25-usgs-quakes` writes milliseconds and `date` finds nothing there. Widening it is the strongest change the run argues for, and it has ONE document |
| `empty` | **predicted to be the weak one and it is not.** It is the only one of the four that says anything about `07-graphql-introspection`, where GraphQL writes `null` rather than omitting |

> **A fifth test is an ARGUMENT and not a word, which is why the set can be
> settled by evidence at all.** Six candidates were measured on the same fold
> and the same documents; `number` is the broadest at 23 of 29 and `packed` —
> defect 26's category — reaches only 3. **None was adopted**, because a test
> set is a promise to every future document and one corpus is not that.

**An unknown test name is now REFUSED rather than answered.** Until 2026-08-14
`find(v, "urls")` returned zero rows and no error, which is defect 35: a zero
here is evidence, so a typo was indistinguishable from a finding. **The four
names live in `fathom-core`**, in `extract::TESTS`, and neither binding checks
them — a binding that knew the set would be a second place to edit when there
is a fifth.
