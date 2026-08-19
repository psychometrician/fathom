# tidyr — 100 GitHub issues from the tidyverse/dplyr repository
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   688 KB, 100 issues
#  measured      2026-08-11
#  run           cd corpus/15-github-issues/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  YES — 36 columns
#   2 how deep                                    3   NO                  by exhaustion
#   3 what is one record                          4   NO                  YES, and RIGHT
#   4 always present vs sometimes                 6   NO                  YES — 5 always empty
#   5 does any field change type                  2   -                   CANNOT
#   6 are any object keys data                    2   -                   NO, correctly
#   7 how many records                            3   NO                  yes — 100 / 166
#   8 three named fields to a table               4  YES                  yes
#   9 a field missing from some rows             12  YES                  YES — AND IT JOINS
#                                                                         THE MAJORITY
#  10 flatten the deepest array                   8  YES                  yes — the object trap
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       4  YES                  100 x 36
#  13 needed the shape in advance?                    NO for 1, 3, 4, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~90
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS ENTRY'S FINDING IS THE WRITTEN-NULL SPLIT, AND TIDYR SETTLES IT 3–1.
# VERDICT.md records that purrr's `pluck(.default =)` returns the DEFAULT for a
# key that is present with a null value, while glom's `Coalesce` and pydash's
# `get` return the NULL itself. `hoist` is tidyr's member of that family and it
# RETURNS THE NULL — so the defaulting verbs split three to one, and purrr is
# the outlier rather than the rule.
#
# `milestone` IS THE PERFECT TEST AND THE DOCUMENT SUPPLIES IT: the key is on
# all 100 issues and is null on 95. Nothing is absent; everything is written.
#
# THE OTHER RESULT IS THE OBJECT TRAP AT ITS CLEAREST. unnest_longer(user)
# returns 1,900 rows from 100 issues — not because any issue has many users, but
# because `user` is an OBJECT with 19 fields and unnest_longer counts FIELDS
# when the thing below it is an object and ELEMENTS when it is an array. Same
# verb, same spelling, two meanings, and only the data says which.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

issues <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7. ───────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = issues), x)),
                    type = "message")
w <- tibble(x = issues) |> unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d, and it is right: one row per issue.\n", nrow(a), ncol(a)))
cat(sprintf("Q1  %d columns, %d of them list-columns. Q7  %d issues.\n",
            ncol(w), sum(map_lgl(w, is.list)), nrow(w)))

# ── Q9. THE CENTREPIECE: the written null. ─────────────────────────────────
present <- sum(map_lgl(issues, \(x) "milestone" %in% names(x)))
written <- sum(map_lgl(issues, \(x) "milestone" %in% names(x) && is.null(x$milestone)))
cat(sprintf("\nQ9  `milestone` is PRESENT on %d of %d issues and NULL on %d.\n",
            present, length(issues), written))
cat("    Nothing is absent, so this is purely the written-null case.\n")
h <- tibble(x = issues) |> hoist(x, ms = "milestone", .simplify = FALSE)
cat(sprintf("    hoist(x, ms = \"milestone\") -> %d entries come back NULL\n",
            sum(map_lgl(h$ms, is.null))))
deep <- tibble(x = issues) |> hoist(x, title = c("milestone", "title"))
cat(sprintf("    hoist through the null, c(\"milestone\", \"title\") -> %d NA of %d\n",
            sum(is.na(deep$title)), nrow(deep)))
cat("    ══ TIDYR RETURNS THE NULL, SO THE SPLIT IS THREE TO ONE. ══\n")
cat("      purrr   pluck(.default =)   returns the DEFAULT\n")
cat("      glom    Coalesce            returns the NULL\n")
cat("      pydash  get                 returns the NULL\n")
cat("      tidyr   hoist               returns the NULL\n")
cat("    Entry 15 recorded this as purrr and pydash sharing a blind spot, and\n")
cat("    a later measurement narrowed it to the deep path. The fourteenth tool\n")
cat("    makes purrr the ODD ONE OUT on the shallow case rather than half of a\n")
cat("    pair — which is the opposite of how the finding was first written.\n")

# ── Q10. the object trap. ──────────────────────────────────────────────────
nf <- n_distinct(unlist(map(w$user, names)))
cat(sprintf("\nQ10 unnest_longer(user) -> %d rows from %d issues.\n",
            nrow(w |> unnest_longer(user)), nrow(w)))
cat(sprintf("    `user` is an OBJECT with %d fields, and %d x %d is %d. NO ISSUE\n",
            nf, nrow(w), nf, nrow(w) * nf))
cat("    HAS MANY USERS — the verb counted fields because the thing below it\n")
cat("    was an object. On `labels`, an array, the same verb counts elements:\n")
d <- nrow(w |> unnest_longer(labels)); k <- nrow(w |> unnest_longer(labels, keep_empty = TRUE))
cat(sprintf("      unnest_longer(labels) -> %d rows; keep_empty %d; DROPS %d\n", d, k, k - d))
cat("    SAME SPELLING, TWO MEANINGS, and nothing in the call distinguishes\n")
cat("    them. This is the one place tidyr's naming — wider versus longer,\n")
cat("    named after the RESULT — stops paying off.\n")

# ── Q4 / Q5 / Q12. ─────────────────────────────────────────────────────────
fill <- map_dbl(w, \(c) mean(if (is.list(c)) lengths(c) > 0 else !is.na(c)))
cat(sprintf("\nQ4  %d of %d columns are empty on every issue: %s\n",
            sum(fill == 0), ncol(w), paste(names(fill)[fill == 0], collapse = ", ")))
cat("Q5  CANNOT — the varying fields are list-columns.\n")
cat(sprintf("Q12 %d x %d with %d list-columns. WHAT IS LOST: every nested object\n",
            nrow(w), ncol(w), sum(map_lgl(w, is.list))))
cat("    stays a list until named individually, so the flat table is a\n")
cat("    decision per column rather than one call.\n")

# ── Q8 / Q11 / Q2. ─────────────────────────────────────────────────────────
three <- tibble(x = issues) |>
  hoist(x, number = "number", state = "state", author = c("user", "login")) |>
  select(number, state, author)
cat(sprintf("\nQ8  hoist() through `user` -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat("\nQ11 CANNOT. No predicate over values.\n")
cat("Q2  by exhaustion only: unnest until no list-column remains, and count\n")
cat("    the calls. The document is 4 levels; tidyr needs four verbs to say so\n")
cat("    and cannot say it in advance.\n")

cat("
13. NO for 1, 3, 4 and 7.

14. YES. The GitHub issues API is stable and nothing here is load-bearing on a
    field name, so the next page runs unchanged.

16. ~90 lines, and most of it is the written-null comparison rather than the
    rectangling, which is two calls.
")
