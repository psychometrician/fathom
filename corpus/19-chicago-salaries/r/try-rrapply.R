# rrapply — Chicago employee salaries
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply 1.2.8 (+ jsonlite 2.0.0 to parse)
#  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
#  measured      2026-08-10
#  run           cd corpus/19-chicago-salaries/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             7   NO                  yes
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          4   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            2   NO                  yes
#   8 three named fields to a table               4   YES                 PARTLY
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   2   -                   n/a
#  11 find every path matching something          4   NO                  yes
#  12 flattest honest table                       6   NO                  PARTLY
#  13 needed the shape in advance?                    NO for almost all of it
#  14 survives the next file unchanged?               YES — melt names nothing
#  15 readable a week later?                          the melt yes
#  16 lines, and how much is ceremony?                ~40, melt is one call
#
# THE MELT'S BEST CASE AND ITS WORST, ON ONE DOCUMENT. `how="melt"` names
# nothing in advance, which is why VERDICT.md keeps returning to it. It is also
# one row per LEAF, and on a document that is already a table that means turning
# 5,000 rows into 38,000 and calling it an answer.
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
cat(sprintf("   listing every path costs %s chars for a 944,651-byte file (%.0f%%)\n",
            format(chars, big.mark = ","), 100 * chars / 944651))
cat("   VERDICT.md measures this melt at 226% on 03-natural-earth, the corpus\n")
cat("   high, driven by 99,566 array indices. Here it is far lower — 5,000\n")
cat("   indices and one level of fields — but it is still one row per LEAF on\n")
cat("   a document that was already a 5,000-row table.\n")

fold <- function(x) if (is.na(suppressWarnings(as.integer(x)))) x else "[]"
paths <- apply(m[, seq_len(lvl), drop = FALSE], 1, \(r) {
  r <- r[!is.na(r)]; paste(vapply(r, fold, ""), collapse = ".")
})
tab <- sort(table(paths), decreasing = TRUE)
cat(sprintf("\n   folded to %d path shapes:\n", length(tab)))
for (i in seq_along(tab)) cat(sprintf("     %-26s %6d\n", names(tab)[i], tab[[i]]))
cat("   The fold is mine. rrapply gives the long frame; collapsing the index\n")
cat("   column is what turns it from data into a description.\n")

cat(sprintf("\n2. depth: %d\n", lvl))
cat(sprintf("\n7. %d records (the melt does not say so; %d leaves / 8 fields\n",
            length(doc), nrow(m)))
cat("   would be wrong, because three fields are sometimes).\n")

keys <- table(m$L2[!is.na(m$L2)])
cat("\n4. keys under the record level, straight off the melt:\n")
for (k in names(sort(keys, decreasing = TRUE)))
  cat(sprintf("     %-22s %5d of %d\n", k, keys[[k]], length(doc)))
cat("   These ARE presence counts here — unlike every other corpus file —\n")
cat("   because no field holds a container, so one leaf is one field.\n")

cat("\n5. classes of the value column, per key:\n")
for (k in names(keys)) {
  v <- m$value[!is.na(m$L2) & m$L2 == k]
  cat(sprintf("     %-22s %s\n", k,
              paste(unique(vapply(v, \(x) class(x)[[1]], "")), collapse = ", ")))
}
cat("   All character, `annual_salary` included.\n")

cat("\n3. one employee per row. The melt cannot propose it: it has exactly one\n")
cat("   row shape — path plus value — so there is nothing to choose between\n")
cat("   and nothing priced. That is the cost of the universal answer, and on a\n")
cat("   document that IS a table it is the whole cost.\n")

tbl <- data.frame(
  name = vapply(doc, \(r) r$name, ""),
  dept = vapply(doc, \(r) r$department, ""),
  salary = vapply(doc, \(r) if (is.null(r$annual_salary)) NA_character_
                            else r$annual_salary, ""))
cat(sprintf("\n8. PARTLY: %d rows, built with base R. `how=\"bind\"` wants a\n", nrow(tbl)))
cat("   regular nested list and this one is ragged, so the extraction falls\n")
cat("   back to vapply. rrapply describes far better than it extracts.\n")
print(head(tbl, 3))
cat(sprintf("\n9. salary NA on %d of %d rows, all kept.\n",
            sum(is.na(tbl$salary)), nrow(tbl)))

isdept <- vapply(m$value, \(v) is.character(v) && grepl("DEPARTMENT", v), TRUE)
cat(sprintf("\n11. %d values match /DEPARTMENT/, at path shape(s): %s\n",
            sum(isdept), paste(unique(paths[isdept]), collapse = ", ")))
cat("   One vapply over a column, because the melt already made every value in\n")
cat("   the document a row. This is the question rrapply is best at.\n")

cat("\n10, 6. n/a. No nested array, no keys that are data.\n")
cat(sprintf("\n12. the melt IS the flattest honest table: %d x %d — and it is\n",
            nrow(m), ncol(m)))
cat(sprintf("   %.1fx the rows of the table anybody wanted.\n", nrow(m) / length(doc)))
cat("   WHAT IS LOST: nothing, and that is the complaint. A document that was\n")
cat("   already rectangular has been made long, and rrapply has no verb to put\n")
cat("   it back — `how=\"bind\"` needs the regularity the document does not have.\n")
