# purrr — ESPN NFL Quarterback Rating, 2019, against a published purrr answer
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.json   180 KB, 28 athletes, depth 7, 131 paths,
#                                 72 fields, keyed 0, 0/56 ragged
#  measured      2026-08-10
#  run           cd corpus/06-espn-qbr/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           3   NO                  NO
#   2 how deep                                  2   NO                  yes
#   3 what is one record                        -   -                   CANNOT
#   4 always present vs sometimes               5   NO                  yes
#   7 how many records                          1   YES                 yes
#   8 three named fields to a table             5   YES, all of it      YES
#  12 flattest honest table                     6   YES                 yes
#  13 needed the shape in advance?                  YES for 8 and 12
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE, AND IT IS THE ONE THAT MATTERS FOR PURRR. `README.md` calls
# purrr "the best answer that exists" for deep JSON. **Here that claim meets a
# published purrr answer written by an R educator for a tutorial**, after four
# documented approaches:
#
#     raw_json %>% purrr::pluck("athletes", n, "categories", 1, "totals")
#
# Rule 6 exists because the probe was once benchmarked against tools given one
# attempt each. This is the inverse: an expert's polished solution, unlimited
# attempts, against a frozen probe's single cold run. The bias runs the other way
# for once, and the comparison is worth having because of it.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
ath <- doc$athletes

cat("\n1. what is in here — str() again, and nothing of purrr's own:\n")
for (lv in c(2, 4))
  cat(sprintf("   str(max.level=%d)  %4d lines\n", lv,
              length(capture.output(str(doc, max.level = lv)))))

depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_dbl(x, depth)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion\n", depth(doc)))
cat(sprintf("7. %d athletes\n", length(ath)))
cat("3. CANNOT — purrr proposes no rows. The tutorial's author chose the\n")
cat("   quarterback after four documented attempts; nothing here shortened that.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
ks <- map(ath, names)
cat(sprintf("   %d athletes, %d distinct key-set(s)\n", length(ks),
            length(unique(map_chr(ks, \(x) paste(sort(x), collapse = ","))))))
cat("   NOTES.md grades 0/56 ragged by absence and 0 by null. This is the\n")
cat("   cleanest document in the corpus and purrr has nothing to work around.\n")

# ── Q8. THE PUBLISHED ANSWER, AND THE SAME THING WRITTEN OVER ALL ATHLETES. ──
cat("\n8. three named fields, one row per quarterback:\n")
cat("   THE TUTORIAL'S EXPRESSION, one athlete at a time:\n")
cat("     raw_json %>% pluck(\"athletes\", n, \"categories\", 1, \"totals\")\n")
p1 <- pluck(doc, "athletes", 1, "categories", 1, "totals")
cat(sprintf("     n=1 gives %d values: %s\n", length(p1),
            paste(unlist(p1), collapse = " ")))

tbl <- map_dfr(ath, \(a) data.frame(
  name = a$athlete$displayName,
  team = a$athlete$teamName,
  qbr  = as.numeric(a$categories[[1]]$totals[[1]])))
cat(sprintf("\n   map_dfr over all of them -> %d x %d, and NOT ONE `%%||%%`\n",
            nrow(tbl), ncol(tbl)))
print(utils::head(tbl[order(-tbl$qbr), ], 3))
cat("   PREDICTION 1 CONFIRMED. Three lines, no defaults, no branches. This is\n")
cat("   purrr at its best and the document is why: 0/56 ragged, no nulls, no\n")
cat("   recursion, no keys-as-data. Compare 05-fhir-bundle, where the same\n")
cat("   three lines need a default on every field but two.\n")

# ── Q12. AND THE MAGIC NUMBER. ───────────────────────────────────────────────
cat("\n12. the flattest honest table, and what it hides:\n")
lab <- unlist(doc$categories[[1]]$labels)
wide <- map_dfr(ath, \(a) {
  v <- as.numeric(unlist(a$categories[[1]]$totals))
  as.data.frame(setNames(as.list(v), lab))
})
wide <- cbind(name = tbl$name, wide)
cat(sprintf("   %d x %d, columns named from categories[[1]]$labels\n",
            nrow(wide), ncol(wide)))
print(utils::head(wide[order(-wide$TQBR), 1:5], 3))
cat("   THAT `setNames(..., lab)` IS THE WHOLE FILE'S LESSON. The values are an\n")
cat("   unnamed array of ten; their names live in a DIFFERENT branch of the\n")
cat("   document, single-copy, and purrr has no verb that relates them. I\n")
cat("   supplied the connection by hand, from NOTES.md.\n")
cat("   The tutorial makes the same connection and hides it better: `totals[1]`\n")
cat("   is Total QBR because `labels[1]` is TQBR, and the published code writes\n")
cat("   the 1 and not the reason. A MAGIC NUMBER THAT IS CORRECT.\n")
cat("   And `$.glossary` carries the same ten abbreviations ALPHABETISED, so\n")
cat("   the obvious join is wrong and produces -7.4 where 83.0 belongs. See\n")
cat("   try-jsonlite.R in this directory for that measurement.\n")

cat("
CONCLUSION — the fair fight, and purrr wins the extraction outright.

  `README.md`'s claim survives its sharpest test. On the corpus's cleanest
  document — `0/56` ragged, no nulls, no recursion, no keyed sites — `map_dfr`
  over 28 athletes needs **no `%||%` anywhere**, and three lines produce the
  table a published tutorial spent four documented approaches arriving at. The
  tutorial's `pluck` chain walks one athlete at a time; `map_dfr` does all 28 in
  the same breath. **Nothing this project could build would improve on that.**

  **THE COST IS ENTIRELY IN QUESTION 12, AND IT IS ONE ARGUMENT.** The ten
  numbers in `totals` are unnamed. Their names live in
  `$.categories[0].labels` — a different branch, a single-copy object, aligned
  only by position. `setNames(v, lab)` connects them and I supplied `lab` from
  `NOTES.md`, not from anything purrr said.

  **The tutorial hides the same gap more elegantly and does not close it.**
  `pluck(..., 'totals')` then taking element 1 as Total QBR is correct *because*
  `labels[1]` is `TQBR` — a fact from elsewhere in the document that the
  published code records nowhere. It is a magic number that happens to be right,
  written by someone who checked.

  **And the document supplies a decoy that makes checking non-optional.**
  `$.glossary` holds the same ten abbreviations alphabetised. Joining `totals`
  against it by position is the obvious move, produces no error, gets `PA` right
  by coincidence, and reports the league's best quarterback at **-7.4** instead
  of **83.0**.

  So the fair fight lands where the project claims it should: **purrr is better
  at extracting than anything here would be, and neither purrr nor an expert
  using it has a way to say which of two ten-element arrays names your
  columns.**
")
