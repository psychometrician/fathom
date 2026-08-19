# tidyjson — one Hacker News comment thread
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson 0.3.3.1; versions printed below
#  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
#  measured      2026-08-08
#  run           cd corpus/02-hn-thread/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is it sound                                 -   -                   CANNOT
#   1 what is in here                             2   no                  partly
#   2 how deep                                    1   no                  YES
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 2   no                  partly
#   5 does any field change type                  2   no                  partly
#   6 are any keys actually data                  -   -                   CANNOT
#   7 how many records                            1   no                  YES
#  13 needed the shape in advance?                    NO
#  14 survives the next file unchanged?               yes; json_schema does not
#                                                     survive being READ
#  15 readable a week later?                          the calls yes, the output no
#  16 lines, and how much is ceremony?                ~8; the cost is runtime
# ─────────────────────────────────────────────────────────────────────────────

library(tidyjson)
suppressMessages(library(dplyr))

cat(sprintf("R %s, tidyjson %s\n", getRversion(), packageVersion("tidyjson")))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "")

# ── json_schema: the tool that most directly claims to answer Q1. ────────────
t0 <- Sys.time()
sch <- json_schema(txt)
elapsed <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("  json_schema: %d chars in %.1f s\n", nchar(sch), elapsed))

# IT EXPANDS THE RECURSION LITERALLY, thirteen times:
#   {"author":"string","children":[{"author":"string","children":[{"author": ...
# 3,228 characters to describe a record with 13 fields, and about seven seconds
# to do it on a 193 KB file. The self-similarity is the one fact that matters
# about this document, and json_schema responds to it by repeating itself.
stopifnot(nchar(sch) > 3000, grepl('"children": \\[\\{"author"', sch))

# ── json_structure: one row per node. Q2 and Q7 come out of it. ──────────────
st <- as.data.frame(json_structure(txt))
stopifnot(nrow(st) == 4704L)          # O(data): 4,704 rows for 13 fields

stopifnot(max(st$level) == 25L)                          # Q2
stopifnot(sum(st$type == "object", na.rm = TRUE) == 336L)  # Q7

# ── Q1 and Q4, partly. ───────────────────────────────────────────────────────
# Distinct field names per level is 13 at every level that has names at all —
# which IS the recursion, visible and unnamed, exactly as in rrapply's melt.
per_level <- st %>% filter(!is.na(name)) %>%
  group_by(level) %>% summarise(n = n_distinct(name))
stopifnot(all(per_level$n == 13L))

# ── Q5, partly, and this is tidyjson's real contribution. ────────────────────
# The type census counts nulls as a type of their own, which no other tool here
# does. 1,006 nulls in a document with "no raggedness" is the null-against-value
# raggedness the axes were split for on 2026-08-08.
census <- table(st$type)
stopifnot(census[["null"]] == 1006L)

# ── Q0, Q3, Q6. CANNOT. ──────────────────────────────────────────────────────
# Q0: nothing. tidyjson parses or errors.
# Q3: json_structure produces one row per NODE, which is a row shape nobody
#     asked for and is not one of the three defensible ones.
# Q6: no notion of a key being data.
#
# WHAT IT COST.
#
# SEVEN SECONDS, on a 193 KB file, and that is the headline. jqr answered more
# questions in 0.02 s and rrapply in 0.01 s. A describer you have to wait for is
# a describer you stop reaching for.
#
# json_schema is the only tool in the grid whose stated purpose is question 1,
# and it is the one that handles this document worst, because its output grows
# with the nesting rather than describing it. Compare design/probe.py, which
# prints the thirteen fields once and adds "RECURSIVE, 13 levels".
#
# WHAT IT UNIQUELY GIVES: null as a first-class type in the census. That is how
# you would find, without being told, that this file is ragged by null while
# being perfectly regular by absence.
