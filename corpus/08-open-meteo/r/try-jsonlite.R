# jsonlite — Open-Meteo hourly forecast, the columnar document
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   12 KB, depth 3, 24 paths, 14 fields,
#                                 every raggedness axis 0, row shapes 1
#  measured      2026-08-10
#  run           cd corpus/08-open-meteo/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           4   NO                  YES
#   2 how deep                                  2   NO                  yes
#   3 what is one record                        6   NO                  YES
#   4 always present vs sometimes               3   NO                  yes
#   7 how many records                          1   NO                  yes
#   8 three named fields to a table             3   YES                 yes
#  7a related by position                       7   NO                  YES
#  12 flattest honest table                     4   NO                  YES
#  13 needed the shape in advance?                  NO for 1, 2, 3, 7a, 12
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE, AND IT IS THE ONE THAT COULD ARGUE AGAINST PHASE 2.
#
# `NOTES.md` calls this the document where the whole design has no purchase:
# *"Operation 1 — fold sibling instances — is the load-bearing idea and it has
# nothing to fold here."* Every axis reads 0 or 1. The useful table is **336 × 5**
# and the probe can only offer *the whole document, 1 row × 9 cols*. `rows()`
# returns 5 rows each holding a 336-element list, and the answer is a transpose
# it has no operator for.
#
# **A data frame IS a named list of equal-length vectors.** R's native model is
# column-oriented and `hourly` is exactly that shape. Prediction 1 in NOTES.md
# says this file is trivial here.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.json"
simp <- fromJSON(path)
doc  <- fromJSON(path, simplifyVector = FALSE)
cat(sprintf("  %s bytes\n", format(file.size(path), big.mark = ",")))

# ── Q1 / Q2. ─────────────────────────────────────────────────────────────────
cat("\n1. what is in here — str(), and for once it fits on a screen:\n")
cat(sprintf("   str(simplified) whole document: %d lines\n",
            length(capture.output(str(simp)))))
cat(sprintf("   top-level names: %s\n", paste(names(simp), collapse = ", ")))
cat("   SCORED YES, and it is the only YES for question 1 in this corpus.\n")
cat("   12 KB with 14 fields and depth 3: str() describes it completely and\n")
cat("   readably. The O(data) problem needs a document with something to\n")
cat("   enumerate, and this one has nine top-level keys.\n")

depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("\n2. depth %d\n", depth(doc)))

# ── Q3 / Q12. PREDICTION 1. THE WHOLE POINT. ─────────────────────────────────
cat("\n3/12. what is one record — PREDICTION 1:\n")
cat(sprintf("   $hourly is a %s of %d, each of length %d\n",
            class(simp$hourly)[1], length(simp$hourly),
            unique(vapply(simp$hourly, length, 0L))))
t0 <- Sys.time()
tbl <- as.data.frame(simp$hourly)
cat(sprintf("   as.data.frame(simp$hourly) -> %d x %d in %.3f s\n",
            nrow(tbl), ncol(tbl), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
print(utils::head(tbl, 3))
cat("   PREDICTION 1 CONFIRMED, IN ONE EXPRESSION, WITH NO VERB CHOSEN.\n")
cat("   NOTES.md records the probe offering `the whole document, 1 rows x 9\n")
cat("   cols` and rows() returning 5 rows each holding a 336-element list,\n")
cat("   with the answer being `a transpose and there is no operator for it`.\n")
cat("   IN R THE TRANSPOSE IS NOT AN OPERATION. `as.data.frame` on a named list\n")
cat("   of equal-length vectors IS this table, because that is what a data\n")
cat("   frame already is. The shape fathom finds hardest is the shape R is\n")
cat("   built on.\n")

# ── 7a. AND THE ALIGNMENT HERE IS SAFE, WHICH IS THE OPPOSITE OF 06. ─────────
cat("\n7a. related by position — and this one is safe, by KEY:\n")
cat(sprintf("   hourly_units names:  %s\n", paste(names(simp$hourly_units), collapse = ", ")))
cat(sprintf("   identical to hourly: %s\n",
            identical(names(simp$hourly_units), names(simp$hourly))))
units <- unlist(simp$hourly_units)[names(tbl)]
cat("   joining units to columns BY NAME, not by position:\n")
for (k in names(tbl)[2:4])
  cat(sprintf("     %-22s %s\n", k, units[[k]]))
cat("   THERE IS NOTHING TO MIS-JOIN. The columns are named by KEY and the\n")
cat("   units object is keyed identically, so `units[names(tbl)]` cannot be\n")
cat("   wrong. Compare 06-espn-qbr, where a same-length array in a different\n")
cat("   ORDER gives the league's best quarterback a Total QBR of -7.4.\n")
cat("   NOTES.md records the probe printing the SAME warning on both files —\n")
cat("   `same length is not same order` — which is the finding on ESPN and\n")
cat("   noise here, attached to the wrong array. jsonlite prints no warning on\n")
cat("   either, and on this file that happens to be correct.\n")

# ── Q4 / Q7 / Q8. ────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
cat(sprintf("   %d columns, %d rows, %d NA cells in the whole table\n",
            ncol(tbl), nrow(tbl), sum(is.na(tbl))))
cat("   NOTES.md grades 0/0 ragged by absence and 0 by null, and there is\n")
cat("   nothing for a raggedness axis to describe. That is the file's point:\n")
cat("   every axis reads 0 or 1 and the document still defeats the design.\n")

cat(sprintf("\n7. %d hourly observations\n", nrow(tbl)))

cat("\n8. three named fields, one row per hour:\n")
three <- tbl[, c("time", "temperature_2m", "wind_speed_10m")]
cat(sprintf("   tbl[, c(...)] -> %d x %d\n", nrow(three), ncol(three)))
print(utils::head(three, 2))
cat("   Free, because question 3 was already answered by the parse.\n")

cat("
CONCLUSION — the document that defeats fathom's central operation is the one R
handles in a single expression, and that belongs in the verdict.

  `NOTES.md` is unambiguous about what this file established: **operation 1 has
  nothing to fold here.** There are no sibling objects. `RECORD SHAPES, FOLDED`
  is empty. The probe offers *the whole document, 1 row x 9 cols*, `rows()`
  returns five rows each holding a 336-element list, and the answer is a
  transpose with no operator.

  **`as.data.frame(fromJSON(path)$hourly)` returns the 336 x 5 table.** One
  expression, no verb chosen, nothing known in advance, three thousandths of a
  second. **In R the transpose is not an operation at all** — a data frame *is*
  a named list of equal-length vectors, so a column-oriented document is
  already in R's native shape.

  **That is the sharpest thing the corpus has said against Phase 2, and it should
  be recorded as such rather than softened.** The case fathom finds hardest —
  the one where its load-bearing idea has no purchase — is the case the
  ecosystem it would ship into finds easiest. A tool cannot claim to help most
  where its host language already needs no help.

  THE HONEST COUNTERWEIGHT, and it is real: this works because R got lucky about
  its data model, not because jsonlite understood anything. It does not tell you
  `hourly` is the interesting key, does not mention that the five arrays are
  equal-length, and would build the same frame from five arrays that happened to
  match by coincidence. On `06-espn-qbr` that same absence of checking is what
  makes the decoy dangerous. **Here it is right for no reason.**

  AND THE ALIGNMENT HERE IS SAFE IN A WAY THE PROBE CANNOT SEE. The columns are
  named by KEY — `hourly_units` is keyed identically — so `units[names(tbl)]`
  cannot be wrong. `NOTES.md` records the probe printing the same
  `same length is not same order` warning on this file and on ESPN, where one is
  the finding and the other is noise. Two documents, opposite risk, one warning.
")
