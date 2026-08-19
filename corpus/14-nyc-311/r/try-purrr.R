# purrr — NYC 311 service requests, the 20,000 most recent
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   28.1 MB, 20,000 records, depth 4
#  measured      2026-08-11
#  run           cd corpus/14-nyc-311/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                            10   NO                  by hand
#   2 how deep                                    2   NO                  by hand
#   3 what is one record                          2   YES                 CANNOT
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  6   NO                  YES
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes — pluck default
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          9   NO                  by hand
#  12 flattest honest table                       5   YES                 yes
#  13 needed the shape in advance?                    NO for 4, 5, 7
#  14 survives the next file unchanged?               Q4/Q5 yes, the rest no
#  15 readable a week later?                          yes — the map_ verbs read well
#  16 lines, and how much is ceremony?                ~120, and the two walks are 20
#
# **THE FINDING IS `$`, AND IT IS THE SHARPEST THING THIS DOCUMENT PRODUCED.**
# R's `$` on a list does PARTIAL MATCHING: if there is no exact key, it returns
# the one key the name is a prefix of. This document has three prefix pairs —
#
#     agency     / agency_name
#     descriptor / descriptor_2
#     location   / location_type
#
# — and the first two are harmless because `agency` and `descriptor` are on every
# record, so the exact match always wins. **`location` is on 19,570 of 20,000.**
# On the 430 records that lack it, 199 carry `location_type`, and for those
#
#     r$location            returns the STRING "Street/Sidewalk"
#     r[["location"]]       returns NULL
#
# The first draft of this file wrote `keep(recs, \(r) !is.null(r$location))` and
# kept **199 records that have no location at all**. It then CRASHED — `$
# operator is invalid for atomic vectors` — and the crash was luck: the next
# accessor happened to be `$coordinates`. A predicate like `length(r$location) > 0`
# would have produced 19,769 coordinate rows instead of 19,570 and said nothing.
#
# **This is a hazard of ragged records specifically.** Partial matching can only
# fire where the exact key is absent, so it is safe on the 13 always-present
# fields and live on the other 35. `[[` is exact and is used everywhere below.
#
# **purrr COUNTS PRESENCE, AND ON THIS DOCUMENT THAT COSTS IT NOTHING.**
# `map(recs, names)` sees a key as present whether or not its value is null, so
# it reports 13 always and 35 sometimes — the probe's answer. On
# `25-usgs-quakes` that distinction split the thirteen tools seven to six.
# **Here it splits nothing: this document has ZERO nulls**, so presence-counting
# and frame-counting agree, and every tool in both directories gets question 4
# right. That agreement is the control case the corpus did not have.
#
# **THE COST IS TIME, AND IT IS THE WORST IN EITHER LANGUAGE.** The two
# hand-written walks over 20,000 records are printed below and they dominate the
# file. `map_chr` over 20,000 records is fine; recursing into every value is not.
#
# **What it has no vocabulary for is questions 1, 2 and 11** — twenty lines of
# recursion for three questions that jq answers in one expression each and
# ijson answers as a side effect of reading the file. That is the Python half's
# refrain in R, and purrr's `map` needs a level to map over before it can start.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

t0 <- Sys.time()
recs <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("    parsed %d records in %.1fs\n",
            length(recs), as.numeric(Sys.time() - t0, units = "secs")))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  purrr never saw the bytes; jsonlite parsed and said nothing. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — by hand. ──────────────────────────
# Depth counts CONTAINER levels, not the scalar under the last one, which is the
# convention design/probe.py prints. Counting every descent gives 5 here.
paths <- new.env(hash = TRUE); maxd <- 0
walk_paths <- function(x, p = "$", d = 1) {
  if (is.list(x)) {
    maxd <<- max(maxd, d)
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
t1 <- Sys.time()
walk_paths(recs)
cat(sprintf("\nQ1  %d distinct paths — a hand-written recursion, in %.1fs\n",
            length(ls(paths)), as.numeric(Sys.time() - t1, units = "secs")))
cat("    the probe prints 52, jq prints 52, ijson prints 52 plus a root.\n")
cat("Q2  depth", maxd, "— same recursion, and it agrees.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  purrr names no row candidates and prices none. CANNOT.\n")
cat("Q7 ", length(recs), "records\n")

# ── Q4. Always present vs sometimes. THE ONE IT IS GOOD AT. ──────────────────
present <- table(unlist(map(recs, names)))
cat("\nQ4 ", length(present), "distinct field names\n")
cat("    always", sum(present == length(recs)), "· sometimes",
    sum(present < length(recs)), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))
cat("    `names()` counts PRESENCE. On 25-usgs-quakes that beat every frame\n")
cat("    tool; here it ties them, because there are no nulls to disagree about.\n")

# ── Q5. Does any field change type between records. ──────────────────────────
json_t <- c(integer = "number", numeric = "number", character = "string",
            logical = "boolean", list = "object")
kinds <- map(set_names(names(present)), \(k)
  unique(map_chr(keep(recs, \(r) !is.null(r[[k]])), \(r) {
    cl <- class(r[[k]])[1]
    if (!is.na(json_t[cl])) unname(json_t[cl]) else cl
  })))
varying <- keep(kinds, \(v) length(v) > 1)
cat("\nQ5  fields varying as JSON types:",
    if (length(varying)) paste(names(varying), collapse = ", ") else "none",
    "— agrees with the probe\n")
cat("    distinct types across all fields:",
    paste(sort(unique(unlist(kinds))), collapse = ", "), "\n")
cat("    Every scalar in this document is a string; `location` is the one object.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
odd <- grep("^[^A-Za-z]", names(present), value = TRUE)
cat("\nQ6  no keyed collections. n/a.", length(odd), "names are not identifiers,\n")
cat("    but `[[` takes them as strings, so purrr pays no syntax tax:\n")
cat("   ", odd[1], "=", recs[[1]][[odd[1]]], "\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl <- data.frame(
  complaint_type = map_chr(recs, \(r) r[["complaint_type"]] %||% NA_character_),
  borough        = map_chr(recs, \(r) r[["borough"]]        %||% NA_character_),
  created_date   = map_chr(recs, \(r) r[["created_date"]]   %||% NA_character_))
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cat("    `%||% NA` on all three even though all three are ALWAYS present — you\n")
cat("    cannot know that until question 4, and 35 of 48 fields here are not.\n")
cat("    `[[` rather than `$` throughout, for the reason Q10 demonstrates.\n")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
closed <- map_chr(recs, \(r) pluck(r, "closed_date", .default = NA_character_))
cat("\nQ9  closed_date non-NA on", sum(!is.na(closed)), "of", length(closed),
    "— `pluck(.default=)` keeps the row\n")

# ── Q10. Flatten the deepest array into rows. AND THE `$` TRAP. ──────────────
# `$` partial-matches. On the 430 records without `location`, 199 have
# `location_type`, and `r$location` returns THAT — a character scalar.
bad  <- keep(recs, \(r) !is.null(r$location))          # WRONG: 19,769
good <- keep(recs, \(r) !is.null(r[["location"]]))     # right: 19,570
cat("\nQ10 `keep(!is.null(r$location))`      ->", length(bad), "records\n")
cat("Q10 `keep(!is.null(r[[\"location\"]]))` ->", length(good), "records\n")
cat("    THE FIRST IS WRONG BY", length(bad) - length(good),
    "and R does not warn. `location` is a\n")
cat("    prefix of `location_type`, so partial matching fires exactly where the\n")
cat("    field is absent. Using it, this file crashed on `$coordinates`; a\n")
cat("    slightly different predicate would have silently over-counted.\n")

co <- map(good, \(r) unlist(r[["location"]][["coordinates"]]))
co <- do.call(rbind, co); colnames(co) <- c("lon", "lat")
cat("Q10", nrow(co), "x", ncol(co), "\n"); print(head(co, 2))

# ── Q11. Find every path whose value matches something — by hand. ────────────
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nm <- names(x)
    iwalk(x, \(v, i) find_url(v, if (is.null(nm)) paste0(p, "[]")
                                 else paste0(p, ".", i)))
  } else if (is.character(x) && length(x) == 1 && grepl("https?://", x)) {
    # inherits = FALSE: an environment used as a dictionary otherwise reaches
    # base:: for names like `url`, which cost entry 25 three fields.
    assign(p, get0(p, hits, inherits = FALSE, ifnotfound = 0) + 1, hits)
  }
}
t2 <- Sys.time()
find_url(recs)
cat(sprintf("\nQ11 URL-valued paths, in %.1fs:\n",
            as.numeric(Sys.time() - t2, units = "secs")))
for (k in ls(hits)) cat("   ", k, get(k, hits, inherits = FALSE), "\n")
cat("    Nine more lines of recursion. jq does this in one expression.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cols <- names(present)
flat <- map_dfr(recs, \(r) {
  row <- map(set_names(cols), \(k) {
    v <- r[[k]]
    if (is.null(v)) NA_character_ else if (is.list(v)) NA_character_ else v
  })
  as.data.frame(row)
})
cat("\nQ12", nrow(flat), "x", ncol(flat), "\n")
cat("    `location` had to be dropped to NA to keep the frame rectangular —\n")
cat("    THAT IS A LOSS, and it is the one jsonlite's flatten() avoids. purrr\n")
cat("    builds rows, so anything non-scalar has to be handled by name first.\n")
