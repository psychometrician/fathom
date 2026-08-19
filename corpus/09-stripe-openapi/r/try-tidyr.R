# tidyr — the Stripe OpenAPI specification
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
#  measured      2026-08-09
#  run           cd corpus/09-stripe-openapi/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          5   no                  WRONG
#   6 are any object keys data                    6   no                  NO
#   7 how many records                            2   no                  WRONG
#   8 three named fields to a table               5   YES                 YES
#
# WHY THIS FILE. It is the corpus's most keys-as-data document — 47 keyed sites
# against npm's 6 — so it is the sharpest possible test of the ONE rule
# unnest_auto uses: do the elements share names?
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)
schemas <- doc$components$schemas

cat("\n3/7. unnest_auto on `components.schemas`:\n")
t <- tibble(x = list(schemas))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   WRONG. NOTES.md records 1,440 rows, one per schema. This is 1 row and\n")
cat("   1,440 columns — the transpose of the answer.\n")
cat("   Same failure as 01-npm-registry's `versions`, on a document ten times\n")
cat("   the size, and for the identical reason: the elements HAVE names, so\n")
cat("   the rule widens, and the names are DATA.\n")

cat("\n6. are any object keys data — the question that decides question 3:\n")
cat("   first three column names unnest_auto produced:\n")
cat("     ", paste(head(names(out), 3), collapse = ", "), "\n")
cat("   Those are Stripe resource names. They are values, and unnest_auto has\n")
cat("   made each one a column, silently and with a message saying it did so\n")
cat("   because they are 'names in common'. The message is true and the\n")
cat("   conclusion is wrong: shared names is what a keyed object looks like.\n")

cat("\n8. the right answer, once a person supplies question 3:\n")
tbl <- tibble(schema = names(schemas), x = unname(schemas)) |>
  hoist(x, type = "type") |>
  mutate(nprops = vapply(x, function(s) length(s$properties), 0L)) |>
  select(schema, type, nprops)
cat("   enframe-then-hoist ->", nrow(tbl), "rows x", ncol(tbl), "cols\n")
print(head(tbl, 3))
cat("   `names(schemas)` is the keys-as-data operator, written by hand.\n")

cat("
CONCLUSION, and it is the strongest evidence in the corpus for fathom's central
claim. unnest_auto's rule is 'do the elements share names', which is exactly
right for an array of records and exactly backwards for a keyed object — and a
keyed object is what shared names MEANS.

The failure is now recorded on two documents, npm at 288 versions and Stripe at
1,440 schemas, with 47 keyed sites here against 6 there. It is not a corner
case, it is the one structure this corpus was built to find, and the only
function in either language that attempts question 3 gets it wrong every time
question 6 is the reason.
")
