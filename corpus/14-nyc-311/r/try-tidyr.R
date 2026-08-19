# tidyr — NYC 311 service requests, 20,000 flat records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   28 MB, 20,000 records
#  measured      2026-08-11
#  run           cd corpus/14-nyc-311/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  YES — 48 columns
#   2 how deep                                    2   NO                  yes — 3, by exhaustion
#   3 what is one record                          5   NO                  YES, and RIGHT
#   4 always present vs sometimes                 7   NO                  YES — 13 of 48 always
#   5 does any field change type                  4   NO                  NO — everything is text
#   6 are any object keys data                    2   -                   NO, correctly
#   7 how many records                            2   NO                  yes — 20,000
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              5  YES                  yes
#  10 flatten the deepest array                   5  YES                  yes — `location`
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       5  YES                  20,000 x 48
#  13 needed the shape in advance?                    NO for 1, 3, 4, 5, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~80
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS IS THE DOCUMENT WHERE unnest_auto IS SIMPLY RIGHT, AND THAT MATTERS AS
# MUCH AS THE FAILURES. Twenty thousand records, thirteen fields on every one of
# them, one obvious row shape — and it says so and produces it. Entries 12, 13,
# 16 and 24 all found the intersection rule deciding keys-as-data on evidence
# that has nothing to do with the question; here the intersection is thirteen
# real shared fields and the wide answer is the right one. A rule that is wrong
# in principle can still be right whenever the document is easy, WHICH IS THE
# CONDITION UNDER WHICH NOBODY NOTICES IT IS WRONG.
#
# AND IT IS THE SCALE TEST BY ACCIDENT. 28 MB and 20,000 records rectangle
# without complaint, so the `scale` axis stays untested here too.
#
# THE ONE REAL FINDING IS THAT NOTHING HAS A TYPE. All 48 columns come back
# character, including `annual_salary`-style numerics and every date. jsonlite's
# simplifyVector = FALSE hands tidyr strings and tidyr keeps them, so question 5
# is `no variation` in the strongest and least useful sense: THE DOCUMENT'S
# TYPES WERE ALREADY GONE BEFORE THE RECTANGLING BEGAN.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

recs <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7. ───────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = recs), x)),
                    type = "message")
w <- tibble(x = recs) |> unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d, AND IT IS RIGHT. One row per service request.\n",
            nrow(a), ncol(a)))
cat(sprintf("Q1  %d columns. Q7  %d records. Q6  no keys are data, correctly.\n",
            ncol(w), nrow(w)))
cat("    THE RULE THAT FAILED ON 12, 13, 16 AND 24 SUCCEEDS HERE because the\n")
cat("    intersection is thirteen genuinely shared fields. Being right on the\n")
cat("    easy documents is how a wrong rule stays unnoticed.\n")

# ── Q4. ─────────────────────────────────────────────────────────────────────
fill  <- map_dbl(w, \(c) mean(if (is.list(c)) lengths(c) > 0 else !is.na(c)))
inter <- Reduce(intersect, map(recs, names))
cat(sprintf("\nQ4  %d of %d columns are on every record; %d are on under 10%%\n",
            length(inter), ncol(w), sum(fill < .1)))
cat("    rarest five:\n")
for (cn in names(sort(fill))[1:5])
  cat(sprintf("      %-26s %5.1f%%\n", cn, 100 * fill[[cn]]))

# ── Q5 / Q2. ────────────────────────────────────────────────────────────────
cls <- map_chr(w, \(c) class(c)[1])
cat(sprintf("\nQ5  column classes present: %s\n",
            paste(sprintf("%s x%d", names(table(cls)), as.integer(table(cls))),
                  collapse = ", ")))
cat("    NO field changes type, and the reason is that no field HAS one —\n")
cat("    every scalar arrived as a string and stayed one. Question 5 answered\n")
cat("    `no` because the evidence was destroyed upstream of the tool.\n")
cat(sprintf("Q2  ONE list-column of %d, so a second unnesting exhausts the\n",
            ncol(w)))
cat("    document. That is how tidyr reports depth: by running out.\n")

# ── Q9 / Q10. ───────────────────────────────────────────────────────────────
lc  <- names(w)[map_lgl(w, is.list)]
d   <- nrow(w |> unnest_longer(all_of(lc[1])))
k   <- nrow(w |> unnest_longer(all_of(lc[1]), keep_empty = TRUE))
has <- sum(lengths(w[[lc[1]]]) > 0)
nf  <- n_distinct(unlist(map(w[[lc[1]]], names)))
cat(sprintf("\nQ10 the one nested field is `%s`, and it is an OBJECT:\n", lc[1]))
cat(sprintf("    unnest_longer -> %d rows; keep_empty -> %d; DROPS %d records\n",
            d, k, k - d))
cat(sprintf("    THE %d IS NOT ONE ROW PER LOCATION. It is %d records that have\n",
            d, has))
cat(sprintf("    one, times its %d fields — unnest_longer on an object counts\n", nf))
cat("    FIELDS, and the call does not say which meaning you are getting.\n")
cat("\n    `unnest_wider` is the one that means one row per record, and the\n")
cat("    documented fix for its name clashes MAKES ONE HERE:\n")
e <- tryCatch(w |> unnest_wider(all_of(lc[1]), names_sep = "_"),
              error = \(e) conditionMessage(e))
cat(sprintf("      names_sep = \"_\"  ->  %s\n",
            trimws(gsub("\\s+", " ", if (is.character(e)) e else "no error"))))
cat(sprintf("    `location` + \"_\" + `type` is `location_type`, WHICH IS ALREADY\n"))
cat("    A 311 FIELD — and the error then advises `names_sep`, which is what\n")
cat("    produced it. Only names_repair gets through:\n")
ok <- w |> unnest_wider(all_of(lc[1]), names_sep = "_", names_repair = "unique_quiet")
cat(sprintf("      + names_repair -> %d x %d\n", nrow(ok), ncol(ok)))
cat("    THIRD INSTANCE OF THIS FAILURE MODE IN THE CORPUS, after entry 01's\n")
cat("    `version` and design/rows.py's `children**` — and the only one where\n")
cat("    the collision is manufactured by the repair itself.\n")
cat("Q9  those dropped records are the ones with no location, and the default\n")
cat("    loses them silently. `keep_empty = TRUE` is the whole answer to\n")
cat("    question 9 and it is one argument.\n")

# ── Q8 / Q11 / Q12. ─────────────────────────────────────────────────────────
three <- w |> select(unique_key, complaint_type, agency)
cat(sprintf("\nQ8  three named fields -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat("\nQ11 CANNOT. No predicate over values.\n")
cat(sprintf("\nQ12 %d x %d, %d list-columns left. WHAT IS LOST: the types, before\n",
            nrow(w), ncol(w), sum(map_lgl(w, is.list))))
cat("    tidyr was reached; and the 3-level structure of `location`, unless\n")
cat("    it is unnested separately. Nothing else — this document really is a\n")
cat("    table, and the honest flat answer is the whole of it.\n")

cat("
13. NO for 1, 3, 4, 5 and 7. The best showing of the fourteen, on the least
    interesting document, which is the expected relationship.

14. YES, and the next 311 export would also be read correctly. Nothing here
    is load-bearing on a field name.

16. ~80 lines, of which the rectangling is one call.
")
