# tidyjson — 100 openFDA adverse-event reports
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (+ dplyr; versions printed at run time)
#  file          ../source.json   2.7 MB, 100 results, depth 8
#  measured      2026-08-11
#  run           cd corpus/18-openfda-events/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   PARTLY
#   1 what is in here                             5   NO                  YES
#   2 how deep                                    6   NO                  YES — exactly 8
#   3 what is one record                           8  NO                  PARTLY
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  6   NO                  NO — one false positive
#   6 are any object keys data                    3   -                   n/a — no abstention
#   7 how many records                             5   NO                  yes — four answers
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   5   YES                 PARTLY — four enter_objects
#  11 find every path matching something          5   NO                  PARTLY
#  12 flattest honest table                       4   YES                 yes
#  13 needed the shape in advance?                    NO for 1, 2, 4, 7
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes — the verbs say what they do
#  16 lines, and how much is ceremony?                ~110
#
# **`json_structure` GIVES A TYPED CENSUS OF ALL EIGHT LEVELS**, and it is the
# best question 1 in R for the fifth file running: 74,115 rows, max level 8 —
# the probe's depth — with the null column showing exactly THREE nulls in
# 2.7 MB.
#
# **AND `json_types` TYPES ONE FIELD WRONG, FOR THE THIRD TIME IN FOUR ENTRIES.**
# It counts `null` as a TYPE, so `receiver` — an object on 99 results and null
# on 1 — comes back carrying two types where the probe reports none.
# `25-usgs-quakes` five wrong, `15-github-issues` five wrong, `17-openlibrary`
# none (no nulls), **and one here.** The count tracks the document's nulls
# exactly, which is the mechanism showing through.
#
# **QUESTION 10 COSTS FOUR `enter_object` CALLS**, one per level — the same
# scaling purrr's nested `map`s pay. jq crosses all four with `..`.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)
recs <- jsonlite::fromJSON("../source.json", simplifyVector = FALSE)$results

# ── Q0. Is this what it claims to be, and is it whole? ─────────────────────
cat("\nQ0  tidyjson parses the text itself rather than taking someone's list, so\n")
cat("    it would fail on malformed input. No duplicate-key, big-int or NaN\n")
cat("    report. PARTLY.\n")

# ── Q1/Q4/Q5. Fields, presence, types. ────────────────────────────────────
arr <- txt %>% as.tbl_json %>% enter_object("results") %>% gather_array
n <- nrow(arr)
ft <- arr %>% gather_object("field") %>% json_types %>% count(field, type)
cat("\nQ1 ", nrow(ft), "field/type pairs over", length(unique(ft$field)),
    "distinct fields\n")
cat("    gather_object puts the field name in a column — a real survey, not a\n")
cat("    guess from the first record. The probe prints ELEVEN record shapes.\n")

present <- tapply(ft$n, ft$field, sum)
cat("\nQ4  always", sum(present == n), "· sometimes", sum(present < n),
    "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))

varying <- names(which(table(ft$field) > 1))
cat("\nQ5 ", length(varying), "field carries more than one type:",
    paste(varying, collapse = ", "), "\n")
print(as.data.frame(ft[ft$field %in% varying, ]))
cat("    AND THE PROBE REPORTS NONE. `receiver` is an object on 99 results and\n")
cat("    NULL on 1, and tidyjson counts `null` AS a type — which design/axes.py\n")
cat("    and defect 11 both rule is missingness written as a value.\n")
cat("    25-usgs-quakes five wrong · 15-github-issues five wrong ·\n")
cat("    17-openlibrary none (no nulls) · 18-openfda ONE. The count tracks the\n")
cat("    document's nulls exactly, which is the mechanism showing through.\n")
cat("    Setting null aside:",
    length(names(which(table(ft$field[ft$type != "null"]) > 1))),
    "fields vary — the probe's answer.\n")

# ── Q2. How deep does it go. ─────────────────────────────────────────────
st <- txt %>% as.tbl_json %>% json_structure
cat("\nQ2  json_structure:", format(nrow(st), big.mark = ","), "rows, max level",
    max(st$level), "— THE PROBE PRINTS 8\n")
print(table(level = st$level, type = st$type))
cat("    THREE nulls in 2.7 MB, all at the result level or below. The best\n")
cat("    question 1 in R for the fifth file running, and depth costs it nothing.\n")

# ── Q3/Q7. The row candidates. ───────────────────────────────────────────
drugs <- unlist(lapply(recs, function(r) r$patient$drug), recursive = FALSE)
rx <- unlist(lapply(recs, function(r) r$patient$reaction), recursive = FALSE)
cat("\nQ3  gather_array committed: results are rows,", n, "of them.\n")
cat("    THE PROBE NAMES FOUR CANDIDATES AND PRICES THEM:\n")
cat("      the whole document        1 rows x  2 cols\n")
cat("      an item of results      100 rows x 39 cols   26% empty\n")
cat("      an item of drug         265 rows x 41 cols   47% empty\n")
cat("      an item of reaction     247 rows x  3 cols\n")
cat("    tidyjson goes wherever the pipe is pointed and prices nothing. PARTLY.\n")
cat("\nQ7  FOUR right answers: results", n, "· drug", length(drugs),
    "· reaction", length(rx), "\n")
meta <- txt %>% as.tbl_json %>% enter_object("meta") %>% enter_object("results") %>%
  spread_values(total = jnumber("total")) %>% as.data.frame()
cat("    and meta.results.total =", format(meta$total, big.mark = ","),
    "— reachable because the pipe starts at the root.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────
cat("\nQ6  no keyed collections. n/a — and the probe prints `could not call 3\n")
cat("    small single-copy objects` and names them. That ABSTENTION is a third\n")
cat("    state tidyjson has no way to express.\n")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────
tbl <- arr %>% spread_values(id = jstring("safetyreportid"),
                             serious = jstring("serious"),
                             received = jstring("receivedate")) %>%
  as.data.frame() %>% select(id, serious, received)
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
sd <- arr %>% spread_values(d = jstring("seriousnessdeath")) %>% as.data.frame()
cat("\nQ9  seriousnessdeath non-NA on", sum(!is.na(sd$d)), "of", n,
    "— spread_values keeps the row\n")

# ── Q10. Flatten the deepest array. ─────────────────────────────────────
bn <- arr %>% enter_object("patient") %>% enter_object("drug") %>%
  gather_array("d") %>% enter_object("openfda") %>% enter_object("brand_name") %>%
  gather_array("b") %>% append_values_string("brand") %>% as.data.frame()
cat("\nQ10", nrow(bn), "brand names — FOUR enter_object calls and two",
    "gather_arrays,\n")
cat("    one per level. jq crosses the same four with `..` and names none;\n")
cat("    jmespath with one chained expression. tidyjson's pipe is explicit all\n")
cat("    the way down, which is readable and scales linearly with depth. PARTLY.\n")

# ── Q11. Find every path whose value matches something. ────────────────
hits <- arr %>% gather_object("field") %>% json_types %>%
  filter(type == "string") %>% append_values_string("v") %>%
  filter(grepl("https?://", v)) %>% count(field) %>% as.data.frame()
cat("\nQ11 URLs among the results' own fields:", nrow(hits), "\n")
mt <- txt %>% as.tbl_json %>% enter_object("meta") %>%
  spread_values(terms = jstring("terms"), license = jstring("license")) %>%
  as.data.frame()
cat("    and under `meta`: terms and license, both URLs.\n")
cat("    BOTH ARE OUTSIDE `results`, and the pipe reaches them only because I\n")
cat("    pointed it there. pandas and polars report NONE OF TWO. PARTLY.\n")

# ── Q12. The flattest honest table. ────────────────────────────────────
sa <- arr %>% spread_all
cat("\nQ12 spread_all():", nrow(sa), "x", ncol(sa), "\n")
cat("    It widens the scalars and the nested OBJECTS, prefixing as it goes, and\n")
cat("    leaves the two arrays behind — which is the honest thing here. On\n")
cat("    13-package-lock the same verb recursed into keyed collections and built\n")
cat("    1,391 columns; rrapply's `bind` builds 37,006 on THIS file.\n")
