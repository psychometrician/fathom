# rrapply — one Hacker News comment thread
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply 1.2.8 (+ jsonlite 2.0.0 to parse); versions printed below
#  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
#  measured      2026-08-08
#  run           cd corpus/02-hn-thread/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is it sound                                 -   -                   CANNOT
#   1 what is in here                             3   no                  YES
#   2 how deep                                    1   no                  YES
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 2   no                  YES
#   5 does any field change type                  2   no                  partly
#   6 are any keys actually data                  2   no                  partly
#   7 how many records                            1   no                  YES
#  13 needed the shape in advance?                    NO — this is the finding
#  14 survives the next file unchanged?               yes, but the ANSWER degrades
#  15 readable a week later?                          the melt call yes; the
#                                                     post-processing no
#  16 lines, and how much is ceremony?                ~10, over half ceremony
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)

cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

# ── The whole tool, in one call. ─────────────────────────────────────────────
m <- rrapply(doc, how = "melt")     # 3,696 rows x 26 cols
Ls <- m[, grep("^L", names(m))]

# ── Q2. How deep? Free: one column per level. ────────────────────────────────
stopifnot(ncol(m) - 1L == 25L)      # 25

# ── Q1. What is in here? ─────────────────────────────────────────────────────
# The last non-NA level of each row is the field the value sits under.
leaf <- apply(Ls, 1, function(r) { r <- r[!is.na(r)]; if (length(r)) tail(r, 1) else NA })
fields <- table(leaf)
stopifnot(length(fields) == 11L)    # author created_at created_at_i id parent_id
                                    # points story_id text title type url

# ── Q4 and Q7, both free from the same table. ────────────────────────────────
# Every one of the 11 appears exactly 336 times, so nothing is ever absent and
# there are 336 records. Two questions answered by looking at one table.
stopifnot(all(fields == 336L))

# ── Q6. Are any keys data? Partly: cardinality per level is the signal. ──────
lvl_card <- sapply(Ls, function(c) length(unique(na.omit(c))))
#   L1 L2 L3 L4 L5 L6 L7 L8
#   12 25 12 14 12  9 12  7
# The ODD levels are field names and hold the same 12 every time; the even ones
# are array indices and vary with how many children a node has. Nothing here is
# keyed by data. On a document that IS keyed by data one of these numbers runs
# into the thousands, which is what makes it a signal — see ../../01-npm-registry,
# where L2 is 2,984.
stopifnot(lvl_card[["L1"]] == 12L, lvl_card[["L3"]] == 12L, lvl_card[["L5"]] == 12L)

# That alternating 12 is also the recursion, sitting in plain sight and unnamed:
# the same twelve field names at every odd level, all the way down.

# ── Q5. Does any field change type? Partly. ──────────────────────────────────
# `value` is a list, so the types are there, but melt has already discarded the
# distinction between "absent" and "null" — both arrive as NULL in the list.
tp <- tapply(m$value, leaf, function(v) length(unique(sapply(v, class))))
# points/title/url are null on 335 of 336 nodes and this does not say so.

# ── Q0, Q3. CANNOT. ──────────────────────────────────────────────────────────
# Q0: rrapply is handed an already-parsed list. Every soundness question was
#     answered by jsonlite before rrapply saw anything, and jsonlite reports
#     nothing unless it throws.
# Q3: melt does not name a row shape. It produces one row per LEAF, which is a
#     fourth shape nobody asked for — 3,696 rows for a 336-node thread.
#
# WHAT IT COST.
#
# This is the strongest existing describer measured so far, and it is not close.
# One function call, no arguments to learn, 0.01 s, and Q2 falls out of ncol().
# On this file Q1, Q4 and Q7 are all correct.
#
# THE CATCH IS THE SHAPE OF THE OUTPUT. 26 columns for a 25-level document, so
# the width is O(depth) exactly as the first version of design/probe.py was. You
# cannot read the melt table; you can only aggregate it, and every aggregation
# above is a line the user had to invent. rrapply supplies the material and none
# of the answers.
#
# AND IT NEVER SAYS THE WORD "RECURSIVE". The 11 field names repeat identically
# at all 13 levels, which is the single most important fact about this document,
# and it is visible in the melt table only if you already suspected it.
