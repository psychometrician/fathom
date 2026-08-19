# The probe, sketched by hand

**What this is.** The ideal output of fathom's one orienting verb, for
`corpus/01-npm-registry`, written on 2026-08-08 **before any code exists**. It is
an experiment, not a specification: if this page reads well, the product is real
and Phase 2 is earned. If it cannot be written, no quantity of corpus or grid
will rescue it, and that is a finding.

**Every number below is measured**, not invented. Nothing here was rounded to
look tidy.

---

```
> fathom("express.json")

  786 KB · valid JSON · read whole file · UTF-8, no BOM
  no duplicate keys · no NaN or Infinity · no integers past 2^53

  STRUCTURE                                       18 fields at the top level

    name license homepage description _id _rev    text
    readme readmeFilename                         text, present but empty
    keywords                                      [10 text]
    contributors maintainers                      [7] [5] of {name, email}
    author bugs repository                        {2 fields each}

    dist-tags       {2 keys}      keys may be data — undecidable, see below
    versions        {288 keys}    KEYS ARE DATA   "1.0.0" … "5.1.0"
    time            {320 keys}    KEYS ARE DATA   the 288 above, +30 more,
                                                  + created, modified
    users           {2,648 keys}  KEYS ARE DATA   username -> true

    versions.<version>            40 fields seen, only 9 in all 288
      always      _id author contributors description directories dist
                  keywords name version
      sometimes   engines(287) dependencies(284) _npmVersion(280) scripts(273)
                  repository(263) devDependencies(256) … funding(7)
                  _resolved(6) modules(4)
      dependencies    {44 names}  KEYS ARE DATA
      devDependencies {32 names}  KEYS ARE DATA
      scripts         {8 names}   KEYS ARE DATA
      engines         {1 key}     structural: node

  6 levels deep · 25,044 distinct paths · about 40 logical fields

  ONE ROW COULD BE
    the package                1 row
    a released version       288 rows x 140 cols    60% of cells empty
    a dependency edge      4,645 rows x   7 cols    name repeated 4,645x
    a release event          318 rows               30 have no version object
    a user                 2,648 rows

  HOW THE KEYS-ARE-DATA CALLS WERE MADE
    dependencies, devDependencies, scripts   284/253/265 sibling copies exist
                                             and share few keys (0.37/0.39/0.42)
    engines                                  287 copies, all share one key (1.00)
    versions, time, users                    only ONE copy each, so the sibling
                                             test cannot run. Called data on key
                                             count alone: 288, 320 and 2,648 are
                                             not field lists.
    dist-tags                                2 keys, one copy. Nothing separates
                                             it from author{name,email}. Not called.
```

---

## What each part is doing, and why it is there

**Health is the first line, and it cannot be skipped.** There is no such thing as
a broken data frame, so nothing in the rectangular world prepares you for a
document that is truncated, double-encoded, or full of `NaN` that Python wrote
and R will refuse. Putting health in a separate verb means people run it after
they are already confused. Here it costs one line when the file is fine.

**The structure is folded, and the fold is reported.** 288 sibling objects
collapse to one description. This is the whole difference between a listing at
25,044 paths and an answer at 40 fields. But the 288 version keys **are data**, so
a probe that silently folded them would hide exactly what makes this file hard —
which is the error DuckDB commits today, reporting 18 tidy rows while concealing
a 378,036-character type inside one cell.

**The fold reports raggedness rather than averaging it away.** "40 fields seen,
only 9 in all 288" is the honest summary. A schema that listed 40 fields flat
would imply a rectangle that does not exist, and 60% of that rectangle is empty.

**Candidate rows are priced.** This is the part no existing tool offers. "288
rows, 60% empty" and "4,645 rows, `name` repeated 4,645 times" is guidance on how
to parse, in a form anyone can act on immediately. It also makes visible
something the corpus notes had not: **the cost of rectangling changes in kind
with the row you choose** — shallow rows give you holes, deep rows give you
duplication, and the document tells you neither.

**The probe shows its work.** Every keys-are-data call is a guess, and the last
block says which evidence produced it. This is not humility for its own sake: the
measurement below shows no signal is reliable, so a probe that asserted silently
would be confidently wrong on some file, and the user would have no way to know.

## What the sketch found that the corpus notes had not

**`users`, a 2,648-key object, was never mentioned.** `NOTES.md` names five
keys-as-data sites; `users` is the largest in the file by key count and was
missed by hand. A probe that had existed on day one would have surfaced it
immediately, which is a small piece of evidence for the whole idea.

**The 288 version objects have 40 distinct key-sets, not one shape.** Any fold
that reports "288 objects of the same shape" is false on this file.

**`engines` is not keys-as-data.** `NOTES.md` lists it among the sites where keys
are data; it has exactly one key, `node`, in all 287 objects that carry it. The
sibling test corrects the hand grading.

## What is unresolved

**The keys-as-data signal does not generalise, and this is the sketch's main
negative result.** `FINDINGS.md` proposed that structural keys repeat across
sibling instances and data keys do not, and called it the first thing to try.
Measured here it separates cleanly **where it can run** — 0.37, 0.39 and 0.42 for
the data sites against 0.57 to 1.00 for the structural ones — and it **cannot run
on the three biggest cases in the file**, because `versions`, `time` and `users`
each occur exactly once and have no siblings to compare against.

The obvious alternative, value homogeneity, fails in both directions: it scores
`author{name,email}` and `engines{node}` as data-like at 1.00, and it scores
`versions` at 0.08 — calling the single largest data site in the document
structural, because its 288 values are too ragged to look alike.

So the probe needs **key count as a fallback where there are no siblings**, which
is a crude proxy that resolves 288, 320 and 2,648 and cannot resolve `dist-tags`
at 2. **That is why the probe reports evidence rather than asserting.**

**Open, and deliberately not settled here:**

- Whether the one verb is called `fathom()`. It reads well in R and
  `fathom.fathom(x)` does not read well in Python.
- What this output becomes when the file does not fit in memory. The probe must
  state what it read and what it therefore cannot claim.
- Whether `dist-tags` should be called, guessed, or left undecided. The sketch
  leaves it undecided, which is honest and may be annoying.

## The test, run 2026-08-08: it did not survive unchanged

Mechanised as `design/probe.py` and run against two documents with strong domain
conventions it knows nothing about — a `package-lock.json` v3 and an executed
Jupyter notebook. **Three defects, all found by running it, none visible on
paper.**

**1. The probe was O(data), which is the thing it exists to prevent.** 1,239 lines
on the 786 KB file, because `candidates()` recursed into raw values and emitted a
row candidate per version. **The fold is not a display step.** Anything computed
from raw values rather than from the folded structure is proportional to the data
no matter what it prints. Fixed: 1,239 → 73 lines.

**2. The fold was decided per instance, but data-ness is a property of the
aggregate.** `peerDependenciesMeta` holds one to five keys per copy and about
thirty across copies, so it never folded and the output grew with the data. The
aggregate is only visible once the container above it folds, so the fold has to
be a **fixed point**: walk, fold what now looks like data, walk again.

**3. The health check cried wolf.** `NaN` was counted by regex over the raw text
and fired ten times on the notebook by matching the string `"NaN"` in legitimate R
output. Now counted on parsed values.

### After the fixes

| file | size | distinct paths | output |
|---|---|---|---|
| npm registry | 786 KB | 25,043 | 73 lines |
| package-lock v3 | 523 KB | 11,716 | 40 lines |
| Jupyter notebook | **10.5 MB** | 43 | **30 lines** |

**The largest file produces the shortest output.** That is the O(structure) claim
demonstrated rather than asserted.

With no format knowledge it rediscovered nbformat — `cells[]` is 69 copies with
`always cell_type id metadata source` and `sometimes outputs(41)` — and described
`outputs[]` correctly as one record with a discriminator and three shapes, priced
at 62% empty. It priced the lockfile at **998 rows × 978 columns, 99% empty**.

### The result that vindicates the domain-blind decision

**`engines` is structural in the npm registry document and data in the
package-lock.** In npm's file it holds exactly one key, `node`, in all 287 copies.
In the lockfile it varies across 614 copies at 0.17 overlap. Both verdicts are
right.

> **Data-ness is a property of the document, not of the format.**

A format table saying "engines is a record" would be wrong on one of these two
files. No domain parser could get both right; a domain-blind measurement gets both
right for free. See `README.md`, "A diverse corpus and a domain-blind tool."

### Still owed

File 02 proper, an LLM or agent trace — ragged and polymorphic where all three of
these are keyed or regular. And the closed-vocabulary boundary stands: `data{text/
html, text/plain}` and `dist-tags{latest, next}` are data-as-keys that are
structurally records, and the probe reports them undecided rather than guessing.
