# tidyr — an npm package-lock.json, 1,657 packages keyed by install path
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   760 KB, 1,657 packages, 144 key-sets
#  measured      2026-08-11
#  run           cd corpus/13-package-lock/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  ONE LEVEL — 5, then 22
#   2 how deep                                    -   -                   CANNOT
#   3 what is one record                          9   NO                  BOTH WAYS, BOTH WIDE
#   4 always present vs sometimes                 5   NO                  YES — 144 key-sets
#   5 does any field change type                  2   -                   CANNOT here
#   6 are any object keys data                   10   NO                  RAISES, and well
#   7 how many records                            3   NO                  yes — 1,657 / 2,841
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              7  YES                  YES — and see the drop
#  10 flatten the deepest array                   5  YES                  yes
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       4  YES                  1,657 x 22
#  13 needed the shape in advance?                    NO for 1, 4, 6, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~95
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS DOCUMENT GIVES ONE VERB TWO CONTRADICTORY REASONS FOR THE SAME VERDICT.
# The 1,657 install paths are keys-as-data of the purest kind. Hand the packages
# object to `unnest_auto` as ONE element and it says "elements have 1657 names in
# common" and goes wide. Hand it the same data as 1,657 ROWS and it says
# "elements have 1 names in common" and goes wide. SAME ANSWER, OPPOSITE
# EVIDENCE, and the only difference is how you framed the input — which is the
# thing you were asking it to work out.
#
# AND THE WIDE ANSWER RAISES RATHER THAN LYING. A package-lock's root entry is
# keyed by the EMPTY STRING, npm's way of saying "the project itself", so
# widening 1,657 paths into columns needs a column named "". tidyr refuses:
#   Can't unnest elements with missing names. Supply `names_sep`.
# Set beside entry 01, where jq listed 3,100 field names and rrapply 3,112
# because neither could tell a key from a field, A LOUD REFUSAL IS THE BETTER
# FAILURE — it is the same distinction this project's health verb is built on.
#
# THE COST IS PAID SOMEWHERE ELSE, SILENTLY. unnest_longer(devDependencies)
# returns 104 rows from 1,657, dropping 1,656 records without a word.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

doc  <- fromJSON("../source.json", simplifyVector = FALSE)
pkgs <- doc$packages

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q7. ────────────────────────────────────────────────────────────────
root <- tibble(d = list(doc)) |> unnest_wider(d)
w <- tibble(path = names(pkgs), x = unname(pkgs)) |>
  unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ1  root -> %d x %d: %s\n", nrow(root), ncol(root),
            paste(names(root), collapse = ", ")))
cat(sprintf("Q1  packages, keys kept as a column -> %d x %d\n", nrow(w), ncol(w)))
cat("Q2  CANNOT — one level per verb.\n")

# ── Q3 / Q6. THE CENTREPIECE: two framings, two reasons, one verdict. ──────
say <- function(lbl, tb) {
  msg <- character()
  r <- withCallingHandlers(
    tryCatch(suppressWarnings(unnest_auto(tb, x)),
             error = \(e) structure(conditionMessage(e), class = "oops")),
    message = \(m) { msg <<- c(msg, conditionMessage(m)); invokeRestart("muffleMessage") })
  cat(sprintf("    %s\n      says: %s\n", lbl,
              trimws(gsub("\n", " ", paste(msg, collapse = " ")))))
  if (inherits(r, "oops"))
    cat(sprintf("      RAISES: %s\n", trimws(gsub("\n", " ", as.character(r)))))
  else cat(sprintf("      -> %d x %d\n", nrow(r), ncol(r)))
}
cat("\nQ3/Q6  the same data, framed two ways:\n")
say("the packages OBJECT as ONE element", tibble(x = list(pkgs)))
say("the same packages as 1,657 ROWS", tibble(x = unname(pkgs)))
cat(sprintf("      the first key is the EMPTY STRING: '%s' — npm's name for the\n",
            names(pkgs)[1]))
cat("      project itself, and the reason the wide answer cannot be built.\n")
cat("    ══ SAME VERDICT, CONTRADICTORY EVIDENCE. ══\n")
cat("    1657 names in common, or 1 name in common, and `unnest_wider` either\n")
cat("    way. Which reason you get depends only on whether you had already\n")
cat("    decided that a package is a row — which IS question 3. Entry 24 found\n")
cat("    the rule is an intersection; here the intersection is computed over\n")
cat("    two different things and never over the one that matters.\n")
cat("    THE REFUSAL IS THE GOOD PART. On entry 01 jq listed 3,100 field names\n")
cat("    and rrapply 3,112, both silently. This one stops and says why.\n")

# ── Q4 / Q5. ───────────────────────────────────────────────────────────────
inter <- Reduce(intersect, map(pkgs, names))
ks <- length(unique(map_chr(pkgs, \(x) paste(sort(names(x)), collapse = ","))))
cat(sprintf("\nQ4  %d distinct key-sets over %d packages; the intersection is %s\n",
            ks, length(pkgs), paste(inter, collapse = ", ")))
fill <- map_dbl(w, \(c) mean(if (is.list(c)) lengths(c) > 0 else !is.na(c)))
cat(sprintf("Q4  columns filled on under 10%% of rows: %d of %d\n",
            sum(fill < .1), ncol(w)))
cat("Q5  CANNOT. Every varying field here is a list-column, and a list-column\n")
cat("    holds whatever it holds — contrast 12-agent-trace, where the same\n")
cat("    verb refused and named the two records that disagreed.\n")

# ── Q7 / Q9 / Q10. the silent drop, which is this document's real cost. ────
cat("\nQ9/Q10  unnest_longer on each dependency map, default vs keep_empty:\n")
for (cn in c("dependencies", "devDependencies", "optionalDependencies",
             "peerDependencies", "engines")) {
  d <- nrow(w |> unnest_longer(all_of(cn), indices_to = "dep"))
  k <- nrow(w |> unnest_longer(all_of(cn), indices_to = "dep", keep_empty = TRUE))
  cat(sprintf("    %-22s %5d rows   keep_empty %5d   DROPS %5d records\n",
              cn, d, k, k - d))
}
cat("    `devDependencies` DROPS 1,656 OF 1,657 AND SAYS NOTHING. The default\n")
cat("    is the lossy one on every column here, because a package-lock is\n")
cat("    mostly packages that have no dev dependencies at all.\n")
cat(sprintf("Q7  1,657 packages, or %d dependency EDGES — and that is question 3's\n",
            nrow(w |> unnest_longer(dependencies, indices_to = "dep"))))
cat("    two answers, the shallow one with holes and the deep one with the\n")
cat("    install path repeated. tidyr produces both and prices neither.\n")

# ── Q8 / Q11 / Q12. ────────────────────────────────────────────────────────
three <- w |> select(path, version, resolved)
cat(sprintf("\nQ8  three named fields -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat("\nQ11 CANNOT. No predicate over values.\n")
cat(sprintf("\nQ12 %d x %d, %d list-columns left. WHAT IS LOST: nothing, and that\n",
            nrow(w), ncol(w), sum(map_lgl(w, is.list))))
cat("    is only because `path` was named by hand. The one call that would\n")
cat("    have kept the keys automatically is the one that raises.\n")

cat("
13. NO for 1, 4, 6 and 7. Question 6 is answered by a refusal, which counts:
    the tool declined to turn 1,657 install paths into columns and said which
    key defeated it.

14. YES. Nothing hard-codes a package name, and the next lock file has the same
    empty-string root key, so the same call raises the same way.

16. ~95 lines, and the rectangling is four of them.
")
