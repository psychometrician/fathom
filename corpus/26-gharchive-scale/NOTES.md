# 26 — one hour of public GitHub events, at 17× the size of entry 04

**Provenance.** `data.gharchive.org/2024-01-15-12.json.gz`, fetched 2026-08-11.
**118 MB gzipped, 870 MB and 286,864 records raw.** Far over the corpus
threshold, so `fetch.sh` is committed and the file is not.

**Why this one, and it is the narrowest reason any entry has had.**
`corpus/README.md` has carried `scale` as an open gap since the beginning:

> ~~**scale**~~ — **first reading taken by `04-gharchive`**: 50 MB and 37,883
> records cost 968 MB of memory, an 18.8x multiplier […] **Still wanted:
> something that genuinely does not fit**, to test a sampling path that does not
> yet exist.

At entry 04's measured 18.8× multiplier, 870 MB of JSON implies **~16.4 GB**
against this machine's **16 GB** of RAM. That is the specimen: a real file, as it
ships, that does not fit.

> **IT IS A CONTROL AND THEREFORE NOT A HELD-OUT TEST OF THE DESIGN.** This is
> the same source, format and event shape as `04-gharchive`, chosen so that
> **size is the only variable that moves.** That makes it a good instrument for
> one axis and a bad one for everything else, and it has a consequence that must
> be stated before the run rather than argued after it:
>
> **THIS FILE MUST NOT MOVE THE GATE COUNTER, in either direction.** The counter
> measures whether an unseen DOCUMENT forces the design to change. A document
> deliberately selected to be shape-identical to one the probe has already been
> run against is not unseen in the sense the counter means. If it finds a defect
> that defect is real and gets recorded; **it still does not reset the counter,
> and finding nothing does not advance it.**

---

## Predictions, recorded 2026-08-11 BEFORE the probe was run

Rule 1. The freeze was verified first — `design/probe.py` at
`d595d1d2db2e78e49d801fc09e2728ab1cd28694` — and the probe will be run **once,
unmodified**, under rule 5.

Two facts about the instrument were read from the source before predicting, and
they are stated so the predictions are not mistaken for blind ones:
`MAX_RECORDS = 20_000` is a sampling cap, and `probe.py` **does** call
`gzip.decompress`.

| # | prediction |
|---|---|
| **P1** | **It completes rather than dying.** The sampling cap bounds the parse, so the run finishes and prints a report |
| **P2** | **It states its own coverage**: `SAMPLE: the first 20,000 of 286,864 records`, which is the promise `README.md` makes about never lying about coverage |
| **P3** | **Peak RSS is proportional to the FILE and not to the SAMPLE.** Entry 04 sampled 20,000 records and peaked at 968 MB on a 50 MB file. This file is 17× larger and the sample is IDENTICAL, so if memory tracks the sample the two figures match, and if it tracks the file this one lands in the **multiple gigabytes**. I predict the file — the read happens before the cap applies |
| **P4** | **The reported STRUCTURE is near-identical to entry 04's** — same event kinds, path variance around 76, keys-as-data at `performed_via_github_app.permissions`. If it differs materially then this document is genuinely new and the control has failed as a control |
| **P5** | **It reads the `.gz` directly**, contradicting `corpus/README.md`'s note that on entry 04 *"the gzipped form the file actually ships in cannot be read at all"* — that must have been repaired between 2026-08-08 and the current freeze |

**The prediction I am least sure of is P3, and it is the one the entry exists
for.** If memory tracks the sample, the sampling contract is doing real work and
the `scale` gap is narrower than `corpus/README.md` claims — the missing piece
would be a *streaming read*, not a *sampling path*, and the sampling path would
already exist. If memory tracks the file, then the cap protects the parse and
nothing protects the read, and a 20,000-record sample costs 17× more on a 17×
larger file for no benefit at all.

**What would make this entry worthless:** the probe completing in about 968 MB
and reporting the same numbers as entry 04. That would mean the axis still has
not separated two files, and 870 MB is simply not big enough to be the specimen.
Recorded here so that outcome is a finding rather than a disappointment.

---

## The cold run, 2026-08-11 — the axis separated two files for the first time

`design/probe.py` at `d595d1d2…`, hash verified immediately before the run, run
**once, unmodified**. Nothing below was repaired.

```
869.8 MB · 117.6 MB of gzip, unpacked to 869.8 MB · NDJSON, 20,000 of 286,864 records read
SAMPLE: the first 20,000 of 286,864 records. Everything below describes those and cannot speak for the rest.
```

**12.3 seconds, exit 0, peak RSS 2,485 MB.**

### The predictions, scored

| # | | outcome |
|---|---|---|
| **P1** | it completes | **✓** exit 0 in 12.3 s |
| **P2** | it states its own coverage | **✓** verbatim, and it names both numbers |
| **P3** | **peak RSS tracks the FILE, not the SAMPLE** | **✓ AND IT IS THE RESULT** |
| **P4** | structure near-identical to entry 04 | **✓ broadly** — 7 levels both, same shape family; paths 816 → 1,048, the record candidate 650 → 855 columns |
| **P5** | it reads the `.gz` directly | **✓** — `corpus/README.md`'s note that the gzipped form *"cannot be read at all"* is stale |

### P3, and the number that sized this file was wrong twice over

**Entry 04 was re-measured on the current freeze and the same machine**, because
comparing a 2026-08-08 figure against a 2026-08-11 one is exactly the error this
project keeps finding in other people's work:

| | file | sampled | peak RSS | multiplier |
|---|---|---|---|---|
| `04-gharchive` **as recorded 2026-08-08** | 50 MB | 20,000 | **968 MB** | 18.8× |
| `04-gharchive` **re-measured today** | 50 MB | 20,000 | **614 MB** | 12.3× |
| `26-gharchive-scale` | **870 MB** | **20,000** | **2,485 MB** | **2.9×** |

> **THE SAMPLE IS IDENTICAL AND THE MEMORY IS FOUR TIMES LARGER.** Both runs
> parse exactly 20,000 records. The only thing that changed is the size of the
> file underneath them, so **memory tracks the file and not the sample** — the
> whole document is read and split into lines before the 20,000-record cap
> applies to anything.

**Two points give a model, and it replaces the multiplier:**

```
peak RSS  ≈  500 MB fixed  +  2.28 × file size
```

**`corpus/README.md`'s 18.8× is wrong in two independent ways.** It is stale —
the current build does the same work in 614 MB — and it was never a multiplier
at all: at 50 MB the fixed cost of parsing 20,000 records dominates and the
ratio reads 12×, at 870 MB the read dominates and it reads 2.9×. **A ratio taken
at one point on a two-term curve is not a property of the tool.**

### The specimen is STILL not obtained, and now it can be sized

I chose 870 MB because 870 × 18.8 ≈ 16.4 GB against 16 GB of RAM. **That
arithmetic used the stale multiplier and was wrong.** Solving the model instead:

> **A file that genuinely does not fit in 16 GB is about 6.8 GB of JSON.** GH
> Archive does not ship an hour that large, so the specimen needs a different
> source or a deliberately concatenated one — and concatenating is manufacturing
> a document, which is the thing `corpus/README.md`'s "real files only" rule
> exists to prevent. **That is now a decision for the author, and it is the same
> decision the broken/truncated gap needs.**

**The entry is not worthless, and the test for that was recorded in advance.**
The condition written before the run was *"the probe completing in about 968 MB
and reporting the same numbers as entry 04."* It used **2,485 MB against 614
MB** and reported different numbers. **`scale` has separated two files for the
first time since the axis was written down.**

### What scale actually costs, and it is not memory

**The sample is 6.97% of this file.** Entry 04's was 52.8%. That difference is
visible in exactly one place in the report:

| keys-as-data site | in the first 20,000 | in the whole file |
|---|---|---|
| `payload.comment.performed_via_github_app.permissions` | 336 | **4,133** |
| `payload.issue.performed_via_github_app.permissions` | **0** | **11** |

**The probe reports ONE keys-as-data site. The document has two.** Entry 04
found both because in that file the second had 65 copies inside the first
20,000; here it has 11 copies in 286,864 records, so the expected count in a 7%
sample is under one and finding none is exactly what sampling does.

> **This is not a defect and the probe did not lie.** It promised to describe
> the first 20,000 records and it described them correctly. **But it is the
> first document in the corpus where sampling demonstrably cost a reported
> finding**, and the report reads identically whether a site is absent from the
> DOCUMENT or merely absent from the SAMPLE.
>
> **So the real price of scale is fidelity rather than memory.** `README.md`
> says the probe *"never lies about its own coverage"* and that is upheld — it
> says how many records it read. What it cannot say is what that cost, and on
> this file it cost one of the two keys-as-data sites.

## Tool-sweep predictions, committed 2026-08-14 BEFORE any attempt was written

Rule 1, applied to the fourteen-tool comparison. **The document is not unseen** —
it was graded on 2026-08-11 and its structure is above — so what is predicted
here is TOOL BEHAVIOUR at scale, which nothing has measured.

**This entry is the only place in the corpus where the scale axis can grade the
TOOLS.** Entry 04 is the same source, format and event shape at 50 MB; this is
870 MB and 286,864 records. Size is the only variable, which is what makes the
control worth its cost here even though it is worthless for finding new
structure.

**Two facts about the instruments, read before predicting.** `fathom` samples
`MAX_RECORDS = 20,000` — **6.97% of this file** — and says so. No competing
tool has a sampling contract at all: handed this file, each one either reads it
or does not.

| # | prediction |
|---|---|
| **T1** | **THE GRID COLLAPSES TO ONE QUESTION: can it stream?** At 50 MB the fourteen differ in expressiveness; at 870 MB I predict they differ only in whether the document must fit in memory first |
| **T2** | **ijson completes the whole file in roughly constant memory** — under 500 MB peak. It is the tool this entry exists to reward |
| **T3** | **duckdb completes**, reading from disk without materialising in Python |
| **T4** | **polars completes IF `scan_ndjson` is used** and fails on `read_ndjson`. A streaming reader is the difference, not the engine |
| **T5** | **pandas does NOT complete** in a 10-minute budget on this machine |
| **T6** | **All six R tools fail or exceed budget**, because every one of them needs `jsonlite` to parse 912 MB into R objects first. rrapply's melt won entry 29 in 0.4 s and I predict it never gets to run here |
| **T7** | **glom, jmespath and pydash fail** for the same reason — they operate on an already-parsed document |
| **T8** | **The split is about 4 tools that finish against 10 that do not** |
| **T9** | **fathom is FASTER than every tool that completes, and its answer is PARTIAL.** 12.3 s over 6.97% against ijson reading 100%. **That is the comparison this entry can make and no other can** |
| **T10** | **No tool names alternative row shapes and prices them**, for the 30th entry running |

> **T9 is the one worth the run.** Every previous entry compared what the tools
> can SAY. This one compares what they can FINISH, and fathom's sampling
> contract — the thing that makes it fast — is also the thing that made it miss
> a keys-as-data site on this very file. **If the streamers get the complete
> answer in tolerable time, the sampling contract is a worse trade than it
> looks; if they take minutes, it is a better one.**

**What would make this sweep worthless:** every tool completing comfortably, so
that 870 MB turns out not to be a scale test for anything but fathom. Recorded
in advance so that outcome is a finding rather than a disappointment.

## ALL FOURTEEN TOOLS, 2026-08-14 — and almost every prediction was wrong

All fourteen written, RUN, and their prose corrected against what printed.
6 R + 8 Python, each carrying a wall-clock budget and a peak-memory reading,
because on this file *did it finish* is the question.

### Five tools agree on the leaf count, exactly

| | |
|---|---|
| **17,670,186 leaves** | ijson, jq, jqr, rrapply, tidyr |
| **286,864 records · depth 6** | every tool that answered at all |
| **13,009,389 string · 2,652,154 number · 1,581,755 boolean · 426,888 null** | ijson, jq, jqr, rrapply |
| **17,809,166** | purrr — **and the difference is explained, not a defect**: my walk counts an empty `{}` or `[]` as a leaf and the others do not. 138,980 of them, confirmed by counting both ways on the first 2,000 records |

> **"How many leaves" has two defensible answers and no tool says which it gave
> you.** That is question 7 being quietly ambiguous, and it only became visible
> because five tools were asked the same thing.

### Did it finish?

| tool | | |
|---|---|---|
| **ijson** | **10.6 s · 25 MB · whole file** | the tool this entry exists to reward |
| **duckdb** | **1.6 s · 263 MB** to count all records | cheapest complete read of the fourteen |
| **jqr** | 21 s chunked · 1.4 GB | **overflows R's protection stack unchunked** |
| **pandas** | 6.1 s · 3.3 GB chunked; 13.3 s · 6.0 GB whole | 286,864 x 8, `payload` left opaque |
| **rrapply** | melt **17,670,186 x 8 in 56.9 s** | after a 60 s parse |
| **jq (python)** | 224 s · **24 MB** | one invocation per record |
| **tidyr** | 17,670,186 rows in **7 calls**, 113 s | the loop is mine |
| **purrr** | 147 s · 11.1 GB | the walk is mine |
| **polars** | 20.3 s · 5.0 GB **only with `infer_schema_length=None`** | eager and lazy both fail without it |
| **jsonlite** | `stream_in` 61 s · 3.6 GB | the ceiling all six R tools share |
| **glom · jmespath · pydash** | parse 5.0 s · 2.9 GB, then fast | they need the document in memory |
| **tidyjson** | **DID NOT FINISH** — killed at 10 min 39 s | the only one of the fourteen |

**Predictions T5, T6 and T7 all said tools would fail, and all three were
wrong.** 870 MB is simply not big enough to defeat a 16 GB machine. **T8 said
about 4 of 14 would finish; THIRTEEN DID.** The prediction that survived is
**T2** — ijson at 25 MB — and it survived by a wider margin than written.

> **tidyjson is the single exception and it did not fail, it just cost too
> much.** Its scaling curve here has a log-log slope of **1.00** — linear, not
> superlinear — and extrapolates to about 466 s of compute. The observed run
> passed 639 s and was still going, because memory pressure at 4.5 million
> nodes per 60,000 records is not in the curve. **A tool that cannot finish has
> answered "cannot", and the curve is what makes that a measurement rather than
> an impatience.**
>
> **`setTimeLimit` did not stop it**, which is worth recording for the next
> person: it interrupts at R-level checkpoints and `json_structure()` is one
> long call into C. The run had to be killed from outside.

### THE FINDING: three tools decide what this file is from its first records, and all three are wrong

This is not a memory story. It is a **sampling** story, and it caught fathom,
duckdb and polars in three different ways:

| | what it does | what happened |
|---|---|---|
| **fathom** | samples 20,000 and **says so** | reports **1 of the 2** keys-as-data sites |
| **duckdb** | infers a schema from a sample | **crashes at line 53,538**, naming the key |
| **polars** | infers a schema from a prefix | **`ComputeError: expected null in json value, got object`** |

**duckdb's crash names this entry's own finding.** The offending key is
`codespaces_lifecycle_admin`, and it lives at
`payload.comment.performed_via_github_app.permissions` — **verified, not
assumed** — which is exactly the keys-as-data site the cold run reported, and
exactly the site whose second instance the 20,000-record sample missed.

**And the fix, in both engines, is to stop sampling:**

| | |
|---|---|
| duckdb `sample_size=-1` | **8.0 s** |
| duckdb `ignore_errors=true` | 3.8 s — **silently lossy** |
| polars `infer_schema_length=None` | 20.3 s |

> **Reading everything costs 8 seconds. That is the whole argument.** fathom
> spends **5.4 s and 1,091 MB** (measured today on the current build) to
> describe **6.97%** of this file. ijson reads **100%** of it in 10.6 s and
> **25 MB**. The sampling contract was supposed to bound the work; on this
> document it bounds the parse and not the read, buys about five seconds, and
> costs a reported finding.
>
> **Of the three, fathom's behaviour is still the best**: it is the only one
> that says what it sampled. That is a low bar and it clears it.

### `rrapply`'s melt preserved the types here and DESTROYED them on entry 29

Same verb, same arguments, opposite outcome — and the difference is the data.
`value` comes back **atomic** when the leaves happen to unify and a **list**
when they do not. Entry 29 was all strings and booleans, which unify to
character, so 57,103 booleans became `"FALSE"`. This file has nulls and numbers
in the mix, nothing unifies, and every count matches jq exactly.

**You cannot tell from the call which you got.** That is worse than a verb that
always coerces.

### jqr overflows R, and the same jq through Python does not

`protect(): protection stack overflow` at 50,000 records. **It is an R limit,
not a jq limit** — the Python binding reads all 286,864 without complaint.
Chunked by 10,000 it works, and it is then **ten times faster than the Python
door** (21 s against 224 s), because jqr takes TEXT and the Python binding takes
a parsed value. **Same engine, same answer, an order of magnitude apart, and
the faster door is the one that falls over unless the caller chunks it.**

### What none of the fourteen does, for the 30th entry running

**No tool names alternative row shapes and prices them.** Questions 3 and 6 are
CANNOT in all fourteen at 870 MB exactly as at 604 KB and 19.9 MB. **Scale
changed what things cost and did not change which questions have an answer.**

### The gate counter does not move, as recorded in advance

**No defect was found and the counter stays where it was**, because this entry
was declared a control before it was run. Nothing here is evidence about whether
an unseen document forces the design to change.
