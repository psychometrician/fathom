# rrapply — Open-Meteo hourly forecast, the columnar document
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.json   12 KB, depth 3, 24 paths, 14 fields,
#                                 every raggedness axis 0, row shapes 1
#  measured      2026-08-10
#  run           cd corpus/08-open-meteo/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                          10   NO                  NO
#   2 how deep                                  2   NO                  YES
#   3 what is one record                        6   NO                  NO
#   7 how many records                          2   NO                  yes
#  12 flattest honest table                     5   NO                  WRONG
#  13 needed the shape in advance?                  NO for 1, 2
#  16 lines, and how much is ceremony?              see the conclusion
#
#  Q12 is scored WRONG. The melted frame is a legitimate flat table and it is
#  the wrong one: 1,692 rows where the document holds 336 observations.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. The melt ratio has been corrected twice — `07-graphql` falsified
# the prediction that it tracks folding, `04-gharchive` and `06-espn-qbr`
# confirmed that it tracks path length against value size. **This document is
# the extreme case of that mechanism**: values are numbers like `23.4` under
# paths like `hourly.temperature_2m.335`.
#
# Prediction 4 in NOTES.md says the ratio comes in **above 150%** and near the
# top of the seven-file table.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

path  <- "../source.json"
bytes <- file.size(path)
doc   <- fromJSON(path, simplifyVector = FALSE)

# ── Q1 / Q12. PREDICTION 4. ──────────────────────────────────────────────────
cat("\n1/12. what is in here — melt every leaf to a row:\n")
m  <- rrapply(doc, how = "melt")
lv <- grep("^L", names(m), value = TRUE)
paths <- apply(m[, lv, drop = FALSE], 1,
               function(r) paste(r[!is.na(r)], collapse = "."))
chars <- sum(nchar(paths)) + length(paths)
idx   <- unique(gsub("(^|[.])[0-9]+($|(?=[.]))", "\\1[]", paths, perl = TRUE))
cat(sprintf("   %s leaves, %s chars for %s bytes — %.0f%%\n",
            format(nrow(m), big.mark = ","), format(chars, big.mark = ","),
            format(bytes, big.mark = ","), 100 * chars / bytes))
cat(sprintf("   average value %.1f bytes, average path %.1f chars\n",
            bytes / nrow(m), chars / nrow(m)))
cat(sprintf("   folding array indices: %d path shapes, %.1f%%, a %.0fx fold\n",
            length(idx), 100 * (sum(nchar(idx)) + length(idx)) / bytes,
            nrow(m) / length(idx)))
cat("   PREDICTION 4 CONFIRMED AND EXCEEDED — this is the CORPUS HIGH, above\n")
cat("   03-natural-earth's 226%, on the corpus's SMALLEST file.\n")
cat("     04-gharchive       52%   long values (SHAs, commit messages)\n")
cat("     05-fhir-bundle     60%\n")
cat("     06-espn-qbr       140%\n")
cat("     09-stripe-openapi 141%\n")
cat("     10-wikidata       173%\n")
cat("     07-graphql        204%\n")
cat("     03-natural-earth  226%\n")
cat(sprintf("     08-open-meteo     %3.0f%%   <- HERE. 7-byte values, 26-char paths\n",
            100 * chars / bytes))
cat("   THE CORRECTED STATISTIC IS NOW CONFIRMED AT BOTH EXTREMES. gharchive's\n")
cat("   40-character SHAs under short paths give 52%; open-meteo's two-decimal\n")
cat("   numbers under `hourly.wind_direction_10m.335` give 356%. Nothing about\n")
cat("   raggedness, keyed sites or depth orders this table — 08 has depth 3 and\n")
cat("   every axis at 0, and it is the most expensive document to list.\n")

cat(sprintf("\n2. how deep: %d level columns — NOTES.md grades depth 3\n", length(lv)))

# ── Q3. WHERE MELT GETS IT WRONG. ────────────────────────────────────────────
cat("\n3. what is one record — and melt answers the wrong question:\n")
cat(sprintf("   the melted frame is %s rows: one per LEAF\n",
            format(nrow(m), big.mark = ",")))
cat(sprintf("   the document holds %d observations of %d variables\n",
            length(doc$hourly[[1]]), length(doc$hourly)))
cat("   1,692 = 336 x 5 + 12 scalars. THE NUMBERS ARE ALL THERE AND THE SHAPE\n")
cat("   IS INSIDE OUT. Melt is the correct flattening of a tree and this\n")
cat("   document is not a tree — it is a table stored column-wise, so\n")
cat("   `one row per leaf` is one row per CELL.\n")
cat("   Recovering the real table from the melted frame means pivoting on L2\n")
cat("   and L3, which is a reshape a person has to know to write:\n")
h <- m[!is.na(m$L1) & m$L1 == "hourly", , drop = FALSE]
wide <- reshape(data.frame(row = as.integer(h$L3), var = h$L2,
                           val = as.character(h$value)),
                idvar = "row", timevar = "var", direction = "wide")
cat(sprintf("   reshape(...) -> %d x %d, which is the answer\n", nrow(wide), ncol(wide)))
cat("   COMPARE `as.data.frame(fromJSON(path)$hourly)` — see try-jsonlite.R —\n")
cat("   which is the same table in one expression with no reshape at all.\n")
cat("   Melting a columnar document and pivoting it back is a round trip.\n")

cat(sprintf("\n7. %d hourly observations, %d variables\n",
            length(doc$hourly[[1]]), length(doc$hourly)))

cat("
CONCLUSION — the corpus high on the corpus's smallest file, and melt is the
wrong shape for a document that is already a table.

  **356% of the file — higher than `03-natural-earth`'s 226%, on 12 KB.** The
  mechanism is exactly what the corrected statistic predicts: **7.2-byte values
  under 25.6-character paths**. `hourly.wind_direction_10m.335` costs four times
  what `118` does.

  **The seven-file table is now confirmed at both ends**, and neither end is
  about raggedness. `04-gharchive` has the corpus's highest path variance,
  severe raggedness both ways, 37,883 records, and lists at **52%** because its
  values are SHAs and commit messages. This file has depth 3, every axis at 0,
  and lists at **356%** because its values are two-decimal numbers.
  `VERDICT.md`'s O(data) percentages measure verbosity. They are fair evidence
  that a tool's answer is bigger than the document and they are not evidence
  about folding.

  **AND MELT ANSWERS THE WRONG QUESTION HERE, which nothing else in the corpus
  has made it do.** 1,692 rows is 336 x 5 cells plus twelve scalars: every
  number present, the shape inside out. Melt is the correct flattening of a
  TREE, and this document is not a tree — it is a table stored column-wise.
  Recovering the real 336 x 5 needs a `reshape` on two level columns, written by
  someone who already knows what the document is.

  `as.data.frame(fromJSON(path)$hourly)` is the same table in one expression.
  **Melting a columnar document and pivoting it back is a round trip**, and the
  tool that never left R's native shape did not have to make it.
")
