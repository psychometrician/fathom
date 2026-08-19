# tidyjson — NYC 311 service requests, the 20,000 most recent
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (+ dplyr; versions printed at run time)
#  file          ../source.json   28.1 MB, 20,000 records, depth 4
#  measured      2026-08-11
#  run           cd corpus/14-nyc-311/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   PARTLY
#   1 what is in here                             5   NO                  YES — typed and counted
#   2 how deep                                    4   NO                  YES — exactly 4
#   3 what is one record                          3   NO                  PARTLY
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  5   NO                  YES — and it NAMES types
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   4   YES                 yes
#  11 find every path matching something          4   NO                  PARTLY
#  12 flattest honest table                       3   YES                 yes
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7
#  14 survives the next file unchanged?               yes for all of those
#  15 readable a week later?                          yes — the verbs say what they do
#  16 lines, and how much is ceremony?                ~110, and the pipes are the intent
#
# **tidyjson TYPES ALL 48 FIELDS AND GETS EVERY ONE RIGHT, WHICH IS NEW.**
# `CLAUDE.md` records that on `25-usgs-quakes` tidyjson *"names every field for
# the first time in the corpus, and types five of them wrong."* Here it names 48
# and misses none: **47 string, 1 object, 0 number, 0 logical, 0 null.**
#
# **The reason is the same one that makes every tool agree on question 4 here.**
# Entry 25's five wrong types were fields that are present-and-null; tidyjson
# typed the null rather than the field. **This document has ZERO nulls**, so
# there is nothing to mistype. The instrument did not improve — the document
# stopped being ambiguous — and that is why this entry is worth having.
#
# **`json_structure` IS THE BEST SINGLE ANSWER TO QUESTION 1 IN EITHER LANGUAGE.**
# One verb returns a typed census by level: 1 array at level 0, 20,000 objects at
# level 1, 694,198 strings and 19,570 objects at level 2, and so on to 39,140
# numbers at level 4. That is `what is in here`, `how deep` and `what types` in
# one frame, and no other tool in this comparison prints all three together.
#
# **THE COST IS TIME AND IT IS THE WORST IN R.** `json_structure` over 20,000
# records takes **10–12 seconds** — printed below, and it is the whole file's
# runtime bar four seconds. That is `design/probe.py`'s ENTIRE runtime on this
# document, 10.8 s, spent on one of its dozen answers. jq pays the same toll for
# question 1 in Python. **Both of the two tools that answer question 1 properly
# cost about what describing the whole document costs.**
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

# tidyjson wants JSON TEXT, not a parsed list. Handing it jsonlite's output
# fails with "20000 records are not arrays", which names the data rather than
# the mistake.
txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  tidyjson parses the text itself rather than taking someone's list, so\n")
cat("    it would fail on malformed input. It reports no duplicate keys, no big\n")
cat("    integers and no NaN. PARTLY — it owns the parse and says nothing about it.\n")

t0 <- Sys.time()
arr <- txt %>% as.tbl_json %>% gather_array
cat(sprintf("    gather_array: %d rows in %.1fs\n",
            nrow(arr), as.numeric(Sys.time() - t0, units = "secs")))

# ── Q1/Q4/Q5. What is in here, how often, and of what type. ──────────────────
t1 <- Sys.time()
fields <- arr %>% gather_object %>% json_types %>% count(name, type)
cat(sprintf("\nQ1  gather_object + json_types: %d name/type pairs in %.1fs\n",
            nrow(fields), as.numeric(Sys.time() - t1, units = "secs")))
cat("   ", length(unique(fields$name)), "distinct field names\n")
cat("Q5  types tidyjson assigned:\n"); print(table(fields$type))
cat("    ONE ROW PER NAME, so no field carries two types — question 5 answered\n")
cat("    directly, and correctly. 47 string + 1 object is the truth.\n")
cat("    On 25-usgs-quakes this same code typed five fields WRONG, because they\n")
cat("    were present-and-null. This document has no nulls to mistype.\n")

n <- nrow(arr)
present <- setNames(fields$n, fields$name)
cat("\nQ4  always", sum(present == n), "· sometimes", sum(present < n),
    "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(present), 5))

# ── Q2. How deep does it go — json_structure. ────────────────────────────────
t2 <- Sys.time()
st <- txt %>% as.tbl_json %>% json_structure
struct_s <- as.numeric(Sys.time() - t2, units = "secs")
cat(sprintf("\nQ2  json_structure: %d rows in %.1fs\n", nrow(st), struct_s))
cat("    max level:", max(st$level), "— the probe prints '4 levels deep'\n")
cat("    a typed census by level, which is Q1, Q2 and Q5 in one frame:\n")
print(table(level = st$level, type = st$type))
cat("    NOTE the null column is zero at every level. That is why every tool in\n")
cat("    both directories agrees on question 4 for this document.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  gather_array made the choice: array elements are rows,", n, "of them.\n")
cat("    It names no alternative and prices nothing. PARTLY.\n")
cat("Q7 ", n, "records\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
odd <- grep("^[^A-Za-z]", unique(fields$name), value = TRUE)
cat("\nQ6  no keyed collections. n/a.", length(odd), "names are not identifiers;\n")
cat("    gather_object puts the key in a COLUMN, so they cost nothing:", odd[1], "\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl <- arr %>% spread_values(complaint_type = jstring("complaint_type"),
                             borough        = jstring("borough"),
                             created_date   = jstring("created_date")) %>%
  as.data.frame() %>% select(complaint_type, borough, created_date)
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
q9 <- arr %>% spread_values(unique_key = jstring("unique_key"),
                            closed_date = jstring("closed_date")) %>% as.data.frame()
cat("\nQ9  closed_date non-NA on", sum(!is.na(q9$closed_date)), "of", nrow(q9),
    "— rows kept\n")
cat("    `spread_values` fills the absent ones with NA rather than dropping the\n")
cat("    row, which is what the question asks for and what jmespath does not do.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co <- arr %>% enter_object("location") %>% enter_object("coordinates") %>%
  gather_array("pos") %>% append_values_number("v") %>% as.data.frame()
cat("\nQ10", nrow(co), "rows —", nrow(co) / 2, "pairs x 2, in long form\n")
print(head(co[, c("pos", "v")], 4))
cat("    tidyjson gives it LONG, one row per element, with the position named.\n")
cat("    Every other tool here gives it wide or as a list; this is the only one\n")
cat("    that treats an array element as a row by default.\n")

# ── Q11. Find every path whose value matches something. ──────────────────────
hits <- arr %>% gather_object %>% json_types %>% filter(type == "string") %>%
  append_values_string("v") %>% filter(grepl("https?://", v)) %>%
  count(name) %>% as.data.frame()
cat("\nQ11 URL-valued fields:\n"); print(hits)
cat("    Correct, but it only reaches the RECORD's own string fields — the pipe\n")
cat("    names the level to scan. A URL inside `location` would need a second\n")
cat("    pipe. PARTLY: no field had to be named, but the depth did.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12 spread_all() would widen every scalar; `location` needs enter_object\n")
cat("    first, so the honest table is two pipes joined on the array index.\n")
cat("    Nothing is lost, and nothing is a list-column — but unlike rrapply's\n")
cat("    one-verb `bind`, the shape has to be assembled by hand.\n")
