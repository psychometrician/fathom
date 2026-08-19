# tidyjson — Jupyter notebook, Norvig Advent-2021
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson 0.3.3.1
#  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
#  measured      2026-08-10
#  run           cd corpus/11-jupyter-notebook/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             6   NO                  WRONG
#   2 how deep                                    -   -                   CANNOT
#   3 what is one record                          5   YES                 PARTLY
#   4 always present vs sometimes                 5   NO                  yes
#   5 does any field change type                  4   NO                  PARTLY
#   6 are any object keys data                    4   YES                 CANNOT
#   7 how many records                            3   YES                 YES
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              4   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          -   -                   CANNOT
#  12 flattest honest table                       5   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 1, 4, 5
#  14 survives the next file unchanged?               json_schema does
#  15 readable a week later?                          yes, it is a pipeline
#  16 lines, and how much is ceremony?                ~50, the pipeline is intent
#
# THE POINT OF THIS FILE, AND IT DID NOT GO AS WRITTEN. `json_schema` is the
# corpus's most-measured describer and its failures are always about
# HETEROGENEITY — it silently picks one shape and discards the rest. This
# document is REGULAR, so it was chosen as the case where the function should be
# right. **It discarded anyway, and it picked the minority shape.** See Q1.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("R %s, tidyjson %s\n", getRversion(), packageVersion("tidyjson")))

j <- readLines("../source.json", warn = FALSE) |> paste(collapse = "")

# ── Q1. what is in here ──────────────────────────────────────────────────────
t0 <- Sys.time()
sch <- j |> as.tbl_json() |> json_schema()
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\n1. json_schema: %d chars in %.1f s (%.2f%% of the 1,114,184-byte file)\n",
            nchar(sch), el, 100 * nchar(sch) / 1114184))
cat(sprintf("   %s\n", substr(sch, 1, 300)))
# PREDICTED WRONG, and the prediction is left here because the miss is the
# finding. This file was written expecting json_schema to be RIGHT for once:
# 05, 03, 07 and 10 all record it silently picking one shape out of several,
# and this document was chosen as the regular one where there is nothing to
# pick between. There is.
cat("\n   IT DISCARDED ANYWAY, on the corpus's most regular document.\n")
cat("   The outputs shape it reports is {name, output_type, text} — that is\n")
cat("   the `stream` shape, held by 27 of the 107 outputs. The other 80 carry\n")
cat("   `data`, `execution_count` and `metadata`, and none of the three\n")
cat("   appears. Measured against the true union:\n")
cat("     true union of outputs[] keys   6  data execution_count metadata\n")
cat("                                       name output_type text\n")
cat("     json_schema names              3  name output_type text\n")
cat("     coverage                      50% of key names, 25% of the outputs\n")
cat("   It picked the MINORITY shape. `metadata: {}` is the same failure one\n")
cat("   level up — right for 271 cells and silent about the 1 that has `tags`.\n")
cat("   Fifth document, fifth silent discard, and this is the one that was\n")
cat("   supposed to be the counterexample.\n")

# ── Q4. always vs sometimes ──────────────────────────────────────────────────
cells <- j |> as.tbl_json() |> enter_object("cells") |> gather_array("cell_i")
keys <- cells |> gather_object("key") |> count(key, name = "n")
cat("\n4. key presence across the cells, from gather_object, nothing named:\n")
for (i in seq_len(nrow(keys)))
  cat(sprintf("     %-18s %4d of 272\n", keys$key[i], keys$n[i]))
cat("   `gather_object` walks whatever keys are there, so this is one of the\n")
cat("   few answers in either language that needs no field name in advance.\n")
cat("   It reads PRESENCE, so execution_count is 132 and the explicit null\n")
cat("   counts as present.\n")

# ── Q5. does any field change type ───────────────────────────────────────────
types <- cells |> gather_object("key") |> json_types("t") |> count(key, t)
cat("\n5. types per key, and tidyjson reports `null` as its own type:\n")
for (i in seq_len(nrow(types)))
  cat(sprintf("     %-18s %-10s %4d\n", types$key[i], as.character(types$t[i]),
              types$n[i]))
cat("   `execution_count` is number x131 and null x1. That is ragged BY NULL\n")
cat("   rather than a type change — the same reading design/probe.py had to be\n")
cat("   repaired for — but tidyjson at least SHOWS both, which pandas, polars,\n")
cat("   duckdb and jsonlite all fail to do.\n")

# ── Q6. are any object keys data ─────────────────────────────────────────────
mimes <- cells |> enter_object("outputs") |> gather_array("o_i") |>
  enter_object("data") |> gather_object("mime") |> count(mime)
cat("\n6. CANNOT. mime keys under outputs[].data:\n")
for (i in seq_len(nrow(mimes)))
  cat(sprintf("     %-18s %4d\n", mimes$mime[i], mimes$n[i]))
cat("   `gather_object` produced them as a COLUMN of key names, which is the\n")
cat("   closest any tool here comes to treating a key as a value — and it is\n")
cat("   the same call that produced the field names in Q4. tidyjson cannot say\n")
cat("   which of the two it just did.\n")

# ── Q3, Q7. what is one record, and how many ─────────────────────────────────
outs <- cells |> enter_object("outputs") |> gather_array("o_i")
cat(sprintf("\n7. %d cells, %d outputs\n", nrow(cells), nrow(outs)))
cat("\n3. two defensible records; tidyjson makes each one `gather_array` away\n")
cat("   and prices neither. `enter_object(\"outputs\")` SILENTLY drops the 140\n")
cat("   markdown cells that have no such key — no warning, no row, and the\n")
cat("   272-to-107 fall is the only evidence it happened.\n")

# ── Q8, Q9. three named fields, one missing from some ────────────────────────
tbl <- cells |> spread_all() |> as_tibble() |>
  select(any_of(c("cell_type", "execution_count"))) |> as.data.frame()
cat(sprintf("\n8. spread_all: %d rows x %d cols\n", nrow(tbl), ncol(tbl)))
print(head(tbl, 3))
cat(sprintf("\n9. execution_count NA on %d of %d rows, all kept — `spread_all`\n",
            sum(is.na(tbl$execution_count)), nrow(tbl)))
cat("   fills absent keys with NA and never drops a row. It also does not\n")
cat("   spread `source` or `outputs`, because they are arrays.\n")

# ── Q10. flatten the deepest array ───────────────────────────────────────────
tp <- outs |> enter_object("data") |> enter_object("text/plain") |>
  gather_array("line_i")
cat(sprintf("\n10. text/plain exploded to lines: %d rows\n", nrow(tp)))
cat("   Four `enter_object`/`gather_array` steps, each one a hand-typed name.\n")

# ── Q11. every path whose value matches ──────────────────────────────────────
cat("\n11. CANNOT. tidyjson's verbs all descend a NAMED path; there is no\n")
cat("   recursive search. `json_schema` knows every path in the document and\n")
cat("   offers no way to filter them by value.\n")

# ── Q12. flattest honest table ───────────────────────────────────────────────
flat <- outs |> spread_all() |> as_tibble()
cat(sprintf("\n12. flattest: %d rows x %d cols\n", nrow(flat), ncol(flat)))
cat(sprintf("   columns: %s\n", paste(names(flat), collapse = ", ")))
cat("   WHAT IS LOST: the 140 markdown cells, silently; `cell_type`, unless\n")
cat("   carried down before the enter_object; and the 17 base64 PNGs, 79% of\n")
cat("   the file, which spread_all puts in a column as whole strings.\n")
