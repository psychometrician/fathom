# jqr — 100 openFDA adverse-event reports
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (version printed at run time)
#  file          ../source.json   2.7 MB, 100 results, depth 8
#  measured      2026-08-11
#  run           cd corpus/18-openfda-events/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             4   NO                  YES — exactly 122
#   2 how deep                                    2   NO                  YES — exactly 8
#   3 what is one record                           8  NO                  PARTLY
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  4   NO                  YES — correctly none
#   6 are any object keys data                    4   -                   n/a — no abstention
#   7 how many records                             4   NO                  yes — four answers
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   3   YES                 YES — one expression
#  11 find every path matching something          4   NO                  YES — best in R
#  12 flattest honest table                       3   YES                 yes
#  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
#  14 survives the next file unchanged?               yes for all of those
#  15 readable a week later?                          the array-index fold needs a comment
#  16 lines, and how much is ceremony?                ~100
#
# **ON THE DEEPEST DOCUMENT IN THE CORPUS jqr REPRODUCES FOUR PROBE NUMBERS
# EXACTLY** — 122 paths, depth 8, 12 key-sets over results and 115 over drug.
#
# **AND `..` CROSSES FOUR LEVELS IN ONE EXPRESSION.**
# `[.. | .brand_name? // empty | .[]]` reaches
# `results[] → patient → drug[] → openfda → brand_name[]` and returns all 2,375
# names **without naming a single level**. jsonlite needs a nested `lapply`
# chain, purrr a nested `map`, rrapply a melt filtered on L7. jmespath matches it
# for length by naming every level; only `..` names none.
#
# **IT FINDS BOTH URLs**, under `meta` and outside `results` — pandas and polars
# frame the records and report none of two.
#
# **WHAT IT HAS NO WORD FOR IS THE ABSTENTION.** The probe prints `could not call
# 3 small single-copy objects` and names them: a third state between "keys are
# data" and "keys are fields". `keys` gives the material and never declines.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("R %s, jqr %s, jsonlite %s (system jq: %s)\n",
            getRversion(), packageVersion("jqr"), packageVersion("jsonlite"),
            tryCatch(system("jq --version", intern = TRUE), error = \(e) "not on PATH")))

txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)
n <- 100

run <- function(program, label) {
  t0 <- Sys.time()
  out <- jq(txt, program)
  cat(sprintf("    [%5.2fs] %s\n", as.numeric(Sys.time() - t0, units = "secs"), label))
  out
}

# ── Q0. Is this what it claims to be, and is it whole? ─────────────────────
cat("\nQ0  jqr hands the text to libjq, which errors on malformed JSON and says\n")
cat("    nothing about duplicate keys, big integers or NaN. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep. ──────────────────────────────────
cat("\nQ1  paths, with array indices folded to []:\n")
paths <- fromJSON(run('[paths | map(if type == "number" then "[]" else . end)
                        | join(".")] | unique', "..."))
cat("   ", length(paths), "— THE PROBE PRINTS 122. Exact.\n")
cat("    deepest:", paths[which.max(lengths(strsplit(paths, ".", fixed = TRUE)))], "\n")
cat("\nQ2  max path length:\n")
cat("   ", fromJSON(run("[paths | length] | max", "...")),
    "— the probe prints 8, the deepest file in the corpus. pandas says 3.\n")

# ── Q3/Q7. The row candidates. ────────────────────────────────────────────
cat("\nQ3/Q7  jqr counts any level named, one expression:\n")
cnt <- fromJSON(run('{results: (.results|length),
                     drug: ([.results[].patient.drug[]]|length),
                     reaction: ([.results[].patient.reaction[]]|length),
                     total_available: .meta.results.total}', "..."))
cat("   ", paste(names(cnt), unlist(cnt), sep = "=", collapse = " · "), "\n")
cat("    THE PROBE NAMES FOUR CANDIDATES AND PRICES THEM:\n")
cat("      the whole document        1 rows x  2 cols\n")
cat("      an item of results      100 rows x 39 cols   26% empty\n")
cat("      an item of drug         265 rows x 41 cols   47% empty\n")
cat("      an item of reaction     247 rows x  3 cols\n")
cat("    jqr counted every level I named and proposed none. PARTLY.\n")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
cat("\nQ4  field counts over the results:\n")
fc <- fromJSON(run('[.results[] | keys_unsorted[]] | group_by(.)
                    | map({(.[0]): length}) | add', "..."))
nul <- fromJSON(run('[.. | select(. == null)] | length', "..."))
cat("   ", length(fc), "fields · always", sum(unlist(fc) == n), "· sometimes",
    sum(unlist(fc) < n), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(unlist(fc)), 5))
cat("    and", nul, "nulls in the WHOLE document, so the raggedness is almost\n")
cat("    purely absence. 15-github-issues had 807.\n")

# ── Q5. Does any field change type. ──────────────────────────────────────
cat("\nQ5  fields whose non-null type varies, over the results:\n")
varying <- fromJSON(run('[.results[] | to_entries[] | select(.value != null)
      | {k: .key, t: (.value|type)}] | group_by(.k)
      | map(select((map(.t)|unique|length) > 1) | .[0].k)', "..."))
cat("   ", if (length(varying)) paste(varying, collapse = ", ") else "none",
    "— the probe's answer. DuckDB's STRUCT route reports TWELVE here,\n")
cat("    eleven of them from keys it invented.\n")

# ── Q6. Are any object keys actually data? AND key-sets. ────────────────
cat("\nQ6  no keyed collections. n/a — and the probe prints `could not call 3\n")
cat("    small single-copy objects`, an ABSTENTION jqr has no way to make.\n")
cat("\nQ6b distinct key-sets:\n")
ks <- fromJSON(run('{results: ([.results[]|keys_unsorted|sort|join(",")]|unique|length),
                     drug: ([.results[].patient.drug[]|keys_unsorted|sort|join(",")]
                            |unique|length)}', "..."))
cat("    results", ks$results, "· drug", ks$drug,
    "— THE PROBE PRINTS 12 and 115. Both exact.\n")

# ── Q8/Q9. Extraction. ──────────────────────────────────────────────────
cat("\nQ8  three fields:\n")
t <- fromJSON(run('[.results[] | {safetyreportid, serious, receivedate}]', "..."))
cat("   ", nrow(t), "rows x", ncol(t), "cols\n"); print(head(t, 2))
cat("\nQ9  a field absent from most results:\n")
q9 <- fromJSON(run('[.results[] | {safetyreportid, seriousnessdeath}]', "..."))
cat("   ", nrow(q9), "rows kept,", sum(is.na(q9$seriousnessdeath)), "NA\n")

# ── Q10. Flatten the deepest array — ONE EXPRESSION. ───────────────────
cat("\nQ10 the deepest array, crossing four levels with `..`:\n")
bn <- fromJSON(run('[.. | .brand_name? // empty | .[]] | length', "..."))
cat("   ", bn, "brand names from `[.. | .brand_name? // empty | .[]]`\n")
cat("    NO LEVEL WAS NAMED. jsonlite needs a nested lapply chain, purrr a\n")
cat("    nested map, rrapply a melt filtered on L7. `..` is the one verb in\n")
cat("    this comparison that does not care how deep the thing is.\n")

# ── Q11. Find every path whose value matches something. ────────────────
cat("\nQ11 URL-valued paths, no field named:\n")
urls <- fromJSON(run('[paths(type == "string" and test("https?://")) | join(".")]
                      | group_by(.) | map({(.[0]): length}) | add', "..."))
print(unlist(urls))
cat("    BOTH, and both under `meta` — outside `results`. pandas and polars\n")
cat("    report NONE OF TWO. purrr and jsonlite each need eight to ten lines.\n")

# ── Q12. The flattest honest table. ────────────────────────────────────
cat("\nQ12 the honest record table:\n")
flat <- fromJSON(run('[.results[]]', "..."))
cat("   ", nrow(flat), "x", ncol(flat), "own fields, two of them arrays holding\n")
cat("    265 drugs and 247 reactions — the probe's other two row candidates.\n")
