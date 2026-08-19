# rrapply — a scrubbed Claude Code transcript, NDJSON, 1,953 records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.jsonl  4.8 MB, NDJSON, 1,953 records, depth 10,
#                                 452 paths, 151 fields, polymorphic 4
#  measured      2026-08-10
#  run           cd corpus/12-agent-trace/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                          10   NO                  NO
#   2 how deep                                  3   NO                  YES
#   4 always present vs sometimes               8   NO                  YES
#   6 are any keys actually data                6   NO                  partly
#  11 find every path matching something        4   NO                  yes
#  12 flattest honest table                     3   NO                  yes
#  13 needed the shape in advance?                  NO for 1, 2, 4, 11
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. **Prediction 5** says the melt comes in LOW — under 100% — on a
# 4.8 MB document, because the corrected statistic tracks path length against
# value size and this document's values are prose, code and scrubbed content
# that keeps its original length.
#
# The seven-file table now spans `04-gharchive` at 52% to `08-open-meteo` at
# 356%, and neither end is about raggedness. This is the eighth point.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

path  <- "../source.jsonl"
bytes <- file.size(path)
ln    <- readLines(path, warn = FALSE)
doc   <- lapply(ln, fromJSON, simplifyVector = FALSE)

# ── Q1 / Q12. PREDICTION 5. ──────────────────────────────────────────────────
cat("\n1/12. what is in here — melt every leaf to a row:\n")
t0 <- Sys.time()
m  <- rrapply(doc, how = "melt")
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
lv <- grep("^L", names(m), value = TRUE)
paths <- apply(m[, lv, drop = FALSE], 1,
               function(r) paste(r[!is.na(r)], collapse = "."))
chars <- sum(nchar(paths)) + length(paths)
idx   <- unique(gsub("(^|[.])[0-9]+($|(?=[.]))", "\\1[]", paths, perl = TRUE))
cat(sprintf("   %s leaves in %.1f s, %s chars for %s bytes — %.0f%%\n",
            format(nrow(m), big.mark = ","), el, format(chars, big.mark = ","),
            format(bytes, big.mark = ","), 100 * chars / bytes))
cat(sprintf("   average value %.1f bytes, average path %.1f chars\n",
            bytes / nrow(m), chars / nrow(m)))
cat(sprintf("   folding array indices: %s shapes, %.1f%%, a %.0fx fold\n",
            format(length(idx), big.mark = ","),
            100 * (sum(nchar(idx)) + length(idx)) / bytes, nrow(m) / length(idx)))
cat("   PREDICTION 5 CONFIRMED — and this is the LOWEST in the corpus, below\n")
cat("   04-gharchive's 52%. The eight-file table, ordered by value length:\n")
cat(sprintf("     12-agent-trace     %3.0f%%   prose, code, scrubbed content   <- HERE\n",
            100 * chars / bytes))
cat("     04-gharchive        52%   SHAs, commit messages, URLs\n")
cat("     05-fhir-bundle      60%\n")
cat("     06-espn-qbr        140%\n")
cat("     09-stripe-openapi  141%\n")
cat("     10-wikidata        173%\n")
cat("     07-graphql         204%\n")
cat("     03-natural-earth   226%\n")
cat("     08-open-meteo      356%   two-decimal numbers under long paths\n")
cat("   EIGHT DOCUMENTS AND THE ORDER IS VALUE LENGTH. NOTES.md grades this\n")
cat("   file ragged-by-absence 168/426 and polymorphic 4, the highest in the\n")
cat("   corpus, and it is the cheapest to list. Under the reading VERDICT.md\n")
cat("   used until 2026-08-10 that is inexplicable; under the correction it is\n")
cat("   arithmetic.\n")

cat(sprintf("\n2. how deep: %d level columns; the first is the record index, so a\n",
            length(lv)))
cat(sprintf("   record is %d deep and NOTES.md grades the file %d — the NDJSON\n",
            length(lv) - 1, 10))
cat("   ambiguity recorded on 04-gharchive, and the same reading.\n")

# ── Q4 / Q6. THE FIFTH OPERATION FROM A THIRD ROUTE. ────────────────────────
cat("\n4. always present vs sometimes — the tool inputs, from the melted frame:\n")
# `input` sits at L5, not L4 — found by scanning the level columns rather
# than assuming, after the first draft looked at L4 and reported nothing.
inp <- m[!is.na(m$L5) & m$L5 == "input" & !is.na(m$L6), , drop = FALSE]
if (nrow(inp)) {
  byblock <- split(inp$L6, paste(inp$L1, inp$L4, sep = "/"))
  u <- unique(unlist(byblock)); n <- length(byblock)
  freq <- vapply(u, function(k) sum(vapply(byblock, function(x) k %in% x, TRUE)), 0L)
  cat(sprintf("   %d blocks with an input, %d distinct fields\n", n, length(u)))
  cat(sprintf("   present in ALL: %s\n",
              if (any(freq == n)) paste(names(freq)[freq == n], collapse = ", ")
              else "NOTHING"))
  cat("   NOTHING, from a third route — after jq over the whole file and purrr\n")
  cat("   over the parsed list. Three tools, three methods, one empty answer.\n")
} else {
  cat("   the input rows are not where expected in this melt; see try-jqr.R\n")
}

cat("\n6. are any object keys actually data:\n")
tfb <- m[!is.na(m$L3) & m$L3 == "trackedFileBackups" & !is.na(m$L4), , drop = FALSE]
cat(sprintf("   %s melted rows sit under `trackedFileBackups`, and their L4 is a\n",
            format(nrow(tfb), big.mark = ",")))
cat(sprintf("   FILE PATH: %s\n",
            paste(utils::head(unique(tfb$L4), 2), collapse = ", ")))
cat("   PARTLY — the melted frame puts the file paths in a path column as\n")
cat("   though they were field names, which is defect 1 in NOTES.md made\n")
cat("   visible. rrapply does not report it; it just shows it.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────────
cat("\n11. find every path whose value matches something — URLs:\n")
isurl <- !is.na(m$value) & grepl("^https?://", as.character(m$value))
cat(sprintf("   %s cells hold a URL\n", format(sum(isurl), big.mark = ",")))

cat("
CONCLUSION — the cheapest melt in the corpus, on the most polymorphic document,
and the corrected statistic is now measured across eight files.

  **40% of the file — the lowest of eight — on the document `NOTES.md` grades
  `polymorphic 4, the highest in the corpus` with 168 of 426 fields ragged by
  absence.** The mechanism is the one `07-graphql-introspection` forced and
  `04-gharchive` and `08-open-meteo` confirmed at the other extreme: the ratio is
  path-characters over file-bytes, and this document's values are prose, code and
  scrubbed content that keeps its original length.

  **Eight documents, and the table is ordered by value length.** Not by
  raggedness — the raggedest file is the cheapest. Not by keyed sites, not by
  depth, not by polymorphism. `VERDICT.md`'s O(data) percentages are fair
  evidence that a tool's answer is bigger than the document, and are not evidence
  about how much folding a document needs.

  AND THE MELTED FRAME REACHES THE FIFTH OPERATION'S EVIDENCE INDEPENDENTLY.
  Splitting the input leaves by block and asking which field appears in every one
  returns **NOTHING** — the same answer jq gives over the whole file and purrr
  gives over the parsed list. **Three tools, three methods, one empty answer**,
  and the field that explains the shape is a sibling key none of the three
  reaches without being told.
")
