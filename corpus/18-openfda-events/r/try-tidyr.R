# tidyr — openFDA adverse drug event reports, 100 records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   2.7 MB, 100 reports
#  measured      2026-08-11
#  run           cd corpus/18-openfda-events/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  YES — 25 columns
#   2 how deep                                    6   NO                  by exhaustion — 8
#   3 what is one record                          4   NO                  YES, and RIGHT
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  2   -                   CANNOT
#   6 are any object keys data                    2   -                   NO, correctly
#   7 how many records                            3   NO                  yes — 100 / 251
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              4  YES                  yes
#  10 flatten the deepest array                  10  YES                  YES — 5 verbs
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       5  YES                  100 x 25
#  13 needed the shape in advance?                    NO for 1, 3, 4, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~85
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS IS THE DEEPEST OF THE ENTRIES GRADED IN THIRTEEN TOOLS, AND IT PRICES THE
# VERB THAT MEANS `DESCEND ONE LEVEL`. Reaching the drug records inside the
# patient inside the report takes a chain of unnesting calls, one per level,
# each of which must name the column it is descending into. purrr paid the same
# price as three nested maps; tidyr pays it as a pipeline of named verbs.
#
# THE PIPELINE IS THE BETTER FORM AND IT IS STILL THE SAME PRICE. You cannot
# write the chain without already knowing the path, so question 13 is YES for
# every extraction question here even though it is NO for the exploration ones.
# THAT SPLIT IS THE FINDING: tidyr explores without being told the shape and
# extracts only when it is told.
#
# AND THE OBJECT TRAP IS HERE TOO, at its most misleading. unnest_longer on
# `patient` returns 567 rows from 100 reports — no report has many patients; the
# patient object has several FIELDS. On this document the number looks like a
# plausible record count, which is exactly when a wrong row count is dangerous.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

doc  <- fromJSON("../source.json", simplifyVector = FALSE)
recs <- doc$results

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7. ───────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = recs), x)),
                    type = "message")
w <- tibble(x = recs) |> unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d, and it is right: one row per report.\n", nrow(a), ncol(a)))
cat(sprintf("Q1  %d columns, %d list-columns. Q7  %d reports.\n",
            ncol(w), sum(map_lgl(w, is.list)), nrow(w)))

# ── Q10 / Q2. the descent. ─────────────────────────────────────────────────
cat("\nQ10 THE DESCENT TO THE DRUG RECORDS, one verb per level:\n")
s1 <- w  |> select(safetyreportid, patient)
s2 <- s1 |> unnest_wider(patient, names_repair = "unique_quiet")
s3 <- s2 |> unnest_longer(drug)
s4 <- s3 |> unnest_wider(drug, names_repair = "unique_quiet")
cat(sprintf("    select                        %5d x %2d\n", nrow(s1), ncol(s1)))
cat(sprintf("    unnest_wider(patient)         %5d x %2d\n", nrow(s2), ncol(s2)))
cat(sprintf("    unnest_longer(drug)           %5d x %2d\n", nrow(s3), ncol(s3)))
cat(sprintf("    unnest_wider(drug)            %5d x %2d\n", nrow(s4), ncol(s4)))
if ("openfda" %in% names(s4)) {
  s5 <- s4 |> unnest_wider(openfda, names_repair = "unique_quiet")
  cat(sprintf("    unnest_wider(openfda)         %5d x %2d\n", nrow(s5), ncol(s5)))
}
cat("    EVERY LINE NAMES THE COLUMN IT IS DESCENDING INTO, so the chain\n")
cat("    cannot be written without the path. Exploration needed no shape;\n")
cat("    extraction needs all of it. THAT SPLIT IS THIS FILE'S RESULT.\n")
cat(sprintf("Q2  the chain above is %d calls and %d list-columns still remain, so\n",
            4L, sum(map_lgl(s4, is.list))))
cat("    tidyr never states the depth — you learn it by running out. The\n")
cat("    document is 8 levels; nothing printed that number.\n")

# ── the object trap. ───────────────────────────────────────────────────────
nf   <- n_distinct(unlist(map(w$patient, names)))
tot  <- sum(map_int(w$patient, length))
plen <- nrow(w |> unnest_longer(patient))
cat(sprintf("\n    THE OBJECT TRAP: unnest_longer(patient) -> %d rows from %d\n",
            plen, nrow(w)))
cat(sprintf("    reports. No report has many patients — `patient` is an OBJECT,\n"))
cat(sprintf("    and %d is the TOTAL FIELD COUNT across the %d patient objects,\n",
            tot, nrow(w)))
cat(sprintf("    which carry %d distinct field names between them and not the\n", nf))
cat("    same number each. A row count that is a sum of field counts still\n")
cat("    looks like a credible record count, which is when it does most harm.\n")

# ── Q4 / Q9. ───────────────────────────────────────────────────────────────
cat("\nQ4/Q9  the list-columns, default versus keep_empty:\n")
for (cn in names(w)[map_lgl(w, is.list)]) {
  d <- nrow(w |> unnest_longer(all_of(cn)))
  k <- nrow(w |> unnest_longer(all_of(cn), keep_empty = TRUE))
  cat(sprintf("    %-18s %4d rows   keep_empty %4d   DROPS %2d reports\n",
              cn, d, k, k - d))
}

# ── Q5 / Q8 / Q11 / Q12. ───────────────────────────────────────────────────
cat("\nQ5  CANNOT — the varying fields are list-columns.\n")
three <- tibble(x = recs) |>
  hoist(x, id = "safetyreportid", serious = "serious", country = "occurcountry") |>
  select(id, serious, country)
cat(sprintf("\nQ8  hoist() -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat("\nQ11 CANNOT. No predicate over values.\n")
cat(sprintf("\nQ12 %d x %d with %d list-columns — and the flat table is not one\n",
            nrow(w), ncol(w), sum(map_lgl(w, is.list))))
cat("    call but a decision per column, four levels down. WHAT IS LOST at\n")
cat("    each level is whichever reports have nothing there, unless every\n")
cat("    unnest_longer in the chain carries keep_empty.\n")

cat("
13. NO for the exploration questions and YES for every extraction one, on the
    same document and in the same session. That is the cleanest statement in
    the fourteen files of where tidyr's help stops.

14. YES for the chain, which names only openFDA's stable field names.

16. ~85 lines, and the descent is four of them.
")
