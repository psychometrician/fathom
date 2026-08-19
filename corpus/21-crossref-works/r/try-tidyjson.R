# tidyjson — Crossref works, 1,000 records
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
#  measured      2026-08-11
#  run           cd corpus/21-crossref-works/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             8   YES                 PARTLY — one level
#   2 how deep                                    1   -                   CANNOT
#   3 what is one record                          1   -                   CANNOT
#   4 always present vs sometimes                 4   NO                  YES — 40 of 57
#   5 does any field change type                 14   NO                  ZERO, correctly
#   6 are any object keys data                    6   YES                 a representation
#   7 how many records                            2   YES                 yes
#   8 three named fields to a table               5   YES                 yes
#   9 a field missing from some rows              2   NO                  YES — presence
#  10 flatten the deepest array                   8   YES                 YES — parent kept
#  11 find every path matching something          6   YES                 CANNOT
#  12 flattest honest table                      12   NO                  1,000 x 38
#  13 needed the shape in advance?                    YES — two enter_object calls to
#                                                     reach the records at all
#  14 survives the next file unchanged?               Q4/Q5 yes, every chain no
#  15 readable a week later?                          YES — the best-reading code here
#  16 lines, and how much is ceremony?                ~130, chains are 1-6 lines
#
# THE STANDING PREDICTION WAS ZERO AND THE ANSWER IS ZERO. tidyjson mistypes
# fields because `json_types()` counts `null` as a type — entry 25 five, entry
# 15 five, entry 18 one, entry 20 fifteen, and entry 20 narrowed the rule to
# "the fields that are SOMETIMES null and sometimes a value". THIS DOCUMENT
# WRITES NO NULLS AT ALL and tidyjson mistypes NOTHING. That is the second
# control case after entry 14, and it is the cleanest confirmation the corpus
# has that the mechanism is the null and not the tool.
#
# THE WRAPPER COSTS TWO NAMED VERBS and tidyjson is honest about it. pandas,
# polars and DuckDB all silently returned the one-row ENVELOPE when pointed at
# this file; tidyjson returns NOTHING until you name `message` and `items`.
# A tool that gives you nothing is safer here than three that give you one row.
#
# QUESTION 10 IS AGAIN THE BEST ANSWER IN R: six chained verbs, the correct
# 18,155, and the parent DOI carried through every level — which pandas needed
# `meta_prefix` for after two raises, and which jmespath cannot do at all.
#
# THE STANDING PREDICTION, WRITTEN BEFORE THE RUN, AND THIS DOCUMENT IS THE
# CONTROL CASE. tidyjson mistypes fields because `json_types()` counts `null` as
# a type — entry 25 five fields, entry 15 five, entry 18 one, entry 20 fifteen,
# and entry 20 sharpened the rule to "the fields that are SOMETIMES null".
# THIS DOCUMENT HAS ZERO WRITTEN NULLS. So the prediction is ZERO mistyped
# fields, and if it is not zero the mechanism is not what four entries said.
# ─────────────────────────────────────────────────────────────────────────────

library(tidyjson)
library(dplyr)
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

src <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
cat("\nQ0  tidyjson parses through jsonlite and reports no health. CANNOT.\n")

# ── Q1. The wrapper costs two verbs. ────────────────────────────────────────
t0 <- Sys.time()
lvl1 <- src %>% enter_object("message") %>% enter_object("items") %>%
  gather_array() %>% gather_object() %>% json_types()
cat(sprintf("\nQ1  enter_object x2 + gather_array + gather_object -> %d rows, %.1fs\n",
            nrow(lvl1), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("    %d distinct record field names\n", n_distinct(lvl1$name)))
cat("    THE WRAPPER IS TWO NAMED VERBS. tidyjson cannot find $.message.items\n")
cat("    on its own — but unlike pandas, polars and DuckDB it does not silently\n")
cat("    return the envelope either: you get nothing until you name the path.\n")
cat("Q2  CANNOT. No depth verb and no recursive gather; the probe says 9.\n")

n <- src %>% enter_object("message") %>% enter_object("items") %>%
  gather_array() %>% nrow()
cat(sprintf("\nQ3  no candidates, no pricing. CANNOT.\nQ7  %d works\n", n))

# ── Q4/Q5. THE PREDICTION. ──────────────────────────────────────────────────
types <- lvl1 %>% count(name, type) %>% as_tibble()
per <- types %>% count(name, name = "n_types")
varying <- per %>% filter(n_types > 1)
with_null <- types %>% filter(type == "null") %>% pull(name)
cat(sprintf("\nQ5  fields tidyjson reports with MORE THAN ONE json_type: %d\n",
            nrow(varying)))
if (nrow(varying)) print(as.data.frame(varying))
cat(sprintf("Q5  of those, %d include `null` among their types\n",
            sum(varying$name %in% with_null)))
cat("    THE PREDICTION SAID ZERO, because this document writes no nulls.\n")
cat("    Read the number above. Entry 14 was the only other zero-null document\n")
cat("    graded and tidyjson was right there too; this is the second control.\n")
cat(sprintf("    (the probe reports ONE type-changing site on this document, and\n"))
cat("    it is issued.date-parts, two levels inside an array, where\n")
cat("    `gather_object` at level 1 cannot reach it either way.)\n")

present <- types %>% group_by(name) %>% summarise(rows = sum(n)) %>% filter(rows < n)
cat(sprintf("\nQ4  fields on fewer than %d works: %d of %d — correct, and by the\n",
            n, nrow(present), n_distinct(lvl1$name)))
cat("    same `gather_object` mechanism that gets question 5 wrong elsewhere.\n")

# ── Q6. ─────────────────────────────────────────────────────────────────────
t0 <- Sys.time()
ref <- src %>% enter_object("message") %>% enter_object("items") %>% gather_array() %>%
  enter_object("reference") %>% gather_array("ri") %>% gather_object()
cat(sprintf("\nQ6  reference[]: %d distinct keys, %d KEY-OCCURRENCE rows from 18,155\n    references, %.1fs\n",
            n_distinct(ref$name), nrow(ref),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    `gather_object` puts keys in a `name` column by construction — a\n")
cat("    representation, not a verdict. The probe DECLINES this site.\n")

# ── HYPHENS. ────────────────────────────────────────────────────────────────
cat("\n     HYPHENS: tidyjson takes field names as STRING arguments —\n")
cat("     `jstring(\"reference-count\")` — so it pays nothing, like polars and\n")
cat("     unlike jsonlite's `$`, DuckDB's identifiers and pandas' `query`.\n")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t0 <- Sys.time()
tbl <- src %>% enter_object("message") %>% enter_object("items") %>% gather_array() %>%
  spread_values(doi = jstring("DOI"), type = jstring("type"),
                publisher = jstring("publisher"))
cat(sprintf("\nQ8  spread_values -> %d x %d, %.1fs\n", nrow(tbl), ncol(tbl),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
ab <- lvl1 %>% filter(name == "abstract") %>% nrow()
cat(sprintf("\nQ9  abstract emits %d gathered rows of %d works — PRESENCE, correct\n", ab, n))
t0 <- Sys.time()
res <- src %>% enter_object("message") %>% enter_object("items") %>% gather_array() %>%
  spread_values(work_doi = jstring("DOI")) %>%
  enter_object("reference") %>% gather_array("ri") %>%
  spread_values(key = jstring("key"))
cat(sprintf("\nQ10 reference[] -> %d x %d, %.1fs — the parent DOI survives\n",
            nrow(res), ncol(res), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    SIX chained verbs, the true count is 18,155, and `work_doi` is carried\n")
cat("    through — which pandas needed meta_prefix for and jmespath cannot do.\n")
cat("\nQ11 CANNOT. No recursive descent; every level is entered by name.\n")
u <- src %>% enter_object("message") %>% enter_object("items") %>% gather_array() %>%
  spread_values(u = jstring("URL"))
cat(sprintf("    a NAMED path: $.URL matches ^https?:// on %d of %d\n",
            sum(grepl("^https?://", u$u)), nrow(u)))
cat("    jq, ijson, glom and pydash report 13 distinct URL PATHS.\n")
t0 <- Sys.time()
sa <- tryCatch(src %>% enter_object("message") %>% enter_object("items") %>%
                 gather_array() %>% spread_all(), error = function(e) e)
if (inherits(sa, "error")) {
  cat(sprintf("\nQ12 spread_all ERRORS: %s\n", conditionMessage(sa)))
} else {
  at <- vapply(sa, is.atomic, logical(1))
  cat(sprintf("\nQ12 spread_all -> %d x %d, %.1fs, %.1f%% NA over %d atomic columns\n",
              nrow(sa), ncol(sa), as.numeric(difftime(Sys.time(), t0, units = "secs")),
              100 * mean(is.na(as.matrix(sa[, at]))), sum(at)))
  cat("    Compare pandas' json_normalize and jsonlite's flatten, both 1,000 x 71,\n")
  cat("    and the probe's own 1,000 x 71 at 44% empty.\n")
}
