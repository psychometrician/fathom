# jsonlite — Jupyter notebook, Norvig Advent-2021
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite 2.0.0
#  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
#  measured      2026-08-10
#  run           cd corpus/11-jupyter-notebook/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             7   NO                  PARTLY
#   2 how deep                                    -   -                   CANNOT
#   3 what is one record                          5   NO                  PARTLY
#   4 always present vs sometimes                 5   YES                 yes
#   5 does any field change type                  4   YES                 PARTLY
#   6 are any object keys data                    3   YES                 CANNOT
#   7 how many records                            2   NO                  YES
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              4   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          -   -                   CANNOT
#  12 flattest honest table                       5   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 1, 3, 7
#  14 survives the next file unchanged?               simplification will differ
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~50, little ceremony
#
# WHAT MAKES THIS FILE DIFFERENT FROM THE OTHER FOUR. jsonlite is the only R
# tool here that SIMPLIFIES by default, turning arrays of like objects into data
# frames without being asked. On this document that is mostly a gift and once a
# trap, and both are measured below.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

# ── Q1. what is in here ──────────────────────────────────────────────────────
# The DEFAULT parse, which is what a person actually types.
d <- fromJSON("../source.json")
cat(sprintf("\n1. root: %s\n", paste(names(d), collapse = ", ")))
cat(sprintf("   cells is a %s: %d x %d — jsonlite SIMPLIFIED 272 heterogeneous\n",
            class(d$cells)[[1]], nrow(d$cells), ncol(d$cells)))
cat(sprintf("   objects into a data frame with columns %s\n",
            paste(names(d$cells), collapse = ", ")))
cat("   That is a real answer to Q1 and no other R tool here gives one unasked.\n")
str_lines <- length(capture.output(str(d, max.level = 3)))
cat(sprintf("   `str(d, max.level=3)` is %d lines. Unbounded it is %d.\n",
            str_lines, length(capture.output(str(d)))))
cat("   VERDICT.md measures str() at 5,289 lines on npm; this document is\n")
cat("   regular enough that str() is genuinely usable, which npm was not.\n")

# ── Q2. how deep ─────────────────────────────────────────────────────────────
cat("\n2. CANNOT. No depth verb, and after simplification the nesting is a mix\n")
cat("   of data-frame columns and list-columns, so even a hand count would be\n")
cat("   counting jsonlite's reshaping rather than the document's depth.\n")

# ── Q7, Q4. how many records, always vs sometimes ────────────────────────────
# `nrow()` on a simplified `outputs` returns integer(0) for the 28 cells whose
# outputs array is EMPTY — a length-0 answer where a 0 was wanted, which killed
# the first version of this line. Simplification turns three different things
# (absent, empty, populated) into three different R objects.
nout <- sum(vapply(d$cells$outputs,
                   \(o) if (is.data.frame(o)) nrow(o) else 0L, 1L))
cat(sprintf("\n7. %d cells, %d outputs\n", nrow(d$cells), nout))

cat("\n4. simplification turns absence into NA, so the frame answers it:\n")
raw0 <- fromJSON("../source.json", simplifyVector = FALSE)
present <- table(unlist(lapply(raw0$cells, names)))
for (k in names(d$cells))
  cat(sprintf("     %-18s %4d present (unsimplified) of %d\n",
              k, present[[k]], nrow(d$cells)))
cat("   Counted on the UNSIMPLIFIED parse, because the simplified frame cannot\n")
cat("   answer it: `execution_count` is NA on 141 rows there — 140 absences\n")
cat("   plus the 1 explicit null — and the two are indistinguishable once\n")
cat("   simplification has run. Presence is 132. Two parses, two answers.\n")

# ── Q5. does any field change type ───────────────────────────────────────────
raw <- fromJSON("../source.json", simplifyVector = FALSE)
ec <- unique(vapply(raw$cells, \(c) if (is.null(c$execution_count)) "null-or-absent"
                                    else class(c$execution_count)[[1]], ""))
cat(sprintf("\n5. PARTLY. execution_count classes: %s\n", paste(ec, collapse = ", ")))
cat("   And the trap: `d$cells$source` is a LIST-COLUMN of character vectors,\n")
cat("   because every cell's source is an array. Had ONE cell held a bare\n")
cat("   string — which nbformat permits — jsonlite would still have built a\n")
cat("   list-column and said nothing. Simplification hides polymorphism by\n")
cat("   absorbing it, which is the failure VERDICT.md records for polars.\n")

# ── Q6. are any object keys data ─────────────────────────────────────────────
cat("\n6. CANNOT. The mime types become COLUMN NAMES of the simplified `data`\n")
cat("   frame — `text/plain` and `image/png` sit where `output_type` sits, and\n")
cat("   nothing marks one as a value and the other as a field.\n")

# ── Q3. what is one record ───────────────────────────────────────────────────
cat("\n3. jsonlite PROPOSES one by simplifying: a cell, 272 rows. That is a\n")
cat("   genuine contribution and it is also unexamined — it proposes the\n")
cat("   shallowest array it meets and never mentions the 107-row output table\n")
cat("   underneath, nor what either costs in holes.\n")

# ── Q8, Q9. three named fields, one missing from some ────────────────────────
tbl <- data.frame(type = d$cells$cell_type, n = d$cells$execution_count,
                  lines = lengths(d$cells$source))
cat(sprintf("\n8. three fields, one row per cell: %d rows\n", nrow(tbl)))
print(head(tbl, 3))
cat(sprintf("\n9. n is NA on %d of %d rows, all kept — for free, because\n",
            sum(is.na(tbl$n)), nrow(tbl)))
cat("   simplification already filled the absent cells with NA.\n")

# ── Q10. flatten the deepest array ───────────────────────────────────────────
tp <- unlist(lapply(d$cells$outputs, \(o) {
  if (is.null(o) || !"data" %in% names(o)) return(NULL)
  unlist(o$data[["text/plain"]])
}))
cat(sprintf("\n10. text/plain exploded to lines: %d rows\n", length(tp)))
cat("   Three guards — NULL outputs, missing `data`, missing `text/plain` —\n")
cat("   because simplification produced a ragged frame-of-frames.\n")

# ── Q11. every path whose value matches ──────────────────────────────────────
cat("\n11. CANNOT. jsonlite parses and serialises; it has no search of any\n")
cat("   kind. The 53 source lines mentioning a URL need a hand-written walk,\n")
cat("   which is try-purrr.R's answer and not this one's.\n")

# ── Q12. flattest honest table ───────────────────────────────────────────────
fl <- flatten(d$cells)
cat(sprintf("\n12. flatten(d$cells): %d x %d, columns: %s\n", nrow(fl), ncol(fl),
            paste(names(fl), collapse = ", ")))
cat("   `flatten()` only unpacks data-frame COLUMNS, so `outputs` and `source`\n")
cat("   stay as list-columns and the deepest two levels never arrive.\n")
cat("   WHAT IS LOST: the cell/output pairing, and the 17 base64 PNGs which\n")
cat("   are 79% of the file's bytes sitting inside a nested list-column.\n")
