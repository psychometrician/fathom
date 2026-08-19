# rrapply — npm registry metadata for `express`
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply 1.2.8 (+ jsonlite 2.0.0 to parse); versions printed below
#  file          ../source.json   786 KB, 288 versions, 25,044 paths
#  measured      2026-08-08
#  run           cd corpus/01-npm-registry/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is it sound                                 -   -                   CANNOT
#   1 what is in here                             3   YES, fatally        NO
#   2 how deep                                    1   no                  YES
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 -   -                   NO
#   5 does any field change type                  2   no                  partly
#   6 are any keys actually data                  2   no                  partly
#   7 how many records                            -   -                   NO
#  13 needed the shape in advance?                    YES — and this is the
#                                                     finding, see the bottom
#  14 survives the next file unchanged?               the CODE yes, the ANSWER no
#  15 readable a week later?                          no
#  16 lines, and how much is ceremony?                ~10, over half ceremony
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)

cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

m <- rrapply(doc, how = "melt")     # 26,307 rows x 7 cols, in 0.01 s
Ls <- m[, grep("^L", names(m))]

# ── Q2. How deep? Free, and correct. ─────────────────────────────────────────
stopifnot(ncol(m) - 1L == 6L)

# ── Q1. What is in here? THE SAME CODE THAT WORKED ON 02 FAILS HERE. ─────────
leaf <- apply(Ls, 1, function(r) { r <- r[!is.na(r)]; if (length(r)) tail(r, 1) else NA })
stopifnot(length(unique(leaf)) == 3112L)   # the answer wanted is about 40

# 3,112 "field names", because a dependency's package name, a script's name and a
# user's name are all leaf names too. On 02-hn-thread the identical three lines
# returned a clean 11. The code survived the next file; the answer did not.

# ── Q6. Are any keys data? Partly, and this is rrapply's best moment. ────────
lvl_card <- sapply(Ls, function(c) length(unique(na.omit(c))))
#   L1   L2   L3   L4   L5   L6
#   18 2984   40  121    3    2
stopifnot(lvl_card[["L2"]] == 2984L, lvl_card[["L1"]] == 18L, lvl_card[["L3"]] == 40L)

# L2 at 2,984 against L1 at 18 and L3 at 40 is unmistakable once you look, and
# melt hands it to you for nothing. This is the single most useful thing any
# existing tool did in this comparison.

# ── AND HERE IS THE CIRCLE THAT MAKES IT NOT ENOUGH. ─────────────────────────
# L3 is 40, which IS the right answer to "what fields does a version have" — the
# number NOTES.md records. It is sitting in the output, correct, at level three.
#
# To use it you must already know that L2 is data and L3 is the record. That is
# question 6, answered before question 1 can be. rrapply computes the material
# for both and orders them the wrong way round, so the user has to arrive already
# suspecting the thing they came to find out.

# ── Q5, partly. Q0, Q3, Q4, Q7. CANNOT. ──────────────────────────────────────
# Q4 and Q7 were free on 02-hn-thread from the same `table(leaf)` and are useless
# here, because the table is 3,112 rows of mostly package names.
#
# WHAT IT COST.
#
# 0.01 s, one function call, and the depth for free. Fast and cheap.
#
# THE FAILURE IS EXACTLY THE ONE AXIS THIS FILE IS SEVERE ON. melt treats a data
# key and a field name as the same kind of thing, because in JSON they are — that
# is the whole problem, and no amount of post-processing inside melt's output can
# separate them without the cardinality trick above being applied by hand.
#
# Compare design/probe.py on the same file: six keys-as-data sites named with
# their evidence, 40 fields folded, 73 lines. The difference is not speed or
# power. It is that one of them answers question 6 before question 1.
