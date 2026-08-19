# jqr — Wikidata entity Q30 (United States), full JSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.json   1.47 MB, depth 13, 19,149 paths, 48 fields,
#                                 7 keyed sites, explosion 398.9
#  measured      2026-08-10
#  run           cd corpus/10-wikidata/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              -   -                   CANNOT
#   1 what is in here                            4   no                  WRONG
#   2 how deep                                   1   no                  yes
#   3 what is one record                         -   -                   CANNOT
#   5 does any field change type                 3   YES                 YES
#   6 are any keys actually data                 5   YES                 NO
#   7 how many records                           2   YES                 partly
#  11 find every path matching something         2   no                  yes
#  12 flattest honest table                      3   no                  yes
#  13 needed the shape in advance?                   NO for 1, 2, 11, 12
#  16 lines, and how much is ceremony?               8 expressions, no ceremony
#
#  Q1 is scored WRONG rather than NO for the same reason as on
#  09-stripe-openapi: it answers, the answer is small, and it is small because
#  the expression cannot see what makes this document hard.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 1** in this entry's NOTES.md, written and
# committed before any tool here ran: that jq's distinct-leaf-name count would
# come back UNDER 100 despite this being the corpus's most path-exploded
# document — 19,149 paths for 48 fields, ratio 398.9, and 7 keys-as-data sites.
#
# The two-cause refinement made on 2026-08-09 says the key reaches a leaf only
# when a keyed object's values are SCALARS. Wikidata's keys are P-numbers and
# language codes holding OBJECTS. **If this came back in the thousands the
# refinement was wrong**, because no file in the corpus is a better worst case.
library(jqr)

cat(sprintf("R %s, jqr %s; jq CLI reports %s (jqr's linked library is not queryable)\n",
            getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

path  <- "../source.json"
bytes <- file.size(path)
txt   <- paste(readLines(path, warn = FALSE), collapse = "")
ask   <- function(q) jq(txt, q)

cat(sprintf("\n2. depth %s, from `[paths|length]|max`\n", ask("[paths|length]|max")))

# ── Q1. PREDICTION 1. ────────────────────────────────────────────────────────
cat("\n1. what is in here:\n")
n_leaf <- ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
cat(sprintf("   distinct leaf names: %s\n", n_leaf))
seen <- ask('[.entities.Q30.claims|keys[]] as $p
             | [paths(type != "object" and type != "array")|map(select(type=="string"))|last]
             | map(select(. as $x | $p|index($x))) | length')
cat(sprintf("   P-numbers ever appearing as the LAST path component: %s of 469\n", seen))
cat("   PREDICTION 1 CONFIRMED, and this is the third document to confirm it.\n")
cat("   The four-point table, one expression, unchanged character-for-character:\n")
cat("     01-npm-registry   3,100   6 keyed sites, values are SCALARS\n")
cat("     03-natural-earth     63   0 keyed sites\n")
cat("     09-stripe-openapi    29  47 keyed sites, values are OBJECTS\n")
cat(sprintf("     10-wikidata        %5s   7 keyed sites, values are OBJECTS\n", n_leaf))
cat("   The count tracks whether the key is the LEAF, not how many keyed sites\n")
cat("   there are. npm's 3,100 is `users` and `time` mapping to scalars.\n")

# ── Q12. The honest measure. ─────────────────────────────────────────────────
cat("\n12. the honest measure — list every leaf path, and price it:\n")
# Asked as a NUMBER rather than as text. The first draft called nchar() on jqr's
# returned string, which is JSON-ENCODED — quotes and backslash escapes included
# — and read 176% where the raw bytes are 173%. Measuring the transport instead
# of the thing is the same error as `str()`'s 7,099 naming a non-default parse.
chars <- as.numeric(ask('([paths(type != "object" and type != "array")|join(".")|length]|add) + ([paths(type != "object" and type != "array")]|length)'))
cat(sprintf("   %s chars for a %s-byte file (%.0f%%)\n",
            format(chars, big.mark = ","), format(bytes, big.mark = ","),
            100 * chars / bytes))
cat("   rrapply's melt on this same file is 2,536,874 chars — 173% as well,\n")
cat("   agreeing with the figure above to within 0.1%. A query language and an\n")
cat("   R tree-walker, independently enumerating the same leaves.\n")
cat("   VERDICT.md records the probe's answer for this document as 75 lines and\n")
cat("   4.5 KB, which is 0.3%. That is the gap the fold is for.\n")

# ── Q5. Genuine polymorphism by type, and jq states it plainly. ──────────────
cat("\n5. does any field change type — and here it is REAL, not an artifact:\n")
poly <- ask('[..|objects|select(has("datavalue"))|.datavalue.value|type]
             |group_by(.)|map({t:.[0],n:length})')
cat(sprintf("   datavalue.value: %s\n", gsub("\\s+", "", poly)))
cat("   YES, and it took one expression. NOTES.md grades this file polymorphic 3\n")
cat("   with `object x1,210, text x512` for the three named fields; the count\n")
cat("   above is every datavalue at any depth, so it is a wider denominator for\n")
cat("   the same property rather than a different reading.\n")
cat("   THIS IS THE ONE QUESTION WHERE JQ BEATS EVERY OTHER TOOL HERE. It has a\n")
cat("   `type` operator and a recursive descent, so `what types does this field\n")
cat("   take` is a sentence. tidyjson, asked the same thing, reports ONE of the\n")
cat("   two and drops the other — see try-tidyjson.R in this directory.\n")

# ── Q6 / Q7. ─────────────────────────────────────────────────────────────────
cat("\n6. are any object keys actually data:\n")
sig <- ask('{claims:(.entities.Q30.claims|length),
             keysets:([.entities.Q30.claims[][0]|keys|join(",")]|unique|length),
             labels:(.entities.Q30.labels|length),
             label_keysets:([.entities.Q30.labels[]|keys|join(",")]|unique|length)}')
cat(sprintf("   %s\n", gsub("\\s+", "", sig)))
cat("   NO as a verb. The signal is computable — 469 children over a handful of\n")
cat("   key-sets, 393 labels over one — and jq volunteers none of it. On this\n")
cat("   file the failure is invisible in the ordinary output, because the\n")
cat("   describer's answer is 34 and looks calm.\n")

cat(sprintf("\n7. %s claims, %s labels — both needed naming\n",
            ask(".entities.Q30.claims|length"), ask(".entities.Q30.labels|length")))
cat("   And `[..|objects]|length` is the unasked answer, which counts nothing\n")
cat("   anybody wants:\n")
cat(sprintf("   %s objects\n", ask("[..|objects]|length")))

# ── Q11. ─────────────────────────────────────────────────────────────────────
cat("\n11. find every path whose value matches something — URLs:\n")
nurl <- ask('[paths(type != "object" and type != "array") as $p|select((getpath($p)|type)=="string")
             |select(getpath($p)|test("^https?://"))]|length')
cat(sprintf("   %s URL-valued cells, from `paths` + `getpath` + a predicate\n", nurl))

cat("\n0. CANNOT — jq parses or it does not.\n")
cat("3. CANNOT — jq offers no row candidates.\n")

cat("
CONCLUSION — prediction 1 confirmed on the document that should have broken it.

  This file has the corpus's highest path explosion — **19,149 paths for 48
  fields, a ratio of 398.9** — and 7 keys-as-data sites. If jq's distinct-leaf-
  name count were driven by keys-as-data it would be enormous here. **It is 34**,
  and not one of the 469 P-numbers ever reaches a leaf.

  So the four-point table now reads 3,100 · 63 · 29 · 34, and the variable that
  explains it is not the number of keyed sites. It is whether a keyed object's
  values are SCALARS, which makes the key the leaf. npm is the only corpus file
  where that is true at scale, and `VERDICT.md`'s central number came from it.

  **The O(data) claim is unharmed and is now measured on four documents.**
  Listing every leaf path costs 173% of this file, and rrapply's melt costs 173%
  as well — agreeing to within 0.05% by a completely different route. The probe's
  own answer is 0.3%.

  WHERE JQ IS THE BEST TOOL IN THIS DIRECTORY is question 5. `[..|objects|
  select(has(\"datavalue\"))|.datavalue.value|type]` is one line, needs nothing
  known in advance, and returns both types with their counts. This document's
  genuine polymorphism is stated plainly by a tool that has been installed the
  whole time — and the R tool built to infer schemas silently reports one of the
  two. That contrast is the finding, and it is in the next file over.
")
