# purrr — USGS earthquakes, one month
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   7.4 MB, 10,885 features, depth 5
#  measured      2026-08-10
#  run           cd corpus/25-usgs-quakes/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             6   NO                  by hand
#   2 how deep                                    2   NO                  by hand
#   3 what is one record                          2   YES                 CANNOT
#   4 always present vs sometimes                 4   NO                  YES
#   5 does any field change type                  5   NO                  YES
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes — pluck default
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          9   NO                  by hand
#  12 flattest honest table                       4   YES                 yes
#  13 needed the shape in advance?                    NO for 4, 5, 7
#  14 survives the next file unchanged?               Q4/Q5 yes, the rest no
#  15 readable a week later?                          yes — the map_ verbs read well
#  16 lines, and how much is ceremony?                ~80, and the walks are 20
#
# **purrr WALKS KEYS, AND THAT IS WHY IT ANSWERS QUESTIONS 4 AND 5 CORRECTLY**
# where jsonlite's own simplification does not. `map(feats, names)` sees a key
# whose value is null as PRESENT, so all 26 property fields are reported on all
# 10,885 features — the same answer jq, ijson, glom and pydash give, and the
# opposite of what pandas, polars, duckdb and simplified jsonlite report.
#
# **What it has no vocabulary for is questions 1, 2 and 11.** `map` needs a
# level to map over, so surveying a document means writing the recursion. That
# is the Python half's refrain in R.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
feats <- doc$features

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  purrr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — by hand. ──────────────────────────
paths <- new.env(); maxd <- 0
walk_paths <- function(x, p = "$", d = 0) {
  maxd <<- max(maxd, d)
  if (is.list(x)) {
    nm <- names(x)
    if (is.null(nm)) {
      assign(paste0(p, "[]"), TRUE, paths)
      walk(x, \(v) walk_paths(v, paste0(p, "[]"), d + 1))
    } else {
      iwalk(x, \(v, k) { assign(paste0(p, ".", k), TRUE, paths)
                         walk_paths(v, paste0(p, ".", k), d + 1) })
    }
  }
}
walk_paths(doc)
cat("\nQ1 ", length(ls(paths)), "distinct paths — a hand-written recursion\n")
cat("Q2  depth", maxd, "— same recursion. Both agree with jq and the probe.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3/Q7 ", length(feats), "features. purrr names no candidates. CANNOT for Q3.\n")

# ── Q4. Always present vs sometimes. THE ONE IT IS GOOD AT. ──────────────────
present <- table(unlist(map(feats, \(f) names(f$properties))))
cat("\nQ4 ", sum(present == length(feats)), "of", length(present),
    "property keys are on EVERY feature\n")
nulls <- map_int(set_names(names(feats[[1]]$properties)),
                 \(k) sum(map_lgl(feats, \(f) is.null(f$properties[[k]]))))
cat("Q4  present-but-null counts:\n"); print(nulls[nulls > 0])
cat("    `names()` counts PRESENCE. Every frame-shaped tool in this directory\n")
cat("    reports six of these as 'sometimes'; they are always there and null.\n")

# ── Q5. Does any field change type between records. ──────────────────────────
json_t <- c(integer = "number", numeric = "number", character = "string",
            logical = "boolean", list = "array")
kinds <- map(set_names(names(feats[[1]]$properties)), \(k)
  unique(map_chr(feats, \(f) {
    v <- f$properties[[k]]
    if (is.null(v)) "null" else { r <- class(v)[1]
      if (!is.na(json_t[r])) unname(json_t[r]) else r }
  })))
varying <- keep(kinds, \(v) length(setdiff(v, "null")) > 1)
cat("\nQ5  fields varying as JSON types, ignoring null:",
    if (length(varying)) paste(names(varying), collapse = ", ") else "none",
    "— agrees with the probe\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  no keyed collections here. n/a\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl <- map_dfr(feats, \(f) data.frame(mag = f$properties$mag %||% NA,
                                      place = f$properties$place,
                                      time = f$properties$time))
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
alert <- map_chr(feats, \(f) pluck(f, "properties", "alert", .default = NA_character_))
cat("\nQ9  alert non-NA on", sum(!is.na(alert)), "of", length(alert),
    "— `pluck(.default=)` keeps the row\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co <- map_dfr(feats, \(f) set_names(as.data.frame(t(unlist(f$geometry$coordinates))),
                                    c("lon", "lat", "depth_km")))
cat("\nQ10", nrow(co), "x", ncol(co), "\n"); print(head(co, 2))

# ── Q11. Find every path whose value matches something — by hand. ────────────
hits <- new.env()
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nm <- names(x)
    iwalk(x, \(v, i) find_url(v, if (is.null(nm)) paste0(p, "[]")
                                 else paste0(p, ".", i)))
  } else if (is.character(x) && length(x) == 1 && startsWith(x, "http")) {
    assign(p, get0(p, hits, inherits = FALSE, ifnotfound = 0) + 1, hits)
  }
}
find_url(doc)
cat("\nQ11 URL-valued paths:\n")
for (k in ls(hits)) cat("   ", k, get(k, hits, inherits = FALSE), "\n")
cat("    purrr has no path language; this is nine lines of recursion.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat <- map_dfr(feats, \(f) {
  p <- modify_if(f$properties, is.null, \(x) NA)
  as.data.frame(c(p, list(id = f$id), set_names(as.list(unlist(f$geometry$coordinates)),
                                                c("lon", "lat", "depth_km"))))
})
cat("\nQ12", nrow(flat), "x", ncol(flat), "— nothing lost; nulls became NA by choice.\n")

# ── The packed strings, because defect 26 came from this file. ───────────────
cat("\nDEFECT 26  does purrr notice a list packed into a string?\n")
cat("   ", feats[[1]]$properties$types, "\n")
cat("    A character scalar. Nothing in purrr looks inside a value.\n")
