# The menu label is not a navigable name — predictions, recorded before measuring

**2026-08-14.** `design/vocabulary.md` has carried this since earlier today and
says of it: *"Not repaired, and the repair is not obvious. Three candidates,
none measured… It wants measuring rather than arguing."* This file records what
is expected before the measuring, under rule 1.

## The defect, restated

```
ONE ROW COULD BE
  an entry of versions                  288 rows x  140 cols
  an entry of dependencies            4,645 rows x    2 cols
```

| | |
|---|---|
| `rows("an entry of dependencies")` | **works from the root.** The label names a row shape ANYWHERE and the fold resolves it |
| `into("dependencies")` | **refuses.** `dependencies` is not a field of `$`; it lives under `versions` |

Confirmed at the CLI before predicting: `--at versions` succeeds and
`--at dependencies` gives `fathom: no dependencies at $`.

## The three candidate repairs, as recorded

- **A** — the menu prints the PATH it found each candidate at, so
  `an entry of dependencies` reads `versions.*.dependencies`. **Costs width on
  every line of the most-read output in the project**, against `WIDTH = 92`.
- **B** — `into()` accepts a label and jumps.
- **C** — the two lists are made visibly separate on the page.

## Predictions

| # | prediction |
|---|---|
| **P1** | **360–420 candidates** across the 29 documents. `test/candidates.py` counted 350 over 28 before entry 26 joined |
| **P2** | **a MINORITY of labels are `into()`-navigable from the root — 25% to 45%.** Candidates come from the fold, which finds row shapes at every depth; only those directly under `$` can be navigated to by name |
| **P3** | **at least 20 of the 29 documents carry at least one non-navigable label.** The defect is ordinary, not exotic |
| **P4** | **`the whole document` is navigable in every document**, trivially, and appears in all 29 |
| **P5** | the median path behind a candidate is **short, under 20 characters**, and the worst is long — **over 50** on `09-stripe-openapi` or `29-mdn-browser-compat` |
| **P6** | **printing the path would push a line past `WIDTH = 92` on at least 3 documents** |
| **P7** | **at least 5 documents have a candidate whose NAME lives at two or more paths.** Defect 34 already measured 159 self-nested names corpus-wide, so B has a CORRECTNESS problem and not only an ergonomic one — a label it accepted would be ambiguous about where to jump |

> **P7 is the one that would decide it.** A and C are about how the page reads;
> **B is about whether `into()` can even be given a label unambiguously.** If a
> meaningful number of labels resolve to more than one path, B is not a design
> choice that costs width — it is a repair that cannot be specified, and the
> question collapses to A against C.

## What I expect the numbers to argue, stated so it can be wrong

**That the ambiguity is about KIND rather than LOCATION**, and therefore that A
is the wrong trade. `rows()` already resolves every label it is given; a reader
who is shown a path learns where the thing lives but not that the word after
`of` belongs to a different verb. **A pays width on every line of every report
to deliver a "no" to the minority of readers who were going to type `into()`.**

**And the honest alternative to all three is that the menu is not the problem.**
It is a menu FOR `rows()`. Nothing on the page claims it is a list of names
`into()` will take; the binding test assumed that, and so would a person, which
is what makes it a defect rather than a misunderstanding. **A fourth candidate —
say so in the page's own words — is not in the recorded three and should be
considered if the measurement supports it.**

## What would make this measurement worthless

**If nearly every label turned out to be navigable**, the defect would be a
curiosity affecting a handful of lines and none of the three repairs would be
worth its cost. Recorded in advance so that outcome is a finding rather than a
disappointment.
