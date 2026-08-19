# The document-shape axis — predictions, recorded before it was run

**2026-08-11.** `corpus/README.md` has carried `column-oriented` as an open gap
since 2026-08-09, and its own diagnosis is that the gap is not a missing file:

> Every axis the corpus grades reported that file as trivial — `0/0` ragged, no
> recursion, no polymorphism, one row shape — and it defeated the probe
> completely […] **The axes measure how ragged a document is and this one is
> about what a document is shaped like.**

`README.md` calls the axes a primary output of this project and sets the bar:
**an axis that never separates two files is not an axis.** This file records what
the new one is expected to do *before* it is run, under rule 1, because the whole
value of the exercise is that it could come out the other way.

## What is being measured, defined without reference to any corpus file

**A record-oriented document puts one object per row.** `[{a:1,b:2},{a:3,b:4}]`
— the values for one row live together, and the field names are repeated once
per record.

**A column-oriented document puts one array per field.** `{a:[1,3],b:[2,4]}` —
the values for one FIELD live together, and a row is a POSITION shared across
sibling arrays. The field names are written once.

So the structural signature is: **an object with two or more sibling values that
are arrays of scalars, all of the same length.** The detector reports the site,
how many parallel arrays it holds (the width) and how long they are (the implied
row count), and it decides nothing — a reader with the width and the length can
judge a coincidence for themselves.

**Deliberately NOT part of the definition:** whether the arrays' names look like
column names, and whether one of them holds the names of the others. This
project refuses lexical rules, and `06-espn-qbr` is the case that shows why —
a same-length decoy sits beside the real name array and nothing but the meaning
separates them.

## Predictions

| | prediction |
|---|---|
| **P1** | **`08-open-meteo` fires, and hardest.** `README.md` already records it as *336 rows, transposed*, with a header invented out of a timestamp column. I expect one site of width ≥ 4 and length 336 |
| **P2** | **`06-espn-qbr` fires**, because `corpus/README.md` calls it the dangerous variant where the names live in a parallel array with a same-length decoy beside it. I expect a NARROWER site than Open-Meteo's — width 2 or 3 — and this is the prediction I am least sure of, because ESPN may nest its arrays one level apart rather than as siblings, in which case it does not fire at all |
| **P3** | **The two GeoJSON files do NOT fire.** `03-natural-earth` and `25-usgs-quakes` hold `coordinates` as ONE array of arrays, not as two or more sibling scalar arrays, and `bbox` is a lone array of 6 |
| **P4** | **The keyed-object documents do NOT fire** — `01-npm-registry`, `09-stripe-openapi`, `13-package-lock`, `24-cargo-metadata`. Keys-as-data is the opposite failure and the axes already have a column for it |
| **P5** | **THE AXIS SEPARATES.** At least one entry fires and the majority do not. If every file fires, the detector is measuring coincidence; if none does, it is measuring nothing. Either would fail README's bar |
| **P6** | **There will be FALSE POSITIVES on short arrays**, where two unrelated fields are the same length by chance. I expect a handful at length 2–3, and I expect them to be obvious from the reported length rather than needing a rule |

## What would sink it

**If more than about half the corpus fires, the measurement is not an axis** —
it is a coincidence detector, and the honest outcome is to report that and NOT
add the column. Recorded here so that result is a finding rather than something
to be tuned away.

---

## The result, 2026-08-11 — it is an axis, and it cannot tell a table from a duplicate

### The predictions, scored

| # | | outcome |
|---|---|---|
| **P1** | `08-open-meteo` fires hardest, width ≥ 4, length 336 | **✓ exactly** — `$.hourly` at **5x336**, and the five are `time`, `temperature_2m`, `wind_speed_10m`, `wind_direction_10m`, `relative_humidity_2m` |
| **P2** | `06-espn-qbr` fires, narrower — the one I was least sure of | **✓** — `$.categories[]` at **4x10**: `labels`, `names`, `displayNames`, `descriptions`. My width guess of 2–3 was low |
| **P3** | neither GeoJSON fires | **✓** — `03` and `25` both 0 |
| **P4** | the keyed-object documents do not fire | **✗ WRONG on two of four.** `01` and `13` are 0 as predicted, but **`09-stripe-openapi` fired 29 times** and `24-cargo-metadata` three |
| **P5** | the axis separates | **✓** |
| **P6** | false positives on short arrays | **✓, and far worse than I expected** |

### P6 was right and my sink condition was the WRONG TEST

The condition recorded in advance was *"if more than about half the corpus
fires."* **Nine of 25 fired — 36%, comfortably passing — and inspection showed
SEVEN OF THE NINE were not tables at all.** The test counted how many files fire
and the thing that matters is how many HITS ARE REAL. That is recorded as an
error in the experiment's design rather than quietly replaced.

### What the false positives actually were, and they are two different failures

**Coincidence, killed by asking whether the property is TYPICAL.** The first
version aggregated by path with `max` across every instance, so one lucky record
set the number:

| | reported | property holds at |
|---|---|---|
| `20-homebrew-formulae` | `5x43` | **8.6%** of 8,536 formulae |
| `18-openfda-events` | `6x878` | **91.3%** of 208 instances |

**Indistinguishable without a third number**, and *is this typical or an
outlier* is the same question every other axis in `axes.py` already asks — so
consistency was added. **It was added AFTER the first run and the docstring says
so.** With it, and a length floor of 4, the nine firing files become **four**.

**Duplication, and NOTHING structural kills it.** `09-stripe-openapi`'s
`required` and `x-expandableFields` are both length 21 **and hold identical
values**, at 100% consistency across 7 sites. That is *perfect* positional
alignment and it is not a table — it is one list written twice.

> **So the axis has the same shape of limit `README.md` already records for path
> variance by renaming.** Equal length is necessary and nowhere near sufficient;
> what makes parallel arrays a table is that **position means the same thing in
> each**, and that is semantic. The difference is that renaming has **no**
> instrument and this has a partial one.

### The verdict

**It is an axis** — 4 of 25 against 21, which clears `README.md`'s bar that an
axis never separating two files is not an axis. **And it found, independently
and from a definition written without reference to any file, exactly the two
documents `corpus/README.md` already names as column-oriented.** That is the
validation, and it is worth more than the two it added.

**Three numbers are required and any one alone misleads**: width, length, and
consistency. `24-cargo-metadata` is `2x2@100%` — perfectly consistent and
meaningless. `20-homebrew-formulae` is `5x43@9%` — wide, long, and an outlier.
