# jqr — Docker Hub tags, 100 tags
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.json   476 KB, 100 tags under $.results, depth 5
#  measured      2026-08-11
#  run           cd corpus/22-dockerhub-tags/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   PARTLY
#   1 what is in here                             2   NO                  yes — 33
#   2 how deep                                    1   NO                  yes — 5
#   3 what is one record                          6   NO                  PARTLY
#   4 always present vs sometimes                 8   NO                  YES — three states
#   5 does any field change type                  6   NO                  yes — NONE
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                            2   NO                  yes, both numbers
#   8 three named fields to a table               2   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   2   YES                 yes — 1,388
#  11 find every path matching something          3   NO                  yes — 1
#  12 flattest honest table                       3   -                   CANNOT — returns TEXT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
#  14 survives the next file unchanged?               yes except Q8/Q9/Q10
#  15 readable a week later?                          yes, on this document
#  16 lines, and how much is ceremony?                ~95
#
# THE RULE-6 TIMING, THIRD DOCUMENT. Entry 14 measured jqr 2.8x faster than the
# Python `jq` binding and entry 20 measured 2.5x on a file 4x larger. This one
# is 476 KB — two orders of magnitude smaller than entry 20's — so it tests
# whether the ratio is a per-call overhead or scales with the work.
# ─────────────────────────────────────────────────────────────────────────────

library(jqr)
cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

src <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
jqt <- function(prog) {
  t0 <- Sys.time()
  out <- jq(src, prog)
  list(out = out, secs = as.numeric(difftime(Sys.time(), t0, units = "secs")))
}

cat("\nQ0  jqr parses or errors; jq keeps the LAST duplicate key silently and\n")
cat("    numbers become doubles. Same libjq as the Python binding. PARTLY.\n")

r <- jqt('[paths | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
cat(sprintf("\nQ1  %s distinct paths, %.3fs — the probe says 33\n", r$out, r$secs))
t_paths <- r$secs
r <- jqt('[paths | length] | max')
cat(sprintf("Q2  depth %s — the probe says 5\n", r$out))

cat("\nQ3  jqr counts any candidate and prices none:\n")
for (nm in list(c("an item of results", ".results | length"),
                c("an item of images", "[.results[].images[]] | length"))) {
  x <- jqt(nm[2]); cat(sprintf("    %-22s %6s rows\n", nm[1], x$out))
}
cat("    the probe prices both: 100 x 16 at 0% empty, 1,388 x 11 at 16%.\n")
r <- jqt('{count, page: (.results|length), has_next: (.next != null)}')
cat(sprintf("Q7  %s\n", r$out))

r <- jqt('[.results[] | keys[]] | group_by(.) | map(select(length < 100)) | length')
cat(sprintf("\nQ4  tag keys not on every tag: %s\n", r$out))
r <- jqt('[.results[].images[] | to_entries[] | select(.value == null) | .key]
          | group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)')
cat(sprintf("Q4  image keys written NULL:  %s\n", paste(r$out, collapse = " ")))
r <- jqt('[.results[].images[] | to_entries[] | select(.value == "") | .key]
          | group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)')
cat(sprintf("Q4  image keys written \"\":    %s\n", paste(r$out, collapse = " ")))
cat("    THREE STATES, AND THE PROBE COUNTS TWO. Its 16% on the images table is\n")
cat("    exactly the nulls; the 2,776 empty strings count as FILLED, and\n")
cat("    counting them too would make it 34%.\n")

r <- jqt('
def ptype: if type == "array" then (if length == 0 then "array" else "array[1] " + (.[0]|type) end)
           else type end;
. as $d | [ paths as $p | {k: ($p | map(if type=="number" then "[]" else . end) | join(".")),
                           t: ($d | getpath($p) | ptype)} ]
| group_by(.k) | map({k: .[0].k, t: (map(.t) | unique | map(select(. != "null")))})
| map(select(.t | length > 1)) | length')
cat(sprintf("\nQ5  paths with more than one non-null shape: %s — the probe says NONE\n", r$out))
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")

r <- jqt('[.results[] | {name, full_size, last_updated}] | length')
cat(sprintf("\nQ8  %s rows x 3, %.3fs\n", r$out, r$secs))
r <- jqt('[.results[].images[] | select(.variant != null)] | length')
cat(sprintf("\nQ9  `variant` non-null on %s of 1,388\n", r$out))
r <- jqt('[.results[] as $t | $t.images[] | {tag: $t.name, architecture, os}] | length')
cat(sprintf("\nQ10 images[] -> %s rows x 3, %.3fs, parent kept\n", r$out, r$secs))
r <- jqt('[paths(type=="string" and test("^https?://"))
           | map(if type=="number" then "[]" else . end) | join(".")] | unique')
cat(sprintf("\nQ11 %d URL path: %s\n", length(r$out), paste(r$out, collapse = ", ")))
cat("    the pagination link, outside the records — pandas, polars and DuckDB\n")
cat("    report none of one because they build from `results`.\n")

cat("\nQ12 jqr returns TEXT, so the honest table means handing the output back to\n")
cat("    jsonlite. That round trip is jqr's real cost and shows in no timing here.\n")

cat(sprintf("\n     RULE-6 TIMING, THIRD DOCUMENT: question 1 took %.3fs from jqr.\n", t_paths))
cat("     ../python/try-jq.py prints the same expression's time from the Python\n")
cat("     binding. Entry 14 measured 2.8x and entry 20 2.5x on 29.6 MB; this\n")
cat("     file is 476 KB, so the ratio here says whether the gap is per-call\n")
cat("     overhead or proportional to the work.\n")
