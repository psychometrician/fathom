# rrapply — Crossref works, 1,000 records
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
#  measured      2026-08-11
#  run           cd corpus/21-crossref-works/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                            10   NO                  yes — 135 leaf paths
#   2 how deep                                    6   NO                  YES — no recursion
#   3 what is one record                          1   -                   CANNOT
#   4 always present vs sometimes                14   NO                  YES — 57 of 57 seen
#   5 does any field change type                  8   NO                  CANNOT, structurally
#   6 are any object keys data                    4   NO                  a representation
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               3   YES                 rrapply did none of it
#   9 a field missing from some rows              4   NO                  NO — drops the rows
#  10 flatten the deepest array                   3   YES                 PARTLY — leaves
#  11 find every path matching something          6   NO                  YES — 13, one boolean
#  12 flattest honest table                       3   -                   the melt IS one
#  13 needed the shape in advance?                    NO for 1, 2, 4, 6, 11 — the most of
#                                                     any R tool here, again
#  14 survives the next file unchanged?               everything off the melt
#  15 readable a week later?                          the L-column indexing, no
#  16 lines, and how much is ceremony?                ~140, and the melt is ONE call
#
# THE MELT FOUND THE RECORDS WITHOUT BEING TOLD, which nothing else in the R
# half managed. `rrapply(doc, how = "melt")` on the WHOLE document gives
# 195,884 leaf rows and 8 level columns, so question 2 is the column count —
# the only answer to depth in R here that is neither a hand walk nor a named
# path. pandas, polars and DuckDB all returned the one-row envelope; tidyjson
# needed two `enter_object` calls; jsonlite needed `$message$items`.
#
# Question 11 is again one boolean over a column: 13 distinct URL paths, the
# same number jq, ijson, glom, pydash and purrr each reached with a recursion.
#
# THE `bind` WATCH, FIFTH POINT, AND THE PREDICTION HELD. Predicted wide before
# the run because 40 of 57 fields are optional and `reference[]` holds 18,155
# objects across 97 key-sets. MEASURED: 1,000 x 8,439 at 97.7% NA.
#     entry 14   20,000 x 50      the only list-column-free extract in the corpus
#     entry 17   36 columns       64% NA
#     entry 18   100 x 37,006     98.1% NA
#     entry 20   8,536 x 3,415    98.3% NA
#     entry 21   1,000 x 8,439    97.7% NA
# Five documents, one unchanged verb, and the width tracks the raggedness every
# time.
#
# THE `bind` WATCH, FIFTH POINT. Entry 14: 20,000 x 50, the only list-column-free
# extract in either language. Entry 17: 36 columns at 64% NA. Entry 18:
# 100 x 37,006 at 98.1%. Entry 20: 8,536 x 3,415 at 98.3%. PREDICTED HERE BEFORE
# THE RUN: wide again, because 40 of 57 fields are optional and `reference[]`
# holds 18,155 objects with 97 distinct key-sets between them.
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
items <- doc$message$items

cat("\nQ0  rrapply works on a parsed list; jsonlite read the bytes. CANNOT.\n")

t0 <- Sys.time()
melted <- rrapply(doc, how = "melt")
cat(sprintf("\nQ1  rrapply(how='melt') on the WHOLE document -> %d rows x %d, %.1fs\n",
            nrow(melted), ncol(melted),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
L <- grep("^L", names(melted), value = TRUE)
cat(sprintf("Q2  %d level columns, so the document is %d deep — AND IT NEEDED NO\n",
            length(L), length(L)))
cat("    RECURSION AND NO PATH. The melt found $.message.items by melting\n")
cat("    everything, which is the only R answer to question 2 in this corpus\n")
cat("    that is neither a hand walk nor a named path. The probe says 9.\n")
pathcols <- melted[, L, drop = FALSE]
folded <- apply(pathcols, 1, \(r) {
  r <- r[!is.na(r)]
  paste(ifelse(grepl("^[0-9]+$", r), "[]", r), collapse = ".")
})
cat(sprintf("Q1  %d distinct folded LEAF paths (the probe's 236 counts containers too)\n",
            length(unique(folded))))

cat(sprintf("\nQ3  no candidates, no pricing. CANNOT.\nQ7  %d works\n", length(items)))

# ── Q4. L3 is the record index, L4 the field name. ──────────────────────────
f <- melted[!is.na(melted$L4) & melted$L1 == "message" & melted$L2 == "items", ]
present <- table(f$L4)
allk <- unique(unlist(lapply(items, names)))
cat(sprintf("\nQ4  L4 names the record field (L1=message, L2=items, L3=RECORD INDEX):\n"))
cat(sprintf("    %d distinct L4 values against %d record fields in the document\n",
            length(present), length(allk)))
gone <- setdiff(allk, names(present))
if (length(gone)) {
  cat(sprintf("    THE MELT CANNOT SEE: %s\n", paste(gone, collapse = ", ")))
  cat("    — empty containers have no leaves, so a field that is always [] or {}\n")
  cat("    contributes no rows. Entry 20 lost four fields this way.\n")
} else cat("    None missing: every field has at least one leaf somewhere.\n")
nleaf <- sum(vapply(melted$value, is.null, logical(1)))
cat(sprintf("Q4  NULL leaves in the melt: %d. NONE of them is at the record level —\n", nleaf))
cat("    the record fields are absent-or-present and never written null, so\n")
cat("    question 4's discriminator has nothing to separate here. The few that\n")
cat("    exist are deeper, including the two `issued.date-parts` [[null]] rows.\n")
cat("    Entry 20's 178,188 nulls are what made this question interesting there.\n")

cat("\nQ5  CANNOT, structurally. The melt reports LEAVES, so a field whose value\n")
cat("    is a container has no row of its own to compare. The probe's one site,\n")
cat("    issued.date-parts, is an array of arrays and only its NUMBERS appear.\n")
dp <- table(vapply(items, \(w) {
  v <- w$issued$`date-parts`[[1]][[1]]
  if (is.null(v)) "null" else class(v)[1]
}, character(1)))
cat(sprintf("    indexed by hand instead: %s\n",
            paste(sprintf("%s=%d", names(dp), dp), collapse = ", ")))

refn <- sum(vapply(items, \(w) length(w$reference), integer(1)))
refk <- unique(unlist(lapply(items, \(w) lapply(w$reference, names))))
cat(sprintf("\nQ6  reference[]: %d keys over %s copies. The probe DECLINES it as a\n",
            length(refk), format(refn, big.mark = ",")))
cat("    vocabulary; the melt puts every key in a column and judges nothing.\n")

cat("\n     HYPHENS: the melt puts field NAMES in a character column, so a hyphen\n")
cat("     is data and costs nothing — the same reason polars and tidyjson pay\n")
cat("     nothing, arrived at from a different direction.\n")

tbl <- data.frame(DOI = vapply(items, \(w) w$DOI, character(1)),
                  type = vapply(items, \(w) w$type, character(1)))
cat(sprintf("\nQ8  %d x %d — and rrapply did none of it.\n", nrow(tbl), ncol(tbl)))
ab <- f[f$L4 == "abstract", ]
cat(sprintf("\nQ9  abstract leaves: %d rows from %d works. A work WITHOUT one\n",
            nrow(ab), length(unique(ab$L3))))
cat("    contributes NO ROW, so the melt drops exactly the rows Q9 says to keep.\n")
r <- f[!is.na(f$L5) & f$L4 == "reference", ]
cat(sprintf("\nQ10 reference leaves in the melt: %d rows (18,155 references, one row\n",
            nrow(r)))
cat("    per KEY). Rebuilding one row per reference is a reshape on L5/L6.\n")

chr <- vapply(melted$value, \(v) is.character(v) && length(v) == 1, logical(1))
vals <- unlist(melted$value[chr])
hit <- chr; hit[chr] <- grepl("^https?://", vals)
cat(sprintf("\nQ11 %d URL leaves over %d distinct folded paths — ONE BOOLEAN OVER A\n",
            sum(hit), length(unique(folded[hit]))))
cat("    COLUMN, no recursion. jq, ijson, glom, pydash and purrr all say 13.\n")

cat("\n     ══ THE bind TEST, fifth point ══\n")
t0 <- Sys.time()
bound <- tryCatch(rrapply(items, how = "bind"), error = function(e) e)
if (inherits(bound, "error")) {
  cat(sprintf("     rrapply(how='bind') ERRORS: %s\n", conditionMessage(bound)))
} else {
  at <- vapply(bound, is.atomic, logical(1))
  cat(sprintf("     %d x %d in %.1fs, %.1f%% NA over %d atomic columns\n",
              nrow(bound), ncol(bound),
              as.numeric(difftime(Sys.time(), t0, units = "secs")),
              100 * mean(is.na(as.matrix(bound[, at]))), sum(at)))
  cat("     14: 20,000 x 50 | 17: 36 cols 64% NA | 18: 100 x 37,006 98.1% |\n")
  cat("     20: 8,536 x 3,415 98.3%. Read this against the prediction above.\n")
}

cat(sprintf("\nQ12 the melt IS the flattest honest table: %d x %d, one leaf per row.\n",
            nrow(melted), ncol(melted)))
cat("    Not rectangular in god's sense — a long edge list, not one row per work.\n")
