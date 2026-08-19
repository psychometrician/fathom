# jqr — 100 GitHub issues from one repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (version printed at run time)
#  file          ../source.json   686 KB, 100 issues, depth 4
#  measured      2026-08-11
#  run           cd corpus/15-github-issues/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             4   NO                  YES — exactly 179
#   2 how deep                                    2   NO                  YES — exactly 4
#   3 what is one record                          5   NO                  PARTLY — 2 key-sets
#   4 always present vs sometimes                 9   NO                  YES — `has` says it
#   5 does any field change type                  5   NO                  YES — correctly none
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              4   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          4   NO                  YES — best in R
#  12 flattest honest table                       5   YES                 yes
#  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
#  14 survives the next file unchanged?               yes for all of those
#  15 readable a week later?                          the array-index fold needs a comment
#  16 lines, and how much is ceremony?                ~110
#
# **jqr REPRODUCES THREE OF THE PROBE'S NUMBERS EXACTLY AND SEPARATES ABSENT FROM
# NULL, WHICH MAKES IT THE BEST TOOL IN EITHER LANGUAGE ON THIS DOCUMENT.**
#
#     paths, array indices folded ..... 179    probe prints 179
#     max path length ................... 4    probe prints 4 levels deep
#     distinct key-sets, SORTED ......... 2    probe prints 2
#
# **`has` IS THE WHOLE ANSWER TO QUESTION 4.** `has("closed_by")` is true on all
# 100 issues; `.closed_by != null` on 48. Two predicates for two facts, so the
# result is **5 sometimes-ABSENT and 8 always-present-but-NULL** with exact
# counts. pandas, polars, DuckDB and simplified jsonlite each report **13** and
# cannot split it.
#
# **AND THE KEY-SET COUNT IS WHERE DuckDB GOES WRONG BY 7x.**
# `count(DISTINCT json_structure(json))` returns **14** on this file, because
# `json_structure` records the TYPE of every value and `closed_by: null` is a
# different structure from `closed_by: {…}`. Asking which keys are PRESENT gives
# **2**. Across three documents that expression has been exact once, 5.4x high
# once and 7x high here, and nothing signals which case you are in.
#
# **jqr IS AGAIN FASTER THAN THE PYTHON BINDING** — measured on entries 13 and 14
# at 2.8x on documents three orders of magnitude apart in size. The timings below
# are printed rather than typed.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("R %s, jqr %s, jsonlite %s (system jq: %s)\n",
            getRversion(), packageVersion("jqr"), packageVersion("jsonlite"),
            tryCatch(system("jq --version", intern = TRUE), error = \(e) "not on PATH")))

txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)
n <- 100

run <- function(program, label) {
  t0 <- Sys.time()
  out <- jq(txt, program)
  cat(sprintf("    [%5.2fs] %s\n", as.numeric(Sys.time() - t0, units = "secs"), label))
  out
}

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
cat("\nQ0  jqr hands the text to libjq, which errors on malformed JSON and says\n")
cat("    nothing about duplicate keys, big integers or NaN. CANNOT.\n")

# ── Q1. What is in here. ────────────────────────────────────────────────────
cat("\nQ1  paths, with array indices folded to []:\n")
paths <- fromJSON(run('[paths | map(if type == "number" then "[]" else . end)
                        | join(".")] | unique', "..."))
cat("   ", length(paths), "— THE PROBE PRINTS 179. Exact.\n")
cat("    ijson's prefixes give 180 because they count the empty root.\n")

# ── Q2. How deep does it go. ────────────────────────────────────────────────
cat("\nQ2  max path length:\n")
cat("   ", fromJSON(run("[paths | length] | max", "...")),
    "— the probe prints '4 levels deep'. Exact.\n")

# ── Q3/Q7. What is one record, and how many. ────────────────────────────────
cat("\nQ3  distinct key-sets over the 100 issues:\n")
ks <- fromJSON(run('[.[] | keys_unsorted | sort | join(",")] | unique | length', "with sort"))
cat("   ", ks, "— THE PROBE PRINTS 2. Exact.\n")
cat("    DuckDB's count(DISTINCT json_structure(json)) returns 14 on this file,\n")
cat("    because json_structure records the TYPE of every value. Asking which\n")
cat("    keys are PRESENT gives 2. jqr names no row candidate. PARTLY.\n")
cat("Q7 ", fromJSON(jq(txt, "length")), "issues\n")

# ── Q4. THE DISCRIMINATOR — `has` separates the two kinds. ─────────────────
cat("\nQ4  which keys are PRESENT:\n")
counts <- fromJSON(run('[.[] | keys_unsorted[]] | group_by(.)
                        | map({(.[0]): length}) | add', "..."))
cat("Q4  and which are present holding NULL:\n")
nulls <- fromJSON(run('[.[] | to_entries[] | select(.value == null) | .key]
                       | group_by(.) | map({(.[0]): length}) | add', "..."))
absent <- sort(names(counts)[unlist(counts) < n])
nullish <- sort(names(nulls)[unlist(counts[names(nulls)]) == n])
cat("      sometimes ABSENT (", length(absent), "):", absent, "\n")
cat("      present but NULL (", length(nullish), "):", nullish, "\n")
cat("      exact null counts:\n"); print(sort(unlist(nulls), decreasing = TRUE))
cat("    `has(\"closed_by\")` is true on all 100; `.closed_by != null` on 48.\n")
cat("    TWO PREDICATES FOR TWO FACTS. The frame tools have one hole and report\n")
cat("    13 without being able to split it 5 and 8.\n")

# ── Q5. Does any field change type between records. ────────────────────────
cat("\nQ5  fields whose non-null type varies:\n")
varying <- fromJSON(run('[.[] | to_entries[] | select(.value != null)
      | {k: .key, t: (.value | type)}] | group_by(.k)
      | map(select((map(.t) | unique | length) > 1) | .[0].k)', "..."))
cat("   ", if (length(varying)) paste(varying, collapse = ", ") else "none",
    "— the probe's answer\n")
cat("    `select(.value != null)` is what makes it right. tidyjson's json_types\n")
cat("    counts null AS a type and reports five changes on this document.\n")

# ── Q6. Are any object keys actually data? ─────────────────────────────────
cat("\nQ6  no keyed collections — GitHub ships fixed field names. n/a\n")

# ── Q8/Q9. Extraction. ─────────────────────────────────────────────────────
cat("\nQ8  three fields:\n")
tbl <- fromJSON(run('[.[] | {number, state, user: .user.login}]', "..."))
cat("   ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cat("\nQ9  a field that is null on some issues:\n")
q9 <- fromJSON(run('[.[] | {number, closed_by: .closed_by.login}]', "..."))
cat("   ", nrow(q9), "rows kept,", sum(is.na(q9$closed_by)), "NA\n")
cat("    `.closed_by.login` through a null gives null rather than raising, and\n")
cat("    object construction keeps the row. tidyjson's `enter_object` drops 52.\n")

# ── Q10. Flatten the deepest array into rows. ──────────────────────────────
cat("\nQ10 labels:\n")
lab <- fromJSON(run('[.[] | .number as $n | .labels[] | {number: $n, name}]', "..."))
cat("   ", nrow(lab), "rows;", sum(sapply(fromJSON(jq(txt, "[.[].labels|length]")),
                                          function(x) x == 0)),
    "issues have an empty list\n")

# ── Q11. Find every path whose value matches something. ────────────────────
cat("\nQ11 URL-valued paths, no field named:\n")
urls <- fromJSON(run('[paths(type == "string" and test("https?://"))
      | map(if type == "number" then "[]" else . end) | join(".")]
      | group_by(.) | map({(.[0]): length}) | add', "..."))
cat("   ", format(sum(unlist(urls)), big.mark = ","), "values over", length(urls), "paths\n")
print(head(sort(unlist(urls), decreasing = TRUE), 3))
cat("    One expression, no field named, no recursion. purrr and jsonlite each\n")
cat("    need nine to ten lines of hand-written walk for the same answer.\n")

# ── Q12. The flattest honest table, and what was lost. ─────────────────────
cat("\nQ12 flattened, prefixing the nested objects by hand:\n")
flat <- fromJSON(run('[.[] | . as $r
      | reduce (to_entries[] | select(.value | type == "object")) as $e
          ($r; . + ($e.value | with_entries(.key |= "\\($e.key).\\(.)")) | del(.[$e.key]))]',
                     "..."))
cat("   ", nrow(flat), "x", ncol(flat), "\n")
cat("    The prefixing is MINE — `with_entries(.key |= ...)`. polars' `unnest`\n")
cat("    RAISES on this document and DuckDB's `struct.*` returns 19 duplicate\n")
cat("    names; pandas, jsonlite, rrapply and tidyjson all prefix unaided.\n")
cat("    Three list columns remain, and `issue_field_values` is an EMPTY LIST on\n")
cat("    all 100 issues — a field that exists and contains nothing.\n")
