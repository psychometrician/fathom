# 13 — an npm lockfile

## The expectation, written 2026-08-09 before the probe was run

Frozen at the moment this was written, and both must still match when the runs
happen:

```
design/probe.py   d04d74a47121b034142f00109b197c16f939ef6e
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Disclosure

*Of the specimen.* Four repositories were tried and three returned 404, so there
was no choosing: this was the only real lockfile available at the size wanted.
Seen: the five top-level keys — `name, version, lockfileVersion, requires,
packages` — `lockfileVersion 3`, and **1,657 children under `packages`**.
Nothing below that has been looked at.

*Of the instrument.* `classify()` was read, because this file was **chosen to
attack it**. That is a large disclosure and it is the point of the choice rather
than an accident of it.

### Why this file — it is chosen to break the newest repair

**This is the first corpus file selected as an adversary rather than to fill a
gap in `corpus/README.md`, and that is a deliberate departure worth stating.**
The remaining wanted gaps are *broken/truncated* and *scale*, and a lockfile
fills neither.

`classify()` gained a rule three hours before this file was fetched — **a
collection keyed by name: ≥ 20 children whose values are all objects sharing
exactly one key-set** — forced by `12-agent-trace`. That rule was fitted against
twelve documents and has never been held out.

**And `classify()`'s own docstring names a lockfile as the case that fooled its
other signal:**

> *"Alone it calls `outputs[]` (0.38) and `packages.<key>` (0.32) data, and they
> are ragged records."*

So a real lockfile is the sharpest available test of the classifier as it now
stands. `packages` is keyed by **install path** — `node_modules/foo`,
`node_modules/foo/node_modules/bar` — which is data, and its values are records
that are **ragged**: some have `dependencies`, some `bin`, some `os`, some
`peerDependencies`. If they turn out to share one key-set the new rule fires and
is right; if they are ragged the new rule must stay silent and the *old* signals
have to carry it.

**Either outcome is informative, which is what makes it worth a held-out run.**

### What is predicted

**1. `packages` is called keys-as-data, and by the OLD signal, not the new one.**
1,657 children whose values are ragged records. Predicted: the sibling test does
it — this is one copy of `packages`, so the single-copy branch with
`n > KEYED_MIN` applies — and **the new one-key-set rule does NOT fire**, because
lockfile entries are ragged. If the new rule fires here, it is looser than it was
written to be and that is a defect.

**2. Keys-as-data ≥ 2 sites**, and possibly many more: `packages`, and then
`dependencies`/`peerDependencies`/`engines` inside each entry, which are keyed by
package name. `01-npm-registry` scored 6 sites and this is the same ecosystem's
other half. **`engines` is the known trap** — `VERDICT.md` records an `engines`
that was reported as keys-as-data and is not.

**3. The install path is the corpus's first genuinely hierarchical key.**
`node_modules/a/node_modules/b` encodes a tree *in the key string*. Nothing in
`README.md`'s axis table describes that, and `12-agent-trace` raised the same
absence for relation-by-reference. Predicted: unmeasured, and worth an axis
discussion rather than a repair.

**4. No split.** Lockfile entries are one kind of thing — a resolved package —
with optional fields, so there is no discriminator. Predicted: **0 splits**, and
this is a false-positive test for the two-kind guard that was relaxed today.
`resolved`, `integrity` and `version` are near-unique per entry and must not be
mistaken for kinds; `dev` and `optional` are booleans present on some entries and
**are** the most plausible false positive.

**5. Ragged by absence, high; ragged by null, near zero.** A lockfile omits.

**6. Recursion 0.** The nesting is in the key string, not in the structure.

**7. Under 150 lines**, and the `└─ or N tables` join silent throughout, since
prediction 4 says nothing splits.

**8. `rows("packages.*")` returns 1,657 rows** with the key column carrying the
install path — `rows()`'s best case for the fourth time, and its list-column
defect should appear again on `dependencies`.

---

## Provenance

| | |
|---|---|
| what | **Visual Studio Code**'s `package-lock.json`, `lockfileVersion 3` |
| source | `raw.githubusercontent.com/microsoft/vscode/main/package-lock.json`, see `fetch.sh` |
| fetched | 2026-08-09 |
| size | 777,210 bytes, **1,657 entries under `packages`**, committed |
| chosen from | four repositories; three commit no lockfile at that path and returned 404 |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers, no
encoded documents. **53 lines of output** for a 759 KB file.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 777,210 · depth **5** · paths **16,545** · fields 27 · explosion **612.8 — the highest in the corpus** |
| keys-as-data | **8** · ragged by absence 21/26 · ragged by null **0** |
| recursion | 0 · polymorphic 2 · heterogeneous 0 · path variance 6 · row shapes 9 |

**Explosion 612.8**, against Wikidata's 398.9 and npm's 353. Sixteen thousand
paths for twenty-seven fields, and the probe answers in 53 lines — which is the
O(structure)-not-O(data) claim at its most extreme so far.

## Prediction scorecard: seven of eight

| # | predicted | outcome |
|---|---|---|
| 1 | `packages` called data by the OLD signal; the new rule silent | **confirmed. `one copy, 1657 keys — not a field list`** |
| 2 | keys-as-data ≥ 2; `engines` is the known trap | **confirmed. 8 sites — and `engines` is the trap, recurring** |
| 3 | the install path is hierarchical and unmeasured | **confirmed. Nothing reports it** |
| 4 | **no split** | **WRONG. `SPLIT ON url — 37 kinds`, and it is a false positive** |
| 5 | absence high, null near zero | **confirmed. 21/26 and 0** |
| 6 | recursion 0 | **confirmed** |
| 7 | under 150 lines, join silent | **confirmed. 53 lines, no `└─` anywhere** |
| 8 | `rows("packages.*")` → 1,657 rows, key carries the path | **confirmed. 1,657 × 22** |

## What the file established

### 1. The adversarial choice paid, and the new rule survived it

**`classify()`'s collection-keyed-by-name rule was written three hours earlier
and had never been held out.** It stayed silent, correctly: lockfile entries are
ragged — **144 distinct key-sets across 1,657 entries** — so the one-key-set
condition never came close. `packages` was caught by the old single-copy branch
instead:

```
$.packages   {1657 keys}   one copy, 1657 keys — not a field list
```

**The rule is as strict as it was written to be.** That is the whole reason for
choosing an adversary, and it is the first of the day's repairs to earn anything.

### 2. DEFECT — `SPLIT ON url` on 37 sponsor URLs, and today's relaxation caused it

```
$.packages.<key>.funding   282 copies · 2 fields · 2 distinct key-sets
  SPLIT ON url — 37 kinds, not one shape. 41% empty folded, 0% after
    https://github.com/sponsors/      83 x 1 cols   0% empty
    https://github.com/sponsors/      55 x 1 cols   0% empty
```

Measured: 282 objects, key-sets `{url}` ×230 and `{type,url}` ×52, disorder
0.408, **37 distinct `url` values against a ceiling of 56**.

**`url` is a sponsor link. It is an identifier, and the probe split a table into
thirty-seven pieces on it.** The reason it is the chosen field is worse than the
choice: `everywhere` — fields present in *every* instance — is `{url}` **alone**,
because `type` is on 52 of 282. There was one candidate and it cleared every
guard.

> **This is the near-identifier hole, and today's `shapes < 2` relaxation is what
> opened it.** Under the old `shapes < 3` rule this returns None: two filled
> key-sets, variation 0. The relaxation was measured on twelve fitted files,
> gained six correct splits, and **the first held-out document it met produced a
> false positive.** That is exactly the asymmetry rule 5 exists to expose.

**What separates it from the good splits is cardinality relative to record
count**, and the current ceiling of `n // 5` is far too generous:

| | discriminator | distinct / records | |
|---|---|---|---|
| `02-hn-thread` | `type` | 2 / 336 = **0.6%** | good |
| `05-fhir-bundle` contained | `id` | 2 / 108 = **1.9%** | good |
| `07-graphql` | `kind` | 4 / 108 = **3.7%** | good |
| `04-gharchive` | `client_id` | 6 / 61 = **10%** | bad, killed by the 0.2 floor |
| **`13-package-lock`** | **`url`** | **37 / 282 = 13%** | **bad, and nothing stops it** |

The 0.2 disorder floor caught `client_id` at 8% disorder. `funding` is at 41%, so
the floor never applies. **Recorded, not repaired** — rule 5.

### 3. DEFECT — `engines` is a closed vocabulary reported as data, confidently

```
$.packages.<key>.engines   {1 keys}   1050 copies share few keys (0.20), values one type
```

Measured, the entire key vocabulary across 1,050 objects:

```
node 1048 · npm 6 · bare 2 · iojs 1 · yarn 1
```

**Five engine names, one of them on 99.8% of instances.** These are field names
from a small fixed set, not data. `VERDICT.md` already records *"an `engines`
that was not keys-as-data"* among the project's early errors, and **it has
recurred.**

**And the new part is which branch reports it.** `classify()`'s docstring names
this limit and accepts it — `dist-tags{latest, next}`, `data{text/html,
text/plain}` — but those reach the **single-copy** branch and are reported
*undecided*, which is honest. `engines` has 1,050 copies, so the **sibling**
branch runs, sees overlap 0.20, and says **data**.

> **The closed-vocabulary limit is not symmetric. With one copy the probe admits
> it cannot tell; with a thousand copies it states the wrong answer.** Each
> object has about one key drawn from five, so low overlap is guaranteed and
> means nothing.

### 4. The install path is a hierarchy inside a key string

`node_modules/a/node_modules/b` encodes a tree in the key itself. `12-agent-trace`
raised the same absence for relation-by-reference, and this is the second
instance in two files: **structure the corpus can see and no axis describes.**

## What it disconfirmed

**That a relaxation validated on the whole corpus is validated.** The two-kind
guard was checked against twelve documents, gained six correct splits, cost
nothing measurable — and broke on the next unseen file. **Twelve fitted documents
did not predict one held-out one**, which is the argument for rule 5 stated as a
measurement rather than as a principle.

**And that the probe's worst output is on its hardest files.** This is the
highest path explosion in the corpus at 612.8 and it produced the shortest report
of any large file — 53 lines. Both defects here are in judgement, not in scale.

---

## Grading

**The thirteen attempt files are DONE, 2026-08-11** — 5 R + 8 Python, one per
tool, each with its scoring header filled in against what actually printed. The
probe was frozen at `d595d1d2…` throughout and was not re-run; this is the tool
half of an entry the probe graded on 2026-08-09.

**This entry is the mirror of `14-nyc-311` and the pair is the point.** Entry 14
had no keys-as-data, no type variation and one row candidate, and all thirteen
tools agreed. This file has **seven keyed sites, two polymorphic fields and eight
priced row candidates**, and the thirteen come apart in every direction.

### What the tools agreed with the probe about

| number | probe | who reproduced it unprompted |
|---|---|---|
| **16,545 distinct paths** | 16,545 | jq, jqr, and the hand-walks in purrr and glom; ijson gets 16,546 with the root |
| **5 levels deep** | 5 | jq, jqr, ijson, tidyjson, DuckDB, polars, purrr, glom, rrapply |
| **144 distinct key-sets** | 144 | **jq and jqr only, and only with `sort`** |
| **engines / funding vary** | both, with counts | jq, jqr, tidyjson, DuckDB, glom, pydash, pandas, purrr (with a hand-written type fn) |

### 16,545 is the right answer and the wrong shape, and that is the entry

Every tool that can enumerate paths gets **16,545**, because every install path
and every dependency name is its own path. Folded on the seven keyed
collections it is **49**. **A ratio of 338 to 1.**

> **Question 1 is only answerable on this file because something folds**, and no
> tool in either language folds. The probe does it unasked and prints
> `KEYS THAT ARE DATA` naming seven sites — and **declining an eighth**,
> `engines`, as a vocabulary rather than data.

### Three libraries, two languages, one 1,390-column monster

The natural "flatten it" verb produces the same catastrophe in three places, and
**not one of them warns**:

| | shape | empty |
|---|---|---|
| pandas `json_normalize` | 1,657 x **1,394** | 99.5% |
| rrapply `how="bind"` | 1,657 x **1,401** | 99.5% |
| tidyjson `spread_all` | 1,657 x **1,391** | 99.3% |
| **`design/probe.py`** | **prices it: `an entry of packages 1,657 x 1394 99% empty`** | |

The probe is the only thing in either language that states the number **before**
you build the thing. pandas will also give `1 x 12,153` from
`json_normalize(doc)` — three different tables from one tool, all one line, and
nothing says which is meant.

### Two refusals and a family of silent losses

| | |
|---|---|
| **DuckDB REFUSES the file** | `InvalidInputException: A table cannot be created from an unnamed struct`. The cause is **one zero-length key** — npm keys the root package `""` — proved by deleting it and re-reading. The message names neither keys nor packages. Its JSON *functions* still work; only the table reader refuses |
| **R cannot reach that same key** | `match("", names(pkgs))` is 1 and **`pkgs[[""]]` is `NULL`**. One pathological key, two tools, one loud failure and one silent one |
| **polars: three routes, three answers** | `DataFrame({'rec':…}).unnest` keeps **7 of 21 fields**; `from_dicts` keeps **19 of 21**; both drop the rest **silently**. `from_dicts(infer_schema_length=None)` RAISES — and its error, `failed to determine supertype of struct[2] and list[str]`, is the truest thing polars says about this file. **The most correct invocation is the one that fails** |
| **ijson reports ZERO varying paths** | on a document with two polymorphic fields, because each package's `engines` sits at its own prefix. The same code was correct on entry 14 |
| **jsonlite's `class()` reports none either** | with `simplifyVector=FALSE` an object and an array are **both `list`**; all 310 `funding` values report `list` |
| **`$` partial-matches on THREE pairs** | `dev`/`devDependencies`, `optional`/`optionalDependencies`, `peerDependencies`/`peerDependenciesMeta`, firing on 1, 20 and 3 packages. `dev` and `optional` are BOOLEANS, so it is a silent TYPE change. Entry 14 had one such pair; this has three |
| **jmespath drops 923 of 1,657 rows** | `values(packages)[].license` returns 734; the multiselect keeps all. **56% of the document**, silently |

### A dot-joined path cannot be inverted, and two tools prove it

**33 package keys and 33 dependency names contain a dot** — `fs.scandir`,
`object.assign`, `bn.js`. Any representation that joins path segments with `.`
is therefore lossy here:

- **pandas**: the deepest column is
  `packages.node_modules/@nodelib/fs.scandir.dependencies.@nodelib/fs.stat` —
  **five dots, three of them separators.**
- **ijson**: folding its prefixes reports `resolved` **1,623 times against a
  true 1,656 — short by exactly 33**, with the rest scattered into invented
  paths like `packages.<key>.scandir.resolved`.

**jq is immune by construction**: `paths` yields an *array* of segments. So do
rrapply's `L1..L5` columns and tidyjson's `gather_object`. It is a property of
the representation, not of the library.

### What the keyed shape rewards

**`to_entries` (jq/jqr), `kvitems` (ijson), `imap` (purrr), `gather_object("path")`
(tidyjson) and melt's `L2` (rrapply) all keep the install path as data** — which
on this document is the row's identity, not a detail. **jmespath's `values()`
discards it entirely**, and polars, pandas and DuckDB turn the keys into schema.

**rrapply's `melt` is the best-shaped default in either language**: 12,235 x 6
with the install path in `L2` as a value and 21 field names in `L3`. On entry 14
it was `bind` that shone and `melt` that lost types. **The verbs did not change;
the document did.**

### Question 3, thirteen of thirteen, again

**No tool names an alternative row shape or prices one.** Four commit to a shape
silently, three build the 1,390-column trap, and none prints `99% empty`. That
is now unbroken across fifteen graded entries, and this is the file where the
cost of getting it wrong is largest.


## The fourteenth tool, 2026-08-11 — `try-tidyr.R`

**One verb, two contradictory reasons, one verdict.** The same 1,657 npm install
paths:

| framed as | `unnest_auto` says | result |
|---|---|---|
| ONE element | *"elements have **1657** names in common"* | `unnest_wider` → **RAISES** |
| 1,657 ROWS | *"elements have **1** names in common"* | `unnest_wider` → 1,657 x 21 |

**Which reason you get depends only on whether you had already answered question
3**, which is the question being asked. The intersection over the package values
is `version` alone, over 144 distinct key-sets.

**The wide answer raises rather than lying**, because a package-lock's root entry
is keyed by the **empty string** — npm's name for the project itself — so the
column cannot be named: *"Can't unnest elements with missing names."* Set beside
jq's 3,100 field names and rrapply's 3,112 on entry 01, both silent, **a loud
refusal is the better failure.**

**The silent cost is elsewhere and it is large.** `unnest_longer` on the
dependency maps, default versus `keep_empty = TRUE`:

| | rows | keep_empty | drops |
|---|---|---|---|
| `dependencies` | 2,841 | 3,617 | 776 |
| `devDependencies` | 104 | 1,760 | **1,656 of 1,657** |
| `optionalDependencies` | 101 | 1,738 | 1,637 |
| `peerDependencies` | 78 | 1,675 | 1,597 |
| `engines` | 1,059 | 1,665 | 606 |
