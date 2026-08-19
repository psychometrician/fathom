# jqr — crates.io summary
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.json   41 KB, six collections at the root, depth 4
#  measured      2026-08-11
#  run           cd corpus/23-cratesio-summary/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   PARTLY
#   1 what is in here                             2   NO                  yes — 140
#   2 how deep                                    1   NO                  yes — 4
#   3 what is one record                         12   NO                  computed, not volunteered
#   4 always present vs sometimes                 6   NO                  YES — three always-null
#   5 does any field change type                  4   NO                  yes — NONE
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                             2  NO                  three answers
#   8 three named fields to a table                2 YES                 yes
#   9 a field missing from some rows                2 YES                 yes
#  10 flatten the deepest array                     3 -                   NO ARRAY TO FLATTEN
#  11 find every path matching something            4 NO                  yes — 11, folds to 3
#  12 flattest honest table                         3 -                   CANNOT — returns TEXT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
#  14 survives the next file unchanged?               yes except Q8/Q9
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~90
#
# RULE-6 TIMING, FOURTH DOCUMENT. 14: 2.8x. 20: 2.5x on 29.6 MB. 22: 2.97x on
# 476 KB. This file is 41 KB — another order of magnitude down — and question 1
# is the same expression the Python attempt times.
# ─────────────────────────────────────────────────────────────────────────────

library(jqr)
cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

src <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
jqt <- function(prog) {
  t0 <- Sys.time()
  out <- jq(src, prog)
  list(out = out, secs = as.numeric(difftime(Sys.time(), t0, units = "secs")))
}
CRATE <- c("new_crates", "most_downloaded", "most_recently_downloaded", "just_updated")
FOUR <- paste0(".", CRATE, "[]", collapse = ", ")

cat("\nQ0  jqr parses or errors. jq keeps the LAST duplicate key silently and\n")
cat("    numbers become doubles. Same libjq as the Python binding. PARTLY.\n")

r <- jqt('[paths | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
cat(sprintf("\nQ1  %s distinct paths, %.3fs — the probe says 140\n", r$out, r$secs))
t_paths <- r$secs
r <- jqt('[paths | length] | max')
cat(sprintf("Q2  depth %s — the probe says 4\n", r$out))
r <- jqt('keys_unsorted | join(", ")')
cat(sprintf("Q1  the root is an OBJECT: %s\n", gsub('"', "", r$out)))

# ── Q3. THE FOUR-IN-ONE, AND THE OVERLAP. ───────────────────────────────────
r <- jqt(sprintf('[%s | keys | sort] | unique | length', FOUR))
cat(sprintf("\nQ3  distinct key-sets over all 40 crate records: %s\n", r$out))
cat("    ONE, in one expression — and it took `unique | length` on purpose.\n")
cat("    The probe prints `same shape as $.new_crates[]` unasked; that is\n")
cat("    defect 25's repair, and NO TOOL HERE VOLUNTEERS IT.\n")
cat("    NOTE this is the KEY-SET question. polars, DuckDB and jsonlite all\n")
cat("    compare TYPES instead and find THREE schemas, because\n")
cat("    `recent_downloads` is null on all ten `new_crates`. Both are right.\n")
r <- jqt(sprintf('{rows: ([%s] | length), distinct: ([%s | .id] | unique | length)}',
                 FOUR, FOUR))
cat(sprintf("\n     THE OVERLAP: %s\n", r$out))
r <- jqt(sprintf('[%s | .name] | group_by(.) | map(select(length > 1)) | map(.[0]) | join(", ")',
                 FOUR))
cat(sprintf("     appearing twice: %s\n", gsub('"', "", r$out)))
cat("     Seven crates are in more than one collection, so concatenating the\n")
cat("     four double-counts them. THE PROBE DOES NOT REPORT THIS EITHER.\n")

# ── Q4/Q5/Q6/Q7. ────────────────────────────────────────────────────────────
r <- jqt(sprintf('[%s | keys[]] | group_by(.) | map(select(length < 40)) | length', FOUR))
cat(sprintf("\nQ4  crate fields sometimes ABSENT: %s of 23\n", r$out))
# R has no implicit string concatenation across lines — that is a Python habit,
# and the first draft died on `unexpected string constant`. jq's own `\(...)`
# interpolation is worse still: reaching it through an R string literal needs
# escaping that came out as a literal backslash, so the counts print as JSON.
r <- jqt(sprintf(paste0('[%s | to_entries[] | select(.value == null) | .key]',
                        ' | group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)'),
                 FOUR))
cat(sprintf("Q4  written NULL: %s\n", paste(r$out, collapse = "")))
r <- jqt(sprintf(paste0('[%s | to_entries[] | select(.value == null) | .key] | group_by(.)',
                        ' | map(select(length == 40) | .[0]) | join(", ")'), FOUR))
cat(sprintf("Q4  NULL ON ALL 40: %s\n", gsub('"', "", r$out)))
cat("    A field that is never anything but null has ONE type — which is why\n")
cat("    tidyjson mistypes THREE fields here and not six. See ../r/try-tidyjson.R.\n")
CENSUS <- paste0(
  'def ptype: if type == "array" then (if length == 0 then "array"',
  ' else "array[1] " + (.[0]|type) end) else type end;',
  ' . as $d | [ paths as $p | {k: ($p | map(if type=="number" then "[]" else . end)',
  ' | join(".")), t: ($d | getpath($p) | ptype)} ]',
  ' | group_by(.k) | map({k: .[0].k, t: (map(.t) | unique',
  ' | map(select(. != "null")))}) | map(select(.t | length > 1)) | length')
r <- jqt(CENSUS)
cat(sprintf("\nQ5  paths with more than one non-null shape: %s — the probe says NONE\n", r$out))
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")
r <- jqt(sprintf('{num_crates, num_downloads, rows: ([%s] | length)}', FOUR))
cat(sprintf("\nQ7  %s\n", r$out))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
r <- jqt('[.new_crates[] | {name, max_version, downloads}] | length')
cat(sprintf("\nQ8  %s rows x 3, %.3fs\n", r$out, r$secs))
r <- jqt(sprintf('[%s | select(.homepage != null)] | length', FOUR))
cat(sprintf("\nQ9  `homepage` non-null on %s of 40\n", r$out))
cat("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is an object of six\n")
cat("    fields; question 10 has no target on this document.\n")
r <- jqt(sprintf(paste0('[%s | . as $c | .links | to_entries[]',
                        ' | {crate: $c.name, link: .key}] | length'), FOUR))
cat(sprintf("    flattening `links` instead: %s rows\n", r$out))
# jqr returns ONE character element per jq OUTPUT, so an array comes back as a
# single string and `length()` is 1. `.[]` emits one per line instead.
r <- jqt(paste0('[paths(type=="string" and test("^https?://"))',
                ' | map(if type=="number" then "[]" else . end) | join(".")]',
                ' | unique | .[]'))
paths11 <- gsub('"', "", r$out)
fold <- unique(sub("^(new_crates|most_downloaded|most_recently_downloaded|just_updated)\\.",
                   "<one of the four>.", paths11))
cat(sprintf("\nQ11 %d distinct URL paths, folding to %d: %s\n",
            length(paths11), length(fold), paste(fold, collapse = ", ")))
cat("    Same numbers as jq, ijson, glom, pydash, purrr and rrapply.\n")
cat("\nQ12 jqr returns TEXT. The honest table means handing the output back to\n")
cat("    jsonlite, and that round trip shows in no timing here.\n")
cat(sprintf("\n     RULE-6 TIMING, FOURTH DOCUMENT: question 1 took %.3fs from jqr.\n", t_paths))
cat("     ../python/try-jq.py prints the same expression's time. 14: 2.8x,\n")
cat("     20: 2.5x on 29.6 MB, 22: 2.97x on 476 KB, and this file is 41 KB.\n")
