# jsonlite — Natural Earth admin-0 countries, as GeoJSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   3.9 MB, 241 features, depth 8, 75 paths
#  measured      2026-08-09
#  run           cd corpus/03-natural-earth/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              12   NO                  PARTLY
#   1 what is in here                             6   NO                  NO
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          3   NO                  YES
#   4 always present vs sometimes                 4   NO                  NO
#   5 does any field change type                 12   YES                 PARTLY
#   6 are any keys actually data                  -   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               1   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   9   YES, both depths    yes
#  11 find every path matching something         14   YES                 CANNOT
#  12 flattest honest table                       2   NO                  PARTLY
#  13 needed the shape in advance?                    no for 1-3, YES for 5 and 10
#  16 lines, and how much is ceremony?                see the conclusion
#
#  Q0  PARTLY: validate() answers well-formedness and nothing else. Every
#      silent damage is silent, and duplicate keys resolve to the FIRST.
#  Q3  YES, and it is the only YES in R: fromJSON() returns `features` as a
#      241-row data frame without being asked.
#  Q4  NO: simplification maps absent and null both to NA, so the two axes
#      NOTES.md grades separately cannot be told apart from here.
#  Q5  PARTLY: it PRESERVES the 3-deep/4-deep split rather than flattening it,
#      but reports it only as a surviving list-column.
#  Q11 CANNOT as a verb — no path language. The recursion is base R, and it is
#      what turned up the -99 sentinels.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. jsonlite has **no attempt file anywhere in the corpus** — it has
# been imported as a parser inside every other R attempt and never scored as a
# tool. `README.md` lists it among the five R tools in the comparison, so every
# "no existing tool does this" claim has been made without ever asking it.
#
# And this is the document that should hurt it most. `VERDICT.md` records polars
# **silently rewriting** this file — all 122 Polygons promoted from 3-deep to
# 4-deep coordinates so one type would cover both. jsonlite's whole design is
# simplification into rectangles. The question this file asks is whether R's
# default JSON reader commits the same silent rewrite.

suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.json"
cat(sprintf("  file is %.1f MB\n", file.size(path) / 1024^2))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\n0. is this sound:\n")
raw <- readChar(path, file.size(path), useBytes = TRUE)
cat(sprintf("   validate()  %s\n", validate(raw)))
cat("   validate() answers well-formedness ONLY. It is silent on every one of\n")
cat("   the four silent damages question 0 names: duplicate keys, ints past\n")
cat("   2^53, NaN/Infinity, an encoded document in a string value.\n")

# Duplicate keys, tested directly rather than assumed — and the answer is not
# the one this project has been assuming.
dup <- tryCatch(fromJSON('{"a":1,"a":2}'), error = function(e) e)
cat(sprintf("   {\"a\":1,\"a\":2} parses to a=%s, no warning — %s WINS\n",
            if (inherits(dup, "error")) "ERROR" else dup$a,
            if (!inherits(dup, "error") && dup$a == 1) "the FIRST" else "the last"))
cat("   QUESTIONS.md says \"duplicate keys where the LAST one quietly wins\".\n")
cat("   That is Python's and JavaScript's rule. jsonlite keeps the first, so two\n")
cat("   languages reading one damaged document disagree about its contents and\n")
cat("   neither warns. Recorded here because it makes question 0 sharper.\n")

# The bigint check, and the FIRST version of this check was fooled by the very
# thing it was testing: `big$n == 9007199254740993` compares two doubles, both
# already rounded, so it reported "exact". Comparing the DIGITS is the only
# honest test.
big <- fromJSON('{"n":9007199254740993}')
cat(sprintf("   9007199254740993 comes back as %s (%s) — %s\n",
            sprintf("%.0f", big$n), class(big$n),
            if (identical(sprintf("%.0f", big$n), "9007199254740993")) "exact"
            else "SILENTLY CHANGED, past 2^53, no warning"))
for (lit in c("NaN", "Infinity")) {
  r <- tryCatch(fromJSON(sprintf('{"x":%s}', lit)), error = function(e) "refuses")
  cat(sprintf("   {\"x\":%s} on read: %s\n", lit,
              if (identical(r, "refuses")) "refuses to parse" else paste("accepts,", r$x)))
}

t0 <- Sys.time()
simp <- fromJSON(path)                       # the default: simplifyVector = TRUE
t_simp <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
t0 <- Sys.time()
doc <- fromJSON(path, simplifyVector = FALSE)
t_list <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\n   parsed simplified in %.1f s, as a plain list in %.1f s\n", t_simp, t_list))

# ── Q1. What is in here? ─────────────────────────────────────────────────────
cat("\n1. what is in here — jsonlite's describer is str() on the result:\n")
for (lv in 1:4) {
  n <- length(capture.output(str(simp, max.level = lv)))
  cat(sprintf("   str(simplified, max.level=%d)  %5d lines\n", lv, n))
}
n_full <- length(capture.output(str(simp)))
cat(sprintf("   str(simplified) whole          %5d lines\n", n_full))
n_list <- length(capture.output(str(doc, max.level = 4)))
cat(sprintf("   str(unsimplified, max.level=4) %5d lines  <- same document, list form\n", n_list))
cat("   Simplification is doing real work here: the same question costs an\n")
cat("   order of magnitude more on the list form, and BOTH are O(data).\n")

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
cat("\n2. how deep does it go:\n")
depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("   %d levels, via a hand-written recursion — jsonlite has no depth verb\n",
            depth(doc)))

# ── Q3 / Q7. What is one record, and how many? ───────────────────────────────
cat("\n3/7. what is one record, and how many:\n")
cat(sprintf("   fromJSON() returned a %s with names: %s\n",
            class(simp)[1], paste(names(simp), collapse = ", ")))
cat(sprintf("   $features is a %s: %d rows x %d cols\n",
            class(simp$features)[1], nrow(simp$features), ncol(simp$features)))
cat("   THIS IS THE ONE THING JSONLITE DOES THAT NO OTHER R TOOL HERE DOES:\n")
cat("   it answered question 3 without being asked. `features` became a data\n")
cat("   frame because the array held objects of one shape, and that IS the row.\n")
cat(sprintf("   Its columns are: %s\n", paste(names(simp$features), collapse = ", ")))
cat(sprintf("   $features$properties is a nested data frame: %d x %d\n",
            nrow(simp$features$properties), ncol(simp$features$properties)))

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
props <- simp$features$properties
nas <- vapply(props, function(col) sum(is.na(col)), 0L)
cat(sprintf("   %d property columns; %d have no NA at all\n",
            ncol(props), sum(nas == 0)))
cat("   Ragged-by-ABSENCE is unanswerable from here, and that is the cost of\n")
cat("   simplification: a key missing from a record and a key present-but-null\n")
cat("   both arrive as NA in a column. NOTES.md grades this file 0 of 68 ragged\n")
cat("   by absence and 6 fields null — jsonlite cannot tell those two apart.\n")
cat(sprintf("   columns that are entirely NA: %d\n", sum(nas == nrow(props))))
cat("   Worst few by NA count:\n")
for (nm in names(sort(nas, decreasing = TRUE))[1:5])
  cat(sprintf("     %-16s %4d of %d NA\n", nm, nas[[nm]], nrow(props)))

# ── Q5. Does any field change type? THE QUESTION THIS FILE EXISTS FOR. ───────
cat("\n5. does any field change type — and this is the file's whole point:\n")
geom <- simp$features$geometry
cat(sprintf("   $features$geometry is a %s with columns %s\n",
            class(geom)[1], paste(names(geom), collapse = ", ")))
cat(sprintf("   geometry$type values: %s\n",
            paste(sprintf("%s x%d", names(table(geom$type)), table(geom$type)),
                  collapse = ", ")))

# The measurement: nesting depth of `coordinates`, per feature, from the
# UNSIMPLIFIED parse, which is the only one that still has the truth in it.
cdepth <- vapply(doc$features, function(f) depth(f$geometry$coordinates), 0)
cat("   coordinates nesting depth, from the UNSIMPLIFIED parse:\n")
for (d in sort(unique(cdepth)))
  cat(sprintf("     %d deep  x%d\n", d, sum(cdepth == d)))

# And now the same measurement through the simplified parse, which is what a
# person actually gets from a bare fromJSON().
sdepth <- vapply(geom$coordinates, function(cc) {
  f <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, f, 0))
                   else if (is.array(x)) length(dim(x)) else 0
  f(cc)
}, 0)
cat("   the same field AFTER simplification:\n")
for (d in sort(unique(sdepth)))
  cat(sprintf("     %d deep  x%d\n", d, sum(sdepth == d)))

cat("   VERDICT: ")
if (identical(sort(unique(cdepth)), sort(unique(sdepth)))) {
  cat("jsonlite PRESERVED the depth split. It did NOT do what polars did.\n")
} else {
  cat("the two disagree — simplification changed the data.\n")
}

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\n6. are any object keys actually data:\n")
cat("   CANNOT, and there is nothing to find here — NOTES.md grades this file\n")
cat("   keys-as-data 0. Recorded as unattempted-because-absent rather than as a\n")
cat("   pass: a tool that says nothing on a document with no keyed sites has not\n")
cat("   been tested on the question.\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
cat("\n8. three named fields, one row per feature:\n")
tbl <- data.frame(name = props$name, iso = props$iso_a3, pop = props$pop_est)
cat(sprintf("   data.frame(props$name, props$iso_a3, props$pop_est) -> %d x %d\n",
            nrow(tbl), ncol(tbl)))
print(head(tbl, 3))
cat("   One line, no map, no default. This is the best question-8 answer in the\n")
cat("   corpus so far, and it is because question 3 was already answered.\n")

# ── Q9. A field missing from some records. ───────────────────────────────────
cat("\n9. a field missing from some records, keeping those rows:\n")
nm <- names(sort(nas, decreasing = TRUE))[1]
cat(sprintf("   %s is NA on %d of %d rows and the rows are still there:\n",
            nm, nas[[nm]], nrow(props)))
cat(sprintf("   nrow(props) == %d, no filtering happened\n", nrow(props)))
cat("   Free, because a data frame column cannot drop rows. The catch is Q4's:\n")
cat("   you cannot tell from here whether the key was absent or null.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
cat("\n10. flatten the deepest array into rows — the coordinates:\n")
t0 <- Sys.time()
one <- doc$features[[1]]
cat(sprintf("   feature 1 is %s, %s\n", one$properties$NAME, one$geometry$type))
pts <- do.call(rbind, lapply(seq_along(doc$features), function(i) {
  f <- doc$features[[i]]
  cc <- f$geometry$coordinates
  # Polygon is 3 deep, MultiPolygon 4 — so the unwrap differs by kind. THIS IS
  # THE COST OF THE POLYMORPHISM, written out.
  rings <- if (f$geometry$type == "Polygon") cc else unlist(cc, recursive = FALSE)
  do.call(rbind, lapply(rings, function(r)
    data.frame(feature = i, x = vapply(r, `[[`, 0, 1), y = vapply(r, `[[`, 0, 2))))
}))
cat(sprintf("   %d coordinate pairs from %d features, in %.1f s\n",
            nrow(pts), length(doc$features),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("   THE `if` IS THE FINDING. One branch per geometry kind, hand-written,\n")
cat("   because the same field name holds two different nesting depths. Nothing\n")
cat("   in jsonlite's output told me to write it — NOTES.md did.\n")

# ── Q11. Find every path whose value matches something. ──────────────────────
cat("\n11. find every path whose value matches something:\n")
cat("   The corpus's usual target is a URL or an email. THIS DOCUMENT HAS\n")
cat("   NEITHER — measured, 0 occurrences of `http`. So the target here is the\n")
cat("   one pattern it does carry, and finding it is a result in its own right.\n")
cat("   CANNOT, as a verb: jsonlite has no path language. Base R recursion:\n")
paths <- local({
  out <- character(0)
  rec <- function(x, p) {
    if (is.list(x)) {
      nms <- names(x)
      for (i in seq_along(x))
        rec(x[[i]], if (is.null(nms) || !nzchar(nms[i]))
                      sprintf("%s[]", p) else sprintf("%s.%s", p, nms[i]))
    } else if (length(x) == 1 && !is.na(x) && as.character(x) == "-99") {
      out <<- c(out, p)
    }
  }
  rec(doc, "$")
  out
})
cat(sprintf("   %d cells hold the literal -99, across %d distinct paths\n",
            length(paths), length(unique(paths))))

# ── AND THIS IS THE FILE'S SECOND FINDING, WHICH NOBODY WENT LOOKING FOR. ────
cat("\n11a. -99 IS A MISSING-VALUE SENTINEL, AND IT IS EVERYWHERE:\n")
n99 <- vapply(props, function(c) sum(!is.na(c) & as.character(c) == "-99"), 0L)
n99 <- sort(n99[n99 > 0], decreasing = TRUE)
for (nm in names(n99))
  cat(sprintf("     %-14s %4d of %d  (%s)\n", nm, n99[[nm]], nrow(props),
              class(props[[nm]])[1]))
cat(sprintf("   %d fields, %d cells. `woe_id`, `adm0_a3_un` and `adm0_a3_wb` are\n",
            length(n99), sum(n99)))
cat("   -99 on ALL 241 records: columns that are entirely missing, reported by\n")
cat("   every tool in this corpus as fully populated.\n")
cat("   NOTES.md grades this file `ragged by absence: none, 0 of 68` and\n")
cat("   `ragged by null: 6 fields`. Both are true and both are beside the point.\n")
cat("   THE PROBE'S DETECTOR CANNOT SEE THIS. VERDICT.md defect 18 catches a\n")
cat("   field that is a NUMBER on some records and one of very FEW STRINGS on\n")
cat("   others. Here every column is uniformly typed: pop_est is a number\n")
cat("   including its -99s, iso_a3 is text including its \"-99\"s. Nothing\n")
cat("   changes type, so nothing fires.\n")

# ── Q12. The flattest honest table. ──────────────────────────────────────────
cat("\n12. the flattest honest table, and what was lost:\n")
flat <- jsonlite::flatten(simp$features)
cat(sprintf("   jsonlite::flatten(features) -> %d x %d\n", nrow(flat), ncol(flat)))
cat(sprintf("   column classes: %s\n",
            paste(sprintf("%s x%d", names(table(vapply(flat, function(c) class(c)[1], ""))),
                          table(vapply(flat, function(c) class(c)[1], ""))),
                  collapse = ", ")))
listcols <- names(flat)[vapply(flat, is.list, TRUE)]
cat(sprintf("   list-columns remaining: %s\n",
            if (length(listcols)) paste(listcols, collapse = ", ") else "none"))
cat("   WHAT WAS LOST: nothing yet, and that is the problem — the geometry is\n")
cat("   still a list-column, so this is the flattest table jsonlite will make\n")
cat("   and it is not flat. god's spec refuses a list-column as a value.\n")

cat("
CONCLUSION — the first jsonlite attempt in the corpus, and it changes a claim.

  IT DID NOT SILENTLY REWRITE THE FILE. This document is in the corpus because
  its polymorphism is in nesting depth rather than type, and `VERDICT.md` records
  polars promoting all 122 Polygons to 4-deep so one schema would fit. jsonlite,
  asked the same thing, keeps 3-deep and 4-deep apart: simplification stops at
  the ragged boundary and leaves a list-column. **The R default reader is safer
  than the Python one on the corpus's own counterexample.**

  It also answers question 3 unprompted, which nothing else in R does. `features`
  arrives as a 241-row data frame because the array held one shape, so questions
  7, 8 and 9 are nearly free and question 8 needs no `map` and no default.

  WHERE IT FAILS is the exploring half, and it fails it the standard way:
  `str()` is the only describer and it is O(data). It cannot tell absent from
  null, which costs it question 4 outright on a file graded `0 of 68` ragged by
  absence with 6 null fields. It has no path language, so question 11 is a
  hand-written recursion.

  ON QUESTION 0 IT IS SILENT, AND IT IS SILENT DIFFERENTLY FROM PYTHON.
  Duplicate keys resolve to **the FIRST** with no warning, where `QUESTIONS.md`
  and every Python parser in this corpus take the last. Two languages reading one
  damaged document disagree about its contents and neither says so. Integers past
  2^53 are silently rounded to a double; `NaN` and `Infinity` are refused
  outright, which is the one place it is stricter than Python.

  AND THE DOCUMENT TURNED OUT TO BE MISSING A FIFTH OF ITSELF. Chasing question
  11 — because this file has no URL to search for — turned up **-99 as a missing
  sentinel in 18 fields and 1,767 cells**, with three columns at -99 on all 241
  records. jsonlite does not report it, but nor does anything else in this
  repository: the probe's sentinel detector looks for a type change, and these
  columns are uniformly typed. See NOTES.md.

  THE SHARPEST LIMIT IS THAT IT DOES NOT SAY WHAT IT DID. The list-column is the
  only evidence that `coordinates` is two shapes, and reading a list-column as a
  polymorphism report requires already knowing to look. jsonlite got the right
  answer and did not tell anybody.
")
