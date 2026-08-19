# tidyjson — 100 GitHub issues from one repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (+ dplyr; versions printed at run time)
#  file          ../source.json   686 KB, 100 issues, depth 4
#  measured      2026-08-11
#  run           cd corpus/15-github-issues/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   PARTLY
#   1 what is in here                             5   NO                  YES
#   2 how deep                                    6   NO                  YES — exactly 4
#   3 what is one record                          3   YES                 PARTLY
#   4 always present vs sometimes                10   NO                  YES — null is a TYPE
#   5 does any field change type                  8   NO                  NO — 5 false positives
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          4   NO                  PARTLY
#  12 flattest honest table                       5   YES                 yes
#  13 needed the shape in advance?                    NO for 1, 2, 4, 7
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes — the verbs say what they do
#  16 lines, and how much is ceremony?                ~115
#
# **`json_types` HAS A `null` TYPE, AND THAT IS BOTH ITS BEST AND ITS WORST
# FEATURE ON THIS DOCUMENT.**
#
# **Best:** counting `type == "null"` per field gives the null half of question 4
# directly and exactly — 9 fields, with counts `type` 100, `active_lock_reason`
# 100, `state_reason` 98, `assignee` 96, `milestone` 95, `closed_by` 52,
# `closed_at` 52, `pinned_comment` 16. No other R tool states it as a type.
#
# **Worst:** it therefore reports **5 fields as carrying more than one type** —
# `assignee`, `closed_at`, `closed_by`, `milestone`, `state_reason` — and **the
# probe reports NO field that changes type on this document.** Those five are
# null on some issues and a value on others, which `design/axes.py` and defect 11
# both rule is *missingness written as a value*, not polymorphism.
#
# > **`FINDINGS.md` records tidyjson typing FIVE fields wrong on
# > `25-usgs-quakes`, for exactly this reason. It is five again here, on a
# > different document, from the same cause.** The count matching is a
# > coincidence; the mechanism repeating is not.
#
# **`json_structure` IS AGAIN THE BEST QUESTION 1 IN R.** 9,420 rows, max level
# 4 — the probe's depth — and the level table shows **709 nulls at level 2**,
# which is the record-level null count exactly, plus 98 deeper. ijson reads 807
# null events off the byte stream and tidyjson gets the same number from a frame.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)

# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
cat("\nQ0  tidyjson parses the text itself rather than taking someone's list, so\n")
cat("    it would fail on malformed input. No duplicate-key, big-int or NaN\n")
cat("    report. PARTLY.\n")

# ── Q1/Q4/Q5. Fields, presence, and types. ──────────────────────────────────
arr <- txt %>% as.tbl_json %>% gather_array
n <- nrow(arr)
ft <- arr %>% gather_object("field") %>% json_types %>% count(field, type)
cat("\nQ1 ", nrow(ft), "field/type pairs over", length(unique(ft$field)), "distinct fields\n")
cat("    gather_object puts the field name in a column, so this is a real survey\n")
cat("    rather than a guess from the first record.\n")

present <- tapply(ft$n, ft$field, sum)
absent <- sort(names(present)[present < n])
nulls <- ft[ft$type == "null", ]
nullish <- sort(nulls$field[present[nulls$field] == n])
cat("\nQ4  from `count(field, type)`:\n")
cat("      sometimes ABSENT (", length(absent), "):", absent, "\n")
cat("      present but NULL (", length(nullish), "):", nullish, "\n")
cat("      exact null counts:\n")
print(as.data.frame(nulls[order(-nulls$n), c("field", "n")]), row.names = FALSE)
cat("    `null` IS A TYPE HERE, so the null half is stated directly. pandas,\n")
cat("    polars, DuckDB and simplified jsonlite each report a single 13.\n")

varying <- names(which(table(ft$field) > 1))
cat("\nQ5 ", length(varying), "fields carry more than one type:",
    paste(varying, collapse = ", "), "\n")
cat("    AND THE PROBE REPORTS NONE. All five are null on some issues and a\n")
cat("    value on others, which design/axes.py and defect 11 both rule is\n")
cat("    MISSINGNESS WRITTEN AS A VALUE, not polymorphism.\n")
cat("    FINDINGS.md records tidyjson typing five fields wrong on 25-usgs-quakes\n")
cat("    from the same cause. Five again here, on a different document.\n")
cat("    Setting null aside:",
    length(names(which(table(ft$field[ft$type != "null"]) > 1))),
    "fields vary — which is the probe's answer.\n")

# ── Q2. How deep does it go — json_structure. ───────────────────────────────
st <- txt %>% as.tbl_json %>% json_structure
cat("\nQ2  json_structure:", format(nrow(st), big.mark = ","), "rows, max level",
    max(st$level), "— the probe prints 4\n")
print(table(level = st$level, type = st$type))
cat("    709 nulls at level 2 is the record-level null count EXACTLY, and 807\n")
cat("    in total — the same number ijson reads off the byte stream as events.\n")

# ── Q3/Q7. What is one record, and how many. ────────────────────────────────
cat("\nQ3  gather_array committed: array elements are rows,", n, "of them. It\n")
cat("    names no alternative and prices nothing; the probe names three. PARTLY.\n")
cat("Q7 ", n, "issues\n")

# ── Q6. Are any object keys actually data? ──────────────────────────────────
cat("\nQ6  no keyed collections — GitHub ships fixed field names. n/a\n")

# ── Q8/Q9. Extraction. ──────────────────────────────────────────────────────
tbl <- arr %>% spread_values(number = jnumber("number"),
                             state  = jstring("state")) %>%
  enter_object("user") %>% spread_values(user = jstring("login")) %>%
  as.data.frame() %>% select(number, state, user)
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cb <- arr %>% spread_values(number = jnumber("number")) %>%
  enter_object("closed_by") %>% spread_values(login = jstring("login")) %>%
  as.data.frame()
cat("\nQ9  closed_by present on", nrow(cb), "of", n, "issues\n")
cat("    `enter_object` DROPS the 52 issues where closed_by is null, silently —\n")
cat("    the same row-dropping jmespath's projection does. spread_values on the\n")
cat("    top level would have kept them.\n")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────────
lab <- arr %>% spread_values(number = jnumber("number")) %>%
  enter_object("labels") %>% gather_array("i") %>%
  spread_values(name = jstring("name")) %>% as.data.frame()
cat("\nQ10", nrow(lab), "label rows over", length(unique(lab$number)), "issues\n")
cat("    the 40 issues with an empty label list contribute none.\n")

# ── Q11. Find every path whose value matches something. ─────────────────────
hits <- arr %>% gather_object("field") %>% json_types %>%
  filter(type == "string") %>% append_values_string("v") %>%
  filter(grepl("https?://", v)) %>% count(field) %>% as.data.frame()
cat("\nQ11", nrow(hits), "top-level string fields hold a URL,", sum(hits$n), "values\n")
cat("    The truth is 77 paths and 3,297 values. The pipe names the LEVEL, so\n")
cat("    `user.avatar_url` and `labels[].url` need their own pipes. PARTLY.\n")

# ── Q12. The flattest honest table, and what was lost. ──────────────────────
sa <- arr %>% spread_all
cat("\nQ12 spread_all():", nrow(sa), "x", ncol(sa), "\n")
cat("    AND IT PREFIXES —", paste(head(grep("login", names(sa), value = TRUE), 2),
                                   collapse = ", "), "\n")
cat("    duplicate names:", if (anyDuplicated(names(sa))) "yes" else "NONE", "\n")
cat("    polars' `unnest` RAISES on this document and DuckDB's `struct.*`\n")
cat("    silently returns 19 duplicate names. tidyjson, rrapply, jsonlite and\n")
cat("    pandas all prefix. On 13-package-lock spread_all built a 1,391-column\n")
cat("    monster; here the same verb is the right answer, because these keys\n")
cat("    are field names rather than data.\n")
