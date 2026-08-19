# The fixed questions

**Every file is asked all of these, in every tool.** Same questions, every time,
or the results cannot be compared and this becomes a gallery of notebooks.

A question that turns out to be trivial in every tool should be **removed**, and a
question that is hard in every tool is where the product is.

**This file is also the vocabulary's specification.** A word belongs in fathom
only if removing it makes one of these questions unanswerable on at least one
corpus file, and no word is added without naming the question it answers and the
file that proves it. That is the project's stopping rule, and it is why this list
is fixed rather than growing.

---

## Phase 0 — is this document sound?

**Asked before anything else**, because there is no such thing as a broken data
frame, so nothing in the rectangular world prepares you for this — and because
every question below assumes an answer to it.

**⚠ Added 2026-08-08, after the probe had already been designed to report health.**
Scoring other tools as "cannot" on this question is therefore weaker evidence than
the same score on questions 1 to 18, which predate any design work. Rule 7.

0. **Is this what it claims to be, and is it whole?** Valid JSON, or NDJSON, or
   not JSON at all. Complete, or chopped off. And the **silent** damage, which is
   the half that matters: duplicate keys where the last one quietly wins,
   integers past 2^53, `NaN` or `Infinity`, a field whose value is itself an
   encoded document.

**Record whether the tool told you, or whether it parsed and said nothing.** A
parser that succeeds on a document with duplicate keys has answered "cannot",
and that is data.

## Phase 1 — exploration

The half this project claims is the real cost. Answer these **without opening the
file in an editor and reading it**, because that is the thing being measured: what
does the tool tell you about a document you have never seen?

1. **What is in here?** List the fields, at every level.
2. **How deep does it go?**
3. **What is one record?** Name every defensible answer, not just the first, and
   say **what each would cost** *(this clause added 2026-08-08, after the probe
   priced row shapes; the question itself is original)*: how many rows, how much
   of the result is empty,
   and what gets repeated. The cost changes in kind with the answer you pick —
   shallow rows give holes, deep rows give duplication — and no document declares
   either.
4. **Which fields are always present, and which are only sometimes?**
5. **Does any field change type between records?**
6. **Are any object keys actually data?**
7. **How many records are there**, under your answer to question 3?
7a. **Is anything here related by position rather than by nesting** — an array of
   values whose names live in a different array somewhere else? If so, which array
   holds the names, and how would you know you had picked the right one?
   *(**Added 2026-08-09 and CIRCULAR — do not score other tools "cannot" on
   it.** `06-espn-qbr` revealed the property and `design/probe.py` gained the
   feature that answers it in the same session, which is exactly the circularity
   rule 7 exists to flag. It is written down because rule 3 requires every file to
   be asked the same questions and five files were never asked this one. It
   becomes fair to compare on only after a tool that predates it has been given a
   real attempt.)*

**Record for each:** what you had to run, how long it took, and whether the tool
answered or you inferred it yourself.

## Phase 2 — extraction

8. **Pull three named fields into a table**, one row per record.
9. **Pull a field that is missing from some records** and keep those rows.
10. **Flatten the deepest array** into rows.
11. **Find every path whose value matches something**, such as an email or a URL.
12. **Turn the whole document into the flattest honest table**, and say what was
    lost.

## Phase 3 — durability

The questions that decide whether a tool is worth learning. These are judgments
and are recorded as such.

13. **Did you need to know the shape before writing the code?**
14. **Does the code survive the next file** of nominally the same kind, unchanged?
15. **Can you read it back a week later** without going to the reference?
16. **How many lines**, and how much of that is ceremony rather than intent?

## Phase 4 — does it work at other depths?

**The test for the hypothesis that these operations differ in depth rather than in
kind**, which is what would make fathom more than a JSON tool. See `README.md`.

Ask questions 8 through 12 again, of the same logical data at three depths:

| Depth | The data |
|---|---|
| **one** | a plain data frame |
| **two** | a data frame with a list-column |
| **N** | the original document |

17. **Does one vocabulary answer all three?** Where it does not, is the difference
    real or only spelling?
18. **Which words worked at every depth?** Those are the candidates for the
    package. A word that worked at exactly one depth belongs somewhere else.

**First answered 2026-08-09, by `first_present`, and these two questions had
stood unattempted since the first day.** One spelling of the word answered all
three depths — `first_present(r, "Rating", "rating")` on a flat record,
`first_present(r, "meta.*.Rating", …)` across a list-column, and
`first_present(doc, '*."12 Strong".Rating')` on the document. **The difference is
only which path you hand it**, which is the answer question 17 asks for.

**One word is not a vocabulary**, so question 18 has one candidate and no
comparison. `take` and `where` have still never run.
