# jqr — npm registry metadata for `express`
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr 1.4.0, over jq 1.8.2; versions printed below
#  file          ../source.json   786 KB, 288 versions, 25,044 paths
#  measured      2026-08-08
#  run           cd corpus/01-npm-registry/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is it sound                                 -   -                   CANNOT
#   1 what is in here                             1   YES, fatally        NO
#   2 how deep                                    1   no                  YES
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 1   no                  partly
#   5 does any field change type                  1   YES                 partly
#   6 are any keys actually data                  -   -                   CANNOT
#   7 how many records                            1   YES                 partly
#  13 needed the shape in advance?                    YES for 1, 5 and 7
#  14 survives the next file unchanged?               the CODE yes, the ANSWER no
#  15 readable a week later?                          NO
#  16 lines, and how much is ceremony?                6 expressions, no ceremony
# ─────────────────────────────────────────────────────────────────────────────

library(jqr)

cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "")
ask <- function(q) jq(txt, q)

# ── Q2. How deep? Correct, unaided, one expression. ──────────────────────────
stopifnot(ask("[paths|length]|max") == "6")

# ── Q1. What is in here? THE SAME EXPRESSION THAT WORKED ON 02 FAILS HERE. ───
# 3,104 and not 3,100 since 2026-08-13. The expression was `paths(scalars)`,
# which drops every `false` and `null` leaf because `select` tests its input for
# truthiness and `scalars` returns the value itself. Four field names were
# invisible: `_hasShrinkwrap`, `contributors`, `serverjs`, `wscript`.
# THE FINDING IS UNCHANGED — 3,104 against ~40 real fields is still OVER by 75x.
stopifnot(ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length') == "3104")

# 3,100 against a true answer of about 40, and on 02-hn-thread the identical
# expression returned a correct 11. Package names, script names and usernames are
# all "field names" to jq, because to JSON they are.
#
# rrapply's melt gave 3,112 for the same reason. TWO INDEPENDENT TOOLS, A QUERY
# LANGUAGE AND AN R WALKER, AGREEING TO WITHIN TWELVE ON A WRONG ANSWER. That
# agreement is the evidence: the failure is not a limitation of either tool, it
# is what happens to anyone who describes paths without deciding which keys are
# data.

# ── Q7. How many records? Only if you already chose. ─────────────────────────
stopifnot(ask("[..|objects]|length") == "6134")   # 6,134 objects, not 288 versions
stopifnot(ask(".versions|length") == "288")
# The first number is what jq offers unasked and answers nothing. The second is
# correct and required knowing that `versions` is the thing to count.

# ── Q4. Always present or sometimes? Partly. ─────────────────────────────────
stopifnot(ask("[..|objects|keys|length]|unique|length") == "35")
# 35 distinct key counts across the document's objects, which says raggedness
# exists without saying which fields or how much.

# ── Q0, Q3, Q6. CANNOT. ──────────────────────────────────────────────────────
# Q6 is the one that matters here, and jq has no notion of it. Note also that jq
# SILENTLY KEEPS THE LAST duplicate key, so a document losing data on the way in
# passes through reporting nothing.
#
# WHAT IT COST.
#
# Q2 for free and correct. Everything else either wrong or requiring the shape in
# advance, which is README.md's hypothesis with the cleanest possible case
# attached: the expressions did not change between file 02 and this one, and the
# answers went from right to useless.
#
# THE ONE THING JQ HAS THAT NOTHING ELSE DOES is that all of this is one
# expression each, on any document, with no setup. It is the best exploration
# tool that exists and it still cannot tell a version number from a field name.
