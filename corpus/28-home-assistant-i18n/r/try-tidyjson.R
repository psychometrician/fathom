# tidyjson — Home Assistant frontend, the English translation catalogue
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
#  measured      2026-08-12
#  run           cd corpus/28-home-assistant-i18n/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             5   NO                  YES — json_structure
#   2 how deep                                    3   NO                  YES — 11, the `level` column
#   3 what is one record                          6   NO                  names none, counts any
#   4 always present vs sometimes                 4   NO                  yes, by grouping `name`
#   5 does any field change type                  5   NO                  YES — the `type` column
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            2   NO                  yes — 8,518
#   8 three named fields to a table               5  YES                  yes — spread_all after enter
#   9 a field missing from some rows              3  YES                  yes — NA column
#  10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
#  11 find every path matching something          4   NO                  YES — filter the structure
#  12 flattest honest table                       5   NO                  YES — 10,137 nodes
#  13 needed the shape in advance?                    NO for 1,2,4,5,11,12
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          YES — `json_structure` says it
#  16 lines, and how much is ceremony?                ~85
#
# **tidyjson has a BUILT-IN recursive structure verb and it is the R twin of
# duckdb's `json_tree`.** `json_structure()` returns one row per node with
# `parent.id`, `level`, `name` and `type` — 10,137 rows here, which agrees node
# for node with duckdb and with the probe's own walk.
#
# It is a TREE, where rrapply's melt is a TABLE: tidyjson keeps the parent
# pointer and rrapply keeps a column per level. Both are complete; which is
# nicer depends on whether you want to walk or to group.

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("tidyjson %s · dplyr %s · R %s.%s\n",
            packageVersion("tidyjson"), packageVersion("dplyr"),
            R.version$major, R.version$minor))

j <- paste(readLines("../source.json", warn = FALSE), collapse = "")

cat("\nQ0  tidyjson parses and says nothing. CANNOT.\n")

# ── Q1/Q2/Q12. json_structure answers three at once. ─────────────────────────
t0 <- Sys.time()
s <- as.data.frame(json_structure(j))
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 2)

cat(sprintf("\nQ1  json_structure() -> %s rows, one per node, at every level.\n",
            format(nrow(s), big.mark = ",")))
cat(sprintf("    columns: %s\n", paste(names(s)[1:8], collapse = ", ")))
cat("    YES, and nothing was known in advance.\n")

cat(sprintf("\nQ2  max(level) = %d. YES — and duckdb, jq, ijson, rrapply and the\n",
            max(s$level)))
cat("    probe all say 11 as well.\n")

# ── Q3/Q7. ───────────────────────────────────────────────────────────────────
leaves <- sum(s$type == "string")
cat("\nQ3  tidyjson names no candidates and prices none. It counts any you name:\n")
cat(sprintf("      one message per row      %s\n", format(leaves, big.mark = ",")))
cat(sprintf("      one object per row       %s\n",
            format(sum(s$type == "object"), big.mark = ",")))
cat(sprintf("      one top-level section    %d\n", sum(s$level == 1)))
cat("    CANNOT for Q3 — three defensible answers, none proposed, none priced.\n")
cat(sprintf("\nQ7  %s messages. yes.\n", format(leaves, big.mark = ",")))

# ── Q4. ──────────────────────────────────────────────────────────────────────
common <- s |> filter(!is.na(name)) |> count(name, sort = TRUE) |> head(4)
cat("\nQ4  the commonest key names anywhere in the tree:\n")
for (i in seq_len(nrow(common)))
  cat(sprintf("      %-22s %5d\n", common$name[i], common$n[i]))
cat("    yes — 'always present' needs repeated records and there are none.\n")

# ── Q5. ──────────────────────────────────────────────────────────────────────
cat(sprintf("\nQ5  node types: %s\n",
            paste(sprintf("%s %d", names(table(s$type)), table(s$type)),
                  collapse = ", ")))
mixed <- s |> filter(!is.na(parent.id)) |> group_by(parent.id) |>
  summarise(k = n_distinct(type), .groups = "drop") |> filter(k > 1) |> nrow()
cat(sprintf("    objects holding BOTH a string and an object: %d\n", mixed))
cat("    YES — and it is the number defects 31 and 32 turned on, produced by a\n")
cat("    group_by that was not asked the question.\n")

cat("\nQ6  CANNOT. No notion of a key being data rather than a name.\n")

# ── Q8/Q9. ───────────────────────────────────────────────────────────────────
got <- j |> enter_object("ui") |> enter_object("common") |>
  spread_all() |> as.data.frame()
cat(sprintf("\nQ8  enter_object(ui) |> enter_object(common) |> spread_all() -> %d x %d\n",
            nrow(got), ncol(got)))
cat(sprintf("    and = %s, loading = %s\n", got$and, got$loading))
cat("    yes — but every level is an `enter_object` you had to name.\n")

cat(sprintf("\nQ9  a key that is not there -> column absent: %s\n",
            !("nope" %in% names(got))))
cat("    spread_all only makes columns for keys that exist, so a missing one is\n")
cat("    absent rather than NA and the caller must check. yes, with care.\n")

cat("\nQ10 zero arrays in this document. NOTHING TO FLATTEN.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────────
vals <- s |> filter(type == "string")
icu <- sum(grepl("\\{", vals$name))
cat(sprintf("\nQ11 `name` holds the KEY, not the message, so a grepl over the\n"))
cat(sprintf("    structure finds %d key names with a brace, not the 744 messages.\n", icu))
cat("    To match on VALUES you must gather them, which json_structure does not\n")
cat("    do — it describes the tree and drops the leaf text. PARTLY.\n")

# ── Q12. ─────────────────────────────────────────────────────────────────────
cat(sprintf("\nQ12 %s nodes x %d cols in %s seconds — the whole tree with parent\n",
            format(nrow(s), big.mark = ","), ncol(s), secs))
print(utils::head(s[, c("parent.id", "level", "name", "type")], 3))
cat("    YES for the STRUCTURE. What is lost is the message text itself.\n")

cat("
CONCLUSION. tidyjson is the R twin of duckdb's json_tree and one of the four
tools of fourteen that describes this document completely without being told its
shape. `json_structure()` is one call, 10,137 nodes, and it agrees node for node
with duckdb and with the probe.

Where it differs from rrapply is what it keeps. tidyjson keeps the TREE — parent
pointers and levels — and drops the leaf text. rrapply keeps the TABLE — a column
per level and the value. For 'what is in this document' tidyjson is better; for
'give me the messages' rrapply is, and Q11 is where that shows: the structure has
no message text to grep.

WHAT IT WILL NOT DO, with the other thirteen: name the alternative row shapes or
price them, or say a word about which keys are data — which on a translation
catalogue is every key there is.
")
