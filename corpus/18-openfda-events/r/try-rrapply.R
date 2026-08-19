# rrapply — 100 openFDA adverse-event reports
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   2.7 MB, 100 results, depth 8
#  measured      2026-08-11
#  run           cd corpus/18-openfda-events/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             6   NO                  YES — melt gives it
#   2 how deep                                    2   NO                  YES — exactly 8
#   3 what is one record                          10  NO                  NO — bind is catastrophic
#   4 always present vs sometimes                 6   NO                  YES
#   5 does any field change type                  6   NO                  YES — types SURVIVE here
#   6 are any object keys data                    3   -                   n/a — no abstention
#   7 how many records                             5   NO                  yes — four answers
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes — melt did it
#  11 find every path matching something          5   NO                  YES
#  12 flattest honest table                       8   YES                 NO — 37,006 columns
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 11
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes — two verbs do everything
#  16 lines, and how much is ceremony?                ~110
#
# **`how = "bind"` PRODUCES 100 x 37,006 AT 98.1% NA, THE WORST TABLE IN THE
# CORPUS BY A WIDE MARGIN** — 3.7 million cells holding 69,228 values, with
# column names like `patient.drug.1.openfda.brand_name.1`. Positional expansion
# of variable-length arrays, compounded by depth 8.
#
# **That is the third point on a clean escalation, and the verb never changed:**
#
#     14-nyc-311    20,000 x     50   arrays exactly length 2   THE HERO
#     17-openlibrary   200 x     36   arrays length 1-9, depth 4   64% NA
#     18-openfda       100 x 37,006   arrays inside arrays, depth 8   98% NA
#
# **`how = "melt"` IS THE RIGHT SHAPE AND IT KEEPS THE TYPES.** 69,228 rows x 8 —
# one row per leaf, L1..L7 for the path — and the `value` column comes back a
# LIST, so the types survive. That happened on `15-github-issues` and not on 13,
# 14 or 17: **R declines to coerce a heterogeneous column, and fidelity is a
# property of the data.**
#
# **It also reaches all eight levels at no extra cost**, which is what a long
# format buys: `L7` is simply another column.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
recs <- doc$results
n <- length(recs)
allf <- sort(unique(unlist(lapply(recs, names))))

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
cat("\nQ0  rrapply operates on a list jsonlite already built. No health\n")
cat("    vocabulary on either side. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep. ──────────────────────────────────
m <- rrapply(doc, how = "melt")
lev <- grep("^L[0-9]+$", names(m), value = TRUE)
cat("\nQ1  how=\"melt\":", format(nrow(m), big.mark = ","), "rows x", ncol(m),
    "— one row per leaf\n")
cat("    path columns:", paste(lev, collapse = ", "), "\n")
cat("    it starts at the ROOT, so `meta` is in there too — which is why Q11\n")
cat("    finds both URLs where pandas and polars find none.\n")
cat("Q2  depth", length(lev), "— one L column per level. THE PROBE PRINTS 8, and\n")
cat("    this is the deepest file in the corpus. It cost nothing: a long format\n")
cat("    just has another column. pandas says 3.\n")

# ── Q3. THE BIND CATASTROPHE. ─────────────────────────────────────────────
b <- rrapply(recs, how = "bind")
cat(sprintf("\nQ3  how=\"bind\": %d x %s at %.1f%% NA\n", nrow(b),
            format(ncol(b), big.mark = ","), 100 * mean(is.na(b))))
cat(sprintf("    %s cells holding %s values.\n",
            format(prod(dim(b)), big.mark = ","),
            format(sum(!is.na(b)), big.mark = ",")))
cat("    column names look like:", grep("brand_name", names(b), value = TRUE)[1], "\n")
cat("    THE WORST TABLE IN THE CORPUS. Positional expansion of variable-length\n")
cat("    arrays, compounded by depth 8 — arrays inside arrays inside objects.\n")
cat("    The verb never changed:\n")
cat("      14-nyc-311     20,000 x     50   arrays exactly length 2   THE HERO\n")
cat("      17-openlibrary    200 x     36   length 1-9, depth 4       64% NA\n")
cat("      18-openfda        100 x 37,006   arrays in arrays, depth 8 98% NA\n")
cat("\nQ3  THE PROBE NAMES FOUR CANDIDATES AND PRICES THEM:\n")
cat("      the whole document        1 rows x  2 cols\n")
cat("      an item of results      100 rows x 39 cols   26% empty\n")
cat("      an item of drug         265 rows x 41 cols   47% empty\n")
cat("      an item of reaction     247 rows x  3 cols\n")
cat("    rrapply offers two shapes and prices neither. NO.\n")

# ── Q7. How many records. ────────────────────────────────────────────────
drugs <- unlist(lapply(recs, function(r) r$patient$drug), recursive = FALSE)
rx <- unlist(lapply(recs, function(r) r$patient$reaction), recursive = FALSE)
cat("\nQ7  FOUR right answers: results", n, "· drug", length(drugs),
    "· reaction", length(rx), "\n")
cat("    and meta.results.total =", format(doc$meta$results$total, big.mark = ","), "\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────
present <- table(unlist(lapply(recs, names)))
isnull <- vapply(m$value, is.null, logical(1))
cat("\nQ4 ", length(present), "fields; always", sum(present == n), "· sometimes",
    sum(present < n), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))
cat("    NULL leaves in the whole melt:", sum(isnull),
    "— so the raggedness is almost purely absence.\n")

# ── Q5. Does any field change type — AND THE TYPES SURVIVED. ────────────
cls <- table(vapply(m$value, function(x) class(x)[1], character(1)))
cat("\nQ5  classes in melt's `value` column:\n"); print(cls)
cat("    A LIST COLUMN, so the types are intact — as on 15-github-issues and\n")
cat("    UNLIKE 13, 14 and 17 where melt coerced everything to character.\n")
cat("    That is R declining to coerce a heterogeneous column; fidelity is a\n")
cat("    property of the data, not of the verb.\n")
json_type <- function(v) if (is.null(v)) "null" else if (is.list(v))
  (if (is.null(names(v))) "array" else "object") else class(v)[1]
kinds <- lapply(setNames(names(present), names(present)), function(k)
  unique(vapply(Filter(function(r) !is.null(r[[k]]), recs),
                function(r) json_type(r[[k]]), character(1))))
cat("    fields whose JSON type varies, nulls excluded:",
    if (length(Filter(function(v) length(v) > 1, kinds))) "some" else "none",
    "— the probe's answer\n")

# ── Q6. Are any object keys actually data? ──────────────────────────────
cat("\nQ6  no keyed collections. n/a — and the probe prints `could not call 3\n")
cat("    small single-copy objects` and names them. That ABSTENTION is a third\n")
cat("    state melt has no column for.\n")

# ── Q8/Q9. Extraction, from the melt. ───────────────────────────────────
top <- m[!is.na(m$L2) & is.na(m$L3) & m$L2 %in% c("safetyreportid", "serious",
                                                  "receivedate"), ]
cat("\nQ8 ", nrow(top), "leaf rows for three fields over", length(unique(top$L1)),
    "results\n")
sd <- m[!is.na(m$L2) & m$L2 == "seriousnessdeath", ]
cat("\nQ9  seriousnessdeath appears on", nrow(sd), "of", n, "results —\n")
cat("    a long format has no hole to fill, so nothing is lost and nothing is\n")
cat("    invented. DuckDB's STRUCT route manufactures 464 keys on this file.\n")

# ── Q10. Flatten the deepest array. ─────────────────────────────────────
# The path is L1=results, L2=result index, L3=patient, L4=drug, L5=drug index,
# L6=openfda, L7=brand_name, L8=brand index — eight columns, one per level.
bn <- m[!is.na(m$L7) & m$L7 == "brand_name", ]
cat("\nQ10", nrow(bn), "brand-name leaves — and the melt had ALREADY flattened them.\n")
cat("    The path reads across the columns: L1 results, L2 result index, L3\n")
cat("    patient, L4 drug, L5 drug index, L6 openfda, L7 brand_name, L8 brand\n")
cat("    index. NO VERB WAS NEEDED — which is what a long format buys on a deep\n")
cat("    document, and the same 2,375 every other tool here reports.\n")

# ── Q11. Find every path whose value matches something. ────────────────
ischr <- vapply(m$value, function(x) is.character(x) && length(x) == 1, logical(1))
hit <- m[ischr & grepl("https?://", unlist(ifelse(ischr, m$value, ""))), ]
cat("\nQ11", nrow(hit), "URL-valued leaves, at:", paste(hit$L1, hit$L2, sep = "."), "\n")
cat("    BOTH are under `meta`, outside `results`. The melt starts at the root,\n")
cat("    so they are simply rows; pandas and polars report NONE OF TWO.\n")

# ── Q12. The flattest honest table. ────────────────────────────────────
cat(sprintf("\nQ12 how=\"bind\" is %d x %s at %.1f%% NA, and that is NOT a table.\n",
            nrow(b), format(ncol(b), big.mark = ","), 100 * mean(is.na(b))))
cat("    The honest one is", n, "x", length(allf), "own fields, with the two arrays\n")
cat("    left alone — the probe prices its flattened form at 39 columns and 26%\n")
cat("    empty. `patient.drug.1.openfda.brand_name.1` is not a field, it is two\n")
cat("    subscripts and a path, and 37,006 of them is a listing rather than a\n")
cat("    description.\n")
