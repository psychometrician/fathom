# Changelog

What changed, for someone deciding whether to upgrade. **Every entry is
something a person using fathom can see** — a different report, a table that was
not offered before, a message that now says what to do. Internal repairs that
change no output do not appear here; they are in the project's own record.

Both packages share one version number and are released together: `fathom` on
r-universe, `fathom-json` on PyPI. A version means the same engine in each.

> **While the series stays at `0.0.x`, every release reads as breaking** to every
> resolver, because that is what `0.0.x` means. That is deliberate: the seven
> words are not settled, and saying otherwise with `0.1.0` would be a promise
> about stability that is not yet earned.

## 0.0.1 (2026-08-20)

The first release. Both packages carry the engine they need, so an installed copy
is self-contained and neither has a dependency.

### The one verb, and what it tells you

`fathom(path)` reads a document you have never seen and returns a page rather
than a schema dump.

- **It checks the file is sound before describing it** — duplicate keys, a bare
  `NaN` or `Infinity`, integers past 2^53, a truncated tail, a `-0`. Those are
  the failures that survive an ordinary parse and corrupt an answer quietly, and
  the parser is hand-written because `serde_json` cannot see most of them.
- **It folds repeats into one shape.** A document with 336 identical records is
  described once, so the output is proportional to the *structure* rather than to
  the data — a 912 MB file and a 12 KB file produce descriptions of similar size.
- **It names keys that are data.** A registry keyed by version number, four
  levels deep, is a table rather than four thousand distinct fields.
- **It splits a shape that is really several.** Where one record type covers two
  kinds of thing, the page says so and prices each separately, rather than
  reporting one table that is 23% empty.
- **It prices every answer to "what is a row"** instead of choosing one, and says
  how many rows and columns each would give you, and how empty.

### Leaving with a table

- **`rows(label)` takes a label the report just printed.** The menu is not
  decoration: every candidate it names resolves to the table it promised.
- **`into()` and `back()` move you** through a document without writing a path.
- **`find()` says which paths hold a name** and how many values each covers.
- **`whichever()` takes the first spelling that is actually there**, which is
  what a document written by more than one producer needs.
- **`read_json()` reads JSON, NDJSON and gzip**, and streams a large NDJSON file
  rather than holding it.

### The same seven words in both languages

R and Python differ by the pipe and nothing else. One engine answers both, so the
two cannot drift: every corpus document and every candidate the menu names is
compared between them on every change.

### Sampling

A very large document is read by sampling rather than in full, which is what
keeps a description quick. **The report says so when it does**, so a number you
are reading is never quietly partial.
