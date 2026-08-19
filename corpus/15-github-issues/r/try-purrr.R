# purrr — 100 GitHub issues from one repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   686 KB, 100 issues, depth 4
#  measured      2026-08-11
#  run           cd corpus/15-github-issues/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                            11   NO                  by hand
#   2 how deep                                    2   NO                  by hand
#   3 what is one record                          3   YES                 CANNOT
#   4 always present vs sometimes                 9   NO                  YES — separates both
#   5 does any field change type                  7   NO                  YES — correctly none
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows               6   YES                 yes — and pluck's blind spot
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something         10   NO                  by hand
#  12 flattest honest table                       5   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 4, 5, 7
#  14 survives the next file unchanged?               Q4/Q5 yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~125, and the two walks are 21
#
# **`names()` AND `is.null()` ARE TWO DIFFERENT TESTS, SO purrr SEPARATES ABSENT
# FROM NULL — AND THIS IS THE FIRST DOCUMENT WHERE THAT PAYS.** 5 fields are
# sometimes ABSENT and 8 are always present but sometimes NULL. `14-nyc-311` had
# zero nulls, so `names()` bought nothing there; here it buys the whole question.
# pandas, polars, DuckDB and simplified jsonlite each report **13** and cannot
# split it.
#
# **`pluck(.default =)` HAS A BLIND SPOT THAT IS EXACTLY pydash's.** The default
# fires when the path cannot be reached, so a key **present holding null** comes
# back as the default too — the same value an absent key gives. `FINDINGS.md`
# records that for pydash on `25-usgs-quakes`; purrr's `pluck` does it in R, and
# on this document it affects **8 fields and 709 values**.
#
# **THE `$` TRAP HAS FOUR OPPORTUNITIES AND TAKES NONE.** `assignee`/`assignees`,
# `comments`/`comments_url`, `labels`/`labels_url`, `state`/`state_reason` — more
# prefix pairs than either document where it fired — and all four short keys are
# always present, so exposure is **0 of 100**. Partial matching needs the exact
# key to be ABSENT, which is why more pairs is not more danger.
#
# **And questions 1, 2 and 11 are twenty-one lines of recursion**, for the fourth
# file running.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

recs <- fromJSON("../source.json", simplifyVector = FALSE)
n <- length(recs)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  purrr never saw the bytes; jsonlite parsed and said nothing. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — by hand. ─────────────────────────
paths <- new.env(hash = TRUE); maxd <- 0
walk_paths <- function(x, p = "$", d = 1) {
  if (is.list(x)) {
    maxd <<- max(maxd, d)
    nms <- names(x)
    if (is.null(nms)) {
      # An EMPTY array has no element path — that is why the probe counts 179
      # and a naive walk counts 180. `issue_field_values` is [] on all 100.
      if (length(x)) assign(paste0(p, "[]"), TRUE, paths)
      walk(x, \(v) walk_paths(v, paste0(p, "[]"), d + 1))
    } else {
      iwalk(x, \(v, k) { assign(paste0(p, ".", k), TRUE, paths)
                         walk_paths(v, paste0(p, ".", k), d + 1) })
    }
  }
}
walk_paths(recs)
cat("\nQ1 ", length(ls(paths)), "distinct paths — THE PROBE PRINTS 179.\n")
cat("    The `if (length(x))` guard is the whole difference: an array that is\n")
cat("    empty on every record has no element path. Without it this counts 180.\n")
cat("Q2  depth", maxd, "— same recursion, and it agrees with the probe.\n")

# ── Q3/Q7. What is one record, and how many. ────────────────────────────────
cat("\nQ3  purrr names no row candidates and prices none. The probe names three\n")
cat("    and prices them, including `100 rows x 144 cols 53% empty`. CANNOT.\n")
cat("Q7 ", n, "issues\n")

# ── Q4. THE DISCRIMINATOR — purrr separates both kinds. ─────────────────────
present <- table(unlist(map(recs, names)))
nonnull <- table(unlist(map(recs, \(r) names(r)[!map_lgl(r, is.null)])))
absent <- sort(names(present)[present < n])
nullish <- sort(keep(names(present), \(k) present[[k]] == n &&
                       (is.na(nonnull[k]) || nonnull[[k]] < n)))
cat("\nQ4 ", length(present), "distinct fields\n")
cat("      sometimes ABSENT (", length(absent), "):", absent, "\n")
cat("      present but NULL (", length(nullish), "):", nullish, "\n")
cat("    `names()` counts PRESENCE and `is.null()` counts VALUE — two tests, two\n")
cat("    facts. The frame tools have one hole and report 13 without splitting it.\n")
cat("    On 14-nyc-311 this distinction bought nothing: that file has no nulls.\n")

# ── Q5. Does any field change type between records. ─────────────────────────
json_type <- function(v) {
  if (is.null(v)) "null"
  else if (is.list(v)) if (is.null(names(v))) "array" else "object"
  else if (is.character(v)) "string"
  else if (is.logical(v)) "boolean"
  else "number"
}
kinds <- map(set_names(names(present)), \(k)
  unique(map_chr(keep(recs, \(r) !is.null(r[[k]])), \(r) json_type(r[[k]]))))
varying <- keep(kinds, \(v) length(v) > 1)
cat("\nQ5  fields whose JSON type varies, nulls excluded:",
    if (length(varying)) paste(names(varying), collapse = ", ") else "none", "\n")
cat("    NONE — the probe's answer. Two things had to be right: excluding null,\n")
cat("    and not trusting `class()`, which calls an object and an array both\n")
cat("    `list`. 13-package-lock recorded the second; this file needs both.\n")

# ── Q6. Are any object keys actually data? AND THE `$` TRAP. ────────────────
cat("\nQ6  no keyed collections — GitHub ships fixed field names. n/a\n")
nm <- names(present)
cat("\nQ6b `$` partial-matches, and this document has FOUR prefix pairs:\n")
for (s in nm) {
  longer <- nm[nm != s & startsWith(nm, s)]
  if (!length(longer)) next
  risky <- sum(map_lgl(recs, \(r) !(s %in% names(r)) && any(startsWith(names(r), s))))
  cat(sprintf("    %-10s -> %-14s exposure %d of %d\n", s, longer[1], risky, n))
}
cat("    NONE FIRE. All four short keys are always present. 14-nyc-311 had one\n")
cat("    pair and 199 exposed; 13-package-lock had three and 24. `[[` is used\n")
cat("    throughout below regardless.\n")

# ── Q8. Three named fields into a table. ────────────────────────────────────
tbl <- map_dfr(recs, \(r) data.frame(
  number = r[["number"]],
  state  = r[["state"]],
  user   = r[["user"]][["login"]]))
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))

# ── Q9. A field missing from some records — AND pluck's BLIND SPOT. ────────
r_null <- detect(recs, \(r) is.null(r[["closed_by"]]))
r_has  <- detect(recs, \(r) !is.null(r[["closed_by"]]))
# Must be an issue that genuinely LACKS pull_request — 16 of the 100 do. The
# first draft reused r_null, which has one, and printed a real URL under a
# heading claiming it was a default.
r_gone <- detect(recs, \(r) !("pull_request" %in% names(r)))
cat("\nQ9  `pluck(r, \"closed_by\", \"login\", .default = \"DEFAULT\")`:\n")
cat("      on an issue where closed_by is an OBJECT ->",
    pluck(r_has, "closed_by", "login", .default = "DEFAULT"), "\n")
cat("      on an issue where closed_by is NULL      ->",
    pluck(r_null, "closed_by", "login", .default = "DEFAULT"), "\n")
cat("      on a field that is genuinely ABSENT      ->",
    pluck(r_gone, "pull_request", "url", .default = "DEFAULT"), "\n")
cat("    THE LAST TWO ARE THE SAME ANSWER. `pluck`'s default fires whenever the\n")
cat("    path cannot be reached, so a key present holding null is indistinguish-\n")
cat("    able from one that is absent. FINDINGS.md records exactly this for\n")
cat("    pydash on 25-usgs-quakes; purrr does it in R. Question 4 above is only\n")
cat("    right because it used `names()` instead.\n")
cb <- map_chr(recs, \(r) pluck(r, "closed_by", "login", .default = NA_character_))
cat("    closed_by.login non-NA on", sum(!is.na(cb)), "of", n, "— all rows kept\n")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────────
labels <- map_dfr(recs, \(r) if (length(r[["labels"]]))
  map_dfr(r[["labels"]], \(l) data.frame(number = r[["number"]], name = l[["name"]]))
  else NULL)
cat("\nQ10", nrow(labels), "label rows;",
    sum(map_int(recs, \(r) length(r[["labels"]])) == 0),
    "issues have an empty list and contribute none\n")

# ── Q11. Find every path whose value matches something — by hand. ──────────
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
find_url(recs, "$[]")
tot <- sum(map_dbl(ls(hits), \(k) get(k, hits, inherits = FALSE)))
cat("\nQ11", format(tot, big.mark = ","), "URL values over", length(ls(hits)), "paths\n")
cat("    Ten more lines of recursion, and no fold was needed — this document has\n")
cat("    no keys-as-data, so 77 paths is a real answer. jqr does it in one line.\n")

# ── Q12. The flattest honest table, and what was lost. ──────────────────────
scalar <- keep(names(present), \(k)
  all(map_lgl(keep(recs, \(r) !is.null(r[[k]])), \(r) !is.list(r[[k]]))))
flat <- map_dfr(recs, \(r) as.data.frame(map(set_names(scalar), \(k) {
  v <- r[[k]]; if (is.null(v)) NA else v
})))
cat("\nQ12", nrow(flat), "x", ncol(flat), "— the", length(scalar), "scalar fields\n")
cat("    PARTLY. The eight nested objects are dropped rather than prefixed, so\n")
cat("    this loses `user.login` and the rest. jsonlite's flatten() keeps them\n")
cat("    and prefixes; purrr builds rows, so anything nested is handled by name.\n")
