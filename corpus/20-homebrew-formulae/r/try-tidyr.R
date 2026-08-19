# tidyr — the Homebrew formulae catalogue, 8,536 formulae
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   30 MB, 8,536 formulae
#  measured      2026-08-11
#  run           cd corpus/20-homebrew-formulae/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  YES — 61 columns
#   2 how deep                                    2   NO                  by exhaustion
#   3 what is one record                          4   NO                  YES, and RIGHT
#   4 always present vs sometimes                 6   NO                  YES — 6 always empty
#   5 does any field change type                  4   NO                  NO — and see below
#   6 are any object keys data                   16   NO                  BOTH ANSWERS AGAIN
#   7 how many records                            3   NO                  yes — 8,536
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows               8  YES                  YES — 98% dropped
#  10 flatten the deepest array                    5  YES                 yes
#  11 find every path matching something           1   -                  CANNOT
#  12 flattest honest table                        4  YES                 8,536 x 61
#  13 needed the shape in advance?                    NO for 1, 3, 4, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~90
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS DOCUMENT HOLDS THE STRONGEST EVIDENCE IN THE CORPUS THAT KEYS-AS-DATA IS
# GENUINELY HARD, and tidyr adds a third verdict to it. NOTES.md records DuckDB
# typing `variations` as a MAP and `bottle.stable.files` as a STRUCT — one
# structure, one document, two verdicts, both keyed by the same platform names,
# from a tool sharing no code with the probe.
#
# TIDYR GIVES BOTH ANSWERS FOR BOTH SITES, and the choice is the verb:
#
#   unnest_wider(variations)                -> 8,536 x 16, platforms as COLUMNS
#   unnest_longer(variations, indices_to =) ->  5,295 rows, platforms as DATA
#
# That is entry 24's finding on a second document: tidyr is in two of question
# 6's three groups at once and the user picks. WHAT THIS DOCUMENT ADDS is that
# the two sites disagree about which choice is right — `variations` is keyed by
# 15 platform names on 2,148 of 8,536 formulae, an open vocabulary that grows
# with macOS; `bottle.stable.files` is keyed by 16 of the same names and is
# closer to a fixed schema. THE SAME VERB PAIR SERVES BOTH AND NOTHING IN THE
# DOCUMENT SAYS WHICH TO REACH FOR.
#
# THE SILENT COST IS THE LARGEST IN THE FOURTEEN FILES. unnest_longer(oldnames)
# returns 191 rows from 8,536 formulae, dropping 8,362 — 98% of the catalogue,
# with no warning.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

forms <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7. ───────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = forms), x)),
                    type = "message")
w <- tibble(x = forms) |> unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d, and it is right: one row per formula.\n", nrow(a), ncol(a)))
cat(sprintf("Q1  %d columns, %d list-columns. Q7  %d formulae.\n",
            ncol(w), sum(map_lgl(w, is.list)), nrow(w)))

# ── Q6. THE CENTREPIECE: two keyed sites, two verbs each. ─────────────────
vk <- unique(unlist(map(forms, \(f) names(f$variations))))
bk <- unique(unlist(map(forms, \(f) names(f$bottle$stable$files))))
cat(sprintf("\nQ6  TWO KEYED SITES, both keyed by platform names:\n"))
cat(sprintf("    `variations`           %2d distinct keys, non-empty on %d of %d\n",
            length(vk), sum(lengths(w$variations) > 0), nrow(w)))
cat(sprintf("    `bottle.stable.files`  %2d distinct keys\n", length(bk)))
cat(sprintf("    they overlap on %d names — one structure, and DuckDB types the\n",
            length(intersect(vk, bk))))
cat("    first a MAP and the second a STRUCT, which NOTES.md calls the\n")
cat("    strongest evidence here that keys-as-data is hard rather than\n")
cat("    merely unimplemented.\n")
vw <- w |> select(name, variations) |>
  unnest_wider(variations, names_repair = "unique_quiet")
vl <- w |> select(name, variations) |>
  unnest_longer(variations, indices_to = "platform")
cat(sprintf("\n    unnest_wider(variations)                -> %d x %d, PLATFORMS AS COLUMNS\n",
            nrow(vw), ncol(vw)))
cat(sprintf("    unnest_longer(variations, indices_to =) -> %d rows, %d platforms AS DATA\n",
            nrow(vl), n_distinct(vl$platform)))
cat("    ══ BOTH ANSWERS, AS TWO VERBS, ON A SECOND DOCUMENT. ══\n")
cat("    Entry 24 found the same pair on Cargo's feature names. What this\n")
cat("    document adds is that the two keyed sites want DIFFERENT answers —\n")
cat("    `variations` is an open vocabulary that grows with macOS, and\n")
cat("    `bottle.stable.files` is nearer a fixed schema — and nothing in the\n")
cat("    document says which is which. The verb pair serves both and the\n")
cat("    judgement is entirely the reader's.\n")

# ── Q9. the silent drop, at its worst. ────────────────────────────────────
cat("\nQ9  THE SILENT DROP, largest in the fourteen files:\n")
for (cn in c("oldnames", "aliases", "versioned_formulae", "patches", "urls")) {
  d <- nrow(w |> unnest_longer(all_of(cn)))
  k <- nrow(w |> unnest_longer(all_of(cn), keep_empty = TRUE))
  cat(sprintf("    %-20s %6d rows   keep_empty %6d   DROPS %5d (%.0f%%)\n",
              cn, d, k, k - d, 100 * (k - d) / nrow(w)))
}
cat("    `oldnames` loses 98% of the catalogue and prints nothing. A reader\n")
cat("    who asked to flatten it gets a 191-row table that looks complete.\n")

# ── Q4 / Q5 / Q8 / Q11 / Q12 / Q2. ────────────────────────────────────────
fill <- map_dbl(w, \(c) mean(if (is.list(c)) lengths(c) > 0 else !is.na(c)))
cat(sprintf("\nQ4  %d of %d columns are empty on every formula: %s\n",
            sum(fill == 0), ncol(w),
            paste(names(fill)[fill == 0], collapse = ", ")))
cat("Q5  NO variation reported, and that is not the same as none: the\n")
cat("    polymorphism polars names on this document lives inside list-columns,\n")
cat("    where tidyr never types anything. NOTES.md records polars giving four\n")
cat("    different causes in six fresh processes; tidyr gives none, every time.\n")
cat("    A stable silence is not agreement.\n")
three <- tibble(x = forms) |>
  hoist(x, name = "name", tap = "tap", license = "license") |>
  select(name, tap, license)
cat(sprintf("\nQ8  hoist() -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat("\nQ11 CANNOT. No predicate over values.\n")
cat(sprintf("\nQ12 %d x %d with %d list-columns. WHAT IS LOST: every keyed site\n",
            nrow(w), ncol(w), sum(map_lgl(w, is.list))))
cat("    keeps its keys only if `indices_to` was asked for, and the 26 list\n")
cat("    columns are 26 separate decisions.\n")
cat("Q2  by exhaustion — no call reports the depth.\n")

cat("
13. NO for 1, 3, 4 and 7.

14. YES for the verbs. The formulae catalogue gains platforms every macOS
    release, so `unnest_wider(variations)` gains columns and any code naming
    them breaks — which is question 14 answered by the DOCUMENT, as on
    ../../24-cargo-metadata.

16. ~90 lines, and the two-verb comparison is fifteen of them.
")
