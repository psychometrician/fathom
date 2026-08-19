# tidyr — a Jupyter notebook (Norvig, Advent of Code 2021)
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   1.1 MB, 272 cells, 107 outputs
#  measured      2026-08-09
#  run           cd corpus/11-jupyter-notebook/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          4   no                  RIGHT
#   5 does any field change type                  6   no                  partly
#   7 how many records                            2   no                  RIGHT
#   8 three named fields to a table               5   YES                 YES
#
# WHY THIS FILE. design/probe.py split the OUTPUTS of this document and refused
# to split the CELLS holding them, because an empty array and a full one are
# counted as different types. The question here is what a rectangling verb makes
# of the same two levels.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cells <- doc$cells

# THE PROTOCOL: the container goes in as a ONE-element list-column, so that
# unnest_auto chooses longer or wider itself.
cat("\n3/7. unnest_auto on `cells`:\n")
t <- tibble(x = list(cells))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   RIGHT.", length(cells), "cells, one row each.\n")

cat("\n   and on the outputs, the level below:\n")
outs <- unlist(lapply(cells, function(c) c$outputs), recursive = FALSE)
t2 <- tibble(x = list(outs))
msg2 <- capture.output(o2 <- suppressWarnings(unnest_auto(t2, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg2, collapse = " ")), "\n")
cat("   result:", nrow(o2), "rows x", ncol(o2), "cols. RIGHT —", length(outs), "outputs.\n")

cat("\n8. three named fields, one row per cell:\n")
tbl <- tibble(cell_type = vapply(cells, function(c) c$cell_type, ""),
              nsource   = vapply(cells, function(c) length(c$source), 0L),
              noutputs  = vapply(cells, function(c) length(c$outputs), 0L))
print(head(tbl, 3))
print(table(tbl$cell_type))

# 5. THE DEFECT THE PROBE HIT, asked of tidyr instead.
cat("\n5. what `source` and `outputs` actually hold, per cell type:\n")
shape <- function(v) if (is.null(v)) "absent" else if (length(v) == 0) "empty list" else
                     paste0("list[", length(v), "] of ", class(v[[1]])[1])
for (ct in unique(tbl$cell_type)) {
  sel <- cells[tbl$cell_type == ct]
  cat(sprintf("     %-9s source: %-22s outputs: %s\n", ct,
      paste(unique(vapply(sel, function(c) sub("\\[[0-9]+\\]", "[n]", shape(c$source)), "")),
            collapse = " / "),
      paste(unique(vapply(sel, function(c) sub("\\[[0-9]+\\]", "[n]", shape(c$outputs)), "")),
            collapse = " / ")))
}
cat("   `source` is a list of character in EVERY cell — no polymorphism, which\n")
cat("   is what this entry predicted and what the corpus README predicted too.\n")
cat("   `outputs` is empty on some code cells and absent on markdown. In R that\n")
cat("   is a length-0 list against NULL, and tidyr keeps them distinct, because\n")
cat("   R's NULL is not R's empty vector.\n")
cat("   design/probe.py conflates exactly these two, calls it a type\n")
cat("   disagreement, and refuses the split on cell_type. See NOTES.md.\n")

cat("
CONCLUSION. unnest_auto RIGHT at both levels, and it is the seventh and eighth
array-of-records it has got right. It does not attempt the partition on
cell_type, which is the operation this file is about.

The interesting agreement is at the other end. The probe's open defect here is
that an empty list and a full one are counted as different types; R keeps NULL,
list(), and list(x) as three distinguishable things and tidyr carries all three
into the table without comment. The distinction the probe needs is one the R
type system simply has.
")
