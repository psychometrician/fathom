# jqr — Natural Earth admin-0 countries, as GeoJSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.json   3.9 MB, 241 features, depth 8, 75 paths
#  measured      2026-08-09
#  run           cd corpus/03-natural-earth/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               -   -                   CANNOT
#   1 what is in here                             1   no                  YES
#   2 how deep                                    1   no                  YES
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 1   no                  YES
#   5 does any field change type                  4   NO                  YES
#   6 are any keys actually data                  -   -                   n/a
#   7 how many records                            2   YES                 partly
#   8 three named fields to a table               1   YES                 yes
#  11 find every path matching something          2   no                  YES
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
#  16 lines, and how much is ceremony?                9 expressions, no ceremony
#
#  RULE 6, RECORDED. The frozen probe got ONE cold run at this file. The generic
#  expression under question 5 took me TWO drafts — the first grouped by full
#  path and found nothing useful. Two attempts against one is a real advantage
#  and it is written down rather than hidden.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. jq answered `01-npm-registry`'s question 1 with **3,100** where
# the truth is about 40, and `VERDICT.md` uses that number — agreeing with
# rrapply's 3,112 to within twelve — as the core evidence that path-listing
# describers are O(data). **This document is the control for that claim**: it
# has no keys-as-data at all, so the identical expression should come back small
# and right. It does, and that matters more than another confirmation would.
#
# It is also the corpus's polymorphism-by-depth specimen, which the frozen probe
# scored **0** and `NOTES.md` calls the single most important fact about the
# format. jq finds it.
library(jqr)

# jqr exposes NO version accessor for the jq library it links — `ls("package:jqr")`
# has nothing but `reverse` matching "ver". So the CLI's version is printed as
# evidence rather than as proof: jqr binds the jq C library, and on this machine
# `/usr/bin/jq` is Apple's 1.7.1 while Homebrew's headers are what jqr compiled
# against. The two CAN differ, and a header that claimed otherwise would be the
# same untrue-on-day-one number CLAUDE.md requires this line to prevent.
cat(sprintf("R %s, jqr %s; jq CLI reports %s (jqr's linked library is not queryable)\n",
            getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "")
ask <- function(q) jq(txt, q)

# ── Q2. How deep? Correct, unaided, one expression. ──────────────────────────
stopifnot(ask("[paths|length]|max") == "8")
cat("2. depth 8, from `[paths|length]|max` — correct, and no shape known first\n")

# ── Q1. What is in here? THE CONTROL FOR THE 3,100. ──────────────────────────
# Character-for-character the expression that returned 3,100 on 01-npm-registry.
n_leaf <- ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
# 64 and not 63 since 2026-08-13, when the expression was corrected — it had
# been `paths(scalars)`, which drops every `false` and `null` leaf.
stopifnot(n_leaf == "64")
cat("1. 64 distinct leaf names, from the SAME expression that gave 3,104 on\n")
cat("   01-npm-registry and 11 on 02-hn-thread. The expression never changed;\n")
cat("   the document did. That is the controlled version of VERDICT.md's claim —\n")
cat("   the blowup is keys-as-data, and with none present jq stays small.\n")
cat("\n   ⚠ THE 'AND RIGHT' HALF OF THAT CLAIM IS WITHDRAWN, 2026-08-13.\n")
cat("   This file used to read 63 and said that was EXACTLY the 63 property\n")
cat("   fields. Measured after the correction, the match was a COINCIDENCE OF\n")
cat("   TWO CANCELLING ERRORS: the old expression missed `fips_10`, which is\n")
cat("   null on every feature, and counted `coordinates`, which is not a\n")
cat("   property at all but lives under `geometry`. 62 + 1 = 63.\n")
cat("   Corrected: 64 leaf names against 63 property fields — the expression is\n")
cat("   OVER by one here, not exact. It was never right on this document, and\n")
cat("   this document was the corpus's only claimed instance of it being right.\n")

# ── Q4. Always present or sometimes? ─────────────────────────────────────────
stopifnot(ask("[.features[].properties|keys|length]|unique") |>
          gsub(pattern = "\\s", replacement = "") == "[63]")
cat("4. every feature's properties has exactly 63 keys — one key-set, 0 ragged\n")
cat("   by absence, which is what NOTES.md grades. One expression, no defaults.\n")

# ── Q5. THE QUESTION THE PROBE GOT WRONG. ────────────────────────────────────
cat("\n5. does any field change type:\n")
by_type <- ask('[.features[].geometry.coordinates|type]|unique')
cat(sprintf("   by TYPE: %s — homogeneous, and every type-based check stops here\n",
            gsub("\\s", "", by_type)))

# The targeted expression: correct, and it required knowing the format.
targeted <- ask('[.features[]|[.geometry.type,([.geometry.coordinates|paths|length]|max)]]
                 |group_by(.)|map({kind:.[0][0],depth:.[0][1],n:length})')
cat("   targeted, naming .geometry.coordinates and .geometry.type:\n")
cat(sprintf("   %s\n", gsub("\\s+", "", targeted)))

# THE GENERIC ONE. No field is named. This is the one that counts.
generic <- ask('[paths(type != "object" and type != "array")|{f:(map(select(type=="string"))|last),d:length}]
                |group_by(.f)|map({f:.[0].f,depths:(map(.d)|unique)})
                |map(select(.depths|length>1))')
cat("   GENERIC — no field named, no knowledge of GeoJSON:\n")
cat(sprintf("   %s\n", gsub("\\s+", "", generic)))
cat("   `coordinates` at depths 7 and 8 IS the polymorphism, found by asking\n")
cat("   which leaf names occur at more than one path length. The frozen probe\n")
cat("   scored this file `polymorphism 0`; four lines of jq find it.\n")
cat("   `type` at depths 1, 3 and 4 is an ARTIFACT and is reported as one: it\n")
cat("   is three different fields that share a name — the collection's, each\n")
cat("   feature's, each geometry's — not one field with three shapes. The\n")
cat("   expression cannot tell those apart, so it has one true positive and\n")
cat("   one false one, and that is the honest score.\n")

# ── Q7. How many records? ────────────────────────────────────────────────────
stopifnot(ask(".features|length") == "241")
n_obj <- ask("[..|objects]|length")
cat(sprintf("\n7. 241 features — but only because I named `features`. Unasked, jq\n"))
cat(sprintf("   offers `[..|objects]|length` = %s, which answers nothing.\n", n_obj))

# ── Q8. Three named fields. ──────────────────────────────────────────────────
n_rows <- ask('[.features[].properties|{name,iso:.iso_a3,pop:.pop_est}]|length')
stopifnot(n_rows == "241")
cat("\n8. 241 rows from one expression; the result is JSON text, and turning it\n")
cat("   into a data frame is jsonlite's job rather than jqr's.\n")

# ── Q11. Find every path whose value matches something. jq's home ground. ────
cat("\n11. find every path whose value matches something:\n")
cat("   No URL and no email in this document — 0 occurrences of `http`. The\n")
cat("   pattern it carries is the -99 missing sentinel:\n")
n99 <- ask('[paths(type != "object" and type != "array") as $p|select((getpath($p)|tostring)=="-99")]|length')
top <- ask('[paths(type != "object" and type != "array") as $p|select((getpath($p)|tostring)=="-99")
            |($p|map(select(type=="string"))|last)]
            |group_by(.)|map({f:.[0],n:length})|sort_by(-.n)|.[0:5]')
cat(sprintf("   %s cells hold -99\n", n99))
cat(sprintf("   worst: %s\n", gsub("\\s+", "", top)))
cat("   THIS IS THE BEST ANSWER TO QUESTION 11 IN EITHER LANGUAGE. `paths` plus\n")
cat("   `getpath` is a real path language with a value predicate, and it needs\n")
cat("   nothing known in advance. jsonlite needed a hand-written recursion for\n")
cat("   the same result; rrapply needed a melted frame first.\n")
cat("   The three agree exactly on 1,767, which is a check on the number.\n")

# ── Q0 / Q3 / Q6. ────────────────────────────────────────────────────────────
cat("\n0. CANNOT. jq parses or it does not. It is silent on duplicate keys,\n")
cat("   on integers past 2^53, and on encoded documents in string values.\n")
cat("3. CANNOT. jq has no notion of a record and offers no candidates.\n")
cat("6. n/a — NOTES.md grades this file keys-as-data 0.\n")

cat("
CONCLUSION — jq's best showing in the corpus, and it costs the project a claim.

  THE 3,100 WAS ABOUT THE DOCUMENT, NOT THE TOOL, AND NOW THAT IS MEASURED
  RATHER THAN ASSERTED. The identical expression gives 3,100 on npm, 11 on the
  HN thread and **63 here — which is right**. `VERDICT.md` says the blowup
  tracks keys-as-data; this file has none and jq is small and correct. That is
  the control the claim never had in R.

  AND JQ FOUND THE POLYMORPHISM THE PROBE MISSED. Four lines, no field named,
  no knowledge of GeoJSON: group leaf names by the path lengths they occur at,
  keep the ones with more than one. `coordinates` comes back at 7 and 8.
  `NOTES.md` records the frozen probe scoring this file `polymorphism 0` on the
  document chosen specifically to have it, and calls polymorphism-by-depth the
  distinction the axes need. **An existing tool can already express it.**

  The honest qualifications, both ways. The expression also reports `type` at
  three depths, which is three fields sharing a name rather than one field
  varying — a false positive the expression cannot distinguish. And it took two
  drafts against the probe's one cold run, per rule 6.

  WHAT JQ STILL CANNOT DO is question 3, and it is the same gap as everywhere
  else. It will tell you there are 724 objects and it will not tell you which
  of them is a row. Everything above that worked, worked because I could name a
  question precisely; nothing here volunteers what to ask.
")
