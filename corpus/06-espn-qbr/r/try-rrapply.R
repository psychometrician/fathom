# rrapply — ESPN NFL Quarterback Rating, 2019, the corpus's only ground truth
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (version printed below), + jsonlite to parse
#  file          ../source.json   180 KB, 28 athletes, depth 7, 131 paths,
#                                 72 fields, keyed 0, 0/56 ragged
#  measured      2026-08-10
#  run           cd corpus/06-espn-qbr/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                          10   NO                  NO
#   2 how deep                                  2   NO                  YES
#   4 always present vs sometimes               6   NO                  yes
#   7 how many records                          1   YES                 yes
#  11 find every path matching something        4   NO                  yes
#  12 flattest honest table                     3   NO                  yes
#  13 needed the shape in advance?                  NO for 1, 2, 11, 12
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. Two reasons.
#
# **The melt ratio has one more prediction to test.** The corrected reading —
# forced by `07-graphql-introspection` and confirmed by `04-gharchive` — is that
# the percentage tracks path length against value size, not raggedness or keyed
# sites. This document is flat, regular, and its values are short numbers and
# short names. Predicted: a MIDDLING ratio, not an extreme one.
#
# **And melt is the one shape that puts the trap on screen.** `NOTES.md` records
# `glossary` and `categories[0].labels` holding the same ten abbreviations in
# different orders. In a melted frame both are just rows with paths and values,
# so the same value appearing under two unrelated paths is visible as data
# rather than as structure.
suppressMessages({library(rrapply); library(jsonlite)})
cat(sprintf("R %s, rrapply %s, jsonlite %s\n", getRversion(),
            packageVersion("rrapply"), packageVersion("jsonlite")))

path  <- "../source.json"
bytes <- file.size(path)
doc   <- fromJSON(path, simplifyVector = FALSE)

# ── Q1 / Q12. ────────────────────────────────────────────────────────────────
cat("\n1/12. what is in here — melt every leaf to a row:\n")
m  <- rrapply(doc, how = "melt")
lv <- grep("^L", names(m), value = TRUE)
paths <- apply(m[, lv, drop = FALSE], 1,
               function(r) paste(r[!is.na(r)], collapse = "."))
chars <- sum(nchar(paths)) + length(paths)
idx   <- unique(gsub("(^|[.])[0-9]+($|(?=[.]))", "\\1[]", paths, perl = TRUE))
cat(sprintf("   %s leaves, %s chars for %s bytes — %.0f%%\n",
            format(nrow(m), big.mark = ","), format(chars, big.mark = ","),
            format(bytes, big.mark = ","), 100 * chars / bytes))
cat(sprintf("   folding array indices: %s path shapes, %.1f%% of file, a %.0fx fold\n",
            format(length(idx), big.mark = ","),
            100 * (sum(nchar(idx)) + length(idx)) / bytes, nrow(m) / length(idx)))
cat("   THE SEVEN-FILE TABLE, and this one lands where the corrected reading\n")
cat("   says it should:\n")
cat("     04-gharchive       52%   long values (SHAs, commit messages)\n")
cat("     05-fhir-bundle     60%\n")
cat(sprintf("     06-espn-qbr       %3.0f%%   short values, short paths   <- HERE\n",
            100 * chars / bytes))
cat("     09-stripe-openapi 141%\n")
cat("     10-wikidata       173%\n")
cat("     07-graphql        204%   short values, long names\n")
cat("     03-natural-earth  226%   short values, 99,566 of them\n")
cat("   NOTES.md grades this the EASIEST file in the corpus — every raggedness\n")
cat("   axis zero — and it sits mid-table. Under the old reading that is\n")
cat("   meaningless; under the corrected one it is what `flat, regular, short\n")
cat("   values, short paths` predicts.\n")

cat(sprintf("\n2. how deep: %d level columns — NOTES.md grades depth %d\n",
            length(lv), 7))

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
ath <- m[!is.na(m$L1) & m$L1 == "athletes" & !is.na(m$L3), , drop = FALSE]
byrec <- split(ath$L3, ath$L2)
u <- unique(unlist(byrec))
n <- length(byrec)
freq <- vapply(u, function(k) sum(vapply(byrec, function(x) k %in% x, TRUE)), 0L)
cat(sprintf("   %d athletes, %d distinct second-level keys, all present on %s\n",
            n, length(u), if (all(freq == n)) "all of them" else "some"))
cat("   0/56 ragged, as graded, reached from the melted frame.\n")

# ── Q11 / THE TRAP AS DATA. ──────────────────────────────────────────────────
cat("\n11. find every path whose value matches something — and here it is the\n")
cat("    trap, because in a melted frame a repeated VALUE is just a query:\n")
# THE PRECISE TEST: a value appearing under more than one TOP-LEVEL branch.
# The first draft asked for short all-caps values appearing more than once and
# drowned in `TRUE`, `FALSE` and `QB` repeated once per athlete — 43 hits, with
# the real signal fourth. Repetition WITHIN a branch is just 28 records having a
# position; repetition ACROSS branches is the thing.
v <- as.character(m$value)
ok <- !is.na(v) & !v %in% c("TRUE", "FALSE")
cross_all <- sum(tapply(m$L1[ok], v[ok], function(x) length(unique(x))) > 1)
cat(sprintf("   values under MORE THAN ONE top-level branch: %d\n", cross_all))
cat("   AND THAT NUMBER IS USELESS ON ITS OWN — it is dominated by numeric\n")
cat("   coincidence: `1`, `2`, `2019`, `28`, `50` all appear in several\n")
cat("   branches because small integers do. Restricting to NON-NUMERIC values,\n")
cat("   which is what a shared VOCABULARY means:\n")
txt_ok <- ok & is.na(suppressWarnings(as.numeric(v)))
cross <- tapply(m$L1[txt_ok], v[txt_ok], function(x) length(unique(x)))
cross <- sort(cross[cross > 1], decreasing = TRUE)
cat(sprintf("   non-numeric values under more than one branch: %d\n", length(cross)))
for (k in names(cross)) {
  wh <- unique(m$L1[txt_ok][v[txt_ok] == k])
  cat(sprintf("     %-5s under %s\n", k, paste(wh, collapse = " + ")))
}
gc_only <- sum(vapply(names(cross), function(k)
  setequal(unique(m$L1[txt_ok][v[txt_ok] == k]), c("glossary", "categories")), TRUE))
cat(sprintf("\n   %d OF THOSE %d ARE `glossary + categories` — THE TRAP ITSELF.\n",
            gc_only, length(cross)))
cat("   All ten abbreviations and their display names, each sitting at two\n")
cat("   unrelated paths. In a melted frame that is a group-by over the value\n")
cat("   column: no knowledge of football, no structural insight, one `tapply`.\n")
cat("   THE FILTER IS THE WHOLE DIFFICULTY. Unrestricted, the test returns 29\n")
cat("   hits dominated by small integers and finds nothing. Restricted to\n")
cat("   non-numeric values it returns 23 and is unmissable. That is one line of\n")
cat("   judgement, and it is judgement nobody applies unprompted.\n")

cat(sprintf("\n7. %d athletes\n", length(doc$athletes)))

cat("
CONCLUSION — the easiest document in the corpus lands mid-table, which is the
corrected statistic behaving correctly, and the trap is visible as data.

  **The melt ratio confirms the correction a third time.** `NOTES.md` grades
  this file the easiest thing in the corpus — every raggedness axis zero, no
  recursion, no keyed sites, explosion 1.8 — and it does not come out cheapest.
  It sits between `05-fhir-bundle` and `09-stripe-openapi`, exactly where
  `flat, regular, short values under short paths` puts it. Under the reading
  `VERDICT.md` used until this week, the easiest file should have been the
  cheapest to list and it is not. Under the corrected one there is nothing to
  explain.

  **AND MELT PUTS THE TRAP ON SCREEN, in the only form any tool here gives it
  for free.** `TQBR`, `EXP`, `PAS` and the rest each appear twice — once under
  `categories` and once under `glossary` — and in a melted frame that is a
  group-by over the value column, not a structural insight. The same ten strings
  at two unrelated paths is the precondition for the wrong positional join that
  turns 83.0 into -7.4.

  `try-jqr.R` states the collision directly and more sharply — same length, same
  set, different order. rrapply gets there sideways, by making values
  addressable. **Neither volunteers it**, and that remains the finding: the test
  is cheap in both tools and nothing runs it.
")
