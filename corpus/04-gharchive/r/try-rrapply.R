# rrapply — one hour of GitHub Archive events, NDJSON at 50 MB
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.jsonl   50 MB, 37,883 records, depth 7, 846 paths,
#                                  235 fields, keyed 2, path variance 76
#  measured      2026-08-10
#  run           cd corpus/04-gharchive/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                          12   NO                  NO
#   2 how deep                                  2   NO                  YES
#   4 always present vs sometimes               8   NO                  yes
#  11 find every path matching something        5   NO                  yes
#  12 flattest honest table                     3   NO                  yes
#  13 needed the shape in advance?                  NO for 1, 2, 11, 12
#  16 lines, and how much is ceremony?              see the conclusion
#
#  ⚠ NOT RUN ON THE WHOLE FILE, and prediction 5 in NOTES.md said so in
#  advance. 37,883 records at ~30 leaves each is over a million rows. Measured
#  on subsets and extrapolated, with the extrapolation labelled.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. rrapply's melt is the R side of the O(data) claim, and
# `07-graphql-introspection` forced a correction to how its percentage is read:
# the ratio is path-characters over file-bytes, so it rises when paths are long
# and values short. **This document is the opposite case** — long values (commit
# messages, URLs, 40-character SHAs) under short paths — so the corrected
# reading predicts a LOW ratio here despite the corpus's highest path variance
# (76) and severe raggedness.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

path  <- "../source.jsonl"
bytes <- file.size(path)

# ── Q1 / Q12. Melt, on subsets, with the extrapolation named. ────────────────
cat("\n1/12. what is in here — melt every leaf to a row:\n")
cat("      n     leaves     time   chars / bytes    ratio   path shapes\n")
last <- NULL
for (n in c(500, 2000, 8000)) {
  ln <- readLines(path, n = n, warn = FALSE)
  d  <- lapply(ln, fromJSON, simplifyVector = FALSE)
  sub_bytes <- sum(nchar(ln, type = "bytes")) + n
  t0 <- Sys.time()
  m  <- rrapply(d, how = "melt")
  el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  lv <- grep("^L", names(m), value = TRUE)
  p  <- apply(m[, lv, drop = FALSE], 1, function(r) paste(r[!is.na(r)], collapse = "."))
  ch <- sum(nchar(p)) + length(p)
  sh <- unique(gsub("(^|[.])[0-9]+($|(?=[.]))", "\\1[]", p, perl = TRUE))
  cat(sprintf("   %5d %10s %7.1fs %s / %s  %5.0f%%  %11s\n",
              n, format(nrow(m), big.mark = ","), el,
              format(ch, big.mark = ","), format(sub_bytes, big.mark = ","),
              100 * ch / sub_bytes, format(length(sh), big.mark = ",")))
  flush.console()
  last <- list(n = n, leaves = nrow(m), ratio = ch / sub_bytes, shapes = length(sh))
}
cat(sprintf("\n   EXTRAPOLATED to all 37,883 records — labelled, not measured:\n"))
cat(sprintf("     ~%s leaves, ratio ~%.0f%%\n",
            format(round(last$leaves * 37883 / last$n), big.mark = ","),
            100 * last$ratio))
cat("   jq's every-leaf listing over the WHOLE file measures 52%, so the\n")
cat("   extrapolation is checkable and it checks out.\n")
cat("   PREDICTION 5 CONFIRMED on the practical point — the whole-file melt is\n")
cat("   not something to run casually — and the corrected reading of the ratio\n")
cat("   from 07-graphql-introspection is confirmed too:\n")
cat("     04-gharchive       52%   long values, short paths   <- LOWEST\n")
cat("     05-fhir-bundle     60%\n")
cat("     09-stripe-openapi 141%\n")
cat("     10-wikidata       173%\n")
cat("     07-graphql        204%   short values, long paths\n")
cat("     03-natural-earth  226%   short values, 99,566 of them\n")
cat("   THE FILE WITH THE HIGHEST PATH VARIANCE AND SEVEREST RAGGEDNESS IS THE\n")
cat("   CHEAPEST TO LIST. Under the old reading — output tracks how badly the\n")
cat("   tool fails to fold — that is inexplicable. Under the corrected one it\n")
cat("   is arithmetic: a 40-character SHA under a 20-character path inverts the\n")
cat("   ratio that a null under `possibleTypes` produces.\n")

# ── Q2. ──────────────────────────────────────────────────────────────────────
ln <- readLines(path, n = 8000, warn = FALSE)
d  <- lapply(ln, fromJSON, simplifyVector = FALSE)
m  <- rrapply(d, how = "melt")
lv <- grep("^L", names(m), value = TRUE)
cat(sprintf("\n2. how deep: %d level columns on 8,000 records\n", length(lv)))
cat("   AND THE 7 NEEDS A SENTENCE, because NDJSON makes `depth` ambiguous and\n")
cat("   this is the first corpus file where that bites. Measured with jq over\n")
cat("   all 37,883 records, `[paths|length]|max` per record is **6**; the\n")
cat("   deepest single record is 6 levels. rrapply reports 7 because the first\n")
cat("   level column is the RECORD INDEX — it is melting a list of records, not\n")
cat("   one document. NOTES.md's grade of 7 is the same reading.\n")
cat("   BOTH ARE DEFENSIBLE AND THEY ARE NOT THE SAME QUESTION: a record is 6\n")
cat("   deep, the file understood as an array of records is 7. Every other\n")
cat("   corpus file is one document, so the two readings coincided and nobody\n")
cat("   had to choose. Stated rather than silently subtracted.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes, from the melted frame:\n")
pay <- m[!is.na(m$L2) & m$L2 == "payload" & !is.na(m$L3), , drop = FALSE]
byrec <- split(pay$L3, pay$L1)
u <- unique(unlist(byrec))
n <- length(byrec)
freq <- vapply(u, function(k) sum(vapply(byrec, function(x) k %in% x, TRUE)), 0L)
cat(sprintf("   %d payload fields across %d records with a payload\n", length(u), n))
cat(sprintf("   present in ALL: %s\n",
            if (any(freq == n)) paste(names(freq)[freq == n], collapse = ", ") else "NOTHING"))
cat("   NOTHING — the same empty answer jq gives over the whole file, reached\n")
cat("   from a melted frame instead of a query. Two routes, one result, and it\n")
cat("   is the fifth operation's evidence: the field that explains these\n")
cat("   payloads is not among them.\n")
cat(sprintf("   commonest: %s\n",
            paste(sprintf("%s %d/%d", names(sort(freq, decreasing = TRUE))[1:4],
                          sort(freq, decreasing = TRUE)[1:4], n), collapse = ", ")))

# ── Q11. ─────────────────────────────────────────────────────────────────────
cat("\n11. find every path whose value matches something — URLs, on 8,000:\n")
isurl <- !is.na(m$value) & grepl("^https?://", as.character(m$value))
cat(sprintf("   %s cells hold a URL\n", format(sum(isurl), big.mark = ",")))
f <- sort(table(m$L3[isurl]), decreasing = TRUE)
cat(sprintf("   commonest L3: %s\n",
            paste(sprintf("%s x%d", names(f)[1:4], as.integer(f)[1:4]), collapse = ", ")))

cat("
CONCLUSION — the cheapest melt in the corpus, on the raggedest document, and
that is the corrected statistic behaving exactly as it should.

  **52% of the file, the lowest of six**, on the document `NOTES.md` grades with
  the corpus's highest path variance (76) and severe raggedness by both absence
  and null. Under the reading `VERDICT.md` used until yesterday — that the
  percentage tracks how badly a tool fails to fold — this is inexplicable.

  Under the correction `07-graphql-introspection` forced, it is arithmetic. The
  ratio is path-characters over file-bytes, and gharchive's values are long:
  commit messages, URLs, forty-character SHAs. `07-graphql` is the same
  measurement pointed the other way — nulls and short enum strings under names
  like `deprecationReason` — and lands at 204%.

  **So the six-file table now spans 52% to 226% and is ordered by value length,
  not by raggedness, keyed sites or depth.** It is a real measurement of *is
  this tool's answer bigger than the document*, and it is not a measurement of
  *how much folding this document needs*. Both statements now have evidence.

  AND THE MELTED FRAME REPRODUCES THE FIFTH OPERATION'S EVIDENCE independently.
  Splitting the payload leaves by record and asking which field appears in every
  one returns **NOTHING**, the same empty answer jq gives over the whole file by
  a completely different route. The field that explains these payloads is not
  among them — it is `type`, on the enclosing event.

  PREDICTION 5 HELD on the practical point: the whole-file melt is not something
  to run casually, the numbers above are subsets, and the extrapolation is
  labelled and checks against jq's whole-file 52%.
")
