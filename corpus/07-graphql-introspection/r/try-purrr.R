# purrr — the SpaceX GraphQL API describing its own schema
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.json   143 KB, 108 types, depth 13, recursion 4,
#                                 94 paths, 22 fields, explosion 4.3, keyed 0
#  measured      2026-08-10
#  run           cd corpus/07-graphql-introspection/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           4   NO                  NO
#   2 how deep                                  2   NO                  yes
#   3 what is one record                        -   -                   CANNOT
#   4 always present vs sometimes               8   NO                  yes
#   5 does any field change type                6   YES                 partly
#   7 how many records                          1   YES                 yes
#   8 three named fields to a table             5   YES                 yes
#   9 a field missing from some rows            7   YES                 yes
#  10 flatten the deepest array                 7   YES, the recursion  yes
#  13 needed the shape in advance?                  YES for 8, 9, 10
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. purrr has now been measured on raggedness-by-absence
# (`01`, `05`), on recursion (`02`), on a flat regular document (`03`) and on
# keys-as-data (`10`). **This is the raggedness-by-NULL case**, and it is the one
# where `%||%` does something different from what it does everywhere else:
# a field that is present-and-null is not a missing field, and `%||%` cannot
# tell, because in R both arrive as NULL.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
ty  <- doc$data$`__schema`$types

cat("\n1. what is in here — str() is the only describer in reach:\n")
for (lv in c(3, 5))
  cat(sprintf("   str(max.level=%d)  %6d lines\n", lv,
              length(capture.output(str(doc, max.level = lv)))))

depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_dbl(x, depth)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion over map_dbl\n", depth(doc)))
cat(sprintf("7. %d types — after naming data$__schema$types\n", length(ty)))
cat("\n3. CANNOT. purrr offers no row candidates. A type is one defensible\n")
cat("   answer; a field is another (there are more of them); an arg is a third.\n")

# ── Q4 / Q9. THE NULL CASE, AND WHAT %||% DOES WITH IT. ──────────────────────
cat("\n4/9. always present vs sometimes:\n")
ks <- map(ty, names)
u  <- unique(flatten_chr(ks))
n  <- length(ty)
absent <- map_int(set_names(u), \(k) sum(map_lgl(ks, \(x) !(k %in% x))))
nulls  <- map_int(set_names(u), \(k) sum(map_lgl(ty, \(t) is.null(t[[k]]))))
cat("     field           absent  null\n")
for (k in u) cat(sprintf("     %-14s %5d %5d\n", k, absent[[k]], nulls[[k]]))
cat(sprintf("   NOTHING IS ABSENT (%d of %d), and %.0f%% of cells are null.\n",
            sum(absent), n * length(u), 100 * sum(nulls) / (n * length(u))))

cat("\n   AND `%||%` ERASES THE DIFFERENCE, which on this file is the whole story:\n")
got <- sum(map_lgl(ty, \(t) is.null(t$fields)))
cat(sprintf("   `t$fields %%||%% NA` fires on %d of %d types\n", got, n))
cat(sprintf("   and of those %d, ALL %d are present-and-null, none absent\n",
            got, nulls[["fields"]]))
cat("   In R a missing key and a present-but-null key are BOTH NULL, so `%||%`\n")
cat("   cannot distinguish them and neither can any purrr predicate. On\n")
cat("   05-fhir-bundle that idiom hid a partition of four resourceTypes; here\n")
cat("   it hides one too, and this time it also hides the fact that the\n")
cat("   document is not ragged at all in the sense NOTES.md grades.\n")

kind <- map_chr(ty, "kind")
cat("\n   THE NULLS ARE THE PARTITION, exactly — measured, not asserted:\n")
cat(sprintf("     kind: %s\n", paste(sprintf("%s %d", names(table(kind)),
                                             as.integer(table(kind))), collapse = ", ")))
for (k in c("fields", "interfaces", "inputFields", "enumValues", "possibleTypes")) {
  who <- unique(kind[map_lgl(ty, \(t) !is.null(t[[k]]))])
  cat(sprintf("     %-14s non-null only on: %s\n", k,
              if (length(who)) paste(who, collapse = ", ") else "(nothing)"))
}
cat("   Fourth document in three days where apparent raggedness is a partition\n")
cat("   wearing a disguise, and the second where the disguise is `null`.\n")

# ── Q5. ──────────────────────────────────────────────────────────────────────
cat("\n5. does any field change type:\n")
cls <- map(set_names(u), \(k)
  unique(map_chr(ty, \(t) if (is.null(t[[k]])) "null" else class(t[[k]])[1])))
varying <- names(cls)[map_lgl(cls, \(x) length(setdiff(x, "null")) > 1)]
cat(sprintf("   fields with more than one NON-NULL class: %s\n",
            if (length(varying)) paste(varying, collapse = ", ") else "none"))
cat("   NOTES.md grades this file `polymorphic 0` and purrr agrees, which is\n")
cat("   worth recording because rrapply's level-count test does NOT — it\n")
cat("   reports six populations here. See try-rrapply.R.\n")

# ── Q8 / Q10. ────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per type:\n")
tbl <- map_dfr(ty, \(t) data.frame(
  kind = t$kind, name = t$name, n_fields = length(t$fields)))
cat(sprintf("   map_dfr -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))

cat("\n10. flatten the deepest array — the ofType chains:\n")
unwrap <- function(x, acc = character(0))
  if (is.null(x)) acc else unwrap(x$ofType, c(acc, x$kind))
chains <- map_dfr(ty, \(t) map_dfr(t$fields %||% list(), \(f) data.frame(
  type = t$name, field = f$name,
  chain = paste(unwrap(f$type), collapse = " > "))))
cat(sprintf("   %d fields across %d types, each with its full type chain\n",
            nrow(chains), n))
print(utils::head(chains[nchar(chains$chain) > 20, ], 3))
cat("   THE `unwrap` RECURSION IS THE COST, and it is the same shape as\n")
cat("   02-hn-thread's walker: purrr has no verb for following a self-similar\n")
cat("   link, so questions about `ofType` need base-R recursion first and\n")
cat("   purrr afterwards.\n")

cat("\n6. n/a — NOTES.md grades this file keys-as-data 0.\n")

cat("
CONCLUSION — the raggedness-by-null case, and `%||%` is blind to it by
construction rather than by oversight.

  This document is **0% ragged by absence and 51.7% null**. In R both a missing
  key and a present-but-null key evaluate to `NULL`, so `%||%` — the idiom that
  makes purrr pleasant on ragged JSON — cannot tell them apart, and neither can
  any predicate built on it. That is not a defect in purrr; it is R's value model
  meeting JSON's, and it means **no purrr expression can distinguish `this type
  has no fields` from `this key was never emitted`.**

  **And once again the nulls are a partition.** `fields` and `interfaces` are
  non-null only on OBJECTs, `inputFields` only on INPUT_OBJECTs, `enumValues`
  only on ENUMs, `possibleTypes` on nothing at all. `kind` predicts every null in
  the document. That is the fourth document in three days where apparent
  raggedness turned out to be a partition wearing a disguise — after
  `05-fhir-bundle`'s four whole resourceTypes, `10-wikidata`'s `somevalue` snak
  and this file's own jq attempt — and the second where the disguise is `null`.

  **purrr agrees with the grading on question 5 where rrapply does not.** It
  reports no field with more than one non-null class, matching `polymorphic 0`.
  rrapply's level-count test reports six populations on the same document. When
  two instruments disagree the document is the tiebreak, and here the document
  says purrr is right.

  QUESTION 10 COST A RECURSION, exactly as on `02-hn-thread`. `ofType` is a
  self-similar link and purrr has no verb for following one, so the six-line
  `unwrap` comes first and `map_dfr` comes after. **Recursion costs purrr the
  list itself; raggedness costs it a default per field; null-raggedness costs it
  a distinction it cannot make at all.** Five documents, three different kinds of
  bill.
")
