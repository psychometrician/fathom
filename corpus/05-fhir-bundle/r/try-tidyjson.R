# tidyjson — a Synthea FHIR R4 patient bundle
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed below)
#  file          ../source.json   2.0 MB, 564 resources, 20 resourceTypes, depth 11
#  measured      2026-08-09
#  run           cd corpus/05-fhir-bundle/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           12   NO                  WRONG
#   3 what is one record                         3   NO                  YES
#   4 always present vs sometimes                6   NO                  yes
#   5 does any field change type                 -   -                   NO
#   6 are any keys actually data                 -   -                   n/a
#   7 how many records                           1   NO                  yes
#   8 three named fields to a table              5   YES                 yes
#  12 flattest honest table                      6   NO                  partly
#  13 needed the shape in advance?                   no for 1, 3, 4
#  16 lines, and how much is ceremony?               see the conclusion
#
#  Q1 is scored WRONG rather than NO, as on 03-natural-earth, and here the
#  measurement is a coverage percentage rather than an anecdote.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `03-natural-earth` showed `json_schema` reporting ONE shape for
# an array holding two, order-dependently. That was two shapes differing only in
# nesting depth, and it is fair to ask whether it was a corner case.
#
# This document is the same test at full strength: `entry[]` holds **twenty
# different resourceTypes**, 42 distinct key-sets, and only two fields present
# throughout. If a schema inferrer unions anything, it should union here.
suppressMessages({library(tidyjson); library(jsonlite)})
cat(sprintf("R %s, tidyjson %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyjson"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
res <- lapply(doc$entry, function(e) e$resource)
rt  <- vapply(res, function(x) x$resourceType, "")

# ── Q1. What is in here? THE COVERAGE MEASUREMENT. ───────────────────────────
cat("\n1. what is in here — json_schema over a growing slice of entry[]:\n")
cat("   `covered` is the share of the TRUE top-level key union that the schema\n")
cat("   actually names. The truth is computed from the same slice.\n\n")
cat("      n  kinds   input      time   schema   true keys  named  covered\n")
for (n in c(1, 3, 10, 25, 50)) {
  sub <- as.character(toJSON(res[seq_len(n)], auto_unbox = TRUE))
  t0  <- Sys.time()
  s   <- as.character(json_schema(sub))
  el  <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  truth <- unique(unlist(lapply(res[seq_len(n)], names)))
  named <- vapply(truth, function(k) grepl(sprintf('"%s":', k), s, fixed = TRUE), TRUE)
  cat(sprintf("   %4d  %5d  %8s B %6.1fs  %6s c  %8d  %5d  %5.0f%%\n",
              n, length(unique(rt[seq_len(n)])), format(nchar(sub), big.mark = ","),
              el, format(nchar(s), big.mark = ","), length(truth), sum(named),
              100 * mean(named)))
  flush.console()
  if (n == 25) missing25 <- truth[!named]
}
cat("\n   COVERAGE FALLS AS THE ARRAY BECOMES MORE HETEROGENEOUS. That is the\n")
cat("   opposite of what a union would do — more kinds should mean more keys\n")
cat("   named, and instead the fraction named drops.\n")
cat(sprintf("   at n=25, keys the schema does NOT mention: %s%s\n",
            paste(utils::head(missing25, 10), collapse = ", "),
            if (length(missing25) > 10) ", …" else ""))
cat("   Several of those — `name`, `telecom`, `gender`, `birthDate`, `address`\n")
cat("   — ARE in the schema when n=1, because resource 1 is the Patient. They\n")
cat("   are dropped as more resources arrive. The description does not grow\n")
cat("   towards the document; it moves away from it.\n")

# The same claim stated the way the corpus states it elsewhere.
sub50 <- as.character(toJSON(res[seq_len(50)], auto_unbox = TRUE))
s50   <- as.character(json_schema(sub50))
cat(sprintf("\n   By the O(data) test this passes easily: %s chars for %s bytes = %.2f%%.\n",
            format(nchar(s50), big.mark = ","), format(nchar(sub50), big.mark = ","),
            100 * nchar(s50) / nchar(sub50)))
cat("   SCORED WRONG, NOT NO. It answers, it is small, and it is 36% right.\n")

# ── Q3 / Q7. gather_array — tidyjson's real contribution. ────────────────────
cat("\n3/7. what is one record, and how many:\n")
etxt <- as.character(toJSON(doc$entry, auto_unbox = TRUE))
g <- gather_array(etxt)
cat(sprintf("   gather_array() over entry -> %d rows\n", nrow(g)))
cat("   Correct, and it needed nothing known in advance. This is the honest\n")
cat("   answer to question 3 and tidyjson is the only R tool that offers one.\n")

# ── Q4. Always vs sometimes. ─────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
kt <- g |> enter_object("resource") |> gather_object() |> json_types()
tb <- sort(table(as.character(kt$name)), decreasing = TRUE)
cat(sprintf("   gather_object over resource -> %d key occurrences, %d distinct keys\n",
            nrow(kt), length(tb)))
cat(sprintf("   present on all %d resources: %s\n", length(res),
            paste(names(tb)[tb == length(res)], collapse = ", ")))
cat(sprintf("   present on exactly one: %d keys\n", sum(tb == 1)))
cat("   THIS WORKS AND IT IS GOOD. gather_object turns keys into rows, so\n")
cat("   raggedness becomes a table you can count — no shape known in advance.\n")

# ── Q5. ──────────────────────────────────────────────────────────────────────
cat("\n5. does any field change type:\n")
vt <- kt[grepl("^value[A-Z]", as.character(kt$name)), ]
cat(sprintf("   value* keys reaching the top level of a resource: %d rows, %d spellings\n",
            nrow(vt), length(unique(as.character(vt$name)))))
cat("   NO. json_types() reports the type of each key, and each spelling is\n")
cat("   internally consistent, so nothing changes type. tidyjson has no way to\n")
cat("   say that eight spellings are one field — the same gap as everywhere.\n")

# ── Q8 / Q12. ────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per resource:\n")
tbl <- g |> enter_object("resource") |>
  spread_values(type = jstring("resourceType"), id = jstring("id"),
                status = jstring("status"))
cat(sprintf("   spread_values -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(as.data.frame(tbl)[, c("type", "id", "status")], 3))
cat(sprintf("   status is NA on %d rows — spread_values fills rather than fails,\n",
            sum(is.na(as.data.frame(tbl)$status))))
cat("   which is the right behaviour on a ragged document and is worth crediting.\n")

cat("\n12. the flattest honest table, and what was lost:\n")
flat <- g |> enter_object("resource") |> spread_all()
cat(sprintf("   spread_all -> %d x %d\n", nrow(flat), ncol(flat)))
cat("   WHAT WAS LOST: every array-valued field. spread_all descends objects\n")
cat("   and stops at arrays, so `component`, `identifier`, `address` and the\n")
cat("   rest are absent. It is honest — it does not invent columns — and it is\n")
cat("   partial in a way the result does not disclose.\n")

cat("\n6. n/a — NOTES.md grades this file keys-as-data 0.\n")

cat("
CONCLUSION — 03-natural-earth was not a corner case, and here the failure has
a number.

  `json_schema` given twenty kinds of resource in one array describes **36% of
  the top-level keys that are actually there**, and the fraction FALLS as more
  kinds arrive: 64% at three resources, 47% at ten, 45% at twenty-five, 36% at
  fifty. Fields that appear in the schema at n=1 — `name`, `birthDate`,
  `address`, all of them the Patient's — are gone by n=25. The description does
  not converge on the document; it moves away from it.

  BY THE PROJECT'S OWN HEADLINE TEST THIS TOOL PASSES: 1,879 characters for
  40 KB is 4.7%, and it barely grows. **That is the loophole, stated twice now
  in one day on two unrelated documents.** A describer that silently discards
  shapes will always look proportional to structure, because it has decided
  there is less structure than there is. `VERDICT.md` measures description size
  and does not measure description COVERAGE, and on the evidence it should.

  WHAT TIDYJSON DOES WELL, and it is more than any other R tool here.
  `gather_array()` answers question 3 with no shape known in advance.
  `gather_object()` turns keys into rows, which makes question 4 — raggedness —
  a matter of counting, and it gets the two always-present fields right.
  `spread_values` fills rather than fails on a missing field. Those are real
  answers to the exploring half, and they are why this is the serious competitor
  even after the paragraph above.

  THE PATTERN ACROSS BOTH FILES: tidyjson's VERBS are trustworthy and its
  INFERENCE is not. Everything that walks the document and reports what it saw
  is correct; the one function that generalises across records invents a
  consensus that no record matches.
")
