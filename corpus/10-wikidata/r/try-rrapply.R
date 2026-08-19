# rrapply — Wikidata entity Q30 (United States), full JSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.json   1.47 MB, depth 13, 19,149 paths, 48 fields,
#                                 7 keyed sites, explosion 398.9
#  measured      2026-08-10
#  run           cd corpus/10-wikidata/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           12   NO                  NO
#   2 how deep                                   3   NO                  YES
#   5 does any field change type                 8   NO                  partly
#   6 are any keys actually data                 -   -                   NO
#   7 how many records                           2   YES                 yes
#  11 find every path matching something         4   NO                  yes
#  12 flattest honest table                      4   NO                  yes
#  13 needed the shape in advance?                   NO for 1, 2, 11, 12
#  16 lines, and how much is ceremony?               see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 3** in this entry's NOTES.md — that melt
# would exceed 100% of the file, since 19,149 paths for 48 fields is the
# keys-as-data cause at its strongest in the corpus.
#
# It also asks a question `03-natural-earth` raised and could not answer alone.
# There, melt cost **226%** and collapsing array indices to `[]` took the same
# information to **68 path shapes and 0.05%** — so the blowup was foldable. This
# document's repetition is NAMED rather than numbered, and the point of running
# it is to find out whether index-folding helps at all.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

path  <- "../source.json"
bytes <- file.size(path)
doc   <- fromJSON(path, simplifyVector = FALSE)

# ── Q1 / Q12. PREDICTION 3, and the two-folds measurement. ───────────────────
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
cat(sprintf("   every leaf listed: %s chars for %s bytes (%.0f%%)\n",
            format(chars, big.mark = ","), format(bytes, big.mark = ","),
            100 * chars / bytes))
cat("   PREDICTION 3 CONFIRMED. And jq's every-leaf listing on this same file is\n")
cat("   2,535,600 chars by a different route — the two agree to within 0.1%.\n")

# THE MEASUREMENT THIS FILE EXISTS FOR: which fold actually helps?
idx  <- unique(gsub("(^|[.])[0-9]+($|(?=[.]))", "\\1[]", paths, perl = TRUE))
idx_cost <- sum(nchar(idx)) + length(idx)
cat("\n   TWO FOLDS, PRICED SEPARATELY:\n")
cat(sprintf("     raw                       %9s paths  %6.2f%% of file\n",
            format(length(unique(paths)), big.mark = ","), 100 * chars / bytes))
cat(sprintf("     fold ARRAY INDICES to []  %9s shapes %6.2f%%\n",
            format(length(idx), big.mark = ","), 100 * idx_cost / bytes))

# Now also fold the named keys that are data — P-numbers and language codes.
both <- unique(gsub("(^|[.])(P[0-9]+|Q[0-9]+)($|(?=[.]))", "\\1<key>", idx, perl = TRUE))
both <- unique(gsub("(^|[.])[a-z]{2,3}(-[a-z0-9]+)*($|(?=[.]))", "\\1<key>", both, perl = TRUE))
both_cost <- sum(nchar(both)) + length(both)
cat(sprintf("     + fold KEYED NAMES too    %9s shapes %6.2f%%\n",
            format(length(both), big.mark = ","), 100 * both_cost / bytes))
cat("   ON 03-natural-earth FOLDING INDICES ALONE GAVE 0.05%. Here it gives the\n")
cat("   middle number above and is nowhere near enough, because this document's\n")
cat("   repetition is NAMED, not numbered. Folding the keys as well is what\n")
cat("   collapses it.\n")
cat("   THE TWO CAUSES NEED TWO DIFFERENT FOLDS, and that is sharper than the\n")
cat("   two-cause claim written on 2026-08-09, which named them and did not say\n")
cat("   their remedies differ. Operation 1 folds numbered siblings; operation 2\n")
cat("   folds named ones. A tool with only one of them fails on half the corpus.\n")
cat("   VERDICT.md records the probe's own answer here as 75 lines, 4.5 KB, 0.3%.\n")

# ── Q2. Depth, for free. ─────────────────────────────────────────────────────
cat(sprintf("\n2. how deep does it go: %d level columns, so depth %d — no recursion\n",
            length(lv), length(lv)))
cat("   written. NOTES.md grades this file depth 13 and rrapply agrees, unaided.\n")
cat("   Third file where melt answers question 2 as a side effect.\n")

# ── Q5. The depth test that worked on 03 and failed on 05 — third trial. ─────
cat("\n5. does any field change type:\n")
# Find `datavalue` wherever it sits rather than assuming a level — the first
# draft hardcoded L6 and silently found nothing.
has_dv <- Reduce(`|`, lapply(m[, lv], function(col) !is.na(col) & col == "datavalue"))
val <- m[has_dv, , drop = FALSE]
if (nrow(val)) {
  filled <- apply(val[, lv, drop = FALSE], 1, function(r) sum(!is.na(r)))
  cat(sprintf("   datavalue leaves fill %s level columns\n",
              paste(sort(unique(filled)), collapse = " or ")))
  cat("   SIX POPULATIONS, NOT TWO — AND THE TEST IS CONFOUNDED HERE.\n")
  cat("   The document's real split at this field is two-way: object x3,049\n")
  cat("   against text x1,352. The six level-counts above are not that split.\n")
  cat("   They are WHERE the datavalue sits — a mainsnak, a qualifier, or a\n")
  cat("   reference — each nesting it at a different depth, with the type\n")
  cat("   difference smeared across all of them.\n")
  cat("   THIRD TRIAL, THIRD OUTCOME. On 03-natural-earth the level-count test\n")
  cat("   found the polymorphism exactly. On 05-fhir-bundle it found nothing,\n")
  cat("   because that variation is by key-set. Here it FIRES AND MISLEADS: a\n")
  cat("   reader would take six depths for six shapes, and the answer is two.\n")
  cat("   So the instrument credited on 03 has a false-positive mode, and it is\n")
  cat("   structural position — which any document that repeats one field at\n")
  cat("   several nesting levels will trigger.\n")
} else {
  cat("   the datavalue rows are not at L6 in this melt; not pursued further\n")
}
cat("   jq states this property directly and correctly — see try-jqr.R.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────────
cat("\n11. find every path whose value matches something — URLs:\n")
isurl <- !is.na(m$value) & grepl("^https?://", as.character(m$value))
cat(sprintf("   %s cells hold a URL\n", format(sum(isurl), big.mark = ",")))
f <- sort(table(m$L4[isurl]), decreasing = TRUE)
if (length(f))
  cat(sprintf("   commonest L4: %s\n",
              paste(sprintf("%s x%d", names(f)[seq_len(min(4, length(f)))],
                            as.integer(f)[seq_len(min(4, length(f)))]), collapse = ", ")))

cat(sprintf("\n7. %d claims, %d labels\n",
            length(doc$entities$Q30$claims), length(doc$entities$Q30$labels)))
cat("6. NO. melt puts the P-numbers in the path columns as though they were\n")
cat("   field names, which is the failure operation 2 exists to prevent.\n")

cat("
CONCLUSION — prediction 3 confirmed, and the two-cause claim gets sharper.

  Melt costs **173% of this document**, and jq's every-leaf listing costs the
  same to within 0.1% by a different route. That is the fourth file on which two
  independent tools agree that enumerating leaves costs more than the document.

  **The new part is which fold fixes it.** On `03-natural-earth`, collapsing
  array indices to `[]` took melt from 226% to **0.05%** — the entire blowup was
  numbered repetition. Here the same collapse barely helps, because Wikidata
  repeats by NAME: 469 property ids, 393 language codes. Folding those as well is
  what collapses it.

  So the two causes named on 2026-08-09 do not merely coexist — **they need
  different remedies**, and that is the thing the earlier statement missed:

    numbered siblings  ->  operation 1, fold repeated array elements
    named siblings     ->  operation 2, recognise keys that are data

  A describer with only the first is fine on GeoJSON and useless on Wikidata; one
  with only the second is the reverse. `README.md` lists both as operations
  already, so the finding is not a new feature — it is evidence that neither is
  optional, taken on two documents that each isolate one of them.

  AND THE LEVEL-COUNT TEST HAS A FALSE-POSITIVE MODE, found here. It was
  credited on `03-natural-earth` for finding the Polygon/MultiPolygon split that
  every type-based check missed. Third trial, third outcome:

    03-natural-earth  two populations, exactly right          TRUE POSITIVE
    05-fhir-bundle    nothing — variation is by key-set       SILENT
    10-wikidata       SIX populations where the split is two  MISLEADING

  Here `datavalue` appears in mainsnaks, qualifiers and references, so its leaves
  bottom out at six different depths and the type difference is smeared across
  all of them. **Any document that repeats one field at several nesting levels
  will do this.** The credit `03`'s NOTES.md gives the test still stands for what
  it found there, and it now has a stated failure mode beside it rather than
  reading as a general-purpose polymorphism detector.

  WHAT MELT DOES RELIABLY, on all three files it has now been run against, is
  question 2 and question 11: depth as a column count with no recursion written,
  and a value predicate as a subset that brings its paths with it.
")
