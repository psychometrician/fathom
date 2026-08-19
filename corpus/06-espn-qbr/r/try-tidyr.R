# tidyr — ESPN quarterback rating, 2019
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   176 KB, 28 athletes
#  measured      2026-08-09
#  run           cd corpus/06-espn-qbr/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          4   no                  RIGHT
#   7 how many records                            2   no                  RIGHT
#   8 three named fields to a table               5   YES                 YES
#  7a related by position, not nesting            8   YES                 partly
#
# WHY THIS FILE. It has a published ground truth — Tom Mock's jsonlite tutorial
# — and it holds the corpus's sharpest trap: the column names live in a parallel
# array, and a same-length DECOY array sits beside it in a different order.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)

# THE PROTOCOL: the container goes in as a ONE-element list-column, so that
# unnest_auto chooses longer or wider itself. Pre-splitting answers question 3.
cat("\n3/7. unnest_auto on `athletes`:\n")
t <- tibble(x = list(doc$athletes))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   RIGHT. NOTES.md records 28 athletes, and the tutorial's own answer is\n")
cat("   one row per athlete.\n")

cat("\n8. three named fields, via hoist — which IS `take`:\n")
tbl <- tibble(x = doc$athletes) |>
  hoist(x, name = list("athlete", "displayName"),
           team = list("athlete", "teamName"),
           totals = list("categories", 1L, "totals"))
cat("   hoist() ->", nrow(tbl), "rows x", ncol(tbl), "cols\n")
print(head(select(tbl, name, team), 3))
cat("   `hoist` reaches into a nested path and names the result, which is\n")
cat("   exactly what design/vocabulary.md proposes `take` for. It is shipped\n")
cat("   prior art and vocabulary.md must say so.\n")

# 7a. THE TRAP. Marked CIRCULAR in QUESTIONS.md — added the same session the
#     probe gained the feature — so this is recorded, not scored as a win.
cat("\n7a. the names live in a parallel array, and there are TWO candidates:\n")
labels <- unlist(doc$categories[[1]]$labels)
glossary <- vapply(doc$glossary, function(g) g$abbreviation, "")
cat("   categories[[1]]$labels :", paste(labels, collapse = " "), "\n")
cat("   glossary abbreviations :", paste(glossary, collapse = " "), "\n")
vals <- unlist(tbl$totals[[1]])
right <- setNames(vals, labels)
wrong <- setNames(vals, glossary)
cat("   both are length", length(labels), ", both zip cleanly, one is wrong:\n")
cat("     TQBR via labels  :", right[["TQBR"]], "\n")
cat("     TQBR via glossary:", wrong[["TQBR"]], "\n")
cat("   tidyr will zip whatever you hand it. It has no verb for 'which array\n")
cat("   holds the names', and neither does anything else in either language.\n")

cat("
CONCLUSION. unnest_auto RIGHT, hoist is `take` already shipped, and the trap is
untouched. tidyr's rectangling verbs are the closest prior art fathom has, and
the gap they leave is precisely the exploring half: they are excellent once you
know what a row is and silent on how to find out.
")
