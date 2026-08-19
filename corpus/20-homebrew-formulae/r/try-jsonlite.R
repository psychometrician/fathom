# jsonlite — Homebrew's whole formula index
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
#  measured      2026-08-11
#  run           cd corpus/20-homebrew-formulae/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   PARTLY
#   1 what is in here                             8   NO                  PARTLY — 61 of 1,132
#   2 how deep                                    2   -                   CANNOT
#   3 what is one record                          2   NO                  PARTLY
#   4 always present vs sometimes                14   NO                  DEPENDS ON A FLAG
#   5 does any field change type                  8   YES                 NO — resolves silently
#   6 are any object keys data                    7   NO                  NO — keys become columns
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               3   YES                 yes, it is already a frame
#   9 a field missing from some rows              14  YES                 PARTLY — see below
#  10 flatten the deepest array                  13   YES                 yes — 557, correct
#  11 find every path matching something          8   NO                  PARTLY — 3 of 48
#  12 flattest honest table                       9   NO                  yes, and not flat
#  13 needed the shape in advance?                    for 5, 6, 9, 10, 11 — yes
#  14 survives the next file unchanged?               Q1/Q4/Q12 yes, the rest no
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~140, and jsonlite is 3 calls
#  timing        fromJSON 5.6s simplified, 0.3s unsimplified(!). flatten 0.0s
#
# ENTRY 15's HEADLINE REPRODUCES ON A DOCUMENT 85x LARGER. `simplifyVector`
# decides the answer to question 4, and the wrong answer is the DEFAULT:
#     fromJSON(file)                    13 of 31 atomic columns hold an NA
#     fromJSON(file, simplifyVector=F)  3 keys sometimes ABSENT
#                                       17 keys always present but NULL
# One flag, documented as controlling array simplification and nothing else.
# The corpus now has three different answers to question 4 on this one
# document — jsonlite 13, pandas 18, DuckDB 20 — and only the walkers' 3-and-17
# is the document's own answer.
#
# QUESTION 9 COLLAPSES TWO STATES AND THE LARGER ONE IS THE SURPRISE. The frame
# reports 1,410 rows with `length(executables) == 0`. The document has 185
# formulae that OMIT the key and 1,225 that write an empty list. `length() == 0`
# is the only test the simplified frame offers and it cannot separate them.
#
# `jsonlite::flatten` MASKS `purrr::flatten`. Entry 18 lost a run to that
# collision; it is noted here so the next session does not lose a second.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

RAW <- "../source.json"

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  jsonlite parses or errors. It has no duplicate-key report and no\n")
cat("    big-int report, and it REFUSES bare NaN — which is more than most\n")
cat("    parsers here do, and is not a report either. PARTLY.\n")

# ── The two parses, timed. ───────────────────────────────────────────────────
t0 <- Sys.time()
simple <- fromJSON(RAW)
t_simple <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
t0 <- Sys.time()
raw <- fromJSON(RAW, simplifyVector = FALSE)
t_raw <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\n     fromJSON(...)                      %.1fs -> %s\n",
            t_simple, paste(class(simple), collapse = "/")))
cat(sprintf("     fromJSON(simplifyVector = FALSE)   %.1fs -> %s of %d\n",
            t_raw, class(raw), length(raw)))

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
cat(sprintf("\nQ1  simplified: a data frame, %d rows x %d columns\n",
            nrow(simple), ncol(simple)))
cat(sprintf("    column names: %s …\n", paste(head(names(simple), 8), collapse = ", ")))
nested <- names(simple)[vapply(simple, \(c) is.list(c) || is.data.frame(c), logical(1))]
cat(sprintf("Q1  %d of those %d columns are themselves lists or data frames\n",
            length(nested), ncol(simple)))
cat("    THE SIMPLIFICATION IS THE ANSWER AND IT IS ONE LEVEL DEEP. jsonlite\n")
cat("    turned the root array into a frame and stopped; the probe reports 1,132\n")
cat("    distinct paths and jsonlite reports 61 columns.\n")
cat("Q2  no depth verb. A nested data frame column has to be recursed by hand,\n")
cat("    which is what try-purrr.R does. CANNOT.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat(sprintf("\nQ3  the simplified frame names ONE candidate — a formula — and prices\n"))
cat(sprintf("    none. %d rows.\n", nrow(simple)))
cat(sprintf("Q7  %d formulae\n", length(raw)))

# ── Q4. THE simplifyVector EXPERIMENT. ───────────────────────────────────────
cat("\nQ4  ══ THE SAME QUESTION, TWO PARSES, TWO ANSWERS ══\n")
na_cols <- vapply(simple, \(c) if (is.list(c) || is.data.frame(c)) 0L
                              else sum(is.na(c)), integer(1))
cat(sprintf("    simplified frame: %d of %d atomic columns hold any NA\n",
            sum(na_cols > 0), sum(!vapply(simple, \(c) is.list(c) || is.data.frame(c), logical(1)))))
present <- table(unlist(lapply(raw, names)))
absent <- present[present < length(raw)]
nulls <- sum(vapply(names(present), \(k)
  any(vapply(raw, \(f) k %in% names(f) && is.null(f[[k]]), logical(1))), logical(1)))
cat(sprintf("    simplifyVector = FALSE + names(): %d keys sometimes ABSENT — %s\n",
            length(absent), paste(names(absent), collapse = ", ")))
cat(sprintf("                                      %d keys always present but NULL\n", nulls))
cat("    ENTRY 15's FINDING REPRODUCES ON A DOCUMENT 85x LARGER. One flag,\n")
cat("    documented as controlling ARRAY SIMPLIFICATION and nothing else,\n")
cat("    decides whether question 4 gets the right answer. Nothing warns you,\n")
cat("    and the wrong answer is the DEFAULT.\n")

# ── Q5. Does any field change type between records? ──────────────────────────
cat("\nQ5  in the simplified frame, what jsonlite chose for the polymorphic sites:\n")
for (k in c("uses_from_macos", "conflicts_with_reasons", "license", "service")) {
  cat(sprintf("    %-24s %s\n", k, paste(class(simple[[k]]), collapse = "/")))
}
cat("    `uses_from_macos` is strings on 1,163 formulae and OBJECTS on 632, and\n")
cat("    jsonlite resolved it to a list column without a word. A list column is\n")
cat("    the honest representation and it is not a REPORT: the polymorphism is\n")
cat("    preserved and unannounced, which is jsonlite's whole character.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
files <- simple$bottle$stable$files
cat(sprintf("\nQ6  bottle$stable$files simplified to a %s with %d columns:\n",
            paste(class(files), collapse = "/"), ncol(files)))
cat(sprintf("    %s\n", paste(names(files), collapse = ", ")))
cat("    SIXTEEN PLATFORM NAMES BECAME SIXTEEN COLUMNS. jsonlite makes exactly\n")
cat("    the pandas choice — keys become schema — and like pandas it never\n")
cat("    raises the question. The probe folds them to one path and declines to\n")
cat("    call them data; DuckDB calls the sibling site a MAP. Three answers.\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl <- simple[, c("name", "desc", "homepage")]
cat(sprintf("\nQ8  simple[, c(...)] -> %d rows x %d cols, and it is already a frame\n",
            nrow(tbl), ncol(tbl)))
print(head(tbl, 2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
cat(sprintf("\nQ9  executables: %s in the frame\n", paste(class(simple$executables), collapse = "/")))
n_empty <- sum(vapply(simple$executables, \(x) length(x) == 0, logical(1)))
absent <- sum(!vapply(raw, \(f) "executables" %in% names(f), logical(1)))
emptyarr <- sum(vapply(raw, \(f) "executables" %in% names(f) &&
                                 length(f$executables) == 0, logical(1)))
cat(sprintf("    the frame says %d of %d rows have length 0. The document says:\n",
            n_empty, nrow(simple)))
cat(sprintf("      ABSENT              %5d\n", absent))
cat(sprintf("      present, empty []   %5d\n", emptyarr))
cat(sprintf("      present, non-empty  %5d\n", nrow(simple) - n_empty))
cat("    TWO DISTINCT STATES COLLAPSED INTO ONE, and the larger of them is the\n")
cat("    one nobody would guess: 1,225 formulae WRITE an empty list, 185 omit\n")
cat("    the key. `length(x) == 0` cannot tell them apart, and it is the only\n")
cat("    test the simplified frame offers. The rows are kept, which is what Q9\n")
cat("    asked; what is lost is why they are empty.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
t0 <- Sys.time()
res <- do.call(rbind, lapply(raw, \(f) {
  ps <- f$patches; if (is.null(ps)) return(NULL)
  do.call(rbind, lapply(ps, \(p) {
    rs <- p$resolves; if (is.null(rs)) return(NULL)
    data.frame(name = f$name,
               id = vapply(rs, \(x) x$id %||% NA_character_, character(1)),
               type = vapply(rs, \(x) x$type %||% NA_character_, character(1)))
  }))
}))
cat(sprintf("\nQ10 patches[].resolves[] -> %d rows x %d, %.1fs\n", nrow(res), ncol(res),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    Two nested lapply and two NULL guards, over the UNSIMPLIFIED parse.\n")
cat("    Over the simplified one it is worse: `simple$patches` is a list of\n")
cat("    data frames whose `resolves` column is a list of data frames, and the\n")
cat("    rows that have no patches are NULL entries in that list.\n")

# ── Q11. Find every path whose value matches something. ──────────────────────
cat("\nQ11 jsonlite has no path language and no search. Column-wise on the\n")
cat("    simplified frame, over the atomic character columns only:\n")
chr <- names(simple)[vapply(simple, is.character, logical(1))]
n_naive <- sum(vapply(chr, \(k) any(startsWith(simple[[k]], "http"), na.rm = TRUE), logical(1)))
n_strict <- sum(vapply(chr, \(k) any(grepl("^https?://", simple[[k]])), logical(1)))
cat(sprintf("    %d character columns; %d hold an http-prefixed value, %d a ^https?:// one\n",
            length(chr), n_naive, n_strict))
cat("    Against 65 and 48 distinct PATHS from the six tools that can walk.\n")
cat("    The gap is not accuracy, it is reach: a column scan sees level 1.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
t0 <- Sys.time()
flat <- flatten(simple)
cat(sprintf("\nQ12 jsonlite::flatten -> %d rows x %d cols, %.1fs\n",
            nrow(flat), ncol(flat), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
still <- names(flat)[vapply(flat, \(c) is.list(c) || is.data.frame(c), logical(1))]
cat(sprintf("    %d columns are STILL lists or frames after flattening\n", length(still)))
cat("    `flatten` expands nested DATA FRAMES and leaves list-columns alone, so\n")
cat("    it is honest and it is not flat. What was lost: nothing. What it costs\n")
cat("    is that the result cannot go into god, which refuses list-columns.\n")
cat("    NOTE `jsonlite::flatten` MASKS `purrr::flatten` — entry 18 lost a run\n")
cat("    to that collision. Load order decides which function you called.\n")
