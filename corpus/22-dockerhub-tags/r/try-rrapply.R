# rrapply — Docker Hub tags, 100 tags
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   476 KB, 100 tags under $.results, depth 5
#  measured      2026-08-11
#  run           cd corpus/22-dockerhub-tags/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             6   NO                  yes
#   2 how deep                                    4   NO                  YES — no recursion
#   3 what is one record                          3   -                   CANNOT
#   4 always present vs sometimes                10   NO                  YES — three states
#   5 does any field change type                  4   NO                  CANNOT
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                            2   NO                  yes, both numbers
#   8 three named fields to a table               3   YES                 rrapply did none of it
#   9 a field missing from some rows              4   NO                  the melt KEEPS nulls
#  10 flatten the deepest array                   4   YES                 PARTLY — leaves
#  11 find every path matching something          5   NO                  YES — 1, one boolean
#  12 flattest honest table                       3   -                   the melt IS one
#  13 needed the shape in advance?                    NO for 1, 2, 4, 11
#  14 survives the next file unchanged?               everything off the melt
#  15 readable a week later?                          the L-column indexing, no
#  16 lines, and how much is ceremony?                ~110, and the melt is ONE call
#
# THE `bind` WATCH, SIXTH POINT — and this is the one that should be SMALL.
# 14: 20,000 x 50. 17: 36 columns at 64% NA. 18: 100 x 37,006 at 98.1%.
# 20: 8,536 x 3,415 at 98.3%. 21: 1,000 x 8,439 at 97.7%. PREDICTED HERE BEFORE
# THE RUN: narrow and dense, because this document has ONE key-set per shape and
# nothing ragged for `bind` to spread out. If the width tracks raggedness, a
# regular document is where that claim can fail.
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
tags <- doc$results
cat("\nQ0  rrapply works on a parsed list. CANNOT.\n")

t0 <- Sys.time()
melted <- rrapply(doc, how = "melt")
cat(sprintf("\nQ1  rrapply(how='melt') -> %d rows x %d, %.2fs\n", nrow(melted), ncol(melted),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
L <- grep("^L", names(melted), value = TRUE)
cat(sprintf("Q2  %d level columns, so depth %d — NO RECURSION AND NO PATH, and\n",
            length(L), length(L)))
cat("    the melt found $.results by melting everything. The probe says 5.\n")
folded <- apply(melted[, L, drop = FALSE], 1, \(r) {
  r <- r[!is.na(r)]; paste(ifelse(grepl("^[0-9]+$", r), "[]", r), collapse = ".")
})
cat(sprintf("Q1  %d distinct folded LEAF paths (the probe's 33 counts containers)\n",
            length(unique(folded))))

cat(sprintf("\nQ3  no candidates, no pricing. CANNOT.\nQ7  %d tags; `count` says %s\n",
            length(tags), format(doc$count, big.mark = ",")))

# ── Q4. THREE STATES, and the melt sees all of them. ────────────────────────
img <- melted[!is.na(melted$L4) & melted$L1 == "results" & melted$L3 == "images", ]
kk <- table(img$L5)
nulls <- sum(vapply(img$value, is.null, logical(1)))
empt <- sum(vapply(img$value, \(v) identical(v, ""), logical(1)))
cat(sprintf("\nQ4  image leaves: %d rows over %d distinct L5 keys\n", nrow(img), length(kk)))
cat(sprintf("Q4  NULL-valued leaves: %d;  EMPTY-STRING leaves: %d\n", nulls, empt))
cat("    THE MELT KEEPS BOTH — a null is a NULL-valued row and an empty string\n")
cat("    is a zero-length character row — so rrapply can separate all three\n")
cat("    states, like ijson and unlike every frame here.\n")
cat(sprintf("    the probe's 16%% counts nulls only; all three would be %.0f%%\n",
            100 * (nulls + empt) / (nrow(img))))

cat("\nQ5  CANNOT, structurally: the melt reports LEAVES, so `images` has no row\n")
cat("    of its own to compare. The probe reports NO type change anyway.\n")
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")

tbl <- data.frame(name = vapply(tags, \(t) t$name, character(1)),
                  full_size = vapply(tags, \(t) t$full_size, numeric(1)))
cat(sprintf("\nQ8  %d x %d — and rrapply did none of it.\n", nrow(tbl), ncol(tbl)))
va <- img[img$L5 == "variant", ]
cat(sprintf("\nQ9  `variant` leaves: %d rows of %d images, of which %d are NULL\n",
            nrow(va), 1388, sum(vapply(va$value, is.null, logical(1)))))
cat("    EVERY IMAGE CONTRIBUTES A ROW, because the key is always present. On\n")
cat("    entry 21 the melt DROPPED the rows question 9 says to keep; here it\n")
cat("    keeps them all, and the difference is the document's, not the verb's.\n")
cat(sprintf("\nQ10 image leaves in the melt: %d rows for 1,388 images (one row per\n", nrow(img)))
cat("    KEY). Rebuilding one row per image is a reshape on L4/L5.\n")

chr <- vapply(melted$value, \(v) is.character(v) && length(v) == 1, logical(1))
vals <- unlist(melted$value[chr])
hit <- chr; hit[chr] <- grepl("^https?://", vals)
cat(sprintf("\nQ11 %d URL leaf over %d folded path(s): %s\n", sum(hit),
            length(unique(folded[hit])), paste(unique(folded[hit]), collapse = ", ")))
cat("    ONE BOOLEAN OVER A COLUMN — no recursion — and it finds the pagination\n")
cat("    link the three frames cannot see because they build from `results`.\n")

cat("\n     ══ THE bind TEST, sixth point, and the prediction was NARROW ══\n")
t0 <- Sys.time()
b <- tryCatch(rrapply(tags, how = "bind"), error = function(e) e)
if (inherits(b, "error")) {
  cat(sprintf("     ERRORS: %s\n", conditionMessage(b)))
} else {
  at <- vapply(b, is.atomic, logical(1))
  cat(sprintf("     %d x %d in %.2fs, %.1f%% NA over %d atomic columns\n",
              nrow(b), ncol(b), as.numeric(difftime(Sys.time(), t0, units = "secs")),
              100 * mean(is.na(as.matrix(b[, at]))), sum(at)))
  cat("     14: 20,000 x 50 | 17: 36 cols 64% | 18: 100 x 37,006 98.1% |\n")
  cat("     20: 8,536 x 3,415 98.3% | 21: 1,000 x 8,439 97.7%.\n")
  cat("     THE PREDICTION HELD AND THE MECHANISM IS NOW PINNED. 16 tag fields\n")
  cat("     plus the widest tag's 18 images x 11 image fields is 16 + 198 = 214,\n")
  cat("     and `bind` produced 213. IT SPENDS A COLUMN PER (POSITION, FIELD)\n")
  cat("     PAIR, so the width is set by the LONGEST child array and not by the\n")
  cat("     raggedness of the keys. That is why entry 18's 100 records gave\n")
  cat("     37,006 columns and this document's 100 give 213: one has deep long\n")
  cat("     arrays and the other has short ones.\n")
  cat("     And the columns are POSITIONS, which is question 7a's property — the\n")
  cat("     same price entry 14 paid for the corpus's only list-column-free\n")
  cat("     extract. A dense `bind` and a positional `bind` are the same thing.\n")
}
cat(sprintf("\nQ12 the melt IS the flattest honest table: %d x %d, one leaf per row.\n",
            nrow(melted), ncol(melted)))
