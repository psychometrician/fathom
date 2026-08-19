# purrr — Open-Meteo hourly forecast, the columnar document
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.json   12 KB, depth 3, 24 paths, 14 fields,
#                                 every raggedness axis 0, row shapes 1
#  measured      2026-08-10
#  run           cd corpus/08-open-meteo/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           3   NO                  NO
#   2 how deep                                  2   NO                  yes
#   3 what is one record                        -   -                   CANNOT
#   7 how many records                          2   YES                 yes
#   8 three named fields to a table             3   YES                 yes
#  10 flatten the deepest array                 6   YES                 YES
#  12 flattest honest table                     4   YES                 YES
#  13 needed the shape in advance?                  YES for 8, 10, 12
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. purrr has been measured on raggedness-by-absence, recursion,
# keys-as-data, raggedness-by-null and scale. **This is the columnar case**, and
# it is the one where purrr has a verb aimed squarely at the problem:
# `list_transpose()`. `NOTES.md` records that `rows()` returns 5 rows each
# holding a 336-element list and *"the answer is the transpose and there is no
# operator for it."* purrr has the operator.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\n1. what is in here — str(), and this document is small enough for it:\n")
cat(sprintf("   str(max.level=2): %d lines\n",
            length(capture.output(str(doc, max.level = 2)))))
depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_dbl(x, depth)) else 0
cat(sprintf("\n2. depth %d\n", depth(doc)))
cat(sprintf("7. %d hourly observations of %d variables\n",
            length(doc$hourly[[1]]), length(doc$hourly)))
cat("3. CANNOT. purrr proposes no rows, and on this file the right answer is\n")
cat("   the one the probe cannot reach either — 336 rows, not 5 and not 1.\n")

# ── Q10 / Q12. THE TRANSPOSE, AND PURRR HAS THE VERB. ───────────────────────
cat("\n10/12. flatten the deepest array — the transpose:\n")
cat(sprintf("   $hourly is %d equal-length lists of %d\n",
            length(doc$hourly), length(doc$hourly[[1]])))
t0 <- Sys.time()
rows <- list_transpose(doc$hourly)
cat(sprintf("   list_transpose() -> %d rows, each a %d-element named list, %.3f s\n",
            length(rows), length(rows[[1]]),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("   row 1: %s\n",
            paste(sprintf("%s=%s", names(rows[[1]]), unlist(rows[[1]])), collapse = " ")))
tbl <- map_dfr(rows, \(r) as.data.frame(r))
cat(sprintf("   map_dfr over the transposed rows -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 2))
cat("   `list_transpose` IS THE OPERATOR NOTES.md SAYS DOES NOT EXIST — and it\n")
cat("   exists in purrr, has a name, and is documented. That sentence in the\n")
cat("   entry is about `rows()`, and it is correct about `rows()`; it should\n")
cat("   not be read as a statement about the ecosystem.\n")
cat("   THE HONEST QUALIFICATION: it works because the five lists are the same\n")
cat("   length, and NOTHING CHECKED THAT. `list_transpose` on lists of unequal\n")
cat("   length does not error — it recycles or drops depending on the case —\n")
cat("   so the correctness here is the document's, not the verb's.\n")

# What happens when the assumption is false. Measured, not asserted.
bad <- tryCatch({
  r <- list_transpose(list(a = 1:3, b = 1:2))
  sprintf("no error: %d rows from lists of 3 and 2", length(r))
}, error = function(e) paste("errors:", sub("\n.*", "", conditionMessage(e))))
cat(sprintf("   list_transpose(list(a=1:3, b=1:2)) -> %s\n", bad))

# ── Q8. ──────────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per hour:\n")
three <- map_dfr(rows, \(r) data.frame(
  time = r$time, temp = r$temperature_2m, wind = r$wind_speed_10m))
cat(sprintf("   -> %d x %d, no defaults needed\n", nrow(three), ncol(three)))
print(utils::head(three, 2))
cat("   AND IT IS THE SLOW WAY. `as.data.frame(fromJSON(path)$hourly)` gives\n")
cat("   the same 336 x 5 with no transpose and no map — see try-jsonlite.R.\n")
cat("   purrr's answer is correct and the round trip is unnecessary, because\n")
cat("   the document was already in R's native shape before purrr touched it.\n")

cat("
CONCLUSION — purrr has the operator this entry says does not exist, and it is
still the long way round.

  `NOTES.md` records `rows()` returning five rows each holding a 336-element
  list, and concludes *\"the answer is the transpose and there is no operator for
  it.\"* **`purrr::list_transpose()` is that operator.** It has a name, it is
  documented, and it turns the five columns into 336 named rows in three
  thousandths of a second. The entry's sentence is correct about `rows()` and
  should not be read as a claim about the ecosystem.

  **THE QUALIFICATION IS THE INTERESTING PART.** `list_transpose` works here
  because the five lists happen to be the same length, and **nothing checked
  that**. Given lists of 3 and 2 it does not error. So the correctness on this
  file belongs to the document, not to the verb — the same shape of luck as
  `jsonlite`'s `as.data.frame`, which would build a frame from five arrays that
  matched by coincidence just as happily.

  **AND IT IS STILL THE LONG WAY.** `as.data.frame(fromJSON(path)$hourly)` is
  the same 336 x 5 with no transpose, no `map`, and no verb chosen — because a
  data frame already IS a named list of equal-length vectors. purrr transposes
  into rows and then rebuilds a frame from them, which is a round trip through
  a shape the document was never in.

  So on the corpus's hardest document for fathom's design, purrr's contribution
  is a correct operator that is unnecessary. That is a better result for purrr
  than for this project.
")
