# rrapply — the Stripe OpenAPI specification
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
#  measured      2026-08-09
#  run           cd corpus/09-stripe-openapi/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             8   NO                  NO
#   6 are any keys actually data                  -   -                   CANNOT
#   7 how many records                            2   YES                 yes
#  12 flattest honest table                       5   NO                  yes
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `rrapply(how = "melt")` is one of the six describers
# `README.md` names, and `VERDICT.md` records it answering **3,112** for
# `01-npm-registry` where the truth is about 40 fields. This is the same
# question on a file ten times the size with 47 keyed sites against npm's 6,
# and it is the direct R counterpart to the Python numbers — `pydash` 157% and
# `ijson` 172% of the document's own size.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
bytes <- file.size("../source.json")

cat("\n1. what is in here — melt every leaf to a row:\n")
t0 <- Sys.time()
m <- rrapply(doc, how = "melt")
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("   rrapply(how='melt') -> %s rows x %d cols in %.1f s\n",
            format(nrow(m), big.mark = ","), ncol(m), el))

# The describer claim is about SIZE, so measure the answer the way the Python
# attempts measured theirs: characters, against the document's own bytes.
paths <- apply(m[, seq_len(ncol(m) - 1), drop = FALSE], 1,
               function(r) paste(r[!is.na(r)], collapse = "."))
chars <- sum(nchar(paths)) + length(paths)
cat(sprintf("   listing every path costs %s chars for a %s-byte file (%.0f%%)\n",
            format(chars, big.mark = ","), format(bytes, big.mark = ","),
            100 * chars / bytes))
u <- unique(paths)
cat(sprintf("   %s distinct paths; %s chars to list those (%.0f%%)\n",
            format(length(u), big.mark = ","),
            format(sum(nchar(u)) + length(u), big.mark = ","),
            100 * (sum(nchar(u)) + length(u)) / bytes))
cat("   VERDICT.md records rrapply answering 3,112 on 01-npm-registry, where\n")
cat("   the truth is about 40 fields. Compare the number above.\n")

cat(sprintf("\n7. schemas: %d   paths: %d\n",
            length(doc$components$schemas), length(doc$paths)))

cat("\n12. the melted frame IS the flattest honest table, and that is the point:\n")
pv <- utils::head(m[, c(1, 2, ncol(m))], 3)
pv$value <- substr(as.character(pv$value), 1, 46)
print(pv)
cat("   Every row is one leaf. Nothing is lost and nothing is answered:\n")
cat("   the table has as many rows as the document has values, which is the\n")
cat("   O(data) shape `README.md` names.\n")

cat("\n6. CANNOT. rrapply melts keys into path columns and has no notion that a\n")
cat("   key might be data. On this file the melted paths contain 1,440 schema\n")
cat("   names and 416 URL paths as though they were field names.\n")

cat("
CONCLUSION.

  rrapply does exactly what it says and the output is proportional to the DATA.
  That is not a defect in rrapply — melting is what it is for — it is the
  measurement `README.md` predicts, taken in R on the corpus's worst case, and
  it now sits beside the Python numbers rather than resting on npm alone.
")
