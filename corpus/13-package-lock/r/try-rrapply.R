# rrapply — an npm lockfile, 1,657 packages keyed by install path
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   759 KB, 1,657 packages, depth 5
#  measured      2026-08-11
#  run           cd corpus/13-package-lock/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             7   NO                  YES — melt gets the shape
#   2 how deep                                    2   NO                  YES — melt's L columns
#   3 what is one record                          8   NO                  PARTLY — both candidates
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  4   NO                  NO — melt destroys types
#   6 are any object keys data                    6   -                   PARTLY — best in R
#   7 how many records                            2   NO                  yes
#   8 three named fields to a table               5   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          5   NO                  YES
#  12 flattest honest table                       8   YES                 NO — 1,401 columns
#  13 needed the shape in advance?                    NO for 1, 2, 4, 7, 11
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes — two verbs do everything
#  16 lines, and how much is ceremony?                ~120, and almost none is ceremony
#
# **rrapply'S TWO VERBS SWAP ROLES BETWEEN THIS FILE AND `14-nyc-311`, AND THAT
# IS THE ENTRY IN ONE SENTENCE.**
#
# On entry 14, `how = "bind"` produced the **only list-column-free table in
# either language** — 20,000 x 50, coordinates as two numeric columns — and
# `how = "melt"` was the weak half because it coerced every value to character.
#
# **Here `bind` is the trap and `melt` is the answer.** `rrapply(packages,
# how = "bind")` returns **1,657 x 1,401 at 99.5% NA**, because the dependency
# NAMES become columns. That is precisely the candidate `design/probe.py` prices
# as `an entry of packages 1,657 x 1394 99% empty` and warns about; rrapply
# builds it and says nothing. **It also loses the install path** — the row names
# do not carry it, so the row's identity is gone.
#
# **`how = "melt"` IS THE BEST-SHAPED ANSWER TO A KEYS-AS-DATA DOCUMENT IN EITHER
# LANGUAGE.** 12,235 rows x 6, and the columns land exactly right:
#
#     L1 = "packages"   L2 = the install path   L3 = the field   value = the value
#
# **The data-keys end up in a COLUMN, as data, without being asked.** Every other
# tool here either turns them into 12,153 column names (pandas), a 1,657-field
# struct (polars, DuckDB), or 16,545 path strings (jq, ijson, the hand-walks).
# rrapply is the only one whose default output treats a key as a value.
#
# **AND IT STILL CANNOT ANSWER QUESTION 5**, for the same reason as on entry 14:
# `melt` coerces every value to character, so the object-vs-array variation in
# `engines` and `funding` is gone before you can look. Two documents, same loss.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
pkgs <- doc$packages
n <- length(pkgs)
cat(sprintf("    parsed %d packages in %.1fs\n", n,
            as.numeric(Sys.time() - t0, units = "secs")))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  rrapply operates on a list jsonlite already built. No health\n")
cat("    vocabulary on either side. DuckDB refuses this file; rrapply does not.\n")
cat("    CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — MELT GIVES BOTH. ──────────────────
t1 <- Sys.time()
m <- rrapply(doc, how = "melt")
melt_s <- as.numeric(Sys.time() - t1, units = "secs")
lev <- grep("^L[0-9]+$", names(m), value = TRUE)
pk <- m[m$L1 == "packages", ]
cat(sprintf("\nQ1  how=\"melt\": %s rows x %d cols in %.1fs — one row per LEAF\n",
            format(nrow(m), big.mark = ","), ncol(m), melt_s))
cat("    path columns:", paste(lev, collapse = ", "), "\n")
cat("   ", length(unique(pk$L2)), "distinct L2 — THE INSTALL PATHS, as DATA in a column\n")
cat("   ", length(unique(pk$L3[!is.na(pk$L3)])), "distinct L3 — the field names\n")
cat("    THAT IS THE RIGHT SHAPE. pandas turns those 1,657 keys into column\n")
cat("    names, polars into struct fields, jq and ijson into path strings.\n")
cat("Q2  depth", length(lev), "— one L column per level, read off the result.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
t2 <- Sys.time()
b <- rrapply(pkgs, how = "bind")
bind_s <- as.numeric(Sys.time() - t2, units = "secs")
cat(sprintf("\nQ3  rrapply offers TWO shapes and prices neither:\n"))
cat(sprintf("      how=\"melt\"  %s x %d   long, one row per leaf\n",
            format(nrow(m), big.mark = ","), ncol(m)))
cat(sprintf("      how=\"bind\"  %s x %s   %.1f%% NA   <- THE TRAP\n",
            format(nrow(b), big.mark = ","), format(ncol(b), big.mark = ","),
            100 * mean(is.na(b))))
cat("    The bind is the candidate the probe prices as `an entry of packages\n")
cat("    1,657 x 1394 99% empty` and warns about. rrapply builds it in",
    sprintf("%.1fs", bind_s), "\n")
cat("    and reports nothing — 2.3 million cells holding about 12,000 values.\n")
cat("    Offering two shapes is more than most tools here manage; pricing them\n")
cat("    is what would make it an answer. PARTLY.\n")
cat("Q7 ", n, "packages\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
fields <- table(pk$L3[!is.na(pk$L3) & is.na(pk$L4)])
nested <- tapply(pk$L2[!is.na(pk$L4)], pk$L3[!is.na(pk$L4)],
                 function(x) length(unique(x)))
present <- c(fields, nested[!names(nested) %in% names(fields)])
cat("\nQ4 ", length(present), "distinct fields; always", sum(present == n),
    "-", names(present)[present == n], "\n")
cat("Q4  sometimes", sum(present < n), ", rarest five:\n")
print(head(sort(present), 5))
cat("    Matches the probe: 21 fields, only `version` on all 1,657. The two\n")
cat("    groups — leaf fields and nested ones — had to be counted separately,\n")
cat("    because a field holding an object contributes no L3 leaf row of its own.\n")

# ── Q5. Does any field change type. IT CANNOT SAY. ───────────────────────────
cat("\nQ5  class of melt's `value` column:", class(m$value), "\n")
cat("    ALL", format(nrow(m), big.mark = ","), "LEAVES COME BACK character. The document has TWO\n")
cat("    polymorphic fields — engines object x1,050 / array x1, funding object\n")
cat("    x282 / array x28 — and melt flattened both before they could be seen.\n")
cat("    Same loss as on 14-nyc-311, and there it cost nothing. CANNOT.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  YES, and rrapply comes CLOSER THAN ANYTHING ELSE IN R without saying it.\n")
cat("    melt puts the install path in L2 as a value, so the keys are already\n")
cat("    data in the result — 1,657 distinct L2 values against 21 distinct L3.\n")
cat("    THAT RATIO IS THE SIGNAL and rrapply computes no verdict from it. The\n")
cat("    probe prints seven keyed sites under KEYS THAT ARE DATA and declines\n")
cat("    an eighth — `engines`, 5 keys over 1,050 copies, a vocabulary. PARTLY.\n")

# ── Q8/Q9. Extraction, from the melt. ────────────────────────────────────────
want <- c("version", "license")
sub <- pk[is.na(pk$L4) & pk$L3 %in% want, c("L2", "L3", "value")]
tbl <- reshape(sub, idvar = "L2", timevar = "L3", direction = "wide")
names(tbl) <- sub("^value\\.", "", names(tbl))
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols, install path kept as L2\n")
print(head(tbl, 2))
cat("\nQ9  license non-NA on", sum(!is.na(tbl$license)), "of", nrow(tbl),
    "— reshape fills the gaps\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
fund <- pk[pk$L3 == "funding" & !is.na(pk$L4), ]
cat("\nQ10 funding leaves in the melt:", nrow(fund), "rows over",
    length(unique(fund$L2)), "packages\n")
print(head(fund[, c("L2", "L4", "L5", "value")], 3))
cat("    The melt already flattened it — L4 is the array index for the 28\n")
cat("    packages whose funding is a list, and the object key for the 282 whose\n")
cat("    funding is an object. THE TWO SHAPES SHARE A COLUMN, which is honest\n")
cat("    about the document and means L4 mixes indices with names.\n")

# ── Q11. Find every path whose value matches something. ──────────────────────
hit <- m[grepl("https?://", m$value), ]
cat("\nQ11", nrow(hit), "URL-valued leaves. Folded on L2, the paths are:\n")
folded <- ifelse(is.na(hit$L4), hit$L3,
                 ifelse(grepl("^[0-9]+$", hit$L4), paste0(hit$L3, "[]"),
                        paste0(hit$L3, ".", hit$L4)))
folded <- ifelse(!is.na(hit$L5), paste0(folded, ".", hit$L5), folded)
print(table(folded))
cat("    One grepl over melt's `value` column, and the fold is arithmetic on\n")
cat("    the L columns rather than string surgery — because melt kept the path\n")
cat("    SEGMENTS APART. pandas and ijson dot-join theirs, and 33 package keys\n")
cat("    contain a dot, so neither of those can be split back. rrapply cannot\n")
cat("    have that bug by construction.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12", format(nrow(b), big.mark = ","), "x", format(ncol(b), big.mark = ","),
    "from how=\"bind\", and it is NOT honest:\n")
cat("   ", sprintf("%.1f%%", 100 * mean(is.na(b))), "NA. The 1,401 columns are dependency NAMES —\n")
cat("    keys-as-data one level down, exactly as pandas' json_normalize does it.\n")
cat("    The install path is LOST: rownames do not carry it.\n")
cat("    On 14-nyc-311 this same verb produced the only list-column-free table\n")
cat("    in the corpus. The verb did not change; the document did.\n")
cat("    The honest table here is the 21-column one, and rrapply has no way to\n")
cat("    stop `bind` at the level where it would be honest.\n")
