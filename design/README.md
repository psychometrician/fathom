# design

The instrument and the decisions behind it.

| | |
|---|---|
| `probe.py` | **the oracle.** The Rust core is *defined* as agreeing with it, so a disagreement is the core's fault by construction. `test/parity.py` measures that on every corpus document. |
| `rows.py` | the extraction sketch the vocabulary grew out of |
| `vocabulary.md` | **which words there are, and what each one means** |
| `implementation.md` | why one core behind a subprocess, rather than FFI |
| `coverage.py`, `axes.py`, `growth.py`, `parity.py` | instruments that read the probe's output; they import it and never modify it |
| the rest | one-off scripts, each written to settle one question and kept as the evidence for it |

**`probe.py` is frozen.** It is committed at a recorded hash, and a document held
out from its development is run against it once, unmodified, so that whatever it
gets wrong is a finding rather than something quietly repaired. Changing it is a
deliberate event, not a convenience.

## Some comments here point at documents that are not in this repository

`CLAUDE.md`, `FINDINGS.md` and `VERDICT.md` are cited throughout these files and
you will not find them. They are the **working record** — the agreement a session
works under, every measurement with the file and the day it was taken, and the
handoffs between sessions — and they are process rather than product, so they are
kept privately.

The references are deliberate rather than broken, and what those documents own is
stated publicly elsewhere: **what the words mean** is `vocabulary.md`, **why the
architecture is what it is** is `implementation.md`, **what the questions are** is
`QUESTIONS.md` at the root, and **what a claim is worth** is the book, which
recomputes every report from the real corpus at render time rather than quoting a
number.

<https://psychometrician.github.io/fathom-book/>
