# jqr — USGS earthquakes, one month
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (version printed at run time)
#  file          ../source.json   7.4 MB, 10,885 features, depth 5
#  measured      2026-08-10
#  run           cd corpus/25-usgs-quakes/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             4   NO                  YES — 45
#   2 how deep                                    2   NO                  YES — 5
#   3 what is one record                          2   YES                 CANNOT
#   4 always present vs sometimes                 4   NO                  YES
#   5 does any field change type                  4   NO                  yes, with a caveat
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                            1   YES                 yes
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          4   NO                  YES
#  12 flattest honest table                       3   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
#  14 survives the next file unchanged?               yes for those five
#  15 readable a week later?                          the R-string quoting hurts
#  16 lines, and how much is ceremony?                ~65, and the quoting is the tax
#
# **jqr IS THE SAME LANGUAGE AS `python/try-jq.py` AND GETS THE SAME ANSWERS**,
# which is the point of having both: `README.md` calls them two doorways to one
# query language, and on this file the doorways agree exactly — 45 path shapes,
# depth 5, all 26 keys on all 10,885 features, no type change once null is
# excluded, and all three URL-valued paths including `metadata.url`.
#
# **What differs is the ergonomics and the memory.** Every program is an R
# string, so jq's own quotes have to be escaped or single-quoted around, and
# `04-gharchive` already recorded the cost side: `jq()` takes an R string and has
# no slurp, so jqr needed 198 MB where the jq BINARY needed 4.3 MB for the same
# query. That is a fact about the binding, not the language.
# ─────────────────────────────────────────────────────────────────────────────

library(jqr)
library(jsonlite)
cat(sprintf("R %s, jqr %s, jsonlite %s\n",
            getRversion(), packageVersion("jqr"), packageVersion("jsonlite")))

raw <- paste(readLines("../source.json", warn = FALSE), collapse = "")
q <- function(prog) jq(raw, prog)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  jq parses or fails, and the LAST duplicate key silently wins.\n")
cat("    Nothing about big ints or encoded payloads. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
cat("\nQ1 ", q('[paths | map(if type=="number" then "[]" else . end) | join(".")] | unique | length'),
    "distinct folded path shapes\n")
cat("Q2  depth", q('[paths | length] | max'), "\n")
cat("    Both agree with python/try-jq.py, with ijson, with purrr's hand-walk\n")
cat("    and with design/probe.py.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3/Q7 ", q('.features | length'), "features. No candidates named. CANNOT for Q3.\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
cat("\nQ4  property keys NOT on every feature:\n   ",
    q('(.features | length) as $n | [.features[].properties | keys[]] | group_by(.) | map(select(length < $n) | .[0])'),
    "\n")
cat("    `keys` counts PRESENCE, so the answer is none — every key is on every\n")
cat("    feature and six of them are null. jsonlite's simplified frame says six\n")
cat("    are 'sometimes'; this is the same split the Python half found.\n")

# ── Q5. Does any field change type between records. ──────────────────────────
cat("\nQ5  fields taking more than one JSON type INCLUDING null:\n   ",
    q('[.features[].properties | to_entries[] | {k: .key, t: (.value|type)}] | group_by(.k) | map(select((map(.t)|unique|length) > 1) | .[0].k)'),
    "\n")
cat("Q5  the same, EXCLUDING null:\n   ",
    q('[.features[].properties | to_entries[] | select(.value != null) | {k: .key, t: (.value|type)}] | group_by(.k) | map(select((map(.t)|unique|length) > 1) | .[0].k)'),
    "\n")
cat("    An empty array is the right answer and matches the probe. jq reports\n")
cat("    null AS a type, so the exclusion has to be written by hand.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  no keyed collections here. n/a\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
cat("\nQ8 ", q('[.features[] | {mag: .properties.mag, place: .properties.place, time: .properties.time}] | .[0:2]'), "\n")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
cat("\nQ9  features with a non-null alert:",
    q('[.features[] | select(.properties.alert != null)] | length'), "\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
cat("\nQ10 ", q('[.features[] | {lon: .geometry.coordinates[0], lat: .geometry.coordinates[1], d: .geometry.coordinates[2]}] | .[0:2]'), "\n")

# ── Q11. Find every path whose value matches something. ──────────────────────
cat("\nQ11 URL-valued path shapes and counts:\n   ",
    q('[paths(type=="string" and startswith("http")) | map(if type=="number" then "[]" else . end) | join(".")] | group_by(.) | map({key: .[0], value: length}) | from_entries'),
    "\n")
cat("    Including metadata.url, which sits outside `features` and which every\n")
cat("    frame-shaped tool in this directory missed.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12 ", q('[.features[] | .properties + {id, lon: .geometry.coordinates[0], lat: .geometry.coordinates[1], depth_km: .geometry.coordinates[2]}] | .[0] | keys | length'),
    "columns, and the three coordinate names are mine.\n")

# ── The packed strings, because defect 26 came from this file. ───────────────
cat("\nDEFECT 26  does jqr notice a list packed into a string?\n")
cat("   ", q('.features[0].properties.types'), "\n")
cat("    A string. Splittable in one step once a human notices:\n")
cat("   ", q('.features[0].properties.types | split(",") | map(select(. != ""))'), "\n")
