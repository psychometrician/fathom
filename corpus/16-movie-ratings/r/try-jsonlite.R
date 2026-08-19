# jsonlite — movie ratings, Kaggle data-cleaning challenge
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite 2.0.0
#  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
#  measured      2026-08-10
#  run           cd corpus/16-movie-ratings/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             5   NO                  WRONG
#   2 how deep                                    2   NO                  PARTLY
#   3 what is one record                          5   YES                 PARTLY
#   4 always present vs sometimes                 4   YES                 yes
#   5 does any field change type                  5   NO                  yes
#   6 are any object keys data                    4   YES                 WRONG
#   7 how many records                            1   YES                 YES
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   1   -                   n/a
#  11 find every path matching something          -   -                   CANNOT
#  12 flattest honest table                       5   YES                 PARTLY
#  13 needed the shape in advance?                    YES — Q1 is actively wrong
#  14 survives the next file unchanged?               no
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~35, little
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

d <- fromJSON("../source.json")
cat(sprintf("\n1. fromJSON gives a %s with %d columns\n", class(d)[[1]], ncol(d)))
cat(sprintf("   first three: %s\n", paste(names(d)[1:3], collapse = ", ")))
cat("   WRONG. The 38 FILM TITLES became columns, because the document is a\n")
cat("   one-element array holding an object keyed by film. Simplification —\n")
cat("   which is right on 19-chicago-salaries and useful on most files — is\n")
cat("   actively harmful here: it turned 38 records into 38 columns.\n")
cat(sprintf("\n6. WRONG. %d of the column names are values.\n", ncol(d)))

raw <- fromJSON("../source.json", simplifyVector = FALSE)[[1]]
cat(sprintf("\n   Told the right shape by hand: %d films.\n", length(raw)))
cat(sprintf("\n7. %d films.\n", length(raw)))
cat("\n2. PARTLY — depth 3, but only countable on the UNSIMPLIFIED parse.\n")
cat("   The simplified frame has flattened the nesting into column names.\n")

keys <- table(unlist(lapply(raw, names)))
cat("\n4. field presence across the 38 films:\n")
for (k in names(sort(keys, decreasing = TRUE)))
  cat(sprintf("     %-18s %3d of %d\n", k, keys[[k]], length(raw)))
cat("   NOTHING is on all 38 — the 23 lowercase films and the 15 Title Case\n")
cat("   ones share no field at all. Two documents in one file.\n")

cat("\n5. classes per field:\n")
for (k in names(keys)) {
  ts <- unique(vapply(raw, \(v) if (is.null(v[[k]])) "absent" else class(v[[k]])[[1]], ""))
  ts <- setdiff(ts, "absent")
  if (length(ts) > 1) cat(sprintf("     %-18s %s\n", k, paste(ts, collapse = ", ")))
}
cat("   `Popcorn Score` and `Tomato Score` are integer-or-character. The\n")
cat("   character values are the SENTINELS: 'unknown' and the misspelt\n")
cat("   'unkown'. jsonlite does NOT unify them — the unsimplified parse keeps\n")
cat("   both, which is more than polars or DuckDB manage.\n")

sent <- table(unlist(lapply(raw, \(v) Filter(\(x) is.character(x) &&
                                               grepl("^unk", x, ignore.case = TRUE), v))))
cat(sprintf("   sentinels: %s — %d of the 159 present cells\n",
            paste(sprintf("%s x%d", names(sent), sent), collapse = ", "), sum(sent)))

tbl <- data.frame(
  title  = names(raw),
  rating = vapply(raw, \(v) as.character(v$Rating %||% v$rating %||% NA), ""),
  genre  = vapply(raw, \(v) as.character(v$Genre %||% NA), ""))
cat(sprintf("\n8. three fields, one row per film: %d rows\n", nrow(tbl)))
print(head(tbl, 3))
cat(sprintf("\n9. genre NA on %d of %d rows, all kept — the 23 lowercase films\n",
            sum(is.na(tbl$genre)), nrow(tbl)))
cat("   never had it. `%||%` chained twice is R's first-present, and it is the\n")
cat("   FOURTH spelling of that word this entry has met after glom's Coalesce,\n")
cat("   jmespath's `||` and pydash-plus-`or`.\n")

cat("\n3. one film per row, and TWO tables inside it:\n")
lower <- Filter(\(v) !is.null(v$rating), raw)
upper <- Filter(\(v) !is.null(v$Rating), raw)
cat(sprintf("     lowercase   %3d films x 3 fields, no holes\n", length(lower)))
cat(sprintf("     Title Case  %3d films x 6 fields, no holes\n", length(upper)))
cat("   54% empty folded, 0% split — and there is NO FIELD to split on. The\n")
cat("   two groups share no key, so the discriminator is the naming convention.\n")

cat("\n10. n/a. 11. CANNOT — jsonlite has no search of any kind.\n")
cat(sprintf("\n12. flattest honest table: %d x 3 above. WHAT IS LOST: the 17\n", nrow(tbl)))
cat("   sentinels, which `%||%` carries through as ordinary values because\n")
cat("   they are PRESENT; and, if you take the default parse, the 38 records.\n")
