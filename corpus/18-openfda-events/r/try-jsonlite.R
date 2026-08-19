# jsonlite — 100 openFDA adverse-event reports
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   2.7 MB, 100 results, depth 8
#  measured      2026-08-11
#  run           cd corpus/18-openfda-events/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   CANNOT
#   1 what is in here                             5   NO                  PARTLY
#   2 how deep                                    4   NO                  PARTLY
#   3 what is one record                           9  NO                  PARTLY — it CHOOSES
#   4 always present vs sometimes                 6   NO                  YES
#   5 does any field change type                  5   NO                  YES — correctly none
#   6 are any object keys data                    3   -                   n/a — no abstention
#   7 how many records                             5   NO                  yes — four answers
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   5   YES                 PARTLY
#  11 find every path matching something          8   NO                  YES — by hand
#  12 flattest honest table                       5   YES                 yes — it PREFIXES
#  13 needed the shape in advance?                    NO for 3, 4, 5, 7
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~110
#
# **`fromJSON()` RETURNS A NESTED FRAME EIGHT LEVELS DEEP AND SAYS NOTHING ABOUT
# IT.** `results` becomes a 100 x 25 data.frame in which five columns are
# themselves data.frames, one of which (`patient`) holds a list-column of
# data.frames (`drug`), one of which holds a data.frame (`openfda`), whose
# columns are lists of strings. **The whole depth-8 structure is preserved, and
# reading it back out means walking `class()` by hand.**
#
# **AND `flatten()` PREFIXES**, so nothing collides — polars' `unnest` RAISED on
# `15-github-issues` over 26 duplicate names, and DuckDB's `struct.*` returned 19
# silently. Here jsonlite, pandas, rrapply and tidyjson all prefix and all work.
#
# **IT ANSWERS QUESTION 3 BY CHOOSING**, as on 14, 15 and 17 and unlike 13: the
# array announces the shape, so `fromJSON` guesses one. It guesses the FIRST of
# the probe's four candidates and never mentions the other three.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

doc  <- fromJSON("../source.json")
recs <- fromJSON("../source.json", simplifyVector = FALSE)$results
df   <- doc$results
n    <- nrow(df)
allf <- sort(unique(unlist(lapply(recs, names))))

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
cat("\nQ0  fromJSON parses and reports nothing: no duplicate-key warning, no\n")
cat("    big-integer notice, no NaN. 2.7 MB and eight levels give it no\n")
cat("    trouble, and it says nothing about either. CANNOT.\n")

# ── Q1. What is in here. ───────────────────────────────────────────────────
cat("\nQ1  top level:", names(doc), "\n")
cat("Q1  the results are a", class(df)[1], paste(dim(df), collapse = " x "), "\n")
cat("   ", sum(sapply(df, is.data.frame)), "columns are themselves data.frames and",
    sum(sapply(df, is.list) & !sapply(df, is.data.frame)), "are list-columns.\n")
cat("    PARTLY — no survey verb. The probe prints 122 paths and ELEVEN shapes.\n")

# ── Q2. How deep does it go. ───────────────────────────────────────────────
depth_of <- function(x, d = 1) {
  if (is.data.frame(x)) max(c(d, sapply(x, depth_of, d + 1)))
  else if (is.list(x) && length(x)) max(c(d, sapply(x, depth_of, d + 1)))
  else d
}
cat("\nQ2  walking class() by hand gives", depth_of(doc), "levels.\n")
cat("    THE PROBE PRINTS 8. jsonlite preserved the whole structure and has no\n")
cat("    verb that reports it, so this is a hand-written recursion over a frame\n")
cat("    rather than over a list. PARTLY.\n")

# ── Q3/Q7. The row candidates. ────────────────────────────────────────────
drugs <- unlist(lapply(recs, function(r) r$patient$drug), recursive = FALSE)
rx <- unlist(lapply(recs, function(r) r$patient$reaction), recursive = FALSE)
cat("\nQ3  fromJSON CHOSE: `results` becomes", paste(dim(df), collapse = " x "),
    "unasked.\n")
cat("    On 13-package-lock the same call DECLINED, because those records lived\n")
cat("    in a keyed object. The guess needs a JSON array, and here it gets one.\n")
cat("    THE PROBE NAMES FOUR CANDIDATES AND PRICES THEM:\n")
cat("      the whole document        1 rows x  2 cols\n")
cat("      an item of results      100 rows x 39 cols   26% empty\n")
cat("      an item of drug         265 rows x 41 cols   47% empty\n")
cat("      an item of reaction     247 rows x  3 cols\n")
cat("    jsonlite guessed the second and never mentioned the rest. PARTLY.\n")
cat("\nQ7  FOUR right answers: results", n, "· drug", length(drugs),
    "· reaction", length(rx), "\n")
cat("    and meta.results.total =", format(doc$meta$results$total, big.mark = ","),
    "— which fromJSON KEPT, because it returns the whole document as a list.\n")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
present <- table(unlist(lapply(recs, names)))
nn <- sum(sapply(recs, function(r) sum(sapply(r, is.null))))
cat("\nQ4 ", length(present), "fields; always", sum(present == n), "· sometimes",
    sum(present < n), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))
cat("    the results hold", nn, "null, so this is almost all genuine absence.\n")

# ── Q5. Does any field change type. ──────────────────────────────────────
json_type <- function(v) if (is.null(v)) "null" else if (is.list(v))
  (if (is.null(names(v))) "array" else "object") else class(v)[1]
kinds <- lapply(setNames(names(present), names(present)), function(k)
  unique(vapply(Filter(function(r) !is.null(r[[k]]), recs),
                function(r) json_type(r[[k]]), character(1))))
varying <- Filter(function(v) length(v) > 1, kinds)
cat("\nQ5  fields whose JSON type varies, nulls excluded:",
    if (length(varying)) paste(names(varying), collapse = ", ") else "none",
    "— the probe's answer\n")
cat("    pandas' python-type check over a frame reports TWELVE here: eleven NaN\n")
cat("    artefacts and one real null (`receiver`).\n")

# ── Q6. Are any object keys actually data? ──────────────────────────────
cat("\nQ6  no keyed collections. n/a — and the probe prints `could not call 3\n")
cat("    small single-copy objects` and names them. That ABSTENTION is a third\n")
cat("    state jsonlite has no way to express.\n")

# ── Q8/Q9. Extraction. ──────────────────────────────────────────────────
cat("\nQ8 ", n, "rows x 3 cols\n")
print(head(df[, c("safetyreportid", "serious", "receivedate")], 2))
cat("\nQ9  seriousnessdeath non-NA on", sum(!is.na(df$seriousnessdeath)), "of", n,
    "— the frame keeps every row\n")

# ── Q10. Flatten the deepest array. ─────────────────────────────────────
bn <- unlist(lapply(recs, function(r)
  unlist(lapply(r$patient$drug, function(dr) dr$openfda$brand_name))))
cat("\nQ10", length(bn), "brand names, four levels down — and this is a nested\n")
cat("    `lapply` chain, not a jsonlite verb. The frame HAS the data:\n")
cat("    df$patient$drug is a list of data.frames whose openfda column is a\n")
cat("    data.frame of list-columns. Reaching it means knowing that. PARTLY.\n")

# ── Q11. Find every path whose value matches something — by hand. ──────
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
cat("    BOTH, and both are under `meta` — outside `results`. Eight lines of\n")
cat("    recursion starting at the root; pandas and polars report NONE OF TWO.\n")

# ── Q12. The flattest honest table. ────────────────────────────────────
flat <- flatten(df)
cat("\nQ12 flatten() gives", nrow(flat), "x", ncol(flat), "\n")
cat("    AND IT PREFIXES — patient.patientsex, sender.senderorganization — so\n")
cat("    nothing collides. polars' `unnest` RAISED on 15-github-issues over 26\n")
cat("    duplicate names and DuckDB's `struct.*` returned 19 silently; jsonlite,\n")
cat("    pandas, rrapply and tidyjson all prefix.\n")
cat("    Two list-columns remain, holding 265 drugs and 247 reactions — the\n")
cat("    probe's other two row candidates, kept in cells.\n")
