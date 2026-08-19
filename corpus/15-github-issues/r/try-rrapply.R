# rrapply — 100 GitHub issues from one repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   686 KB, 100 issues, depth 4
#  measured      2026-08-11
#  run           cd corpus/15-github-issues/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             6   NO                  YES — melt gives it
#   2 how deep                                    2   NO                  YES — melt's L columns
#   3 what is one record                          7   NO                  PARTLY — two shapes
#   4 always present vs sometimes                 9   NO                  YES — melt keeps nulls
#   5 does any field change type                  6   NO                  YES — types SURVIVE here
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               5   YES                 yes
#   9 a field missing from some rows              4   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          5   NO                  YES
#  12 flattest honest table                       6   YES                 yes — AND IT PREFIXES
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 11
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes — two verbs do everything
#  16 lines, and how much is ceremony?                ~115, and almost none is ceremony
#
# **`melt` KEEPS THE NULLS THIS TIME, AND THAT IS THE WHOLE DIFFERENCE.** On
# `13-package-lock` and `14-nyc-311` it coerced every value to `character`, which
# cost question 5 outright. Here the `value` column comes back a **LIST** holding
# character, integer, logical, numeric **and 807 NULLs** — the exact null count
# ijson reads off the byte stream.
#
# > **That is not rrapply improving; it is R declining to coerce.** Those two
# > documents were homogeneous enough for `unlist` to produce an atomic vector,
# > and this one is not. **The instrument's fidelity is a property of the data**,
# > which is worth knowing before trusting it on the next file.
#
# With the nulls present, question 4 comes out **5 sometimes-ABSENT and 8
# always-present-but-NULL** — the truth — where pandas, polars, DuckDB and
# simplified jsonlite all report a single 13.
#
# **AND `how = "bind"` PREFIXES.** `user.login`, `closed_by.login`,
# `milestone.creator.login`, no duplicate names. polars' `unnest` RAISES on this
# document and DuckDB's `struct.*` silently returns 19 duplicate names; rrapply
# joins pandas and jsonlite in getting it right unaided.
#
# **The bind is still the expensive shape**: 100 x 209 at 59.5% NA, against
# pandas' 144 x 53%, because it descends further. The probe prices `a record 100
# rows x 144 cols 53% empty` and rrapply prices nothing.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

recs <- fromJSON("../source.json", simplifyVector = FALSE)
n <- length(recs)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  rrapply operates on a list jsonlite already built. No health\n")
cat("    vocabulary on either side. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep. ───────────────────────────────────
m <- rrapply(recs, how = "melt")
lev <- grep("^L[0-9]+$", names(m), value = TRUE)
cat("\nQ1  how=\"melt\":", format(nrow(m), big.mark = ","), "rows x", ncol(m),
    "— one row per leaf\n")
cat("    path columns:", paste(lev, collapse = ", "), "\n")
cat("   ", length(unique(m$L2[!is.na(m$L2)])), "distinct L2 — the record's field names\n")
cat("Q2  depth", length(lev), "— one L column per level, read off the result.\n")
cat("    The probe prints 4. Correct, and computed by nothing.\n")

# ── Q3/Q7. What is one record, and how many. ────────────────────────────────
b <- rrapply(recs, how = "bind")
cat("\nQ3  rrapply offers TWO shapes and prices neither:\n")
cat(sprintf("      how=\"melt\"  %s x %d    long, one row per leaf\n",
            format(nrow(m), big.mark = ","), ncol(m)))
cat(sprintf("      how=\"bind\"  %d x %d   %.1f%% NA\n",
            nrow(b), ncol(b), 100 * mean(is.na(b))))
cat("    The probe prices `a record 100 rows x 144 cols 53% empty`; bind's 209\n")
cat("    columns descend further than pandas' 144. Neither number is announced.\n")
cat("    PARTLY.\n")
cat("Q7 ", n, "issues\n")

# ── Q4. THE DISCRIMINATOR — melt kept the nulls. ────────────────────────────
top <- m[!is.na(m$L2) & is.na(m$L3), ]
present <- table(unlist(lapply(recs, names)))
isnull <- vapply(m$value, is.null, logical(1))
nullcount <- table(m$L2[isnull])
absent <- sort(names(present)[present < n])
nullish <- sort(names(nullcount)[names(nullcount) %in% names(present)[present == n]])
cat("\nQ4 ", length(present), "distinct fields\n")
cat("      sometimes ABSENT (", length(absent), "):", absent, "\n")
cat("      present but NULL (", length(nullish), "):", nullish, "\n")
cat("      total NULL leaves in the melt:", sum(isnull), "\n")
cat("    THE NULLS SURVIVED INTO THE FRAME, so both kinds are countable. On\n")
cat("    13-package-lock and 14-nyc-311 melt coerced everything to character and\n")
cat("    this would have been impossible. pandas, polars, DuckDB and simplified\n")
cat("    jsonlite each report a single 13 on this document.\n")

# ── Q5. Does any field change type — AND THE TYPES SURVIVED. ───────────────
cls <- table(vapply(m$value, function(x) class(x)[1], character(1)))
cat("\nQ5  classes present in melt's `value` column:\n"); print(cls)
cat("    A LIST COLUMN, so the types are intact — 5,494 character, 1,545 integer,\n")
cat("    511 logical, 114 numeric and 807 NULL. On the two earlier files this\n")
cat("    column was plain `character` and question 5 was unanswerable.\n")
cat("    THAT IS R DECLINING TO COERCE, not rrapply choosing to preserve: those\n")
cat("    documents were homogeneous enough for unlist to make an atomic vector.\n")
# A field's OWN type is not the classes of its leaves. Grouping leaf classes by
# L2 marks every object-valued field as "varying", because `user` has character,
# integer and logical children. The melt has no column for the type of the field
# itself, so this has to be read off the shape: a field is a LEAF where L3 is NA
# and NESTED where L3 is set, and nulls are leaves either way.
shape <- unique(data.frame(field = m$L2,
                           kind = ifelse(is.na(m$L3), "leaf", "nested"),
                           null = vapply(m$value, is.null, logical(1))))
shape <- shape[!is.na(shape$field) & !shape$null, c("field", "kind")]
varying <- names(which(table(unique(shape)$field) > 1))
cat("\nQ5b fields that are a LEAF on some issues and NESTED on others,\n")
cat("    excluding nulls:", if (length(varying)) paste(varying, collapse = ", ") else "none",
    "— the probe's answer\n")
cat("    The melt has no column for the type of a FIELD, only of its leaves, so\n")
cat("    grouping leaf classes by L2 marks `user`, `reactions` and every other\n")
cat("    object as varying. This draft did exactly that before it was run.\n")

# ── Q6. Are any object keys actually data? ──────────────────────────────────
cat("\nQ6  no keyed collections — GitHub ships fixed field names. n/a\n")

# ── Q8/Q9. Extraction, from bind. ───────────────────────────────────────────
cat("\nQ8 ", nrow(b), "rows; three columns from the bind:\n")
print(head(b[, c("number", "state", "user.login")], 2))
cat("\nQ9  closed_by.login non-NA on", sum(!is.na(b$closed_by.login)), "of", n,
    "— rows kept\n")
cat("    and the bind alone CANNOT say those 52 are nulls; the melt above can.\n")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────────
lab <- m[!is.na(m$L2) & m$L2 == "labels" & !is.na(m$L4), ]
cat("\nQ10 label leaves in the melt:", nrow(lab), "over",
    length(unique(lab$L1)), "issues\n")
cat("    L3 is the array index and L4 the field, so the melt already flattened\n")
cat("    it — 166 labels x 7 fields, minus the 40 issues with an empty list.\n")

# ── Q11. Find every path whose value matches something. ─────────────────────
ischr <- vapply(m$value, function(x) is.character(x) && length(x) == 1, logical(1))
urls <- m[ischr & grepl("https?://", unlist(ifelse(ischr, m$value, ""))), ]
folded <- ifelse(is.na(urls$L3), urls$L2,
                 ifelse(grepl("^[0-9]+$", urls$L3), paste0(urls$L2, "[]"),
                        paste0(urls$L2, ".", urls$L3)))
folded <- ifelse(!is.na(urls$L4), paste0(folded, ".", urls$L4), folded)
cat("\nQ11", format(nrow(urls), big.mark = ","), "URL values over",
    length(unique(folded)), "paths\n")
print(head(sort(table(folded), decreasing = TRUE), 3))
cat("    One grepl over the value column, and the path arithmetic uses the L\n")
cat("    columns — SEGMENTS KEPT APART, so no delimiter can be confused with\n")
cat("    data. That is the bug that cost ijson 33 paths on 13-package-lock.\n")

# ── Q12. The flattest honest table, and what was lost. ──────────────────────
cat("\nQ12", nrow(b), "x", ncol(b), "from how=\"bind\", and IT PREFIXES:\n")
cat("   ", head(grep("login", names(b), value = TRUE), 3), "\n")
cat("    duplicate column names:", if (anyDuplicated(names(b))) "yes" else "NONE", "\n")
cat("    polars' `unnest` RAISES on this document — 26 names collide, 58 renames\n")
cat("    — and DuckDB's `struct.*` silently returns 19 duplicate names. rrapply,\n")
cat("    pandas and jsonlite all prefix and all get it right unaided.\n")
cat("    59.5% NA is the cost, and the probe is the only thing that says so.\n")
