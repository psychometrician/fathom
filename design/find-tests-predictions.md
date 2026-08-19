# `find`'s four tests, argued against the corpus — predictions, recorded first

**2026-08-14.** `VERDICT.md`'s START HERE box carries this as the top code
action, in these words:

> **`find`'s tests are four, and nothing chose them.** `url`, `email`, `date`,
> `empty` came from `design/where.py` and were never argued against the corpus.
> **Which tests would a person actually want?** That is a question the corpus
> can answer and nobody has asked it.

Recorded before the run under rule 1, because the exercise is only worth
anything if it can come out the other way.

## What is being measured, and why it is two numbers rather than one

**Coverage — on how many of the 29 documents does the test fire at all?** A test
that never fires is dead weight in a five-word vocabulary.

**Discrimination — when it fires, how many FOLDED PATHS does it name?** This is
the number that matters and it is the one nobody has looked at.
`where_`'s own docstring in `fathom-core/src/extract.rs` sets the standard:

> the naive answer on `01-npm-registry` is thousands of paths, which is the
> O(data) failure this project exists to name, **committed by fathom's own
> word**.

Folding fixed the O(data) failure for `url`. It does not follow that it fixed it
for all four. **A test that answers "everywhere" has not answered anything**, and
that is a failure the fold cannot repair because the paths really are distinct.

So the grid is: fires on many documents, names few paths on each. A test that
fails the second is not neutral — it is `CLAUDE.md`'s over-reporting, *"how a
diagnostic gets ignored"*.

**Values matched is recorded but is NOT a criterion.** 806 URLs at 10 paths is a
good answer; 806 URLs at 806 paths is not. The path count is the whole point.

## Predictions — the four that exist

| test | fires on | when it fires, median paths | held |
|---|---|---|---|
| `url` | **≥ 20 of 29** | **≤ 12** | |
| `email` | **≤ 8 of 29** | **≤ 4** | |
| `date` | **12–20 of 29** | **≤ 10** | |
| `empty` | **≥ 25 of 29** | **≥ 25** | |

**`empty` is predicted to be the weakest of the four and to fail on
discrimination rather than on coverage.** It is the one test that is not about
what a value *is*: null, `""`, `[]` and `{}` are four different facts about a
document glued together by a shared shape, and every one of them is common. I
expect it to fire almost everywhere and to name so many paths on the large
documents that a reader learns nothing. **If that is right, the repair is not
deletion** — the probe already prices emptiness per candidate, so the question
becomes whether `find("empty")` is saying anything `fathom()` did not.

**`email` is predicted to be the narrowest and I expect it to survive anyway.**
Coverage is the wrong axis for it: it is the one test whose *absence* of a hit
is worth as much as a hit, because a document that should carry contact
information and does not is a finding.

**`date` is predicted to miss dates that are present.** `ISO` is anchored at
`^\d{4}-\d{2}-\d{2}`, so an epoch integer is not a date to it and neither is
`Tue, 14 Aug 2026`. I predict **≥ 3 documents contain a time that `date` does
not find**, and that at least one of them is a document where a person's whole
question is *when*.

**`url` is predicted to be the strongest and the least interesting.** It will do
well on both axes and teach nothing, because it was the word's original example
and the fold was built against it.

## Predictions — what a fifth test would be

Ranked by what I expect the corpus to support. Each is a guess and the point of
writing them down is that most of them should be wrong.

| candidate | what it catches | fires on |
|---|---|---|
| **`number`** — a numeral written as a string | `"1.4"`, `"00123"`, `"3"` | **≥ 8 of 29** |
| **`when`** — a time in any notation, incl. epoch | widens `date` rather than joining it | **≥ 20 of 29** |
| **`packed`** — a list or object inside a string | **this is DEFECT 26**, open since 2026-08-10 | **≥ 4 of 29** |
| **`id`** — uuid, sha, hex digest, opaque key | `"sha512-…"`, `"a3f…"` | **≥ 10 of 29** |
| **`version`** — semver and its neighbours | `01`, `13`, `20`, `23`, `24` at least | **≥ 6 of 29** |
| **`text`** — prose rather than a token: has spaces, long | the thing `28-home-assistant-i18n` is entirely made of | **≥ 15 of 29** |

**The one I most expect to be justified is `number`**, and not because it is
common. It is the only candidate that names a **defect in the document** rather
than a category of content — a numeral written as a string is a schema mistake,
and finding them is the kind of thing a person opens an unknown file to learn.
`url` and `email` tell you what is there; `number` tells you what is wrong.

**`packed` is the one I expect to be most valuable and least measurable.**
Defect 26 says the probe calls these fields text *because they are text*, so a
regex will over-fire on any prose containing a comma. I predict it fires on
**more than 4 documents by the naive test and on fewer than 4 by a strict one**,
and that the gap between those two numbers is the finding.

**`text` is predicted to be the one that looks good and should be rejected.** It
will fire almost everywhere, which is `empty`'s failure again — and
`28-home-assistant-i18n` is the document where fathom already loses, so a test
that fires on all of it adds nothing to the case.

## What would change the vocabulary

**Nothing here can add a word.** `find` takes a NAMED test, so a fifth test is a
new *argument*, not a new word — which is exactly why the set can be argued from
evidence at all. `design/vocabulary.md`'s seven are untouched by any outcome
below.

**What it can do is retire one.** If `empty` fails discrimination on the large
documents and says nothing `fathom()` has not already priced, that is an
argument for three tests and not four, and it would be the first time this
project removed something rather than added to it.

## The result, 2026-08-14 — five of eight numbers, and BOTH judgements wrong

Run by `design/find-tests.py` over all 29 documents. Full numbers and what they
mean live in `FINDINGS.md`, 2026-08-14; this section scores only the
predictions above.

### The four, scored

| test | predicted fires | got | predicted median | got |
|---|---|---|---|---|
| `url` | ≥ 20 | **20** ✓ | ≤ 12 | **8** ✓ |
| `email` | ≤ 8 | **7** ✓ | ≤ 4 | **8** ✗ |
| `date` | 12–20 | **18** ✓ | ≤ 10 | **6** ✓ |
| `empty` | ≥ 25 | **21** ✗ | ≥ 25 | **17** ✗ |

### The two judgements, both refuted

**"`empty` is predicted to be the weakest of the four and to fail on
discrimination rather than on coverage."** **WRONG on both halves.** It is
mid-pack — 21 of 29, median 17, worst 470 — and it is the ONLY shipped test
that says anything about `07-graphql-introspection`, where the other three are
all zero.

**"`url` is predicted to be the strongest and the least interesting… it will do
well on both axes and teach nothing."** **WRONG, and it is the run's finding.**
`url` names **11,320 folded paths on `29-mdn-browser-compat`**, 79.8% of them
covering a single value each. The O(data) failure the word exists to name is
committed by the test I predicted would be dull.

> **The reasoning that produced both errors was the same and is worth naming.**
> I ranked the tests by how *pervasive* their subject matter is — nulls are
> everywhere, URLs are well understood — and discrimination does not follow
> from that at all. **It follows from the DOCUMENT**: drop entry 29 and every
> test on every remaining document stays under 500 paths. I was grading the
> tests when the axis was separating the corpus.

### The candidates, scored

| candidate | predicted | got | |
|---|---|---|---|
| `number` | ≥ 8 | **23/29** | ✓, and far past it |
| `when` | ≥ 20 | **20/29** | ✓, exactly |
| `packed` | naive > 4, strict < 4 | **21 and 3** | ✓ **as stated** |
| `id` | ≥ 10 | **13/29** | ✓ |
| `version` | ≥ 6 | **21/29** | ✓ |
| `text` | ≥ 15 | **25/29** | ✓ |

**Six of six on the candidates and two of four on the tests that exist**, which
is the opposite of what the exercise was set up to expect. Guessing what a
regex will find in unseen documents turned out to be easy; guessing which of
four well-understood tests would embarrass itself turned out to be beyond me.

**`text` is the one result that argues with itself.** Predicted to *"look good
and be rejected"* for firing everywhere — it fires on 25 of 29 — and on
`28-home-assistant-i18n`, where all four shipped tests are silent, it names
1,048 paths against the next test's 21. That is the document where `VERDICT.md`
records that fathom loses to four competitors. **The prediction and its stated
ground both held, and the conclusion drawn from them does not follow.**

### What is NOT settled, deliberately

No test was added and none retired. `date`'s blindness to epoch time is the
strongest case in the run for a change — `25-usgs-quakes` writes epoch
milliseconds and `date` finds nothing where `when` finds 21,771 values — and
one document is one document. **That is the bar item 13 and defect 24 are both
still waiting at.**

## The prior run this repeats, and how it differs

`design/where.py`'s four were chosen on 2026-08-09 by writing down what a person
might search for. **They have never been run against the corpus as a set** — the
harnesses pass individual names to check parity, which is a different question.
`test/parity.py`'s `WHERE_CASES` names 8 pairs across 7 documents; this is 4
tests across 29.
