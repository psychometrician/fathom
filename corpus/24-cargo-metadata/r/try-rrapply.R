# rrapply — cargo metadata for this repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   27 KB, 8 packages, depth 8
#  measured      2026-08-11
#  run           cd corpus/24-cargo-metadata/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             6   NO                  yes
#   2 how deep                                    4   NO                  YES — no recursion
#   3 what is one record                          2   -                   CANNOT
#   4 always present vs sometimes                 8   NO                  YES — four always-null
#   5 does any field change type                  4   NO                  CANNOT
#   6 are any object keys data                   10   NO                  a COLUMN, like tidyjson
#   7 how many records                             2  NO                  yes
#   8 three named fields to a table                3 YES                 rrapply did none of it
#   9 a field missing from some rows                3 NO                  the melt KEEPS nulls
#  10 flatten the deepest array                     4 YES                 PARTLY — leaves
#  11 find every path matching something            5 NO                  YES — one boolean
#  12 flattest honest table                         3 -                   the melt IS one
#  13 needed the shape in advance?                    NO for 1, 2, 4, 6, 11
#  14 survives the next file unchanged?               YES — the melt puts feature
#                                                     names in a COLUMN
#  15 readable a week later?                          the L-column indexing, no
#  16 lines, and how much is ceremony?                ~105
#
# THE `bind` WATCH, EIGHTH AND LAST POINT. 14: 20,000 x 50. 17: 36 cols 64% NA.
# 18: 100 x 37,006 98.1%. 20: 8,536 x 3,415 98.3%. 21: 1,000 x 8,439 97.7%.
# 22: 100 x 213 21.8%. 23: 10 x 27 0.0%. Entry 22 pinned the mechanism as a
# column per (position, field) pair and entry 23 confirmed it by removing the
# cause. PREDICTED HERE: WIDE AND EMPTY, because `targets` runs up to 5 per
# package and `features` contributes a column per name — the first document in
# the series with BOTH a positional array and keys-as-data.
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
pkgs <- doc$packages
cat("\nQ0  rrapply works on a parsed list. CANNOT.\n")

t0 <- Sys.time()
melted <- rrapply(doc, how = "melt")
cat(sprintf("\nQ1  rrapply(how='melt') -> %d rows x %d, %.3fs\n", nrow(melted), ncol(melted),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
L <- grep("^L", names(melted), value = TRUE)
cat(sprintf("Q2  %d level columns, so depth %d — NO RECURSION AND NO PATH.\n",
            length(L), length(L)))
folded <- apply(melted[, L, drop = FALSE], 1, \(r) {
  r <- r[!is.na(r)]; paste(ifelse(grepl("^[0-9]+$", r), "[]", r), collapse = ".")
})
cat(sprintf("Q1  %d distinct folded LEAF paths (the probe's 143 counts containers)\n",
            length(unique(folded))))
cat(sprintf("\nQ3  no candidates, no pricing. CANNOT.\nQ7  %d packages\n", length(pkgs)))

# ── Q6. ─────────────────────────────────────────────────────────────────────
f <- melted[melted$L1 == "packages" & !is.na(melted$L3) & melted$L3 == "features", ]
fn <- table(f$L4)
cat(sprintf("\nQ6  in the melt, L1=packages, L2=index, L3=field, L4=FEATURE NAME.\n"))
cat(sprintf("    %d distinct L4 values, %d appearing once\n", length(fn), sum(fn == 1)))
cat(sprintf("    %d contain a HYPHEN, and the melt does not care — they are\n",
            sum(grepl("-", names(fn)))))
cat("    VALUES in a character column, not identifiers.\n")
cat("    THE SAME RIGHT SHAPE tidyjson's `gather_object` gives, from a verb\n")
cat("    that was not asked for it. jsonlite, pandas and polars all put these\n")
cat("    28 names into a SCHEMA instead, so `cargo add` changes their columns\n")
cat("    and not this melt's. STILL A REPRESENTATION AND NOT A VERDICT — the\n")
cat("    melt does the same to genuine field names one level up.\n")

# ── Q4/Q5. ──────────────────────────────────────────────────────────────────
pres <- table(unlist(lapply(pkgs, names)))
nulls <- vapply(names(pres), \(k) sum(vapply(pkgs, \(p) is.null(p[[k]]), logical(1))),
                integer(1))
nleaf <- sum(vapply(melted$value, is.null, logical(1)))
cat(sprintf("\nQ4  package keys not on every package: %d of %d\n",
            sum(pres < length(pkgs)), length(pres)))
cat("Q4  written NULL:\n"); print(nulls[nulls > 0])
cat(sprintf("Q4  NULL ON ALL %d: %s\n", length(pkgs),
            paste(names(nulls)[nulls == length(pkgs)], collapse = ", ")))
cat(sprintf("Q4  NULL-valued leaves in the melt: %d — THE MELT KEEPS THEM.\n", nleaf))
cat("\nQ5  CANNOT, structurally: the melt reports LEAVES, so a field whose value\n")
cat("    is a container has no row of its own. The probe reports NONE anyway.\n")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
tbl <- data.frame(name = vapply(pkgs, \(p) p$name, character(1)),
                  version = vapply(pkgs, \(p) p$version, character(1)))
cat(sprintf("\nQ8  %d x %d — and rrapply did none of it.\n", nrow(tbl), ncol(tbl)))
d <- melted[melted$L1 == "packages" & !is.na(melted$L3) & melted$L3 == "description", ]
cat(sprintf("\nQ9  `description` leaves: %d rows of %d packages, %d NULL-valued\n",
            nrow(d), length(pkgs), sum(vapply(d$value, is.null, logical(1)))))
tg <- melted[melted$L1 == "packages" & !is.na(melted$L3) & melted$L3 == "targets", ]
dk <- melted[melted$L1 == "resolve" & !is.na(melted$L5), ]
cat(sprintf("\nQ10 targets leaves: %d rows; resolve subtree leaves: %d rows\n",
            nrow(tg), nrow(dk)))
cat("    The melt reaches BOTH branches with no path at all, which no frame in\n")
cat("    this directory managed — resolve.nodes is not under `packages`.\n")
chr <- vapply(melted$value, \(v) is.character(v) && length(v) == 1, logical(1))
vals <- unlist(melted$value[chr])
hit <- chr; hit[chr] <- grepl("^https?://", vals)
cat(sprintf("\nQ11 %d URL leaves over %d folded paths — ONE BOOLEAN OVER A COLUMN\n",
            sum(hit), length(unique(folded[hit]))))
cat("    and the same 5 that jq, ijson, glom, pydash and purrr each reached.\n")

cat("\n     ══ THE bind TEST, eighth and last point ══\n")
t0 <- Sys.time()
b <- tryCatch(rrapply(pkgs, how = "bind"), error = function(e) e)
if (inherits(b, "error")) {
  cat(sprintf("     ERRORS: %s\n", conditionMessage(b)))
} else {
  at <- vapply(b, is.atomic, logical(1))
  cat(sprintf("     %d x %d in %.3fs, %.1f%% NA over %d atomic columns\n",
              nrow(b), ncol(b), as.numeric(difftime(Sys.time(), t0, units = "secs")),
              100 * mean(is.na(as.matrix(b[, at]))), sum(at)))
  cat("     14: 20,000 x 50 | 17: 36 cols 64% | 18: 100 x 37,006 98.1% |\n")
  cat("     20: 8,536 x 3,415 98.3% | 21: 1,000 x 8,439 97.7% |\n")
  cat("     22: 100 x 213 21.8% | 23: 10 x 27 0.0%\n")
  cat("     PREDICTED WIDE AND EMPTY: this is the first document in the series\n")
  cat("     with BOTH a positional array (`targets`, up to 5 per package) and\n")
  cat("     keys-as-data (`features`, 28 names). Read the width and the NA\n")
  cat("     fraction against entry 22's 213 at 21.8% and entry 23's 27 at 0.0%.\n")
}
cat(sprintf("\nQ12 the melt IS the flattest honest table: %d x %d, one leaf per row.\n",
            nrow(melted), ncol(melted)))
