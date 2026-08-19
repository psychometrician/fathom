# jsonlite — 200 OpenLibrary search results
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   64 KB, 200 docs, depth 4
#  measured      2026-08-11
#  run           cd corpus/17-openlibrary/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   CANNOT
#   1 what is in here                             5   NO                  PARTLY
#   2 how deep                                    3   NO                  PARTLY
#   3 what is one record                          12  NO                  PARTLY — it CHOOSES
#   4 always present vs sometimes                 6   NO                  YES
#   5 does any field change type                  5   NO                  YES — correctly none
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                             4   NO                  yes — both answers
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          8   NO                  by hand
#  12 flattest honest table                       5   YES                 yes
#  13 needed the shape in advance?                    NO for 3, 4, 5, 7
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~110
#
# **`fromJSON()` ANSWERS QUESTION 3 BY CHOOSING, AND HERE IT CHOOSES WELL.** One
# call returns a list whose `docs` element is a **200 x 17 data.frame** with the
# five array fields as list-columns — the probe's second candidate, built unasked.
# On `13-package-lock` the same call declined, because those records lived in a
# keyed object rather than an array. **The guess fires when a JSON array
# announces the shape.**
#
# **WHAT IT DOES NOT DO IS THE SPLIT.** The probe prints
# `└─ or 4 tables, split on ebook_access — 16% empty`, halving the emptiness.
# `split(df, df$ebook_access)` produces them in base R once the field is known,
# and nothing in jsonlite searched for it. Of the six always-present fields,
# `edition_count` makes it worse and `public_scan_b` changes nothing.
#
# **AND THE SIMPLIFIED FRAME KEEPS THE TOP-LEVEL FIELDS**, which the Python
# frames do not: `fromJSON` returns a LIST whose other seven elements are
# `numFound`, `q`, `documentation_url` and the rest. So jsonlite answers question
# 7 with both numbers and finds the one URL, where pandas and polars — which
# frame `docs` — report none of one.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

doc  <- fromJSON("../source.json")
recs <- fromJSON("../source.json", simplifyVector = FALSE)$docs
df   <- doc$docs
n    <- nrow(df)
allf <- sort(unique(unlist(lapply(recs, names))))
holes <- mean(sapply(recs, function(r) sum(!(allf %in% names(r))))) / length(allf)

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
cat("\nQ0  fromJSON parses and reports nothing: no duplicate-key warning, no\n")
cat("    big-integer notice, no NaN. It errors on malformed JSON and is silent\n")
cat("    on every silent damage. CANNOT.\n")

# ── Q1. What is in here. ───────────────────────────────────────────────────
cat("\nQ1  top level:", names(doc), "\n")
cat("Q1  the records carry", length(allf), "distinct fields\n")
cat("    PARTLY — no survey verb and no path enumeration; the probe prints 31\n")
cat("    distinct paths without being told anything.\n")

# ── Q2. How deep does it go. ───────────────────────────────────────────────
cat("\nQ2  no depth verb. The FRAME hints:", sum(sapply(df, is.list)),
    "columns are list-columns\n")
cat("    of character vectors, so the nesting is 4 — read off the classes by\n")
cat("    hand. THE PROBE PRINTS 4. PARTLY.\n")

# ── Q3. THE SPLIT. ─────────────────────────────────────────────────────────
cat("\nQ3  fromJSON returned a", class(df)[1], paste(dim(df), collapse = " x "),
    "for `docs`, UNASKED —\n")
cat(sprintf("    the probe's second candidate, priced there at %.0f%% empty.\n",
            100 * holes))
cat("    On 13-package-lock the same call DECLINED: those records lived in a\n")
cat("    keyed object, and the guess needs a JSON array.\n")
cat("\nQ3  what it does NOT do is the split the probe prints:\n")
cat("      └─ or 4 tables, split on ebook_access — 16% empty\n")
for (kind in names(sort(table(df$ebook_access), decreasing = TRUE))) {
  g <- Filter(function(r) r$ebook_access == kind, recs)
  fs <- sort(unique(unlist(lapply(g, names))))
  h <- mean(sapply(g, function(r) sum(!(fs %in% names(r))))) / length(fs)
  cat(sprintf("      %-16s %3d x %3d cols  %3.0f%% empty\n", kind, length(g),
              length(fs), 100 * h))
}
cat("    `split(df, df$ebook_access)` gives those in base R once the field is\n")
cat("    known. Of the six always-present fields, edition_count makes it WORSE\n")
cat("    and public_scan_b changes nothing. Choosing is the fourth operation.\n")

# ── Q7. How many records. ─────────────────────────────────────────────────
cat("\nQ7 ", n, "docs — and fromJSON KEPT THE TOP-LEVEL FIELDS, so:\n")
cat("      numFound", format(doc$numFound, big.mark = ","),
    "· num_found", format(doc$num_found, big.mark = ","), "· start", doc$start, "\n")
cat("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. pandas and polars frame\n")
cat("    `docs` and cannot see either number.\n")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
present <- table(unlist(lapply(recs, names)))
nn <- sum(sapply(recs, function(r) sum(sapply(r, is.null))))
cat("\nQ4  always", sum(present == n), "· sometimes", sum(present < n),
    "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))
cat("    the records hold", nn, "nulls, so the simplified frame's NA and the\n")
cat("    list's `names()` agree. On 15-github-issues they did not: the frame\n")
cat("    reported a single 13 for 5 absences plus 8 nulls.\n")

# ── Q5. Does any field change type. ───────────────────────────────────────
json_type <- function(v) if (is.null(v)) "null" else if (is.list(v))
  (if (is.null(names(v))) "array" else "object") else class(v)[1]
kinds <- lapply(setNames(names(present), names(present)), function(k)
  unique(sapply(Filter(function(r) !is.null(r[[k]]), recs),
                function(r) json_type(r[[k]]))))
varying <- Filter(function(v) length(v) > 1, kinds)
cat("\nQ5  fields whose JSON type varies:",
    if (length(varying)) paste(names(varying), collapse = ", ") else "none",
    "— the probe's answer\n")
cat("    DuckDB's `unnest` route reports ELEVEN on this document, every one an\n")
cat("    invented null.\n")

# ── Q6. Are any object keys actually data? ────────────────────────────────
cat("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA\n")
cat("    section is empty for this file.\n")

# ── Q8/Q9. Extraction. ────────────────────────────────────────────────────
cat("\nQ8 ", n, "rows x 3 cols\n")
print(head(df[, c("title", "edition_count", "ebook_access")], 2))
cat("\nQ9  cover_i non-NA on", sum(!is.na(df$cover_i)), "of", n, "— rows kept\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────
an <- data.frame(key = rep(df$key, lengths(df$author_name)),
                 author = unlist(df$author_name))
cat("\nQ10", nrow(an), "author rows;", sum(lengths(df$author_name) == 0),
    "doc has none\n")
cat("    FIVE fields are list-columns and every one is ALSO sometimes absent.\n")

# ── Q11. Find every path whose value matches something — by hand. ────────
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nms <- names(x)
    for (i in seq_along(x))
      find_url(x[[i]], if (is.null(nms)) paste0(p, "[]") else paste0(p, ".", nms[i]))
  } else if (is.character(x)) {
    k <- sum(grepl("https?://", x))
    # inherits = FALSE, or the environment reaches base:: for names like `url`.
    if (k > 0) assign(p, get0(p, hits, inherits = FALSE, ifnotfound = 0) + k, hits)
  }
}
find_url(fromJSON("../source.json", simplifyVector = FALSE))
cat("\nQ11 URL-valued paths:\n")
for (k in ls(hits)) cat("   ", k, get(k, hits, inherits = FALSE), "\n")
cat("    ONE URL, at the TOP LEVEL. Eight lines of recursion, starting at the\n")
cat("    root — which is why it is found at all. jqr does it in one expression.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────
cat("\nQ12", n, "x", ncol(df), sprintf("at %.0f%% empty, five list-columns.\n",
                                       100 * holes))
cat("    NOTHING COLLIDES — these records have no nested OBJECTS, only arrays of\n")
cat("    scalars, so flatten() has nothing to prefix and polars' `unnest` has\n")
cat("    nothing to clash on. (It RAISED on 15-github-issues.)\n")
cat("    rrapply's `bind` expands those five arrays positionally into 36 columns\n")
cat("    at 64% NA — worse than leaving them alone.\n")
