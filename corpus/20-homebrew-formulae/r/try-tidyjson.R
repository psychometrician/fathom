# tidyjson — Homebrew's whole formula index
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
#  measured      2026-08-11
#  run           cd corpus/20-homebrew-formulae/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             7   NO                  PARTLY — one level
#   2 how deep                                    3   -                   CANNOT
#   3 what is one record                          2   -                   CANNOT
#   4 always present vs sometimes                 7   NO                  YES for absent
#   5 does any field change type                 22   NO                  NO — 15 false positives
#   6 are any object keys data                    9   YES                 a representation
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               5   YES                 yes
#   9 a field missing from some rows              13  YES                 yes, not by the obvious route
#  10 flatten the deepest array                   8   YES                 YES — 557, parent kept
#  11 find every path matching something          7   YES                 CANNOT
#  12 flattest honest table                      14   NO                  yes — 223 cols, 77.8% NA
#  13 needed the shape in advance?                    YES for 6, 10, 11, and for 1 past
#                                                     level one
#  14 survives the next file unchanged?               Q4/Q5 yes, every chain no
#  15 readable a week later?                          YES — the best-reading code here
#  16 lines, and how much is ceremony?                ~150, the chains are 1-6 lines each
#  timing        gather 0.9s, Q6 chain 1.5s, Q10 chain 1.6s, spread_all 22.3s
#
# THE STANDING PREDICTION WAS 17 AND THE ANSWER IS 15, AND THE MISS IS THE
# USEFUL PART. Across four documents tidyjson has typed exactly the
# NULL-BEARING FIELD COUNT wrongly, from one cause: `json_types()` counts
# `null` as a type. This document has 17 always-present-but-null fields, so 17
# was predicted. Measured: 15 — and the two missing are `linked_keg` and
# `disable_replacement_cask`, which are null on EVERY record and therefore have
# exactly ONE type. THE RULE IS NARROWER THAN FOUR DOCUMENTS COULD SHOW:
# tidyjson mistypes the fields that are SOMETIMES null and sometimes a value.
# On entries 25, 15 and 18 those two sets were the same size; this one
# separates them. Mechanism unchanged, predicting count corrected.
#
# ALL 15 ARE FALSE POSITIVES AND THERE ARE ZERO TRUE ONES: not one field varies
# without null in the mix, and the probe reports no root type change either.
#
# QUESTION 10 IS THE BEST ANSWER IN R. Six chained verbs reach
# patches[].resolves[], return the correct 557, and carry the formula NAME
# through all six — which pandas could not do without a python loop and
# jmespath could not do at all.
#
# A tbl_json HAS NO `json` COLUMN. The JSON lives in an attribute, so dplyr
# verbs cannot see it; the first draft of question 9 died on
# `object 'json' not found`.
# ─────────────────────────────────────────────────────────────────────────────

library(tidyjson)
library(dplyr)
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

RAW <- "../source.json"
src <- paste(readLines(RAW, warn = FALSE), collapse = "\n")

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  tidyjson parses through jsonlite and reports nothing about health.\n")
cat("    No duplicate-key report, no big-int report. CANNOT.\n")

# ── Q1. What is in here — gather_object is one level. ────────────────────────
t0 <- Sys.time()
lvl1 <- src %>% gather_array() %>% gather_object() %>% json_types()
t_g <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\nQ1  gather_array + gather_object -> %d rows in %.1fs\n", nrow(lvl1), t_g))
cat(sprintf("    %d distinct root field names\n", n_distinct(lvl1$name)))
cat("    ONE LEVEL. `gather_object` descends exactly one, so 'the fields at\n")
cat("    every level' means chaining one call per level — and this document is\n")
cat("    8 deep with keyed collections in the middle, so the chain cannot be\n")
cat("    written without knowing the platform names.\n")

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
cat("\nQ2  CANNOT. There is no depth verb and no recursive gather. You confirm a\n")
cat("    depth you already know, one `enter_object` at a time — entry 18 counted\n")
cat("    four of them to reach one field.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
n <- src %>% gather_array() %>% nrow()
cat(sprintf("\nQ3  tidyjson names no candidates and prices none. CANNOT.\n"))
cat(sprintf("Q7  %d formulae\n", n))

# ── Q4/Q5. THE STANDING PREDICTION. ──────────────────────────────────────────
types <- lvl1 %>% count(name, type) %>% as_tibble()
per_field <- types %>% count(name, name = "n_types")
varying <- per_field %>% filter(n_types > 1)
cat(sprintf("\nQ5  fields tidyjson reports with MORE THAN ONE json_type: %d\n",
            nrow(varying)))
print(as.data.frame(varying), max = 200)

with_null <- types %>% filter(type == "null") %>% pull(name)
false_pos <- varying %>% filter(name %in% with_null)
cat(sprintf("\n     OF THOSE %d, %d INCLUDE `null` AS ONE OF THEIR TYPES.\n",
            nrow(varying), nrow(false_pos)))
cat("     `design/axes.py` and defect 11 both say a null is not a type, and the\n")
cat("     probe reports NO type change at the root of this document at all.\n")
real <- varying %>% filter(!name %in% with_null)
cat(sprintf("     fields varying WITHOUT null in the mix: %d\n", nrow(real)))

# THE PREDICTION SAID 17 AND THE ANSWER IS 15, AND THE GAP IS THE USEFUL PART.
allnull <- types %>% group_by(name) %>%
  summarise(kinds = n(), has_null = any(type == "null")) %>%
  filter(has_null, kinds == 1)
cat(sprintf("\n     THE PREDICTION SAID 17 AND THIS SAYS %d. The %d missing are the\n",
            nrow(varying), 17 - nrow(varying)))
cat(sprintf("     fields that are null on EVERY record: %s\n",
            paste(allnull$name, collapse = ", ")))
cat("     They have exactly ONE type — null — so they cannot be reported as\n")
cat("     varying. THE RULE IS SHARPER THAN FOUR DOCUMENTS COULD SHOW IT:\n")
cat("     tidyjson mistypes the fields that are SOMETIMES null and sometimes a\n")
cat("     value, not every field that bears a null. On entries 25, 15 and 18\n")
cat("     those two sets were the same size and this document separates them.\n")
cat("     The mechanism is unchanged; the count that predicts it is not.\n")

# ── Q4 proper. ───────────────────────────────────────────────────────────────
present <- types %>% group_by(name) %>% summarise(rows = sum(n)) %>%
  filter(rows < n)
cat(sprintf("\nQ4  fields whose gathered rows number fewer than %d: %d — %s\n", n,
            nrow(present), paste(present$name, collapse = ", ")))
cat("    CORRECT for the absent half. `gather_object` emits a row per KEY, so a\n")
cat("    key written null still emits one — tidyjson is a walker here, and the\n")
cat("    same mechanism that gets question 4 right is the one that gets\n")
cat("    question 5 wrong.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
t0 <- Sys.time()
plat <- src %>% gather_array() %>% enter_object("bottle") %>%
  enter_object("stable") %>% enter_object("files") %>% gather_object()
cat(sprintf("\nQ6  four chained calls to reach bottle.stable.files: %d rows, %.1fs\n",
            nrow(plat), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("    %d distinct keys — %s …\n", n_distinct(plat$name),
            paste(head(sort(unique(plat$name)), 5), collapse = ", ")))
cat("    `gather_object` treats keys as DATA by construction — it puts them in\n")
cat("    a `name` column — which is the right representation and is applied\n")
cat("    uniformly to real field names too. Like rrapply's melt: a\n")
cat("    representation, not a verdict.\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t0 <- Sys.time()
tbl <- src %>% gather_array() %>%
  spread_values(name = jstring("name"), desc = jstring("desc"),
                homepage = jstring("homepage"))
cat(sprintf("\nQ8  spread_values -> %d rows x %d, %.1fs\n", nrow(tbl), ncol(tbl),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
print(head(as.data.frame(tbl)[, c("name", "desc")], 2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
# FIRST DRAFT REACHED FOR A `json` COLUMN AND THERE ISN'T ONE:
#   Error: object 'json' not found
# A `tbl_json` keeps the JSON in an ATTRIBUTE, not a column, so dplyr verbs
# cannot see it. The gathered key table from Q1 is the way in.
ex_rows <- lvl1 %>% filter(name == "executables") %>% nrow()
cat(sprintf("\nQ9  executables emits %d gathered rows of %d formulae — so it is\n",
            ex_rows, n))
cat(sprintf("    PRESENT on %d and absent on %d. `gather_object` counts presence,\n",
            ex_rows, n - ex_rows))
cat("    which is the right answer and is NOT how you would reach for it:\n")
cat("    `spread_values(jstring('executables'))` returns NA for an absent key\n")
cat("    and NA for an array-valued present one, so the obvious route conflates\n")
cat("    them. Note also that a tbl_json has no `json` COLUMN — the JSON lives\n")
cat("    in an attribute, so dplyr cannot reach it and the first draft of this\n")
cat("    section died with `object 'json' not found`.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
t0 <- Sys.time()
res <- src %>% gather_array() %>% spread_values(nm = jstring("name")) %>%
  enter_object("patches") %>% gather_array("pi") %>%
  enter_object("resolves") %>% gather_array("ri") %>%
  spread_values(id = jstring("id"), rtype = jstring("type"))
cat(sprintf("\nQ10 patches[].resolves[] -> %d rows x %d, %.1fs\n", nrow(res), ncol(res),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    SIX chained verbs, and `nm` survives all of them — the parent is kept,\n")
cat("    which pandas could not do and jmespath could not do. The true count is\n")
cat("    557. tidyjson's chain is the most readable correct answer to Q10 in R.\n")

# ── Q11. Find every path whose value matches something. ──────────────────────
cat("\nQ11 CANNOT in the sense the question means. tidyjson has no recursive\n")
cat("    descent and no path enumeration; every level must be entered by name.\n")
hp <- src %>% gather_array() %>% spread_values(h = jstring("homepage"))
cat(sprintf("    a NAMED path works: homepage is http-prefixed on %d of %d,\n",
            sum(startsWith(hp$h, "http"), na.rm = TRUE), nrow(hp)))
cat(sprintf("    ^https?:// on %d\n", sum(grepl("^https?://", hp$h))))
cat("    Against 65 and 48 distinct PATHS from the seven tools that can walk.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12 `spread_all` is the verb. Entry 13 recorded it returning 1,391 COLUMNS\n")
cat("    on a document with keys-as-data, which is the failure this question\n")
cat("    exists to find. Run here with a timer:\n")
t0 <- Sys.time()
sa <- tryCatch(src %>% gather_array() %>% spread_all(), error = function(e) e)
if (inherits(sa, "error")) {
  cat(sprintf("    spread_all ERRORS: %s\n", conditionMessage(sa)))
} else {
  cat(sprintf("    spread_all -> %d rows x %d cols, %.1fs\n", nrow(sa), ncol(sa),
              as.numeric(difftime(Sys.time(), t0, units = "secs"))))
  atomic <- vapply(sa, is.atomic, logical(1))
  na_frac <- mean(is.na(as.matrix(sa[, atomic])))
  cat(sprintf("    %.1f%% NA over %d atomic columns\n", 100 * na_frac, sum(atomic)))
  cat("    Compare pandas' json_normalize at 8,536 x 447 and 85% NA, jsonlite's\n")
  cat("    flatten at 440, and rrapply's bind at 3,415. Four libraries, four\n")
  cat("    widths, one document, and none of them warns.\n")
}
