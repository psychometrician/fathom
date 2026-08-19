# tidyjson — Chicago employee salaries
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson 0.3.3.1
#  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
#  measured      2026-08-10
#  run           cd corpus/19-chicago-salaries/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                            14   NO                  WRONG
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          5   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  YES
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   2   -                   n/a
#  11 find every path matching something          -   -                   CANNOT
#  12 flattest honest table                       4   NO                  yes
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7
#  14 survives the next file unchanged?               json_schema does
#  15 readable a week later?                          yes, it is a pipeline
#  16 lines, and how much is ceremony?                ~35, the pipeline is intent
#
# THE CASE WHERE json_schema SHOULD HAVE BEEN RIGHT, AND WAS NOT. It has
# discarded silently on 03, 05, 07, 10 and 11 — five documents, always by picking
# one shape out of several. This document's two shapes are both FLAT, so nothing
# forces a choice. **It dropped `annual_salary`, the field held by 3,938 of the
# 5,000 records, and kept the 1,062-record hourly fields.** Sixth document, sixth
# discard, and the second running where the MAJORITY is what goes. See Q1.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("R %s, tidyjson %s\n", getRversion(), packageVersion("tidyjson")))

j <- readLines("../source.json", warn = FALSE) |> paste(collapse = "")

t0 <- Sys.time()
sch <- j |> as.tbl_json() |> json_schema()
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\n1. json_schema: %d chars in %.1f s (%.3f%% of the file)\n",
            nchar(sch), el, 100 * nchar(sch) / 944651))
cat(sprintf("   %s\n", sch))
cat("   SEVEN FIELDS OF EIGHT, and the missing one is `annual_salary`.\n")
cat("   This file was written predicting json_schema would finally report a\n")
cat("   UNION — the document has two flat key-sets and nothing forces a choice\n")
cat("   between nesting levels. **It discarded anyway.** Measured:\n")
cat("     the two key-sets   SALARY 3,938 rows: annual_salary\n")
cat("                        HOURLY 1,062 rows: hourly_rate, typical_hours\n")
cat("     json_schema keeps  hourly_rate, typical_hours  — the 1,062\n")
cat("     json_schema drops  annual_salary               — the 3,938\n")
cat("   **It kept the MINORITY shape and dropped the majority field**, exactly\n")
cat("   as it did on 11-jupyter-notebook, where it kept the 27-output `stream`\n")
cat("   shape and dropped the 80. Sixth document, sixth silent discard — and\n")
cat("   the second running where the majority is what goes.\n")
cat("   The prediction is left here, wrong, because the miss is the finding.\n")

recs <- j |> as.tbl_json() |> gather_array("i")
cat(sprintf("\n7. %d records.\n", nrow(recs)))
cat("\n2. depth 2 — `gather_array` then `gather_object` exhausts the document.\n")

keys <- recs |> gather_object("key") |> count(key, name = "n")
cat("\n4. key presence, from gather_object, nothing named:\n")
for (i in order(-keys$n))
  cat(sprintf("     %-22s %5d of 5000\n", keys$key[i], keys$n[i]))
cat("   3,938 + 1,062 = 5,000. Mutually exclusive and unremarked.\n")

types <- recs |> gather_object("key") |> json_types("t") |> count(key, t)
cat("\n5. types per key:\n")
for (i in seq_len(nrow(types)))
  cat(sprintf("     %-22s %-8s %5d\n", types$key[i], as.character(types$t[i]),
              types$n[i]))
cat("   Every key is `string`, `annual_salary` included. tidyjson reports it\n")
cat("   correctly and correctly is the problem — a document uniformly wrong\n")
cat("   about its own types is invisible to a type report.\n")

tbl <- recs |> spread_all() |> as_tibble()
cat(sprintf("\n8/12. spread_all: %d x %d\n", nrow(tbl), ncol(tbl)))
print(head(as.data.frame(tbl[, c("name", "department", "annual_salary")]), 3))
cat(sprintf("\n9. annual_salary NA on %d of %d rows, all kept — spread_all\n",
            sum(is.na(tbl$annual_salary)), nrow(tbl)))
cat("   fills absent keys with NA and drops no row.\n")

cat("\n3. one employee per row, and TWO defensible tables:\n")
for (k in names(sort(table(tbl$salary_or_hourly), decreasing = TRUE))) {
  s <- tbl[tbl$salary_or_hourly == k, ]
  cat(sprintf("     %-18s %5d rows x %d cols, no holes\n", k, nrow(s),
              sum(colSums(!is.na(s)) > 0)))
}
cat("   22% empty folded, 0% split. One `group_by` and tidyjson is silent.\n")

cat("\n10, 6. n/a. No nested array, no keys that are data.\n")
cat("\n11. CANNOT. Every tidyjson verb descends a NAMED path; there is no\n")
cat("   recursive search. `json_schema` knows every path and cannot filter by\n")
cat("   value.\n")
cat("   WHAT IS LOST: `annual_salary` from the schema — 3,938 records' worth of\n")
cat("   the document's most important column, absent from the description with\n")
cat("   no warning. `spread_all` above recovers it; `json_schema` never says it\n")
cat("   was there.\n")
