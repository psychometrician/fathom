# purrr — npm registry metadata for `express`
#
# THIS FILE IS THE SCORING TEMPLATE. Copy the header shape into every new attempt
# file rather than inventing a second format.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr 1.2.2 (+ jsonlite 2.0.0 to parse)
#  file          ../source.json   786 KB, 288 versions, 25,044 paths
#  measured      2026-08-08
#  run           cd corpus/01-npm-registry/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             -   -                   TODO
#   2 how deep                                    -   -                   TODO
#   3 what is one record                          -   -                   TODO
#   4 always present vs sometimes                 -   -                   TODO
#   5 does any field change type                  -   -                   TODO
#   6 are any keys actually data                  -   -                   TODO
#   7 how many records                            -   -                   TODO
#   8 three named fields to a table               6   YES, all four       yes
#   9 a field missing from some rows              -   -                   TODO
#  10 flatten the deepest array                   -   -                   TODO
#  11 find every path matching something          -   -                   TODO
#  12 flattest honest table                       -   -                   TODO
#  13 needed the shape in advance?                    see notes below
#  14 survives the next file unchanged?               TODO
#  15 readable a week later?                          TODO
#  16 lines, and how much is ceremony?                TODO
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)

# Printed rather than typed. The header above records what produced the scores;
# this line records what just ran, and a difference between them means the re-run
# is not comparable. It is code rather than trust because two of this corpus's
# first three headers named a version that was not installed.
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

# ── Q8. Pull three named fields into a table, one row per record. ────────────
# 288 rows, one per released version.
tbl <- map_dfr(doc$versions, \(v) data.frame(
  version = v$version,
  author  = v$author$name %||% NA_character_,
  tarball = v$dist$tarball
))

stopifnot(nrow(tbl) == 288)

# WHAT IT COST.
#
# `%||% NA` is not decoration. 31 of the 40 keys seen across the 288 version
# objects are absent from at least one of them, so any field reached without a
# default is one ragged record away from stopping the whole map. purrr makes that
# easy to write and does not make it easy to *remember*: the code reads as though
# `author` were always there.
#
# Q13, ANSWERED HERE BECAUSE IT IS THE POINT OF THE PROJECT.
# Four things had to be known before a line of this could be written:
#   1. that `versions` is the thing to iterate
#   2. that one row is a version
#   3. that the author's name is nested at `author$name`, not at `author`
#   4. that the tarball is at `dist$tarball`
# purrr told me none of them. They came from hand-written probe scripts, which
# is the exploring phase, and it happened before this file existed.

# ── Q1-Q7, Q9-Q12 ────────────────────────────────────────────────────────────
# Not attempted yet. Each one gets a numbered section here, the scoring row above
# filled in, and a note saying what it cost. A question purrr cannot answer
# records "cannot" and the reason; that is the most useful cell in the grid.
