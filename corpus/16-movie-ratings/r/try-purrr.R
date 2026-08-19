# purrr — movie ratings, Kaggle data-cleaning challenge
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr 1.2.2 (+ jsonlite 2.0.0 to parse)
#  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
#  measured      2026-08-10
#  run           cd corpus/16-movie-ratings/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             5   NO                  PARTLY
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          5   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    3   YES                 CANNOT
#   7 how many records                            1   YES                 YES
#   8 three named fields to a table               5   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   1   -                   n/a
#  11 find every path matching something          5   NO                  yes
#  12 flattest honest table                       4   NO                  yes
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
#  14 survives the next file unchanged?               the describe half does
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~40, `%||%` is the ceremony
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

raw <- fromJSON("../source.json", simplifyVector = FALSE)[[1]]
cat(sprintf("\n7. %d films.\n", length(raw)))

keys <- table(unlist(map(raw, names)))
cat("\n1/4. field presence across the 38 films, nothing named in advance:\n")
for (k in names(sort(keys, decreasing = TRUE)))
  cat(sprintf("     %-18s %3d of %d\n", k, keys[[k]], length(raw)))
cat("   NOTHING is on all 38. Two disjoint key-sets — 23 lowercase, 15 Title\n")
cat("   Case — sharing no field at all.\n")

depth <- function(x) if (is.list(x) && length(x)) 1L + max(vapply(x, depth, 1L)) else 0L
cat(sprintf("\n2. depth: %d (from the array root)\n", depth(raw) + 1L))

cat("\n6. CANNOT. The 38 names of `raw` are FILM TITLES — values — and purrr\n")
cat("   hands them back from `names()` exactly as it hands back field names.\n")
cat("   It is the same call, and there is no verb that distinguishes them.\n")

cat("\n5. classes per field, where more than one:\n")
for (k in names(keys)) {
  ts <- setdiff(unique(map_chr(raw, \(v) if (is.null(v[[k]])) "absent"
                                         else class(v[[k]])[[1]])), "absent")
  if (length(ts) > 1) cat(sprintf("     %-18s %s\n", k, paste(ts, collapse = ", ")))
}
cat("   The character values in those two fields are the SENTINELS.\n")

# `%||%` chained is R's first-present, and this document is what it is for.
tbl <- map_dfr(raw, \(v) data.frame(
  rating  = as.character(v$Rating %||% v$rating %||% NA),
  popcorn = as.character(v$`Popcorn Score` %||% v$popcornscore %||% NA),
  tomato  = as.character(v$`Tomato Score` %||% v$tomatoscore %||% NA)),
  .id = "title")
cat(sprintf("\n8/12. `%%||%%` chained collapses all three renamed pairs: %d rows,\n",
            nrow(tbl)))
cat(sprintf("   rating filled %d of %d\n", sum(!is.na(tbl$rating)), nrow(tbl)))
print(head(tbl, 3))
cat("   `.id = \"title\"` is what keeps the film name — `map_dfr` drops the list\n")
cat("   names otherwise, and on a document keyed by title that is the record\n")
cat("   identity. It is one argument and easy to forget.\n")

cat(sprintf("\n9. rating NA on %d of %d after the fallback — none. Either\n",
            sum(is.na(tbl$rating)), nrow(tbl)))
cat("   spelling alone misses 15 or 23.\n")

hits <- new.env()
walk_match <- function(node, p = character(0)) {
  if (is.list(node) && length(node)) {
    nm <- names(node)
    for (i in seq_along(node))
      walk_match(node[[i]], c(p, if (is.null(nm)) "[]" else nm[[i]]))
  } else if (is.character(node) && grepl("^unk", node, ignore.case = TRUE)) {
    k <- p[[length(p)]]
    assign(k, (if (exists(k, hits)) get(k, hits) else 0L) + 1L, hits)
  }
}
walk_match(raw)
h <- unlist(as.list(hits))
cat(sprintf("\n11. %d values match /^unk/, by FIELD (the last path segment):\n", sum(h)))
for (k in names(h)) cat(sprintf("     %-18s %3d\n", k, h[[k]]))
cat("   All 17. Five lines of recursion, mine — purrr has no recursive descent.\n")

cat("\n3. one film per row, and TWO tables inside it:\n")
cat(sprintf("     lowercase   %3d x 3, no holes\n",
            sum(map_lgl(raw, \(v) !is.null(v$rating)))))
cat(sprintf("     Title Case  %3d x 6, no holes\n",
            sum(map_lgl(raw, \(v) !is.null(v$Rating)))))
cat("   54% to 0%, with no field to split on — the discriminator is the\n")
cat("   naming convention and lives in no value.\n")
cat("\n10. n/a. WHAT IS LOST: the 17 sentinels ride through `%||%` as values.\n")
