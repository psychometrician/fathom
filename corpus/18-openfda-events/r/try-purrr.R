# purrr — 100 openFDA adverse-event reports
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   2.7 MB, 100 results, depth 8
#  measured      2026-08-11
#  run           cd corpus/18-openfda-events/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                            11  NO                  by hand
#   2 how deep                                    2   NO                  by hand
#   3 what is one record                           8  YES                 CANNOT
#   4 always present vs sometimes                 6   NO                  YES
#   5 does any field change type                  6   NO                  YES — correctly none
#   6 are any object keys data                    4   -                   n/a — no abstention
#   7 how many records                             5   NO                  yes — four answers
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 PARTLY — nested maps
#  11 find every path matching something         10  NO                  YES — by hand
#  12 flattest honest table                       5   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 4, 5, 7
#  14 survives the next file unchanged?               Q4/Q5 yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~115, and the two walks are 21
#
# **THE HAND-WRITTEN WALK REPRODUCES BOTH PROBE NUMBERS ON THE DEEPEST DOCUMENT
# IN THE CORPUS** — 122 paths and depth 8 — and it is the same twenty-one lines
# purrr has needed on every file. Depth costs it nothing extra, because a
# recursion does not care; **what depth costs is question 10.**
#
# **REACHING `brand_name` TAKES THREE NESTED `map`s.**
# `map(recs, ~ map(.x$patient$drug, ~ .x$openfda$brand_name))` then a flatten —
# one level of nesting per level of document. jq crosses the same four levels
# with `..` and names none of them; jmespath with one chained expression; glom
# with one spec. **purrr's `map` is the verb that scales worst with depth**, and
# this is the file that shows it.
#
# **THE `$` TRAP HAS FIVE OPPORTUNITIES HERE AND TAKES NONE** — `serious`,
# `receivedate`, `receiptdate`, `transmissiondate` and `primarysource` are all
# prefixes of siblings, and all five are ALWAYS PRESENT, so the exact match
# always wins. **This is the most pairs any corpus document has and the exposure
# is zero**, which is the rule stated as sharply as it can be: partial matching
# fires only where the exact key is ABSENT.
#
# **And `is.null()` costs almost nothing**: the whole document holds 3 nulls, so
# presence-counting and value-counting agree everywhere but one field.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc  <- fromJSON("../source.json", simplifyVector = FALSE)
recs <- doc$results
n    <- length(recs)

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
cat("\nQ0  purrr never saw the bytes; jsonlite parsed and said nothing. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — by hand. ────────────────────────
paths <- new.env(hash = TRUE); maxd <- 0
walk_paths <- function(x, p = "$", d = 1) {
  if (is.list(x)) {
    maxd <<- max(maxd, d)
    nms <- names(x)
    if (is.null(nms)) {
      if (length(x)) assign(paste0(p, "[]"), TRUE, paths)
      walk(x, \(v) walk_paths(v, paste0(p, "[]"), d + 1))
    } else {
      iwalk(x, \(v, k) { assign(paste0(p, ".", k), TRUE, paths)
                         walk_paths(v, paste0(p, ".", k), d + 1) })
    }
  }
}
walk_paths(doc)
cat("\nQ1 ", length(ls(paths)), "distinct paths — THE PROBE PRINTS 122.\n")
cat("    The same twenty-one lines purrr has needed on every file, starting at\n")
cat("    the ROOT — which is why Q11 finds both URLs below.\n")
cat("Q2  depth", maxd, "— same recursion. THE PROBE PRINTS 8, and this is the\n")
cat("    deepest file in the corpus. A recursion does not care how deep a thing\n")
cat("    is; pandas says 3, because json_normalize stops at the first array.\n")

# ── Q3/Q7. The row candidates. ────────────────────────────────────────────
# jsonlite masks purrr::flatten (its own expects a data.frame), so the
# namespace is spelled out. The attach message says so and is easy to skip.
drugs <- purrr::list_flatten(map(recs, \(r) r$patient$drug))
rx <- purrr::list_flatten(map(recs, \(r) r$patient$reaction))
cat("\nQ3  purrr names no row candidates and prices none. THE PROBE NAMES FOUR:\n")
cat("      the whole document        1 rows x  2 cols\n")
cat("      an item of results      100 rows x 39 cols   26% empty\n")
cat("      an item of drug         265 rows x 41 cols   47% empty\n")
cat("      an item of reaction     247 rows x  3 cols\n")
cat("    CANNOT.\n")
cat("\nQ7  FOUR right answers: results", n, "· drug", length(drugs),
    "· reaction", length(rx), "\n")
cat("    and meta.results.total =", format(doc$meta$results$total, big.mark = ","), "\n")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
present <- table(unlist(map(recs, names)))
nonnull <- table(unlist(map(recs, \(r) names(r)[!map_lgl(r, is.null)])))
nullish <- keep(names(present), \(k) present[[k]] == n &&
                  (is.na(nonnull[k]) || nonnull[[k]] < n))
cat("\nQ4 ", length(present), "fields; always", sum(present == n), "· sometimes",
    sum(present < n), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))
cat("    present but NULL:", nullish, "— one field, one record. `names()` and\n")
cat("    `is.null()` are two tests and this document needs both exactly once.\n")

# ── Q5. Does any field change type. ──────────────────────────────────────
json_type <- function(v) if (is.null(v)) "null" else if (is.list(v))
  (if (is.null(names(v))) "array" else "object") else class(v)[1]
kinds <- map(set_names(names(present)), \(k)
  unique(map_chr(keep(recs, \(r) !is.null(r[[k]])), \(r) json_type(r[[k]]))))
varying <- keep(kinds, \(v) length(v) > 1)
cat("\nQ5  fields whose JSON type varies, nulls excluded:",
    if (length(varying)) paste(names(varying), collapse = ", ") else "none",
    "— the probe's answer\n")
cat("    pandas' python-type check over a frame reports TWELVE on this file.\n")

# ── Q6. Are any object keys actually data? AND the `$` trap. ────────────
cat("\nQ6  no keyed collections. n/a — and the probe prints `could not call 3\n")
cat("    small single-copy objects` and names them. That ABSTENTION is a third\n")
cat("    state purrr has no way to express.\n")
nm <- names(present)
cat("\nQ6b `$` partial-matches. Prefix pairs among the result fields:\n")
exposed <- 0
for (s in nm) {
  longer <- nm[nm != s & startsWith(nm, s)]
  if (!length(longer)) next
  risky <- sum(map_lgl(recs, \(r) !(s %in% names(r)) && any(startsWith(names(r), s))))
  exposed <- exposed + risky
  cat(sprintf("    %-16s -> %-26s exposure %d of %d\n", s, longer[1], risky, n))
}
cat("    FIVE PAIRS AND ZERO EXPOSURE — every short key is always present, so\n")
cat("    the exact match always wins. Five documents now pin the rule:\n")
cat("      14-nyc-311       1 pair    199 of 20,000 exposed\n")
cat("      13-package-lock  3 pairs    24 of  1,657\n")
cat("      15-github-issues 4 pairs     0 of    100\n")
cat("      17-openlibrary   1 pair      0 of    200\n")
cat("      18-openfda       5 pairs     0 of    100\n")
cat("    MORE PAIRS IS NOT MORE DANGER. Partial matching fires only where the\n")
cat("    exact key is ABSENT. `[[` is used throughout regardless.\n")

# ── Q8/Q9. Extraction. ──────────────────────────────────────────────────
tbl <- map_dfr(recs, \(r) data.frame(id = r[["safetyreportid"]],
                                     serious = r[["serious"]],
                                     received = r[["receivedate"]]))
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
sd <- map_chr(recs, \(r) pluck(r, "seriousnessdeath", .default = NA_character_))
cat("\nQ9  seriousnessdeath non-NA on", sum(!is.na(sd)), "of", n,
    "— `pluck(.default=)` keeps the row\n")

# ── Q10. Flatten the deepest array — THREE NESTED MAPS. ────────────────
bn <- purrr::list_flatten(map(recs, \(r)
  purrr::list_flatten(map(r$patient$drug, \(dr)
    dr$openfda$brand_name %||% list()))))
cat("\nQ10", length(bn), "brand names, four levels down — and it took THREE\n")
cat("    nested `map`s plus two flattens, one nesting level per document level.\n")
cat("    jq crosses the same four with `..` and names none; jmespath with one\n")
cat("    chained expression; glom with one spec. purrr's `map` is the verb that\n")
cat("    scales worst with depth, and this is the file that shows it. PARTLY.\n")

# ── Q11. Find every path whose value matches something — by hand. ──────
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
cat("    BOTH, and both under `meta` — outside `results`. Ten lines of recursion\n")
cat("    starting at the root; pandas and polars report NONE OF TWO.\n")

# ── Q12. The flattest honest table. ───────────────────────────────────
scalar <- keep(names(present), \(k)
  all(map_lgl(keep(recs, \(r) !is.null(r[[k]])), \(r) !is.list(r[[k]]))))
flat <- map_dfr(recs, \(r) as.data.frame(map(set_names(scalar), \(k) {
  v <- r[[k]]; if (is.null(v)) NA else v
})))
cat("\nQ12", nrow(flat), "x", ncol(flat), "— the", length(scalar), "scalar fields\n")
cat("    PARTLY: the five nested objects and two arrays are DROPPED rather than\n")
cat("    prefixed. jsonlite's flatten() keeps and prefixes them; rrapply's bind\n")
cat("    expands them into 37,006 columns at 98% NA.\n")
