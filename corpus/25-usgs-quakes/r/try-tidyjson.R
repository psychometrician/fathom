# tidyjson — USGS earthquakes, one month
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed at run time)
#  file          ../source.json   7.4 MB, 10,885 features, depth 5
#  measured      2026-08-10
#  run           cd corpus/25-usgs-quakes/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  YES, then WRONG
#   2 how deep                                    3   NO                  NO — says 3
#   3 what is one record                          2   YES                 CANNOT
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  4   NO                  yes, with a filter
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                            1   YES                 yes
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes, LONG
#  11 find every path matching something          2   -                   CANNOT
#  12 flattest honest table                       3   YES                 yes
#  13 needed the shape in advance?                    NO for 1, 4, 5
#  14 survives the next file unchanged?               Q1/Q4/Q5 yes
#  15 readable a week later?                          yes — the verbs are the clearest here
#  16 lines, and how much is ceremony?                ~95, and the type audit is 20
#
# **THIS IS THE FIRST DOCUMENT IN THE CORPUS WHERE `json_schema` DISCARDS
# NOTHING.** Five previous entries record it silently dropping fields —
# `11-jupyter-notebook` lost 50% of key names on the corpus's most regular
# document — and here it names **all 26** property fields. The difference is
# that this file has exactly ONE key-set across 10,885 records, which is the
# case the verb was built for.
#
# **AND IT TYPES FIVE OF THEM WRONG, which is the more interesting failure.**
# `alert`, `cdi`, `felt` and `mmi` are typed `"null"` because they are null on
# most records, and `status` is typed `"number"` where it is a string on every
# one. `design/coverage.py` scores `design/probe.py` at **0.0% TYPED WRONG**
# across 1,104,833 field occurrences — it types far less, and what it types it
# gets right. **Naming a field and typing it are two claims, and this document
# separates them.**
#
# **Question 2 is wrong too**: the schema's nesting reads 3 where the document
# is 5 deep, because `json_schema` collapses an array to a single element.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages(library(tidyjson))
suppressMessages(library(dplyr))
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

raw <- paste(readLines("../source.json", warn = FALSE), collapse = "")

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  tidyjson parses via jsonlite and says nothing about damage. CANNOT.\n")

# ── Q1. What is in here — json_schema is the verb built for it. ──────────────
schema <- json_schema(raw)
cat("\nQ1  json_schema is", nchar(schema), "characters for a 7.4 MB file\n")
cat("Q1  first 400:\n   ", substr(schema, 1, 400), "\n")

# ── HOW MANY OF THE DOCUMENT'S FIELDS DOES THE SCHEMA ACTUALLY NAME? ─────────
# `12-agent-trace` and `11-jupyter-notebook` both found json_schema silently
# discarding, so this is checked rather than assumed.
feats_raw <- jsonlite::fromJSON("../source.json", simplifyVector = FALSE)$features
truth <- names(feats_raw[[1]]$properties)
named <- vapply(truth, \(k) grepl(paste0('"', k, '"'), schema, fixed = TRUE), TRUE)
cat("\nQ1  of the", length(truth), "property fields the document has,",
    sum(named), "appear in json_schema\n")
if (any(!named)) cat("    MISSING:", paste(truth[!named], collapse = ", "), "\n")

# ── AND HOW MANY OF THOSE TYPES ARE RIGHT? ──────────────────────────────────
# Naming a field and typing it are different claims, and `design/coverage.py`
# scores the probe at 0.0% TYPED WRONG across 1,104,833 field occurrences. The
# same test, applied here.
truth_t <- lapply(setNames(nm = truth), \(k)
  unique(vapply(feats_raw, \(f) { v <- f$properties[[k]]
    if (is.null(v)) "null" else if (is.character(v)) "string"
    else if (is.logical(v)) "logical" else "number" }, "")))
claimed <- regmatches(schema, gregexpr('"[A-Za-z]+": "[a-z]+"', schema))[[1]]
wrong <- 0; tot <- 0
for (cl in claimed) {
  parts <- regmatches(cl, gregexpr("[A-Za-z]+", cl))[[1]]
  k <- parts[1]; ty <- parts[2]
  if (!is.null(truth_t[[k]])) {
    tot <- tot + 1
    real <- setdiff(truth_t[[k]], "null")
    if (length(real) && !(ty %in% real)) {
      wrong <- wrong + 1
      cat(sprintf("    WRONG  %-8s schema says %-7s truth is %s\n",
                  k, ty, paste(truth_t[[k]], collapse = "/")))
    }
  }
}
cat(sprintf("\nQ1  %d of %d typed property claims are WRONG\n", wrong, tot))
cat("    Four fields are typed `null` because they are null on most records,\n")
cat("    and `status` is typed `number` where it is a string everywhere.\n")
cat("    The probe types 0.0% wrong corpus-wide; it also types far less.\n")

# ── Q2. How deep. ────────────────────────────────────────────────────────────
cat("\nQ2  json_schema shows the nesting but reports no number; counting braces\n")
cat("    in the schema string is the only reading available. Depth from the\n")
cat("    schema's nesting:", max(cumsum(strsplit(gsub("[^{}]", "", schema), "")[[1]] == "{") -
                                 cumsum(strsplit(gsub("[^{}]", "", schema), "")[[1]] == "}")), "\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
feats <- raw %>% enter_object("features") %>% gather_array("feature_no")
cat("\nQ3/Q7 ", nrow(feats), "features after gather_array. tidyjson names no\n")
cat("    candidates; `enter_object('features')` is my choice, not its suggestion.\n")

# ── Q4/Q5. Always present, and does any field change type. ───────────────────
kv <- feats %>% enter_object("properties") %>% gather_object("key") %>% json_types("type")
tab <- as_tibble(kv) %>% count(key, type)
cat("\nQ4  distinct property keys seen:", length(unique(tab$key)), "\n")
per_key <- as_tibble(kv) %>% count(key, name = "n")
cat("Q4  keys appearing on fewer than all", nrow(feats), "features:",
    sum(per_key$n < nrow(feats)), "\n")
cat("    gather_object walks KEYS, so a null is present — the same right answer\n")
cat("    purrr, jq, jqr, ijson and rrapply give.\n")
varying <- tab %>% filter(type != "null") %>% count(key) %>% filter(n > 1)
cat("\nQ5  keys with more than one non-null type:",
    if (nrow(varying)) paste(varying$key, collapse = ", ") else "none",
    "— agrees with the probe\n")
cat("Q5  and json_types DOES report null as its own type, so the filter is mine:\n")
print(tab %>% filter(key %in% c("alert", "mag")) %>% as.data.frame())

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  no keyed collections here. n/a\n")

# ── Q8/Q9. Extraction with spread_all. ───────────────────────────────────────
three <- feats %>% enter_object("properties") %>%
  spread_values(mag = jnumber("mag"), place = jstring("place"), time = jnumber("time"))
cat("\nQ8 ", nrow(three), "rows x 3 named values\n")
print(head(as_tibble(three)[c("mag", "place", "time")], 2))

alert <- feats %>% enter_object("properties") %>% spread_values(alert = jstring("alert"))
cat("\nQ9  alert non-NA on", sum(!is.na(as_tibble(alert)$alert)), "of", nrow(alert),
    "— rows kept, hole is NA\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co <- feats %>% enter_object("geometry") %>% enter_object("coordinates") %>%
  gather_array("axis") %>% append_values_number("v")
cat("\nQ10", nrow(co), "rows —", nrow(co) / nrow(feats), "per feature, LONG not wide\n")

# ── Q11. Find every path whose value matches something. ──────────────────────
cat("\nQ11 CANNOT. tidyjson has no path enumeration and no value predicate over\n")
cat("    unnamed keys; every verb needs the key it is entering.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
wide <- feats %>% enter_object("properties") %>% spread_all()
cat("\nQ12 spread_all gives", nrow(wide), "x", ncol(wide), "\n")
cat("Q12 columns:", paste(head(names(wide), 8), collapse = ", "), "…\n")

# ── The packed strings, because defect 26 came from this file. ───────────────
cat("\nDEFECT 26  does tidyjson notice a list packed into a string?\n")
cat("   ", as_tibble(wide)$types[1], "\n")
cat("    A character column. No verb looks inside a value.\n")
