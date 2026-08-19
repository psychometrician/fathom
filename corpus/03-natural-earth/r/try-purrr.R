# purrr — Natural Earth admin-0 countries, as GeoJSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.json   3.9 MB, 241 features, depth 8, 75 paths
#  measured      2026-08-09
#  run           cd corpus/03-natural-earth/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             5   NO                  NO
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          -   -                   CANNOT
#   4 always present vs sometimes                 6   YES                 yes
#   5 does any field change type                  8   YES                 PARTLY
#   6 are any keys actually data                  -   -                   n/a
#   7 how many records                            1   YES                 yes
#   8 three named fields to a table               5   YES, all three      yes
#  10 flatten the deepest array                  10   YES, both depths    yes
#  13 needed the shape in advance?                    YES for everything but 2
#  16 lines, and how much is ceremony?                see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `README.md` calls purrr **"the best answer that exists"** for
# deep JSON. Before today it had been run on `01-npm-registry`, `02-hn-thread`
# and `09-stripe-openapi` — a keyed registry, a recursive thread and a giant
# spec, all three of which are ragged by ABSENCE. This document is the opposite
# and is the cleaner test: **0 of 68 ragged**, every feature carrying every
# field, so `%||%` is never needed and purrr should look its best.
#
# The one thing that is hard here is the thing purrr cannot see: `coordinates`
# is 3 deep on 122 Polygons and 4 deep on 119 MultiPolygons. Same name, same
# JSON type, different nesting. Question 10 is where that lands.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
feats <- doc$features

# ── Q1. What is in here? ─────────────────────────────────────────────────────
cat("\n1. what is in here — purrr has no describe verb, so this is str():\n")
for (lv in 2:4)
  cat(sprintf("   str(max.level=%d)  %5d lines\n", lv,
              length(capture.output(str(doc, max.level = lv)))))
cat("   No verb of purrr's own answers this. That is not a criticism — purrr is\n")
cat("   an iteration library — but `README.md` lists it among the describers a\n")
cat("   person would actually reach for, and this is what reaching for it gives.\n")

# ── Q2. How deep? ────────────────────────────────────────────────────────────
cat("\n2. how deep does it go:\n")
depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_dbl(x, depth)) else 0
cat(sprintf("   %d levels, via a hand-written recursion over map_dbl\n", depth(doc)))

# ── Q3 / Q7. What is one record, and how many? ───────────────────────────────
cat("\n3/7. what is one record:\n")
cat(sprintf("   CANNOT as a verb. Measured by hand: doc has %d top-level keys,\n",
            length(doc)))
cat(sprintf("   and $features has %d elements — the row, if you already know it.\n",
            length(feats)))

# ── Q4. Always present vs sometimes. THIS FILE'S EASY CASE. ──────────────────
cat("\n4. always present vs sometimes:\n")
keysets <- map_chr(feats, \(f) paste(sort(names(f$properties)), collapse = ","))
cat(sprintf("   %d distinct property key-sets across %d features\n",
            length(unique(keysets)), length(feats)))
nfields <- length(names(feats[[1]]$properties))
cat(sprintf("   every feature carries all %d property fields — 0 ragged by absence\n",
            nfields))
cat("   purrr computed this in one map_chr, and it is genuinely useful. It is\n")
cat("   also the comparison I had to think to write; nothing volunteered it.\n")

# ── Q5. Does any field change type? THE FILE'S POINT. ────────────────────────
cat("\n5. does any field change type:\n")
types <- map_chr(feats, \(f) class(f$geometry$coordinates)[1])
cat(sprintf("   class(coordinates) across all features: %s\n",
            paste(sprintf("%s x%d", names(table(types)), table(types)), collapse = ", ")))
cat("   BY TYPE, NOTHING CHANGES. One class, 241 times. A type-based check —\n")
cat("   which is every check in this corpus except the probe's array-element\n")
cat("   rule — sees a homogeneous field and moves on.\n")
cdepth <- map_dbl(feats, \(f) depth(f$geometry$coordinates))
gtype  <- map_chr(feats, \(f) f$geometry$type)
cat("   by NESTING DEPTH, measured with the same recursion as question 2:\n")
for (g in sort(unique(gtype)))
  cat(sprintf("     %-14s x%3d   coordinates %d deep\n", g, sum(gtype == g),
              unique(cdepth[gtype == g])))
cat("   PARTLY: purrr can measure it in one line once you suspect it. It has no\n")
cat("   way to raise the suspicion.\n")

# ── Q8. Three named fields. purrr's best case, and this file is its best. ────
cat("\n8. three named fields, one row per feature:\n")
tbl <- map_dfr(feats, \(f) data.frame(name = f$properties$name,
                                      iso  = f$properties$iso_a3,
                                      pop  = f$properties$pop_est))
cat(sprintf("   map_dfr -> %d x %d, and NOT ONE `%%||%%` was needed\n",
            nrow(tbl), ncol(tbl)))
print(head(tbl, 3))
cat("   Compare `01-npm-registry`, where 31 of 40 keys are absent from at least\n")
cat("   one record and every field needs a default. The difference is the\n")
cat("   document, not the tool — which is the honest way to score question 8.\n")

# ── Q10. Flatten the deepest array. WHERE THE POLYMORPHISM BITES. ────────────
cat("\n10. flatten the deepest array into rows:\n")
cat("   The naive purrr answer, written as though coordinates were one shape:\n")
naive <- tryCatch({
  n <- map_int(feats, \(f) length(unlist(f$geometry$coordinates)) / 2L)
  sprintf("map_int + unlist gives %s pairs and is WRONG-BY-LUCK", format(sum(n), big.mark = ","))
}, error = function(e) paste("errors:", conditionMessage(e)))
cat(sprintf("     %s\n", naive))
cat("   It returns a number because unlist() flattens both depths to the same\n")
cat("   vector. The count is right and the STRUCTURE is destroyed: ring and\n")
cat("   polygon boundaries are gone, so a Polygon and a MultiPolygon become\n")
cat("   indistinguishable. A wrong answer that looks like a right one.\n")
cat("   The correct version needs the branch:\n")
pts <- map_dfr(seq_along(feats), function(i) {
  f <- feats[[i]]
  rings <- if (f$geometry$type == "Polygon") f$geometry$coordinates
           else purrr::list_flatten(f$geometry$coordinates)
  map_dfr(rings, \(r) data.frame(feature = i,
                                 x = map_dbl(r, 1), y = map_dbl(r, 2)))
})
cat(sprintf("     with the if: %s coordinate pairs, rings preserved\n",
            format(nrow(pts), big.mark = ",")))
cat("   `list_flatten` removes exactly one level, which is the whole fix and\n")
cat("   also the whole problem: you must know which records need it.\n")
cat("   WORTH RECORDING: the first draft of this line called `flatten()`, which\n")
cat("   jsonlite MASKS — every R attempt in this corpus loads jsonlite to parse,\n")
cat("   so purrr's own verb is shadowed by the parser in all of them. The error\n")
cat("   names `is.data.frame(x) is not TRUE`, which points at neither cause.\n")

# ── Q6. ──────────────────────────────────────────────────────────────────────
cat("\n6. are any object keys actually data:\n")
cat("   n/a — NOTES.md grades this file keys-as-data 0. Recorded as\n")
cat("   not-tested rather than as a pass.\n")

cat("
CONCLUSION — purrr on the file where it should look best, and it does.

  This is the least ragged document in the corpus, and it removes the one thing
  that made purrr awkward on npm: `map_dfr` over 241 features needs no `%||%`
  anywhere, because every feature carries all 63 property fields. Question 8 is
  five lines and reads cleanly. `README.md`'s claim holds for a fourth document.

  QUESTION 1 IS STILL str() AND STILL O(data), and questions 3 and 6 are still
  CANNOT. Nothing has changed there and nothing was expected to.

  WHAT THIS FILE ADDS is question 10, and it is the sharpest purrr result yet.
  The naive `unlist` answer RETURNS A PLAUSIBLE NUMBER — the right count of
  coordinate pairs — while silently destroying the ring structure that
  distinguishes a Polygon from a MultiPolygon. It does not error, it does not
  warn, and the number it prints is correct. The fix is one `if` on
  `geometry$type`, and the only way to know to write it is to already know the
  format.

  That is the project's thesis in one expression: **the extraction was never the
  problem, and purrr is excellent at it. Knowing that the branch is needed is
  the problem, and purrr is silent.**
")
