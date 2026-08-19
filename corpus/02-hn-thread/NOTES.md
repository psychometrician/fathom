# 02 — one Hacker News comment thread

**Provenance.** `hn.algolia.com/api/v1/items/49220339`, fetched 2026-08-08.
193 KB, 336 nodes. See `fetch.sh`.

**Why Algolia and not HN's own API.** `hacker-news.firebaseio.com` returns **flat
items whose `kids` are id references**, so a thread has to be assembled from
hundreds of requests. Assembling it would make the document ours rather than one
somebody was handed, which `corpus/README.md` forbids. Algolia returns the whole
nested tree in one GET.

**Why this one.** The corpus had no recursion specimen at all, and
`package-lock.json` v3 had just failed to supply one. Three front-page threads
were measured for nesting depth and the deepest was taken.

**Graded by the probe before anybody read it**, which is the rule
`corpus/README.md` adopted the same day. Everything below the grading table was
learned from `design/probe.py` output or from a hand audit run afterwards.

---

## Grading, measured 2026-08-08

Measured with `design/axes.py`, against the axis list as audited the same day.

| Axis | Grade | Measured |
|---|---|---|
| depth | **severe** | 25 levels; the comment tree itself nests **13** deep |
| recursion | **severe** | **13** levels of self-similar nesting, 336 nodes, one shape |
| raggedness, by absence | **none** | **0 of 13** — one key-set across all 336 nodes |
| raggedness, by null | **severe** | **4 of 13** fields are null on all but one node |
| polymorphism | **none** | 0 fields take more than one *non-null* type |
| keys-as-data | **none** | no keyed-by-data object anywhere |
| heterogeneous arrays | **none** | `children` holds one shape only |
| path variance | **none** | **0** |
| unit ambiguity | **low** | **3** row shapes; a node or the story, nothing else defensible |
| scale | **trivial** | 193 KB |
| *path explosion* | *derived* | 181 paths for 13 field names, a ratio of **14** — a symptom of the recursion above, not of keys-as-data |

**This file is why `raggedness` was split into two axes.** On the old single axis
it scored "none", which is true of absence and wholly wrong about the document.

**Severe on one axis and clean on almost everything else**, which is the contrast
`01-npm-registry` could not provide on its own and the whole argument for grading
per axis.

## It corrects a finding the first file produced

`FINDINGS.md` concluded on 2026-08-08 that **"path explosion is not an independent
axis. It is what keys-as-data does."**

**This file has 181 paths for 13 logical fields and no keys-as-data at all.** The
cause is recursion: every nesting level mints a fresh path prefix,
`children[].children[].children[]`, exactly as every version key did in npm.

> **Path explosion has at least two causes. It is a symptom of anything that
> mints path prefixes, and keys-as-data is only the first one we met.**

Two files, and the second overturned a conclusion drawn from the first. That is
what the corpus is for.

## The story and its comments are the same shape

All 336 nodes carry the same 13 fields, so **the root is structurally a comment**.
The probe folded the entire document to a single record description because there
is genuinely only one.

**The polymorphism is entirely null-against-value**, and it says what that shared
shape costs:

| field | |
|---|---|
| `points` | number ×1, null ×335 |
| `title` | text ×1, null ×335 |
| `url` | text ×1, null ×335 |
| `parent_id` | number ×335, null ×1 |

Those four fields apply to the story or to a comment, never to both. So the one
shape is a **union of two record types with the inapplicable fields nulled** —
which is a different phenomenon from npm's raggedness, where a missing field is
simply absent. **Raggedness by null rather than by absence**, and nothing in the
grading axes currently distinguishes them.

## The expectation this file disconfirmed

**A comment thread was expected to be ragged** — deleted comments, missing text,
fields that appear only on some nodes. Measured: **zero.** One key-set across all
336 nodes, and not a single empty `text`.

**Algolia normalises on ingest, exactly as the npm registry does.** That is now
twice, and it is worth stating as a pattern rather than a coincidence:

> **The ugliness an ecosystem is famous for is usually cleaned up before the API
> hands it to you.** A corpus built only from public APIs will systematically
> under-sample raggedness and polymorphism.

That is an argument for the corpus to include documents that were *not* served by
an API — files written by tools, by models, and by hand.

## What the probe got wrong, before it was fixed

Recorded because the file's job was to test the probe as much as to fill an axis.
Four defects, and all four are the same defect wearing different clothes.

1. **It printed the same 13-field shape twelve times**, once per nesting level,
   with paths growing to `children[].children[].children[]…`. O(depth) output for
   a structure whose entire point is that it repeats.
2. **It priced the thread at 25 rows.** The true answer is 336. It had seen only
   the outermost `children` array.
3. **It reported no polymorphism at all**, because types were collected on
   unfolded paths and no single path ever saw both the story's `points` and a
   comment's.
4. **The row candidate was called "an item of "**, with an empty name, because a
   root that shares its children's shape canonicalises to `$` and the code took a
   two-character suffix off it.

> **Anything not computed on the fold reports the wrong thing.** That is now the
> fourth separate place this has bitten, after `candidates()`, the fold threshold
> and the type collection.

## Status

**Graded, and the probe fixed against it.** The fixed-point fold now collapses
self-similar nesting to one entry, and reports it: `RECURSIVE, 13 levels`.

**Questions 0 to 7 answered in three tools** — `r/try-jqr.R`, `r/try-rrapply.R`,
`r/try-tidyjson.R`. All three get question 1 right here (11 leaf fields) and all
three score CANNOT on questions 0, 3 and 6.

**`try-jsonlite.R` and `try-purrr.R` added 2026-08-09, and the R half is now
complete** — all five of `README.md`'s R tools plus `tidyr`. Under `CLAUDE.md`'s
definition this entry is done. What the recursive shape did to each:

- **jsonlite's simplification is at its most dangerous here, on the corpus's
  second-smallest file.** `$children` is a genuine 25 × 13 data frame and
  `nrow()` returns **25** — the top-level replies — **in a 336-node thread**,
  with nothing indicating 13 more levels below. Each `children` is a table whose
  `children` column is a list of tables, so the rectangle contains itself and
  there is no depth at which one table of comments exists. On `01-npm-registry`
  simplification fails visibly and you know you have work to do; **here it
  succeeds visibly and is wrong.**
- **purrr's `map_depth` is the verb that should have helped and cannot**: it
  takes a FIXED depth, and these nodes live at thirteen depths at once. Every
  question that worked — 4, 7, 8, 10 — worked by mapping over a flat list of 336
  nodes that **six lines of hand-written recursion** produced. Once that list
  exists purrr is excellent and reads cleanly.

> **Raggedness costs purrr a default per field; recursion costs it the list
> itself.** That is a difference in kind, and this file is the only one in the
> corpus that shows it.

Both attempts independently confirm the grades above: 336 nodes, 13 keys, **one**
key-set, 0 ragged by absence, and exactly **4** fields null on at least one node
(`parent_id` ×1, `points`/`title`/`url` ×335).
