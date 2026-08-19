# jqr — one Hacker News comment thread
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr 1.4.0, over jq 1.8.2; versions printed below
#  file          ../source.json   193 KB, 336 nodes, 13 levels of recursion
#  measured      2026-08-08
#  run           cd corpus/02-hn-thread/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is it sound                                 -   -                   CANNOT
#   1 what is in here                             1   no                  YES
#   2 how deep                                    1   no                  YES
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 1   no                  YES
#   5 does any field change type                  1   no                  YES
#   6 are any keys actually data                  -   -                   CANNOT
#   7 how many records                            1   no                  YES
#  13 needed the shape in advance?                    NO
#  14 survives the next file unchanged?               yes, but see npm
#  15 readable a week later?                          NO. this is jq's whole problem
#  16 lines, and how much is ceremony?                6 expressions, no ceremony
# ─────────────────────────────────────────────────────────────────────────────

library(jqr)

cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "")
ask <- function(q) jq(txt, q)

# ── Q2. How deep? One expression, no prior knowledge. ────────────────────────
stopifnot(ask("[paths|length]|max") == "25")

# ── Q1. What is in here? ─────────────────────────────────────────────────────
# `paths(scalars)` yields every route to a value; dropping the array indices and
# taking the last step gives the field a value sits under.
stopifnot(ask('[paths(scalars)|map(select(type=="string"))|last]|unique|length') == "11")

# ── Q7. How many records? ────────────────────────────────────────────────────
stopifnot(ask("[..|objects]|length") == "336")

# ── Q4. Always present or sometimes? ─────────────────────────────────────────
# Every object has all 13 keys, so the key count per object never varies.
stopifnot(ask("[..|objects|keys|length]|unique") == "[13]")

# ── Q5. Does any field change type? YES, and jq says so precisely. ───────────
# For each field name, the set of types its values take.
poly <- ask('[..|objects|to_entries[]]|group_by(.key)
             |map({key:.[0].key, types:(map(.value|type)|unique)})
             |map(select(.types|length>1))|length')
stopifnot(poly == "4")     # parent_id points title url, each null-against-value

# ── Q0, Q3, Q6. CANNOT. ──────────────────────────────────────────────────────
# Q0: jq refuses an unparseable document with a byte offset and says nothing
#     about duplicate keys, big integers or a truncated tail. Note that jq
#     SILENTLY KEEPS THE LAST duplicate key, so a document losing data passes
#     through it reporting nothing.
# Q3: nothing in jq names a row shape.
# Q6: nothing distinguishes a data key from a field name. Here there are none,
#     but jq could not have told you that — see ../../01-npm-registry, where
#     the same expressions return 3,100 field names instead of about 40.
#
# WHAT IT COST.
#
# Five of the eight questions, each in one expression, with no prior knowledge of
# the document. That is the best exploration score of any existing tool measured
# so far, and it directly contradicts the first version of README.md.
#
# Q5 IS WHERE JQ BEATS EVERYTHING ELSE HERE. `group_by(.key)` over `to_entries`
# gives per-field type sets in one pass. rrapply cannot do it because melt has
# already flattened nulls away, and tidyjson gives a type census without saying
# which field each type belongs to.
#
# AND IT IS UNREADABLE, WHICH IS THE POINT. The Q5 expression above took several
# attempts and will not survive question 15. Compare the same fact from
# design/probe.py: "parent_id  number x335, null x1". jq can compute the answer
# and cannot state it.
