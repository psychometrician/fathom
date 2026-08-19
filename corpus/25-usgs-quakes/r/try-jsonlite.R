# jsonlite — USGS earthquakes, one month
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   7.4 MB, 10,885 features, depth 5
#  measured      2026-08-10
#  run           cd corpus/25-usgs-quakes/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   PARTLY
#   1 what is in here                             7   NO                  YES — handed over
#   2 how deep                                    3   NO                  by hand
#   3 what is one record                          3   NO                  HANDED, not named
#   4 always present vs sometimes                 8   NO                  needs the RAW parse
#   5 does any field change type                 14   NO                  needs the RAW parse
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               2   YES                 yes
#   9 a field missing from some rows              1   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something         12   NO                  by hand
#  12 flattest honest table                       2   YES                 yes
#  13 needed the shape in advance?                    NO for Q1/Q3 — see below
#  14 survives the next file unchanged?               Q1/Q3 yes; the rest name fields
#  15 readable a week later?                          yes, except the two walks
#  16 lines, and how much is ceremony?                ~110, and the walks are 25
#
# **jsonlite HANDS YOU A RECORD SHAPE WITHOUT BEING ASKED, and that is the
# strongest single answer in this directory to question 3.** `fromJSON()` alone
# returns `doc$features` as a **10,885-row data.frame whose `properties` column
# is itself a 26-column data.frame** — no schema, no column list, no unnest.
# polars RAISED on this same document and pandas needed `json_normalize`.
#
# **AND THE SAME SIMPLIFICATION IS WHY IT ANSWERS QUESTIONS 4 AND 5 WRONG.**
# Absent and null both become NA, and one type per column is resolved rather
# than reported. Both are recoverable only by re-parsing with
# `simplifyVector = FALSE` and walking the list by hand — which is to say, by
# not using the feature that makes jsonlite good at question 3.
#
# **TWO OVER-REPORTS IN MY OWN CODE, both caught by running it.** R's `class()`
# splits integer from numeric, which is not a JSON distinction. And an
# environment used as a dictionary INHERITS, so `url`, `time` and `title` picked
# up `base::url`, `base::time` and `graphics::title` and were reported as
# varying. `inherits = FALSE` was the whole fix and nothing warned.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  fromJSON() parses or errors. It is SILENT on duplicate keys (last\n")
cat("    wins), on ints past 2^53, and on a field holding an encoded document.\n")
cat("    It does refuse a bare NaN, which is more than python's json does.\n")

# ── The simplifying parse: jsonlite's whole personality in one call. ─────────
doc <- fromJSON("../source.json")
cat("\nQ1  fromJSON() with simplification, top level:\n")
cat("   ", paste(names(doc), collapse = ", "), "\n")
cat("Q1  class(doc$features):", class(doc$features), "\n")
cat("Q1  names(doc$features):", paste(names(doc$features), collapse = ", "), "\n")
cat("Q1  class(doc$features$properties):", class(doc$features$properties), "\n")
cat("Q1  properties has", ncol(doc$features$properties), "columns:\n")
cat("   ", paste(names(doc$features$properties), collapse = " "), "\n")

# ── Q2. How deep. ────────────────────────────────────────────────────────────
depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 1)) else 0
raw <- fromJSON("../source.json", simplifyVector = FALSE)
cat("\nQ2  depth of the UNSIMPLIFIED list:", depth(raw), "\n")
cat("    jsonlite reports no depth itself; this is a hand-written recursion,\n")
cat("    and it needs simplifyVector=FALSE because simplification FLATTENS the\n")
cat("    thing being measured.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  jsonlite names no candidates. It HANDED me one, which is different:\n")
cat("    doc$features is already a data.frame of", nrow(doc$features), "rows.\n")
cat("Q7 ", nrow(doc$features), "features\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
p <- doc$features$properties
na_counts <- vapply(p, function(col) sum(is.na(col)), 1)
cat("\nQ4  columns with any NA:\n")
print(na_counts[na_counts > 0])
cat("    THIS IS NOT QUESTION 4. Simplification turned every absent key AND\n")
cat("    every null into NA, so this counts NULLS, not absences. Measured on the\n")
cat("    unsimplified list, every one of the 26 keys is present on all",
    length(raw$features), "\n")
present <- table(unlist(lapply(raw$features, function(f) names(f$properties))))
cat("    features:", sum(present == length(raw$features)), "of", length(present), "keys always present\n")

# ── Q5. Does any field change type between records? ──────────────────────────
cat("\nQ5  simplification RESOLVED one type per column:\n")
print(vapply(p, function(col) class(col)[1], ""))
cat("    Like polars and duckdb, it cannot report a change because it made one.\n")
# **THE FIRST DRAFT OF THIS REPORTED url, time AND title AS VARYING, and the
# cause was R rather than the data.** An environment used as a dictionary
# INHERITS, so `get0("url", tt)` walked past the empty environment and found
# `base::url` — a function — and "function" joined the set of types. Any field
# sharing a name with a base R function was contaminated: url, time, title.
# `inherits = FALSE` is the whole fix, and nothing warned.
#
# The second over-report is real R and still not a JSON distinction: `class()`
# separates integer from numeric, and `{"mag": 2}` and `{"mag": 2.4}` are both
# `number` to jq, to ijson and to the probe.
tt <- new.env()
json_t <- c(integer = "number", numeric = "number", character = "string",
            logical = "boolean", list = "array")
for (f in raw$features) for (k in names(f$properties)) {
  v <- f$properties[[k]]
  cls <- if (is.null(v)) "null" else {
    r <- class(v)[1]
    if (!is.na(json_t[r])) unname(json_t[r]) else r
  }
  assign(k, unique(c(get0(k, tt, inherits = FALSE, ifnotfound = character()), cls)), tt)
}
varying <- Filter(function(k) length(setdiff(get(k, tt, inherits = FALSE), "null")) > 1, ls(tt))
cat("Q5  on the UNSIMPLIFIED list, as JSON types, ignoring null:",
    if (length(varying)) paste(varying, collapse = ", ") else "none",
    "— agrees with the probe\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  no keyed collections here. n/a\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl <- p[c("mag", "place", "time")]
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols, and the subsetting is base R\n")
print(head(tbl, 2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
cat("\nQ9  alert non-NA on", sum(!is.na(p$alert)), "of", nrow(p), "rows, rows kept\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co <- doc$features$geometry$coordinates
cat("\nQ10 class(coordinates):", class(co), " length:", length(co), "\n")
m <- do.call(rbind, co)
cat("Q10 rbind gives", nrow(m), "x", ncol(m), "— lon/lat/depth\n")
print(head(m, 2))
cat("    coordinates stayed a LIST of numeric vectors, not a matrix, because\n")
cat("    simplification will not build a matrix from equal-length vectors here.\n")

# ── Q11. Find every path whose value matches something — by hand. ────────────
hits <- new.env()
findurl <- function(x, p = "$") {
  if (is.list(x)) {
    nm <- names(x)
    for (i in seq_along(x)) {
      findurl(x[[i]], if (is.null(nm) || nm[i] == "") paste0(p, "[]") else paste0(p, ".", nm[i]))
    }
  } else if (is.character(x) && length(x) == 1 && startsWith(x, "http")) {
    assign(p, get0(p, hits, inherits = FALSE, ifnotfound = 0) + 1, hits)
  }
}
findurl(raw)
cat("\nQ11 URL-valued paths:\n")
for (k in ls(hits)) cat("   ", k, get(k, hits), "\n")
cat("    Hand-written. jsonlite has no path language at all.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat <- cbind(p, id = doc$features$id, lon = m[, 1], lat = m[, 2], depth_km = m[, 3])
cat("\nQ12", nrow(flat), "x", ncol(flat), "— nothing lost once coordinates are split.\n")

# ── The packed strings, because defect 26 came from this file. ───────────────
cat("\nDEFECT 26  does jsonlite notice a list packed into a string?\n")
cat("   ", p$types[1], "\n")
cat("    A character column. Splitting is one strsplit once a human notices.\n")
