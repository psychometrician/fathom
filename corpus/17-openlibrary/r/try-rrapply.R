# rrapply — 200 OpenLibrary search results
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   64 KB, 200 docs, depth 4
#  measured      2026-08-11
#  run           cd corpus/17-openlibrary/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             6   NO                  YES — melt gives it
#   2 how deep                                    2   NO                  YES — melt's L columns
#   3 what is one record                          12  NO                  NO — bind is WORSE here
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  5   NO                  NO — melt destroys types
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                             4   NO                  yes — both answers
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          5   NO                  YES
#  12 flattest honest table                       8   YES                 NO — 36 cols at 64% NA
#  13 needed the shape in advance?                    NO for 1, 2, 4, 7, 11
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes — two verbs do everything
#  16 lines, and how much is ceremony?                ~115
#
# **`how = "bind"` WAS THE HERO ON `14-nyc-311` AND IS THE TRAP HERE, AND THE
# VERB DID NOT CHANGE.** There it produced the corpus's only list-column-free
# table — 20,000 x 50, a coordinate pair as two clean numeric columns — because
# every array was **exactly length 2**. This document's arrays are length **1 to
# 9**, so the same positional expansion gives:
#
#     the honest record table    200 x 17    34% empty
#     rrapply how = "bind"       200 x 36    64% NA
#
# `author_name` becomes `.1` through `.6` and `ia_collection` `.1` through `.9`,
# **nearly doubling the emptiness** and giving 19 columns whose names are
# positions. That is the third document on which rrapply's two verbs have
# swapped roles, and each time the cause was the data rather than the tool.
#
# **`how = "melt"` LOSES THE TYPES AGAIN**, as on entries 13 and 14 and unlike
# 15: the `value` column comes back plain `character`, because this document is
# homogeneous enough for R to coerce. **The instrument's fidelity is a property
# of the data**, which is worth knowing before trusting it on the next file.
#
# **AND NEITHER VERB FINDS THE SPLIT.** The probe prints
# `└─ or 4 tables, split on ebook_access — 16% empty`. rrapply has no group-by at
# all; the four tables need `split()` from base R, with the field named first.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
recs <- doc$docs
n <- length(recs)
allf <- sort(unique(unlist(lapply(recs, names))))
holes <- mean(sapply(recs, function(r) sum(!(allf %in% names(r))))) / length(allf)

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
cat("\nQ0  rrapply operates on a list jsonlite already built. No health\n")
cat("    vocabulary on either side. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep. ──────────────────────────────────
m <- rrapply(doc, how = "melt")
lev <- grep("^L[0-9]+$", names(m), value = TRUE)
cat("\nQ1  how=\"melt\":", format(nrow(m), big.mark = ","), "rows x", ncol(m),
    "— one row per leaf\n")
cat("    path columns:", paste(lev, collapse = ", "), "\n")
cat("    under `docs`: L2 is the RECORD INDEX (", length(unique(m$L2[m$L1 == "docs"])),
    "of them), L3 the field name (",
    length(unique(m$L3[m$L1 == "docs" & !is.na(m$L3)])), "), L4 the array index.\n")
cat("   ", sum(m$L1 != "docs"), "rows sit OUTSIDE `docs` — the page metadata and the\n")
cat("    one URL. melt starts at the ROOT, so they are simply rows, where pandas\n")
cat("    and polars build a frame from `docs` and never see them.\n")
cat("Q2  depth", length(lev), "— one L column per level. THE PROBE PRINTS 4.\n")

# ── Q3. THE SPLIT, and bind's positional expansion. ────────────────────────
b <- rrapply(recs, how = "bind")
cat(sprintf("\nQ3  the honest record table is %d x %d at %.0f%% empty.\n",
            n, length(allf), 100 * holes))
cat(sprintf("Q3  how=\"bind\" gives %d x %d at %.1f%% NA — WORSE.\n",
            nrow(b), ncol(b), 100 * mean(is.na(b))))
cat("    It expands every array POSITIONALLY:",
    paste(head(grep("^author_name", names(b), value = TRUE), 3), collapse = ", "), "...\n")
for (f in c("author_name", "ia_collection")) {
  L <- sapply(recs, function(r) length(r[[f]]))
  cat(sprintf("      %-14s lengths 0-%d, so %d columns\n", f, max(L),
              length(grep(paste0("^", f), names(b)))))
}
cat("    ON 14-nyc-311 THIS VERB WAS THE HERO — the corpus's only list-column-free\n")
cat("    table — because every array there was EXACTLY length 2. The verb did not\n")
cat("    change; the arrays did.\n")
cat("\nQ3  and the probe offers a shape rrapply has no verb for at all:\n")
cat("      └─ or 4 tables, split on ebook_access — 16% empty\n")
for (kind in names(sort(table(sapply(recs, `[[`, "ebook_access")), decreasing = TRUE))) {
  g <- Filter(function(r) r$ebook_access == kind, recs)
  fs <- sort(unique(unlist(lapply(g, names))))
  h <- mean(sapply(g, function(r) sum(!(fs %in% names(r))))) / length(fs)
  cat(sprintf("      %-16s %3d x %3d cols  %3.0f%% empty\n", kind, length(g),
              length(fs), 100 * h))
}
cat("    `split(recs, sapply(recs, `[[`, \"ebook_access\"))` produces those in base\n")
cat("    R once the field is known. rrapply has no group-by, and nothing here\n")
cat("    chose the field. NO.\n")

# ── Q7. How many records. ─────────────────────────────────────────────────
cat("\nQ7 ", n, "docs in the array — the document says numFound =",
    format(doc$numFound, big.mark = ","), "\n")
cat("    num_found =", format(doc$num_found, big.mark = ","), ", start =", doc$start, "\n")
cat("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. This is a PAGE, and the\n")
cat("    melt above carries both because it starts at the root.\n")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
present <- table(unlist(lapply(recs, names)))
cat("\nQ4 ", length(present), "distinct fields; always", sum(present == n),
    "· sometimes", sum(present < n), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))
nn <- sum(sapply(recs, function(r) sum(sapply(r, is.null))))
cat("    the records hold", nn, "nulls, so presence-counting and hole-counting\n")
cat("    agree. On 15-github-issues they did not, and split the tools 9-4.\n")

# ── Q5. Does any field change type. ───────────────────────────────────────
cat("\nQ5  class of melt's `value` column:", class(m$value), "\n")
cat("    ALL", format(nrow(m), big.mark = ","), "LEAVES COME BACK character, so the melt cannot\n")
cat("    answer this — same loss as on entries 13 and 14, and unlike 15 where the\n")
cat("    document was heterogeneous enough that R declined to coerce.\n")
json_type <- function(v) if (is.null(v)) "null" else if (is.list(v))
  (if (is.null(names(v))) "array" else "object") else class(v)[1]
kinds <- lapply(setNames(names(present), names(present)), function(k)
  unique(sapply(Filter(function(r) !is.null(r[[k]]), recs), function(r) json_type(r[[k]]))))
cat("    From the LIST instead:",
    if (length(Filter(function(v) length(v) > 1, kinds))) "some vary" else "none vary",
    "— the probe's answer.\n")

# ── Q6. Are any object keys actually data? ────────────────────────────────
cat("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA\n")
cat("    section is empty for this file.\n")

# ── Q8/Q9. Extraction. ────────────────────────────────────────────────────
cat("\nQ8 ", nrow(b), "rows; three columns from the bind:\n")
print(head(b[, c("title", "edition_count", "ebook_access")], 2))
cat("\nQ9  cover_i non-NA on", sum(!is.na(b$cover_i)), "of", n, "— rows kept\n")

# ── Q10. Flatten the deepest array into rows. ─────────────────────────────
an <- m[m$L1 == "docs" & !is.na(m$L3) & m$L3 == "author_name", ]
cat("\nQ10 author_name leaves in the melt:", nrow(an), "over",
    length(unique(an$L2)), "records\n")
cat("    L4 is the array index, so the melt had already flattened it — no verb\n")
cat("    was needed, and the one doc without authors simply has no rows.\n")

# ── Q11. Find every path whose value matches something. ──────────────────
hit <- m[grepl("https?://", m$value), ]
cat("\nQ11", nrow(hit), "URL-valued leaf:", hit$L1, "\n")
cat("    ONE URL IN THE DOCUMENT, and it is a TOP-LEVEL field. The melt starts\n")
cat("    at the root so it is simply a row; pandas and polars build a frame from\n")
cat("    `docs` and report NONE OF ONE.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────
cat(sprintf("\nQ12 how=\"bind\" is %d x %d at %.1f%% NA, and that is NOT the honest table.\n",
            nrow(b), ncol(b), 100 * mean(is.na(b))))
cat(sprintf("    The honest one is %d x %d at %.0f%% empty, with five list-columns.\n",
            n, length(allf), 100 * holes))
cat("    bind traded five list-columns for 19 POSITIONAL ones and nearly doubled\n")
cat("    the emptiness. `author_name.4` is not a field, it is a subscript, and\n")
cat("    nothing in the output says which of the 36 columns are real.\n")
cat("    The seven top-level fields are absent from both, which is why the probe\n")
cat("    names `the whole document 1 rows x 8 cols` as its own candidate.\n")
