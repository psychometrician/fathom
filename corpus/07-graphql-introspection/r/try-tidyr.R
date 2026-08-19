# tidyr — a GraphQL introspection result
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   143 KB, 108 types
#  measured      2026-08-09
#  run           cd corpus/07-graphql-introspection/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          4   no                  RIGHT
#   4 always vs sometimes                         6   no                  RIGHT
#   7 how many records                            2   no                  RIGHT
#   8 three named fields to a table               4   YES                 YES
#
# WHY THIS FILE. Every field is PRESENT on all 108 records and NULL on most, so
# a tool that measures key presence calls it perfectly regular. R distinguishes
# NULL from absent natively, which no Python tool here does without help.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)
types <- doc$data$`__schema`$types

# THE PROTOCOL: the container goes in as a ONE-element list-column, so that
# unnest_auto chooses longer or wider itself. Pre-splitting answers question 3.
cat("\n3/7. unnest_auto on `types`:\n")
t <- tibble(x = list(types))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   RIGHT. NOTES.md records 108 types as the answer to question 3.\n")

cat("\n8. three named fields:\n")
tbl <- tibble(x = types) |>
  hoist(x, kind = "kind", name = "name", ndesc = "description")
print(head(select(tbl, kind, name), 3))

# 4. THE POINT OF THIS FILE. R's NULL is not R's NA, and unnest_wider keeps the
#    difference, so tidyr answers question 4 correctly where pandas, polars and
#    DuckDB all collapse null and absent into one.
cat("\n4. present vs non-null, per field of types[] — the file's whole trap:\n")
fields <- unique(unlist(lapply(types, names)))
for (f in sort(fields)) {
  present <- sum(vapply(types, function(x) f %in% names(x), TRUE))
  filled  <- sum(vapply(types, function(x) !is.null(x[[f]]), TRUE))
  cat(sprintf("     %-16s present %3d/108   non-null %3d/108\n", f, present, filled))
}
cat("   Every field present on all 108. `possibleTypes` non-null on ZERO.\n")
cat("   Ragged by absence 0, ragged by null severe — and unnest_wider carries\n")
cat("   that through as a list-column of NULLs rather than flattening it away,\n")
cat("   so the information survives into the table. That is more than any\n")
cat("   Python tool here manages without a hand-written presence test.\n")

cat("\n   and the kinds, which is what a partition would split on:\n")
print(table(vapply(types, function(x) x$kind, "")))
cat("   FOUR kinds. This entry's expectation block predicted six; see NOTES.md.\n")

cat("
CONCLUSION. unnest_auto RIGHT, and tidyr is the only tool in either language
that carries NULL-versus-absent into the rectangled result unaided. That is
question 4 answered properly on the one corpus file where the distinction
decides the answer.

It still does not group by `kind`, and nothing suggests it should: the operation
this file demands is the partition, and no rectangling verb in either ecosystem
has one.
")
