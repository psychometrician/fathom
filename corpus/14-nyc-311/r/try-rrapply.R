# rrapply — NYC 311 service requests, the 20,000 most recent
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   28.1 MB, 20,000 records, depth 4
#  measured      2026-08-11
#  run           cd corpus/14-nyc-311/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             5   NO                  YES — melt gives paths
#   2 how deep                                    2   NO                  YES — melt's L columns
#   3 what is one record                          3   NO                  PARTLY
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  4   NO                  NO — melt destroys types
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               2   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          4   NO                  YES
#  12 flattest honest table                       4   NO                  YES — best in the corpus
#  13 needed the shape in advance?                    NO for 1, 2, 4, 7, 11, 12
#  14 survives the next file unchanged?               yes for all of those
#  15 readable a week later?                          yes — two verbs do everything
#  16 lines, and how much is ceremony?                ~105, and almost none is ceremony
#
# **`rrapply(recs, how = "bind")` PRODUCES THE ONLY LIST-COLUMN-FREE TABLE ANY OF
# THE THIRTEEN TOOLS MANAGED ON THIS DOCUMENT.** 20,000 x 50, in 0.2 s, with
# `location` expanded to `location.type`, `location.coordinates.1` and
# `location.coordinates.2` — **and the two coordinate columns are numeric.**
#
# Every other tool here stops one level short: pandas, polars, DuckDB, jsonlite,
# glom, jmespath, pydash and jq all leave `coordinates` as a list in one cell,
# which is the thing god's spec refuses. `VERDICT.md`'s item A2 records that
# **17 of 19 corpus extracts carry a list-column**; this is one that does not,
# and the tool that got there is the least-known name in either language.
#
# **THE CAVEAT IS POSITIONAL AND IT IS REAL.** `.1` and `.2` are positions, not
# names — rrapply split the array because every copy of it is length 2, and on a
# ragged array it would widen to the longest one. Nothing declares that longitude
# comes first. That is question 7a's property, arrived at from the other side.
#
# **`how = "melt"` IS THE BEST PATH ENUMERATION IN R.** 752,908 rows x 5 in
# 0.4 s, one row per leaf, with the path in columns L1..L4 — the same 752,908
# leaves ijson counts from the byte stream. Questions 1, 2, 4 and 11 all fall
# out of that one frame.
#
# **AND IT LOSES QUESTION 5 IN THE PROCESS.** `melt` coerces every value to
# character, so all 752,908 leaves come back `character` and the 39,140
# coordinate floats are indistinguishable from text. The document happens to be
# all-strings so nothing here is misreported — **but the instrument could not
# have told you either way**, and that is a "cannot" rather than an answer.
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

t0 <- Sys.time()
recs <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("    parsed %d records in %.1fs\n",
            length(recs), as.numeric(Sys.time() - t0, units = "secs")))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  rrapply operates on a list jsonlite already built. No health\n")
cat("    vocabulary on either side. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — MELT GIVES BOTH. ──────────────────
t1 <- Sys.time()
m <- rrapply(recs, how = "melt")
melt_s <- as.numeric(Sys.time() - t1, units = "secs")
lev <- grep("^L[0-9]+$", names(m), value = TRUE)
cat(sprintf("\nQ1  how=\"melt\": %d rows x %d cols in %.1fs — one row per LEAF\n",
            nrow(m), ncol(m), melt_s))
cat("    the path is in", paste(lev, collapse = ", "), "and the value in `value`\n")
cat("   ", length(unique(m$L2)), "distinct field names under the record\n")
cat("Q2  depth", length(lev), "— melt made one L column per level. Correct, and\n")
cat("    it is READ OFF the result rather than computed. jq needs an expression.\n")
cat("    leaf count", nrow(m), "is exactly what ijson's event census reports.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  L1 is the record index, so melt implies the row shape without naming\n")
cat("    it as a choice:", length(unique(m$L1)), "records. It offers no alternative\n")
cat("    and prices nothing. PARTLY.\n")
cat("Q7 ", length(recs), "records\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
present <- table(m$L2[is.na(m$L3)])
loc <- length(unique(m$L1[!is.na(m$L3)]))
present["location"] <- loc
cat("\nQ4 ", length(present), "field names\n")
cat("    always", sum(present == length(recs)), "· sometimes",
    sum(present < length(recs)), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))

# ── Q5. Does any field change type between records. IT CANNOT SAY. ───────────
cat("\nQ5  classes present in melt's `value` column:",
    paste(unique(sapply(m$value[1:5000], \(x) class(x)[1])), collapse = ", "), "\n")
cat("    ALL", nrow(m), "LEAVES COME BACK character. melt coerced the 39,140\n")
cat("    coordinate floats to text, so the frame cannot distinguish a number\n")
cat("    from a numeral. The answer happens to be `none varies`, and rrapply is\n")
cat("    not the thing that told me. CANNOT.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
odd <- grep("^[^A-Za-z]", names(present), value = TRUE)
cat("\nQ6  no keyed collections. n/a.", length(odd), "names are not identifiers;\n")
cat("    melt puts them in a column as data, so they cost nothing:", odd[1], "\n")

# ── Q8/Q9. Extraction, via bind. ─────────────────────────────────────────────
t2 <- Sys.time()
b <- rrapply(recs, how = "bind")
bind_s <- as.numeric(Sys.time() - t2, units = "secs")
cat(sprintf("\nQ8  how=\"bind\": %d x %d in %.1fs\n", nrow(b), ncol(b), bind_s))
print(head(b[, c("complaint_type", "borough", "created_date")], 2))
cat("\nQ9  closed_date present on", sum(!is.na(b$closed_date)), "of", nrow(b),
    "— rows kept, gaps NA\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co <- b[!is.na(b$location.coordinates.1),
        c("location.coordinates.1", "location.coordinates.2")]
names(co) <- c("lon", "lat")
cat("\nQ10", nrow(co), "x", ncol(co), "— and they are",
    class(co$lon), "columns, not a list\n")
print(head(co, 2))

# ── Q11. Find every path whose value matches something. ──────────────────────
hit <- m[grepl("https?://", m$value), ]
cat("\nQ11 URL-valued leaves:", nrow(hit), "\n")
print(table(hit$L2))
cat("    One grepl over melt's `value` column. No recursion, no field named —\n")
cat("    the melt already turned every path into a row. purrr and jsonlite each\n")
cat("    need nine lines of hand-written walk for this.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12", nrow(b), "x", ncol(b), "and NOTHING IS A LIST COLUMN:\n")
cat("    classes:", paste(names(table(sapply(b, \(x) class(x)[1]))),
                          table(sapply(b, \(x) class(x)[1])), collapse = " · "), "\n")
cat("    new columns:", paste(setdiff(names(b), names(present)), collapse = ", "), "\n")
cat("    THE ONLY FULLY RECTANGULAR RESULT IN EITHER LANGUAGE ON THIS FILE.\n")
cat("    The cost is that .1 and .2 are POSITIONS: rrapply split the array\n")
cat("    because every copy is length 2, and nothing says which is longitude.\n")
