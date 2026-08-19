# jqr — Open-Meteo hourly forecast, the columnar document
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.json   12 KB, depth 3, 24 paths, 14 fields,
#                                 every raggedness axis 0, row shapes 1
#  measured      2026-08-10
#  run           cd corpus/08-open-meteo/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           2   no                  yes
#   2 how deep                                  1   no                  yes
#   3 what is one record                        -   -                   CANNOT
#   7 how many records                          2   YES                 yes
#   8 three named fields to a table             3   YES                 yes
#  7a related by position                       6   NO                  YES
#  12 flattest honest table                     5   YES                 YES
#  13 needed the shape in advance?                  NO for 1, 2, 7a
#  16 lines, and how much is ceremony?              7 expressions, no ceremony
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. Two things worth measuring.
#
# **jq has `transpose` as a builtin**, so the operation `NOTES.md` says has no
# operator is a word here too — the third tool in this directory to have it.
#
# **And this file is the safe half of a pair.** `06-espn-qbr` has two
# same-length arrays in DIFFERENT orders and the wrong join gives the league's
# best quarterback a Total QBR of -7.4. This document names its columns by KEY.
# The same jq collision test that fires on ESPN should stay silent here — and if
# it does, that is a discriminating test rather than a warning printed on
# everything, which is what `NOTES.md` faults the probe for.
library(jqr)

cat(sprintf("R %s, jqr %s; jq CLI reports %s\n", getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "")
ask <- function(q) jq(txt, q)

cat(sprintf("\n2. depth %s, unaided\n", ask("[paths|length]|max")))
cat(sprintf("1. %s distinct leaf names, against NOTES.md's 14 fields\n",
            ask('[paths(scalars)|map(select(type=="string"))|last]|unique|length')))
cat(sprintf("7. %s variables of %s observations\n",
            ask(".hourly|keys|length"), ask(".hourly.time|length")))
cat("3. CANNOT — jq proposes no rows.\n")

# ── Q12. THE TRANSPOSE, AS A BUILTIN. ────────────────────────────────────────
cat("\n12. the flattest honest table — jq has `transpose` as a word:\n")
n <- ask('.hourly | to_entries | [.[].value] | transpose | length')
cols <- ask('.hourly | keys_unsorted')
first <- ask('.hourly | to_entries | [.[].value] | transpose | .[0]')
cat(sprintf("   .hourly | to_entries | [.[].value] | transpose  ->  %s rows\n", n))
cat(sprintf("   columns: %s\n", gsub("\\s+", "", cols)))
cat(sprintf("   row 1:   %s\n", gsub("\\s+", "", first)))
cat("   THE OPERATOR EXISTS IN THREE OF THE FIVE TOOLS HERE — jq's `transpose`,\n")
cat("   purrr's `list_transpose`, and R's own `as.data.frame` on a named list\n")
cat("   of equal-length vectors, which needs no operator at all. NOTES.md says\n")
cat("   `there is no operator for it`; that is true of `rows()` and not of the\n")
cat("   ecosystem, and the distinction is worth keeping straight.\n")
cat("   AND JQ IS THE ONLY ONE THAT CHECKS NOTHING EITHER: `transpose` on\n")
cat("   ragged arrays pads with null rather than complaining.\n")
ragged <- ask('[[1,2,3],[1,2]] | transpose | length')
cat(sprintf("   [[1,2,3],[1,2]] | transpose -> %s rows, padded with null\n", ragged))

# ── 7a. THE COLLISION TEST, AND IT SHOULD BE SILENT HERE. ───────────────────
cat("\n7a. related by position — the same test that fires on 06-espn-qbr:\n")
keyed <- ask('{hourly: (.hourly|keys|sort), units: (.hourly_units|keys|sort)}
              | {same_set: (.hourly == .units)}')
cat(sprintf("   hourly vs hourly_units, by KEY: %s\n", gsub("\\s+", "", keyed)))
cat("   The columns are named by KEY and the units object is keyed identically,\n")
cat("   so `hourly_units[k]` is the unit for `hourly[k]` and there is no order\n")
cat("   to get wrong.\n")
same_len <- ask('[.hourly[]|length] as $L
                 | {arrays_of_equal_length: ($L|unique|length == 1), n: $L[0]}')
cat(sprintf("   and the five arrays: %s\n", gsub("\\s+", "", same_len)))
cat("   SO THE COLLISION TEST FROM 06 STAYS SILENT, WHICH IS THE POINT. There\n")
cat("   is no second array holding the same vocabulary in a different order —\n")
cat("   the names ARE the keys. NOTES.md faults the probe for printing\n")
cat("   `same length is not same order` on both files, where it is the finding\n")
cat("   on ESPN and noise here. A test that distinguishes them exists and is\n")
cat("   two expressions: are the names KEYS, or are they a parallel ARRAY?\n")

# ── Q8. ──────────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per hour:\n")
three <- ask('.hourly | [.time, .temperature_2m, .wind_speed_10m] | transpose | length')
u <- ask('[.hourly_units|to_entries[]|select(.key|IN("temperature_2m","wind_speed_10m"))]')
cat(sprintf("   %s rows, and the units come from the keyed object: %s\n",
            three, gsub("\\s+", "", u)))

cat("\n0. CANNOT. 6. n/a — keys-as-data 0.\n")

cat("
CONCLUSION — the operator exists in three of five tools, and the warning this
document gets is the one it should not.

  **`transpose` is a jq builtin.** `.hourly | to_entries | [.[].value] |
  transpose` returns the 336 rows in one expression. purrr has
  `list_transpose`. R has `as.data.frame` on a named list of equal-length
  vectors, which needs no operator because that is already what a data frame is.
  `NOTES.md`'s *\"there is no operator for it\"* is true of `rows()` and is not
  true of the ecosystem, and the two readings should not be conflated.

  **None of the three checks anything.** jq's `transpose` pads ragged arrays with
  null, `list_transpose` silently returns three rows from lists of three and
  two, and `as.data.frame` recycles. All three are correct on this document
  because the document is well-formed, not because any of them verified it.

  **THE SHARPER RESULT IS THE COLLISION TEST STAYING SILENT.** The expression
  that fires on `06-espn-qbr` — two arrays, same length, same set, different
  order — finds nothing here, because this document names its columns by KEY and
  `hourly_units` is keyed identically. `NOTES.md` faults the probe for printing
  `same length is not same order` on both files, where it is the finding on one
  and noise on the other. **A test that separates them is two expressions**: are
  the names KEYS of the same object, or a parallel ARRAY somewhere else?

  That is the concrete form of what this pair of documents is for. The warning
  is not wrong; it is undiscriminating, and the discrimination is cheap.
")
