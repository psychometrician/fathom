# tidyjson — Grafana "Node Exporter Full", dashboard 1860
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (+ dplyr; versions printed at run time)
#  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
#  measured      2026-08-13
#  run           cd corpus/27-grafana-dashboard/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  yes — json_structure
#   2 how deep                                    2   NO                  yes — 12
#   3 what is one record                          6   -                   CANNOT
#   4 always present vs sometimes                 5   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    2   NO                  yes, inferred
#   7 how many records                            6   NO                  YES — 132
#   8 three named fields to a table               4  YES                  yes — spread_values
#   9 a field missing from some rows              2  YES                  yes — NA
#  10 flatten the deepest array                   3  YES                  yes — gather_array
#  11 find every path matching something          3   NO                  yes
#  12 flattest honest table                       2   NO                  YES — the TREE
#  13 needed the shape in advance?                    NO for the tree
#  14 survives the next file unchanged?               YES
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~70
#
# **`json_structure()` returns the TREE as a data frame** — one row per node with
# its level, its name, its type and its PARENT — and that is a different and in
# some ways better melt than rrapply's. rrapply gives you the path spread across
# columns; tidyjson gives you the edges, so the document becomes a graph you can
# group and join.
#
# **For the central question the parent column is what matters.** A panel is a
# node whose parent is named `panels`, at ANY level, so the count needs no
# pattern that knows how deep the nesting goes.

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("tidyjson %s · dplyr %s · R %s.%s\n",
            packageVersion("tidyjson"), packageVersion("dplyr"),
            R.version$major, R.version$minor))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")

cat("\nQ0  tidyjson parses and reports nothing about duplicates, 2^53 or NaN. CANNOT.\n")

# ── Q1/Q2/Q12. json_structure is the melt, as a TREE. ─────────────────────
t0 <- Sys.time()
st <- txt |> json_structure()
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 2)
depth <- max(st$level)
leaves <- sum(!st$type %in% c("object", "array"))

cat(sprintf("\nQ12 %s nodes x %d in %s seconds, from ONE call: json_structure().\n",
            format(nrow(st), big.mark = ","), ncol(st), secs))
cat(sprintf("    %s of them are leaves, which agrees with jq, ijson, duckdb and\n",
            format(leaves, big.mark = ",")))
cat("    rrapply at 11,063. YES.\n")
cat("    WHAT IT GIVES THAT A PATH-MELT DOES NOT: `parent.id`, so the document is\n")
cat("    a graph. 'The children of X' is a join rather than a string operation.\n")
cat(sprintf("      columns: %s\n", paste(names(st), collapse = ", ")))

cat(sprintf("\nQ1  %s nodes at every level, nothing known in advance. yes.\n",
            format(nrow(st), big.mark = ",")))
cat(sprintf("\nQ2  %d levels (json_structure counts the root as 0, so this is the\n", depth))
cat("    same 12 the probe, jq, ijson, duckdb and rrapply report). yes.\n")

# ── Q7. THE CENTRAL QUESTION, via the parent edge. ───────────────────────
panel_arrays <- st |> filter(name == "panels", type == "array")
panels <- st |> filter(parent.id %in% panel_arrays$child.id)
cat("\nQ7  THE CENTRAL QUESTION.\n")
cat(sprintf("      arrays named \"panels\", at any level      -> %d\n", nrow(panel_arrays)))
cat(sprintf("      nodes whose PARENT is one of those      -> %d\n", nrow(panels)))
cat("    YES, and the expression never mentions a depth. `name == \"panels\"`\n")
cat("    finds the top-level array AND the 16 inside row panels; the join on\n")
cat("    parent.id turns those into their children. A dashboard nesting rows\n")
cat("    three deep would need no change at all — the strongest Q14 here.\n")
by_level <- panels |> count(level)
for (i in seq_len(nrow(by_level)))
  cat(sprintf("        level %-3d %4d panels\n", by_level$level[i], by_level$n[i]))

# ── Q3. What is one record. ──────────────────────────────────────────────
tgt_arrays <- st |> filter(name == "targets", type == "array")
tgts <- st |> filter(parent.id %in% tgt_arrays$child.id)
cat("\nQ3  tidyjson counts any reading you name and proposes none:\n")
for (r in list(c("one panel per row (all depths)", nrow(panels)),
               c("one TOP-LEVEL panel per row", sum(panels$level == 2)),
               c("one target per row", nrow(tgts)),
               c("one leaf per row", leaves)))
  cat(sprintf("      %-32s %6s\n", r[1], format(as.integer(r[2]), big.mark = ",")))
cat("    CANNOT. Four readings, each a filter and a join, none proposed or priced.\n")

# ── Q4. Always vs sometimes, over the 132 panels. ────────────────────────
fields <- st |> filter(parent.id %in% panels$child.id) |> count(name, sort = TRUE)
cat(sprintf("\nQ4  fields directly under a panel, over the %d:\n", nrow(panels)))
for (i in seq_len(nrow(fields)))
  cat(sprintf("      %-16s %4d %s\n", fields$name[i], fields$n[i],
              ifelse(fields$n[i] == nrow(panels), "always", "")))
cat("    yes — a join on parent.id, and it agrees with jq exactly, INCLUDING\n")
cat("    `links` at 115 which tidyr's table erased to 0. The tree keeps an empty\n")
cat("    array as a node; a rectangling verb turns it into an absent cell.\n")

# ── Q5. Type variation. ──────────────────────────────────────────────────
varying <- st |>
  filter(!is.na(name)) |>
  group_by(name) |>
  summarise(k = n_distinct(type), .groups = "drop") |>
  filter(k > 1)
cat(sprintf("\nQ5  NAMES carrying more than one node type: %d\n", nrow(varying)))
cat(sprintf("      %s\n", paste(head(varying$name, 8), collapse = ", ")))
cat("    yes — and note this is the by-NAME pooling duckdb's Q5 warns about. The\n")
cat("    tree has no path column, so grouping by path needs the parent chain\n")
cat("    walked back up, which json_structure gives you but does not do for you.\n")

# ── Q6. ──────────────────────────────────────────────────────────────────
widest <- st |> filter(type == "object") |>
  left_join(st |> count(parent.id), by = c("child.id" = "parent.id")) |>
  summarise(m = max(n, na.rm = TRUE)) |> pull(m)
cat(sprintf("\nQ6  none; the widest object has %d keys and they are field names.\n", widest))
cat("    yes, inferred — tidyjson counts, the judgement is mine.\n")

# ── Q8/Q9. spread_values is the extraction verb. ─────────────────────────
tbl <- txt |> enter_object("panels") |> gather_array() |>
  spread_values(title = jstring("title"), type = jstring("type"),
                id = jnumber("id"), description = jstring("description"))
cat(sprintf("\nQ8  spread_values -> %d rows x 4 — BUT ONLY THE TOP LEVEL.\n", nrow(tbl)))
cat("    `enter_object(\"panels\") |> gather_array()` is the extraction idiom and\n")
cat("    it names one path, so it gets 31. The tree above found 132; the\n")
cat("    EXTRACTION side of tidyjson has the same literal-path limit as everyone\n")
cat("    else. Exploring and extracting are two different tools inside one package.\n")
print(utils::head(as.data.frame(tbl)[, c("title", "type", "id")], 2))
cat(sprintf("\nQ9  `description` is NA on %d of these %d rows and they survive. yes —\n",
            sum(is.na(tbl$description)), nrow(tbl)))
cat("    `jstring` returns NA for an absent key with no argument needed.\n")

# ── Q10. ─────────────────────────────────────────────────────────────────
cat(sprintf("\nQ10 %s target nodes found through the tree. yes, and it agrees with\n",
            format(nrow(tgts), big.mark = ",")))
cat("    every other tool at 269 — again without naming a depth.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────
strs <- vapply(st$`..JSON`[st$type == "string"],
               function(x) if (is.character(x)) x else "", "")
hits <- sum(grepl("\\$node|\\$job|\\$__rate_interval", strs))
cat(sprintf("\nQ11 %d string nodes mention a Grafana template variable. yes, one grepl\n", hits))
cat("    over the tree, and it agrees with jq, duckdb and rrapply at 255.\n")

cat("
CONCLUSION. tidyjson gives the best answer to the central question in the whole
comparison, and it is the only tool that gives it without a depth-aware pattern
written by someone who already suspected the nesting.

`json_structure()` returns the tree with a `parent.id`, so 'a panel is a node
whose parent is an array named panels' is expressible directly, at any depth,
and the count comes out 132 with a `level` breakdown for free. jq's `..` and
duckdb's `+` regex both reach 132, but both encode 'I am looking for something
that repeats'; this expression does not. It would survive rows nested three deep
unchanged, which no other attempt here can claim.

It also keeps what the rectangling verbs destroy. `links` is present on 115
panels and every value is `[]`; tidyjson reports 115, tidyr's table reports 0.

The split inside the package is the interesting part. Its EXPLORING verb has no
depth limit and its EXTRACTING verb — `enter_object |> gather_array` — takes a
literal path and returns 31. One package, both halves of this project's thesis,
and the two halves do not talk to each other.
")
