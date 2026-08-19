# jqr — Home Assistant frontend, the English translation catalogue
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
#  measured      2026-08-12
#  run           cd corpus/28-home-assistant-i18n/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             5   NO                  YES — every level
#   2 how deep                                    2   NO                  YES — 11
#   3 what is one record                          6   NO                  names none, counts any
#   4 always present vs sometimes                 4   NO                  yes, once you pick a level
#   5 does any field change type                  4   NO                  YES — 330 mixed objects
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            2   NO                  yes — 8,518
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              2  YES                  yes — null, not an error
#  10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
#  11 find every path matching something          3   NO                  YES
#  12 flattest honest table                       4   NO                  YES — 8,518 x 2
#  13 needed the shape in advance?                    NO for 1,2,4,5,11,12
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          the jq is; the R around it is not
#  16 lines, and how much is ceremony?                ~75
#
# **jqr is jq, so the answers are jq's** — `paths(scalars)` gives the honest
# table and nothing here is new. What IS worth recording is the seam: every
# result arrives as a JSON STRING that R must parse again, so a one-expression
# answer becomes two steps and a `fromJSON`.
#
# **`leaf_paths`, the documented builtin, is not available here either** — same
# as the Python binding. Written out as `paths(scalars)`.

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("jqr %s · jsonlite %s · R %s.%s\n",
            packageVersion("jqr"), packageVersion("jsonlite"),
            R.version$major, R.version$minor))

j <- paste(readLines("../source.json", warn = FALSE), collapse = "")
q <- function(expr) fromJSON(jq(j, expr))

cat("\nQ0  jq parses and says nothing. CANNOT.\n")

top <- q("keys_unsorted")
cat(sprintf("\nQ1  top level, %d: %s\n", length(top), paste(top, collapse = ", ")))
n_paths <- q("[paths] | length")
n_leaf <- q("[paths(scalars)] | length")
cat(sprintf("    [paths] | length          -> %s\n", format(n_paths, big.mark = ",")))
cat(sprintf("    [paths(scalars)] | length -> %s leaves\n",
            format(n_leaf, big.mark = ",")))
cat("    YES, every level, nothing known in advance.\n")

cat(sprintf("\nQ2  [paths | length] | max -> %d. YES.\n", q("[paths|length]|max")))

cat("\nQ3  jqr names no candidates and prices none. It counts any you name:\n")
cat(sprintf("      one message per row   %s\n", format(n_leaf, big.mark = ",")))
cat(sprintf("      one object per row    %s\n",
            format(q('[paths(type=="object")]|length'), big.mark = ",")))
cat(sprintf("      one ui section        %s\n", q(".ui|keys|length")))
cat("    CANNOT for Q3.\n")
cat(sprintf("\nQ7  %s messages. yes.\n", format(n_leaf, big.mark = ",")))

kk <- q('[.ui.panel.config | .. | objects | keys_unsorted] | flatten | group_by(.) | map({(.[0]): length}) | add')
cat(sprintf("\nQ4  keys under ui.panel.config, commonest: %s\n",
            paste(utils::head(names(sort(unlist(kk), decreasing = TRUE)), 4),
                  collapse = ", ")))
cat("    yes, once you have chosen a level to ask about.\n")

mixed <- q('[paths(type=="object") as $p | getpath($p) | to_entries | map(.value|type) | unique | select(length>1)] | length')
cat(sprintf("\nQ5  objects holding BOTH a string and an object: %d\n", mixed))
cat("    YES — the same 330 the Python jq and duckdb report, independently.\n")

cat("\nQ6  CANNOT. No notion of a key being data rather than a name.\n")

cat(sprintf("\nQ8  %s\n", paste(q('[.ui.common.and, .ui.common.loading, .ui.panel.profile.logout]'),
                                collapse = " | ")))
cat(sprintf("\nQ9  a key that is not there -> %s. null, not an error. yes.\n",
            is.null(q(".ui.panel.profile.nope"))))

cat("\nQ10 zero arrays. NOTHING TO FLATTEN.\n")

icu <- q('[paths(scalars) as $p | select(getpath($p)|test("\\\\{")) | $p|join(".")]')
cat(sprintf("\nQ11 messages with an ICU placeholder: %s, e.g. %s. YES.\n",
            format(length(icu), big.mark = ","), icu[1]))

t0 <- Sys.time()
tab <- q('[paths(scalars) as $p | {path: ($p|join(".")), message: getpath($p)}]')
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 2)
cat(sprintf("\nQ12 %s rows x %d cols in %s seconds.\n",
            format(nrow(tab), big.mark = ","), ncol(tab), secs))
print(utils::head(tab, 3))
cat("    NOTHING IS LOST. Same answer as the Python jq, arrived at the same way.\n")

cat("
CONCLUSION. jqr scores exactly as jq does, because it IS jq, and that is the
point worth recording rather than the answers: the fourteen tools are not
fourteen ideas. jq and jqr are one idea reached through two doors, as this
project has said since the first day.

The cost of the R door is the seam. Every result comes back as a JSON string and
has to be `fromJSON`ed before R can use it, so a one-expression answer is two
steps and the types are whatever jsonlite decides. That is why Q15 splits: the jq
is readable a week later and the R wrapped around it is not.

It also confirms the 330 mixed objects independently of the Python binding and of
duckdb — three tools, one number, none of them asked the question.
")
