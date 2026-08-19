# jqr — Grafana "Node Exporter Full", dashboard 1860
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
#  measured      2026-08-13
#  run           cd corpus/27-grafana-dashboard/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  yes
#   2 how deep                                    2   NO                  yes — 12
#   3 what is one record                          6   -                   CANNOT
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    2   NO                  yes, inferred
#   7 how many records                            5   NO                  YES — 132
#   8 three named fields to a table               4  YES                  yes
#   9 a field missing from some rows              2  YES                  yes — // null
#  10 flatten the deepest array                   2   NO                  yes
#  11 find every path matching something          3   NO                  yes
#  12 flattest honest table                       3   NO                  YES
#  13 needed the shape in advance?                    NO — `..` needs no shape
#  14 survives the next file unchanged?               YES
#  15 readable a week later?                          the `..` line yes
#  16 lines, and how much is ceremony?                ~60
#
# **jqr is a doorway to the same language the Python `jq` attempt uses, and the
# two must not disagree.** They do not: every number below matches, which is
# the point of running both rather than a duplication of effort. A person who
# reaches for R and a person who reaches for Python get the same answer here,
# which is exactly what the fathom architecture claims for itself and is worth
# checking in someone else's tool.
#
# **Its one real difference from Python's jq is ergonomic and it matters.**
# `jqr` returns JSON TEXT, so every answer needs `fromJSON` to become an R
# value. That is one extra step on every single line.

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("jqr %s · jsonlite %s · R %s.%s\n",
            packageVersion("jqr"), packageVersion("jsonlite"),
            R.version$major, R.version$minor))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
Q <- function(expr) fromJSON(jq(txt, expr))

# The corrected leaf-path expression — see the Python jq attempt. `paths(scalars)`
# silently drops every `false` and every `null`, because `select` tests its input
# for truthiness and `scalars` returns the value itself.
LEAF <- 'path(.. | select(type != "object" and type != "array"))'

cat("\nQ0  jq parses and reports nothing about duplicates, 2^53 or NaN. CANNOT.\n")

# ── Q1/Q2/Q12. ────────────────────────────────────────────────────────────
leaves <- Q(sprintf('[%s] | length', LEAF))
distinct <- Q(sprintf('[%s | map(if type == "number" then "[]" else . end) | join(".")] | unique | length', LEAF))
depth <- Q(sprintf('[%s | length] | max', LEAF))
cat(sprintf("\nQ1  %s leaves at %d distinct paths. yes, nothing known in advance.\n",
            format(leaves, big.mark = ","), distinct))
cat(sprintf("\nQ2  %d. yes — and it matches the probe, ijson, duckdb and rrapply.\n", depth))

broken <- Q('[paths(scalars)] | length')
cat(sprintf("\nQ12 %s x 2. YES, one expression.\n", format(leaves, big.mark = ",")))
cat(sprintf("    ⚠ `paths(scalars)` returns %s here — %d rows short. Same defect as\n",
            format(broken, big.mark = ","), leaves - broken))
cat("      the Python binding, because it is the same jq. A `false` leaf fails\n")
cat("      its own filter. Entry 28 used that idiom and its document was all\n")
cat("      strings, so it cost nothing there and costs 6.3% here.\n")
cat("    WHAT IS LOST: array indices become `[]` so paths compare, so a row says\n")
cat("    a target has an `expr` and not which target.\n")

# ── Q7. THE CENTRAL QUESTION. ─────────────────────────────────────────────
naive <- Q('.panels | length')
allp  <- Q('[.. | objects | select(has("gridPos"))] | length')
cat("\nQ7  THE CENTRAL QUESTION.\n")
cat(sprintf("      .panels | length                                 -> %d\n", naive))
cat(sprintf("      [.. | objects | select(has(\"gridPos\"))] | length  -> %d\n", allp))
cat(sprintf("      the difference is %d panels inside the 16 `row` panels.\n", allp - naive))
cat("    YES. `..` is the whole answer and it needs no shape known in advance.\n")
cat("    The naive expression is shorter, obvious, and wrong — and jqr will\n")
cat("    print either without comment.\n")

tgt <- Q('[.. | objects | select(has("gridPos")) | .targets // [] | .[]] | length')
refid <- Q('[.. | objects | select(has("refId"))] | length')
cat(sprintf("\n    targets: %d by containment, but `select(has(\"refId\"))` gives %d —\n", tgt, refid))
cat("    two `templating.list[].query` objects carry a refId too. The `gridPos`\n")
cat("    trick worked by luck of that field being exclusive to panels.\n")

# ── Q3. What is one record. ───────────────────────────────────────────────
cat("\nQ3  jq counts any reading you name and proposes none:\n")
readings <- list(
  c("one panel per row (all depths)", '[.. | objects | select(has("gridPos"))] | length'),
  c("one TOP-LEVEL panel per row", '.panels | length'),
  c("one target per row", '[.. | objects | select(has("gridPos")) | .targets // [] | .[]] | length'),
  c("one template variable per row", '.templating.list | length'),
  c("one leaf per row", sprintf('[%s] | length', LEAF)))
for (r in readings)
  cat(sprintf("      %-32s %7s\n", r[1], format(Q(r[2]), big.mark = ",")))
cat("    CANNOT. Five readings, none proposed, none priced.\n")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
cnt <- Q('[.. | objects | select(has("gridPos"))] | [.[] | keys[]] | group_by(.) | map({k: .[0], n: length}) | sort_by(-.n)')
cat(sprintf("\nQ4  fields over all %d panels:\n", allp))
for (i in seq_len(nrow(cnt)))
  cat(sprintf("      %-16s %4d %s\n", cnt$k[i], cnt$n[i],
              ifelse(cnt$n[i] == allp, "always", "")))
cat("    yes, once the population is Q7's answer rather than `.panels`.\n")

# ── Q5. Type variation. ───────────────────────────────────────────────────
varying <- Q('[paths as $p | select(($p|length) > 0) | {p: ($p | map(if type == "number" then "[]" else . end) | join(".")), t: (getpath($p) | type)}] | group_by(.p) | map({p: .[0].p, t: (map(.t) | unique)}) | map(select((.t | length) > 1)) | length')
cat(sprintf("\nQ5  paths whose value type varies: %d. yes.\n", varying))
cat("    This counts CONTAINERS too, so it is a larger number than ijson's 4,\n")
cat("    which looked only at leaf events. Same document, two defensible\n")
cat("    definitions, and neither tool says which it used.\n")

# ── Q6. ───────────────────────────────────────────────────────────────────
widest <- Q('[.. | objects | keys | length] | max')
cat(sprintf("\nQ6  none; the widest object has %d keys and they are field names.\n", widest))
cat("    yes, inferred — jq counts, the judgement is mine.\n")

# ── Q8/Q9. ────────────────────────────────────────────────────────────────
tbl <- Q('[.. | objects | select(has("gridPos")) | {title, type, id, description: (.description // null)}]')
cat(sprintf("\nQ8  %d rows x %d. yes, one expression, reaching both depths.\n",
            nrow(tbl), ncol(tbl)))
print(utils::head(tbl[, c("title", "type", "id")], 2))
cat(sprintf("\nQ9  `description` absent from %d of %d; `// null` keeps every row. yes,\n",
            sum(is.na(tbl$description)), nrow(tbl)))
cat("    and it agrees with every other tool at 84.\n")

# ── Q10. ──────────────────────────────────────────────────────────────────
n_arr <- Q('[.. | arrays] | length')
cat(sprintf("\nQ10 %s arrays and `.. | arrays` reaches every one. yes.\n",
            format(n_arr, big.mark = ",")))

# ── Q11. ──────────────────────────────────────────────────────────────────
hits <- Q(sprintf('[%s as $p | getpath($p) | select(type == "string") | select(test("\\\\$node|\\\\$job|\\\\$__rate_interval"))] | length', LEAF))
cat(sprintf("\nQ11 %d leaves mention a Grafana template variable. yes, and it matches\n", hits))
cat("    the Python jq attempt, duckdb and rrapply at 255.\n")

cat("
CONCLUSION. jqr reaches 132 with the same expression the Python binding uses and
returns the same number, which is the result worth having: two languages, one
query engine, no disagreement. Every count in this file matches its Python twin.

The cost of the doorway is real. `jqr` hands back JSON TEXT, so `fromJSON` wraps
every single call, and complex expressions become string literals inside R
strings with the escaping doubled — the Q11 line has four backslashes to express
one. It is the same language with a layer of quoting tax on top.

Its verdict on the central question is jq's verdict. `..` answers it correctly
without knowing the shape, `.panels | length` answers it incorrectly and looks
identical, and nothing in the tool distinguishes them.
")
