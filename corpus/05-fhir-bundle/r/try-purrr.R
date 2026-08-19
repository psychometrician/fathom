# purrr — a Synthea FHIR R4 patient bundle
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.json   2.0 MB, 564 resources, 20 resourceTypes, depth 11
#  measured      2026-08-09
#  run           cd corpus/05-fhir-bundle/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                            4   NO                  NO
#   2 how deep                                   2   NO                  yes
#   3 what is one record                         -   -                   CANNOT
#   4 always present vs sometimes                8   NO                  YES
#   5 does any field change type                 7   YES, the convention  partly
#   6 are any keys actually data                 -   -                   n/a
#   7 how many records                           1   YES                 yes
#   8 three named fields to a table              6   YES                 yes
#   9 a field missing from some rows             5   YES                 yes
#  13 needed the shape in advance?                   YES for 8 and 9
#  16 lines, and how much is ceremony?               see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE, AND WHY IT PAIRS WITH 03. On `03-natural-earth` `map_dfr` over
# 241 features needed **not one `%||%`**, because every feature carried every
# field. That was purrr looking its best, and it was the document doing the
# work rather than the tool.
#
# This is the other end of the same axis. **153 of 446 fields are ragged by
# absence, there are 42 distinct key-sets, and exactly two fields are present in
# all 564 resources.** Every field but `id` and `resourceType` needs a default.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
res <- map(doc$entry, "resource")

# ── Q1 / Q2 / Q7. ────────────────────────────────────────────────────────────
cat("\n1. what is in here — purrr has no describe verb, so this is str():\n")
for (lv in 2:4)
  cat(sprintf("   str(max.level=%d)  %6d lines\n", lv,
              length(capture.output(str(doc, max.level = lv)))))

cat("\n2. how deep does it go:\n")
depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_dbl(x, depth)) else 0
cat(sprintf("   %d levels, hand-written recursion over map_dbl\n", depth(doc)))
cat(sprintf("\n7. %d resources — after naming `entry` and then `resource`\n", length(res)))

# ── Q4. Always vs sometimes. purrr is genuinely good at this. ────────────────
cat("\n4. always present vs sometimes:\n")
ks <- map(res, names)
u  <- unique(flatten_chr(ks))
n  <- length(res)
freq <- map_int(set_names(u), \(k) sum(map_lgl(ks, \(x) k %in% x)))
cat(sprintf("   %d distinct keys across %d resources\n", length(u), n))
cat(sprintf("   present in ALL: %s\n", paste(names(freq)[freq == n], collapse = ", ")))
cat(sprintf("   present in exactly one: %d keys\n", sum(freq == 1)))
cat(sprintf("   distinct key-sets: %d\n",
            length(unique(map_chr(ks, \(x) paste(sort(x), collapse = ","))))))
cat("   Four map_ calls and it is right. purrr is a good instrument for this\n")
cat("   question and it is the question the corpus grades as `ragged by\n")
cat("   absence` — but nothing volunteered it, and on a document nobody has\n")
cat("   seen there is no reason to suspect 42 key-sets are hiding in an array.\n")

# ── Q5. value[x]. ────────────────────────────────────────────────────────────
cat("\n5. does any field change type — FHIR's value[x]:\n")
vx <- keep(u, \(k) grepl("^value[A-Z]", k))
cat(sprintf("   top level of a resource: %s\n", paste(vx, collapse = ", ")))
allv <- local({
  out <- character(0)
  rec <- function(x) if (is.list(x)) {
    nm <- names(x)
    if (!is.null(nm)) out <<- c(out, keep(nm, \(k) grepl("^value[A-Z]", k)))
    walk(x, rec)
  }
  rec(doc); sort(table(out), decreasing = TRUE)
})
cat(sprintf("   document-wide: %s\n",
            paste(sprintf("%s(%d)", names(allv), as.integer(allv)), collapse = " ")))
cat("   Eight spellings, each internally consistent by type, so nothing here\n")
cat("   changes type. purrr can COUNT them once I supply `^value[A-Z]`, which\n")
cat("   is a naming convention rather than a structural signal. Partly.\n")

# ── Q8. Three named fields. THE CONTRAST WITH 03. ────────────────────────────
cat("\n8. three named fields, one row per resource:\n")
tbl <- map_dfr(res, \(r) data.frame(
  type   = r$resourceType,
  id     = r$id,
  status = r$status %||% NA_character_))
cat(sprintf("   map_dfr -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat(sprintf("   `%%||%%` WAS REQUIRED and without it this stops: status is absent\n"))
cat(sprintf("   from %d of %d resources. On 03-natural-earth the identical\n",
            sum(is.na(tbl$status)), nrow(tbl)))
cat("   expression needed no default at all. Same tool, same three lines, and\n")
cat("   the difference is entirely the document.\n")

# What happens if you forget. Measured rather than asserted.
boom <- tryCatch({
  map_dfr(res[1:3], \(r) data.frame(type = r$resourceType, status = r$status))
  "no error"
}, error = function(e) paste("ERROR:", conditionMessage(e)))
cat(sprintf("   without the default, on the first three resources: %s\n", boom))
cat("   THE FAILURE IS THE GOOD CASE. It stops loudly on record 1. A document\n")
cat("   whose first ragged record is number 400 fails after four hundred\n")
cat("   successes, and that is the ordinary case.\n")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
cat("\n9. a field missing from some records, keeping those rows:\n")
cat(sprintf("   the map_dfr above already does it: %d rows survive, %d with NA\n",
            nrow(tbl), sum(is.na(tbl$status))))
kept <- tbl[is.na(tbl$status), ]
cat(sprintf("   the NA rows are %s\n",
            paste(sprintf("%s x%d", names(sort(table(kept$type), decreasing = TRUE)),
                          sort(table(kept$type), decreasing = TRUE)), collapse = ", ")))
cat("   AND THAT LIST IS THE ANSWER TO QUESTION 3 THE TOOL NEVER GAVE. The rows\n")
cat("   missing `status` are not scattered — they are whole resourceTypes. The\n")
cat("   raggedness is a partition wearing a disguise.\n")

cat("\n3. CANNOT. purrr offers no row candidates.\n")
cat("6. n/a — NOTES.md grades this file keys-as-data 0.\n")

cat("
CONCLUSION — the same three lines that were free on 03 cost a default here,
and the defaults are hiding the document's real structure.

  `README.md` calls purrr \"the best answer that exists\", and across four
  documents that holds. It is also now measured on both ends of the raggedness
  axis with the SAME expression: on `03-natural-earth`, `map_dfr` over 241
  features needed no `%||%` anywhere; here it needs one on every field but two,
  because only `id` and `resourceType` are present in all 564 resources.

  QUESTION 4 IS PURRR'S BEST SHOWING IN THIS CORPUS. Four `map_` calls give the
  key union, the always-present pair, the singletons and the 42 key-sets, and
  every number matches what tidyjson and jq found independently. That is a real
  answer to a real exploring question.

  THE FINDING IS UNDER QUESTION 9. The rows where `status` is NA are not
  scattered records with a missing field — **they are entire resourceTypes**,
  and the list of them is a partition of the array. `%||% NA` is doing something
  worse than papering over a hole: it is converting a structural fact into
  missing data, silently, one field at a time. The idiom that makes purrr
  pleasant on ragged JSON is the same idiom that hides why the JSON is ragged.

  That is `VERDICT.md`'s fourth operation arriving from the opposite direction.
  The probe finds the partition and reports it; purrr finds the same partition,
  spells it `NA`, and moves on.
")
