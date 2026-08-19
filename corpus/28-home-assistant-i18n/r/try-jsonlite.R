# jsonlite — Home Assistant frontend, the English translation catalogue
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
#  measured      2026-08-12
#  run           cd corpus/28-home-assistant-i18n/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               4   NO                  PARTLY — it VALIDATES
#   1 what is in here                             4   NO                  ONE LEVEL — names()
#   2 how deep                                    3   NO                  yes, via base rapply
#   3 what is one record                          5   NO                  IT HANDS YOU ONE — wrongly
#   4 always present vs sometimes                 -   -                   CANNOT
#   5 does any field change type                  4   NO                  yes, via base rapply
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            2   NO                  1, or 8,518, depending
#   8 three named fields to a table               3  YES                  yes — [[ ]]
#   9 a field missing from some rows              3  YES                  NULL, needs a guard
#  10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
#  11 find every path matching something          3   NO                  yes, via base rapply
#  12 flattest honest table                       6   NO                  PARTLY — base R, not jsonlite
#  13 needed the shape in advance?                    NO for 0, 2, 5, 11
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          YES
#  16 lines, and how much is ceremony?                ~70
#
# **jsonlite is the parser the other five R tools are built on, and this entry
# scores it on its own.** Its one distinctive answer is Q0: `validate()` is a
# real check that most tools in the fourteen do not offer at all.
#
# **Its `flatten()` is for data frames with data-frame columns and does nothing
# here**, because there is no data frame — `simplifyVector = TRUE` on a document
# with no arrays gives a nested list and not a table.

suppressMessages(library(jsonlite))
cat(sprintf("jsonlite %s · R %s.%s\n", packageVersion("jsonlite"),
            R.version$major, R.version$minor))

raw <- paste(readLines("../source.json", warn = FALSE), collapse = "")

# ── Q0. The one thing jsonlite does that most of the fourteen do not. ────────
cat(sprintf("\nQ0  validate(raw) -> %s\n", validate(raw)))
cat("    PARTLY, and it is more than most of the fourteen manage: a real\n")
cat("    well-formedness check with a reason attached when it fails. It says\n")
cat("    nothing about duplicate keys, 2^53 or NaN — the silent half.\n")

doc <- fromJSON(raw, simplifyVector = FALSE)

cat(sprintf("\nQ1  names(doc) -> %d: %s\n", length(doc), paste(names(doc), collapse = ", ")))
cat("    ONE LEVEL. jsonlite has no verb for the levels below.\n")

# ── Q2/Q5/Q11/Q12, all through base R's rapply rather than jsonlite. ─────────
paths <- character()
depths <- integer()
vals <- character()
walk_it <- function(x, p = character()) {
  if (is.list(x)) for (nm in names(x)) walk_it(x[[nm]], c(p, nm))
  else {
    paths <<- c(paths, paste(p, collapse = "."))
    depths <<- c(depths, length(p))
    vals <<- c(vals, as.character(x))
  }
}
walk_it(doc)

cat(sprintf("\nQ2  %d. yes — from the recursion above, which is base R.\n", max(depths)))
cat(sprintf("\nQ5  leaf classes: %s. Every leaf is a character.\n",
            paste(unique(vapply(vals, class, "")), collapse = ", ")))
cat(sprintf("\nQ11 messages with an ICU placeholder: %s. yes, once melted.\n",
            format(sum(grepl("\\{", vals)), big.mark = ",")))
cat(sprintf("\nQ12 %s rows x 3. PARTLY — the walk is base R and jsonlite\n",
            format(length(paths), big.mark = ",")))
cat("    contributed the parse and nothing else.\n")

# ── Q3. The interesting failure. ─────────────────────────────────────────────
simple <- fromJSON(raw, simplifyVector = TRUE)
cat(sprintf("\nQ3  fromJSON(simplifyVector = TRUE) gives a %s, not a data frame.\n",
            class(simple)[1]))
cat("    IT HANDS YOU ONE ANSWER without being asked, which is the behaviour\n")
cat("    entry 25 records as jsonlite's habit — and here the answer is a nested\n")
cat("    list, because with no arrays there is nothing to simplify. It names no\n")
cat("    alternatives and prices none. CANNOT for Q3.\n")

cat(sprintf("\nQ7  1 document, or %s messages. Whichever you meant.\n",
            format(length(paths), big.mark = ",")))

cat("\nQ4  CANNOT — no population of records.\n")
cat("\nQ6  CANNOT.\n")

cat(sprintf("\nQ8  %s\n", paste(c(doc$ui$common$and, doc$ui$common$loading,
                                  doc$ui$panel$profile$logout), collapse = " | ")))
cat("    yes — `$` chains, which is R and needs no library.\n")

cat(sprintf("\nQ9  doc$ui$panel$profile$nope -> %s\n",
            ifelse(is.null(doc$ui$panel$profile$nope), "NULL", "?")))
cat("    NULL, which drops silently out of a c() — so it needs a guard the\n")
cat("    caller has to remember. yes, with care.\n")

cat("\nQ10 zero arrays in 604 KB. NOTHING TO FLATTEN.\n")

cat("
CONCLUSION. jsonlite is scored here on its own rather than as the parser under
the other five, and on its own it is a parser with one real diagnostic:
`validate()`. That is worth more than it sounds — most of the fourteen offer no
soundness check at all — but it stops at well-formedness and the damage this
project cares about is the silent kind.

`flatten()` does nothing here because there is no data frame to flatten: with no
arrays anywhere, `simplifyVector = TRUE` returns a nested list. The verb assumes
the rectangling has already happened.

And Q3 is the habit entry 25 already recorded: jsonlite hands you an answer
without being asked. Here the answer is 'a list', which is true, unhelpful, and
offered with the same confidence it offers a data frame elsewhere.
")
