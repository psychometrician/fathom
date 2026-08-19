# jqr — cargo metadata for this repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.json   27 KB, 8 packages, depth 8
#  measured      2026-08-11
#  run           cd corpus/24-cargo-metadata/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   PARTLY
#   1 what is in here                             2   NO                  yes — 143
#   2 how deep                                    1   NO                  yes — 8
#   3 what is one record                          4   NO                  PARTLY
#   4 always present vs sometimes                 6   NO                  YES — four always-null
#   5 does any field change type                  8   NO                  ZERO, with the rule
#   6 are any object keys data                   10   NO                  the ingredients only
#   7 how many records                             2  NO                  yes
#   8 three named fields to a table                2 YES                 yes
#   9 a field missing from some rows                2 YES                 yes
#  10 flatten the deepest array                     3 YES                 yes
#  11 find every path matching something            3 NO                  yes — 5
#  12 flattest honest table                         3 -                   CANNOT — returns TEXT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 6, 11
#  14 survives the next file unchanged?               YES — jq names no feature
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~85
#
# RULE-6 TIMING, LAST DOCUMENT. 14: 2.8x. 20: 2.5x on 29.6 MB. 22: 2.97x on
# 476 KB. 23: see that entry. This file is 27 KB — the smallest in the corpus —
# so it is the last point on whether the gap is per-call overhead or work.
# ─────────────────────────────────────────────────────────────────────────────

library(jqr)
cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

src <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
jqt <- function(prog) {
  t0 <- Sys.time()
  out <- jq(src, prog)
  list(out = out, secs = as.numeric(difftime(Sys.time(), t0, units = "secs")))
}

cat("\nQ0  jqr parses or errors. jq keeps the LAST duplicate key silently and\n")
cat("    numbers become doubles. Same libjq as the Python binding. PARTLY.\n")

r <- jqt('[paths | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
cat(sprintf("\nQ1  %s distinct paths, %.3fs — the probe says 143\n", r$out, r$secs))
t_paths <- r$secs
r <- jqt('[paths | length] | max')
cat(sprintf("Q2  depth %s — the probe says 8, in 27 KB\n", r$out))
r <- jqt('{packages: (.packages|length), workspace: (.workspace_members|length), nodes: (.resolve.nodes|length)}')
cat(sprintf("\nQ3  jqr counts and prices nothing. CANNOT.\nQ7  %s\n", r$out))

# ── Q6. ─────────────────────────────────────────────────────────────────────
r <- jqt('[.packages[].features | keys[]] | unique | length')
nnames <- as.integer(r$out)
r2 <- jqt('[.packages[].features | keys[]] | length')
r3 <- jqt('[.packages[].features | keys[]] | group_by(.) | map(select(length == 1)) | length')
r4 <- jqt('[.packages[].features | keys[]] | unique | map(select(test("-"))) | length')
cat(sprintf("\nQ6  $.packages[].features — THE PROBE CALLS THESE KEYS DATA.\n"))
cat(sprintf("    %s distinct feature names over %s occurrences; %s appear ONCE\n",
            r$out, r2$out, r3$out))
cat(sprintf("    %s of them contain a HYPHEN\n", r4$out))
cat("    ONE EXPRESSION FOR THE WHOLE VOCABULARY, and no escaping: a jq key is\n")
cat("    a string. jq supplies every ingredient `classify()` judges on — the\n")
cat("    count, the occurrences, the once-only share — and states no verdict.\n")
cat("    COMPARE ../python/try-duckdb.py, where typing the column made every\n")
cat("    package carry all 28 names and 23-appearing-once became 0. jq reads\n")
cat("    the DOCUMENT, so the signal cannot be typed away.\n")

# ── Q4/Q5. ──────────────────────────────────────────────────────────────────
r <- jqt('[.packages[] | keys[]] | group_by(.) | map(select(length < 8)) | length')
cat(sprintf("\nQ4  package fields sometimes ABSENT: %s of 24\n", r$out))
r <- jqt(paste0('[.packages[] | to_entries[] | select(.value == null) | .key]',
                ' | group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)'))
cat(sprintf("Q4  written NULL: %s\n", paste(r$out, collapse = "")))
r <- jqt(paste0('[.packages[] | to_entries[] | select(.value == null) | .key]',
                ' | group_by(.) | map(select(length == 8) | .[0]) | join(", ")'))
cat(sprintf("Q4  NULL ON ALL 8: %s\n", gsub('"', "", r$out)))
CENSUS <- paste0(
  'def ptype: if type == "array" then (if length == 0 then "array"',
  ' else "array[1] " + (.[0]|type) end) else type end;',
  ' def varies: . as $ts | if (any(.[]; startswith("array[")))',
  ' then map(select(. != "array")) else $ts end;',
  ' . as $d | [ paths as $p | {k: ($p | map(if type=="number" then "[]" else . end)',
  ' | join(".")), t: ($d | getpath($p) | ptype)} ]',
  ' | group_by(.k) | map({k: .[0].k, t: (map(.t) | unique',
  ' | map(select(. != "null")) | RULE)}) | map(select(.t | length > 1)) | length')
loose <- jqt(gsub("RULE", ".", CENSUS))
tight <- jqt(gsub("RULE", "varies", CENSUS))
cat(sprintf("\nQ5  a null is not a type, empty arrays still counted: %s paths\n", loose$out))
cat(sprintf("Q5  + AN EMPTY ARRAY IS NOT A TYPE:                    %s paths\n", tight$out))
cat("    ZERO, and the probe says NONE. Everything the loose census flags is an\n")
cat("    optional list that is sometimes empty. ENTRY 20's LADDER ON THE LAST\n")
cat("    DOCUMENT: the rule does all of the work.\n")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
r <- jqt('[.packages[] | {name, version, edition}] | length')
cat(sprintf("\nQ8  %s rows x 3, %.3fs\n", r$out, r$secs))
r <- jqt('[.packages[] | select(.description != null)] | length')
cat(sprintf("\nQ9  `description` non-null on %s of 8\n", r$out))
r <- jqt('[.packages[] as $p | $p.targets[] | {pkg: $p.name, target: .name}] | length')
r2 <- jqt('[.resolve.nodes[] as $n | $n.deps[] | .dep_kinds[] | {node: $n.id, kind}] | length')
cat(sprintf("\nQ10 targets -> %s rows; resolve.nodes[].deps[].dep_kinds[] -> %s rows\n",
            r$out, r2$out))
cat("    at depth 6, and jq reaches BOTH branches with `[]` and no level names.\n")
r <- jqt(paste0('[paths(type=="string" and test("^https?://"))',
                ' | map(if type=="number" then "[]" else . end) | join(".")]',
                ' | unique | .[]'))
cat(sprintf("\nQ11 %d distinct URL paths — same as jq, ijson, glom, pydash and purrr\n",
            length(r$out)))
cat("\nQ12 jqr returns TEXT, so the honest table means handing the output back to\n")
cat("    jsonlite — and on THIS document that is where question 6 goes wrong,\n")
cat("    because jsonlite simplifies `features` into 28 columns. jqr's own\n")
cat("    output survives a `cargo add`; what you do with it next may not.\n")
cat(sprintf("\n     RULE-6 TIMING, LAST DOCUMENT: question 1 took %.3fs from jqr.\n", t_paths))
cat("     ../python/try-jq.py prints the same expression's time. 14: 2.8x,\n")
cat("     20: 2.5x on 29.6 MB, 22: 2.97x on 476 KB, and this is 27 KB.\n")
