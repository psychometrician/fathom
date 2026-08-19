# 04 — one hour of public GitHub events

**Provenance.** `data.gharchive.org/2026-08-07-15.json.gz`, fetched 2026-08-08.
**10.6 MB gzipped, 50 MB and 37,883 records raw.** Over the corpus threshold, so
`fetch.sh` is committed and the file is not. GH Archive publishes one file per
hour indefinitely: any hour reproduces the shape, no hour reproduces the bytes.

**Why this one.** `scale` was the last axis never tested — every earlier document
fits in memory many times over — and this is also the first specimen that arrives
**gzipped**, which is how JSON at scale actually reaches anybody.

> **Second held-out test.** `design/probe.py` was frozen at `68cec83`
> (`a8307c8`) before this file was fetched, and run **once, unmodified**, under
> rule 5. Nothing below was repaired.

---

## Grading, measured 2026-08-08 with `design/axes.py`

| Axis | Grade | Measured |
|---|---|---|
| depth | **moderate** | 7 levels |
| recursion | **none** | 0 |
| raggedness, by absence | **severe** | **53 of 727** field slots |
| raggedness, by null | **severe** | **33** fields sometimes null |
| polymorphism | **none** | 0 — see the note below, it is not what you would guess |
| keys-as-data | **mild** | 2 sites, both `performed_via_github_app.permissions` |
| heterogeneous arrays | **mild** | 1 |
| path variance | **severe** | **76** — the highest in the corpus |
| unit ambiguity | **moderate** | 8 row shapes |
| scale | **the first real reading** | 50 MB, 37,883 records, **968 MB peak RSS**, 7.2 s |
| *path explosion* | *derived* | 846 paths for 235 fields, ratio 3.6 |

**Polymorphism reads 0 on an event stream, which is the interesting part.** A
`PushEvent` and an `IssuesEvent` carry completely different `payload` contents, but
`payload` is an object in both, so no field ever changes type. **The variation is
entirely raggedness**, 53 of 727, and the polymorphism axis is right to stay
silent. Event streams differ in *which keys exist*, not in *what type a key holds* —
which is the opposite of what "LLM output is polymorphic" led this project to
expect of machine-generated JSON.

## What the frozen probe got wrong, and the third one is the worst

**1. It cannot read the file as it arrives.** Given the `.gz`:

```
10.6 MB · not a format I recognise
Expecting value: line 1 column 1 (char 0)
```

`corpus/README.md` already says NDJSON is how JSON at scale arrives. It arrives
**compressed**, and the probe has no path for it at all.

**2. It needs 18.8× the file in memory.** 968 MB peak resident for a 50 MB
document, because `health()` does `open(path,"rb").read()`, decodes the whole
thing, and then builds a Python object for every one of the 37,883 records.
Extrapolated, a 500 MB file wants ~9 GB and the 10 GB file `README.md` talks about
wants ~190 GB.

> **`README.md` promises that "the probe never lies about its own coverage — it
> states how many records it read and what it therefore cannot claim." Half of
> that is now real and half is not.** It states what it read, accurately. It has
> no way to read less, so on a file that does not fit it does not sample — it
> dies.

**3. It reported six unreadable lines, and it had broken them itself.**

```
NDJSON, 37,880 of 37,886 records read
6 lines could not be read, first at line 10263 — everything below describes the rest
```

There are **37,883 newlines and zero malformed records**. `str.splitlines()`
splits on Unicode line separators as well as `\n`, and three GitHub payloads
contain a literal **U+2028 LINE SEPARATOR** in user-written text. Three valid
records became six broken fragments.

**NDJSON is delimited by `\n` and nothing else.** `splitlines()` is the wrong
function, and the failure is invisible without a control: the report was accurate,
specific, and blamed the data.

> **A diagnostic that accurately reports damage it caused itself is worse than one
> that stays quiet, because it sends you to look in the wrong place.** The health
> verb exists to say what a parser silently did to your data. Here fathom was the
> parser doing it.

## The expectation this file disconfirmed

**A machine-generated event stream was expected to be polymorphic**, on the
strength of `README.md`'s argument that model and machine output is ragged by
nature. Measured: **zero polymorphic fields** across 37,883 records and 235 field
names. What it has instead is severe raggedness and the corpus's highest path
variance. **Machine-generated is not the same as polymorphic**, and the two were
being treated as one thing.

## Status

Graded, and used as the second held-out test. **Not repaired** — under rule 5 the
probe stays frozen and all three failures stand as measured. **No tool attempts
yet.**

## The R half — predictions, written 2026-08-10 BEFORE the tools were run

**Committed as its own change, before any file exists in `r/` beyond the tidyr
attempt**, so the order is checkable. Rule 1.

This document is being used to test three things at once, and it is the only
corpus file that can carry all three.

**1. The discriminator method will FAIL here, and that is the point.** On
`05-fhir-bundle` and `07-graphql-introspection`, `[keys present in EVERY record]`
found the discriminator in one expression — `resourceType` at 20 distinct values
against `id` at 564, and `kind` predicting every null. **`VERDICT.md` item 15
says this file has NO field present in every `payload` at all.** So the
expression should return an **empty list**, and the method that has worked twice
should have nothing to rank. Predicted: **zero always-present fields under
`payload`.**

**2. And the discriminator should be one level UP.** Item 15's proposed fifth
operation is that the field explaining a shape sometimes sits on the ENCLOSING
object — here the event's `type`. Predicted: partitioning payloads by the
parent's `type` produces groups that are markedly fuller than the fold, the way
`resourceType` took `05` from 87% to 22%. **If that does not happen, the case for
a fifth operation is weaker than item 15 claims.**

**3. R's line splitting will disagree with the probe's, in R's favour.**
`NOTES.md` above records the frozen probe reporting *"6 lines could not be read"*
on a file with **37,883 newlines and zero malformed records**, because Python's
`str.splitlines()` also splits on **U+2028 LINE SEPARATOR**, which appears in
three user-written GitHub payloads. R's `readLines` splits on `\n` only.
**Predicted: R reads 37,883 records and reports no damage** — a cross-language
control on a bug this corpus already knows the answer to, which is the cleanest
kind of check available.

**4. Scale will cost the R tools something none of the other files charged
them.** The probe needed **968 MB peak RSS for a 50 MB document, 18.8x**.
Predicted: `jsonlite::fromJSON` on the whole file is far more expensive than
`stream_in`, and **`jqr` is at a structural disadvantage to the jq CLI**, because
`jq()` takes an R character vector — so the whole 50 MB must be materialised in R
memory before jq sees it, where the command-line tool streams. If so, that is a
real finding about the binding rather than about the language.

**5. rrapply's melt will not be runnable on the whole file.** 37,883 records at
roughly 30 leaves each is over a million rows. Predicted: measured on a subset
and extrapolated, and **labelled as an extrapolation** rather than quietly
reported as a whole-file number.

**A prediction that would hurt.** If the parent's `type` does NOT clean up the
payload fold, then item 15's fifth operation is resting on a document that does
not support it, and the entry should say so.

## The R half, run 2026-08-10 — five of five, and the fifth operation gets its evidence

**All five R tools run; the entry is done.** Predictions were committed in
`1109753`, before any file in `r/` existed beyond the tidyr attempt.

| # | predicted | outcome |
|---|---|---|
| 1 | the discriminator method returns **nothing** | **confirmed. `[]`** — no field in all 37,883 payloads |
| 2 | the parent's `type` cleans up the fold | **confirmed, more cleanly than FHIR** — 82% empty → 13 of 16 groups 100% filled |
| 3 | R reads **37,883** records, no damage | **confirmed.** 3 lines carry U+2028; all 3 are valid JSON |
| 4 | scale costs the R tools; `jqr` loses to the CLI | **confirmed both ways, and R beats the probe** |
| 5 | melt not runnable whole; subset + extrapolate | **confirmed**, and the extrapolation checks against jq |

### 1. The fifth operation now rests on a measurement

`VERDICT.md` item 15 proposes a fifth operation — *the field that explains a
shape sometimes sits on the ENCLOSING object* — on the strength of this file.
Measured three independent ways (jq over the whole file, rrapply over a melted
frame, purrr over the parsed list), all agreeing:

```
fields present in EVERY payload:  []          <- nothing, across 37,883 records

folded on payload alone       25 keys, 18% filled  ->  82% EMPTY
partitioned on parent .type   13 of 16 groups 100% filled, worst real 48%
```

The discriminator method that solved `05-fhir-bundle` and
`07-graphql-introspection` **in one expression each** has nothing to rank here.
And the parent settles it more cleanly than FHIR did — 87% → 22% there, with the
discriminator *inside* the record; 82% → mostly zero here, with it *outside*.

**The general form is stronger than any single field**: of the 25 payload
fields, **13 belong to exactly one event type** — `push_id`, `release`, `review`,
`number`, `head`, `before`, `forkee`, `pages` and five more. `push_id` is on
precisely the 30,099 PushEvents; `ref` on precisely Push, Create and Delete.

> **Fourth document in three days where raggedness is a partition wearing a
> disguise**, after `05`'s four whole resourceTypes, `10`'s `somevalue` snak and
> `07`'s `kind` predicting every null. **What is new here is that the
> partitioning field is not in the record at all**, so no test over the payloads
> can find it. That is the difference between operation 4 and the proposed fifth.

### 2. R is right where the probe was wrong, on a bug with a known answer

```
readLines                    37,883 records
lines containing U+2028            3
lines failing validate()           0
```

The frozen probe reported *"6 lines could not be read"* on this file and **had
broken them itself**: Python's `str.splitlines()` splits on U+2028 and three
GitHub payloads contain one. R splits on `\n` and nothing else. **jsonlite earns
the first YES on question 0 anywhere in this corpus** — narrow, because it
validated the framing and not the contents, but right where the probe was wrong.

### 3. An existing R library beats the prototype on memory — the third qualification

Measured with `/usr/bin/time -l`:

| | peak RSS | time | multiplier |
|---|---|---|---|
| `design/probe.py` | **968 MB** | 7.2 s | 18.8× |
| `stream_in(simplifyVector = FALSE)` | **427 MB** | 4.4 s | 8.6× |
| `stream_in()` simplified | 636 MB | 6.3 s | 12.8× |

`design/implementation.md` names memory as one of two justifications for a Rust
port, and `VERDICT.md` records that argument being qualified twice already.
**This is a third and the most direct: on the corpus's only scale reading an
existing R library uses less than half the prototype's memory.** The comparison
is not Python-versus-Rust; it is this-prototype-versus-a-tool-people-already-have.

### 4. A finding about the binding, not the language

| | peak RSS | time |
|---|---|---|
| `jqr`, `.type` over the file | **198 MB** | 1.01 s |
| `jq` CLI, same query, streaming | **4.3 MB** | 0.41 s |

**46×.** `jq()` takes an R character vector, so the whole document is
materialised before jq sees it. Worse, **`jqr` has no slurp** — `jq_flags()`
offers pretty, ascii, color, sorted, stream, seq — so any whole-file question
requires building the array by hand, a *second* 52 MB string in R memory.

**jq the language is the most memory-frugal tool in this corpus by a wide
margin, and the R binding gives all of it away.** `README.md` credits jq and jqr
as "two doorways to one query language"; on a 50 MB file they are not.

### 5. The melt ratio is confirmed as a verbosity measure

**52% — the lowest of six** — on the document with the corpus's **highest path
variance (76)** and severe raggedness by both absence and null.

| file | melt ratio | why |
|---|---|---|
| **`04-gharchive`** | **52%** | long values: commit messages, URLs, 40-char SHAs |
| `05-fhir-bundle` | 60% | |
| `09-stripe-openapi` | 141% | |
| `10-wikidata` | 173% | |
| `07-graphql` | 204% | short values, long names |
| `03-natural-earth` | 226% | short values, 99,566 of them |

Under the reading `VERDICT.md` used until 2026-08-10 — that the percentage
tracks how badly a tool fails to fold — the raggedest file being the cheapest is
inexplicable. Under the correction `07-graphql-introspection` forced it is
arithmetic. **The table is ordered by value length, not by raggedness, keyed
sites or depth.**

### 6. `json_schema` does not finish, and NDJSON is tidyjson's native shape

Two opposite results from one tool. `as.tbl_json()` on a character vector of
lines gives **37,883 documents with nothing known in advance and no verb
chosen** — the cleanest answer to question 3 in the corpus, because tidyjson's
model is *a table of documents* and NDJSON is literally that. `gather_object() |>
json_types()` then answers question 4 over all 37,883 records in seconds.

And `json_schema` measures **25.5 KB/s here**, extrapolating to about **33
minutes** for the file. **Scored CANNOT — the first time in five documents it has
earned that rather than WRONG.** Its throughput is document-dependent by nearly
7× (3.8 KB/s on `03`'s nested coordinate arrays), so whatever it costs is not a
function of bytes alone.

### A note on depth, which NDJSON makes ambiguous

Measured with jq over all 37,883 records, `[paths|length]|max` **per record is
6**. rrapply's melt reports **7** level columns because the first is the record
index — it is melting a list of records, not one document — and the grade of 7
above is the same reading. **Both are defensible and they are not the same
question**: a record is 6 deep, the file understood as an array of records is 7.
Every other corpus file is one document, so the readings coincided and nobody had
to choose.

## Status

**R half complete 2026-08-10** — purrr, jsonlite, tidyjson, rrapply, jqr, plus
tidyr. Python is 8 attempts. Under `CLAUDE.md`'s definition this entry is done.

## Corrected 2026-08-13: 254 → 272 leaf names, and the character total moves too

**The grades above are left alone.** `paths(scalars)` drops every `false` and
`null` leaf — see `01-npm-registry`.

| | recorded | corrected |
|---|---|---|
| distinct leaf names | **254** | **272** |
| every-leaf character total | **27,108,878** | **28,351,333** |

The 18 names that were invisible include `answer_chosen_at`, `answer_chosen_by`
and `answer_html_url` — GitHub writes `null` rather than omitting them.

**THE FINDING IS UNCHANGED.** 272 against 235 true fields is still OVER, still
by roughly 8%, and still because two keyed sites hold scalar values.
