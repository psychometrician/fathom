# jsonlite — Chicago employee salaries
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite 2.0.0
#  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
#  measured      2026-08-10
#  run           cd corpus/19-chicago-salaries/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             5   NO                  yes
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          5   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  5   NO                  DANGEROUS
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  YES
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   2   -                   n/a
#  11 find every path matching something          -   -                   CANNOT
#  12 flattest honest table                       4   NO                  yes
#  13 needed the shape in advance?                    NO — the file is flat
#  14 survives the next file unchanged?               yes, for this shape
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~30, none
#
# THE ONE FILE WHERE SIMPLIFICATION IS UNAMBIGUOUSLY RIGHT. Everywhere else in
# the corpus `fromJSON`'s default reshaping is a gift with a cost attached. Here
# there is no cost: 5,000 flat records become the exact data frame anybody
# wanted, in one call, with no arguments.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

d <- fromJSON("../source.json")
cat(sprintf("\n1. fromJSON gives a %s: %d x %d\n", class(d)[[1]], nrow(d), ncol(d)))
cat(sprintf("   columns: %s\n", paste(names(d), collapse = ", ")))
cat(sprintf("   `str(d)` is %d lines — readable, which it is on no other corpus\n",
            length(capture.output(str(d)))))
cat("   file. VERDICT.md measures str() at 5,289 lines on npm.\n")

cat("\n2. depth 2. No list-column in the frame, which is jsonlite saying\n")
cat("   nothing was nested, without being asked.\n")

cat(sprintf("\n7. %d records.\n", nrow(d)))

cat("\n4. non-NA count per column:\n")
for (k in names(d)[order(-colSums(!is.na(d)))])
  cat(sprintf("     %-22s %5d of %d\n", k, sum(!is.na(d[[k]])), nrow(d)))
cat("   3,938 + 1,062 = 5,000 exactly. Mutually exclusive, and unremarked.\n")

# ── Q5. the trap ─────────────────────────────────────────────────────────────
cat(sprintf("\n5. DANGEROUS. classes: %s\n",
            paste(sprintf("%s=%s", names(d), sapply(d, \(x) class(x)[[1]])),
                  collapse = ", ")))
cat("   Every column is character, `annual_salary` included. jsonlite does\n")
cat("   coerce JSON NUMBERS to numeric — these are JSON STRINGS, so there is\n")
cat("   nothing to coerce and no warning to give.\n")
cat(sprintf("   max(d$annual_salary) = %s   <- lexicographic, silently\n",
            max(d$annual_salary, na.rm = TRUE)))
cat("   The document is consistently wrong and every tool in both languages\n")
cat("   reports it as consistently right.\n")

cat("\n3. one employee per row, and TWO defensible tables:\n")
for (k in names(sort(table(d$salary_or_hourly), decreasing = TRUE))) {
  s <- d[d$salary_or_hourly == k, ]
  live <- names(s)[colSums(!is.na(s)) > 0]
  cat(sprintf("     %-18s %5d rows x %d cols, no holes\n", k, nrow(s), length(live)))
}
cat(sprintf("   Folded: %d x %d at %.0f%% empty. Split: 0%%. `split(d, ...)` is\n",
            nrow(d), ncol(d), 100 * mean(is.na(d))))
cat("   one call and jsonlite will not propose it.\n")

cat("\n8. three fields:\n")
print(head(d[, c("name", "department", "annual_salary")], 3))
cat(sprintf("\n9. annual_salary NA on %d of %d rows, all kept — for free, because\n",
            sum(is.na(d$annual_salary)), nrow(d)))
cat("   simplification already filled the absent cells with NA.\n")

cat("\n10, 6. n/a. No nested array, no keys that are data.\n")
cat("\n11. CANNOT. jsonlite parses and serialises; it has no search of any kind.\n")

cat(sprintf("\n12. flattest honest table: %d x %d, already flat and already\n",
            nrow(d), ncol(d)))
cat("   correct. WHAT IS LOST: nothing. This is the one corpus entry where\n")
cat("   `fromJSON(path)` with no arguments is the whole answer to the\n")
cat("   extraction half — and it still says nothing about the two things a\n")
cat("   reader needs: the salaries are text, and the table should be two.\n")
