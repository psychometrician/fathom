# rrapply — Jupyter notebook, Norvig Advent-2021
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply 1.2.8 (+ jsonlite 2.0.0 to parse)
#  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
#  measured      2026-08-10
#  run           cd corpus/11-jupyter-notebook/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             7   NO                  yes
#   2 how deep                                    3   NO                  yes
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 5   NO                  yes
#   5 does any field change type                  5   NO                  yes
#   6 are any object keys data                    4   NO                  PARTLY
#   7 how many records                            3   NO                  yes
#   8 three named fields to a table               5   YES                 PARTLY
#   9 a field missing from some rows              4   YES                 yes
#  10 flatten the deepest array                   4   NO                  yes
#  11 find every path matching something          5   NO                  yes
#  12 flattest honest table                       5   NO                  PARTLY
#  13 needed the shape in advance?                    NO for almost all of it
#  14 survives the next file unchanged?               YES — melt names nothing
#  15 readable a week later?                          the melt yes; `how=` no
#  16 lines, and how much is ceremony?                ~50, melt is one call
#
# WHY THIS TOOL MATTERS HERE. `how="melt"` turns a whole document into a long
# frame of path-plus-value with NOTHING named in advance — the closest thing in
# either language to walking a document you have never seen. VERDICT.md records
# it at 226% of 03-natural-earth, the corpus high. This document is the other
# extreme and the contrast is the measurement.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

# ── Q1, Q2, Q7. the melt, and everything it answers at once ──────────────────
m <- rrapply(doc, how = "melt")
cat(sprintf("\n1. melt: %d leaf rows x %d columns\n", nrow(m), ncol(m)))
lvl <- ncol(m) - 1L
cat(sprintf("   %d L-columns, so the deepest leaf is %d levels down.\n", lvl, lvl))
# The corpus's comparable statistic is the cost of LISTING EVERY PATH —
# `sum(nchar(paths)) + length(paths)`, the same expression
# corpus/03-natural-earth/r/try-rrapply.R uses — and not the printed frame.
full <- apply(m[, seq_len(lvl)], 1, \(r) paste(r[!is.na(r)], collapse = "."))
chars <- sum(nchar(full)) + length(full)
cat(sprintf("   listing every path costs %s chars for a 1,114,184-byte file (%.0f%%)\n",
            format(chars, big.mark = ","), 100 * chars / 1114184))
cat("   VERDICT.md measures this melt at 226% of 03-natural-earth, the corpus\n")
cat("   high, driven by 99,566 array elements minting path indices. Here the\n")
cat("   document has 37 distinct paths and the melt stays small — the ratio\n")
cat("   tracks how many SIBLINGS there are, not how deep or how big.\n")

fold <- function(x) if (is.na(suppressWarnings(as.integer(x))) && !is.null(x)) x else "[]"
paths <- apply(m[, seq_len(lvl)], 1, \(r) {
  r <- r[!is.na(r)]
  paste(vapply(r, fold, ""), collapse = ".")
})
tab <- sort(table(paths), decreasing = TRUE)
cat(sprintf("\n   folded to %d path shapes:\n", length(tab)))
for (i in seq_len(min(8, length(tab))))
  cat(sprintf("     %-46s %6d\n", names(tab)[i], tab[[i]]))
cat("   The fold is mine. rrapply gives the long frame; collapsing the index\n")
cat("   columns is the step that turns it from data into a description.\n")

cat(sprintf("\n2. depth: %d\n", lvl))
cat(sprintf("\n7. cells: %d   outputs: %d\n", length(doc$cells),
            sum(vapply(doc$cells, \(c) length(c$outputs), 1L))))

# ── Q4, Q5. always vs sometimes, and types ───────────────────────────────────
cells_m <- m[m$L1 == "cells", ]
keys <- table(cells_m$L3[!is.na(cells_m$L3)])
cat("\n4. keys appearing under cells[], straight off the melt:\n")
for (k in names(sort(keys, decreasing = TRUE)))
  cat(sprintf("     %-18s %6d leaf rows\n", k, keys[[k]]))
cat("   These are LEAF counts, not presence counts — `source` is 1,671 because\n")
cat("   it holds 1,671 lines. The melt cannot answer Q4 as presence without a\n")
cat("   group-by, which is the price of turning structure into rows.\n")

cat("\n5. classes of the value column, for the cells[] keys that are LEAVES:\n")
for (k in c("cell_type", "execution_count")) {
  v <- cells_m$value[!is.na(cells_m$L3) & cells_m$L3 == k]
  cat(sprintf("     %-18s %s\n", k, paste(unique(vapply(v, \(x)
    if (is.null(x)) "NULL" else class(x)[[1]], "")), collapse = ", ")))
}
cat("   Only the leaf keys are shown. `source` and `outputs` are containers, so\n")
cat("   grouping their DESCENDANTS by L3 reports the classes of things three\n")
cat("   levels down as though they were the field's own — a real hazard of the\n")
cat("   melt, which flattens away the distinction between a field and its\n")
cat("   subtree.\n")
cat("   `execution_count` shows integer and NULL — the melt KEEPS a null as a\n")
cat("   row, which is more than pandas, polars or duckdb manage.\n")

# ── Q6. are any object keys data ─────────────────────────────────────────────
# L5 and L6, not L4 and L5: the path is cells / index / outputs / index / data
# / mime, so `data` sits at the FIFTH level. Getting this wrong returns an
# empty table rather than an error, which is the melt's own quiet failure mode.
mimes <- table(m$L6[!is.na(m$L5) & m$L5 == "data"])
cat(sprintf("\n6. PARTLY. mime keys at L6 under data: %s\n",
            paste(sprintf("%s %d", names(mimes), mimes), collapse = ", ")))
cat("   Those are LEAF counts again, and the two disagree for a reason:\n")
cat("   `image/png` is 17 because its value is one string, `text/plain` is 233\n")
cat("   because its value is an array of 233 lines across 80 outputs. The melt\n")
cat("   cannot say `text/plain` occurs 80 times without a group-by.\n")
cat("   The melt puts them in a COLUMN, which is structurally the right place\n")
cat("   for a key that is a value — but `cell_type` and `output_type` are in\n")
cat("   the same column at the same level, so rrapply has not distinguished\n")
cat("   them, it has merely stopped privileging either.\n")

# ── Q3. what is one record ───────────────────────────────────────────────────
cat("\n3. CANNOT. The melt has exactly one row shape — path plus value — so\n")
cat("   there is nothing to choose between and nothing priced. That is the\n")
cat("   cost of the universal answer.\n")

# ── Q8, Q9. three named fields, one missing from some ────────────────────────
tbl <- data.frame(
  type = vapply(doc$cells, \(c) c$cell_type, ""),
  n = vapply(doc$cells, \(c) if (is.null(c$execution_count)) NA_integer_
                             else as.integer(c$execution_count), 1L),
  lines = vapply(doc$cells, \(c) length(c$source), 1L))
cat(sprintf("\n8. PARTLY: %d rows, built with base R. rrapply's `how=\"bind\"`\n",
            nrow(tbl)))
cat("   wants a regular nested list and this one is ragged, so the extraction\n")
cat("   falls back to vapply. rrapply describes far better than it extracts.\n")
print(head(tbl, 3))
cat(sprintf("\n9. n is NA on %d of %d rows, all kept.\n",
            sum(is.na(tbl$n)), nrow(tbl)))

# ── Q10. flatten the deepest array ───────────────────────────────────────────
tp <- m[!is.na(m$L5) & m$L5 == "data" & !is.na(m$L6) & m$L6 == "text/plain", ]
cat(sprintf("\n10. text/plain leaf rows: %d\n", nrow(tp)))
cat("   Filtering the melt on two path columns, which needed no descent and\n")
cat("   no `enter_object` — the whole document was already flat.\n")

# ── Q11. every path whose value matches ──────────────────────────────────────
isurl <- vapply(m$value, \(v) is.character(v) && grepl("https?://", v), TRUE)
hit <- m[isurl, ]
cat(sprintf("\n11. %d values contain a URL, at path shape(s): %s\n", sum(isurl),
            paste(unique(paths[isurl]), collapse = ", ")))
cat("   One vapply over a column, because the melt already turned every value\n")
cat("   in the document into a row. This is the question rrapply is best at\n")
cat("   and it needed nothing named.\n")

# ── Q12. flattest honest table ───────────────────────────────────────────────
cat(sprintf("\n12. the melt IS the flattest honest table: %d x %d.\n",
            nrow(m), ncol(m)))
cat(sprintf("   And PRINTING it costs %s chars — R pads every row to the widest\n",
            format(nchar(paste(capture.output(print(m)), collapse = "")),
                   big.mark = ",")))
cat("   value in the column, and the widest value is a 22,732-character base64\n")
cat("   PNG. That is a printing artifact rather than a description size, and it\n")
cat("   is recorded separately so it is not read as one — but it is what a\n")
cat("   person who types `m` at the console actually gets.\n")
cat("   WHAT IS LOST: nothing, and that is the problem — it is one row per\n")
cat("   LEAF, so 1,671 source lines are 1,671 rows and the 17 base64 PNGs are\n")
cat("   17 rows carrying 79% of the file's bytes. Honest, complete, and not a\n")
cat("   table anybody wanted.\n")
