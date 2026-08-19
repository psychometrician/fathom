# tidyr — Crossref works metadata, 1,000 scholarly records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   7.5 MB, 1,000 works, depth 9
#  measured      2026-08-11
#  run           cd corpus/21-crossref-works/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  YES — 57 columns
#   2 how deep                                    3   NO                  by exhaustion
#   3 what is one record                          4   NO                  YES, and RIGHT
#   4 always present vs sometimes                 6   NO                  YES — 17 always
#   5 does any field change type                  2   -                   CANNOT
#   6 are any object keys data                    2   -                   NO, correctly
#   7 how many records                            3   NO                  yes — 1,000
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              6  YES                  yes
#  10 flatten the deepest array                   6  YES                  yes
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       4  YES                  1,000 x 57
#  13 needed the shape in advance?                    NO for 1, 3, 4, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~85
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS ENTRY'S FINDING IS THE `$` PARTIAL-MATCHING TRAP, AND RECTANGLING CURES
# IT. On the parsed list, `rec$issue` silently returns `issued` — a publication
# date standing in for an issue number — on 905 of 1,000 works, because `issue`
# is ABSENT there and `issued` is the single longer match. That is entry 21's
# result and it is reproduced below on the raw list.
#
# AFTER `unnest_wider` IT CANNOT HAPPEN. Both `issue` and `issued` exist as
# columns on every row, so `$` always finds an exact match and the 905 works
# without an issue number come back NA. No warning is needed because there is
# nothing to warn about.
#
# AND THE CURE AND THE DAMAGE ARE ONE BEHAVIOUR. `unnest_wider` gives every
# record every column, which is exactly why the short name is always present —
# and exactly why ABSENT and NULL arrive as the same NA, the distinction entries
# 21 and 23 both turn on. ONE PROPERTY, TWO CONSEQUENCES, OPPOSITE SIGNS: it
# removes a silent wrong answer by removing the information that made it
# possible.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

items <- fromJSON("../source.json", simplifyVector = FALSE)$message$items

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7. ───────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = items), x)),
                    type = "message")
w <- tibble(x = items) |> unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d, and it is right: one row per work.\n", nrow(a), ncol(a)))
cat(sprintf("Q1  %d columns, %d list-columns. Q7  %d works.\n",
            ncol(w), sum(map_lgl(w, is.list)), nrow(w)))

# ── THE `$` TRAP, before and after. ────────────────────────────────────────
absent <- keep(items, \(x) !("issue" %in% names(x)) && ("issued" %in% names(x)))
cat(sprintf("\n    THE `$` TRAP ON THE PARSED LIST: %d of %d works have no `issue`\n",
            length(absent), length(items)))
cat(sprintf("    and do have `issued`. absent[[1]]$issue returns a %s — that is\n",
            class(absent[[1]]$issue)[1]))
cat("    `issued`, a publication date standing in for an issue number.\n")
cat(sprintf("\n    AFTER unnest_wider: columns %s both exist, so\n",
            paste(grep("^issue", names(w), value = TRUE), collapse = " and ")))
cat(sprintf("    w$issue is an exact match — %d present, %d NA, nothing borrowed.\n",
            sum(!is.na(w$issue)), sum(is.na(w$issue))))
cat("    ══ THE CURE AND THE DAMAGE ARE THE SAME BEHAVIOUR. ══\n")
cat("    Every record gets every column, so the short name is always there —\n")
cat("    and so ABSENT and NULL become one NA. The silent wrong answer is\n")
cat("    removed by removing the information that made it possible.\n")

# ── Q4 / Q9 / Q10. ─────────────────────────────────────────────────────────
inter <- Reduce(intersect, map(items, names))
cat(sprintf("\nQ4  %d of %d columns are on every work.\n", length(inter), ncol(w)))
cat("Q9/Q10  the list-columns that lose rows, default versus keep_empty:\n")
for (cn in names(w)[map_lgl(w, is.list)]) {
  d <- nrow(w |> unnest_longer(all_of(cn)))
  k <- nrow(w |> unnest_longer(all_of(cn), keep_empty = TRUE))
  if (k - d > 0)
    cat(sprintf("    %-22s %5d rows   keep_empty %5d   DROPS %3d works\n",
                cn, d, k, k - d))
}

# ── Q5 / Q8 / Q11 / Q12 / Q2. ──────────────────────────────────────────────
cat("\nQ5  CANNOT. Entry 21's only reported type change is `issued.date-parts`,\n")
cat("    `array[2] number` on 998 works and `array[2] null` on 2 — and a\n")
cat("    list-column cannot show that at all.\n")
three <- tibble(x = items) |>
  hoist(x, doi = "DOI", type = "type", publisher = "publisher") |>
  select(doi, type, publisher)
cat(sprintf("\nQ8  hoist() -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat("\nQ11 CANNOT. No predicate over values.\n")
cat(sprintf("\nQ12 %d x %d with %d list-columns. WHAT IS LOST: `type` is the\n",
            nrow(w), ncol(w), sum(map_lgl(w, is.list))))
cat("    discriminator entry 17's jq search ranks first on both metrics, and\n")
cat("    tidyr will group by it but cannot price the grouping — see\n")
cat("    ../../19-chicago-salaries/r/try-tidyr.R, where the same arithmetic is\n")
cat("    measured to the last digit on a document small enough to show it.\n")
cat("Q2  by exhaustion — the document is 9 levels and no call says so.\n")

cat("
13. NO for 1, 3, 4 and 7.

14. YES. Nothing here names a work or a publisher.

16. ~85 lines. The rectangling is one call; the trap comparison is ten.
")
