# tidyr — Chicago city employee salaries, 5,000 flat records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   924 KB, 5,000 records, 8 fields
#  measured      2026-08-11
#  run           cd corpus/19-chicago-salaries/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  YES — 8 columns
#   2 how deep                                    2   NO                  yes — 2, at once
#   3 what is one record                         18   NO                  YES, AND PRICES
#                                                                         NOTHING — see below
#   4 always present vs sometimes                 5   NO                  YES — the split
#   5 does any field change type                  3   NO                  NO — all text
#   6 are any object keys data                    1   -                   NO, correctly
#   7 how many records                            2   NO                  yes — 5,000
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              4  YES                  yes
#  10 flatten the deepest array                   2  -                    NOTHING NESTED
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       3  YES                  5,000 x 8, 0 lists
#  13 needed the shape in advance?                    NO for 1, 3, 4, 5, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~85
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS DOCUMENT GIVES VERDICT.md's SHARPEST ARITHMETIC ITS SECOND WITNESS, AND
# THE FIRST ONE WAS THE ONLY ONE. Entry 21 found that pandas and polars price a
# split at exactly the unsplit emptiness — 44.3% against 44.3% — and that this
# is NECESSARY rather than coincidental: a frame has committed to all its
# columns, so grouping moves no holes and the size-weighted mean of the group
# emptinesses IS the global emptiness for EVERY possible split.
#
# Measured here on a second document and a different tool, and it holds exactly:
#
#   unsplit 0.2235      weighted over the split on `salary_or_hourly` 0.2235
#
# AND THIS DOCUMENT SHOWS WHAT THE SPLIT IS ACTUALLY WORTH, because it is small
# enough to compute both ways. Recompute each group's column set the way jq and
# DuckDB do — drop the columns that are empty throughout a group — and the same
# split scores 0.0000. THE SPLIT IS PERFECT AND THE FRAME SCORES IT AT ZERO
# BENEFIT. Salaried employees have no hourly rate and hourly employees have no
# annual salary, so `salary_or_hourly` partitions the holes completely.
#
# 0.2235 -> 0.0000 recomputed, 0.2235 -> 0.2235 as a frame. That is not a tool
# missing a verb; the rectangle cannot represent the quantity the search is for.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

recs <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7 / Q12. ─────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = recs), x)),
                    type = "message")
w <- tibble(x = recs) |> unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d, right, and there was never another candidate.\n",
            nrow(a), ncol(a)))
cat(sprintf("Q1  %d columns: %s\n", ncol(w), paste(names(w), collapse = ", ")))
cat(sprintf("Q7  %d records. Q10  nothing is nested — %d list-columns.\n",
            nrow(w), sum(map_lgl(w, is.list))))

# ── Q4. the discriminator. ─────────────────────────────────────────────────
cat("\nQ4  columns and how full they are:\n")
for (cn in names(w))
  cat(sprintf("    %-20s %5.1f%%\n", cn, 100 * mean(!is.na(w[[cn]]))))
cat(sprintf("    `salary_or_hourly` takes %d values and every hole in the table\n",
            n_distinct(w$salary_or_hourly)))
cat("    is on one side of it. That is the discriminator this project's\n")
cat("    partition looks for, sitting in plain sight as a column.\n")

# ── Q3 continued. THE CENTREPIECE: pricing the split. ──────────────────────
emptiness <- function(t) mean(is.na(as.matrix(t)))
glob  <- emptiness(w)
grp   <- w |> group_by(salary_or_hourly) |> group_split()
wt    <- sum(map_dbl(grp, \(t) nrow(t) * emptiness(t))) / nrow(w)
worst <- max(map_dbl(grp, emptiness))
cat(sprintf("\nQ3  PRICING THE SPLIT, as a frame:\n"))
cat(sprintf("      unsplit emptiness                    %.4f\n", glob))
for (t in grp)
  cat(sprintf("      %-8s n = %4d   emptiness       %.4f\n",
              t$salary_or_hourly[1], nrow(t), emptiness(t)))
cat(sprintf("      size-weighted mean of the groups     %.4f   EQUAL: %s\n",
            wt, isTRUE(all.equal(glob, wt))))
cat(sprintf("      worst group                          %.4f\n", worst))
recomp <- map_dbl(grp, \(t) {
  keep <- names(t)[map_lgl(t, \(c) any(!is.na(c)))]
  mean(is.na(as.matrix(t[keep])))
})
cat(sprintf("\n    NOW RECOMPUTE EACH GROUP'S COLUMN SET, as jq and DuckDB do:\n"))
for (i in seq_along(grp))
  cat(sprintf("      %-8s keeps %d columns   emptiness       %.4f\n",
              grp[[i]]$salary_or_hourly[1],
              sum(map_lgl(grp[[i]], \(c) any(!is.na(c)))), recomp[i]))
cat(sprintf("      weighted %.4f, worst %.4f\n",
            sum(map_dbl(seq_along(grp), \(i) nrow(grp[[i]]) * recomp[i])) / nrow(w),
            max(recomp)))
cat("    ══ 0.2235 -> 0.0000 RECOMPUTED, 0.2235 -> 0.2235 AS A FRAME. ══\n")
cat("    The split is PERFECT — each group needs only its own columns and has\n")
cat("    no holes at all — and the frame scores it at zero benefit, because a\n")
cat("    frame committed to all eight columns before the grouping happened.\n")
cat("    Entry 21 measured this on pandas and polars and called it necessary\n")
cat("    rather than coincidental. THIS IS THE SECOND DOCUMENT AND THE THIRD\n")
cat("    TOOL, and it is the one where the loss is total rather than partial.\n")

# ── Q5 / Q8 / Q9 / Q11. ────────────────────────────────────────────────────
cls <- table(map_chr(w, \(c) class(c)[1]))
cat(sprintf("\nQ5  column classes: %s\n",
            paste(sprintf("%s x%d", names(cls), as.integer(cls)), collapse = ", ")))
cat("    NO variation, and again because nothing has a type: `annual_salary`\n")
cat("    is the string \"$100,000.00\" and stays one. A tool cannot find type\n")
cat("    variation in a document whose types were text to begin with.\n")
three <- w |> select(name, department, annual_salary)
cat(sprintf("\nQ8  three named fields -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat(sprintf("\nQ9  `annual_salary` is absent on %d rows and every one is kept,\n",
            sum(is.na(w$annual_salary))))
cat("    because unnest_wider keeps rows by construction. The rows it is\n")
cat("    absent on are exactly the hourly employees.\n")
cat("\nQ11 CANNOT. No predicate over values.\n")
cat(sprintf("Q12 %d x %d, no list-columns, nothing lost. The one document in the\n",
            nrow(w), ncol(w)))
cat("    fourteen where the flattest honest table is the document itself.\n")

cat("
13. NO for 1, 3, 4, 5 and 7 — but question 3 is answered only in the sense of
    naming the row. The COST half of question 3, which is the half this
    project added, is the thing the frame cannot express.

14. YES.

16. ~85 lines, of which the rectangling is one call and the pricing is thirty.
")
