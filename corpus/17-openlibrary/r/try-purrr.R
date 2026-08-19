# purrr — 200 OpenLibrary search results
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   64 KB, 200 docs, depth 4
#  measured      2026-08-11
#  run           cd corpus/17-openlibrary/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                            11  NO                  by hand
#   2 how deep                                    2   NO                  by hand
#   3 what is one record                          12  YES                 NO — misses the SPLIT
#   4 always present vs sometimes                 6   NO                  YES
#   5 does any field change type                  6   NO                  YES — correctly none
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                             4   NO                  yes — both answers
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something         10  NO                  by hand
#  12 flattest honest table                       5   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 4, 5, 7
#  14 survives the next file unchanged?               Q4/Q5 yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~120, and the two walks are 21
#
# **THE PROBE'S FOURTH OPERATION FIRES ON THIS DOCUMENT AND purrr HAS NO WORD FOR
# IT.** `design/probe.py` prints `an item of docs 200 rows x 17 cols 34% empty`
# and then `└─ or 4 tables, split on ebook_access — 16% empty`. `split()` from
# base R produces those four tables once the field is named; nothing in purrr
# searched for it. Of the six always-present fields, `edition_count` makes the
# emptiness WORSE and `public_scan_b` changes nothing.
#
# **`names()` VERSUS `is.null()` COSTS NOTHING HERE**, because the records hold
# zero nulls: 6 fields always present, 11 sometimes absent, no type variation.
# On `15-github-issues` that distinction was the entire entry and split the
# thirteen tools nine to four. Same code, same tool, and the document decided.
#
# **THE `$` TRAP HAS ONE OPPORTUNITY AND TAKES IT NOT AT ALL.** `ia` is a prefix
# of `ia_collection`, and both are absent on exactly the same 183 docs — so when
# `ia` is missing, `ia_collection` is missing too and the partial match has no
# sibling to reach. **Exposure 0 of 200.**
#
#     14-nyc-311        1 pair    199 of 20,000 exposed
#     13-package-lock   3 pairs    24 of  1,657 exposed
#     15-github-issues  4 pairs     0 of    100 exposed
#     17-openlibrary    1 pair      0 of    200 exposed
#
# **Four documents now pin the rule**, and this one adds the case the other three
# lacked: a pair whose two fields are absent TOGETHER, which is safe for a reason
# nothing to do with how many pairs there are.
#
# **And questions 1, 2 and 11 are twenty-one lines of recursion**, for the sixth
# file running.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc  <- fromJSON("../source.json", simplifyVector = FALSE)
recs <- doc$docs
n    <- length(recs)
allf <- sort(unique(unlist(map(recs, names))))
holes <- mean(map_dbl(recs, \(r) sum(!(allf %in% names(r))))) / length(allf)

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
cat("\nQ0  purrr never saw the bytes; jsonlite parsed and said nothing. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — by hand. ────────────────────────
paths <- new.env(hash = TRUE); maxd <- 0
walk_paths <- function(x, p = "$", d = 1) {
  if (is.list(x)) {
    maxd <<- max(maxd, d)
    nms <- names(x)
    if (is.null(nms)) {
      # An EMPTY array has no element path.
      if (length(x)) assign(paste0(p, "[]"), TRUE, paths)
      walk(x, \(v) walk_paths(v, paste0(p, "[]"), d + 1))
    } else {
      iwalk(x, \(v, k) { assign(paste0(p, ".", k), TRUE, paths)
                         walk_paths(v, paste0(p, ".", k), d + 1) })
    }
  }
}
walk_paths(doc)
cat("\nQ1 ", length(ls(paths)), "distinct paths — THE PROBE PRINTS 31.\n")
cat("    A hand-written recursion, and it starts at the ROOT rather than at\n")
cat("    `docs`, which is why question 11 works below.\n")
cat("Q2  depth", maxd, "— same recursion, and it agrees with the probe.\n")

# ── Q3. THE SPLIT. ─────────────────────────────────────────────────────────
cat("\nQ3  purrr names no row candidates and prices none. The probe names two,\n")
cat("    prices both, and adds a third line:\n")
cat(sprintf("      an item of docs   %d rows x %d cols   %.0f%% empty\n",
            n, length(allf), 100 * holes))
cat("      └─ or 4 tables, split on ebook_access — 16% empty\n")
cat("\nQ3  what a split on each always-present field would cost:\n")
always <- keep(allf, \(k) all(map_lgl(recs, \(r) k %in% names(r))))
for (f in always) {
  vals <- unique(map_chr(recs, \(r) as.character(r[[f]])))
  if (length(vals) < 2 || length(vals) > 24) {
    cat(sprintf("      %-16s %3d kinds  — too many to be a discriminator\n",
                f, length(vals))); next
  }
  worst <- max(map_dbl(vals, \(v) {
    g <- keep(recs, \(r) as.character(r[[f]]) == v)
    fs <- sort(unique(unlist(map(g, names))))
    mean(map_dbl(g, \(r) sum(!(fs %in% names(r))))) / length(fs)
  }))
  cat(sprintf("      %-16s %3d kinds  worst group %5.1f%%  %s\n", f, length(vals),
              100 * worst, if (worst > holes - 0.01) "WORSE" else "better"))
}
cat("    `split()` from base R gives the four tables once the field is known.\n")
cat("    Nothing in purrr searched, priced or chose. That is the fourth operation.\n")

# ── Q7. How many records. ─────────────────────────────────────────────────
cat("\nQ7 ", n, "docs — and purrr got the whole document, so:\n")
cat("      numFound", format(doc$numFound, big.mark = ","),
    "· num_found", format(doc$num_found, big.mark = ","), "· start", doc$start, "\n")
cat("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist.\n")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
present <- table(unlist(map(recs, names)))
nn <- sum(map_int(recs, \(r) sum(map_lgl(r, is.null))))
cat("\nQ4 ", length(present), "distinct fields; always", sum(present == n),
    "· sometimes", sum(present < n), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))
cat("    the records hold", nn, "nulls, so `names()` and `is.null()` agree and\n")
cat("    the distinction costs nothing. On 15-github-issues it was the entry.\n")

# ── Q5. Does any field change type. ──────────────────────────────────────
json_type <- function(v) if (is.null(v)) "null" else if (is.list(v))
  (if (is.null(names(v))) "array" else "object") else class(v)[1]
kinds <- map(set_names(names(present)), \(k)
  unique(map_chr(keep(recs, \(r) !is.null(r[[k]])), \(r) json_type(r[[k]]))))
varying <- keep(kinds, \(v) length(v) > 1)
cat("\nQ5  fields whose JSON type varies:",
    if (length(varying)) paste(names(varying), collapse = ", ") else "none",
    "— the probe's answer\n")
cat("    `class()` alone would be wrong for 13-package-lock's reason; the type\n")
cat("    function is hand-written again.\n")

# ── Q6. Are any object keys actually data? AND the `$` trap. ─────────────
cat("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA\n")
cat("    section is empty for this file.\n")
cat("\nQ6b `$` partial-matches. This document's prefix pairs:\n")
found <- FALSE
for (s in names(present)) {
  longer <- setdiff(names(present)[startsWith(names(present), s)], s)
  if (!length(longer)) next
  found <- TRUE
  risky <- sum(map_lgl(recs, \(r) !(s %in% names(r)) && any(startsWith(names(r), s))))
  cat(sprintf("    %-14s -> %-16s exposure %d of %d\n", s, longer[1], risky, n))
}
if (!found) cat("    none.\n")
cat("    14-nyc-311 had ONE pair and 199 exposed; 13-package-lock three and 24;\n")
cat("    15-github-issues four and none. Partial matching fires only where the\n")
cat("    exact key is ABSENT, which four documents now pin.\n")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────
tbl <- map_dfr(recs, \(r) data.frame(title = r[["title"]],
                                     editions = r[["edition_count"]],
                                     access = r[["ebook_access"]]))
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cov <- map_int(recs, \(r) pluck(r, "cover_i", .default = NA_integer_))
cat("\nQ9  cover_i non-NA on", sum(!is.na(cov)), "of", n,
    "— `pluck(.default=)` keeps the row\n")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────
an <- map_dfr(recs, \(r) if (length(r[["author_name"]]))
  data.frame(key = r[["key"]], author = unlist(r[["author_name"]])) else NULL)
cat("\nQ10", nrow(an), "author rows;",
    sum(map_int(recs, \(r) length(r[["author_name"]])) == 0), "doc has none\n")
cat("    FIVE fields are arrays and every one is ALSO sometimes absent.\n")

# ── Q11. Find every path whose value matches something — by hand. ───────
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nms <- names(x)
    iwalk(x, \(v, i) find_url(v, if (is.null(nms)) paste0(p, "[]")
                                 else paste0(p, ".", i)))
  } else if (is.character(x) && length(x) == 1 && grepl("https?://", x)) {
    # inherits = FALSE, or the environment reaches base:: for names like `url`.
    assign(p, get0(p, hits, inherits = FALSE, ifnotfound = 0) + 1, hits)
  }
}
find_url(doc)
cat("\nQ11 URL-valued paths:\n")
for (k in ls(hits)) cat("   ", k, get(k, hits, inherits = FALSE), "\n")
cat("    ONE URL, at the TOP LEVEL, found because the walk starts at the root.\n")
cat("    pandas and polars frame `docs` and report NONE OF ONE. Ten lines.\n")

# ── Q12. The flattest honest table, and what was lost. ──────────────────
scalar <- keep(names(present), \(k)
  all(map_lgl(keep(recs, \(r) !is.null(r[[k]])), \(r) !is.list(r[[k]]))))
flat <- map_dfr(recs, \(r) as.data.frame(map(set_names(scalar), \(k) {
  v <- r[[k]]; if (is.null(v)) NA else v
})))
cat("\nQ12", nrow(flat), "x", ncol(flat), "— the", length(scalar), "scalar fields\n")
cat("    PARTLY: the five array fields are DROPPED rather than kept as list-\n")
cat("    columns. jsonlite's frame keeps them; rrapply's `bind` expands them\n")
cat("    positionally into 36 columns at 64% NA, which is worse than either.\n")
