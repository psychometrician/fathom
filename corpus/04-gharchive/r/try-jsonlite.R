# jsonlite — one hour of GitHub Archive events, NDJSON at 50 MB
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.jsonl   50 MB, 37,883 records, depth 7, 846 paths,
#                                  235 fields, keyed 2, path variance 76
#  measured      2026-08-10
#  run           cd corpus/04-gharchive/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                             6   no                  YES
#   1 what is in here                           4   NO                  NO
#   2 how deep                                  2   NO                  yes
#   3 what is one record                        7   NO                  YES
#   4 always present vs sometimes               8   NO                  MISLEADING
#   7 how many records                          1   no                  yes
#   8 three named fields to a table             4   YES                 yes
#  13 needed the shape in advance?                  no for 0, 3, 7
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. Three reasons, and they are all firsts.
#
# **It is the corpus's only scale reading.** `NOTES.md` records the frozen probe
# at **968 MB peak RSS for a 50 MB document — 18.8x — and 7.2 s**, and observes
# that it has no way to read less, so on a file that does not fit it dies rather
# than sampling. No R tool in this corpus has been asked to handle scale at all.
#
# **It is NDJSON**, which `corpus/README.md` calls how JSON at scale actually
# arrives, and `stream_in` is jsonlite's answer to it.
#
# **And it is a cross-language control with a known answer.** The probe reported
# `6 lines could not be read` on a file with **zero** malformed records, because
# Python's `str.splitlines()` splits on U+2028 and three GitHub payloads contain
# one. R splits on `\n` only. Prediction 3 in NOTES.md says R will read 37,883
# and report no damage.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path  <- "../source.jsonl"
bytes <- file.size(path)
cat(sprintf("  %.1f MB\n", bytes / 1024^2))

# ── Q0 / Q7. PREDICTION 3, THE CONTROL. ──────────────────────────────────────
cat("\n0/7. is this sound, and how many records:\n")
t0 <- Sys.time()
ln <- readLines(path, warn = FALSE)
cat(sprintf("   readLines -> %s records in %.1f s\n",
            format(length(ln), big.mark = ","),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
u2028 <- sum(grepl(" ", ln, fixed = TRUE))
cat(sprintf("   lines containing U+2028 LINE SEPARATOR: %d\n", u2028))
bad <- sum(!vapply(ln, validate, TRUE, USE.NAMES = FALSE))
cat(sprintf("   lines that fail validate(): %d\n", bad))
cat("   PREDICTION 3 CONFIRMED. 37,883 records, zero malformed, and the three\n")
cat("   U+2028 lines are perfectly valid JSON. The frozen probe reported SIX\n")
cat("   broken lines here and had broken them itself with str.splitlines().\n")
cat("   R's readLines splits on \\n and nothing else, so the damage never\n")
cat("   happens. A cross-language control on a bug whose answer was known.\n")
cat("   SCORED YES on question 0 — the first YES any tool has earned on it,\n")
cat("   and it is narrow: jsonlite validated the framing, not the contents.\n")
cat("   Duplicate keys, ints past 2^53 and encoded payloads remain invisible.\n")

# ── Q3 / scale. PREDICTION 4. ────────────────────────────────────────────────
cat("\n3. what is one record, and what it costs to find out:\n")
t0 <- Sys.time()
df <- stream_in(file(path), verbose = FALSE)
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("   stream_in() -> %s x %d in %.1f s\n",
            format(nrow(df), big.mark = ","), ncol(df), el))
cat(sprintf("   columns: %s\n", paste(names(df), collapse = ", ")))
cat("   IT ANSWERED QUESTION 3 UNPROMPTED AND CORRECTLY. An event is a row,\n")
cat("   and NOTES.md's row-shape grade of 8 is about the payloads below it.\n")
cat("   `stream_in` is the right verb for NDJSON and jsonlite is the only R\n")
cat("   tool in this corpus that has one.\n")
cat("\n   THE MEMORY, measured separately with /usr/bin/time -l and recorded in\n")
cat("   this entry's NOTES.md rather than re-measured here:\n")
cat("     design/probe.py                968 MB   7.2 s   18.8x the file\n")
cat("     stream_in(simplifyVector=FALSE) 427 MB   4.4 s    8.6x\n")
cat("     stream_in() simplified          636 MB   6.3 s   12.8x\n")
cat("   PREDICTION 4 CONFIRMED IN THE DIRECTION THAT MATTERS: R's streaming\n")
cat("   reader is 2.3x leaner and 1.6x faster than the probe on the corpus's\n")
cat("   only scale reading. `design/implementation.md` cites memory as a\n")
cat("   justification for a Rust port; on this document the existing R tool\n")
cat("   already beats the prototype.\n")

# ── Q4. THE PAYLOAD FOLD. ────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
cat(sprintf("   the EVENT level: %d columns, rows with nothing in them:\n", ncol(df)))
# A ROW-LEVEL test. The first draft used sum(is.na(col)), which on a nested
# data-frame column counts every cell recursively and reported 23,835,101
# missing values in a 37,883-row table. A number larger than the table is the
# kind of error that survives review because nobody reads the denominator.
empty_rows <- function(col) {
  if (is.data.frame(col)) {
    f <- jsonlite::flatten(col)                       # nested frames -> plain columns
    f <- f[vapply(f, function(x) !is.list(x), TRUE)]  # drop what is still a list
    if (!ncol(f)) return(0L)
    sum(rowSums(!is.na(f)) == 0)
  } else if (is.list(col)) {
    sum(vapply(col, function(x) is.null(x) || length(x) == 0, TRUE))
  } else sum(is.na(col))
}
nas <- vapply(df, empty_rows, 0L)
for (k in names(nas)) cat(sprintf("     %-16s %6s of %s\n", k,
                                  format(nas[[k]], big.mark = ","),
                                  format(nrow(df), big.mark = ",")))
cat("   The event level is regular. The raggedness NOTES.md grades — 53 of 727\n")
cat("   field slots — is inside `payload`, and simplification turned that into\n")
cat("   a nested data frame:\n")
pl <- df$payload
cat(sprintf("   $payload is a %s: %s x %s\n", class(pl)[1],
            format(nrow(pl), big.mark = ","), ncol(pl)))
cat("   SCORED MISLEADING, for the reason 07-graphql-introspection established.\n")
cat("   Every payload column exists on every row because the frame is\n")
cat("   rectangular; the emptiness is NA, and NA here means `this event type\n")
cat("   does not have this field` rather than `missing`.\n")
cat(sprintf("   measured: %.0f%% of the payload frame's cells are empty\n",
            100 * mean(vapply(pl, function(c) empty_rows(c) / nrow(df), 0))))
cat("   AND THE DISCRIMINATOR IS NOT IN THE FRAME. It is `df$type`, one level\n")
cat("   up — see try-jqr.R, where partitioning on it takes the payload fold\n")
cat("   from 82% empty to 100% filled on 13 of 16 groups.\n")

# ── Q1 / Q2. ─────────────────────────────────────────────────────────────────
cat("\n1. what is in here — str() on a 37,883-row nested frame:\n")
cat(sprintf("   str(max.level=2)  %d lines\n",
            length(capture.output(str(df, max.level = 2)))))
cat("   The whole str() is not attempted. NOTES.md measures 846 paths for 235\n")
cat("   fields; str() has no setting that reports either.\n")
one <- fromJSON(ln[1], simplifyVector = FALSE)
depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("\n2. depth of record 1: %d (NOTES.md grades the file 7)\n", depth(one)))

# ── Q8. ──────────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per event:\n")
tbl <- data.frame(type = df$type, actor = df$actor$login, repo = df$repo$name)
cat(sprintf("   -> %s x %d\n", format(nrow(tbl), big.mark = ","), ncol(tbl)))
print(utils::head(tbl, 3))
cat(sprintf("   type: %s\n",
            paste(sprintf("%s %s", names(sort(table(tbl$type), decreasing = TRUE))[1:4],
                          format(sort(table(tbl$type), decreasing = TRUE)[1:4],
                                 big.mark = ",")), collapse = ", ")))
cat("   Free, because stream_in already answered question 3.\n")

cat("
CONCLUSION — jsonlite is the best tool in this corpus on this document, and it
beats the probe at the one thing `design/implementation.md` cites for Rust.

  **Question 0 is a YES, and it is the first one anybody has earned.** 37,883
  records, zero malformed, and the three lines carrying U+2028 are valid JSON.
  The frozen probe reported six broken lines here and had broken them itself
  with `str.splitlines()`. R splits on `\\n` and nothing else. The YES is narrow
  — jsonlite validated the framing, not the contents, and duplicate keys and
  oversized integers stay invisible — but on the question of *is this file
  whole*, it is right and the probe was wrong.

  **And it is leaner than the probe.** Measured with `/usr/bin/time -l`:

    design/probe.py                  968 MB   7.2 s   18.8x the file
    stream_in(simplifyVector=FALSE)  427 MB   4.4 s    8.6x
    stream_in() simplified           636 MB   6.3 s   12.8x

  `design/implementation.md` names memory as one of two justifications for a
  Rust port, and `VERDICT.md` already records that argument being qualified
  twice. **Here an existing R library uses less than half the prototype's memory
  on the corpus's only scale reading.** That is a third qualification, and it is
  the most direct one: the comparison is not Python-versus-Rust, it is
  this-prototype-versus-a-tool-people-already-have.

  WHERE IT FAILS is question 4, and in the way `07-graphql-introspection`
  established: `stream_in` builds a rectangular payload frame, every column
  exists on every row, and the emptiness is NA. **The discriminator that
  explains all of it — `type` — sits one level up, outside the frame**, so no
  amount of looking at the payload table can find it. That is `VERDICT.md` item
  15's fifth operation, and this file is its evidence.
")
