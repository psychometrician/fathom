# Can `into` enter an unnamed container? — predictions, recorded before measuring

**2026-08-14.** `design/vocabulary.md` carries this as its one recorded
limitation on `into`:

> **`into` descends by NAME only**, so a document that wraps its records in a
> bare array cannot be entered: `16-movie-ratings` is `[{38 movies}]`. Its 38
> are reachable through the menu as `an entry of $[]` […] Whether `into` should
> be able to enter an unnamed container is an open question and is **not**
> answered here.

`VERDICT.md` lists it as open and unanswered. Predictions first, under rule 1.

## What `at()` actually does, read from the source before predicting

This is the instrument, not the answer, and it is stated so the predictions are
not mistaken for blind ones. `fathom-core/src/extract.rs::at` has four cases:

| standing on | `into("x")` means |
|---|---|
| an object **with** an `x` | that value |
| an object **without** an `x` | every value's `x`, gathered — a keyed collection |
| **an array** | **every element's `x`, gathered** |
| a scalar | an error |

**So an array is not refused.** It is descended THROUGH, by naming a field of
the things inside it.

## Predictions

| # | prediction |
|---|---|
| **P1** | the root is a bare **array in 3 to 7** of the 29 documents |
| **P2** | **THE RECORDED LIMITATION IS NARROWER THAN WRITTEN.** `into` CAN enter an array-rooted document by naming a field of its records, because the array branch gathers. Specifically, `into("<a movie title>")` on `16-movie-ratings` **works** |
| **P3** | **the real gap is that the only names on offer are DATA keys.** On at least 3 documents, every name `into` accepts at the root is a data key — a movie title, a package name — so there is no expression that survives the next file. That is question 14 failing, not question 8 |
| **P4** | where scoping works it pays: **at least 10x** on the largest documents, matching the 66x already recorded for `--at webassembly` on `29-mdn-browser-compat` |
| **P5** | **on an array root, `into` cannot narrow to ONE record** — it gathers the named field across every element — so the saving is small. Predict **under 2x** for array-rooted documents |

> **P5 is the one worth the run.** `into` is documented as *"the performance
> mechanism rather than a convenience"*, because scoping the analysis is the
> only saving available. **If entering an unnamed container gathers rather than
> narrows, then `into` is not merely awkward there — it does not do the job it
> exists for**, and that is a sharper statement of the limitation than "cannot
> be entered".

## What I expect the answer to be, stated so it can be wrong

**That the question as posed — should `into` enter an unnamed container — is
the wrong question.** It already can, by name. What it cannot do is *narrow*
there, and it cannot offer a name that means the same thing in the next file.
**If that is right, the repair is not a new capability in `into` but either a
positional word or an admission that array-rooted documents are scoped by
`rows()` and not by `into`.**

## What would make this worthless

**If `into` genuinely refuses array roots outright**, the recorded limitation
stands exactly as written, the measurement adds nothing, and the open question
is unchanged. Recorded in advance so that outcome is a finding rather than a
disappointment.
