# 17 — an OpenLibrary search result

## The expectation, written 2026-08-09 before the probe was run

```
design/probe.py   981a45f023e8de6f0db5951e33c4a4b4d5d6d75b
design/rows.py    109cf0222c84ee7a4cbffa592eed0bbee6b82703
```

### Disclosure

*Of the specimen.* The top-level keys — `numFound, start, numFoundExact,
num_found, documentation_url, q` — and that `docs` is a list of 200 objects.
Nothing inside a `doc` has been seen.

*Of the instrument.* None read for this file.

*Of prior knowledge.* I know OpenLibrary is a bibliographic catalogue whose
records are famously uneven, because they are merged from many library sources.
That informs prediction 2.

### Why this file

**The gate counter is at zero and this is the first of three.** Chosen
**ordinary**, per the rule `14-nyc-311` established: a document picked to break
the newest constant is guaranteed to find something and therefore cannot measure
convergence.

**Deliberately unlike files 14 and 15 in shape.** NYC 311 is a flat table export
and GitHub issues is a nested API response with one record kind. This is a
**search result** — a wrapper object carrying metadata beside a `docs` array —
which is the third common shape and the one the corpus does not have. It also
carries a **duplicate-looking pair, `numFound` and `num_found`**, at the top
level, which is worth watching.

### What is predicted

**1. Two row shapes and the wrapper is not one of them.** The honest answer is
one row per doc, 200 rows. The probe should also offer *the whole document*,
1 row, because the root is an object. Predicted: 2 candidates, and `docs` named.

**2. Ragged by absence, high — the highest outside FHIR.** Bibliographic records
merged from many sources have wildly uneven fields. Predicted: absence well above
null, and more than half the fields sometimes-absent.

**3. keys-as-data 0.** A search response uses fixed field names.

**4. No split.** The docs are one kind of thing — a book — with optional fields.
There is no discriminator, and the raggedness is by source rather than by kind.
**Predicted silence, and correct silence**, like `14-nyc-311`.

**5. Polymorphism 0 or 1**, and if 1 it will be a field that is a scalar on some
records and an array on others, which is the classic catalogue defect.

**6. Depth 3 or 4, recursion 0, under 60 lines.**

**7. `rows("docs.*")` returns 200 rows** with list-columns at `author_name` and
similar — its known defect.

**8. Nothing from the new sentinel rule.** A catalogue omits rather than writing
`"unknown"`. If it fires here it is a false positive and the rule is looser than
the corpus showed.

---

## Provenance

| | |
|---|---|
| what | **OpenLibrary search**, `q=data science`, first 200 docs |
| source | `openlibrary.org/search.json?q=data+science&limit=200` |
| fetched | 2026-08-09 |
| size | 65,336 bytes, **200 docs**, committed |

Valid JSON, whole, one pass. No duplicate keys, no `NaN`, no big integers, no
encoded documents, **no sentinel report**. 25 lines of output.

## The grades, measured 2026-08-09

| axis | measured |
|---|---|
| bytes | 65,336 · depth **4** · paths 31 · fields 25 · explosion 1.2 |
| keys-as-data | **0** · ragged by absence **11/17** · ragged by null **0** |
| recursion | 0 · polymorphic 0 · heterogeneous 1 · path variance 0 · row shapes 2 |

## Prediction scorecard: seven of eight

| # | predicted | outcome |
|---|---|---|
| 1 | two row shapes, `docs` named | **confirmed** |
| 2 | absence high, null low, over half the fields | **confirmed. 11 of 17, null 0** |
| 3 | keys-as-data 0 | **confirmed** |
| 4 | **no split** | **WRONG — a split fired, and it is correct** |
| 5 | polymorphism 0 or 1 | **confirmed. 0** |
| 6 | depth 3–4, recursion 0, under 60 lines | **confirmed. Depth 4, 25 lines** |
| 7 | `rows("docs.*")` → 200 rows | **confirmed. 200 × 18** |
| 8 | the new sentinel rule stays silent | **confirmed — no false positive on its first held-out file** |

## What the file established

### 1. NO DEFECT — the gate counter is at 1 of 3

### 2. The split I predicted against is right, and provably

```
SPLIT ON ebook_access — 4 kinds, not one shape. 34% empty folded, 16% after
  no_ebook 183 · printdisabled 12 · borrowable 4 · public 1
```

Measured, `ebook_access` genuinely determines which fields exist:

```
              borrowable  printdisabled  no_ebook  public
ia                     4             12         0       1
ia_collection          4             12         0       1
```

**`ia` and `ia_collection` are on all 17 ebook-accessible records and on zero of
the 183 without.** The field is a real kind and the split is the right one. It is
marginal — the worst group is 16% against a 17% ceiling — and it passes on the
operation's own definition.

**Second time in two files a prediction has been wrong and the probe right**,
after `15-github-issues`, where the probe's silence turned out to have a second
correct reason the prediction did not contain.

### 3. Defect 15's repair fires on a held-out document

```
an item of docs      200 rows x 17 cols   34% empty
  └─ or 4 tables, split on ebook_access — 16% empty: no_ebook 183, …
```

The row pricing names the split rather than leaving a 34%-empty table unqualified
twenty lines from the partition that fixes it. **First held-out confirmation.**

### 4. The sentinel rule did not fire, which is the result wanted

`981a45f0…`'s new number-versus-few-strings report was written against
`16-movie-ratings` yesterday and had never met an unseen document. **It stayed
silent**, as prediction 8 asked. One held-out negative is not proof it will never
over-report, but it is the first evidence either way.

## What it disconfirmed

**That a wrapper-plus-array response needs the wrapper explained.** The probe
offers *the whole document, 1 row x 8 cols* and *an item of docs, 200 rows*, and
never suggests joining them. That is correct and it is the shape most search APIs
return, so the corpus now covers the third common response shape after the flat
export and the plain record array.


---

## Grading

**The thirteen attempt files are DONE, 2026-08-11** — 5 R + 8 Python, one per
tool, each with its scoring header filled in against what actually printed. The
probe was frozen at `d595d1d2…` throughout and was not re-run.

**This is the first of the four entries graded today where the probe's FOURTH
OPERATION fires**, and that makes it the entry the other three could not be.

### The split, and what every tool does with it

`design/probe.py` prints:

```
an item of docs        200 rows x 17 cols   34% empty
  └─ or 4 tables, split on ebook_access — 16% empty
```

**No tool in either language produces that second line.** They divide into three
groups by how close they get:

| | |
|---|---|
| **can search and price it** | **jq and jqr only.** `group_by` plus an emptiness function expresses the whole search, and its ranking agrees with the probe exactly — `ebook_access` 16.4%, `has_fulltext` 16.4%, `public_scan_b` 34.4%, `edition_count` 35.5%. **Fifteen lines, written knowing what to look for** |
| **can apply it, once told the field** | pandas `groupby`, polars `partition_by`, DuckDB `GROUP BY`, pydash `group_by`, base R `split` |
| **cannot even apply it** | **jmespath** — no group-by at all, so it needs one filter expression per kind and the kinds known in advance |

**Two fields tie on the probe's metric.** `has_fulltext` is a perfect coarsening
of `ebook_access` — `no_ebook` ↔ FALSE, the other three ↔ TRUE — so both give a
worst group of 16.4%. **Weighted by group size they separate: 15.4% against
16.2%, and the weighted metric picks the field the probe already picked.** That
is a data point for **open defect 24**, which proposes exactly that change and
has been waiting for a second document.

### DuckDB manufactures 1,164 nulls, and it is the inverse of entry 15

`unnest(docs)` builds a STRUCT with the **union** of all 17 fields, so a record
that carried 16 keys comes back with 17 and `::JSON` writes the missing one as an
explicit `null`. **The records contain zero nulls; after the round trip they
contain 1,164.**

| route | Q4 always/sometimes | Q5 varying | Q10 rows |
|---|---|---|---|
| `unnest(docs)` → STRUCT → `::JSON` | **17 / 0** | **11** | **350** |
| `json_each(json, '$.docs')` → raw JSON | 6 / 11 | 0 | 349 |
| the probe | 6 / 11 | 0 | 349 |

**Two routes, one tool, a couple of lines apart, and the obvious one is wrong.**
`15-github-issues` found the frame tools unable to tell a null from an absence;
this one **creates** the nulls and then reads them as data.

`count(DISTINCT json_structure)` survives it by luck — the invented nulls fall in
exactly the pattern the absences did, so 15 comes out right either way.

### The only URL is outside the records

The document holds exactly **one** URL, `documentation_url`, at the top level.

- **pandas and polars report NONE OF ONE** — both build a 200-row frame from
  `docs` and cannot see it.
- **DuckDB finds it** because it reads the whole object as a row, so the field is
  just a column — right by accident of shape, not by scanning paths.
- **Everything that starts at the root finds it**: jq, jqr, ijson, pydash, and
  the hand-written walks in glom, purrr and jsonlite.

`25-usgs-quakes` recorded this shape of miss on `metadata.url` at two of three.
**Here the frame-shaped answer is none of one**, which is the extreme case.

### Question 7 has two right answers and only some tools can give both

200 records are present; `numFound` says **30,427** exist. **This is a page**, and
only a top-level field says so. pandas and polars, framing `docs`, can report
neither number. **ijson gives both from one pass** — the metadata is beside
`docs` in the stream.

### rrapply's two verbs swap roles for the third time

`how = "bind"` produced the corpus's **only list-column-free table** on
`14-nyc-311`, because every array there was exactly length 2. Here the arrays run
**1 to 9 elements**, so the same positional expansion gives **200 × 36 at 64.3%
NA** against the honest 200 × 17 at 34% — `author_name.1`…`.6`,
`ia_collection.1`…`.9`. **Nearly double the emptiness, and 19 columns whose names
are subscripts.** The verb did not change; the arrays did.

`how = "melt"` loses the types again here (plain `character`), as on 13 and 14
and unlike 15 — R coerces when the data is homogeneous enough to let it.

### tidyjson is right for the first time in three entries

It typed **five fields wrong on `25-usgs-quakes` and five again on
`15-github-issues`**, both times because it counts `null` as a TYPE. **These 200
records hold zero nulls**, so 17 fields give 17 name/type pairs and none varies —
the probe's answer. Three documents, one mechanism, and the instrument only looks
accurate on the third.

### The `$` trap has one opportunity here and takes none

`ia` is a prefix of `ia_collection`, and **both are absent on exactly the same
183 docs** — so when `ia` is missing there is no sibling to reach.

| entry | prefix pairs | exposed |
|---|---|---|
| `14-nyc-311` | 1 | **199 of 20,000** |
| `13-package-lock` | 3 | **24 of 1,657** |
| `15-github-issues` | 4 | 0 of 100 |
| `17-openlibrary` | 1 | 0 of 200 |

**Four documents now pin the rule**, and this one adds the case the others
lacked: a pair whose two fields are absent *together*, which is safe for a reason
unrelated to how many pairs exist.

### Everything else is easy, and that is the point

**Zero nulls in the records, no keys-as-data, no type variation, no name
collisions** — 31 paths, depth 4, 15 key-sets, all reproduced exactly by jq, jqr,
ijson and the hand-walks. At 64 KB it is the smallest file in the corpus. **And
it still hides a split that halves the emptiness, which nothing but the probe
reports.**

## The fourteenth tool, 2026-08-11 — `try-tidyr.R`

**This entry is the fair attempt question 7a has been waiting for.**
`QUESTIONS.md` marks 7a — *is anything here related by position rather than by
nesting* — as **circular**, since `06-espn-qbr` revealed the property and
`design/probe.py` gained the feature answering it in the same session. It names
the condition for fair comparison: **a tool that predates the question has to be
given a real attempt.** tidyr predates it by years.

`author_key` and `author_name` are two arrays per document, aligned by position
and by nothing else — the QBR property — and their lengths agree on every
document.

```r
unnest_longer(c(author_key, author_name))   # -> 349 rows, correctly paired
```

**It zips. On arrays of different length it RAISES** rather than recycling; a
cross join would have given 855 rows.

> **So question 7a is answered YES by an existing tool, and the probe's
> positional alignment is a reimplementation rather than a new idea.** Any claim
> resting on 7a being unanswerable elsewhere is withdrawn.
>
> **What this does NOT reach is `06-espn-qbr`'s actual finding** — *no tool
> distinguishes the right array of ten from the wrong one*. tidyr zips two
> arrays a person has already chosen, and length is no guard when both
> candidates are the right length. **That claim stands.**

`unnest_auto` is right here too (*"6 names in common"*, 200 x 17). The silent
drop is `ia`: **18 rows from 200 works, losing 183**, so the default answer to
*flatten this* is a table of the 17 works that happen to have one.
