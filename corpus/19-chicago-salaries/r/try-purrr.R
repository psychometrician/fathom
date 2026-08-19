# purrr — Chicago employee salaries
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr 1.2.2 (+ jsonlite 2.0.0 to parse)
#  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
#  measured      2026-08-10
#  run           cd corpus/19-chicago-salaries/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             5   NO                  PARTLY
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          5   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   YES                 YES
#   8 three named fields to a table               5   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   2   -                   n/a
#  11 find every path matching something          5   NO                  yes
#  12 flattest honest table                       5   NO                  yes
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
#  14 survives the next file unchanged?               the describe half does
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~40, `%||%` is the ceremony
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat(sprintf("\n7. %d records.\n", length(doc)))

keys <- table(unlist(map(doc, names)))
cat("\n1/4. key presence across the 5,000 records, nothing named in advance:\n")
for (k in names(sort(keys, decreasing = TRUE)))
  cat(sprintf("     %-22s %5d of %d\n", k, keys[[k]], length(doc)))
cat("   `names()` is PRESENCE, so this separates absent from null. Five keys\n")
cat("   always, three sometimes — and 3,938 + 1,062 = 5,000, which purrr has\n")
cat("   on screen and does not add up.\n")

depth <- function(x) if (is.list(x) && length(x)) 1L + max(vapply(x, depth, 1L)) else 0L
cat(sprintf("\n2. depth: %d\n", depth(doc)))

cat("\n5. classes per field:\n")
for (k in names(keys)) {
  ts <- unique(map_chr(doc, \(r) if (is.null(r[[k]])) "absent" else class(r[[k]])[[1]]))
  cat(sprintf("     %-22s %s\n", k, paste(ts, collapse = ", ")))
}
cat("   Every present value is `character`, `annual_salary` included. purrr is\n")
cat("   right and the document is wrong, which no type report can catch.\n")

cat("\n3. one employee per row, and TWO defensible tables:\n")
grp <- split(doc, map_chr(doc, \(r) r$salary_or_hourly))
for (k in names(sort(lengths(grp), decreasing = TRUE)))
  cat(sprintf("     %-18s %5d rows x %d fields, no holes\n", k, length(grp[[k]]),
              length(unique(unlist(map(grp[[k]], names))))))
cat("   Folded, 8 fields at 22% empty; split, 6 and 7 at 0%. `split()` is base\n")
cat("   R and one line, and nothing suggested it.\n")

tbl <- map_dfr(doc, \(r) data.frame(
  name = r$name, dept = r$department,
  salary = r$annual_salary %||% NA_character_))
cat(sprintf("\n8. three fields, one row per employee: %d rows\n", nrow(tbl)))
print(head(tbl, 3))
cat(sprintf("\n9. salary NA on %d of %d rows, all kept. `%%||%%` again — and here\n",
            sum(is.na(tbl$salary)), nrow(tbl)))
cat("   it converts a KIND OF RECORD into missing data, which is the sharpest\n")
cat("   instance in the corpus of the failure VERDICT.md item 22g names.\n")

hits <- new.env()
walk_match <- function(node, p = character(0)) {
  if (is.list(node) && length(node)) {
    nm <- names(node)
    for (i in seq_along(node))
      walk_match(node[[i]], c(p, if (is.null(nm)) "[]" else nm[[i]]))
  } else if (is.character(node) && grepl("DEPARTMENT", node)) {
    k <- paste(p, collapse = ".")
    assign(k, (if (exists(k, hits)) get(k, hits) else 0L) + 1L, hits)
  }
}
walk_match(doc)
h <- unlist(as.list(hits))
cat(sprintf("\n11. %d values match /DEPARTMENT/, at %d folded paths:\n", sum(h), length(h)))
for (k in names(h)) cat(sprintf("     %-26s %6d\n", k, h[[k]]))
cat("   Five lines of recursion, mine. purrr has no recursive descent.\n")

cat("\n10, 6. n/a. No nested array, no keys that are data.\n")
cat(sprintf("\n12. flattest honest table: %d x 3 above, or %d x 8 with every\n",
            nrow(tbl), length(doc)))
cat("   field. WHAT IS LOST: nothing. purrr reshapes only what it is told to.\n")
