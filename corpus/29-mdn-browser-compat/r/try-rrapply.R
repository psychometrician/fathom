# rrapply — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  TOP LEVEL ONLY without the melt
#   2 how deep                                    2   NO                  YES — 12, from the melt's width
#   3 what is one record                          6   NO                  CANNOT — names none, prices none
#   4 always present vs sometimes                 5   NO                  yes, after the melt
#   5 does any field change type                 22   NO                  **WRONG** — the melt COERCES, see below
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            3   NO                  yes — 470,673 leaves
#   8 three named fields to a table               5  YES                  yes, but by `$` not by rrapply
#   9 a field missing from some rows              4  YES                  YES — NULL, row survives
#  10 flatten the deepest array                   3   NO                  yes, it is already in the melt
#  11 find every path matching something         14   NO                  YES, but it FOLDS NOTHING
#  12 flattest honest table                       3   NO                  YES — ONE CALL, 470,673 x 13, 0.4 s
#  13 needed the shape in advance?                    NO for 1, 2, 4, 10, 11, 12. The >40 threshold is MINE
#  14 survives the next file unchanged?               YES — nothing names a level
#  15 readable a week later?                          YES — one verb, one argument
#  16 lines, and how much is ceremony?                ~135, and ~40 of it is measuring the coercion
#
# **Q5 IS THE ONE THAT MATTERS AND IT IS A SILENT WRONG ANSWER.** `version_added`
# is 228,083 strings and 57,103 booleans; jsonlite preserves both and the melt
# returns all 285,186 as character. This document was CHOSEN for that field.

suppressMessages({library(jsonlite); library(rrapply)})
cat(sprintf("jsonlite %s · rrapply %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("rrapply"),
            R.version$major, R.version$minor))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("parse: %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

# ── Q1. Top level only, without help. ────────────────────────────────────────
cat(sprintf("\nQ1  names(doc) -> %d keys: %s\n", length(doc),
            paste(names(doc), collapse = ", ")))
cat("    That is ONE level. The full field list comes from the melt below,\n")
cat("    which is Q12 doing Q1's work.\n")

# ── Q12. THE MELT. One call, no shape known in advance. ──────────────────────
t0 <- Sys.time()
melt <- rrapply(doc, how = "melt")
secs <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\nQ12 rrapply(doc, how = \"melt\") -> %s rows x %d cols in %.1f s\n",
            format(nrow(melt), big.mark = ","), ncol(melt), secs))
cat(sprintf("    columns: %s\n", paste(names(melt), collapse = ", ")))
cat("    ONE CALL, and the level columns are already columns.\n")

lev <- setdiff(names(melt), "value")
depth_of <- rowSums(!is.na(melt[, lev]))

# ── Q2. ──────────────────────────────────────────────────────────────────────
cat(sprintf("\nQ2  %d level columns -> depth %d. YES, from the melt's width.\n",
            length(lev), length(lev)))

# ── Q3/Q7. ───────────────────────────────────────────────────────────────────
cat("\nQ3  rrapply names no candidates and prices none. What it gives is counts:\n")
for (i in seq_len(min(4, length(lev)))) {
  n <- length(unique(do.call(paste, c(melt[, lev[seq_len(i)], drop = FALSE], sep = ""))))
  cat(sprintf("      distinct paths to level %d   %s\n", i, format(n, big.mark = ",")))
}
cat("    CANNOT — every one of those is defensible and rrapply proposes none.\n")

cat(sprintf("\nQ7  %s leaves at the bottom. yes.\n", format(nrow(melt), big.mark = ",")))

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\nQ4  leaves by depth:\n")
print(table(depth_of))
cat("    yes, once melted, and in one call rather than eleven.\n")

# ── Q5. THE TRI-TYPED FIELD, AND THE MELT DESTROYS IT. ───────────────────────
# This is the finding of the whole attempt and it was not predicted.
va <- melt[apply(melt[, lev], 1, function(r) "version_added" %in% r), ]
cat(sprintf("\nQ5  version_added: %s leaves after the melt, classes: %s\n",
            format(nrow(va), big.mark = ","),
            paste(sort(unique(vapply(va$value, function(z) class(z)[1], ""))),
                  collapse = ", ")))

# What jsonlite actually handed over, BEFORE rrapply touched it:
n_logical <- 0L; n_char <- 0L
scan <- function(n) {
  if (!is.list(n)) return(invisible())
  nm <- names(n)
  for (k in seq_along(n)) {
    if (!is.null(nm) && nm[k] == "version_added" && !is.list(n[[k]])) {
      if (is.logical(n[[k]])) n_logical <<- n_logical + 1L else n_char <<- n_char + 1L
    } else scan(n[[k]])
  }
}
scan(doc)
cat(sprintf("    but jsonlite gave: %s character and %s LOGICAL\n",
            format(n_char, big.mark = ","), format(n_logical, big.mark = ",")))
cat("    ** THE MELT COERCED THEM. ** `value` comes back as an ATOMIC character\n")
cat("    vector when the leaves are mixed, so a string and a boolean arrive\n")
cat("    indistinguishable. Minimal case:\n")
tiny <- list(a = list(v = "32"), b = list(v = FALSE), c = list(v = 7L))
tm <- rrapply(tiny, how = "melt")
cat(sprintf("      list(v=\"32\"), list(v=FALSE), list(v=7L) -> value is %s: %s\n",
            class(tm$value), paste(tm$value, collapse = ", ")))
cat("    NO for this document. The verb that answers Q12 best answers Q5 WRONG,\n")
cat("    and it does so silently — `FALSE` is also a legal version_added string,\n")
cat("    so the distinction cannot be recovered after the fact.\n")

cat("\nQ6  CANNOT. rrapply has no notion of a key being data.\n")

# ── Q8/Q9. ───────────────────────────────────────────────────────────────────
one <- doc$api$ANGLE_instanced_arrays$`__compat`
cat(sprintf("\nQ8  three named fields off one record: mdn_url=%s status.standard_track=%s source_file=%s\n",
            !is.null(one$mdn_url), one$status$standard_track, !is.null(one$source_file)))
cat("    yes, but by `$` — rrapply contributes nothing here.\n")
cat(sprintf("\nQ9  a missing field -> %s. NULL, and the row survives. YES.\n",
            ifelse(is.null(one$nope), "NULL", "?")))

# ── Q10. AND THE MELT CANNOT ANSWER IT. ──────────────────────────────────────
# The obvious reading — count level cells that look like an index — is measured
# first, then shown to be wrong.
tot <- sum(apply(melt[, lev], 1,
                 function(r) any(grepl("^[0-9]+$", trimws(r)), na.rm = TRUE)))
cat(sprintf("\nQ10 leaves whose path contains an all-digits segment: %s\n",
            format(tot, big.mark = ",")))

# The truth, from a walk that knows what kind of container it is standing in.
n_true <- 0L; n_leaf <- 0L; n_numkey <- 0L
tw <- function(x, under_array) {
  if (is.list(x) && length(x)) {
    nm <- names(x)
    if (is.null(nm)) {
      for (i in seq_along(x)) tw(x[[i]], TRUE)
    } else {
      for (i in seq_along(x)) {
        if (grepl("^[0-9]+$", nm[i])) n_numkey <<- n_numkey + 1L
        tw(x[[i]], under_array)
      }
    }
  } else {
    n_leaf <<- n_leaf + 1L
    if (under_array) n_true <<- n_true + 1L
  }
}
tw(doc, FALSE)
cat(sprintf("    leaves ACTUALLY under an array: %s   (over-count: %s)\n",
            format(n_true, big.mark = ","), format(tot - n_true, big.mark = ",")))
cat(sprintf("    and the cause: %s object keys in this document are all digits\n",
            format(n_numkey, big.mark = ",")))
cat("    — browser release versions, keyed `1`, `10`, `58`. ** ONCE A KEY AND AN\n")
cat("    INDEX ARE BOTH STRINGS IN A COLUMN, NOTHING SEPARATES THEM. ** The melt\n")
cat("    throws away the one bit that would, which is whether the parent was an\n")
cat("    array. PARTLY — the rows are all there and the question is not askable\n")
cat("    of them; answering it needs a walk that never melted.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────────
is_chr <- vapply(melt$value, is.character, logical(1))
urls <- melt[is_chr & grepl("^https?://", unlist(lapply(melt$value, function(z)
  if (is.character(z)) z[1] else NA_character_))), ]
cat(sprintf("\nQ11 %s URL leaves. YES — grepl over the melt's value column.\n",
            format(nrow(urls), big.mark = ",")))
upath <- do.call(paste, c(urls[, lev], sep = "."))
upath <- gsub("(\\.NA)+$", "", upath)
cat(sprintf("    distinct URL PATHS once the level columns are pasted: %s\n",
            format(length(unique(upath)), big.mark = ",")))
cat("    ** AND THAT IS ONE PATH PER VALUE, WHICH IS THE POINT. ** The melt does\n")
cat("    not fold anything: every literal key is its own path, so `distinct\n")
cat("    paths` and `leaves` are the same number. fathom folds and gets 11,320,\n")
cat("    which is defect 36 — but 35,392 is not a better answer to `where do the\n")
cat("    URLs live`, it is the same answer as `list them`.\n")

# What a reader would actually do next: drop the levels that are open
# vocabularies and count the SHAPES. rrapply gives the columns to do it with
# and no signal about which columns they are.
shape <- urls[, lev]
for (j in seq_along(lev)) {
  u <- unique(shape[[j]]); u <- u[!is.na(u)]
  if (length(u) > 40) shape[[j]] <- ifelse(is.na(shape[[j]]), NA, "<key>")
}
sp <- gsub("(\\.NA)+$", "", do.call(paste, c(shape, sep = ".")))
cat(sprintf("    collapse any level with >40 distinct keys to <key>: %s shapes\n",
            format(length(unique(sp)), big.mark = ",")))
cat("    ONE LINE, and the 40 is mine — rrapply proposes no threshold and no\n")
cat("    column to apply it to. That is question 13 failed and question 6 too.\n")

cat("
CONCLUSION. Written after the run and corrected against what printed.

rrapply melts 19.9 MB into 470,673 x 13 in 0.4 SECONDS, on top of a 0.3 s parse.
The tool-sweep prediction said `slow enough to notice, over 30 seconds` and that
was wrong by two orders of magnitude. Scale is simply not this verb's problem,
and entry 28's verdict that the melt is the best single verb in the R half
survives a document 33x larger.

TWO THINGS IT GETS WRONG, and neither was predicted.

THE MELT DESTROYS THE POLYMORPHISM. `version_added` is 228,083 strings and
57,103 booleans; jsonlite hands both over with their types intact and the melt
returns all 285,186 as character. `value` is an ATOMIC vector, so mixed leaves
are coerced, and `FALSE` is itself a legal version_added string — the
distinction cannot be recovered afterwards. Question 5 is the question this
document was CHOSEN for, and the tool that wins question 12 answers it wrong
while looking like it answered it.

AND IT FOLDS NOTHING. 35,392 URL leaves at 35,392 distinct paths, because every
literal key is its own path. That is not a better answer than fathom's 11,320
folded paths, it is a refusal to answer: `where do the URLs live` and `list the
URLs` return the same table.

BUT THE COLUMNS ARE THE RIGHT PRIMITIVE, and this is the finding that matters
for defect 36. Collapsing every level with more than 40 distinct keys gives
176 SHAPES in one line. fathom's fold gets 11,320 on the same document, and a
hand-collapse of fathom's own output gave 166 — so 176 is the right order and
fathom is wrong by a factor of 64.

THE ONE LINE IS NOT A REFUTATION THOUGH, because the 40 is mine. rrapply
proposes no threshold, names no column as an open vocabulary, and prices no row
shape; questions 3 and 6 are CANNOT. What it provides is L1…L12 as real
columns, which makes the fold a group_by that a person can write. fathom
attempts the same fold automatically and gets it wrong here — which is a worse
failure than not attempting it, and a smaller one than not providing the
columns.
")
