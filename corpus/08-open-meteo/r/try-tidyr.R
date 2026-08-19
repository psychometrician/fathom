# tidyr — an Open-Meteo hourly forecast
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   12,198 bytes, 5 columns of 336
#  measured      2026-08-09
#  run           cd corpus/08-open-meteo/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          4   no                  WRONG
#   7 how many records                            3   no                  WRONG
#   8 three named fields to a table               5   YES                 YES
#
# WHY THIS FILE. It is column-oriented: five parallel arrays of 336 under one
# parent, which is the shape that defeated design/probe.py outright. unnest_auto
# gets it WRONG, and it is the only file where tidyr's answer and the probe's
# failure have the same cause.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\n3/7. unnest_auto on `hourly`:\n")
t <- tibble(x = list(doc$hourly))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   WRONG. The answer is 336 rows x 5 columns and this is its transpose.\n")
cat("   The rule is 'do the elements share names', and five columns share none,\n")
cat("   so it widened a document that needed lengthening.\n")

cat("\n8. the right answer, once a person supplies question 3:\n")
tbl <- as_tibble(lapply(doc$hourly, unlist))
cat("   as_tibble(lapply(hourly, unlist)) ->", nrow(tbl), "rows x", ncol(tbl), "cols\n")
cat("   columns:", paste(names(tbl), collapse = ", "), "\n")
cat("   one line, and it is the cleanest answer anything has given on this file.\n")
cat("
CONCLUSION, AND IT CUTS BOTH WAYS.

  tidyr gets question 3 wrong here for the same reason design/probe.py gets the
  whole file wrong: both look for records among SIBLINGS, and a column-oriented
  document has no sibling records at all. unnest_auto widened; the probe folded
  nothing and offered `the whole document, 1 row x 9 cols`.

  But tidyr recovers in one line once told, because `as_tibble` over parallel
  vectors IS the transpose. design/rows.py has no operator for it: rows('hourly.*')
  returns 5 rows, one per variable, each holding a 336-element list.

  So on the file that defeated the probe, the competing tool is wrong in the same
  way and one line from right, and the probe is wrong in the same way and has no
  line to write.
")
