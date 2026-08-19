# jsonlite — 100 GitHub issues from one repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   686 KB, 100 issues, depth 4
#  measured      2026-08-11
#  run           cd corpus/15-github-issues/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   CANNOT
#   1 what is in here                             5   NO                  PARTLY
#   2 how deep                                    3   NO                  PARTLY
#   3 what is one record                           5   NO                  PARTLY — it CHOOSES
#   4 always present vs sometimes                12   NO                  BOTH ANSWERS — see below
#   5 does any field change type                  5   NO                  yes
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              4   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          9   NO                  by hand
#  12 flattest honest table                       4   YES                 yes — flatten()
#  13 needed the shape in advance?                    NO for 3, 4, 5, 7
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~120, and the URL walk is 9
#
# **THE SAME LIBRARY GIVES BOTH ANSWERS TO QUESTION 4, AND THE FLAG THAT DECIDES
# IT IS ABOUT SOMETHING ELSE ENTIRELY.**
#
#     fromJSON(file)                       -> a frame; reports 13 fields missing
#     fromJSON(file, simplifyVector=FALSE) -> a list;  names() gives 5 and 8
#
# The truth is **5 sometimes-ABSENT and 8 always-present-but-NULL**. The frame
# collapses them, because once a row exists absent and null are the same hole.
# **`simplifyVector` is documented as controlling whether arrays become vectors**
# — nothing about it suggests it decides whether you can answer a question about
# missingness, and it does.
#
# **AND `fromJSON()` ANSWERS QUESTION 3 BY CHOOSING, WHICH IS MORE THAN ANY
# PYTHON TOOL DOES.** It returns a **100 x 36 data.frame** unasked, with the
# nested objects as nested data.frames. On `13-package-lock` the same call
# declined, because those records lived in a keyed object rather than an array.
# **The guess fires when a JSON array announces the shape, and not otherwise.**
#
# **THE `$` PARTIAL-MATCHING TRAP HAS FOUR OPPORTUNITIES HERE AND TAKES NONE.**
# `assignee`/`assignees`, `comments`/`comments_url`, `labels`/`labels_url` and
# `state`/`state_reason` are all prefix pairs — more than either of the two
# documents where it fired — and **all four short keys are always present**, so
# the exact match always wins. Exposure is **0 of 100**. That is the rule stated
# cleanly: partial matching can only fire where the exact key is ABSENT, so a
# document with more pairs can be safer than one with fewer.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

recs <- fromJSON("../source.json", simplifyVector = FALSE)
n <- length(recs)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  fromJSON parses and reports nothing: no duplicate-key warning, no\n")
cat("    big-integer notice, no NaN. It errors on malformed JSON and is silent\n")
cat("    on every silent damage. CANNOT.\n")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
present <- table(unlist(lapply(recs, names)))
cat("\nQ1 ", length(present), "distinct fields across", n, "issues\n")
cat("    the probe prints 179 distinct paths; jsonlite has no survey verb and no\n")
cat("    path enumeration, so this is base R over `names()`. PARTLY.\n")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
df <- fromJSON("../source.json")
nested <- names(df)[sapply(df, is.data.frame)]
cat("\nQ2  no depth verb. The FRAME hints:", length(nested), "columns are nested\n")
cat("    data.frames and `labels` is a list of frames, so the nesting is 4 —\n")
cat("    read off the classes by hand. PARTLY.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  fromJSON(simplifyVector = TRUE) returns a", class(df)[1],
    paste(dim(df), collapse = " x "), "UNASKED.\n")
cat("    It decided the array elements are rows and the union of keys are\n")
cat("    columns. On 13-package-lock the same call DECLINED, because those\n")
cat("    records lived in a keyed object. The guess needs a JSON array.\n")
cat("    It names no alternative and prices nothing. PARTLY.\n")
cat("Q7 ", n, "issues\n")

# ── Q4. THE DISCRIMINATOR, BOTH WAYS. ───────────────────────────────────────
nonnull <- table(unlist(lapply(recs, function(r) names(r)[!vapply(r, is.null, logical(1))])))
absent <- sort(names(present)[present < n])
nullish <- sort(Filter(function(k) present[[k]] == n &&
                         (is.na(nonnull[k]) || nonnull[[k]] < n), names(present)))
cat("\nQ4  FROM THE LIST, with names():\n")
cat("      sometimes ABSENT (", length(absent), "):", absent, "\n")
cat("      present but NULL (", length(nullish), "):", nullish, "\n")

pres_frame <- sapply(names(df), function(nm) {
  x <- df[[nm]]
  if (is.data.frame(x)) sum(!is.na(x[[1]])) else sum(!is.na(x))
})
cat("\nQ4  FROM THE FRAME, the same document:\n")
cat("     ", sum(pres_frame < n), "columns report missing values, and", length(absent),
    "+", length(nullish), "=", length(absent) + length(nullish), "\n")
cat("    THE FRAME CANNOT SPLIT IT. `simplifyVector` is documented as deciding\n")
cat("    whether arrays become vectors; it also decides whether this question\n")
cat("    is answerable, and nothing says so.\n")
alwaysnull <- sort(Filter(function(k) is.na(nonnull[k]), names(present)))
cat("    and", length(alwaysnull), "fields are NULL EVERYWHERE they appear:", alwaysnull, "\n")

# ── Q5. Does any field change type between records. ─────────────────────────
json_type <- function(v) {
  if (is.null(v)) "null"
  else if (is.list(v)) if (is.null(names(v))) "array" else "object"
  else if (is.character(v)) "string"
  else if (is.logical(v)) "boolean"
  else "number"
}
kinds <- lapply(setNames(names(present), names(present)), function(k)
  unique(vapply(Filter(function(r) !is.null(r[[k]]), recs),
                function(r) json_type(r[[k]]), character(1))))
varying <- Filter(function(v) length(v) > 1, kinds)
cat("\nQ5  fields whose JSON type varies, nulls excluded:",
    if (length(varying)) paste(names(varying), collapse = ", ") else "none", "\n")
cat("    NONE, which is the probe's answer. `class()` alone would be wrong here\n")
cat("    for the reason 13-package-lock recorded — an object and an array are\n")
cat("    both `list` — so the type function is hand-written again.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  no keyed collections — GitHub ships fixed field names. n/a\n")

# ── Q6b. THE `$` TRAP, four opportunities and no exposure. ──────────────────
nm <- names(present)
cat("\nQ6b `$` partial-matches, and this document has FOUR prefix pairs:\n")
for (s in nm) {
  longer <- nm[nm != s & startsWith(nm, s)]
  if (!length(longer)) next
  risky <- sum(vapply(recs, function(r)
    !(s %in% names(r)) && any(startsWith(names(r), s)), logical(1)))
  cat(sprintf("    %-10s -> %-14s exposure %d of %d\n", s, longer[1], risky, n))
}
cat("    ALL FOUR SHORT KEYS ARE ALWAYS PRESENT, so the exact match always wins.\n")
cat("    14-nyc-311 had ONE pair and 199 records exposed; 13-package-lock had\n")
cat("    three and 24. Partial matching can only fire where the exact key is\n")
cat("    ABSENT, so more pairs is not more danger.\n")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
tbl <- data.frame(number = df$number, state = df$state, user = df$user$login)
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cat("\nQ9  closed_by non-NA on", sum(!is.na(df$closed_by$login)), "of", n,
    "— the frame keeps every row\n")
cat("    and it CANNOT tell you those 52 are nulls rather than absences.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
labels <- do.call(rbind, Map(function(l, num)
  if (length(l)) cbind(number = num, l) else NULL, df$labels, df$number))
cat("\nQ10", nrow(labels), "label rows;", sum(lengths(df$labels) == 0),
    "issues have an empty list and contribute none\n")
print(head(labels[, c("number", "name")], 2))

# ── Q11. Find every path whose value matches something — by hand. ───────────
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nms <- names(x)
    for (i in seq_along(x))
      find_url(x[[i]], if (is.null(nms)) paste0(p, "[]") else paste0(p, ".", nms[i]))
  } else if (is.character(x)) {
    k <- sum(grepl("https?://", x))
    # inherits = FALSE, or an environment used as a dictionary reaches base::
    # for names like `url`. That cost entry 25 three fields.
    if (k > 0) assign(p, get0(p, hits, inherits = FALSE, ifnotfound = 0) + k, hits)
  }
}
find_url(recs, "$[]")
tot <- sum(vapply(ls(hits), function(k) get(k, hits, inherits = FALSE), numeric(1)))
cat("\nQ11", format(tot, big.mark = ","), "URL values over", length(ls(hits)), "paths\n")
cat("    Nine lines of hand-written recursion. jqr does it in one expression.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat <- flatten(df)
cat("\nQ12 flatten() gives", nrow(flat), "x", ncol(flat), "\n")
cat("    AND IT PREFIXES — `user.login`, `closed_by.login` — so nothing collides.\n")
cat("    polars' `unnest` RAISES on this document (26 names collide, 58 renames)\n")
cat("    and DuckDB's `struct.*` returns 19 duplicate names. jsonlite and pandas\n")
cat("    are the two that get this right unaided.\n")
cat("    Three list columns remain, and `issue_field_values` is an EMPTY LIST on\n")
cat("    all 100 issues — a field that exists and contains nothing.\n")
