# tidyr — npm registry metadata for `express`
#
# Scoring header follows try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   804,956 bytes, 288 versions, 25,044 paths
#  measured      2026-08-09
#  run           cd corpus/01-npm-registry/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             3   no                  PARTLY
#   2 how deep                                    -   -                   cannot
#   3 what is one record                          4   no                  WRONG
#   4 always present vs sometimes                 3   YES                 YES
#   5 does any field change type                  -   -                   cannot
#   6 are any keys actually data                  -   -                   WRONG
#   7 how many records                            2   YES                 YES
#   8 three named fields to a table               3   YES                 YES
#  13 needed the shape in advance?                    see notes below
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE EXISTS, AND IT IS OVERDUE. tidyr was missing from CLAUDE.md's R
# list until 2026-08-09 while being installed the whole time, so seven corpus
# files were graded without the tidyverse's actual answer to nested JSON.
#
# `unnest_longer` is one row per array element, which is `rows("x.*")`.
# `unnest_wider` is fields to columns. `hoist` is `take` with paths. These are
# the closest prior art to this project's proposed words in either language.
#
# AND `unnest_auto` ATTEMPTS QUESTION 3, which VERDICT.md said no tool in either
# language attempts. It chooses between wider and longer and PRINTS ITS REASON.
# That claim was wrong and this file is the measurement that corrects it.

suppressMessages({
  library(tidyr); library(tibble); library(jsonlite); library(dplyr)
})

# Printed rather than typed. The header records what produced the scores below;
# this line records what just ran, and a difference means the re-run is not
# comparable. Two of this corpus's first three headers named a version that was
# not installed.
cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

# ── 3. what is one record — the question this file is here for ───────────────
cat("\n3. unnest_auto on `versions`, which is 288 versions of one package:\n")
v <- tibble(v = list(doc$versions))
msg <- capture.output(out <- suppressWarnings(unnest_auto(v, v)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   first columns:", paste(head(names(out), 5), collapse = ", "), "\n")
cat("   THE ANSWER IS 288 ROWS. It chose wider and produced one row with 288\n")
cat("   columns, each named after a version number.\n")

# ── 6. are any keys actually data — the same failure, named ──────────────────
cat("\n6. and that IS question 6, answered wrongly.\n")
cat("   `unnest_auto`'s rule is whether the elements have names in common. The\n")
cat("   288 version objects each have names, so it reads them as fields. This is\n")
cat("   the keys-as-data failure that gives jq 3,100 field names and rrapply\n")
cat("   3,112 on this file, arriving through a third door — and unlike those two\n")
cat("   it is a decision about the TABLE rather than about a listing.\n")

# ── the right answer, once a person supplies question 3 ──────────────────────
cat("\n   the correct call, which a person has to know to make:\n")
cat("   and the FIRST attempt at it failed, which is worth recording:\n")
cat("   unnest_wider() refused, because every version object has its own\n")
cat("   `version` field and it collided with the key column named `version`:\n")
cat("     Error: Can't duplicate names between the affected columns and the\n")
cat("     original data. These names are duplicated: `version`, from `v`.\n")
cat("   design/rows.py hit the identical collision with `children**` and\n")
cat("   SILENTLY OVERWROTE the key until it was repaired. tidyr raises and\n")
cat("   names two fixes. Loud beats silent on a document nobody has read.\n")
right <- tibble(key = names(doc$versions), v = unname(doc$versions)) |>
  unnest_wider(v, names_repair = "unique_quiet")
cat("   with a distinct key name ->", nrow(right), "rows x", ncol(right), "cols\n")

# ── 4 / 7. always vs sometimes, and how many ─────────────────────────────────
cat("\n4/7.", nrow(right), "versions,",
    sum(sapply(right, function(c) !any(sapply(c, is.null)))),
    "columns with no missing value, of", ncol(right), "\n")

# ── 8. three named fields, which is what hoist is for ────────────────────────
cat("\n8. hoist(), which is `take` with paths:\n")
three <- tibble(version = names(doc$versions), v = unname(doc$versions)) |>
  hoist(v, author = c("author", "name"), tarball = c("dist", "tarball")) |>
  select(version, author, tarball)
cat("   ", nrow(three), "rows x", ncol(three), "cols, one expression\n")
print(head(as.data.frame(three), 2))

cat("
1, 2, 5. partly, cannot, cannot.

  tidyr describes ONE LEVEL at a time. `unnest_wider` on the root gives 18
  columns and tells you their names, which is more than glom or jmespath offer,
  and it says nothing about what is below them. Depth needs repeated unnesting,
  which needs the depth. Type variation is invisible: list-columns hold whatever
  they hold.

13. needed the shape in advance? PARTLY, AND THAT IS THE FINDING.

  Every other tool in this comparison needed question 3 answered before it could
  do anything. tidyr GUESSES, states the guess, and is wrong here — but being
  wrong out loud is a different category from not attempting. VERDICT.md's claim
  that no tool attempts question 3 was false, and it now says so.
")
