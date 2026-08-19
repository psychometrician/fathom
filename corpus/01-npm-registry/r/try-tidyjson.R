# tidyjson — npm registry metadata for `express`
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson 0.3.3.1; versions printed below
#  file          ../source.json   786 KB, 288 versions, 25,044 paths
#  measured      2026-08-08
#  run           cd corpus/01-npm-registry/r && Rscript try-tidyjson.R
#                SLOW ON PURPOSE: json_schema takes about a minute here.
#
#  question                                    lines  shape known first?  worked
#   0 is it sound                                 -   -                   CANNOT
#   1 what is in here                             2   no                  NO
#   2 how deep                                    1   no                  YES
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 -   -                   NO
#   5 does any field change type                  1   no                  partly
#   6 are any keys actually data                  -   -                   CANNOT
#   7 how many records                            -   -                   NO
#  13 needed the shape in advance?                    NO, and it did not help
#  14 survives the next file unchanged?               yes, and gets worse
#  15 readable a week later?                          the output is not readable
#                                                     at all, at any distance
#  16 lines, and how much is ceremony?                ~6; the cost is 58 seconds
# ─────────────────────────────────────────────────────────────────────────────

library(tidyjson)
suppressMessages(library(dplyr))

cat(sprintf("R %s, tidyjson %s\n", getRversion(), packageVersion("tidyjson")))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "")

# ── Q1. json_schema, the one tool in the grid built for this question. ───────
t0 <- Sys.time()
sch <- json_schema(txt)
elapsed <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("  json_schema: %d chars in %.0f s  (source is %d chars)\n",
            nchar(sch), elapsed, nchar(txt)))

stopifnot(nchar(sch) > 480000)
# 489,696 characters. THE SCHEMA IS 61% THE SIZE OF THE DOCUMENT IT DESCRIBES,
# and it took 58 seconds to produce. The cause is keys-as-data: every one of the
# 288 version strings becomes a key in the schema, each carrying a full copy of
# the version object's shape, and `dependencies` does it again underneath.
#
# A schema that scales with the data is not a schema. It is the document with the
# values replaced by the word "string".

# ── Q2. json_structure. Correct, and the only clean answer here. ─────────────
st <- as.data.frame(json_structure(txt))
stopifnot(max(st$level) == 6L)

# ── Q5, partly. The type census, which is genuinely useful. ──────────────────
census <- table(st$type)
stopifnot(all(c("object", "array", "string", "number") %in% names(census)))
# No nulls at all in this document, against 1,006 in 02-hn-thread. That contrast
# is how you would find, unaided, that npm is ragged by absence and the thread is
# ragged by null.

# ── Q1 again, the other way, and it fails the same way as everything else. ───
names_seen <- length(unique(na.omit(st$name)))
stopifnot(names_seen > 3000L)
# Because version strings, package names and usernames are all `name` values in
# json_structure, exactly as they are leaf names to rrapply and jq.
#
# WHAT IT COST.
#
# FIFTY-EIGHT SECONDS. jqr answered more of these questions in 0.02 s and rrapply
# in 0.01 s. On 02-hn-thread the same call took 7 s for a 193 KB file. tidyjson is
# between two and three orders of magnitude slower than the alternatives, and the
# thing it is slow at is the question this project says matters most.
#
# THE THREE DESCRIBERS FAIL IDENTICALLY AND FOR ONE REASON. rrapply says 3,112
# field names, jq says 3,100, tidyjson says over 3,000 and a half-megabyte
# schema. None of them can tell a version number from a field name, so all three
# report the data as though it were structure. That is not three tool
# limitations. It is one missing idea, and it is the one design/probe.py adds.
