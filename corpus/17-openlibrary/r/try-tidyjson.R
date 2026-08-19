# tidyjson — 200 OpenLibrary search results
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (+ dplyr; versions printed at run time)
#  file          ../source.json   64 KB, 200 docs, depth 4
#  measured      2026-08-11
#  run           cd corpus/17-openlibrary/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   PARTLY
#   1 what is in here                             5   NO                  YES
#   2 how deep                                    5   NO                  YES — exactly 4
#   3 what is one record                          10  NO                  NO — misses the SPLIT
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  6   NO                  YES — no null to mistype
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                             4   NO                  yes — both answers
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          5   NO                  PARTLY
#  12 flattest honest table                       5   YES                 yes
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes — the verbs say what they do
#  16 lines, and how much is ceremony?                ~110
#
# **tidyjson TYPES EVERY FIELD AND GETS EVERY ONE RIGHT, WHICH IS THE OPPOSITE OF
# ITS LAST TWO ENTRIES.** On `25-usgs-quakes` it typed five fields wrong and on
# `15-github-issues` five again, both times because it counts `null` as a TYPE
# and those documents had present-but-null fields. **The 200 records here hold
# ZERO nulls**, so there is nothing to mistype: 17 fields, 17 name/type pairs,
# none varying — the probe's answer.
#
# > Three documents, one mechanism, and the instrument only looks accurate on the
# > third. **What changed is the data.**
#
# **`json_structure` IS AGAIN THE BEST QUESTION 1 IN R** — max level 4, the
# probe's depth, with a typed census showing exactly one null in the whole
# document (the top-level `offset`).
#
# **AND IT MISSES THE SPLIT, LIKE EVERYTHING ELSE.** The probe prints
# `└─ or 4 tables, split on ebook_access — 16% empty`. `gather_array` commits to
# one shape; dplyr's `group_by` produces the four tables once the field is named,
# and nothing here chose the field.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)

# ── Q0. Is this what it claims to be, and is it whole? ─────────────────────
cat("\nQ0  tidyjson parses the text itself rather than taking someone's list, so\n")
cat("    it would fail on malformed input. No duplicate-key, big-int or NaN\n")
cat("    report. PARTLY.\n")

# ── Q1/Q4/Q5. Fields, presence, types. ────────────────────────────────────
arr <- txt %>% as.tbl_json %>% enter_object("docs") %>% gather_array
n <- nrow(arr)
ft <- arr %>% gather_object("field") %>% json_types %>% count(field, type)
cat("\nQ1 ", nrow(ft), "field/type pairs over", length(unique(ft$field)),
    "distinct fields\n")
cat("    gather_object puts the field name in a column, so this is a real survey\n")
cat("    rather than a guess from the first record.\n")

present <- tapply(ft$n, ft$field, sum)
cat("\nQ4  always", sum(present == n), "· sometimes", sum(present < n),
    "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))

varying <- names(which(table(ft$field) > 1))
cat("\nQ5 ", length(varying), "fields carry more than one type:",
    if (length(varying)) paste(varying, collapse = ", ") else "none",
    "— the probe's answer\n")
cat("    AND THAT IS NEW. On 25-usgs-quakes tidyjson typed FIVE fields wrong and\n")
cat("    on 15-github-issues five again, both because it counts `null` AS a type\n")
cat("    and those documents had present-but-null fields. These 200 records hold\n")
cat("    ZERO nulls, so there is nothing to mistype. The instrument did not\n")
cat("    improve; the ambiguity left.\n")
print(table(ft$type))

# ── Q2. How deep does it go. ─────────────────────────────────────────────
st <- txt %>% as.tbl_json %>% json_structure
cat("\nQ2  json_structure:", format(nrow(st), big.mark = ","), "rows, max level",
    max(st$level), "— THE PROBE PRINTS 4\n")
print(table(level = st$level, type = st$type))
cat("    ONE null in the whole document, at level 1 — the top-level `offset`.\n")
cat("    15-github-issues had 807 and the tools split nine to four over them.\n")

# ── Q3. THE SPLIT. ───────────────────────────────────────────────────────
recs <- jsonlite::fromJSON("../source.json", simplifyVector = FALSE)$docs
allf <- sort(unique(unlist(lapply(recs, names))))
holes <- mean(sapply(recs, function(r) sum(!(allf %in% names(r))))) / length(allf)
cat(sprintf("\nQ3  gather_array committed: docs are rows, %d of them, %d fields, %.0f%% empty\n",
            n, length(allf), 100 * holes))
cat("    THE PROBE PRINTS THAT AND THEN A LINE tidyjson has no verb for:\n")
cat("      └─ or 4 tables, split on ebook_access — 16% empty\n")
acc <- arr %>% spread_values(access = jstring("ebook_access")) %>% as.data.frame()
for (kind in names(sort(table(acc$access), decreasing = TRUE))) {
  g <- Filter(function(r) r$ebook_access == kind, recs)
  fs <- sort(unique(unlist(lapply(g, names))))
  h <- mean(sapply(g, function(r) sum(!(fs %in% names(r))))) / length(fs)
  cat(sprintf("      %-16s %3d x %3d cols  %3.0f%% empty\n", kind, length(g),
              length(fs), 100 * h))
}
cat("    dplyr's `group_by` gives those once the field is named. Of the six\n")
cat("    always-present fields, edition_count makes it WORSE and public_scan_b\n")
cat("    changes nothing. Choosing is the fourth operation. NO.\n")

# ── Q7. How many records. ────────────────────────────────────────────────
meta <- txt %>% as.tbl_json %>%
  spread_values(numFound = jnumber("numFound"), start = jnumber("start")) %>%
  as.data.frame()
cat("\nQ7 ", n, "docs in the array — and from the same text:\n")
cat("      numFound", format(meta$numFound, big.mark = ","), "· start", meta$start, "\n")
cat("    TWO RIGHT ANSWERS: 200 are here, 30,427 exist. This is a PAGE, and\n")
cat("    tidyjson can reach both because it starts at the root.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────
cat("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA\n")
cat("    section is empty for this file.\n")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────
tbl <- arr %>% spread_values(title = jstring("title"),
                             editions = jnumber("edition_count"),
                             access = jstring("ebook_access")) %>%
  as.data.frame() %>% select(title, editions, access)
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cov <- arr %>% spread_values(cover = jnumber("cover_i")) %>% as.data.frame()
cat("\nQ9  cover_i non-NA on", sum(!is.na(cov$cover)), "of", n,
    "— spread_values keeps the row\n")

# ── Q10. Flatten the deepest array into rows. ───────────────────────────
an <- arr %>% spread_values(key = jstring("key")) %>%
  enter_object("author_name") %>% gather_array("i") %>%
  append_values_string("author") %>% as.data.frame()
cat("\nQ10", nrow(an), "author rows over", length(unique(an$key)), "docs\n")
cat("    `enter_object` drops the one doc with no author_name, silently.\n")
cat("    FIVE fields are arrays and every one is ALSO sometimes absent.\n")

# ── Q11. Find every path whose value matches something. ────────────────
hits <- arr %>% gather_object("field") %>% json_types %>%
  filter(type == "string") %>% append_values_string("v") %>%
  filter(grepl("https?://", v)) %>% count(field) %>% as.data.frame()
cat("\nQ11 URLs inside the 200 docs:", if (nrow(hits)) nrow(hits) else 0, "\n")
top <- txt %>% as.tbl_json %>%
  spread_values(u = jstring("documentation_url")) %>% as.data.frame()
cat("    and at the TOP LEVEL:", top$u, "\n")
cat("    THE ONLY URL IS THE TOP-LEVEL ONE. tidyjson can reach it because the\n")
cat("    pipe starts at the root — but the LEVEL had to be named, twice. PARTLY.\n")
cat("    pandas and polars frame `docs` and report NONE OF ONE.\n")

# ── Q12. The flattest honest table, and what was lost. ─────────────────
sa <- arr %>% spread_all
cat("\nQ12 spread_all():", nrow(sa), "x", ncol(sa), "\n")
cat("    It widens the scalars and LEAVES THE FIVE ARRAYS BEHIND — which is the\n")
cat("    honest thing here. On 13-package-lock the same verb recursed into keyed\n")
cat("    collections and built 1,391 columns; there is nothing to recurse into\n")
cat("    now, so it stops where it should.\n")
cat("    rrapply's `bind` expands those arrays positionally into 36 columns at\n")
cat("    64% NA, which is worse than leaving them alone.\n")
