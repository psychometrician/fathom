# 01 — npm registry metadata for `express`

**Provenance.** `curl https://registry.npmjs.org/express`, fetched 2026-08-08.
786 KB. Public, stable, and re-fetchable, though the content grows as versions are
published, so the committed copy is the specimen rather than the endpoint.

**Why this one first.** It is real data that people genuinely parse, it is one
HTTP GET, and it is famous for being unpleasant. It turned out to be unpleasant in
a narrower way than expected, which is recorded below and is the useful part.

---

## Grading, measured 2026-08-08

| Axis | Grade | Measured |
|---|---|---|
Re-measured 2026-08-08 with `design/axes.py`, against the axis list as audited
that day.

| Axis | Grade | Measured |
|---|---|---|
| depth | **moderate** | 6 levels. Corrected from 9; see below |
| recursion | **none** | no self-similar nesting anywhere |
| raggedness, by absence | **severe** | across version objects, **9 of 40 keys appear in every one and 31 do not**; **36 of 83** field slots document-wide |
| raggedness, by null | **none** | **0** fields are sometimes null and sometimes not |
| polymorphism | **none** | 0 fields take more than one non-null type |
| keys-as-data | **severe** | **6 sites**; the largest is `users` at 2,648 keys |
| heterogeneous arrays | **mild** | **1** array holds more than one shape |
| path variance | **severe** | **18** field names live under more than one container |
| unit ambiguity | **high** | **10** defensible row shapes |
| scale | **trivial** | fits in memory many times over |
| *path explosion* | *derived* | 25,043 paths for 71 field names, a ratio of **353** — demoted to a symptom of the keys-as-data above |

**The two cells that said "not yet measured" are now filled, and one is severe.**
`path variance` is **18**: `author`, `maintainers`, `contributors`, `repository`,
`bugs`, `keywords`, `description`, `license` and `homepage` all live both at the
top level and again inside every version. Nobody had noticed, and it makes this
file a path-variance specimen as well as a keys-as-data one.

## What the numbers say

**25,044 paths for 40 fields is the headline**, and it is entirely caused by
keys-as-data. `versions` is an object keyed by version string, so every one of the
288 releases is its own path prefix, and `dependencies`, `devDependencies`,
`scripts` and `time` are each keyed by data again. A naive collapse of the
version-like and date-like keys takes 25,044 down to 2,851, and the rest is the
levels the heuristic could not see.

**No tool tells you this**, and it is the first thing you need to know. A path
listing of this document is useless at 25,044 entries and would be legible at
about 40. Recognizing keys-as-data is what stands between those two numbers.

**Detecting it is harder than it looks**, which is itself a finding. Matching keys
that look like versions or dates catches the top two levels and misses the rest,
because package names as keys look exactly like field names. The signal that
should work is that structural keys **repeat across sibling instances** and data
keys do not. Untested.

## Corrected 2026-08-08

**Depth is 6, not 9, and how the 9 happened is worth more than the correction.**
The deepest scalar is `versions.<version>.dist.signatures[0].sig`, which is six
levels. The 9 reproduces only if depth is counted by splitting a dotted path
*string*, because a version key like `5.0.0-alpha.1` then counts as four levels
instead of one.

**So the axis this file is severe on corrupted the grade on a different axis.**
Keys-as-data did not merely make the document large and the tools ugly. It
inflated a measurement, silently, to a number that still looked plausible.
**Never grade depth from a dotted path string**: every document this corpus wants
will have dots in its keys, so the instrument fails exactly where it is needed.

**Release events are 318, not 290, and the miscount was hiding something.** `time`
holds 320 keys, less `created` and `modified`. The 290 is `versions` plus those
two, a number derived from the wrong object. Of the 318 real entries, **30 have no
version object at all** — `1.0.0rc2`, `2.0.0-pre`, `1.0.0beta` and others. `time`
and `versions` disagree about what a release is, so a join between two of this
document's defensible row shapes is ragged in a direction nothing declares.

**The keys-as-data sites were misidentified, and the largest was missed.**
`engines` is listed above as one of them and is not: it holds exactly one key,
`node`, in all 287 objects that carry it. And **`users` is an object with 2,648
keys** — the biggest keys-as-data site in the document, never mentioned. The six
real sites are `versions` (288), `time` (320), `users` (2,648), `dependencies`
(44 package names), `devDependencies` (32) and `scripts` (8). `dist-tags` has two
keys and one instance, and nothing distinguishes it from `author{name, email}`, so
it is left undecided. Also measured: the 288 version objects have **40 distinct
key-sets**, so no fold may describe them as one shape.

All of that was found by drawing `design/probe-sketch.md`, not by re-reading the
file, which is a small piece of evidence for the probe.

**25,044 paths stands, now measured twice.** A hand-written walker and jq both
report 25,043 distinct node paths with array indices collapsed, plus the root. jq
reports 6 for depth as well.

## The expectation this file disconfirmed

**It was chosen partly as a polymorphism specimen and it has none.** npm's
`repository`, `bugs` and `author` fields are classically cited as sometimes a
string and sometimes an object, so the prediction was several polymorphic fields.
Measured across all 288 version objects: **zero**. The registry normalizes on
ingest, so the ugliness that the npm *ecosystem* is known for has been cleaned up
before the API hands it over.

Worth keeping for two reasons. The grading separated a file that is severe on
three axes from a file that is severe on all of them, which is the whole argument
for grading per axis. And it means **the corpus still needs a polymorphism
specimen**, which is now a stated gap rather than an assumption that it was
covered.

## Unit ambiguity, which is the point of the project

Four defensible answers to "what is one row", all from this one document:

| One row is | Rows | Reached by |
|---|---|---|
| the package | 1 | the top level |
| a released version | 288 | `versions`, keyed by data |
| a dependency of a version | thousands | `versions.*.dependencies`, keyed by data again |
| a release event | 318 | `time`, a different keyed object entirely |

**No tool asks which one you want.** Each is reached by a different traversal, and
the traversal is where the choice gets expressed, so the choice is never written
down anywhere a reader can see it. This is the hypothesis in `README.md` with a
concrete case attached.

## Status

Graded, then corrected in three places above.

**Question 8 is answered in three tools** — purrr, `pandas.json_normalize` and
DuckDB. **Questions 0 to 7 are answered in three more** — `r/try-jqr.R`,
`r/try-rrapply.R`, `r/try-tidyjson.R`, all of which get question 1 badly wrong
here (about 3,100 field names against a true 40) while getting it right on
`02-hn-thread` with unchanged code.

Questions 9 to 18 are unanswered.

**`try-jsonlite.R` added 2026-08-09, and the R half is now complete** — all five
of `README.md`'s R tools plus `tidyr`. Under `CLAUDE.md`'s definition this entry
is done. Two things it found:

- **Simplification is INERT on this document.** `fromJSON()` returns `versions`,
  `time` and `users` as named lists, not tables, because they are objects keyed
  by data and jsonlite has no notion that a key might be a value. On
  `03-natural-earth` the same rule builds a frame and preserves a polymorphism
  polars erased; on `05-fhir-bundle` it builds a frame that is 87% holes; on
  `02-hn-thread` it builds one at every level and none compose. **One rule, four
  outcomes, and it cannot tell which it is doing.**
- **`str()` here is 5,289 lines by default and 7,099 unsimplified.** `VERDICT.md`
  and `README.md` both published the 7,099 without saying it names a non-default
  parse. Both now carry the footnote.

**And the 3,100 is now explained rather than just recorded.** Measured
2026-08-09: it is `users` (2,648 usernames → booleans) + `time` (320 version
strings → timestamps) + 40 real version fields. **The key is the leaf only when a
keyed object's values are SCALARS** — which is why the same expression returns
**29** on `09-stripe-openapi`, whose 47 keyed sites hold objects. See that
entry's `r/try-jqr.R`.

**This file is spent as an exploration specimen.** It was hand-graded before any
tool attempted it, so nothing measured here can say how long a tool takes to
orient you on a document you have not seen. That is why `corpus/README.md` now
requires the tools to grade file 02 before anybody reads it.

## Corrected 2026-08-13: the leaf-name count was 3,100 and is 3,104

**The grades above are left alone** — they record what was measured on the day,
which is what a dated record is for. This says what the same expression returns
once corrected.

`try-jq.py` and `try-jqr.R` used `paths(scalars)`, which **silently drops every
`false` and every `null` leaf**: `select` tests its input for truthiness and
`scalars` returns the value itself, so a leaf that *is* `false` fails its own
filter. Four field names were invisible — `_hasShrinkwrap`, `contributors`,
`serverjs`, `wscript`.

| | |
|---|---|
| recorded | **3,100** |
| corrected | **3,104** |

**THE FINDING IS UNCHANGED.** 3,104 against ~40 real fields is still OVER by
75×, and the cause is still keys-as-data minting field names. `FINDINGS.md`,
2026-08-13, owns the corpus-wide account.
