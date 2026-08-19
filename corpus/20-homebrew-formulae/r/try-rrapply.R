# rrapply — Homebrew's whole formula index
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
#  measured      2026-08-11
#  run           cd corpus/20-homebrew-formulae/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                            12   NO                  yes — 724 leaf paths
#   2 how deep                                    5   NO                  YES — no recursion
#   3 what is one record                          2   -                   CANNOT
#   4 always present vs sometimes                18   NO                  YES — both halves
#   5 does any field change type                 15   NO                  CANNOT, structurally
#   6 are any object keys data                   14   NO                  a representation, not
#                                                                          a verdict
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               5   YES                 rrapply did none of it
#   9 a field missing from some rows              4   YES                 NO — drops the rows
#  10 flatten the deepest array                   4   YES                 PARTLY — leaves, not pairs
#  11 find every path matching something          9   NO                  YES — 65 and 48, easily
#  12 flattest honest table                       4   -                   the melt IS one
#  13 needed the shape in advance?                    NO for 1, 2, 4, 6, 11 — more than any
#                                                     other R tool here
#  14 survives the next file unchanged?               everything off the melt does
#  15 readable a week later?                          the L-column indexing, no
#  16 lines, and how much is ceremony?                ~170, and the melt is ONE call
#  timing        melt 0.5s for 671,178 rows; bind 2.5s. Both on 29.6 MB
#
# RRAPPLY IS THE BEST R TOOL IN THIS DIRECTORY FOR THE EXPLORATION HALF, and
# that is not what its escalating `bind` reputation would suggest.
# `rrapply(doc, how = "melt")` is ONE call, and off it:
#   - question 2 falls out of the L-column count, the only R answer to depth
#     in this corpus that is not a hand-written recursion
#   - question 11 is one boolean over a column — 65 naive and 48 strict paths,
#     the SAME two numbers jq, jqr, ijson, glom, pydash and purrr report, and
#     the only one of the seven that took no recursion to get
#   - question 4 gets both halves, because a written null is a NULL-valued ROW
#     and an absent key is no row at all
#
# TWO PREDICTIONS DIED IN THE RUN.
# I wrote that the melt DROPS nulls: it keeps 178,188 of them, which is why
# question 4 works and puts rrapply with the walkers rather than the frames.
# And I asked for `bottle/stable/files/<platform>` at L4 and got
# `files, rebuild, root_url` — off by one, because L1 is the RECORD INDEX. That
# is the identical mistake entry 17 recorded against this same melt layout.
#
# WHAT THE MELT CANNOT SEE is a field that is an EMPTY ARRAY everywhere: four
# of 61 — options, installed, recommended_dependencies, optional_dependencies —
# have no leaves and so no rows. Those are the same four DuckDB typed `JSON[]`
# for having no elements to judge. Two tools, two representations, one blind
# spot, one cause.
#
# THE `bind` WATCH, FOURTH POINT. Entry 14 called it the hero — 20,000 x 50,
# the only list-column-free extract in either language. Entry 17: 36 columns at
# 64% NA. Entry 18: 100 x 37,006 at 98.1% NA. Predicted here before the run to
# be very wide, because two keyed collections give `bind` a column per platform
# path. MEASURED: 8,536 x 3,415 at 98.3% NA. The prediction holds and the
# escalation is now four documents long with the verb unchanged throughout.
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  rrapply operates on a parsed list. jsonlite read the bytes. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — melt gives BOTH. ──────────────────
t0 <- Sys.time()
melted <- rrapply(doc, how = "melt")
t_melt <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\nQ1  rrapply(how = 'melt') -> %d rows x %d cols in %.1fs\n",
            nrow(melted), ncol(melted), t_melt))
cat(sprintf("    columns: %s\n", paste(names(melted), collapse = ", ")))
Lcols <- grep("^L", names(melted), value = TRUE)
cat(sprintf("Q2  %d level columns, so the document is %d deep — and THIS IS THE\n",
            length(Lcols), length(Lcols)))
cat("    ONLY R VERB IN THIS DIRECTORY THAT ANSWERS QUESTION 2 WITHOUT A\n")
cat("    HAND-WRITTEN RECURSION. The melt layout IS the depth.\n")
cat("    NOTE the L columns are levels, and L1 is the RECORD INDEX, not a field\n")
cat("    name — entry 17 recorded getting that backwards.\n")

# distinct folded paths, from the melt
pathcols <- melted[, Lcols, drop = FALSE]
folded <- apply(pathcols, 1, \(r) {
  r <- r[!is.na(r)]
  paste(ifelse(grepl("^[0-9]+$", r), "[]", r), collapse = ".")
})
cat(sprintf("Q1  %d distinct folded leaf paths from the melt\n", length(unique(folded))))
cat("    The probe reports 1,132 distinct paths INCLUDING containers; the melt\n")
cat("    has one row per LEAF, so this counts leaf paths only. Different\n")
cat("    question, and worth stating rather than comparing the numbers.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat(sprintf("\nQ3  rrapply names no candidates and prices none. CANNOT.\n"))
cat(sprintf("Q7  %d formulae\n", length(doc)))

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
l2 <- unique(melted$L2[!is.na(melted$L2)])
allk <- unique(unlist(lapply(doc, names)))
cat(sprintf("\nQ4  from the melt, L2 names the root FIELD. %d distinct L2 values,\n", length(l2)))
cat(sprintf("    against %d root fields in the document.\n", length(allk)))
gone <- setdiff(allk, l2)
cat(sprintf("    THE %d THE MELT CANNOT SEE: %s\n", length(gone), paste(gone, collapse = ", ")))
cat("    Every one is an EMPTY ARRAY on all 8,536 formulae. A leaf-melt has one\n")
cat("    row per leaf, and an empty container has no leaves, so a field that is\n")
cat("    always `[]` is invisible. Those are the same four DuckDB typed `JSON[]`\n")
cat("    for having no elements to judge — two tools, two representations, one\n")
cat("    blind spot with the same cause.\n")
nleaf <- sum(vapply(melted$value, is.null, logical(1)))
cat(sprintf("Q4  NULLS ARE KEPT, not dropped: %d NULL leaves in the melt.\n", nleaf))
cat("    I PREDICTED THE MELT WOULD DROP THEM AND IT DOES NOT. So rrapply CAN\n")
cat("    separate a written null from an absent key — a null is a row whose\n")
cat("    value is NULL, an absent key is no row — which puts it with the\n")
cat("    walkers on question 4 and not with the frames.\n")
absent_ct <- vapply(setdiff(allk, gone), \(k)
  sum(vapply(doc, \(f) k %in% names(f), logical(1))), integer(1))
cat(sprintf("    fields present on fewer than all %d formulae: %s\n", length(doc),
            paste(names(absent_ct)[absent_ct < length(doc)], collapse = ", ")))

# ── Q5. Does any field change type between records? ──────────────────────────
cat("\nQ5  the melt's `value` column is a LIST, so the leaf class is available:\n")
kinds <- table(vapply(melted$value, \(v) class(v)[1], character(1)))
cat(sprintf("    leaf classes across all %d leaves: %s\n", nrow(melted),
            paste(sprintf("%s=%d", names(kinds), kinds), collapse = ", ")))
cat("    NOTE `NULL` IS ONE OF THOSE CLASSES, which is Q4's finding again: the\n")
cat("    melt keeps written nulls as NULL-valued rows.\n")
cat("    ENTRY 15 RECORDED AN rrapply TYPE CHECK THAT GROUPED LEAF CLASSES BY\n")
cat("    FIELD AND SO MARKED EVERY OBJECT AS VARYING. The check above is\n")
cat("    deliberately a global census and makes no per-field claim, and the\n")
cat("    reason is structural: the melt reports LEAVES, so a field whose value\n")
cat("    is an object contributes no row of its own — only its scalar\n")
cat("    descendants do. `uses_from_macos`, strings on 1,163 formulae and\n")
cat("    OBJECTS on 632, therefore has no single row to compare. rrapply cannot\n")
cat("    answer question 5, and grouping leaf classes by field is the wrong\n")
cat("    answer that looks like the right one.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
# L1 is the record index, so bottle/stable/files/<platform> lands in L5, not L4.
# The first draft asked L4 and got `files, rebuild, root_url` — off by one, the
# same mistake entry 17 recorded against this tool's melt layout.
files <- melted[!is.na(melted$L2) & melted$L2 == "bottle" &
                !is.na(melted$L4) & melted$L4 == "files", ]
plat <- sort(unique(files$L5))
cat(sprintf("\nQ6  bottle/stable/files/<key> is L5 (L1 is the RECORD INDEX):\n"))
cat(sprintf("    %d distinct L5 values — %s …\n", length(plat),
            paste(head(plat, 6), collapse = ", ")))
vplat <- sort(unique(melted$L3[!is.na(melted$L2) & melted$L2 == "variations"]))
cat(sprintf("    variations/<key> is L3: %d distinct — %s …\n", length(vplat),
            paste(head(vplat, 6), collapse = ", ")))
cat("    THE MELT PUTS THE PLATFORM NAMES IN A COLUMN, which is the closest any\n")
cat("    R tool comes to treating keys as data — and it does exactly the same to\n")
cat("    every genuine field name, so it is a REPRESENTATION and not a verdict.\n")
cat("    That is the honest position: rrapply neither answers question 6 nor\n")
cat("    gets it wrong, where jsonlite and pandas answer it wrongly by building\n")
cat("    the keys into a schema.\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t0 <- Sys.time()
tbl <- data.frame(
  name = vapply(doc, \(f) f$name, character(1)),
  desc = vapply(doc, \(f) f$desc %||% NA_character_, character(1)),
  homepage = vapply(doc, \(f) f$homepage %||% NA_character_, character(1)))
cat(sprintf("\nQ8  %d rows x %d, %.1fs — and rrapply did none of it. Its verbs are\n",
            nrow(tbl), ncol(tbl), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    `prune`/`melt`/`bind`/`unmelt`, none of which selects three fields.\n")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
ex <- melted[!is.na(melted$L2) & melted$L2 == "executables", ]
cat(sprintf("\nQ9  executables leaves in the melt: %d rows, from %d distinct formulae\n",
            nrow(ex), length(unique(ex$L1))))
cat("    A formula with NO executables contributes NO ROWS, so the melt has\n")
cat("    silently dropped the very rows question 9 says to keep. That is the\n")
cat("    melt working as designed and failing the question.\n")

# ── Q10. Flatten the deepest array into rows — and THE bind TEST. ────────────
res <- melted[!is.na(melted$L2) & melted$L2 == "patches" & !is.na(melted$L4) &
              melted$L4 == "resolves", ]
cat(sprintf("\nQ10 patches/resolves leaves in the melt: %d rows\n", nrow(res)))
cat("    Those are LEAVES — each resolve contributes `id` and `type` — so the\n")
cat("    557 resolves appear as 1,114 rows and rebuilding the pair is a reshape.\n")

cat("\n     ══ THE bind TEST, fourth point on the escalation ══\n")
t0 <- Sys.time()
bound <- tryCatch(rrapply(doc, how = "bind"), error = function(e) e)
if (inherits(bound, "error")) {
  cat(sprintf("     rrapply(how='bind') ERRORS: %s\n", conditionMessage(bound)))
} else {
  na_frac <- mean(is.na(as.matrix(bound[, vapply(bound, is.atomic, logical(1))])))
  cat(sprintf("     %d rows x %d cols in %.1fs, %.1f%% NA\n", nrow(bound), ncol(bound),
              as.numeric(difftime(Sys.time(), t0, units = "secs")), 100 * na_frac))
  cat("     entry 14: 20,000 x 50, the only list-column-free extract in either\n")
  cat("     language. entry 17: 36 columns at 64% NA. entry 18: 100 x 37,006 at\n")
  cat("     98.1% NA. This is the fourth, and the prediction above said it would\n")
  cat("     be very wide because two keyed collections give `bind` a column per\n")
  cat("     platform path. Read the number against that.\n")
}

# ── Q11. Find every path whose value matches something. ──────────────────────
chr <- vapply(melted$value, \(v) is.character(v) && length(v) == 1, logical(1))
vals <- unlist(melted$value[chr])
hit_n <- chr; hit_n[chr] <- startsWith(vals, "http")
hit_s <- chr; hit_s[chr] <- grepl("^https?://", vals)
cat(sprintf("\nQ11 http-prefixed leaves %d, ^https?:// leaves %d\n", sum(hit_n), sum(hit_s)))
cat(sprintf("    distinct folded paths: %d naive, %d strict\n",
            length(unique(folded[hit_n])), length(unique(folded[hit_s]))))
cat("    THE MELT MAKES THIS THE EASIEST Q11 IN R. One boolean over a column,\n")
cat("    no recursion — the only tool in this directory where question 11 is\n")
cat("    not twenty lines. Compare purrr's hand-written walk.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat(sprintf("\nQ12 the melt IS the flattest honest table: %d rows x %d, one leaf per row.\n",
            nrow(melted), ncol(melted)))
cat("    Nothing is lost except the object/array distinction and the nulls.\n")
cat("    It is also not RECTANGULAR in god's sense — it is a long-format edge\n")
cat("    list, and turning it into one row per formula is `unmelt` or `bind`.\n")
