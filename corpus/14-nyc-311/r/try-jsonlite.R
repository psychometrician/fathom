# jsonlite — NYC 311 service requests, the 20,000 most recent
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   28.1 MB, 20,000 records, depth 4
#  measured      2026-08-11
#  run           cd corpus/14-nyc-311/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   CANNOT
#   1 what is in here                             4   NO                  yes
#   2 how deep                                    3   NO                  PARTLY
#   3 what is one record                          4   NO                  PARTLY — it PICKS one
#   4 always present vs sometimes                 8   NO                  YES — but see the trap
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               2   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          7   NO                  by hand
#  12 flattest honest table                       3   NO                  yes — flatten()
#  13 needed the shape in advance?                    NO for 1, 3, 4, 5, 7, 12
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~110, and the URL walk is 7
#
# **jsonlite ANSWERS QUESTION 3 BY MAKING A CHOICE, WHICH NO PYTHON TOOL DOES.**
# `fromJSON("../source.json")` returns a **20,000 x 48 data.frame in 0.8 s**, with
# no shape declared and no columns named. It decided the array elements are rows
# and the union of their keys are columns. That is question 3's answer, arrived at
# silently — it names no alternative and prices nothing, so it is PARTLY, but it
# is more than pandas, polars, DuckDB, glom, jmespath, pydash or jq attempt here.
#
# **AND THEN THE SIMPLIFICATION LAYS A TRAP THAT COSTS QUESTION 4 A FIELD.**
# `location` comes back as a nested data.frame column. R's most natural
# missingness idiom —
#
#     colSums(!is.na(df))
#
# — returns **49 values for a 48-column frame**, because `!is.na()` silently
# expands the nested frame into its two children. The names no longer line up:
# `colSums(!is.na(df))["location"]` is **NA**, not a count. The always-present
# count comes out **14 where the truth is 13**, and nothing warns you. The
# corrected version below walks the columns and gets 13 and 35, matching the
# probe, polars and DuckDB exactly.
#
# **This is the R half of the same lesson entry 25 recorded**: an idiom that is
# right on a flat frame is quietly wrong on a nested one, and only running it
# against a known answer shows the difference.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  fromJSON parses and reports nothing: no duplicate-key warning, no\n")
cat("    big-integer notice, no NaN. It would ERROR on malformed JSON, which is\n")
cat("    a health signal of sorts, and it is silent on every silent damage. CANNOT.\n")

t0 <- Sys.time()
df <- fromJSON("../source.json")
cat(sprintf("    fromJSON: %s in %.1fs\n",
            paste(dim(df), collapse = " x "), as.numeric(Sys.time() - t0, units = "secs")))

# ── Q1. What is in here. ─────────────────────────────────────────────────────
cat("\nQ1 ", ncol(df), "columns, in document order:\n")
print(names(df))

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
cat("\nQ2  jsonlite reports no depth. The frame HINTS at it: `location` is a\n")
cat("    data.frame column whose `coordinates` is a list column, so the nesting\n")
cat("    is 4 levels — but that is read off the classes by hand. PARTLY.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  jsonlite CHOSE: array elements are rows, union of keys are columns.\n")
cat("   ", nrow(df), "rows x", ncol(df), "cols, unasked. It names no alternative\n")
cat("    and prices nothing, so the cost of the choice is invisible. PARTLY.\n")
cat("Q7 ", nrow(df), "records\n")

# ── Q4. Always present vs sometimes — AND THE TRAP. ──────────────────────────
naive <- colSums(!is.na(df))
cat("\nQ4  THE NATURAL IDIOM IS WRONG HERE.\n")
cat("    colSums(!is.na(df)) returns", length(naive), "values for a", ncol(df),
    "column frame,\n")
cat("    because !is.na() expands the nested `location` frame into its children.\n")
cat("    lookup by name breaks: naive[\"location\"] =", naive["location"], "\n")
cat("    it reports", sum(naive == nrow(df)), "always-present columns.\n")

present <- sapply(names(df), function(n) {
  x <- df[[n]]
  if (is.data.frame(x)) sum(!is.na(x[[1]])) else sum(!is.na(x))
})
cat("\nQ4  CORRECTED, walking the columns instead:\n")
cat("    always", sum(present == nrow(df)), "· sometimes", sum(present < nrow(df)),
    "— matches the probe, polars and DuckDB\n")
cat("    rarest five:\n"); print(head(sort(present), 5))

# ── Q5. Does any field change type between records. ──────────────────────────
cls <- sapply(df, function(x) class(x)[1])
cat("\nQ5  column classes:\n"); print(table(cls))
cat("    47 character + 1 data.frame, and NO field varies — the truth. jsonlite\n")
cat("    did NOT coerce `latitude` to numeric; Socrata ships text and it believed\n")
cat("    it, same as pandas, polars and DuckDB.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
odd <- grep("^[^A-Za-z]", names(df), value = TRUE)
cat("\nQ6  no keyed collections. n/a.", length(odd), "names are not identifiers,\n")
cat("    and R needs backticks for them:", odd[1], "\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl <- df[, c("complaint_type", "borough", "created_date")]
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
cat("\nQ9  closed_date present on", sum(!is.na(df$closed_date)), "of", nrow(df),
    "— rows kept\n")
cat("    The union-of-keys simplification filled the gaps with NA. No default\n")
cat("    had to be written, and the absence is indistinguishable from a null —\n")
cat("    harmless here because the document contains ZERO nulls.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co <- do.call(rbind, df$location$coordinates[!sapply(df$location$coordinates, is.null)])
colnames(co) <- c("lon", "lat")
cat("\nQ10", nrow(co), "x", ncol(co), "\n"); print(head(co, 2))

# ── Q11. Find every path whose value matches something — by hand. ────────────
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x) || is.data.frame(x)) {
    nm <- names(x)
    for (i in seq_along(x)) {
      find_url(x[[i]], if (is.null(nm)) paste0(p, "[]") else paste0(p, ".", nm[i]))
    }
  } else if (is.character(x)) {
    n <- sum(grepl("https?://", x))
    # inherits = FALSE, because an environment used as a dictionary otherwise
    # reaches base:: for names like `url`. That cost entry 25 three fields.
    if (n > 0) assign(p, get0(p, hits, inherits = FALSE, ifnotfound = 0) + n, hits)
  }
}
find_url(df, "$[]")
cat("\nQ11 URL-valued paths:\n")
for (k in ls(hits)) cat("   ", k, get(k, hits, inherits = FALSE), "\n")
cat("    Seven lines of hand-written recursion. jsonlite has no path language.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat <- flatten(df)
cat("\nQ12 flatten() gives", nrow(flat), "x", ncol(flat), "\n")
cat("    `location` became location.type and location.coordinates. The latter is\n")
cat("    still a LIST column — the thing god's spec refuses — and it is the only\n")
cat("    one. flatten() is the shortest honest flattening in R.\n")
