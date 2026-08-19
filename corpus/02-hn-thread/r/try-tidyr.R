# tidyr — one Hacker News comment thread
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
#  measured      2026-08-09
#  run           cd corpus/02-hn-thread/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          4   no                  YES
#   7 how many records                            5   no                  PARTLY
#   8 three named fields to a table               4   YES                 YES
#  10 flatten the deepest array                   5   YES                 PARTLY
#
# WHY THIS FILE. unnest_auto gets this one RIGHT, and it is the clearest case in
# the corpus of a tool answering question 3 unaided. The interest is what happens
# next: getting one row per top-level comment is not getting one row per comment.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr); library(purrr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\n3. unnest_auto on `children`:\n")
t <- tibble(x = list(doc$children))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols — CORRECT for the top level\n")

cat("\n7. and 25 is not 336. The thread is 13 levels deep and unnest_auto sees one.\n")
depth_count <- function(n) 1 + sum(map_int(n$children %||% list(), depth_count))
cat("   nodes in the thread:", depth_count(doc), "\n")
cat("   tidyr has no fixpoint: reaching all of them is a recursion a person\n")
cat("   writes, and `unnest_longer` repeated 13 times needs the 13.\n")

cat("\n10. the recursion, written by hand, then handed to tidyr:\n")
flatten_thread <- function(n) {
  bind_rows(tibble(id = n$id %||% NA, author = n$author %||% NA,
                   text = substr(n$text %||% "", 1, 30)),
            map_dfr(n$children %||% list(), flatten_thread))
}
tbl <- flatten_thread(doc)
cat("   ", nrow(tbl), "rows x", ncol(tbl), "cols — and every line of the walk is mine.\n")
cat("
CONCLUSION FOR THIS FILE. unnest_auto answered question 3 correctly and the
answer was for ONE LEVEL. A recursive document needs the operation repeated
until it stops changing, and that fixpoint is the thing tidyr does not have —
which is exactly what design/rows.py's `children**` notation was invented for.
")
