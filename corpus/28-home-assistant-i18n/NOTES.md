# 28 — Home Assistant frontend, the English translation catalogue

## Provenance

**Fetched 2026-08-12** from
`raw.githubusercontent.com/home-assistant/frontend/dev/src/translations/en.json`.
604,600 bytes, 7 top-level keys — `panel`, `state`, `state_badge`, `groups`,
`config_entry`, `ui`, `landing-page`.

**A moving target by nature.** A translation catalogue grows every week, so
`fetch.sh` returns a LATER file rather than this one. `source.json` is committed
because it is under 5 MB, and these numbers describe the file as it was on the
day.

## Why this file, and it is a TARGETED test

**This document was chosen to attack defect 31's repair**, made hours earlier
the same day. That repair made the single-copy branch of `classify()` demand the
type homogeneity the multi-copy branch already demanded — and the evidence for
it was **ten corpus sites scoring exactly `1.0000` and one scoring `0.2400`.**

> **The corpus has NOTHING IN BETWEEN, and that is the hole.** A rule separating
> 1.0 from 0.24 is untested anywhere in the middle. The failure it would cause is
> silent and in the opposite direction from the defect it fixed: **a genuine
> keyed collection whose values are nearly-but-not-quite uniform would now be
> called a field list and would not fold.**

**A translation catalogue is that shape on purpose.** Its keys are message IDs —
data, unarguably — and its values are a string where a message is flat and an
object where messages are grouped. **Mixed values at the same level are not an
accident here; they are how the format works.**

**Selected by what it is, not by measuring it.** Only its size, that it parses,
and its 7 top-level key names were looked at before the predictions below. The
corpus has chosen files by intended property before, and recorded the four times
that failed.

## Predictions, committed 2026-08-12 BEFORE the probe was run

| # | prediction |
|---|---|
| 1 | **Deep**: nested message groups, depth ≥ 6 |
| 2 | **keys-as-data fires on several sites** — message IDs are data by definition |
| 3 | **THE TEST: at least one site scores `hom` strictly between 0.5 and 1.0**, mixing string and object values, which is the region the corpus has never had |
| 4 | **And defect 31's repair COSTS something there** — at least one site that a reader would call a keyed collection is now called a field list |
| 5 | **Recursion 0.** Message groups nest but are not self-similar; nothing recurses by name |
| 6 | **No positional alignment, no polymorphism worth the name** — values are strings and objects, and the probe reports type variation per site rather than per field |
| 7 | **Sound**: no duplicate keys, no NaN, no integers past 2^53 |
| 8 | **Almost no arrays.** A translation file is objects and strings |
| 9 | **The row menu is short** — few arrays means few `an item of` candidates, and the interesting units are all `an entry of` |
| 10 | **The description is under 2% of the input** |

> **Prediction 4 is the one that matters and it is a prediction AGAINST MY OWN
> REPAIR.** If it holds, defect 31's threshold is too strict and the fix needs a
> second look. If it fails — if every site is either clearly data or clearly a
> field list — then the 0.9 line survives a document built to break it.

## The grades, measured 2026-08-12

Cold run against `design/probe.py` at **`70d6c159…`**, verified before the run.

| axis | measured |
|---|---|
| bytes | 604,600 · depth **11** · paths **10,136** · fields **2,841** · explosion 3.6 |
| recursion | **0** · polymorphic **33** · heterogeneous 0 |
| keys-as-data | **52** |
| ragged by absence | **1,018/1,064** · ragged by null 0 |
| path variance | **604** · row shapes **47** |
| column-oriented | 0 sites |
| description | 34,388 bytes, **5.6877%** of the input |

## Prediction scorecard: seven of ten, one half, and the two misses matter

| # | predicted | outcome |
|---|---|---|
| 1 | depth ≥ 6 | **right.** 11 |
| 2 | keys-as-data fires on several sites | **right.** 52 |
| 3 | a site with `hom` strictly between 0.5 and 1.0 | **right, and it fills the hole.** 14 sites — **5 in the 0.50–0.89 band the corpus had never had** |
| 4 | defect 31's repair costs something | **RIGHT, and it is the finding.** Five sites lost, six menu candidates |
| 5 | recursion 0 | **right** |
| 6 | no alignment, no polymorphism worth the name | **half.** Alignment 0, but **polymorphic 33** |
| 7 | sound | **right** |
| 8 | almost no arrays | **right.** Not one `an item of` candidate in 47 |
| 9 | the row menu is short | **WRONG.** 47 candidates |
| 10 | description under 2% | **WRONG.** 5.69% |

## DEFECT 32: defect 31's threshold is in the wrong place

**The repair I made hours earlier is too strict, and this document was built to
find out.** It refuses five message groups that a reader would call keyed
collections:

| site | keys | `hom` |
|---|---|---|
| `$.ui.panel.profile` | 33 | 0.6364 |
| `$.ui.panel.lovelace.cards.energy` | 21 | 0.7143 |
| `$.ui.panel.config.<key>.account` | 47 | 0.7447 |
| `$.ui.panel.config.<key>.http` | 22 | 0.7727 |
| `$.ui.panel.page-onboarding.restore` | 47 | 0.8723 |

**The distinction the probe is drawing is not one a reader can defend.**
`ui.common` — 64 keys, every value a string — is called data. `ui.panel.profile`
is the same kind of object, a catalogue of message IDs, and is called a field
list **because it happens to contain a few sub-groups**:

```
ui.common          and · continue · previous · loading …          all strings
ui.panel.profile   current_user · logout · logout_title  strings
                   tabs · force_narrow                    dicts   <- the only difference
```

**Both are message catalogues. Whether a group contains sub-groups is incidental
to whether its keys are data.**

> **The band is now measured from both sides**, which is what makes this
> actionable rather than an opinion:
>
> | | `hom` | must be |
> |---|---|---|
> | `27-grafana-dashboard`'s root, a real schema | **0.2400** | **refused** |
> | entry 28's five message groups | **0.6364 – 0.8723** | **accepted** |
>
> **Any threshold in `(0.24, 0.64)` satisfies both documents. `0.9` satisfies
> only one.** Recorded, not repaired: the probe stays at `70d6c159…`.

**What the repair got right is untouched.** Entry 27's root at 0.2400 is still
correctly refused, and nothing here argues for going back — only for moving the
line.

## ALL FOURTEEN TOOLS, 2026-08-12 — and four of them beat fathom here

**All fourteen written, RUN, and their prose corrected against what printed.**
This entry is graded in all fourteen tools; 6 R + 8 Python.

### The R half, and R wins this document

| tool | Q12, the flattest honest table | |
|---|---|---|
| **rrapply** | `how = "melt"` — **8,518 x 12, ONE CALL** | a column per level, L1…L11 + value |
| **tidyjson** | `json_structure()` — 10,137 nodes | the TREE: parent.id, level, name, type |
| **jqr** | `paths(scalars)` — 8,518 x 2 | jq through a second door |
| **tidyr** | 8,518 x 12, **in eleven calls** | and three pieces of ceremony, below |
| **purrr**, **jsonlite** | PARTLY — the recursion is base R | neither contributed it |

**`rrapply(doc, how = "melt")` is the single best verb any of the fourteen brings
to this document.** One call, no shape known in advance, and its answer is richer
than `json_tree` or `paths(scalars)`: a dotted path is a string you must split
again, and `L1 … L11` are already columns you can group by.

### tidyr is the closest prior art fathom has, and this is where that runs out

**It reaches the same table and it takes THREE pieces of ceremony**, each found
by running it rather than by reading:

1. **The naive loop fails.** `unnest_longer` refuses a column holding both a
   finished message and a group still to open — *"Can't combine `<character>`
   and `<list>`"*. **330 objects here are exactly that**, and it is the same
   property defects 31 and 32 turned on.
2. **So the leaves must be set aside by hand** at every step.
3. **And then forced back to a list**, because `unnest_longer` silently
   simplifies the column when a level happens to be all characters, after which
   `bind_rows` refuses the halves.

**Written straight it is eleven identical calls by someone who already counted
the levels** — which is question 13 failed, in the tool whose rectangling verbs
are the nearest thing to `rows()` in either language.

> **polars fails the same way for the same reason** and does not recover:
> `unnest` raises on a name collision instead. **Two of the fourteen cannot melt
> this document with their own rectangling verbs**, and both break on a level
> that mixes a leaf and a group.

### Five independent tools agree on the shape

`rrapply`, `tidyr`, `purrr`, `jsonlite` and the probe all produce the same depth
histogram — **28 messages at depth 2 … 2,434 at depth 6 … 15 at depth 11** — and
`tidyjson`, `duckdb`, `jq`, `jqr`, `ijson` and the probe all say **depth 11** and
**8,518 leaves**. `jq`, `jqr` and `duckdb` independently report **330 objects
holding both a string and an object**, none of them asked the question.

### The Python half

**All eight written, RUN, and their prose corrected against what printed.**

| tool | Q12, the flattest honest table | |
|---|---|---|
| **duckdb** | `json_tree` — **8,518 x 2, built in** | one SELECT, `fullkey` is the dotted path |
| **jq** | `paths(scalars)` — 8,518 x 2 | one expression |
| **ijson** | the event PREFIX is already the path | and in constant memory |
| **pydash** | 8,518 x 2 | **but the recursion is mine, not pydash's** |
| **pandas** | **1 x 8,518** | the exact transpose, and it calls that a frame |
| **polars** | **CANNOT — `unnest` RAISES** | see below |
| **glom**, **jmespath** | CANNOT | no way to enumerate an unnamed path |

### `duckdb.json_tree` is the surprise, and my first draft assumed it away

**`json_tree(json)` walks the whole tree and returns one row per node** with
`fullkey`, `type` and `atom` — the melt, as a relation, no recursion written and
no shape known first. **A first draft of that attempt wrote a nine-line recursive
CTE because I assumed no such verb existed**, and the file records that it was
wrong. It is the closest prior art in either language to what `rows()` is for.

### polars cannot build the table AT ALL, and the reason is a name collision

```
df.unnest('ui')  ->  DuplicateError: column with name 'panel' has more than
                     one occurrence
```

**The root has `panel` and so does `ui`.** Lifting one level collides with the
level above, and polars refuses rather than renaming. The fix is to rename every
field on the way up — which is the dotted path the other three hand over for
nothing. **Not "awkward": cannot.**

### Four independent parsers agree, which is worth more than any one of them

| | probe | jq | ijson | duckdb |
|---|---|---|---|---|
| depth | 11 | 11 | 11 | 11 |
| leaves | 8,518 | 8,518 | 8,518 | 8,518 |
| objects | — | 1,618 | — | 1,619 |
| duplicate keys | 0 | — | 0 | — |
| objects mixing string and object | — | **330** | — | **330** |

**That last row is the number defects 31 and 32 were argued over**, and two tools
produce it without being asked the question.

### What none of the eight does, unchanged across 28 entries

**Name the alternative row shapes and price them.** Every one of them will count
8,518 messages, or 1,619 objects, or 7 sections — whichever you name — and not
one proposes the three or says what each would cost.

> **AND THE HONEST COMPARISON, now with all fourteen in.** On this document
> fathom's description is 5.69% of the input with 39.3% of fields unnamed, its
> worst in the corpus — while **rrapply, tidyjson, duckdb and jq each melt it
> completely, three of them in a single call.** On this document four of the
> fourteen give a better answer than fathom does, and that belongs in the record
> rather than in a footnote.
>
> **What none of the fourteen does, unchanged across 28 entries**: name the
> alternative row shapes and price them. Every one will count 8,518 messages or
> 1,619 objects or 7 sections — whichever you name — and not one proposes the
> three or says what each would cost. **That gap is the whole of what fathom has
> here, and on this document it is not enough to win.**

## What this file disconfirmed, and it is about the central claim

**A translation catalogue defeats the fold, and the numbers are not close.**

| | this file | the other 25 |
|---|---|---|
| description | **5.69%** | 0.1% overall |
| fields the probe leaves **unnamed** | **39.3%** | 1.1% overall |
| distinct paths | **10,136** | — |
| path variance | **604** | — |

**`README.md`'s claim is output proportional to STRUCTURE rather than to data.
That is exactly what happens here, and it is not a win**: in a translation file
the structure *is* the data. Every message group is a one-off, so there is
nothing to fold, and a description proportional to structure is proportional to
the file.

> **This is the honest limit of the thesis rather than a bug**, and it is worth
> more than another document that folds well. The probe does not fail — it
> reports 52 keyed sites correctly and gets **0.0% typed wrong** — it simply has
> nothing to compress. **The claim degrades gracefully and the corpus had no
> example of it degrading at all.**

**And it stresses defect 28's naming.** `an entry of components.*.*.*.*.*` is
typeable and it is five levels of stars. Nothing is wrong with it; it is the
scheme meeting a document with six levels of keyed nesting, and a reader should
see what that looks like before the vocabulary is called settled.

