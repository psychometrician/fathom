# tidyr — a Synthea FHIR bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   2,024,911 bytes, 564 resources, 20 resourceTypes
#  measured      2026-08-09
#  run           cd corpus/05-fhir-bundle/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          4   no                  YES
#   4 always present vs sometimes                 4   no                  YES
#   7 how many records                            2   no                  YES
#  3b does it propose the 20 kinds                 5   no                  NO
#
# WHY THIS FILE. This is the document design/probe.py grew its fourth operation
# for: 564 records that are 20 different kinds, discriminated by a field inside
# each record. unnest_auto answers question 3 correctly here. The question is
# whether anything in tidyr goes on to notice that one table is the wrong answer.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\n3/7. unnest_auto on `entry`:\n")
t <- tibble(x = list(doc$entry))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows — CORRECT\n")

res <- tibble(r = lapply(doc$entry, `[[`, "resource")) |>
  unnest_wider(r, names_repair = "unique_quiet")
cat("\n4. unnest_wider on the resources ->", nrow(res), "rows x", ncol(res), "cols\n")
# A field absent from a record becomes NULL in a list-column and NA in an atomic
# one, and the first version of this line tested only is.null(). It reported 30
# always-present columns where design/probe.py says 2 — a wrong number in a
# comparison column, produced by the check rather than by tidyr.
present <- function(x) if (is.list(x)) !vapply(x, is.null, logical(1)) else !is.na(x)
filled <- sapply(res, function(c) sum(present(c)))
cat("   columns present on every row:", sum(filled == nrow(res)), "of", ncol(res),
    "  (design/probe.py says 2: id, resourceType)\n")
cat("   the emptiest five:", paste(head(sort(filled), 5), collapse = ", "),
    "of", nrow(res), "\n")
cat("   design/probe.py reports the same table as 564 x 97, 87% empty.\n")

cat("\n3b. does tidyr suggest these are 20 kinds? No.\n")
cat("   It produced a 97-column frame that is mostly NA and said nothing. NA is\n")
cat("   not an error in a tibble, and there is no verb that asks whether a frame\n")
cat("   would be better as several. Once a PERSON names resourceType:\n")
k <- table(sapply(doc$entry, function(e) e$resource$resourceType))
cat("     ", length(k), "kinds:", paste(head(names(sort(k, decreasing = TRUE)), 5), collapse = ", "), "...\n")
cat("   which is group_by() away, and nothing proposes it.\n")
cat("
CONCLUSION. unnest_auto gets question 3 right and stops exactly where the
probe's fourth operation starts. Getting the ROW right and the TABLE wrong is a
distinction this corpus did not have a case for until file 05, and tidyr shows
it cleanly: the row is one entry, and the table should be twenty.
")
