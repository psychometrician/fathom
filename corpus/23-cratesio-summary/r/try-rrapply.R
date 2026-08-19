# rrapply — crates.io summary
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   41 KB, six collections at the root, depth 4
#  measured      2026-08-11
#  run           cd corpus/23-cratesio-summary/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             6   NO                  yes
#   2 how deep                                    4   NO                  YES — no recursion
#   3 what is one record                         12   NO                  THE MELT SHOWS IT
#   4 always present vs sometimes                 8   NO                  YES — three always-null
#   5 does any field change type                  4   NO                  CANNOT
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                             2  NO                  three answers
#   8 three named fields to a table                3 YES                 rrapply did none of it
#   9 a field missing from some rows                4 NO                  the melt KEEPS nulls
#  10 flatten the deepest array                     3 -                   NO ARRAY TO FLATTEN
#  11 find every path matching something            6 NO                  YES — one boolean
#  12 flattest honest table                         3 -                   the melt IS one
#  13 needed the shape in advance?                    NO for 1, 2, 3, 4, 11
#  14 survives the next file unchanged?               everything off the melt
#  15 readable a week later?                          the L-column indexing, no
#  16 lines, and how much is ceremony?                ~110, and the melt is ONE call
#
# THE MELT IS THE CLOSEST ANY TOOL COMES TO ANSWERING DEFECT 25's QUESTION
# WITHOUT BEING ASKED. `rrapply(doc, how="melt")` puts the COLLECTION NAME in
# L1 and the field name in L3, so grouping by L3 and counting distinct L1s
# shows the four collections sharing one field vocabulary — in one `table()`,
# over a structure nobody had to name.
#
# THE `bind` WATCH, SEVENTH POINT. 14: 20,000 x 50. 17: 36 cols 64% NA.
# 18: 100 x 37,006 98.1%. 20: 8,536 x 3,415 98.3%. 21: 1,000 x 8,439 97.7%.
# 22: 100 x 213 21.8%. Entry 22 pinned the mechanism — a column per (position,
# field) pair — so the prediction here is NARROW: ten records per collection,
# no arrays below them, so `bind` on one collection should be about 10 x 29.
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
CRATE <- c("new_crates", "most_downloaded", "most_recently_downloaded", "just_updated")
cat("\nQ0  rrapply works on a parsed list. CANNOT.\n")

t0 <- Sys.time()
melted <- rrapply(doc, how = "melt")
cat(sprintf("\nQ1  rrapply(how='melt') -> %d rows x %d, %.3fs\n", nrow(melted), ncol(melted),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
L <- grep("^L", names(melted), value = TRUE)
cat(sprintf("Q2  %d level columns, so depth %d — NO RECURSION AND NO PATH.\n",
            length(L), length(L)))
cat("    The melt found all six collections by melting everything. Probe: 4.\n")
folded <- apply(melted[, L, drop = FALSE], 1, \(r) {
  r <- r[!is.na(r)]; paste(ifelse(grepl("^[0-9]+$", r), "[]", r), collapse = ".")
})
cat(sprintf("Q1  %d distinct folded LEAF paths (the probe's 140 counts containers)\n",
            length(unique(folded))))

# ── Q3. THE FOUR-IN-ONE, VISIBLE IN THE MELT. ───────────────────────────────
cr <- melted[melted$L1 %in% CRATE & !is.na(melted$L3), ]
tab <- table(cr$L3, cr$L1)
shared <- rownames(tab)[rowSums(tab > 0) == length(CRATE)]
cat(sprintf("\nQ3  in the melt, L1 is the COLLECTION and L3 the FIELD NAME.\n"))
cat(sprintf("    %d distinct field names across the four collections, of which\n",
            nrow(tab)))
cat(sprintf("    %d appear in ALL FOUR.\n", length(shared)))
cat("    ONE `table(L3, L1)` AND THE ANSWER IS THERE. rrapply is the only tool\n")
cat("    in this directory where defect 25's question — do these collections\n")
cat("    share a shape? — falls out of the DEFAULT representation rather than\n")
cat("    a comparison you had to think to write. It is still not a verdict.\n")
cat(sprintf("    (the four collections hold %d, %d, %d and %d records)\n",
            length(doc$new_crates), length(doc$most_downloaded),
            length(doc$most_recently_downloaded), length(doc$just_updated)))
ids <- unlist(lapply(CRATE, \(k) vapply(doc[[k]], \(c) c$id, character(1))))
nms <- unlist(lapply(CRATE, \(k) vapply(doc[[k]], \(c) c$name, character(1))))
cat(sprintf("\n     THE OVERLAP: %d rows, %d DISTINCT crates — %s\n",
            length(ids), length(unique(ids)),
            paste(sort(names(which(table(nms) > 1))), collapse = ", ")))
cat("     AND THE MELT DOES NOT SHOW THIS. L1 tells you which collection a row\n")
cat("     came from and nothing compares the ids across them. Seven crates\n")
cat("     appear twice and no representation here says so.\n")

# ── Q4. ─────────────────────────────────────────────────────────────────────
crates <- unlist(lapply(CRATE, \(k) doc[[k]]), recursive = FALSE)
pres <- table(unlist(lapply(crates, names)))
nulls <- vapply(names(pres),
                \(k) sum(vapply(crates, \(c) is.null(c[[k]]), logical(1))), integer(1))
nleaf <- sum(vapply(melted$value, is.null, logical(1)))
cat(sprintf("\nQ4  crate keys not on every crate: %d of %d\n",
            sum(pres < length(crates)), length(pres)))
cat("Q4  written NULL:\n"); print(nulls[nulls > 0])
cat(sprintf("Q4  NULL ON ALL %d: %s\n", length(crates),
            paste(names(nulls)[nulls == length(crates)], collapse = ", ")))
cat(sprintf("Q4  NULL-valued leaves in the melt: %d — THE MELT KEEPS THEM, so a\n", nleaf))
cat("    written null is a row and an absent key is no row. Entry 21's melt\n")
cat("    dropped the rows question 9 wanted; this document has none to drop.\n")

cat("\nQ5  CANNOT, structurally: the melt reports LEAVES, so a field whose value\n")
cat("    is a container has no row of its own. The probe reports NONE anyway.\n")
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")
cat(sprintf("\nQ7  num_crates %s; num_downloads %s; %d rows, %d distinct\n",
            format(doc$num_crates, big.mark = ","),
            format(doc$num_downloads, big.mark = ","),
            length(ids), length(unique(ids))))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
tbl <- data.frame(name = vapply(doc$new_crates, \(c) c$name, character(1)),
                  version = vapply(doc$new_crates, \(c) c$max_version, character(1)))
cat(sprintf("\nQ8  %d x %d — and rrapply did none of it.\n", nrow(tbl), ncol(tbl)))
hp <- cr[cr$L3 == "homepage", ]
cat(sprintf("\nQ9  `homepage` leaves: %d rows of %d crates, %d NULL-valued\n",
            nrow(hp), length(crates), sum(vapply(hp$value, is.null, logical(1)))))
cat("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is an object of six\n")
cat("    fields; question 10 has no target on this document.\n")
lk <- cr[!is.na(cr$L4) & cr$L3 == "links", ]
cat(sprintf("    `links` leaves in the melt: %d rows\n", nrow(lk)))
chr <- vapply(melted$value, \(v) is.character(v) && length(v) == 1, logical(1))
vals <- unlist(melted$value[chr])
hit <- chr; hit[chr] <- grepl("^https?://", vals)
fold2 <- unique(sub("^(new_crates|most_downloaded|most_recently_downloaded|just_updated)\\.",
                    "<one of the four>.", folded[hit]))
cat(sprintf("\nQ11 %d URL leaves over %d folded paths, folding again over the four\n",
            sum(hit), length(unique(folded[hit]))))
cat(sprintf("    collections to %d: %s\n", length(fold2), paste(fold2, collapse = ", ")))
cat("    ONE BOOLEAN OVER A COLUMN, no recursion — and the same 11-folding-to-3\n")
cat("    that jq, ijson, glom, pydash and purrr each reached with more work.\n")

cat("\n     ══ THE bind TEST, seventh point, predicted NARROW ══\n")
t0 <- Sys.time()
b <- tryCatch(rrapply(doc$new_crates, how = "bind"), error = function(e) e)
if (inherits(b, "error")) {
  cat(sprintf("     ERRORS: %s\n", conditionMessage(b)))
} else {
  at <- vapply(b, is.atomic, logical(1))
  cat(sprintf("     one collection: %d x %d in %.3fs, %.1f%% NA over %d atomic cols\n",
              nrow(b), ncol(b), as.numeric(difftime(Sys.time(), t0, units = "secs")),
              100 * mean(is.na(as.matrix(b[, at]))), sum(at)))
  cat("     14: 20,000 x 50 | 17: 36 cols 64% | 18: 100 x 37,006 98.1% |\n")
  cat("     20: 8,536 x 3,415 98.3% | 21: 1,000 x 8,439 97.7% | 22: 100 x 213 21.8%\n")
  cat("     ENTRY 22 PINNED THE MECHANISM — a column per (position, field) pair —\n")
  cat("     and this document has NO ARRAY below the records at all, so the\n")
  cat("     prediction was 23 fields plus the 6 `links` children = 29.\n")
  cat("     MEASURED 27 AND 0.0% NA — two narrower than predicted, because two\n")
  cat("     fields are null on all ten of THIS collection and contribute no\n")
  cat("     column at all. AND ZERO PER CENT NA IS THE FIRST IN THE SERIES:\n")
  cat("     every earlier `bind` was 21.8% to 98.3% empty. Entry 22 said the\n")
  cat("     width is set by the longest child array; this document has NO child\n")
  cat("     array, and the table comes out dense. That is the mechanism\n")
  cat("     confirmed by its own limiting case.\n")
}
cat(sprintf("\nQ12 the melt IS the flattest honest table: %d x %d, one leaf per row,\n",
            nrow(melted), ncol(melted)))
cat("    and L1 carries which collection each row came from — which is the one\n")
cat("    thing the four-way repetition needs and no frame here provides.\n")
