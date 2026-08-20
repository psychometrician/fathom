# fathom — see what is in a JSON document, for R

**Fathom first. Then parse.**

With a data frame you always know how to start: it has already answered *what is
a row* before you arrive. JSON never answers that question, so the code you wrote
for one file is useless on the next one — even when the two are nominally the
same kind of thing.

fathom is the first thing you reach for. You point it at a document you have
never seen and it tells you what you are dealing with.

```r
library(fathom)

fathom("thread.json")
```

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

Three things happened there that are the whole point. It **checked the file is
sound** before describing it. It **folded 336 repeats into one shape**, so the
description is proportional to the structure rather than to the data — a 912 MB
file and a 12 KB file produce descriptions of similar size. And it **priced every
answer to "what is a row"**, rather than picking one for you.

## Then take the table you want

The menu is not decoration: give a label back to `rows()` and you get that table.

```r
rows("thread.json", "an item of children")
```

Deeper, when the thing you want is nested — the pipe reads as a sentence:

```r
read_json("package.json") |>
  into("versions") |>
  into("dependencies") |>
  rows("an entry of $[]")
```

## Seven words, and that is the whole vocabulary

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

**The same seven words, spelled the same way, work in Python.** One engine
answers both, so the two languages cannot drift apart.

## Installing

```r
install.packages("fathom",
  repos = c("https://psychometrician.r-universe.dev", "https://cloud.r-project.org"))
```

That is a binary, with no toolchain to set up. Installing from the source tarball
compiles the engine during installation, which takes a few seconds and needs
[Rust](https://rustup.rs/); an install that can find no engine and no way to
build one refuses, naming every place it looked, rather than succeeding into a
package that cannot describe anything.

The package has **no dependencies** and carries its own engine.

## One name this package masks

`find`. The vocabulary's `find` takes the word's everyday meaning, `utils::find`
stays one `utils::` away, and loading the package says so once. The other six
words shadow nothing.

## It samples, by default

A very large document is read by sampling rather than in full, which is what
keeps the description quick. `fathom()` says so in its own output when it does.

The manual, with every report in it computed by running this engine over real
documents, is at <https://psychometrician.github.io/fathom-book/>.
