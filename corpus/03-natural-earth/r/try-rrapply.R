# rrapply — Natural Earth admin-0 countries, as GeoJSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.json   3.9 MB, 241 features, depth 8, 75 paths
#  measured      2026-08-09
#  run           cd corpus/03-natural-earth/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             8   NO                  NO
#   2 how deep                                    4   NO                  YES
#   5 does any field change type                 12   NO                  YES
#   6 are any keys actually data                  -   -                   n/a
#   7 how many records                            1   YES                 yes
#  11 find every path matching something          5   NO                  yes
#  12 flattest honest table                       6   NO                  yes
#  13 needed the shape in advance?                    NO — see question 5
#  16 lines, and how much is ceremony?                see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE, AND IT TURNED OUT TO BE THE INTERESTING ONE. `rrapply(how =
# "melt")` is one of the describers `README.md` names, and `VERDICT.md` records
# it answering **3,112** on `01-npm-registry` and **141%** of the Stripe spec —
# both of them the O(data) failure.
#
# This document is the corpus's polymorphism-by-depth specimen: `coordinates` is
# 3 deep on 122 Polygons and 4 deep on 119 MultiPolygons, identical by type. The
# probe missed it. polars silently erased it. jsonlite preserved it and did not
# say so. **rrapply is the only tool in either language whose ordinary output
# makes it visible**, and the reason is structural: melt turns nesting DEPTH
# into COLUMN COUNT.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

path  <- "../source.json"
bytes <- file.size(path)
doc   <- fromJSON(path, simplifyVector = FALSE)

# ── Q1 / Q12. Melt every leaf to a row, and price the answer. ────────────────
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
cat(sprintf("   listing every path costs %s chars for a %s-byte file (%.0f%%)\n",
            format(chars, big.mark = ","), format(bytes, big.mark = ","),
            100 * chars / bytes))
cat(sprintf("   every leaf has its own path — %s of them are distinct, because\n",
            format(length(unique(paths)), big.mark = ",")))
cat("   the array indices are IN the path. That is the honest melt number and\n")
cat("   it is useless as a description, so collapse the indices to []:\n")
shaped <- unique(gsub("(^|\\.)[0-9]+(?=\\.|$)", "\\1[]", paths, perl = TRUE))
cat(sprintf("   %s distinct path SHAPES; %s chars to list those (%.2f%%)\n",
            format(length(shaped), big.mark = ","),
            format(sum(nchar(shaped)) + length(shaped), big.mark = ","),
            100 * (sum(nchar(shaped)) + length(shaped)) / bytes))
cat("   Compare: 3,112 chars on 01-npm-registry, 141% on 09-stripe-openapi.\n")
cat("   THE GAP BETWEEN THOSE TWO NUMBERS IS THE WHOLE ARGUMENT. rrapply's own\n")
cat("   output is 226% of the file; the same information with indices folded is\n")
cat("   a fraction of a percent. Folding repeated siblings into one description\n")
cat("   is operation 1, and the tool does not do it — but nothing about this\n")
cat("   document prevents it, which is what makes it a missing feature rather\n")
cat("   than a hard problem.\n")

# ── Q2. How deep? rrapply answers this one properly. ─────────────────────────
cat("\n2. how deep does it go:\n")
cat(sprintf("   melt produced %d level columns (%s), so the document is %d deep\n",
            length(lv), paste(lv, collapse = ", "), length(lv)))
cat("   NO HAND-WRITTEN RECURSION. Every other R tool here needed one for this;\n")
cat("   rrapply's column count IS the depth, for free, as a side effect.\n")

# ── Q5. THE ONE THAT MATTERS. Polymorphism by depth, visible in the output. ──
cat("\n5. does any field change type — and rrapply is the tool that can see it:\n")
gt <- vapply(doc$features, function(f) f$geometry$type, "")
cat(sprintf("   geometry$type: %s\n",
            paste(sprintf("%s x%d", names(table(gt)), table(gt)), collapse = ", ")))

# The measurement, taken from the melted frame ALONE — no knowledge of GeoJSON,
# no recursion, no reference to geometry$type until the comparison at the end.
# L1 = top key, L2 = feature index, L3 = geometry/properties, L4 = field name,
# L5..L8 = array indices. So "how deep does THIS FIELD go" is a count of filled
# level columns, per feature — arithmetic on the frame, nothing GeoJSON-specific.
coord  <- m[!is.na(m$L4) & m$L4 == "coordinates", , drop = FALSE]
filled <- apply(coord[, lv, drop = FALSE], 1L, function(r) sum(!is.na(r)))
per_feature <- tapply(filled, as.integer(coord$L2), max)
cat(sprintf("   coordinate leaves fill %s level columns\n",
            paste(sort(unique(filled)), collapse = " or ")))
tb <- table(per_feature)
cat(sprintf("   per feature, the deepest coordinate leaf fills: %s\n",
            paste(sprintf("%s cols x%d", names(tb), as.integer(tb)), collapse = ", ")))
cat("   TWO POPULATIONS, IN THE OUTPUT, WITH NO PROMPTING. A field whose leaves\n")
cat("   sit at two different level-counts is polymorphic by depth, and that is\n")
cat("   a property of the melted frame rather than of GeoJSON.\n")
deep  <- as.integer(names(per_feature))[per_feature == max(per_feature)]
agree <- setequal(deep, which(gt == "MultiPolygon"))
cat(sprintf("   cross-check against geometry$type: %s\n",
            if (agree) sprintf("the deep group IS exactly the %d MultiPolygons",
                               sum(gt == "MultiPolygon"))
            else "the split does not line up with geometry$type"))

# ── Q11. Find every path whose value matches something. ──────────────────────
cat("\n11. find every path whose value matches something:\n")
cat("   This document holds no URL and no email — measured, 0 occurrences of\n")
cat("   `http`. The pattern it does carry is the -99 missing sentinel:\n")
s99 <- m[!is.na(m$value) & as.character(m$value) == "-99", , drop = FALSE]
f99 <- table(s99$L4)
cat(sprintf("   %s cells hold -99, in %d distinct fields\n",
            format(nrow(s99), big.mark = ","), length(f99)))
cat("   rrapply does this WELL, and it is the one question where melting pays:\n")
cat("   a value predicate over a melted frame is a subset, and the path columns\n")
cat("   come back with it. No recursion to write.\n")
cat(sprintf("   worst fields: %s\n",
            paste(sprintf("%s x%d", names(sort(f99, decreasing = TRUE))[1:5],
                          sort(f99, decreasing = TRUE)[1:5]), collapse = ", ")))

# ── Q6 / Q7. ─────────────────────────────────────────────────────────────────
cat(sprintf("\n7. features: %d\n", length(doc$features)))
cat("\n6. are any object keys actually data:\n")
cat("   n/a — NOTES.md grades this file keys-as-data 0. rrapply has no notion\n")
cat("   of the question either way; recorded as not-tested, not as a pass.\n")

cat("
CONCLUSION — and this is the best result any existing tool has posted in this
corpus on a question the probe got wrong.

  MELT MAKES DEPTH POLYMORPHISM VISIBLE, and nothing else does. Every other
  check in this repository asks what TYPE a value has, and by type this
  document is perfectly homogeneous: `coordinates` is a list 241 times out of
  241. rrapply does not ask about type at all. It turns each nesting level into
  a column, so a field whose leaves bottom out at two different level-counts
  shows up as two populations in the frame — measured above, with no knowledge
  of GeoJSON, and the deep group is exactly the 119 MultiPolygons.

  `NOTES.md` records the probe scoring this file `polymorphism 0` on the
  document chosen specifically to have it, and calls the distinction — by type
  versus by depth — the thing the axes need. **rrapply already had the
  instrument.** It does not report it, and nobody would see it without going
  looking, but the information is in the ordinary output rather than lost.

  IT ALSO ANSWERS QUESTION 2 FOR FREE, which no other R tool here does without
  a hand-written recursion, and for the same reason.

  WHAT IT STILL DOES NOT DO is question 1 — AND THE NUMBER QUALIFIES A CLAIM
  THIS PROJECT RESTS ON.

  `VERDICT.md` says: *\"Every existing describer's output is proportional to the
  number of distinct key names, and keys-as-data is what makes that proportional
  to the data.\"* This file has **keys-as-data 0** — the cleanest negative case
  in the corpus — and rrapply's melt is **226% of the document**, higher than
  `ijson` on the Stripe spec at 172%, which `VERDICT.md` records as the corpus
  high. 214,798 distinct paths against npm's 3,112, on a file with six fewer
  keyed sites.

  **The driver here is not keyed objects. It is array indices.** Collapsing
  `.1.2.3` to `[]` takes the same information to **68 path shapes and 0.05%**.
  So there are two ways to make a describer O(data), not one:

    keys-as-data  — every VALUE mints a new key name      (npm, Stripe)
    deep arrays   — every ELEMENT mints a new path index  (this file)

  The claim as written predicts this document should be cheap to describe, and
  it is the most expensive one measured. The repair is to the claim rather than
  to the tool, and it makes the underlying point stronger rather than weaker:
  what a describer must fold is REPEATED SIBLINGS, whether they are named or
  numbered. That is operation 1, stated without reference to keys.
")
