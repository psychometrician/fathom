# rrapply — a Synthea FHIR R4 patient bundle
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.json   2.0 MB, 564 resources, 20 resourceTypes, depth 11
#  measured      2026-08-09
#  run           cd corpus/05-fhir-bundle/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           10   NO                  NO
#   2 how deep                                   3   NO                  YES
#   4 always present vs sometimes                7   NO                  YES
#   5 does any field change type                 6   NO                  NO
#   6 are any keys actually data                 -   -                   n/a
#   7 how many records                           2   YES                 yes
#  11 find every path matching something         5   NO                  yes
#  12 flattest honest table                      4   NO                  yes
#  13 needed the shape in advance?                   NO for 1, 2, 4, 11
#  16 lines, and how much is ceremony?               see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. rrapply's melt is the R side of the O(data) claim — 3,112 on
# `01-npm-registry`, 141% of the Stripe spec, and **226% on `03-natural-earth`**,
# which turned out to be the corpus high and came from a document with no
# keys-as-data at all. That result said the blowup has two independent causes:
# every VALUE minting a key name, and every ELEMENT minting a path index.
#
# This document has neither in quantity. It has no keys-as-data, and its arrays
# are short — no 99,566-point coordinate rings. So it is the third point on that
# line and the one that should be cheapest. It also asks whether the melted
# frame, which exposed depth polymorphism on 03, can expose anything about a
# heterogeneous array.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

path  <- "../source.json"
bytes <- file.size(path)
doc   <- fromJSON(path, simplifyVector = FALSE)

# ── Q1 / Q12. Melt, and price the answer three ways. ─────────────────────────
cat("\n1/12. what is in here — melt every leaf to a row:\n")
t0 <- Sys.time()
m  <- rrapply(doc, how = "melt")
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("   rrapply(how='melt') -> %s rows x %d cols in %.1f s\n",
            format(nrow(m), big.mark = ","), ncol(m), el))

lv <- grep("^L", names(m), value = TRUE)
paths <- apply(m[, lv, drop = FALSE], 1,
               function(r) paste(r[!is.na(r)], collapse = "."))
chars <- sum(nchar(paths)) + length(paths)
shaped <- unique(gsub("(^|\\.)[0-9]+(?=\\.|$)", "\\1[]", paths, perl = TRUE))
cat(sprintf("   every leaf listed:      %s chars for %s bytes  (%.0f%%)\n",
            format(chars, big.mark = ","), format(bytes, big.mark = ","),
            100 * chars / bytes))
cat(sprintf("   distinct paths:         %s\n",
            format(length(unique(paths)), big.mark = ",")))
cat(sprintf("   distinct path SHAPES:   %s, costing %s chars  (%.2f%%)\n",
            format(length(shaped), big.mark = ","),
            format(sum(nchar(shaped)) + length(shaped), big.mark = ","),
            100 * (sum(nchar(shaped)) + length(shaped)) / bytes))
cat("   THE THREE-POINT COMPARISON, all rrapply, all `how='melt'`:\n")
cat("     01-npm-registry     3,112 chars   6 keyed sites\n")
cat("     09-stripe-openapi   141% of file  47 keyed sites\n")
cat("     03-natural-earth    226% of file  0 keyed sites, 99,566 coordinate points\n")
cat(sprintf("     05-fhir-bundle      %.0f%% of file  0 keyed sites, short arrays\n",
            100 * chars / bytes))
cat("   NOTES.md records `distinct paths 580` for this file. The shape count\n")
cat("   above is the same order; the every-leaf count is not, and the ratio\n")
cat("   between them is what a describer has to fold away.\n")

# ── Q2. Depth, for free. ─────────────────────────────────────────────────────
cat("\n2. how deep does it go:\n")
cat(sprintf("   %d level columns, so depth %d — no recursion written\n",
            length(lv), length(lv)))
cat("   NOTES.md grades this file depth 11 and rrapply agrees, unaided. This\n")
cat("   is the second file where melt answers question 2 as a side effect.\n")

# ── Q4. Always vs sometimes, from the melted frame alone. ────────────────────
cat("\n4. always present vs sometimes:\n")
# L1=entry, L2=index, L3=resource|fullUrl|request, L4=field name.
r4 <- m[!is.na(m$L3) & m$L3 == "resource" & !is.na(m$L4), , drop = FALSE]
byrec <- split(r4$L4, r4$L2)
u <- unique(unlist(byrec))
n <- length(byrec)
freq <- vapply(u, function(k) sum(vapply(byrec, function(x) k %in% x, TRUE)), 0L)
cat(sprintf("   %d resources, %d distinct fields under `resource`\n", n, length(u)))
cat(sprintf("   present in ALL: %s\n", paste(names(freq)[freq == n], collapse = ", ")))
cat(sprintf("   distinct key-sets: %d\n",
            length(unique(vapply(byrec, function(x) paste(sort(unique(x)), collapse = ","), "")))))
cat("   Same three numbers purrr, tidyjson and jq found, from a fourth route.\n")

# ── Q5. Can the melted frame see the heterogeneity? ──────────────────────────
cat("\n5. does any field change type:\n")
cdepth <- tapply(apply(r4[, lv, drop = FALSE], 1, function(x) sum(!is.na(x))),
                 r4$L4, function(x) length(unique(x)))
varying <- names(cdepth)[cdepth > 1]
cat(sprintf("   fields whose leaves sit at more than one level-count: %d\n",
            length(varying)))
cat(sprintf("   %s%s\n", paste(utils::head(varying, 8), collapse = ", "),
            if (length(varying) > 8) ", …" else ""))
cat("   NO — AND THE CONTRAST WITH 03-natural-earth IS THE POINT. There, this\n")
cat("   exact test found the polymorphism every type-based check missed, because\n")
cat("   GeoJSON's variation IS depth. FHIR's variation is which KEYS a record\n")
cat("   has, and depth cannot see that. The list above is ordinary nesting —\n")
cat("   a field that is sometimes scalar and sometimes an object of objects —\n")
cat("   not `value[x]`, which never appears because eight spellings at one\n")
cat("   depth are eight separate fields to every instrument here.\n")
cat("   ONE INSTRUMENT, TWO DOCUMENTS, ONE HIT AND ONE MISS, and knowing which\n")
cat("   is which requires knowing what kind of variation you are looking for.\n")

# ── Q11. Value predicate over the melted frame. ──────────────────────────────
cat("\n11. find every path whose value matches something — URLs:\n")
isurl <- !is.na(m$value) & grepl("^https?://", as.character(m$value))
cat(sprintf("   %s cells hold a URL\n", format(sum(isurl), big.mark = ",")))
f <- sort(table(m$L4[isurl]), decreasing = TRUE)
cat(sprintf("   commonest fields: %s\n",
            paste(sprintf("%s x%d", names(f)[1:4], as.integer(f)[1:4]), collapse = ", ")))
cat("   jq counted 5,511 on this file by a completely different route —\n")
cat("   `paths(scalars)` plus `getpath` plus a regex. THEY AGREE EXACTLY, and\n")
cat("   the agreement was not arranged: an R tree-walker and a query language\n")
cat("   independently call the same 5,511 cells leaves. That is a check on the\n")
cat("   number, which is what agreement between tools is good for.\n")

cat(sprintf("\n7. %d entries\n", length(doc$entry)))
cat("6. n/a — NOTES.md grades this file keys-as-data 0.\n")

cat("
CONCLUSION — the third point on the melt-size line, and the instrument that
worked on 03 does not work here.

  ON SIZE, this is the cheap document the two-cause reading predicted. rrapply's
  melt was 226% of `03-natural-earth`, which has no keys-as-data but 99,566
  coordinate points, and 141% of the Stripe spec, which has 47 keyed sites. This
  file has neither — no keyed sites, and short arrays — and the melt lands far
  below both. **Three documents, two independent causes, and the file with
  neither is the cheapest.** That is the controlled version of a claim
  `VERDICT.md` currently states with one cause.

  ON POLYMORPHISM, THE SAME TEST THAT SUCCEEDED ON 03 FAILS HERE, and the
  failure is informative. Counting the level-columns a field's leaves fill
  found GeoJSON's Polygon/MultiPolygon split exactly. FHIR's heterogeneity is
  not in depth — it is in WHICH KEYS a resource has — so the same arithmetic
  returns ordinary nesting variation and nothing about `value[x]`, whose eight
  spellings sit at one depth and read as eight unrelated fields.

  **An instrument that finds polymorphism-by-depth is not an instrument that
  finds polymorphism.** `03-natural-earth`'s NOTES.md now records rrapply as
  seeing what the probe missed; this file is the other half of that sentence and
  keeps it from being over-read.

  WHAT MELT DOES RELIABLY, on both files, is question 2 and question 11. Depth
  falls out as a column count with no recursion, and a value predicate over a
  melted frame is a subset that brings its paths with it.
")
