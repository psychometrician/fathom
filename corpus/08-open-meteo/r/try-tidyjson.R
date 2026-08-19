# tidyjson — Open-Meteo hourly forecast, the columnar document
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed below)
#  file          ../source.json   12 KB, depth 3, 24 paths, 14 fields,
#                                 every raggedness axis 0, row shapes 1
#  measured      2026-08-10
#  run           cd corpus/08-open-meteo/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           6   NO                  yes
#   3 what is one record                        8   NO                  WRONG
#   4 always present vs sometimes               4   NO                  yes
#   7 how many records                          3   YES                 partly
#   8 three named fields to a table             6   YES                 partly
#  12 flattest honest table                     5   YES                 partly
#  13 needed the shape in advance?                  no for 1, 4
#  16 lines, and how much is ceremony?              see the conclusion
#
#  Q3 is scored WRONG. `gather_array` over `hourly.time` gives 336 rows of one
#  column, which is a real table and the wrong one.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. tidyjson's model is **a table of documents**, and on
# `04-gharchive` that matched NDJSON so exactly it gave the corpus's cleanest
# answer to question 3. **This document is the opposite case**: one document,
# no sibling objects anywhere, and a table stored column-wise. The tool whose
# model fitted best on one file should fit worst here, and that pair is worth
# more than either reading alone.
suppressMessages({library(tidyjson); library(jsonlite)})
cat(sprintf("R %s, tidyjson %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyjson"), packageVersion("jsonlite")))

path <- "../source.json"
raw  <- paste(readLines(path, warn = FALSE), collapse = "")
doc  <- fromJSON(path, simplifyVector = FALSE)

# ── Q1. ──────────────────────────────────────────────────────────────────────
cat("\n1. what is in here — json_schema, and this file is small enough to run:\n")
t0 <- Sys.time()
s  <- as.character(json_schema(raw))
cat(sprintf("   %.1f s, %s chars for %s bytes (%.0f%%)\n",
            as.numeric(difftime(Sys.time(), t0, units = "secs")),
            format(nchar(s), big.mark = ","),
            format(file.size(path), big.mark = ","),
            100 * nchar(s) / file.size(path)))
cat(sprintf("   %s\n", substr(s, 1, 300)))
cat("   CORRECT AND USEFUL. Five arrays of numbers under `hourly`, five strings\n")
cat("   under `hourly_units`, scalars at the top. On a document with one shape\n")
cat("   json_schema describes that shape, which is the pattern `06-espn-qbr`\n")
cat("   established: the losses are about heterogeneity, not about the function.\n")

# ── Q3 / Q7. WHERE THE MODEL DOES NOT FIT. ───────────────────────────────────
cat("\n3/7. what is one record — and the model does not fit this document:\n")
g <- raw |> enter_object("hourly") |> enter_object("time") |> gather_array()
cat(sprintf("   enter_object('hourly','time') |> gather_array() -> %d rows x %d cols\n",
            nrow(g), ncol(g)))
cat("   336, and it is ONE COLUMN. To get the table you must do that five\n")
cat("   times and join on the array index:\n")
cols <- names(doc$hourly)
# Each part must carry a UNIQUELY NAMED column. The first draft called them all
# `val`, so the merge chain produced `val.x`/`val.y` collisions and returned a
# 0-row frame under a confident header — a table with the right column names and
# no rows, which is exactly the kind of wrong answer this corpus keeps recording.
# ⚠ `enter_object(!!k)` — THE `!!` IS LOAD-BEARING AND ITS ABSENCE IS SILENT.
# `enter_object` uses non-standard evaluation, so `enter_object(k)` with a
# character VARIABLE looks for a field literally named `k`, finds none, and
# returns **0 rows with no error or warning**. The literal
# `enter_object("temperature_2m")` returns 336. The first draft of this file
# looped with the variable and printed a confident `0 x 6` table with the right
# column names and no rows.
#
# Measured: variable 0 rows, `!!k` 336, `!!sym(k)` 336, `do.call` 336.
# A silent zero-row result from a loop is the same class of failure this corpus
# keeps recording — an answer rather than an error.
parts <- lapply(cols, function(k) {
  d <- raw |> enter_object("hourly") |> enter_object(!!k) |> gather_array() |>
    (\(x) as.data.frame(x))()
  out <- data.frame(i = d$array.index, v = as.character(d$..JSON))
  names(out)[2] <- k
  out
})
tbl <- Reduce(function(a, b) merge(a, b, by = "i"), parts)
cat(sprintf("   five gather_arrays + four merges -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl[, 1:4], 2))
cat("   SCORED WRONG ON QUESTION 3, and the reason is structural rather than a\n")
cat("   defect. `gather_array` turns ONE array into rows. This document is five\n")
cat("   parallel arrays that are together one table, and tidyjson has no verb\n")
cat("   that relates them — every path through the library treats them as\n")
cat("   independent. Compare `as.data.frame(fromJSON(path)$hourly)`, which is\n")
cat("   the same 336 x 5 in one expression, in try-jsonlite.R.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
kt <- raw |> gather_object() |> json_types()
print(table(as.character(kt$name), as.character(kt$type)))
cat("   Nine top-level keys, each once, no raggedness to report — NOTES.md\n")
cat("   grades 0/0 and 0. `gather_object` is honest and there is nothing here\n")
cat("   for it to find.\n")

# ── Q8 / Q12. ────────────────────────────────────────────────────────────────
cat("\n8/12. three named fields:\n")
cat(sprintf("   from the merged table: %s\n",
            paste(names(tbl)[2:4], collapse = ", ")))
cat(sprintf("   %d rows, and it took five gather_arrays and four merges to get\n",
            nrow(tbl)))
cat("   there. PARTLY: the answer is right and the route is the longest of the\n")
cat("   five tools in this directory.\n")

cat("
CONCLUSION — the tool whose model fitted best on `04-gharchive` fits worst here,
and the pair is the useful result.

  On `04-gharchive`, tidyjson's model — **a table of documents** — matched NDJSON
  so exactly that `as.tbl_json(readLines(...))` gave 37,883 records with nothing
  known in advance, the cleanest question-3 answer in the corpus.

  **Here the same model has nothing to hold.** There is one document, no sibling
  objects anywhere, and the data is five parallel arrays that are together one
  table. `gather_array` turns ONE array into rows, so getting the real table
  takes **five `gather_array` calls and four merges on the array index** — the
  longest route of any tool in this directory, for a table
  `as.data.frame(fromJSON(path)$hourly)` produces in one expression.

  That is not a defect. It is what happens when a record-oriented library meets
  a column-oriented document, and it is the exact mirror of what happens to
  fathom: `NOTES.md` says *operation 1 has nothing to fold here*, and tidyjson
  has nothing to gather. **Both tools are organised around the same assumption —
  that a document is a collection of things — and this file is a document that
  is a collection of columns.**

  `json_schema` meanwhile is correct and useful, at 12 KB with one shape. That
  is the third document confirming what `06-espn-qbr` settled: given one shape it
  describes that shape; the losses are about heterogeneity.
")
