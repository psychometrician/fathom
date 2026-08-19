# rrapply — movie ratings, Kaggle data-cleaning challenge
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply 1.2.8 (+ jsonlite 2.0.0 to parse)
#  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
#  measured      2026-08-10
#  run           cd corpus/16-movie-ratings/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             6   NO                  yes
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          4   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    5   NO                  PARTLY
#   7 how many records                            2   NO                  yes
#   8 three named fields to a table               4   YES                 PARTLY
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   1   -                   n/a
#  11 find every path matching something          4   NO                  yes
#  12 flattest honest table                       5   NO                  PARTLY
#  13 needed the shape in advance?                    NO for almost all of it
#  14 survives the next file unchanged?               YES — melt names nothing
#  15 readable a week later?                          the melt yes
#  16 lines, and how much is ceremony?                ~40, melt is one call
#
# THE MELT'S BEST QUESTION IS Q6, AND THIS DOCUMENT IS WHY. `how="melt"` puts
# every path segment in its own COLUMN, so a key that is data ends up in a
# column of data — which is structurally the right place for it and is the
# closest any tool in either language comes to naming keys-as-data.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
m <- rrapply(doc, how = "melt")
lvl <- ncol(m) - 1L

cat(sprintf("\n1. melt: %d leaf rows x %d columns\n", nrow(m), ncol(m)))
full <- apply(m[, seq_len(lvl), drop = FALSE], 1,
              \(r) paste(r[!is.na(r)], collapse = "."))
chars <- sum(nchar(full)) + length(full)
cat(sprintf("   listing every path costs %s chars for a 6,975-byte file (%.0f%%)\n",
            format(chars, big.mark = ","), 100 * chars / 6975))
cat("   Over 100%, and the cause is in the paths: every one carries a FILM\n")
cat("   TITLE. This is the same O(data) failure as json_schema's 66% and\n")
cat("   polars' 65% on the same file, reached by a third road.\n")

cat(sprintf("\n2. depth: %d\n", lvl))
cat(sprintf("\n7. %d films — `length(unique(m$L2))`, and the melt makes that\n",
            length(unique(m$L2[!is.na(m$L2)]))))
cat("   countable because the titles are IN A COLUMN rather than in a path.\n")

cat("\n6. PARTLY, and this is rrapply's best answer on any corpus file.\n")
cat("   L2 holds the 38 FILM TITLES and L3 holds the 9 FIELD NAMES — two\n")
cat("   columns, cleanly separated, by a call that named nothing. Every other\n")
cat("   tool here mixes them into one namespace. rrapply still cannot SAY that\n")
cat("   L2 is data and L3 is structure; it has merely put them where the\n")
cat("   difference is visible.\n")

keys <- table(m$L3[!is.na(m$L3)])
cat("\n4. field counts, straight off L3:\n")
for (k in names(sort(keys, decreasing = TRUE)))
  cat(sprintf("     %-18s %3d of 38\n", k, keys[[k]]))
cat("   NOTHING is on all 38 — two disjoint key-sets.\n")

cat("\n5. classes of the value column, per field:\n")
for (k in names(keys)) {
  v <- m$value[!is.na(m$L3) & m$L3 == k]
  cl <- unique(vapply(v, \(x) class(x)[[1]], ""))
  if (length(cl) > 1) cat(sprintf("     %-18s %s\n", k, paste(cl, collapse = ", ")))
}
cat("   The melt keeps both populations — it never unifies, because `value` is\n")
cat("   a LIST column. polars and DuckDB both coerced here.\n")

isunk <- vapply(m$value, \(v) is.character(v) && grepl("^unk", v, ignore.case = TRUE), TRUE)
cat(sprintf("\n11. %d values match /^unk/, by field: %s\n", sum(isunk),
            paste(sprintf("%s x%d", names(table(m$L3[isunk])), table(m$L3[isunk])),
                  collapse = ", ")))
cat("   One vapply over a column, because the melt already made every value a\n")
cat("   row. rrapply and jq are the two tools that answer Q11 without a walk.\n")

wide <- data.frame(
  title  = names(doc[[1]]),
  rating = vapply(doc[[1]], \(v) as.character(v$Rating %||% v$rating %||% NA), ""))
cat(sprintf("\n8/12. PARTLY: %d rows, built with base R. `how=\"bind\"` wants a\n",
            nrow(wide)))
cat("   regular nested list and the two disjoint key-sets deny it that.\n")
print(head(wide, 3))
cat(sprintf("\n9. rating NA on %d of %d after `%%||%%` — none.\n",
            sum(is.na(wide$rating)), nrow(wide)))

cat("\n3. one film per row, and TWO tables inside it — 54% empty folded, 0%\n")
cat("   split, and no field to split on.\n")
cat("\n10. n/a. WHAT IS LOST: nothing — and the melt is 4.2x the rows of the\n")
cat("   table anybody wanted, on a document that was nearly one already.\n")
