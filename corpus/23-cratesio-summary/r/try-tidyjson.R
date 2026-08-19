# tidyjson — crates.io summary
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.json   41 KB, six collections at the root, depth 4
#  measured      2026-08-11
#  run           cd corpus/23-cratesio-summary/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             8   YES                 PARTLY — one level
#   2 how deep                                    1   -                   CANNOT
#   3 what is one record                         10   YES                 four chains, no compare
#   4 always present vs sometimes                 6   NO                  YES — nothing absent
#   5 does any field change type                 14   NO                  THE PREDICTION
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                             3  YES                 three answers
#   8 three named fields to a table                4 YES                 yes
#   9 a field missing from some rows                3 NO                  YES — both halves
#  10 flatten the deepest array                     4 -                   NO ARRAY TO FLATTEN
#  11 find every path matching something            4 YES                 CANNOT
#  12 flattest honest table                         8 NO                  yes
#  13 needed the shape in advance?                    YES — each of the four collections
#                                                     entered by name
#  14 survives the next file unchanged?               Q4/Q5 yes
#  15 readable a week later?                          YES
#  16 lines, and how much is ceremony?                ~105
#
# THE STANDING PREDICTION, AND THIS DOCUMENT TESTS THE REFINED VERSION.
# tidyjson mistypes fields because `json_types()` counts `null` as a type. Entry
# 20 narrowed that to "the fields that are SOMETIMES null and sometimes a
# value", and entry 22 confirmed it one level down.
#
# This document has SIX null-bearing fields and THREE of them are null on ALL
# FORTY crates — `categories`, `keywords`, `versions`. A field that is never
# anything but null has ONE type. SO THE PREDICTION IS THREE, NOT SIX:
# `documentation`, `homepage` and `recent_downloads`.
# ─────────────────────────────────────────────────────────────────────────────

library(tidyjson)
library(dplyr)
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

src <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
CRATE <- c("new_crates", "most_downloaded", "most_recently_downloaded", "just_updated")
cat("\nQ0  tidyjson parses through jsonlite and reports no health. CANNOT.\n")

# ══════════════════════════════════════════════════════════════════════════
# `enter_object(k)` WITH A VARIABLE RETURNS ZERO ROWS AND RAISES NOTHING.
# ══════════════════════════════════════════════════════════════════════════
# This document has four identically-shaped collections, so the natural thing
# to write is a loop over their names. Measured:
#     enter_object("new_crates")   -> 10 rows
#     enter_object(k), k = same    ->  0 rows, NO ERROR
#     enter_object(!!k)            -> 10 rows
# `enter_object` uses non-standard evaluation, so a variable is taken as a
# LITERAL KEY NAME and a key called `k` does not exist. The first draft of this
# file printed 0 crate rows, 0 varying fields and 0 distinct key-sets, and every
# one of those zeros looked like a finding.
# Entry 22 found `distinct()` ERRORING on a tbl_json and entry 20 found it has
# no `json` column. THIS IS THE THIRD: A TIDYJSON TABLE LOOKS LIKE A TIBBLE AND
# IS NOT ONE, and the failure mode differs by verb — error, silence, or a
# silently empty result.
gather_one <- function(k) as_tibble(src %>% enter_object(!!k) %>% gather_array() %>%
  gather_object() %>% json_types()) %>% mutate(.list = k)
g <- bind_rows(lapply(CRATE, gather_one))
cat(sprintf("\nQ1  four chains, one per collection -> %d gathered rows\n", nrow(g)))
cat(sprintf("    %d distinct crate field names\n", n_distinct(g$name)))
cat("    FOUR CHAINS. tidyjson's idiom is naming a path, and this document's\n")
cat("    point is that four differently-named paths hold one shape — so the\n")
cat("    repetition in the DOCUMENT appears as repetition in the SOURCE.\n")
cat("Q2  CANNOT. No depth verb; the probe says 4.\n")

# ── Q3. ─────────────────────────────────────────────────────────────────────
sets <- g %>% group_by(.list) %>% summarise(k = paste(sort(unique(name)), collapse = ","))
cat(sprintf("\nQ3  distinct key-sets across the four: %d\n", n_distinct(sets$k)))
cat("    ONE, and comparing them meant collapsing each to a string in dplyr.\n")
cat("    tidyjson produced the four key lists and has no verb that compares\n")
cat("    two gathers. The probe prints `same shape as $.new_crates[]`.\n")
n <- nrow(g %>% distinct(.list, array.index))
cat(sprintf("Q3  %d crate rows across the four collections\n", n))

# ── Q4/Q5. THE PREDICTION. ──────────────────────────────────────────────────
ty <- g %>% count(name, type)
vary <- ty %>% count(name, name = "k") %>% filter(k > 1)
wn <- ty %>% filter(type == "null") %>% pull(name)
allnull <- ty %>% group_by(name) %>%
  summarise(kinds = n(), nulls = sum(n[type == "null"]), tot = sum(n)) %>%
  filter(nulls == tot)
cat(sprintf("\nQ5  fields with MORE THAN ONE json_type: %d — %s\n",
            nrow(vary), paste(sort(vary$name), collapse = ", ")))
cat(sprintf("Q5  of those, %d include `null`\n", sum(vary$name %in% wn)))
cat(sprintf("Q5  fields that are null on ALL %d crates: %s\n", n,
            paste(sort(allnull$name), collapse = ", ")))
cat("    THE PREDICTION SAID THREE — documentation, homepage, recent_downloads —\n")
cat("    and NOT categories, keywords or versions, because a field that is\n")
cat("    never anything but null has ONE type and cannot be reported as varying.\n")
cat("    Read the numbers. This is the third document to test entry 20's\n")
cat("    refinement and the first where SIX fields bear a null and only THREE\n")
cat("    of them can be mistyped.\n")
miss <- ty %>% group_by(name) %>% summarise(rows = sum(n)) %>% filter(rows < n)
cat(sprintf("\nQ4  fields on fewer than all %d crates: %d — nothing is ever absent\n",
            n, nrow(miss)))
cat("    `gather_object` counts PRESENCE, so tidyjson has both halves here and\n")
cat("    the document gives it nothing to get wrong.\n")

cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")
tot <- src %>% spread_values(nc = jnumber("num_crates"), nd = jnumber("num_downloads"))
cat(sprintf("\nQ7  num_crates %s, num_downloads %s, %d crate rows\n",
            format(tot$nc, big.mark = ","), format(tot$nd, big.mark = ","), n))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8 <- src %>% enter_object("new_crates") %>% gather_array() %>%
  spread_values(name = jstring("name"), version = jstring("max_version"),
                downloads = jnumber("downloads"))
cat(sprintf("\nQ8  spread_values -> %d x %d\n", nrow(t8), ncol(t8)))
hp <- g %>% filter(name == "homepage")
cat(sprintf("\nQ9  `homepage` emits %d gathered rows of %d crates, %d typed `null`\n",
            nrow(hp), n, sum(hp$type == "null")))
cat("    PRESENCE and NULL reported separately — both halves, which is what\n")
cat("    `gather_object` plus `json_types` buys and what a frame cannot do.\n")
cat("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is an object of six\n")
cat("    fields; question 10 has no target on this document.\n")
lk <- src %>% enter_object("new_crates") %>% gather_array() %>%
  enter_object("links") %>% gather_object()
cat(sprintf("    entering `links` instead: %d rows, %d distinct keys\n",
            nrow(lk), n_distinct(lk$name)))
cat("\nQ11 CANNOT enumerate paths — no recursive descent, and every one of the\n")
cat("    four collections would have to be entered by name anyway.\n")
u <- src %>% enter_object("new_crates") %>% gather_array() %>%
  spread_values(r = jstring("repository"))
cat(sprintf("    a NAMED path: `repository` matches ^https?:// on %d of %d\n",
            sum(grepl("^https?://", u$r)), nrow(u)))
sa <- src %>% enter_object("new_crates") %>% gather_array() %>% spread_all()
at <- vapply(sa, is.atomic, logical(1))
cat(sprintf("\nQ12 spread_all on ONE collection -> %d x %d, %.1f%% NA over %d atomic cols\n",
            nrow(sa), ncol(sa), 100 * mean(is.na(as.matrix(sa[, at]))), sum(at)))
cat("    and it must be run four times. Compare pandas' four frames of 10 x 28\n")
cat("    and polars' four of 10 x 23 — the repetition is the document's, and\n")
cat("    every tool in this directory pays it in source lines.\n")
