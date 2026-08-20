# fathom — see what is in a JSON document

<img src="images/fathom-hex.png" alt="The fathom hex sticker: a rose pink hexagon with a black border, holding a face built from JSON's own marks — an opening and a closing brace as the two eyes, a colon as the nose, and the package name as the mouth." align="right" width="170">

**Fathom first. Then parse.**

One engine, written in Rust, spoken from R and Python. You point it at a JSON
document you have never seen and it tells you what you are dealing with —
whether the file is even sound, what shapes it holds, and **what one row could
be**, with every candidate priced.

```r
fathom("thread.json")
```

That is the whole program. You named a file. What comes back is not a schema
dump: it is a page a person reads, and the last section of it is a menu of
tables you can ask for by name.

**📖 The manual is online, and every report in it was produced by running this
engine over a real document while the page was built:
<https://psychometrician.github.io/fathom-book/>**

## Why

With a data frame you always know how to start. It has already answered *what is
a row* before you arrive, so `dplyr` and `tidyr` work the same way on every
table you will ever meet. Technique transfers.

**JSON never answers that question.** Every document makes you work it out from
scratch, which is why the code you wrote for one file is useless on the next one
— even when the two are nominally the same kind of thing. That is not a skill
gap. It is a property of the format, and it is what makes this a different
problem from every other kind of data cleaning.

So the first cost is not extraction. It is **finding out what you have**, and
that is the part nothing measures.

## What it says

```
  193 KB · valid JSON · read whole file
  no duplicate keys · no NaN or Infinity · no ints past 2^53

  KEYS THAT ARE DATA

  RECORD SHAPES, FOLDED
    $   336 copies · 13 fields · 1 distinct key-set · RECURSIVE, 13 levels
      always     author children created_at created_at_i id options parent_id points story_id text title type
                 url
      SPLIT ON   type — 2 kinds, not one shape. 23% empty folded, 0% after
        comment                          335 x  10 cols   0% empty
        story                              1 x  12 cols   0% empty

  25 levels deep · 181 distinct paths

  ONE ROW COULD BE — give any of these to rows()
    the whole document                      1 rows x   13 cols
    a node at any depth (13 levels)       336 rows x   13 cols   23% empty
      └─ or 2 tables, split on type — 0% empty: comment 335, story 1
    an item of children                    25 rows x   13 cols   23% empty
```

Three things happened there.

**It checked the file is sound** before describing it — duplicate keys, `NaN`,
integers past 2^53, a truncated tail. Those are the failures that survive a
parse and corrupt an answer quietly.

**It folded 336 repeats into one shape.** The description is proportional to the
*structure*, not to the data, so a 912 MB file and a 12 KB file produce
descriptions of similar size.

**It priced every answer to "what is a row"** rather than picking one. The menu
is not decoration: give a label back to `rows()` and you get that table.

## The same document, in two languages

```r
read_json("package.json") |>
  into("versions") |>
  into("dependencies") |>
  rows("an entry of $[]")
```

```python
(fathom.read_json("package.json")
   >> fathom.into("versions")
   >> fathom.into("dependencies")
   >> fathom.rows("an entry of $[]"))
```

Both return the same 4,645 rows. **The pipe is the only difference**, because one
engine answers both and the packages are wrappers around it.

## Install

**R**, from r-universe, which builds a binary for every platform so no Rust is
needed:

```r
install.packages("fathom",
  repos = c("https://psychometrician.r-universe.dev", "https://cloud.r-project.org"))
```

**Python:**

```bash
pip install fathom-json
```

The distribution is `fathom-json` because `fathom` was taken on PyPI in 2011 by
an unrelated project. **The import is `fathom` either way.**

Neither package has a dependency, and each carries its own engine, so an
installed copy is self-contained.

> If your R is a source-only build, `install.packages` compiles rather than
> fetching the binary, and that needs [Rust](https://rustup.rs/).
> `getOption("pkgType")` says which you have. An install that can find no engine
> and no way to build one refuses, naming every place it looked, rather than
> succeeding into a package that cannot describe anything.

## The vocabulary

Seven words, and that is all of it.

| job | words | |
|---|---|---|
| read in | `read_json` | JSON, NDJSON or gzip |
| **see** | **`fathom`** | the whole shape, sound or not, row candidates priced |
| move | `into` · `back` | change where you are standing |
| search | `find` · `whichever` | locate a specific thing |
| leave | `rows` | out with a table |

`find("url")` says which paths hold one and how many values each covers.
`whichever("Rating", "rating")` takes the first spelling that is actually there,
which is what a document written by more than one producer needs.

**fathom is deliberately not a grammar.** It has no kernel, no laws and no closed
vocabulary, and it may never want them. A word is here because removing it makes
a real question unanswerable on a real file.

## Architecture

<p align="center">
  <img src="images/architecture.svg" width="100%"
       alt="Two language bindings, one for R and one for Python, each invoke the same command line as a subprocess. fathom-cli passes the path to fathom-core, the engine, which reads the JSON document itself and returns text: a description of the document, or a table. The document never travels through a binding.">
</p>

One core, so the two languages agree by construction. A binding finds the engine,
hands back its bytes, and adds nothing — anything more would be a second
implementation of the report, which is what this shape exists to prevent.

**The document goes to the engine, never through a wrapper.** That is a rule
rather than a drawing convenience: base R cannot represent JSON's number range,
so `jsonlite` reads `9007199254740993` as `…992` where Python's `json` is exact.
A parser in each binding would make the two languages disagree about exactly the
value the health verb exists to warn you about.

The JSON parser is hand-written for the same kind of reason. `serde_json` cannot
express what the health verb measures: it rejects the bare `NaN` that Python's
`json` writes, discards the duplicate keys whose silent loss is the finding, and
cannot see the sign on `-0`.

## Build from source

Requires a Rust toolchain, and the language you want to drive it from.

```bash
cargo build --release
./target/release/fathom probe corpus/02-hn-thread/source.json
```

## The corpus

Thirty real JSON documents — a package registry, a FHIR bundle, an OpenAPI
schema, a Grafana dashboard, 19.9 MB of browser-compatibility data — each graded
the same way, and each answered by the same fixed questions in **fourteen tools**
across R and Python. Toy JSON is hard in ways nobody suffers from, so the corpus
takes real files only.

`QUESTIONS.md` is the question list. It is also the vocabulary's specification: a
word belongs here only if removing it makes one of those questions unanswerable
on at least one real file.

## The book

Every report in it is computed by running the engine over the corpus at render
time rather than quoted, so a chapter can be wrong about what a number *means*
but not about what the number *is*:
<https://psychometrician.github.io/fathom-book/>

## Related

fathom sits beside **god**, a grammar of data, and **gog**, a grammar of
graphics. The chain is **fathom → god → gog**: a document becomes a table, the
table is manipulated, the result is drawn.

- <https://github.com/psychometrician/god>
- <https://github.com/psychometrician/gog>

## The name

**To fathom** something is to measure how deep it goes, and to finally understand
it. Both meanings are the job, and the understanding sense is a dead metaphor
rather than a live one — which is why it reads as a word rather than as a pun.

The hex is drawn as geometry, not type: JSON's own marks make a face, an opening
and a closing brace as the eyes and a colon as the nose. Its rose is measured
rather than chosen — in CIELAB, gog's sand is hue 82 and god's slate is 254, and
fathom takes 348, equidistant from both. **Three peers, not a progression.**

## Contributing

[`CONTRIBUTING.md`](CONTRIBUTING.md) has the rules most likely to be broken by
accident, and why each one exists. [`CHANGELOG.md`](CHANGELOG.md) is what changed,
written for somebody deciding whether to upgrade.

## License

Apache 2.0.
