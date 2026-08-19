# 15 — GitHub issues and pull requests

## The expectation, written 2026-08-09 before the probe was run

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   a9e17af043495be40867a277485a4287385d94b8
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Disclosure

*Of the specimen.* **Three facts: it is a JSON array, it holds 100 objects, and
it is 702,018 bytes.** No field name read, no value seen.

*Of the instrument.* None read for this file.

*Of prior knowledge, and it is substantial.* I know GitHub's issue schema
without looking — `user`, `labels[]`, `assignees[]`, `milestone`, `reactions`,
`pull_request`, `state` — and that a pull request is returned by this endpoint as
an issue carrying an extra `pull_request` key. **Predictions 1 and 2 lean on that
heavily and should be discounted.** This is the same exposure file 14 had.

### Why this file — the second ordinary one, and the gate is why

**`14-nyc-311` found nothing and put the gate counter at 1 of 3.** Two more quiet
files close it, and `design/implementation.md`'s gate is the thing that decides
whether the Rust port happens. So this is again chosen to be **representative
rather than adversarial**, for the reason file 14 records: a document picked to
break the newest constant is guaranteed to find something and therefore cannot
measure convergence.

**It is deliberately unlike file 14 in shape.** NYC 311 is a flat table export —
depth 4, explosion 1.0, the dullest document in the corpus. This is the other
ordinary case: **a nested API response**, which is what most people who touch
JSON actually parse. The corpus is heavy on specifications and exports and thin
on the everyday API payload; `06-espn-qbr` is the only other one.

**It fills no "Wanted" gap.** The two open gaps are *broken/truncated* and
*scale*. Stated rather than glossed.

### What is predicted

**1. Ragged by NULL, not by absence — the reverse of file 14.** GitHub emits
`null` for an absent scalar rather than omitting the key, so a closed issue and
an open one carry the same key-set with different fill. Predicted: null high,
absence low, matching `07-graphql-introspection` and opposite to
`14-nyc-311`'s 35/50-and-0. **If it comes out the other way, my knowledge of this
API is worse than I think and the prediction was the risk.**

**2. No split, and the reason is a genuinely new one worth naming.** This
endpoint returns **two kinds of thing** — issues and pull requests — and a pull
request is an issue with an extra `pull_request` key. That is real key-set
raggedness with a real discriminator, **except the discriminator is the PRESENCE
of a key rather than the VALUE of one.** `discriminator()` requires a field
present in every instance whose *value* partitions the key-sets, and no scalar
here encodes issue-versus-PR.

> **Predicted: the probe finds no split on a document that genuinely has two
> kinds, because the thing that separates them is a key's presence.** That is
> distinct from `04-gharchive`'s discriminator-on-the-parent and from
> `10-wikidata`'s one-level-apart case. If it fires anyway, on `state` or
> `author_association`, that is a false positive of the kind `13-package-lock`
> just produced and the `KIND_MAX` repair did not cover.

**3. keys-as-data 0.** GitHub uses fixed field names throughout; `reactions` has
a closed key set and should be *undecided* rather than data, which is
`VOCAB_GROWTH`'s job and would be its first held-out firing.

**4. Depth 5 or 6, recursion 0.** `user` and `milestone.creator` are nested
objects; `labels[]` holds objects. Nothing self-similar.

**5. Polymorphism 0 or 1.** A typed API. If anything varies it will be a field
that is an object on some records and `null` on others, which `axes.py` counts as
ragged-by-null and not as polymorphism — **and the probe's report should agree
with `axes.py` now that defect 11 is repaired.** That agreement is worth
checking; it is the first held-out test of that fix.

**6. Under 100 lines, and one or two row candidates.** The honest answer is one
row per issue, 100 rows.

**7. `rows("*")` returns 100 rows** with list-columns at `labels` and
`assignees` — its known defect, fourth or fifth instance.

**8. Memory well under 100 MB.** 702 KB at file 14's 8.2× would be 6 MB of
objects; the floor is the interpreter. This is a control on the scale reading
rather than a test of it.

---

## Provenance

| | |
|---|---|
| what | **`pandas-dev/pandas` issues and pull requests**, most recent 100, any state |
| source | `api.github.com/repos/pandas-dev/pandas/issues`, see `fetch.sh` |
| fetched | 2026-08-09 |
| size | 702,018 bytes, **100 records**, committed |
| chosen from | this, OpenLibrary search (65 KB), openFDA drug events (2.9 MB) — GitHub for being the most ordinary of the three |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers, no
encoded documents. **0.6 s, 84 MB resident, 44 lines of output.**

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 702,018 · depth **4** · paths 179 · fields 76 · explosion 2.4 |
| keys-as-data | **0** · ragged by absence **5/176** · ragged by null **7** |
| recursion | 0 · polymorphic **0** · heterogeneous 1 · path variance 27 · row shapes 3 |

## Prediction scorecard: six of eight

| # | predicted | outcome |
|---|---|---|
| 1 | ragged by null, not by absence — the reverse of file 14 | **confirmed. 7 null against 5/176 absence, where file 14 was 35/50 and 0** |
| 2 | no split, because the discriminator is a key's PRESENCE | **no split confirmed — but the reason is only half right, see below** |
| 3 | keys-as-data 0; `reactions` not called data | **confirmed, both** |
| 4 | depth 5–6, recursion 0 | **depth 4 — WRONG. Recursion 0 confirmed** |
| 5 | polymorphism 0 or 1, and the probe agrees with `axes.py` | **confirmed. 0, and they agree — first held-out test of defect 11's repair** |
| 6 | under 100 lines, one or two row candidates | **44 lines. Three candidates, so half wrong** |
| 7 | `rows("*")` → 100 rows with list-columns | **confirmed. 100 × 37** |
| 8 | memory well under 100 MB | **confirmed. 84 MB** |

## What the file established

### 1. NO DEFECT — the gate counter is at 2 of 3

**Nothing here needs repairing.** With `14-nyc-311` this is the second
consecutive quiet file, and `design/implementation.md` wants three.

### 2. The silence is correct, and for a reason the prediction did not contain

Prediction 2 named the right outcome and only half the reason. The document
genuinely holds **two kinds** — 84 pull requests and 16 issues, since this
endpoint returns a PR as an issue carrying an extra `pull_request` key:

```
$[]   100 copies · 36 fields · 2 distinct key-sets
  sometimes  pull_request(84) draft(84) sub_issues_summary(16) …
```

**And `discriminator()` cannot see it, because what separates the two kinds is a
key's PRESENCE rather than any scalar's VALUE.** `state` is present on all 100
and takes `open`/`closed`, which has nothing to do with shape.

**But measuring the split it cannot see shows it would be refused anyway:**

```
fold emptiness 18.5%  ->  a split must leave the worst group at 9.3% or less
split by presence of pull_request:  PR 84 @ 10%,  issue 16 @ 12%   worst 12%
```

**12% is not half of 18.5%, so the halving rule rejects it.** The probe reaches
the right answer, and the second reason is the one that actually decides. Had the
prediction stopped at *"it cannot see presence-discriminators"*, this entry would
have recorded a defect that is not there.

> **Presence-as-discriminator is still a real gap in operation 4** — it is
> distinct from `04-gharchive`'s discriminator-on-the-parent and from
> `10-wikidata`'s one-level-apart case — **but this document does not
> demonstrate it costing anything.** A file where the presence split *does* halve
> the holes would, and the corpus does not have one.

### 3. First held-out confirmation that defect 11's repair holds

The probe prints no `FIELDS THAT CHANGE TYPE` section and `axes.py` grades
polymorphic **0**. Before 2026-08-09 the probe counted a null as a type and the
two instruments disagreed on `11-jupyter-notebook`. **They agree here, on a
document neither was fitted against.**

### 4. `VOCAB_GROWTH` had a candidate and correctly did not need to fire

`reactions` carries a closed vocabulary — `+1 -1 confused eyes heart hooray laugh
rocket total_count url` — which is the `dist-tags` shape. It was not called data,
and not because the new rule caught it: all 100 copies share all ten keys, so
sibling overlap is high and the old test already called it structural. **The
saturation rule is for the case where copies do NOT share keys**, and this file
did not produce one.

## What it disconfirmed

**That a prediction naming the right outcome has named the right mechanism.**
Prediction 2 was scored a hit on the outcome and is half wrong on the cause, and
only measuring the counterfactual split showed which half. **The corpus has been
wrong this way before** — `10-wikidata` recorded *"the discriminator is on the
grandparent"* on the day and had to be corrected by measurement, and
`11-jupyter-notebook`'s prediction 5 was *"right for the wrong reason"*. This is
the third instance, and the lesson each time is the same: reasoning from printed
output is not measurement.


---

## Grading

**The thirteen attempt files are DONE, 2026-08-11** — 5 R + 8 Python, one per
tool, each with its scoring header filled in against what actually printed. The
probe was frozen at `d595d1d2…` throughout and was not re-run.

**This entry is the third of three graded in one day, and the three together are
the result.** `14-nyc-311` has **zero nulls**; `13-package-lock` has
**keys-as-data**; this file has **709 nulls and no keys-as-data**. Each isolates
one variable, and the thirteen tools sort differently under each.

### The document is the absent-vs-null discriminator

Of 36 record fields: **5 are sometimes ABSENT**, **8 are always present but
sometimes NULL**, and **three of those are null on all 100 issues** — `type`,
`active_lock_reason`, `performed_via_github_app`.

> **pandas, polars, DuckDB and simplified jsonlite each report exactly 13**, and
> 13 is 5 + 8. The reported set is the *union*, verified identical. Once a row
> exists, absent and null are the same hole.

**Nine tools separate the two**, each by its own route: `has` (jq, jqr), a `null`
EVENT (ijson), `null` as a TYPE (tidyjson), `names()` vs `is.null()` (purrr,
unsimplified jsonlite), `k in record` vs `record[k] is None` (glom, pydash), and
`keys(@)` plus a per-field predicate (jmespath).

**jmespath belongs with the walkers here**, which corrects the corpus's earlier
placement of it: `[].keys(@)|[]` includes keys whose value is null and reports
the 5 absent fields exactly.

### `count(DISTINCT json_structure)` completes a three-document ladder

| file | DuckDB | probe | |
|---|---|---|---|
| `14-nyc-311` | **153** | 153 | exact |
| `13-package-lock` | **776** | 144 | 5.4x — keys-as-data |
| `15-github-issues` | **14** | 2 | 7.0x — NULLS |

`json_structure` records the TYPE of every value, so `closed_by: null` differs
from `closed_by: {…}`. **jq's `keys_unsorted | sort` returns 2 — the probe's
number — on the same document.** The expression is trustworthy only where there
are neither data keys nor nulls, and nothing signals which case you are in.

### The ghost column is real, and worse than recorded

`VERDICT.md` carried *"pandas' ghost `closed_by` column"* from a note. Measured:
`json_normalize` emits **20 columns** for that one field — an entirely empty
`closed_by` plus 19 populated `closed_by.*`. It cannot expand a null, so it
leaves the scalar column behind and expands the objects into dotted children.
**`milestone`, `assignee` and `pinned_comment` do the same; nine all-NaN columns
in total, of which only three are honestly empty.**

polars and DuckDB build no ghost — one Struct column, 52 nulls.

### Flattening collides, and the three behaviours are one trade-off

`url` appears at the top level and inside six nested objects.

| | |
|---|---|
| **polars `unnest`** | **RAISES** `DuplicateError`. **26 names collide, 58 renames needed.** `25-usgs-quakes` recorded the same failure on 3 columns called `type`; **it generalises to a second document and gets twenty times worse** |
| **DuckDB `struct.*`** | **SILENT.** Returns 19 duplicate column names and raises nothing; converting to pandas then renames them `login` / `login_1`. Two silent transformations stacked |
| **pandas, jsonlite, rrapply, tidyjson** | all **prefix** — `closed_by.login` — and all get it right unaided |

pandas is correct here, and it is the *same* decision that gave it 144 columns
and the ghost.

### An always-empty array is a field that exists and contains nothing

`issue_field_values` is `[]` on all 100 issues. A naive path walk counts
**180**; the probe counts **179**, because an array that never holds an element
has no element path. jq gives 179; ijson gives 180 counting the empty root.
Three conventions, none of them stated by the tool.

### Type-of-null splits the tools a second way

**tidyjson reports 5 fields as carrying more than one type** — `assignee`,
`closed_at`, `closed_by`, `milestone`, `state_reason` — and **the probe reports
none.** All five are null on some issues and a value on others, which
`design/axes.py` and defect 11 both rule is missingness written as a value.
`FINDINGS.md` records tidyjson typing **five** fields wrong on `25-usgs-quakes`
for exactly this reason: **same mechanism, different document, same count.**
pandas' python-type check reports 9 for the same cause.

### Two default-value traps, one in each language

- **`pydash.get(r, "closed_by", "DEFAULT")` returns `None`, not the default**,
  because the key is present holding null. One level deeper,
  `get(r, "closed_by.login", "DEFAULT")` *does* return the default, because
  traversal through a null fails. **Same function, opposite answers.**
- **`purrr::pluck(.default =)` fires for a present-but-null key and an absent
  key identically** — the same blind spot in R.

`FINDINGS.md` records the pydash half on `25-usgs-quakes`; this is its second
document and its R twin.

### The `$` trap has four opportunities here and takes none

`assignee`/`assignees`, `comments`/`comments_url`, `labels`/`labels_url`,
`state`/`state_reason` — **more prefix pairs than either document where it
fired**, and exposure is **0 of 100**, because all four short keys are always
present. `14-nyc-311` had one pair and 199 records exposed; `13-package-lock`
had three and 24. **Partial matching can only fire where the exact key is
ABSENT, so more pairs is not more danger.**

### Question 3, thirteen of thirteen, for the sixteenth graded entry

pandas and tidyjson both build **100 x 144** — the probe's priced candidate —
and neither prints `53% empty`. rrapply's bind goes to 209 columns at 59.5% NA.
**No tool names an alternative or prices one.**

## The fourteenth tool, 2026-08-11 — `try-tidyr.R`

**The written-null split is settled three to one, and purrr is the outlier.**
`milestone` is the perfect test and this document supplies it: **present on all
100 issues and null on 95**, so nothing is absent and everything is written.

| | on a written null |
|---|---|
| purrr `pluck(.default =)` | returns the **DEFAULT** |
| glom `Coalesce` | returns the **NULL** |
| pydash `get` | returns the **NULL** |
| **tidyr `hoist`** | **returns the NULL** — 95 of 100 |

This entry originally recorded purrr and pydash *sharing a blind spot*, and a
later measurement narrowed that to the deep path. **The fourteenth tool makes
purrr the odd one out on the shallow case rather than half of a pair**, which is
the opposite of how the finding was first written.

**The object trap at its clearest.** `unnest_longer(user)` returns **1,900 rows
from 100 issues** — no issue has many users; `user` is an object with 19 fields
and 100 × 19 = 1,900. On `labels`, an array, the same verb counts elements: 166
rows, dropping 40. **Same spelling, two meanings, and nothing in the call
distinguishes them** — the one place tidyr's naming stops paying off.
