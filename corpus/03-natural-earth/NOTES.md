# 03 — Natural Earth admin-0 countries, as GeoJSON

**Provenance.** `d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson`,
fetched 2026-08-08. 3.9 MB, 241 features. Natural Earth is public domain. See
`fetch.sh`.

**Why this one.** The corpus had no heterogeneous-arrays specimen, and GeoJSON
carries a kind of polymorphism nothing else here has: `coordinates` is
`[[[x,y],…]]` for a Polygon and `[[[[x,y],…]]]` for a MultiPolygon — the same
field name, the same JSON type, a different **nesting depth**.

> **This is the first held-out test in the project.** `design/probe.py` was frozen
> and committed at `7385b18` (`eda5f05`) *before* this file was fetched, and run
> **once, unmodified**, under rule 5. Nothing below was repaired afterwards.

---

## Grading, measured 2026-08-08 with `design/axes.py`

| Axis | Grade | Measured |
|---|---|---|
| depth | **moderate** | 8 levels |
| recursion | **none** | 0 |
| raggedness, by absence | **none** | **0 of 68** — every feature carries every field |
| raggedness, by null | **moderate** | 6 fields null on most records |
| polymorphism | **severe, and the axis read 0** | see below |
| keys-as-data | **none** | 0 |
| heterogeneous arrays | **none** | 0 — and the first grading of this file said otherwise; see the correction below |
| path variance | **none** | 1 |
| unit ambiguity | **low** | 2 row shapes; a feature, or the collection |
| scale | **trivial** | 3.9 MB |
| *path explosion* | *derived* | 75 paths for 67 fields, ratio **1.1** — the lowest in the corpus, because there is neither keys-as-data nor recursion to mint prefixes |

## What the frozen probe got right

In 0.85 s and 39 lines, with no knowledge of GeoJSON:

- the record shape — `features[]`, 241 copies, `always geometry properties type`
- `properties` at 63 fields, one key-set, no raggedness
- **6 polymorphic fields**, all null-against-text, correctly named
- the right row: *an item of features, 241 rows × 66 cols*
- depth 8 and 241 features, both confirmed by hand

That is GeoJSON's structure rediscovered from nothing, and the row shape a person
actually wants.

## What it missed, which is the point of running it

**`coordinates` splits the file almost in half and the probe is silent.**

| geometry | count | `coordinates` nesting |
|---|---|---|
| Polygon | 122 | **3 deep** — `[[[x,y],…]]` |
| MultiPolygon | 119 | **4 deep** — `[[[[x,y],…]]]` |

Every one of those values is a JSON array. **By type the field is perfectly
homogeneous**, so `FIELDS THAT CHANGE TYPE` says nothing, `RECORD SHAPES` reports
one key-set, and the polymorphism axis measures **0** on the file chosen
specifically to have it.

> **The probe measures polymorphism by type. This document's polymorphism is in
> the nesting depth.**

**It is not a small miss.** 119 of 241 records — 49% — differ in shape at that
field, and the probe reports one record shape with one key-set. It is the single
most important fact about the format and it is absent.

**And the row candidate inherits it.** *241 rows × 66 cols* is right as far as it
goes, but flattening `coordinates` would produce two incompatible structures for
the two halves, and nothing in the output warns you.

## A correction, and it is mine rather than the probe's

**The first grading of this file also claimed `heterogeneous arrays` was severe
and the axis blind. That was wrong.** Every array in this document holds one
shape, the axis correctly reads 0, and **this file does not fill that gap.**

The error was in a throwaway script written to check the axis, not in the axis. It
labelled values with raw Python type names, so a coordinate pair like
`[100, 25.5]` came back as `{"int", "float"}` — two shapes — and 65 arrays looked
heterogeneous. `design/axes.py` maps both to `number`, as JSON does, and finds
none.

**Worth keeping because it is the same mistake in a new place.** Deriving a
verdict from something adjacent to the data rather than from the data cost this
project a depth grade of 9 that was 6, an `engines` that was not keys-as-data, and
now a heterogeneity that does not exist. **Measure the thing, with the instrument
that will be used for the real reading.**

## What this changes

**A new distinction the axes need**, and the first one earned by a held-out file
rather than by inspection:

> **polymorphism by type** — a field is text here and an object there.
> **polymorphism by depth** — a field is an array in both, nested differently.

The second is invisible to every type-based check, and it is the ordinary case in
any format that encodes dimensionality in nesting: GeoJSON geometries, tensors,
nested tabular exports.

**Not repaired.** Under rule 5 the probe stays frozen and this stands as measured.
The fix belongs to the next freeze cycle, and file 04 will test whatever it
becomes.

## The five R tools, run 2026-08-09 — and two of them beat the probe here

**The R half was `tidyr` alone until 2026-08-09.** `purrr`, `jsonlite`,
`tidyjson`, `rrapply` and `jqr` were run that day, which makes this the first
entry outside `01`/`02` with a complete R column. Three results change something
written elsewhere in the repository.

**1. Two existing tools find the polymorphism this file was chosen for, and the
frozen probe scored it `0`.**

| tool | sees the 3-deep/4-deep split? | how |
|---|---|---|
| `jqr` | **YES, generically** | leaf names grouped by the path lengths they occur at → `coordinates` at 7 and 8. No field named, four lines |
| `rrapply` | **YES, structurally** | `how="melt"` makes nesting depth a COLUMN COUNT; Polygon fills 7 level columns, MultiPolygon 8 — and the deep group is exactly the 119 |
| `jsonlite` | preserves it, silently | simplification stops at the ragged boundary and leaves a list-column; nothing says why |
| `purrr` | only if asked | one line once you suspect it; nothing raises the suspicion |
| `tidyjson` | **NO — and it reports a wrong answer** | see below |

**This is the sharpest correction the corpus has produced about its own
instrument.** The section above says polymorphism-by-depth "is invisible to every
type-based check", which is true, and concludes the axes need a new
distinction. They do — but **rrapply already had the instrument and jq can
express the test in four lines**. The gap is that neither reports it unasked.

**2. `tidyjson::json_schema` answers, and the answer is false.** Given a Polygon
and a MultiPolygon in one array it reports **one** shape, and *which* one depends
on input order:

```
one Polygon alone       {"coordinates": [[["number"]]],   "type": "string"}
one MultiPolygon alone  {"coordinates": [[[["number"]]]], "type": "string"}
[Polygon, MultiPolygon] [{"coordinates": [[["number"]]],   ...}]   <- 3 deep
[MultiPolygon, Polygon] [{"coordinates": [[[["number"]]]], ...}]   <- 4 deep
```

The control is worse: `["a", {"b":1}]` describes as `[{"b": "number"}]` in both
orders — the string vanishes. **Its schema is a constant 1,438 characters however
many features are fed in, which passes `VERDICT.md`'s O(data) test outright, and
it passes because it has decided there is one shape.** Size of description is not
sufficient; a describer that silently picks a shape always looks proportional to
structure. Its runtime is the opposite — measured at 3.8 KB/s, so the full file
extrapolates to about 17 minutes and was not run.

**3. -99 IS A MISSING-VALUE SENTINEL HERE, in 18 fields and 1,767 cells**, found
while answering question 11 — this document has no URL or email to search for, so
the sentinel was the only pattern available. `woe_id`, `adm0_a3_un` and
`adm0_a3_wb` are `-99` on **all 241 records**: columns that are entirely missing
and that every tool in this corpus reports as fully populated. jsonlite, rrapply
and jqr agree exactly on 1,767, which is a check on the number rather than on one
tool.

> **The probe's sentinel detector cannot see this.** `VERDICT.md` defect 18
> catches *a field that is a NUMBER on some records and one of very FEW STRINGS
> on others*. Here every column is uniformly typed — `pop_est` is a number
> including its `-99`s, `iso_a3` is text including its `"-99"`s — so nothing
> changes type and nothing fires. That entry says the `<= 3` bound is "a guess
> with headroom"; the real limit is narrower than the bound, and this is the
> second corpus file to carry sentinel missingness the detector misses.

**The grading rows above are unchanged.** Raggedness by absence is still `0 of
68` and by null still 6: both are correct readings of the axes as defined, and
neither axis asks whether a present value means anything. That is the gap, and it
is recorded here rather than repaired.

**4. rrapply's melt is 226% of the document — the highest describer ratio in the
corpus — on the file with `keys-as-data 0`.** `VERDICT.md` says the blowup tracks
keys-as-data; the previous high was `ijson` at 172% on the Stripe spec, which has
47 keyed sites. Collapsing array indices to `[]` takes the same information to
**68 path shapes and 0.05%**. So there are two independent routes to an O(data)
describer — every VALUE minting a key name, and every ELEMENT minting a path
index — and only the first is written down.

**And `jqr` is the control that claim never had.** The expression that returns
**3,100** on `01-npm-registry` returns **63** here, character-for-character
unchanged, and 63 is right — it is exactly the 63 property fields. Same
expression, three documents, three answers: 3,100 · 11 · 63.

## Status

Graded, used as the held-out test, and **the R half is complete** as of
2026-08-09: `purrr`, `jsonlite`, `tidyjson`, `rrapply`, `jqr`, plus `tidyr`.
**The Python half is 8 attempts, unchanged.** Under `CLAUDE.md`'s definition this
entry is now done.

## Corrected 2026-08-13, and this entry's claim to be the CONTROL is withdrawn

**The grades above are left alone.** The expression used `paths(scalars)`, which
drops every `false` and `null` leaf — see `01-npm-registry`.

| | |
|---|---|
| recorded | **63**, described as *exactly the 63 property fields* |
| corrected | **64**, against 63 property fields |

**THE MATCH WAS A COINCIDENCE OF TWO CANCELLING ERRORS.** The old expression
**missed `fips_10`**, which is `null` on every feature, and **counted
`coordinates`**, which is not a property at all but lives under `geometry`.
62 + 1 = 63.

> **So the expression is OVER by one here, not exact.** This document was the
> corpus's only claimed instance of the leaf-name expression being RIGHT — cited
> as such in `07-graphql-introspection` and in the cross-entry table in
> `12-agent-trace`. **It is right zero times.** The keys-as-data explanation for
> the size of the number is untouched; the claim that a flat document makes the
> expression correct is not.
