# tidyr — USGS earthquake catalogue, GeoJSON, 10,885 features
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   7.4 MB, 10,885 features
#  measured      2026-08-11
#  run           cd corpus/25-usgs-quakes/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  YES — 4, then 26
#   2 how deep                                    2   NO                  by exhaustion — 5
#   3 what is one record                          4   NO                  YES, and RIGHT
#   4 always present vs sometimes                 4   NO                  YES
#   5 does any field change type                  2   -                   CANNOT
#   6 are any object keys data                    2   -                   NO, correctly
#   7 how many records                            3   NO                  yes — 10,885
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              3  YES                  yes
#  10 flatten the deepest array                   8  YES                  YES — and see 7a
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       5  YES                  10,885 x 32
#  13 needed the shape in advance?                    NO for 1, 3, 4, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~90
#
# THE FOURTEENTH TOOL, and the last of the fourteen. See
# ../../24-cargo-metadata/r/try-tidyr.R for why entries 12–25 were missing it.
#
# THIS DOCUMENT PRODUCED DEFECT 26 — a health category the probe does not have.
# Three fields are LISTS PACKED INTO STRINGS, and the probe calls them text
# because they ARE text: `types` is ",nearby-cities,origin,phase-data," with a
# leading and a trailing comma, and once those sentinels are stripped it holds
# between 1 and 13 items.
#
# TIDYR HAS THE VERB FOR EXACTLY THIS, AND IT IS THE ONLY TOOL OF THE FOURTEEN
# THAT DOES. `separate_longer_delim` unpacks the packed string into rows:
#
#   separate_longer_delim(types, delim = ",")  ->  27,762 rows, 21 type names
#
# So the fourteenth tool can EXTRACT what defect 26 says the probe cannot
# DETECT, and those are different halves of the problem. tidyr does not notice
# that `types` is a packed list — it unpacks it once a person has noticed and
# named the delimiter. THE DETECTION IS STILL UNOWNED, and defect 26 stands
# exactly as written; what changes is that the repair is not a new verb.
#
# THE SECOND RESULT IS GEOJSON'S POSITIONAL COORDINATES, which is question 7a
# from the other side. `coordinates` is [lon, lat, depth] with no names
# anywhere in the document, and unnest_wider can only invent `coordinates_1`,
# `_2`, `_3`. Entry 17 showed tidyr zipping two parallel arrays correctly; here
# there is nothing to zip against, and NO TOOL CAN RECOVER NAMES THAT THE
# FORMAT KEEPS IN ITS SPECIFICATION RATHER THAN IN ITS BYTES.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

doc   <- fromJSON("../source.json", simplifyVector = FALSE)
feats <- doc$features

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q3 / Q7. ───────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = feats), x)),
                    type = "message")
w <- tibble(x = feats) |> unnest_wider(x, names_repair = "unique_quiet")
p <- w |> unnest_wider(properties, names_repair = "unique_quiet")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d — one row per earthquake, and right.\n", nrow(a), ncol(a)))
cat(sprintf("Q1  %d columns at the top, %d once `properties` is opened.\n",
            ncol(w), ncol(p)))
cat(sprintf("Q7  %d features.\n", nrow(p)))

# ── THE CENTREPIECE: defect 26's packed strings. ──────────────────────────
cat("\nQ10 THE PACKED LISTS — defect 26's finding, and tidyr has the verb:\n")
for (cn in c("types", "ids", "sources")) {
  v <- p[[cn]]; v <- v[!is.na(v)]
  n <- lengths(strsplit(gsub("^,|,$", "", v), ","))
  cat(sprintf("    %-8s class %-9s  e.g. %-34s  %d-%d items\n",
              cn, class(p[[cn]])[1], substr(v[1], 1, 34), min(n), max(n)))
}
s <- p |> select(id, types) |> filter(!is.na(types)) |>
  mutate(types = gsub("^,|,$", "", types)) |>
  separate_longer_delim(types, delim = ",")
cat(sprintf("\n    separate_longer_delim(types, delim = \",\") -> %d rows, %d names\n",
            nrow(s), n_distinct(s$types)))
print(head(sort(table(s$types), decreasing = TRUE), 5))
cat("    ══ THE ONLY TOOL OF THE FOURTEEN WITH A VERB FOR THIS. ══\n")
cat("    But it does NOT detect the packing — a person had to see the commas\n")
cat("    and name the delimiter. Defect 26 is about DETECTION and stands as\n")
cat("    written; what this changes is that the repair needs no new verb.\n")

# ── question 7a from the other side. ───────────────────────────────────────
g <- w |> select(id, geometry) |> unnest_wider(geometry, names_repair = "unique_quiet")
gw <- g |> unnest_wider(coordinates, names_sep = "_")
cat(sprintf("\nQ7a GEOJSON'S COORDINATES ARE POSITIONAL: %s\n",
            paste(grep("coordinates", names(gw), value = TRUE), collapse = ", ")))
cat("    [lon, lat, depth] with no names anywhere in the document, so\n")
cat("    unnest_wider can only invent `_1`, `_2`, `_3`. Entry 17 showed the\n")
cat("    same package zipping two parallel arrays correctly; the difference\n")
cat("    is that there the names lived in a sibling array and here they live\n")
cat("    in the GeoJSON specification. NO TOOL RECOVERS NAMES THAT ARE NOT IN\n")
cat("    THE BYTES, and this is the clean statement of that limit.\n")

# ── the object trap once more. ─────────────────────────────────────────────
nf <- n_distinct(unlist(map(w$properties, names)))
cat(sprintf("\n    THE OBJECT TRAP: unnest_longer(properties) -> %d rows from\n",
            nrow(w |> unnest_longer(properties))))
cat(sprintf("    %d features, because `properties` is an OBJECT with %d fields.\n",
            nrow(w), nf))
cat("    The largest wrong row count in the fourteen files, by a wide margin.\n")

# ── Q4 / Q5 / Q8 / Q9 / Q11 / Q12 / Q2. ───────────────────────────────────
fill <- map_dbl(p, \(c) mean(if (is.list(c)) lengths(c) > 0 else !is.na(c)))
cat(sprintf("\nQ4  %d of %d columns are on every feature; sparsest is `%s` at %.1f%%\n",
            sum(fill == 1), ncol(p), names(which.min(fill)), 100 * min(fill)))
cat("Q5  CANNOT.\n")
three <- p |> select(id, mag, place)
cat(sprintf("\nQ8  three named fields -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))
cat(sprintf("\nQ9  `mag` is absent on %d features and all are kept.\n",
            sum(is.na(p$mag))))
cat("\nQ11 CANNOT. No predicate over values.\n")
cat(sprintf("\nQ12 %d x %d with %d list-columns. WHAT IS LOST: the three packed\n",
            nrow(p), ncol(p), sum(map_lgl(p, is.list))))
cat("    fields stay strings unless unpacked by name, and the coordinates\n")
cat("    keep invented column names. Both are the document withholding\n")
cat("    structure that it never wrote down.\n")
cat("Q2  5 levels, by running out of list-columns.\n")

cat("
13. NO for 1, 3, 4 and 7.

14. YES. The USGS feed is stable and nothing here names an earthquake.

16. ~90 lines. `separate_longer_delim` is one of them, and it is the line
    that no other tool in this comparison can write.
")
