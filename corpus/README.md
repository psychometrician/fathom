# The corpus

**Real files only.** Toy JSON is hard in ways nobody actually suffers from, and
the whole premise here is that the pain comes from documents somebody was handed.

## Adding one

1. `corpus/<nn>-<short-name>/`, numbered in the order added.
2. `source.json`, committed. Over about 5 MB, commit `fetch.sh` instead and say in
   `NOTES.md` what the file looked like on the day.
3. `NOTES.md`, following `01-npm-registry`: provenance with a date, then the
   grading table with a **measured** number in every row it can have one, then
   what the file disconfirmed.
4. `r/` and `python/`, one attempt per tool, answering `../../QUESTIONS.md`.

## The rule that keeps this honest

**Write down what you expect the file to be hard at, before measuring it.** The
first file was chosen as a polymorphism specimen and has no polymorphism at all.
That is worth more than a file which confirmed what somebody already believed, and
it is only worth anything because the expectation was recorded first.

## Validity is a precondition, not an axis

**Decided 2026-08-08.** A broken file cannot be graded on the other ten axes, so
soundness is not one of them — it is the thing you establish before grading
begins. Record it at the top of `NOTES.md`: valid or not, whole or chopped off,
and the silent damage (duplicate keys, integers past 2^53, `NaN`, values that are
themselves encoded documents).

**A file that is broken is still worth having.** It is a specimen of the thing
`README.md` says has no rectangular analogue, and the corpus needs one.

## Wanted

Gaps in the corpus as it stands, stated so they are not assumed covered:

- ~~**polymorphism**~~ — **FILLED 2026-08-09 by `12-agent-trace`, on the fifth
  candidate.** `polymorphic 4`, the highest in the corpus, and the headline field
  is `message.content`: **a bare string on 20 messages and an array of blocks on
  1,363**, reported without the *"an artifact of folding"* label.

  **The four failures are worth more than the success**, because between them
  they named the requirement. `01-npm-registry` was chosen as a polymorphism
  specimen and had none. `05-fhir-bundle` had it engineered out by a
  specification that enumerates every variant as its own field name.
  `11-jupyter-notebook` was chosen because `nbformat` permits `source` to be a
  string *or* a list of strings, both legal, with nothing engineering the choice
  away — and it uses a list on all 272 cells.

  > **A permissive format is not enough. Polymorphism needs more than one
  > producer.** A notebook never varies because one tool wrote it in one sitting;
  > a transcript is written by a person, a model and a tool harness in turn, none
  > of them agreeing on anything.

  Kept in full rather than struck through, because this list was **wrong about a
  file in advance four times**, and the record of how it was wrong is the only
  reason the fifth choice was right.

  *The original entry:* **Language model output is the strongest candidate**:
  structured output and agent traces are ragged by nature, since a field is a
  string in one response and an object in the next.

  **FHIR was named here as a conventional alternative and it did not deliver, which
  is the third time this list has been wrong about a file in advance.**
  `05-fhir-bundle` has **zero** genuine polymorphism: the three fields the probe
  reported vary only *across* resourceTypes, and within any one of them each is a
  single type always. FHIR's raggedness is in the *naming* — `value[x]` — not in
  the typing, because a specification that enumerates every variant as its own
  field name has engineered the polymorphism out. **A format strict enough to be
  worth choosing as a specimen is strict enough not to be one.** That leaves model
  output, where nothing enforces anything, as the only remaining candidate.

  **A fourth candidate was tried on 2026-08-09 and also failed, and it sharpens
  what the gap actually needs.** `11-jupyter-notebook` was chosen because
  `nbformat` permits `source` and `text` to be **either a string or a list of
  strings**, both legal, with no specification engineering the choice away. The
  notebook uses a list on every one of its 272 cells. **Measured polymorphism:
  0.**

  > FHIR had it specified out. A notebook simply never varies **because there is
  > one writer.** The gap does not need a permissive format. It needs a document
  > **assembled from more than one producer** — which is what an agent trace or a
  > pile of model responses is, and why the open decision below is now the
  > blocker for this gap rather than a side question.
- ~~**NDJSON**, one object per line.~~ — **FILLED 2026-08-09 by
  `12-agent-trace`**, the first *plain* one: `04-gharchive` arrives gzipped, so
  the health verb had never met the bare case. Reported as
  `NDJSON, 1,953 of 1,953 records read · not one JSON document, and not broken`,
  with no health-check noise. In scope because the health check forces it: an
  NDJSON file is *not valid JSON*, so telling "broken" from "a different format"
  is unavoidable. It is also how JSON at scale actually arrives.
- **broken or truncated**, a real one rather than a damaged copy. A model response
  cut off at `max_tokens` is the most common case there is.
- ~~**keys-as-data NESTED INSIDE keys-as-data**~~ — **FILLED 2026-08-18 by
  `30-aws-redshift-pricing`, on the FIRST candidate.** AWS documents `terms` as
  `terms.<type>.<sku>.<sku>.<offerTermCode>.priceDimensions.<sku>.<offerTermCode>.<rateCode>`
  — four levels of data keys nested directly inside one another. **Reserved
  pricing is what qualifies it**: a reserved SKU carries one term per purchase
  option, so `terms.Reserved.<sku>` holds **min 4, median 6, max 6** keys, which
  is the 3-to-15 band this entry asked for.

  **It is the SHARPER of the two instances.** `where date` names **3,300 paths
  for 3,300 values** — every path covering exactly one, against entry 29's
  79.8% — where **3 paths are right**. A price list and a compat matrix share no
  producer, so **the mechanism is a property of the shape rather than of MDN.**
  `FINDINGS.md`, 2026-08-18.

  > **This list was right in advance for the first time, and the reason is that
  > the specification was numeric.** The four polymorphism candidates that
  > failed were chosen by what a format PERMITS; this one was chosen by a
  > measured threshold — `KEYED_MIN` = 20, inner containers below it, union
  > above it — and the format's own documentation said the shape was there
  > before the file was fetched. **A gap stated as a number is findable; a gap
  > stated as a hope is not.**

  *The original entry, kept because the reasoning is what made the choice
  possible:*

- **keys-as-data NESTED INSIDE keys-as-data**, where the inner containers are
  individually small. **Added 2026-08-14, and it is asked for so that defect 36
  can be repaired on more than one document's evidence.**
  `29-mdn-browser-compat` is the only instance the corpus has: an outer map of
  1,090 names whose values are themselves maps of a handful of names each, and
  `find("url")` names **11,320 folded paths for 35,392 values** there — 79.8% of
  them covering a single value.

  **The specification is the SHAPE and not the size**, which is what makes this
  a gap rather than a want for another big file. What is needed is a second
  document where an outer container's keys are data AND the inner containers'
  keys are data too, with the inner ones holding few enough keys that each looks
  like a record on its own evidence. **A registry keyed by name whose entries
  are keyed by version is the obvious shape**; so is any catalogue keyed by
  locale then by message id.

  > **The threshold is now known and it sharpens the ask — 2026-08-14.** The
  > fold requires more than `KEYED_MIN` = **20** keys in a container before it
  > will call that container's keys data. Entry 29's outer map has 1,090 and
  > folds; its inner maps hold a **median of 5**, and only 70 of 1,090 reach
  > twenty. **So a qualifying specimen is one whose INNER containers hold
  > roughly 3 to 15 keys each** — few enough to fall under the threshold,
  > enough of them that a reader would still call the level a collection.
  > `FINDINGS.md`, 2026-08-14, has the mechanism and the simulation showing no
  > threshold fixes it.

  > **One document cannot justify the repair and the reason is written down
  > elsewhere.** Defect 24 has been open since 2026-08-10 on exactly this bar,
  > and the rule it established is that a fix priced against a single file is a
  > rule with one file's evidence. **`26-gharchive-scale` is not a second
  > instance** — it is larger and its worst test is 470 paths, because its
  > nesting is arrays of records rather than maps of maps.
- ~~**recursion**~~ — **filled by `02-hn-thread`**: 13 levels of self-similar
  nesting, 336 nodes, one record shape.
- ~~**heterogeneous arrays**~~ — **filled by `05-fhir-bundle`**: one `entry` array
  holding **20 resourceTypes** across 564 resources, 42 distinct key-sets, and
  exactly two fields present in all of them. `03-natural-earth` was briefly
  recorded as filling this and does not: every array in it holds one shape. What
  it filled instead is *polymorphism by depth*, `coordinates` nesting 3 for
  Polygons and 4 for MultiPolygons.
- ~~**path variance**~~ — **filled by `05-fhir-bundle`**: 44 sites, and by a
  mechanism the corpus had not seen. npm varies the *depth* of one name; FHIR's
  `value[x]` varies the *name* at one depth, eight spellings of one field. Still
  wanted: a document where the same value moves between *records* rather than
  between spellings, which is the reading `04-gharchive`'s 76 gave.
- **column-oriented**, a document storing a table as parallel arrays rather than
  as an array of records. **Added 2026-08-09 after `08-open-meteo`, and the gap
  it exposes is in this list itself.** Every axis the corpus grades reported that
  file as trivial — `0/0` ragged, no recursion, no polymorphism, one row shape —
  and it defeated the probe completely: nothing to fold, one row candidate (*the
  whole document*), and a header row invented out of a timestamp column. **The
  axes measure how ragged a document is and this one is about what a document is
  shaped like.** `06-espn-qbr` holds the dangerous variant, where the column names
  live in a parallel array and a same-length decoy sits beside it.

  > **CLOSED 2026-08-11, and it was an AXIS that was missing rather than a
  > FILE.** `design/axes.py` now measures document shape and `README.md` grades
  > it. The definition was written without reference to any corpus file — *an
  > object holding two or more sibling arrays of scalars, all the same length* —
  > and it found **exactly the two documents this note already named**. That is
  > the validation, and it is worth more than the entries it added.
  >
  > **NO NEW CORPUS FILE IS WANTED FOR THIS GAP**, which is the only part of it
  > this list owns. `design/shape-axis-predictions.md` holds the definition, the
  > predictions recorded before the run and the scoring; `FINDINGS.md` dates the
  > result. **Neither is repeated here.**
  >
  > **One limit belongs in this list, because it is about what a future specimen
  > could ever prove**: the axis cannot tell a table from a *duplicated list* —
  > two arrays of equal length, full consistency, and identical contents are
  > perfect positional alignment and not a table. **That is semantic, so no
  > document added here will fix it.**
- ~~**scale**~~ — **first reading taken by `04-gharchive`**: 50 MB and 37,883
  records cost 968 MB of memory, an 18.8x multiplier, and the gzipped form the
  file actually ships in cannot be read at all. Still wanted: something that
  genuinely does not fit, to test a sampling path that does not yet exist.

  > **SECOND READING taken 2026-08-11 by `26-gharchive-scale`, and every clause
  > above is superseded.** Same source and shape as `04-gharchive`, chosen so
  > that size is the only variable that moves. **The axis separated two files for
  > the first time.** `corpus/26-gharchive-scale/NOTES.md` owns the measurements
  > and `FINDINGS.md` dates them; **the three clauses above are wrong and are
  > kept only because the record of how a gap was misdescribed is worth having.**
  >
  > - **the 18.8x** — stale *and* never a multiplier. Peak memory is a fixed
  >   term plus a linear one, so a ratio taken at one point on that curve is not
  >   a property of the tool. **Sizing a specimen with it is exactly how entry 26
  >   came to be too small.**
  > - **"cannot read the gzipped form"** — it reads `.gz` unaided.
  > - **"a sampling path that does not yet exist"** — the sampling path EXISTS
  >   and works. **What is missing is a streaming READ**: the whole document is
  >   loaded and split into lines before the cap applies to anything.
  >
  > **STILL WANTED, and this list owns the number because it is the spec for the
  > specimen: about 6.8 GB of JSON** to exceed 16 GB. No GH Archive hour is that
  > large. **Concatenating hours would manufacture a document, which is what the
  > "real files only" rule exists to prevent — so this needs the author's
  > decision, and it is the same decision the broken/truncated gap needs.**
  >
  > **And what scale actually costs is FIDELITY, not memory** — at entry 26's
  > coverage the probe reports one keys-as-data site where the document has two.
  > **That is what a bigger specimen would test**, and it is the reason to want
  > one beyond watching the memory climb.

## Prefer documents no API has tidied

**Added 2026-08-08, after it happened twice.** `01-npm-registry` was chosen as a
polymorphism specimen and had none. `02-hn-thread` was expected to be ragged and
has one key-set across 336 nodes. Both times the API normalised on ingest.

> **The ugliness an ecosystem is famous for is usually cleaned up before the API
> hands it to you.** A corpus built from public APIs will systematically
> under-sample raggedness and polymorphism.

So weight the corpus toward documents **written by a tool, a model, or a person**
rather than served by an endpoint. An agent trace, a lockfile, a notebook and a
config file are all closer to what people are actually handed.

**The next file is an LLM or agent trace**, which closes polymorphism, NDJSON and
truncation at once — and, being written rather than served, is not normalised.

**It is the one decision waiting on the author, and it has stayed open on
purpose.** An agent trace is a transcript of the author's own conversations.
Commit a short one as-is; or scrub the string values and keep the structure, which
preserves every graded property because all of them are structural; or generate
one on a deliberately public task. `VERDICT.md` carries the same three options.

**It has to be collected, because it cannot be downloaded.** Checked 2026-08-08
against live sources: **there is no public dataset of real malformed LLM JSON.**
A HuggingFace search returns one seven-row entry with no provenance, and none of
the three main repair libraries ships a data corpus — their cases are inline test
assertions. The one exception is `majiayu000/jsonrepair-rs`, MIT, whose
`tests/fixtures/parity_cases.json` holds 36 categorised cases.

**Two licence traps, if a specimen is ever fetched from these.**
`RealAlexandreAI/json-repair` is GPL-3.0. `nlohmann/json_test_data` and
`simdjson-data` state no repo-level licence at all. Kuhn's UTF-8 file is CC BY 4.0
and needs attribution.

## Grade with the tools before grading by hand

**Added 2026-08-08, and it reverses the order used for file 01.** The tool
attempts for the exploration questions are written **before** `NOTES.md`, on a
document nobody has read yet.

The reason is that exploration is the thing being measured, and it can only be
measured once per file. File 01 was hand-graded first, so every later attempt on
it can only report what was already known — its exploration timings are worthless
and cannot be recovered. **An unseen document is the instrument. Spending it on a
hand-written probe script wastes it.**
