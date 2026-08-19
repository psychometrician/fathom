# tidyr — Grafana "Node Exporter Full", dashboard 1860
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite, dplyr; versions printed at run time)
#  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
#  measured      2026-08-13
#  run           cd corpus/27-grafana-dashboard/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  yes — unnest_wider
#   2 how deep                                    -   -                   CANNOT
#   3 what is one record                          5   -                   CANNOT
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  PARTLY
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            8  YES                  31 FIRST, 132 after
#   8 three named fields to a table               3  YES                  yes — hoist
#   9 a field missing from some rows              2  YES                  yes — NULL becomes NA
#  10 flatten the deepest array                   4  YES                  yes — unnest_longer
#  11 find every path matching something          -   -                   CANNOT
#  12 flattest honest table                       -   -                   CANNOT
#  13 needed the shape in advance?                    YES — every unnest names a column
#  14 survives the next file unchanged?               NO
#  15 readable a week later?                          YES — the verbs are plain
#  16 lines, and how much is ceremony?                ~65
#
# **tidyr is the closest prior art fathom has in either language** — `hoist`,
# `unnest_wider` and `unnest_longer` are the tidyverse's answer to nested JSON
# and the nearest thing to `rows()` and `take()` that exists. `CLAUDE.md` says
# so, which is why this file matters more than most.
#
# **And this is the document where that resemblance runs out.** The rectangling
# verbs are excellent at flattening a level you NAME. The central question here
# is which levels exist, and every verb tidyr has takes that as an argument.

suppressMessages({library(jsonlite); library(tidyr); library(dplyr); library(tibble)})
cat(sprintf("jsonlite %s · tidyr %s · dplyr %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("tidyr"),
            packageVersion("dplyr"), R.version$major, R.version$minor))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

# ── Q7. THE CENTRAL QUESTION, and the naive answer comes first. ───────────
top <- tibble(p = doc$panels) |> unnest_wider(p)
cat("\nQ7  THE CENTRAL QUESTION.\n")
cat(sprintf("      tibble(p = doc$panels) |> unnest_wider(p)      -> %d rows\n", nrow(top)))
cat("    THAT IS THE OBVIOUS CALL AND IT IS THE WRONG ANSWER. It is one verb,\n")
cat("    it produces a tidy tibble with real column names, and nothing about it\n")
cat("    suggests three quarters of the panels are missing.\n")

# Reaching the rest needs a SECOND unnest, on a column you must know exists.
nested <- top |>
  filter(!vapply(panels, is.null, logical(1))) |>
  select(panels) |>
  unnest_longer(panels) |>
  unnest_wider(panels, names_sep = "_")
cat(sprintf("\n      |> unnest_longer(panels) |> unnest_wider(panels)  -> %d rows\n",
            nrow(nested)))
cat(sprintf("      the sum, written by hand                          -> %d\n",
            nrow(top) + nrow(nested)))
cat("    132, after naming `panels` a second time. tidyr has no verb that asks\n")
cat("    'which columns are still nested' and no way to repeat until nothing is.\n")
cat("    `unnest_auto` guesses between longer and wider for ONE column you name;\n")
cat("    it does not find the columns.\n")

# ── Q1. What is in here. ──────────────────────────────────────────────────
cat(sprintf("\nQ1  unnest_wider gives %d columns at the panel level:\n", ncol(top)))
cat(sprintf("      %s\n", paste(head(names(top), 9), collapse = ", ")))
cat("    yes for one level, and this is genuinely good — `unnest_wider` IS the\n")
cat("    'what fields are here' verb. It just needs to be pointed at a level.\n")

# ── Q2. How deep. ─────────────────────────────────────────────────────────
cat("\nQ2  CANNOT. Depth is not a question tidyr can be asked; you discover it by\n")
cat("    unnesting until nothing is left, counting the calls yourself.\n")

# ── Q3. What is one record. ──────────────────────────────────────────────
panels <- c(doc$panels, unlist(lapply(doc$panels, `[[`, "panels"), recursive = FALSE))
tg <- unlist(lapply(panels, `[[`, "targets"), recursive = FALSE)
cat("\nQ3  CANNOT — nothing proposed, nothing priced:\n")
for (r in list(c("one panel per row (all depths)", length(panels)),
               c("one TOP-LEVEL panel per row", nrow(top)),
               c("one target per row", length(tg)),
               c("one template variable per row", length(doc$templating$list))))
  cat(sprintf("      %-32s %6s\n", r[1], format(as.integer(r[2]), big.mark = ",")))

# ── Q4. Always vs sometimes. ─────────────────────────────────────────────
all_p <- tibble(p = panels) |> unnest_wider(p)
# An absent field arrives as NA in an atomic column and as NULL in a list
# column, so both have to be tested. A first draft checked only is.null and
# reported every field as always-present, which is a confidently wrong answer.
present <- vapply(all_p, function(col) {
  if (is.list(col)) sum(!vapply(col, is.null, logical(1)))
  else sum(!is.na(col))
}, 0L)
present <- sort(present, decreasing = TRUE)
cat(sprintf("\nQ4  over the %d panels, present counts:\n", nrow(all_p)))
for (i in seq_len(length(present)))
  cat(sprintf("      %-16s %4d %s\n", names(present)[i], present[i],
              ifelse(present[i] == nrow(all_p), "always", "")))
cat("    yes, and the six always-present fields agree with jq and ijson.\n")
cat("    ⚠ TWO THINGS ARE ERASED BY THE VERB THAT MAKES THE TABLE.\n")
cat("      `unnest_wider` materialises a column for every field ANY panel has,\n")
cat("      so an absent field becomes NA or NULL — the same cell a present-and-\n")
cat("      null field gets. That is the polars failure in another language.\n")
cat("      Second, AN EMPTY ARRAY IS STORED AS NULL, so `[]` and 'no such key'\n")
cat("      become the same cell. Two consequences visible above:\n")
cat(sprintf("        `panels` reads %d, and 16 panels have the key — two hold `[]`\n",
            present[["panels"]]))
cat(sprintf("        `links`  reads %d, and 115 panels have the key — ALL of them\n",
            present[["links"]]))
cat("                 hold `[]`, so the field vanishes from the table completely\n")
cat("      jq reports links on 115 of 132. This table says nothing has links at\n")
cat("      all. That is not a rounding difference; it is a field disappearing.\n")

# ── Q5. Type variation. ──────────────────────────────────────────────────
kinds <- vapply(all_p, function(col) {
  cl <- unique(vapply(col[!vapply(col, is.null, logical(1))],
                      function(x) class(x)[1], ""))
  length(cl)
}, 0L)
cat(sprintf("\nQ5  columns holding more than one class: %d\n", sum(kinds > 1)))
if (any(kinds > 1)) cat(sprintf("      %s\n", paste(names(kinds)[kinds > 1], collapse = ", ")))
cat("    PARTLY. This looks only at the panel level because that is the level\n")
cat("    unnested; the real variation in this document is five levels deeper, at\n")
cat("    `fieldConfig.overrides[].properties[].value`, and no tidyr verb goes\n")
cat("    looking. jq, ijson, duckdb and rrapply all found it without being asked.\n")

# ── Q6. ──────────────────────────────────────────────────────────────────
cat("\nQ6  CANNOT. `unnest_wider` turns keys into columns unconditionally.\n")

# ── Q8/Q9. hoist is the right verb and it is very good. ──────────────────
tbl <- tibble(p = panels) |>
  hoist(p, title = "title", type = "type", id = "id", description = "description") |>
  select(-p)
cat(sprintf("\nQ8  hoist -> %d rows x %d. YES, and `hoist` is the best-named verb in\n",
            nrow(tbl), ncol(tbl)))
cat("    this comparison: it says take these fields out of that nested thing,\n")
cat("    and it reads back perfectly in a week. It is prior art for `take`.\n")
print(utils::head(tbl[, c("title", "type", "id")], 2))
desc_missing <- if (is.list(tbl$description))
  sum(vapply(tbl$description, is.null, logical(1))) else sum(is.na(tbl$description))
cat(sprintf("\nQ9  `description` is missing on %d of %d rows and they survive. yes,\n",
            desc_missing, nrow(tbl)))
cat("    `hoist` fills an absent field with NULL and keeps the row, which is the\n")
cat("    correct behaviour and needs no argument.\n")

# ── Q10. Flatten the deepest array. ──────────────────────────────────────
tg_tbl <- tibble(p = panels) |>
  hoist(p, targets = "targets") |>
  select(targets) |>
  unnest_longer(targets)
cat(sprintf("\nQ10 unnest_longer(targets) -> %d rows. yes, and it agrees with every\n",
            nrow(tg_tbl)))
cat("    other tool at 269. `unnest_longer` is exactly right for a level you name.\n")

# ── Q11/Q12. ─────────────────────────────────────────────────────────────
cat("\nQ11 CANNOT. No path enumeration and no value search; a grep would need\n")
cat("    every column named, and naming them is the question.\n")
cat("\nQ12 CANNOT ON THIS DOCUMENT, and entry 28 scored it PARTLY in eleven calls.\n")
cat("    The difference is that entry 28's catalogue was uniform, so eleven\n")
cat("    identical `unnest_longer` calls reached the bottom. Here the columns\n")
cat("    differ by panel type and the levels are not uniform, so there is no\n")
cat("    finite sequence of named unnests that flattens the document.\n")

cat("
CONCLUSION. tidyr is the closest thing to fathom's `rows()` that exists, and
this document is where the resemblance stops.

`hoist` is the best verb in the comparison for Q8 — it is `take`, already
shipped, in R — and `unnest_longer` is exactly right for Q10. Both take the path
as an argument. That is the whole finding: tidyr's rectangling verbs are superb
at flattening a level you can name, and this document's question is which levels
exist.

The naive call is the damaging one. `unnest_wider` on `doc$panels` gives 31 tidy
rows in a single verb, and it is wrong. Reaching 132 needs a second unnest on a
column that 15 of the 31 rows do not have, plus a filter, plus an addition —
and, before any of it, knowing that a `row` panel nests its own `panels`.

One structural cost worth recording next to polars': `unnest_wider` materialises
a column for every field ANY panel carries, so an absent field becomes a NULL
cell indistinguishable from a present one. The ragged edge this project measures
is erased by the verb that makes the table.
")
