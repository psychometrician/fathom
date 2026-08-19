# purrr — Jupyter notebook, Norvig Advent-2021
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr 1.2.2 (+ jsonlite 2.0.0 to parse)
#  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
#  measured      2026-08-10
#  run           cd corpus/11-jupyter-notebook/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             6   NO                  PARTLY
#   2 how deep                                    5   NO                  yes
#   3 what is one record                          6   YES                 PARTLY
#   4 always present vs sometimes                 5   NO                  yes
#   5 does any field change type                  5   NO                  yes
#   6 are any object keys data                    4   YES                 CANNOT
#   7 how many records                            2   YES                 YES
#   8 three named fields to a table               5   YES                 yes
#   9 a field missing from some rows              4   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          6   NO                  yes
#  12 flattest honest table                       6   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
#  14 survives the next file unchanged?               the describe half does
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~55, `%||%` is the ceremony
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

# ── Q1, Q2. what is in here, and how deep ────────────────────────────────────
# purrr has no describer, but it has the recursion to build one in five lines,
# which is more than glom, jmespath or pydash can say.
walk_paths <- function(node, p = character(0), acc = new.env()) {
  if (is.list(node) && length(node)) {
    nm <- names(node)
    for (i in seq_along(node)) {
      seg <- if (is.null(nm)) "[]" else nm[[i]]
      walk_paths(node[[i]], c(p, seg), acc)
    }
  } else {
    k <- paste(p, collapse = ".")
    assign(k, (if (exists(k, acc)) get(k, acc) else 0L) + 1L, acc)
  }
  acc
}
acc <- walk_paths(doc)
paths <- sort(unlist(as.list(acc)), decreasing = TRUE)
cat(sprintf("\n1. %d folded leaf paths\n", length(paths)))
for (i in seq_len(min(8, length(paths))))
  cat(sprintf("     %-46s %6d\n", names(paths)[i], paths[[i]]))
cat("   The recursion is mine; purrr contributed `map` and nothing else. It is\n")
cat("   the same nine lines every list-walking tool in this corpus needs.\n")

depth <- function(x) if (is.list(x) && length(x)) 1L + max(vapply(x, depth, 1L)) else 0L
cat(sprintf("\n2. depth: %d\n", depth(doc)))

# ── Q7, Q4. how many records, always vs sometimes ────────────────────────────
cells <- doc$cells
outs <- list_flatten(map(cells, \(c) c$outputs %||% list()))
cat(sprintf("\n7. %d cells, %d outputs\n", length(cells), length(outs)))

cat("\n4. key presence across the 272 cells, no field named in advance:\n")
keys <- table(unlist(map(cells, names)))
for (k in names(sort(keys, decreasing = TRUE)))
  cat(sprintf("     %-18s %4d of %d\n", k, keys[[k]], length(cells)))
cat("   `names()` is PRESENCE, so execution_count reads 132 and not 131 — the\n")
cat("   one explicit null is a present key. purrr, jq and ijson are the only\n")
cat("   three tools in either language that separate absence from null here.\n")

# ── Q5. does any field change type ───────────────────────────────────────────
cat("\n5. types per cell field:\n")
for (k in names(keys)) {
  ts <- unique(map_chr(cells, \(c) if (is.null(c[[k]])) "absent-or-null"
                                   else class(c[[k]])[[1]]))
  if (length(ts) > 1) cat(sprintf("     %-18s %s\n", k, paste(ts, collapse = ", ")))
}
cat("   R cannot distinguish an ABSENT key from a NULL one through `[[`, so\n")
cat("   `execution_count` shows one bucket for both. The presence count above\n")
cat("   is where that distinction lives, and it takes two different calls.\n")

# ── Q6. are any object keys data ─────────────────────────────────────────────
mimes <- table(unlist(map(outs, \(o) names(o$data %||% list()))))
cat(sprintf("\n6. CANNOT. mime keys under outputs[].data: %s\n",
            paste(sprintf("%s %d", names(mimes), mimes), collapse = ", ")))
cat("   purrr lists them and has no notion of a key being a value. They arrive\n")
cat("   from `names()` exactly as `cell_type` does.\n")

# ── Q3. what is one record ───────────────────────────────────────────────────
cat("\n3. two defensible records, and purrr prices neither:\n")
cat(sprintf("     a cell      %d rows, 5 fields, 140 of them missing 2\n",
            length(cells)))
cat(sprintf("     an output   %d rows, 6 fields, 3 disjoint key-sets\n",
            length(outs)))

# ── Q8, Q9. three named fields, one missing from some ────────────────────────
tbl <- map_dfr(cells, \(c) data.frame(
  type  = c$cell_type,
  n     = c$execution_count %||% NA_integer_,
  lines = length(c$source)
))
cat(sprintf("\n8. three fields, one row per cell: %d rows\n", nrow(tbl)))
print(head(tbl, 3))
cat(sprintf("\n9. n is NA on %d of %d rows, all kept. `%%||%%` is the whole\n",
            sum(is.na(tbl$n)), nrow(tbl)))
cat("   answer and it is one operator — but it converts a structural fact into\n")
cat("   missing data, which VERDICT.md records as happening on four documents.\n")

# ── Q10. flatten the deepest array ───────────────────────────────────────────
lines <- list_flatten(map(outs, \(o) o$data[["text/plain"]] %||% list()))
cat(sprintf("\n10. text/plain exploded to lines: %d rows\n", length(lines)))
cat("   `o$data[[\"text/plain\"]]` — the slash forces `[[` over `$`, and the\n")
cat("   `%||% list()` is needed because 27 stream outputs have no `data`.\n")

# ── Q11. every path whose value matches ──────────────────────────────────────
hits <- new.env()
walk_match <- function(node, p = character(0)) {
  if (is.list(node) && length(node)) {
    nm <- names(node)
    for (i in seq_along(node))
      walk_match(node[[i]], c(p, if (is.null(nm)) "[]" else nm[[i]]))
  } else if (is.character(node) && grepl("https?://", node)) {
    k <- paste(p, collapse = ".")
    assign(k, (if (exists(k, hits)) get(k, hits) else 0L) + 1L, hits)
  }
}
walk_match(doc)
h <- unlist(as.list(hits))
cat(sprintf("\n11. %d values contain a URL, at %d folded paths:\n", sum(h), length(h)))
for (k in names(h)) cat(sprintf("     %-46s %4d\n", k, h[[k]]))
cat("   Six lines of recursion, again mine. purrr has no recursive descent.\n")

# ── Q12. flattest honest table ───────────────────────────────────────────────
flat <- map_dfr(cells, \(c) if (!length(c$outputs %||% list())) NULL else
  map_dfr(c$outputs, \(o) data.frame(
    type = c$cell_type, n = c$execution_count %||% NA_integer_,
    kind = o$output_type, tp = length(o$data[["text/plain"]] %||% list()))))
cat(sprintf("\n12. flattest: %d rows x %d cols\n", nrow(flat), ncol(flat)))
cat("   WHAT IS LOST: the 140 markdown cells, dropped by the NULL branch —\n")
cat("   which I wrote, and purrr would otherwise have errored on. Plus the 17\n")
cat("   base64 PNGs, 79% of the file's bytes, reduced to nothing here.\n")
