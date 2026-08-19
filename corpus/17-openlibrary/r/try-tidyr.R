# tidyr — an OpenLibrary search response, 200 work records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   64 KB, 200 docs
#  measured      2026-08-11
#  run           cd corpus/17-openlibrary/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  YES — 17 columns
#   2 how deep                                    2   NO                  by exhaustion
#   3 what is one record                          3   NO                  YES, and RIGHT
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  2   -                   CANNOT
#   6 are any object keys data                    2   -                   NO, correctly
#   7 how many records                            3   NO                  yes — 200 / 349
#  7a related by POSITION not nesting            12   NO                  YES — IT ZIPS
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              5  YES                  yes — keep_empty
#  10 flatten the deepest array                   4  YES                  yes
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       4  YES                  200 x 17
#  13 needed the shape in advance?                    NO for 1, 3, 4, 7, 7a
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~85
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS FILE IS THE FAIR ATTEMPT QUESTION 7a HAS BEEN WAITING FOR. QUESTIONS.md
# marks 7a — "is anything here related by position rather than by nesting" — as
# CIRCULAR and says so in the question itself: `06-espn-qbr` revealed the
# property and `design/probe.py` gained the feature answering it in the same
# session, so no other tool may be scored `cannot` on it. It then names the
# condition under which comparison becomes fair: A TOOL THAT PREDATES THE
# QUESTION HAS TO BE GIVEN A REAL ATTEMPT.
#
# tidyr predates it by years and this is that attempt. `author_key` and
# `author_name` are two arrays per document, aligned by position and by nothing
# else — the same property as the QBR file.
#
#   unnest_longer(c(author_key, author_name))   ->  349 rows, correctly paired
#
# IT ZIPS, AND ON A LENGTH MISMATCH IT RAISES rather than recycling or cross-
# joining. So question 7a is answered YES by an existing tool, and the honest
# reading is that the probe's feature is not novel — it is a reimplementation of
# something the tidyverse already spells in one call.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

docs <- fromJSON("../source.json", simplifyVector = FALSE)$docs

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7. ───────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = docs), x)),
                    type = "message")
w <- tibble(x = docs) |> unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d, and it is right: one row per work.\n", nrow(a), ncol(a)))
cat(sprintf("Q1  %d columns, %d list-columns. Q7  %d works.\n",
            ncol(w), sum(map_lgl(w, is.list)), nrow(w)))

# ── Q7a. THE CENTREPIECE. ──────────────────────────────────────────────────
cat("\nQ7a `author_key` and `author_name` are parallel arrays, aligned by\n")
cat("    POSITION and by nothing else — 06-espn-qbr's property.\n")
cat(sprintf("    lengths agree on every document: %s\n",
            all(lengths(w$author_key) == lengths(w$author_name))))
z <- w |> select(key, author_key, author_name) |>
  unnest_longer(c(author_key, author_name))
cat(sprintf("    unnest_longer(c(author_key, author_name)) -> %d rows, ZIPPED:\n",
            nrow(z)))
print(head(as.data.frame(z), 2))
cat(sprintf("    a cross join would have given %d. It did not do that.\n",
            sum(lengths(w$author_key)^2)))
bad <- tryCatch(w |> select(key, author_key, ia) |> unnest_longer(c(author_key, ia)),
                error = \(e) "RAISES")
cat(sprintf("    zipping arrays of DIFFERENT length: %s\n",
            if (identical(bad, "RAISES")) "RAISES — it will not recycle" else "silently proceeds"))
cat("    ══ QUESTION 7a IS ANSWERED YES BY AN EXISTING TOOL. ══\n")
cat("    QUESTIONS.md flags 7a as circular and says a tool predating it must\n")
cat("    be given a real attempt before anything is scored `cannot`. This is\n")
cat("    that attempt, and it succeeds — so the probe's positional alignment\n")
cat("    is a reimplementation rather than a new idea, and any claim resting\n")
cat("    on 7a being unanswerable elsewhere has to be withdrawn.\n")

# ── Q4 / Q9 / Q10. ─────────────────────────────────────────────────────────
cat("\nQ4/Q9  the list-columns, default versus keep_empty:\n")
for (cn in names(w)[map_lgl(w, is.list)]) {
  d <- nrow(w |> unnest_longer(all_of(cn)))
  k <- nrow(w |> unnest_longer(all_of(cn), keep_empty = TRUE))
  cat(sprintf("    %-16s %4d rows   keep_empty %4d   DROPS %3d works\n", cn, d, k, k - d))
}
cat("    `ia` drops 183 of 200 silently — the internet-archive ids are on the\n")
cat("    minority of works, and the default answer to `flatten this` is a\n")
cat("    table of the 17 works that happen to have one.\n")

# ── Q5 / Q8 / Q11 / Q12. ───────────────────────────────────────────────────
cat("\nQ5  CANNOT — the varying fields are list-columns.\n")
three <- tibble(x = docs) |>
  hoist(x, title = "title", year = "first_publish_year", editions = "edition_count") |>
  select(title, year, editions)
cat(sprintf("\nQ8  hoist() -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat("\nQ11 CANNOT. No predicate over values.\n")
cat(sprintf("\nQ12 %d x %d with %d list-columns. WHAT IS LOST: the author arrays\n",
            nrow(w), ncol(w), sum(map_lgl(w, is.list))))
cat("    collapse to one row per author-work pair, so any per-work count has\n")
cat("    to be taken before the zip. Nothing else — this document is close to\n")
cat("    a table already.\n")
cat("Q2  by exhaustion: unnest until no list-column is left.\n")

cat("
13. NO for 1, 3, 4, 7 and 7a. Question 7a is the one that matters and it is
    the first YES any tool other than the probe has scored on it.

14. YES. The next OpenLibrary page has the same parallel arrays and the same
    call zips them.

16. ~85 lines, and the zip is one of them.
")
