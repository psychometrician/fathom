# tidyr — Docker Hub tags for library/python, 100 tags
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   480 KB, 100 tags, 1,388 images
#  measured      2026-08-11
#  run           cd corpus/22-dockerhub-tags/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  YES — 16 columns
#   2 how deep                                    2   NO                  by exhaustion — 3
#   3 what is one record                          8   NO                  YES — BOTH SHAPES
#   4 always present vs sometimes                14   NO                  YES, AND IN THREE
#                                                                         STATES
#   5 does any field change type                  2   -                   CANNOT
#   6 are any object keys data                    2   -                   NO, correctly
#   7 how many records                            4   NO                  yes — 100 / 1,388
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              3  YES                  yes
#  10 flatten the deepest array                   6  YES                  yes — 1,388 x 12
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       5  YES                  1,388 x 26
#  13 needed the shape in advance?                    NO for 1, 3, 4, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~90
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS FILE MEASURES THE THING VERDICT.md FLAGGED FOR THE AUTHOR AND DID NOT
# SETTLE: the probe's emptiness counts NULLS and not EMPTY STRINGS. Entry 22's
# images table has three states, the probe's headline figure is the nulls alone,
# and the note says the choice is defensible but unnamed.
#
# THE NUMBERS, over the images table's scalar cells:
#
#   NA (a JSON null)     2,485    14.9%
#   empty string ""      2,776    16.7%
#   either              5,261    31.6%
#
# AND THE PART THAT DECIDES IT: THE TWO KINDS DO NOT MIX WITHIN A COLUMN. Not
# one of the twelve fields uses both. `features` and `os_features` are the empty
# string on ALL 1,388 images; `variant` and `os_version` are null on 1,125 and
# 1,360 and are never empty. THE DISTINCTION IS A PER-FIELD CONVENTION, NOT A
# PER-CELL JUDGEMENT — two fields say "nothing here" one way and two say it the
# other, consistently, because they come from different writers.
#
# That is an argument for reporting them separately rather than folding them:
# folding hides which convention a field follows, and the convention is the
# only thing that tells you whether "" is a value or a hole.
#
# THE SECOND RESULT IS `bind`'s CONTRAST. NOTES.md pins jsonlite's `bind` at
# 100 x 213 — a column per (POSITION, FIELD) pair, so the width is set by the
# longest child array. tidyr's unnest_longer gives 1,388 x 12 for the same data:
# THE SAME INFORMATION AS ROWS INSTEAD OF AS COLUMNS, and the width stops
# depending on the deepest tag.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

tags <- fromJSON("../source.json", simplifyVector = FALSE)$results

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7. ───────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = tags), x)),
                    type = "message")
w <- tibble(x = tags) |> unnest_wider(x, names_repair = "unique_quiet")
img <- w |> select(name, images) |> unnest_longer(images) |>
  unnest_wider(images, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d — one row per TAG.\n", nrow(a), ncol(a)))
cat(sprintf("Q3  the other defensible row is one per IMAGE: %d x %d\n",
            nrow(img), ncol(img)))
cat(sprintf("Q7  %d tags, or %d images. Q1  %d columns at the top.\n",
            nrow(w), nrow(img), ncol(w)))
cat("    AND THAT IS THE CONTRAST WITH `bind`. NOTES.md pins jsonlite at\n")
cat("    100 x 213 — a column per (position, field) pair, so the width is set\n")
cat(sprintf("    by the longest child array. Here the same data is %d x %d:\n",
            nrow(img), ncol(img)))
cat("    ROWS INSTEAD OF COLUMNS, and the width no longer depends on the\n")
cat("    deepest tag.\n")

# ── Q4. THE CENTREPIECE: three states of empty. ────────────────────────────
cat("\nQ4  THE THREE STATES OF EMPTY, over the images table's scalar cells:\n")
scal <- names(img)[map_lgl(img, \(c) !is.list(c))]
tot <- 0; nul <- 0; emp <- 0
for (cn in scal) {
  v <- img[[cn]]
  tot <- tot + length(v)
  nul <- nul + sum(is.na(v))
  emp <- emp + sum(!is.na(v) & v == "", na.rm = TRUE)
}
cat(sprintf("      cells            %6d\n", tot))
cat(sprintf("      NA (JSON null)   %6d   %5.1f%%\n", nul, 100 * nul / tot))
cat(sprintf("      empty string \"\"  %6d   %5.1f%%\n", emp, 100 * emp / tot))
cat(sprintf("      either           %6d   %5.1f%%\n", nul + emp, 100 * (nul + emp) / tot))
cat("\n    AND THEY DO NOT MIX WITHIN A COLUMN:\n")
mixed <- 0
for (cn in scal) {
  v <- img[[cn]]
  n <- sum(is.na(v)); e <- sum(!is.na(v) & v == "", na.rm = TRUE)
  if (n > 0 || e > 0) {
    if (n > 0 && e > 0) mixed <- mixed + 1
    cat(sprintf("      %-14s null %4d   empty %4d   of %d\n", cn, n, e, length(v)))
  }
}
cat(sprintf("      columns using BOTH conventions: %d\n", mixed))
cat("    ══ IT IS A PER-FIELD CONVENTION, NOT A PER-CELL JUDGEMENT. ══\n")
cat("    Two fields always say `nothing here` with \"\" and two always say it\n")
cat("    with null, because they come from different writers. Folding the two\n")
cat("    into one emptiness figure hides which convention a field follows —\n")
cat("    and the convention is the only thing that tells you whether an empty\n")
cat("    string is a value or a hole. THAT IS AN ARGUMENT FOR REPORTING THEM\n")
cat("    SEPARATELY, and it is offered as evidence rather than as a decision.\n")

# ── Q5 / Q8 / Q9 / Q11 / Q12 / Q2. ────────────────────────────────────────
cat("\nQ5  CANNOT — `images` is a list-column and nothing else varies.\n")
three <- tibble(x = tags) |>
  hoist(x, tag = "name", size = "full_size", pushed = "tag_last_pushed") |>
  select(tag, size, pushed)
cat(sprintf("\nQ8  hoist() -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
d <- nrow(w |> unnest_longer(images))
k <- nrow(w |> unnest_longer(images, keep_empty = TRUE))
cat(sprintf("\nQ9  unnest_longer(images) -> %d rows; keep_empty %d; DROPS %d.\n", d, k, k - d))
cat("    Every tag has at least one image, so the default is safe here — the\n")
cat("    only document of the fourteen where it is.\n")
cat("\nQ11 CANNOT. No predicate over values.\n")
flat <- w |> select(-images) |> mutate(i = row_number()) |>
  right_join(img |> mutate(i = match(name, w$name)), by = "i", suffix = c("", ".img"))
cat(sprintf("\nQ12 tags joined to images -> %d x %d. WHAT IS LOST: nothing\n",
            nrow(flat), ncol(flat)))
cat("    structural, and every tag field is repeated once per image.\n")
cat("Q2  3 levels, found by running out of list-columns.\n")

cat("
13. NO for 1, 3, 4 and 7. Question 3 is the good one: both defensible row
    shapes are one call each, and neither is priced.

14. YES.

16. ~90 lines, and the emptiness measurement is half of them.
")
