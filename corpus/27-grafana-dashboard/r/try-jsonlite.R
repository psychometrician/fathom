# jsonlite — Grafana "Node Exporter Full", dashboard 1860
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
#  measured      2026-08-13
#  run           cd corpus/27-grafana-dashboard/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   PARTLY
#   1 what is in here                             5   NO                  yes — simplification
#   2 how deep                                    3   NO                  yes, by MY recursion
#   3 what is one record                          5   -                   CANNOT
#   4 always present vs sometimes                 4   NO                  PARTLY — see below
#   5 does any field change type                  4   NO                  yes, once melted
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            6   NO                  31 BY DEFAULT, 132 after
#   8 three named fields to a table               2  YES                  YES — it is already a frame
#   9 a field missing from some rows              2  YES                  yes — NA
#  10 flatten the deepest array                   3  YES                  yes
#  11 find every path matching something          3   NO                  yes, once melted
#  12 flattest honest table                       4   NO                  PARTLY — recursion is mine
#  13 needed the shape in advance?                    NO to read, YES to go deeper
#  14 survives the next file unchanged?               NO
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~55
#
# **`fromJSON` auto-simplifies, and on this document that is both the best and
# the most dangerous behaviour in the R half.** With no arguments it turns
# `panels` into a 31 x 15 data frame — a real, tidy, immediately usable table,
# built without naming a single path.
#
# **And it stops exactly one level too early.** The `panels` COLUMN of that frame
# is a list of data frames holding the other 101, sitting in plain sight, and
# nothing counts them. `nrow(doc$panels)` is 31 and looks like the answer.

suppressMessages(library(jsonlite))
cat(sprintf("jsonlite %s · R %s.%s\n", packageVersion("jsonlite"),
            R.version$major, R.version$minor))

cat("\nQ0  PARTLY, and it is the best Q0 in the R half. `validate()` reports\n")
cat(sprintf("    well-formedness: %s. jsonlite also REFUSES bare NaN and Infinity\n",
            validate(paste(readLines("../source.json", warn = FALSE), collapse = "\n"))))
cat("    rather than accepting them silently, which is a real check the Python\n")
cat("    parsers do not make. It says nothing about duplicate keys or 2^53.\n")

# ── Q1/Q7. Simplification does the work, and then stops. ─────────────────
doc <- fromJSON("../source.json")
p <- doc$panels
cat(sprintf("\nQ1  fromJSON() -> doc$panels is a %s, %d x %d, with no path named:\n",
            class(p)[1], nrow(p), ncol(p)))
cat(sprintf("      %s\n", paste(head(names(p), 8), collapse = ", ")))
cat("    yes, and this is genuinely impressive: a usable table straight out of\n")
cat("    the parser. It is the only tool of the fourteen that rectangles by\n")
cat("    default rather than on request.\n")

cat("\nQ7  THE CENTRAL QUESTION.\n")
cat(sprintf("      nrow(doc$panels)                                  -> %d\n", nrow(p)))
nested_n <- vapply(p$panels, \(x) if (is.data.frame(x)) nrow(x) else 0L, 0L)
cat(sprintf("      sum(nrow) over the `panels` LIST-COLUMN            -> %d\n", sum(nested_n)))
cat(sprintf("      the sum                                           -> %d\n",
            nrow(p) + sum(nested_n)))
cat("    31 BY DEFAULT, AND THE 101 ARE ALREADY IN THE OBJECT. The `panels`\n")
cat("    column is a list of data frames — simplification built them and then\n")
cat("    left them nested, one level below the frame it returned.\n")
cat("    That is the most interesting near-miss in the comparison: jsonlite did\n")
cat("    the recursive work and its RESULT does not report it. `nrow()` is 31.\n")
cat(sprintf("      (%d of the 31 rows carry a non-empty nested frame.)\n",
            sum(nested_n > 0)))

# ── Q2/Q12. The melt, and the recursion is mine. ─────────────────────────
raw <- fromJSON("../source.json", simplifyVector = FALSE)
rows <- list()
walk_it <- function(x, path = character()) {
  if (is.list(x) && length(x) > 0) {
    nm <- names(x)
    for (i in seq_along(x))
      walk_it(x[[i]], c(path, if (is.null(nm)) "*" else nm[i]))
  } else if (!is.list(x)) {
    rows[[length(rows) + 1]] <<- list(path = paste(path, collapse = "."),
                                      depth = length(path), value = x)
  }
}
walk_it(raw)
depth <- max(vapply(rows, \(r) r$depth, 0L))
cat(sprintf("\nQ2  %d, from a recursion I wrote against simplifyVector = FALSE. yes,\n", depth))
cat("    and it agrees with every other tool at 12. jsonlite has no depth verb.\n")
cat(sprintf("\nQ12 %s rows x 3. PARTLY — the walk is base R.\n",
            format(length(rows), big.mark = ",")))
cat("    `flatten()` is jsonlite's own answer and it is worth being precise about:\n")
cat(sprintf("    flatten(doc$panels) gives %d columns by lifting nested OBJECT columns\n",
            ncol(flatten(p))))
cat("    into dotted names, and it does NOT touch list-columns of data frames.\n")
cat("    So it widens the 31 rows and never reaches the 101.\n")

# ── Q3. What is one record. ─────────────────────────────────────────────
panels_all <- c(
  lapply(seq_len(nrow(p)), \(i) as.list(p[i, ])),
  unlist(lapply(p$panels, \(x) if (is.data.frame(x) && nrow(x))
    lapply(seq_len(nrow(x)), \(i) as.list(x[i, ])) else NULL), recursive = FALSE))
tg <- sum(vapply(raw$panels, \(x) length(x$targets), 0L)) +
      sum(vapply(unlist(lapply(raw$panels, `[[`, "panels"), recursive = FALSE),
                 \(x) length(x$targets), 0L))
cat("\nQ3  CANNOT — nothing proposed, nothing priced:\n")
for (r in list(c("one panel per row (all depths)", length(panels_all)),
               c("one TOP-LEVEL panel per row", nrow(p)),
               c("one target per row", tg),
               c("one leaf per row", length(rows))))
  cat(sprintf("      %-32s %6s\n", r[1], format(as.integer(r[2]), big.mark = ",")))

# ── Q4. Always vs sometimes — and simplification has damaged this. ──────
cat("\nQ4  PARTLY, AND THE FRAME HAS ALREADY LOST THE ANSWER.\n")
present <- vapply(p, \(col) {
  if (is.list(col)) sum(!vapply(col, \(x) is.null(x) || length(x) == 0, logical(1)))
  else sum(!is.na(col))
}, 0L)
present <- sort(present, decreasing = TRUE)
for (i in seq_len(min(9, length(present))))
  cat(sprintf("      %-16s %4d of %d %s\n", names(present)[i], present[i], nrow(p),
              ifelse(present[i] == nrow(p), "always", "")))
cat("    Simplification materialised a column for every field ANY panel has and\n")
cat("    filled the rest with NA, so absent and present-and-null are one cell —\n")
cat("    the same erasure tidyr's `unnest_wider` and polars' structs perform.\n")
cat("    `links` is present on 115 of 132 panels in the document and every value\n")
cat("    is `[]`; count it here and you get an answer about emptiness instead.\n")

# ── Q5. ─────────────────────────────────────────────────────────────────
paths <- vapply(rows, \(r) r$path, "")
cls <- vapply(rows, \(r) class(r$value)[1], "")
tab <- tapply(cls, paths, \(x) length(unique(x)))
cat(sprintf("\nQ5  paths whose leaves have more than one class: %d. yes, once melted,\n",
            sum(tab > 1)))
cat("    and it agrees with ijson, rrapply, duckdb and purrr at 4.\n")

cat("\nQ6  CANNOT. Keys become column names unconditionally.\n")

# ── Q8/Q9. ──────────────────────────────────────────────────────────────
cat(sprintf("\nQ8  p[, c(\"title\", \"type\", \"id\")] -> %d rows, ALREADY A FRAME. yes, and\n", nrow(p)))
cat("    it is the least ceremony of any Q8 here — no verb at all, just indexing.\n")
print(utils::head(p[, c("title", "type", "id")], 2))
cat(sprintf("\nQ9  `description` is NA on %d of these %d rows and they survive. yes —\n",
            sum(is.na(p$description)), nrow(p)))
cat("    simplification fills an absent field with NA and keeps the row.\n")

# ── Q10. ────────────────────────────────────────────────────────────────
cat(sprintf("\nQ10 %d targets, by summing over the list-column. yes for a level you\n", tg))
cat("    name, and it agrees with every other tool at 269.\n")

# ── Q11. ────────────────────────────────────────────────────────────────
vals <- vapply(rows, \(r) if (is.character(r$value)) r$value else "", "")
cat(sprintf("\nQ11 %d leaves mention a Grafana template variable. yes, once melted,\n",
            sum(grepl("\\$node|\\$job|\\$__rate_interval", vals))))
cat("    and it agrees with jq, duckdb, rrapply, tidyjson and purrr at 255.\n")

cat("
CONCLUSION. jsonlite is the most interesting near-miss in the comparison.

Its auto-simplification is the only thing in fourteen tools that hands back a
usable table with no path named and no verb called — `fromJSON()` alone gives a
31 x 15 data frame — and Q8 is consequently the cheapest here, because the table
already exists.

And it built the nested panels too. They are sitting in the `panels` list-column
as data frames, 101 rows across 16 of them, fully parsed. jsonlite did the
recursive work and then returned an object whose `nrow()` is 31. The information
is present and the answer is wrong, which is a different failure from every
other tool here: pandas and tidyr never reached the 101, and jsonlite is holding
them.

Its `flatten()` widens rather than deepens — 15 columns to 68 by lifting nested
objects into dotted names — and explicitly does not descend into list-columns of
frames, so the verb that looks like it would finish the job cannot.

Q0 is the best in the R half: `validate()` is a real check, and refusing bare
NaN is a real difference from the Python parsers.
")
