# fathom, for Python

**See what is in a JSON document before you parse it.**

```python
from fathom import fathom

fathom("package-lock.json")
```

One verb. It reads the file — JSON, NDJSON, or gzipped — and describes it:
whether it is sound, the shapes it holds folded to their structure, the fields
that change type, and **what one row could be, with every candidate priced**.

```
> fathom('package-lock.json')

  786 KB · valid JSON · read whole file
  no duplicate keys · no NaN or Infinity · no ints past 2^53

  ONE ROW COULD BE — give any of these to rows()
    the whole document                      1 rows x    5 cols
    an entry of packages                1,657 rows x 1394 cols   99% empty
    an entry of dependencies            4,645 rows x    2 cols
```

**The output is proportional to the STRUCTURE, not to the data.** A 912 MB file
and a 12 KB file produce descriptions of similar size, which is why this is
worth running on something too large to open.

## What it needs

The `fathom` binary, which does all the work. This package is a thin wrapper
that runs it as a subprocess and hands back what it printed — no compiled
extension, no FFI, and no dependencies. The binary is looked for in three
places, in this order:

1. `$FATHOM_BIN`, if set
2. `fathom` on your `PATH`
3. `target/release/fathom`, in the working directory or any directory above it

Build it with `cargo build --release` from the project root.

## Status

**This is an investigation, not a finished package.** It ships one verb because
one verb is what has been built and measured; the extraction vocabulary —
`rows`, `find`, `whichever` — is designed and not yet released. See the
project's `README.md`, `VERDICT.md` and `design/vocabulary.md`.

Apache 2.0.
