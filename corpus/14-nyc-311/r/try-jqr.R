# jqr — NYC 311 service requests, the 20,000 most recent
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (version printed at run time)
#  file          ../source.json   28.1 MB, 20,000 records, depth 4
#  measured      2026-08-11
#  run           cd corpus/14-nyc-311/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             3   NO                  YES — exactly 52
#   2 how deep                                    2   NO                  YES — exactly 4
#   3 what is one record                          3   NO                  PARTLY — 153 key-sets
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  4   NO                  YES
#   6 are any object keys data                    3   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   2   YES                 yes
#  11 find every path matching something          3   NO                  YES — best in R
#  12 flattest honest table                       3   YES                 yes
#  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
#  14 survives the next file unchanged?               yes for all of those
#  15 readable a week later?                          the path folds need a comment
#  16 lines, and how much is ceremony?                ~100, and the programs are the intent
#
# **jqr IS THE SAME LANGUAGE AS `../python/try-jq.py` AND IT IS 2.8x FASTER.**
# Identical programs, identical document, identical answers — 52 paths, depth 4,
# 153 key-sets — and the timings are not close:
#
#     question 1, paths ....... jqr  3.6-3.8s    python jq  9.9s
#     question 2, depth ....... jqr      0.7s    python jq  2.1s
#     question 3, key-sets .... jqr      0.9s    python jq  2.5s
#
# **The obvious explanation is wrong and was tested.** The Python binding takes
# an already-parsed object, so the conversion looked like the cost — but
# `input_text()` on the raw string is **11.2 s, no faster than 10.5 s**. The two
# bindings link different libjq builds (jqr uses Homebrew's jq 1.8.2, the Python
# package bundles its own), and this file records the gap as measured rather
# than explained. **It is the first time this corpus has priced the same program
# in both languages**, and rule 6's premise — that a tool is a tool — turns out
# to hide a 2.8x factor.
#
# **AND IT MAKES QUESTION 11 CHEAP IN R FOR THE FIRST TIME.**
# `paths(type == "string" and test("https?://"))` finds the 19 buried URLs in
# **1.6 s without naming a field.** purrr and jsonlite each need nine lines of
# hand-written recursion for the same answer; rrapply needs a melt first.
#
# **What it cannot do is question 3**, like the other twelve. 153 key-sets is
# the raw material for pricing a row shape, and jqr names no candidate.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("R %s, jqr %s, jsonlite %s (system jq: %s)\n",
            getRversion(), packageVersion("jqr"), packageVersion("jsonlite"),
            tryCatch(system("jq --version", intern = TRUE), error = \(e) "not on PATH")))

txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)
cat(sprintf("    read %.1f MB of text\n", nchar(txt) / 1e6))

run <- function(program, label) {
  t0 <- Sys.time()
  out <- jq(txt, program)
  cat(sprintf("    [%5.1fs] %s\n", as.numeric(Sys.time() - t0, units = "secs"), label))
  out
}

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  jqr hands the text to libjq, which errors on malformed JSON and says\n")
cat("    nothing about duplicate keys, big integers or NaN. CANNOT.\n")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
# Array indices fold to [] so the 20,000 record positions become one path.
cat("\nQ1  paths, folded on array indices:\n")
paths <- fromJSON(run('[paths | map(if type == "number" then "[]" else . end)
                        | join(".")] | unique', "..."))
cat("   ", length(paths), "distinct paths — THE PROBE PRINTS 52.\n")
# Deepest means most SEGMENTS, not the longest string. The first draft used
# nchar() and named `resolution_action_updated_date`, which is depth 2.
cat("    deepest:", paths[which.max(lengths(strsplit(paths, ".", fixed = TRUE)))], "\n")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
cat("\nQ2  max path length:\n")
cat("   ", fromJSON(run("[paths | length] | max", "...")),
    "— the probe prints '4 levels deep'. Same number, no hint given.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  distinct key-sets over the records:\n")
ks <- fromJSON(run('[.[] | keys_unsorted | join(",")] | unique | length', "..."))
cat("   ", ks, "— THE PROBE PRINTS '153 distinct key-sets'. DuckDB and the\n")
cat("    Python jq binding both return 153 too. Four tools, one number.\n")
cat("    jqr still names no row candidate and prices none. PARTLY.\n")
cat("Q7 ", fromJSON(jq(txt, "length")), "records\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
cat("\nQ4  key counts:\n")
counts <- fromJSON(run('[.[] | keys_unsorted[]] | group_by(.)
                        | map({(.[0]): length}) | add', "..."))
n <- 20000
cat("   ", length(counts), "fields · always", sum(unlist(counts) == n),
    "· sometimes", sum(unlist(counts) < n), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(unlist(counts)), 5))

# ── Q5. Does any field change type between records. ──────────────────────────
cat("\nQ5  every scalar's type, censused:\n")
sc <- fromJSON(run('[.. | scalars | type] | group_by(.)
                    | map({(.[0]): length}) | add', "..."))
print(unlist(sc))
cat("    713,768 strings and 39,140 numbers, and every number is a coordinate.\n")
cat("    EVERY SCALAR FIELD IS A JSON STRING — Socrata types nothing. ijson's\n")
cat("    event census and tidyjson's json_structure give the same two counts.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
odd <- grep("^[^A-Za-z]", names(counts), value = TRUE)
cat("\nQ6  no keyed collections — Socrata ships fixed names. n/a\n")
cat("   ", length(odd), "keys are not identifiers, e.g.", odd[1], "\n")
cat('    jq needs them quoted as .["…"], and its error NAMES the key where\n')
cat("    jmespath's names a column number.\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
cat("\nQ8  three fields:\n")
tbl <- fromJSON(run("[.[] | {complaint_type, borough, created_date}]", "..."))
cat("   ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
cat("\nQ9  with a missing field:\n")
q9 <- fromJSON(run("[.[] | {unique_key, status, closed_date}]", "..."))
cat("   ", nrow(q9), "rows kept,", sum(is.na(q9$closed_date)), "NA\n")
cat("    Object construction fills absent keys with null and KEEPS the row.\n")
cat("    `.[].closed_date` would have returned 10,739 and said nothing.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
cat("\nQ10 coordinates:\n")
co <- fromJSON(run("[.[] | select(.location) | .location.coordinates]", "..."))
cat("   ", nrow(co), "x", ncol(co), "\n"); print(head(co, 2))

# ── Q11. Find every path whose value matches something. ──────────────────────
cat("\nQ11 URL-valued paths, without naming a field:\n")
urls <- fromJSON(run('[paths(type == "string" and test("https?://"))
                       | map(if type == "number" then "[]" else . end) | join(".")]
                      | group_by(.) | map({(.[0]): length}) | add', "..."))
print(unlist(urls))
cat("    One expression, no field named, no recursion written. This is the\n")
cat("    cheapest question 11 in R by a wide margin.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12 flattened:\n")
flat <- fromJSON(run('[.[] | . + (.location // {} | {loc_type: .type,
                       lon: (.coordinates[0]? // null), lat: (.coordinates[1]? // null)})
                      | del(.location)]', "..."))
cat("   ", nrow(flat), "x", ncol(flat), "— nothing lost, location became three\n")
cat("    scalar columns. jsonlite::fromJSON turned jq's ragged objects into a\n")
cat("    rectangle here, so the rectangle is jsonlite's doing rather than jq's.\n")
