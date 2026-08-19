# rrapply — the SpaceX GraphQL API describing its own schema
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.json   143 KB, 108 types, depth 13, recursion 4,
#                                 94 paths, 22 fields, explosion 4.3, keyed 0
#  measured      2026-08-10
#  run           cd corpus/07-graphql-introspection/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           14   NO                  NO
#   2 how deep                                   2   NO                  YES
#   5 does any field change type                 9   NO                  WRONG
#   6 are any keys actually data                 -   -                   n/a
#   7 how many records                           2   YES                 yes
#  11 find every path matching something         4   NO                  yes
#  12 flattest honest table                      4   NO                  yes
#  13 needed the shape in advance?                   NO for 1, 2, 11, 12
#  16 lines, and how much is ceremony?               see the conclusion
#
#  Q5 is scored WRONG, not NO. NOTES.md grades this file `polymorphic 0`, so
#  every population the level-count test reports here is a false positive.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It is the **control** for the two-cause O(data) claim, and
# **prediction 1 in this entry's NOTES.md was FALSIFIED by it.** That prediction
# — committed before this file existed — said melt would come in under 100% of
# the document and be the cheapest of the five measured, because keys-as-data is
# 0 and the explosion ratio is 4.3.
#
# It came in at over 200%. The prediction that would hurt was written down and
# it happened, so the correction below is forced rather than chosen.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

path  <- "../source.json"
bytes <- file.size(path)
doc   <- fromJSON(path, simplifyVector = FALSE)

# ── Q1 / Q12. PREDICTION 1, AND IT IS WRONG. ─────────────────────────────────
cat("\n1/12. what is in here — melt every leaf to a row:\n")
m  <- rrapply(doc, how = "melt")
lv <- grep("^L", names(m), value = TRUE)
paths <- apply(m[, lv, drop = FALSE], 1,
               function(r) paste(r[!is.na(r)], collapse = "."))
chars <- sum(nchar(paths)) + length(paths)
idx   <- unique(gsub("(^|[.])[0-9]+($|(?=[.]))", "\\1[]", paths, perl = TRUE))
idx_cost <- sum(nchar(idx)) + length(idx)

cat(sprintf("   %s leaves, %s chars for %s bytes — %.1f%% OF THE FILE\n",
            format(nrow(m), big.mark = ","), format(chars, big.mark = ","),
            format(bytes, big.mark = ","), 100 * chars / bytes))
cat("   PREDICTION 1 FALSIFIED. It said under 100% and cheapest of five.\n")
cat("   The running table, all rrapply melt, as a share of each file:\n")
cat("     05-fhir-bundle       60%   keyed 0, short arrays\n")
cat("     09-stripe-openapi   141%   keyed 47\n")
cat("     10-wikidata         173%   keyed  7\n")
cat(sprintf("     07-graphql          %3.0f%%   keyed  0, explosion 4.3   <- HERE\n",
            100 * chars / bytes))
cat("     03-natural-earth    226%   keyed 0, 99,566 coordinate points\n")

cat("\n   WHY, AND IT IS A CORRECTION TO THE STATISTIC RATHER THAN TO THE CLAIM:\n")
cat(sprintf("     average value size   %5.1f bytes per leaf\n", bytes / nrow(m)))
cat(sprintf("     average path length  %5.1f chars per leaf\n", chars / nrow(m)))
cat("   The ratio printed above is path-chars over file-bytes, so it rises when\n")
cat("   paths are LONG and values are SHORT. This document is 13 levels deep\n")
cat("   with field names like `possibleTypes` and `deprecationReason`, holding\n")
cat("   mostly nulls and short enum strings. **The percentage is measuring\n")
cat("   verbosity as much as it is measuring failure to fold.**\n")

cat("\n   THE STATISTIC THAT ACTUALLY STATES THE CLAIM is the fold factor:\n")
cat(sprintf("     %s leaves collapse to %s path shapes — a %.0fx fold, %.2f%% of file\n",
            format(nrow(m), big.mark = ","), format(length(idx), big.mark = ","),
            nrow(m) / length(idx), 100 * idx_cost / bytes))
cat("   By THAT measure this file behaves exactly as the two-cause claim says:\n")
cat("   its repetition is numbered, so folding array indices alone collapses it,\n")
cat("   as on 03-natural-earth and unlike 10-wikidata where names had to go too.\n")
cat("   So the CLAIM survives and the TABLE above is a bad instrument for it.\n")
cat("   VERDICT.md's O(data) percentages should be read as `this tool's output\n")
cat("   is larger than the document`, which is true and useful, and NOT as\n")
cat("   `this document needs more folding`, which they do not measure.\n")

# ── Q2. ──────────────────────────────────────────────────────────────────────
cat(sprintf("\n2. how deep does it go: %d level columns, so depth %d — no recursion\n",
            length(lv), length(lv)))
cat("   written. NOTES.md grades depth 13 and rrapply agrees, unaided. Fourth\n")
cat("   file where melt answers question 2 as a side effect.\n")

# ── Q5. PREDICTION 4 — THE FALSE POSITIVE, ON A FILE GRADED polymorphic 0. ───
cat("\n5. does any field change type:\n")
has <- Reduce(`|`, lapply(m[, lv], function(col) !is.na(col) & col == "ofType"))
v <- m[has, , drop = FALSE]
filled <- apply(v[, lv, drop = FALSE], 1, function(r) sum(!is.na(r)))
cat(sprintf("   `ofType` leaves fill %s level columns\n",
            paste(sort(unique(filled)), collapse = ", ")))
cat("   PREDICTION 4 CONFIRMED, AND THIS IS THE CLEANEST CASE OF THE FAILURE.\n")
cat(sprintf("   %d distinct level-counts on a document NOTES.md grades\n",
            length(unique(filled))))
cat("   `polymorphic 0` and `heterogeneous 0`. Every population reported here\n")
cat("   is a FALSE POSITIVE by construction — there is no polymorphism to find.\n")
cat("   The cause is `ofType` being genuinely self-similar: NOTES.md records\n")
cat("   recursion at 4 sites, 2 and 4 levels deep, so the same field bottoms\n")
cat("   out at many depths for reasons of POSITION, not of type.\n")
cat("   Fourth trial of the level-count test, and the score is now:\n")
cat("     03-natural-earth  two populations, exactly right    TRUE POSITIVE\n")
cat("     05-fhir-bundle    silent — variation is by key-set  SILENT\n")
cat("     10-wikidata       six where the split is two        MISLEADING\n")
cat("     07-graphql        six where there is NO split       FALSE POSITIVE\n")
cat("   A test that fires on a document with nothing to find is not a detector.\n")
cat("   Its one success on 03 stands, and it is a coincidence of that file\n")
cat("   having no recursion, so depth there could only mean shape.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────────
cat("\n11. find every path whose value matches something:\n")
isurl <- !is.na(m$value) & grepl("^https?://", as.character(m$value))
cat(sprintf("   %d cells hold a URL\n", sum(isurl)))
dep <- !is.na(m$value) & as.character(m$value) == "TRUE" &
       !is.na(m$L6) & grepl("Deprecated", m$L6)
cat(sprintf("   %d cells are isDeprecated = TRUE\n", sum(dep)))
cat("   A value predicate over the melted frame, paths carried along. This\n")
cat("   works on every file it has been tried on.\n")

cat(sprintf("\n7. %d types\n", length(doc$data$`__schema`$types)))
cat("6. n/a — NOTES.md grades this file keys-as-data 0.\n")

cat("
CONCLUSION — a falsified prediction, and it corrects a statistic this project
has been quoting since the first Python backfill.

  **Prediction 1 said melt would be under 100% here and the cheapest of five.
  It is over 200%** — on the document with keys-as-data 0 and an explosion ratio
  of 4.3, which by the two-cause claim should have been the easy case.

  The reason is arithmetic rather than structural. The percentage is
  path-characters over file-bytes, so it rises whenever paths are long and
  values are short. This file is 13 levels deep with names like `possibleTypes`
  and `deprecationReason`, and its values are mostly nulls and short enum
  strings. **The statistic is measuring verbosity as much as it is measuring a
  failure to fold.**

  **The claim itself is untouched, and the right statistic says so plainly:
  6,504 leaves collapse to 73 path shapes by folding array indices alone — an
  89x fold, 2.57% of the file.** That is the same behaviour as
  `03-natural-earth`, whose repetition is also numbered, and unlike
  `10-wikidata`, where the names had to be folded too. So this document IS the
  control it was chosen to be; the measurement that disagreed was the wrong one.

  **What should change:** `VERDICT.md`'s O(data) percentages are fair evidence
  for *this tool's answer is bigger than the document* — which is the claim they
  are cited for — and they are NOT evidence for *this document needs more
  folding*. Depth and name length move them, and this file moves them a long way
  with nothing to fold that the other files do not also have.

  AND PREDICTION 4 LANDED, on the cleanest possible test. `ofType` leaves sit at
  six different level-counts on a document graded `polymorphic 0`. Every
  population is a false positive, because the field is genuinely recursive and
  depth here means position rather than shape. Fourth trial, and the level-count
  test now reads true-positive, silent, misleading, false-positive. **Its one
  success needed a document with no recursion, and that is a narrow condition.**
")
