# tidyr — Wikidata entity Q30
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   1.4 MB, 469 claim properties, 7 keyed sites
#  measured      2026-08-09
#  run           cd corpus/10-wikidata/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          5   no                  WRONG
#   5 does any field change type                  6   no                  NO
#   7 how many records                            2   no                  WRONG
#   8 three named fields to a table               5   YES                 YES
#
# WHY THIS FILE. Keys-as-data at FOUR levels — entity id, property id, language
# code, wiki name — and the corpus's genuine polymorphism at datavalue.value.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)
claims <- doc$entities$Q30$claims

cat("\n3/7. unnest_auto on `entities.Q30.claims`:\n")
t <- tibble(x = list(claims))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   WRONG. NOTES.md records 469 rows, one per claim property.\n")
cat("   Third instance of the same failure, after npm and Stripe.\n")

cat("\n   and one level up, unnest_auto on `entities` itself:\n")
t2 <- tibble(x = list(doc$entities))
msg2 <- capture.output(o2 <- suppressWarnings(unnest_auto(t2, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg2, collapse = " ")), "\n")
cat("   `Q30` becomes a column name. The entity ID is the most obviously\n")
cat("   data-like key in the corpus and it is still read as a field.\n")

cat("\n8. the right answer, once a person supplies question 3:\n")
tbl <- tibble(property = names(claims), x = unname(claims)) |>
  mutate(n = vapply(x, length, 0L),
         datatype = vapply(x, function(s) s[[1]]$mainsnak$datatype %||% NA_character_, "")) |>
  select(property, n, datatype)
cat("   enframe-then-mutate ->", nrow(tbl), "rows x", ncol(tbl), "cols\n")
print(head(tbl, 3))

# 5. The corpus's genuine polymorphism, and the boundary of what rectangling
#    can see.
cat("\n5. datavalue.value across every mainsnak:\n")
vals <- unlist(lapply(claims, function(cl) lapply(cl, function(s) s$mainsnak$datavalue$value)),
               recursive = FALSE)
kinds <- table(vapply(vals, function(v) if (is.list(v)) "object" else class(v)[1], ""))
print(kinds)
cat("   character on 512 and a list on 1,210. tidyr has no verb that reports\n")
cat("   this; it would arrive as a list-column and the disagreement would be\n")
cat("   inside it, invisible, exactly as with 03-natural-earth's coordinates.\n")

cat("
CONCLUSION. Third consecutive keyed-object failure for unnest_auto, and the
cleanest one: `Q30` is an entity identifier and it still becomes a column name.

The scoreboard is now unambiguous. unnest_auto is RIGHT on every array of
records this corpus holds and WRONG on every keyed object, because its one rule
— do the elements share names — is a perfect detector of the structure it
mishandles. That is not a heuristic that needs tuning. It is the wrong question,
and question 6 is the right one.
")
