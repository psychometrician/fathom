# jsonlite — a Synthea FHIR R4 patient bundle
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   2.0 MB, 564 resources, 20 resourceTypes, depth 11
#  measured      2026-08-09
#  run           cd corpus/05-fhir-bundle/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              4   NO                  PARTLY
#   1 what is in here                            5   NO                  NO
#   2 how deep                                   2   NO                  yes
#   3 what is one record                         8   NO                  WRONG
#   4 always present vs sometimes                6   NO                  YES
#   5 does any field change type                 9   YES                 NO
#   6 are any keys actually data                 -   -                   n/a
#   7 how many records                           1   NO                  yes
#   8 three named fields to a table              5   YES, painfully      partly
#  12 flattest honest table                      5   NO                  WRONG
#  13 needed the shape in advance?                   no — and that is the trap
#  16 lines, and how much is ceremony?               see the conclusion
#
#  Q3 and Q12 are scored WRONG rather than NO. jsonlite does not decline; it
#  returns a table, and the table is the move `design/probe.py`'s fourth
#  operation exists to refuse.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE, AND WHY IT PAIRS WITH 03. On `03-natural-earth` jsonlite's
# simplification was the SAFE choice: it preserved a 3-deep/4-deep split that
# polars erased. This document is the same mechanism pointed at a harder array —
# `entry[]` holds **20 different resourceTypes**, 42 distinct key-sets, and
# exactly two fields present in all 564 records.
#
# `VERDICT.md`'s fourth operation says: partition on a discriminator BEFORE
# folding, because folding genuinely different things together produces a table
# that is mostly holes. jsonlite folds unconditionally. This file measures what
# that costs.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.json"
cat(sprintf("  file is %.1f MB\n", file.size(path) / 1024^2))

# ── Q0. Is this sound? ───────────────────────────────────────────────────────
cat("\n0. is this sound:\n")
raw <- readChar(path, file.size(path), useBytes = TRUE)
cat(sprintf("   validate() %s — well-formedness only, as on 03-natural-earth.\n",
            validate(raw)))
cat("   The four silent damages behave identically here and are not re-measured:\n")
cat("   duplicate keys resolve to the FIRST (Python takes the last), integers\n")
cat("   past 2^53 round to a double, NaN and Infinity are refused. See\n")
cat("   ../../03-natural-earth/r/try-jsonlite.R for the measurement.\n")

simp <- fromJSON(path)
doc  <- fromJSON(path, simplifyVector = FALSE)

# ── Q1 / Q2. ─────────────────────────────────────────────────────────────────
cat("\n1. what is in here — str() is the only describer jsonlite has:\n")
for (lv in 2:4)
  cat(sprintf("   str(simplified, max.level=%d)  %6d lines\n", lv,
              length(capture.output(str(simp, max.level = lv)))))
cat(sprintf("   str(simplified) whole          %6d lines\n",
            length(capture.output(str(simp)))))

cat("\n2. how deep does it go:\n")
depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("   %d levels, hand-written recursion\n", depth(doc)))

# ── Q3. WHAT IS ONE RECORD. THE QUESTION THIS FILE DECIDES. ──────────────────
cat("\n3. what is one record — jsonlite answers without being asked:\n")
cat(sprintf("   $entry is a %s: %d x %d (%s)\n", class(simp$entry)[1],
            nrow(simp$entry), ncol(simp$entry),
            paste(names(simp$entry), collapse = ", ")))
res <- simp$entry$resource
cat(sprintf("   $entry$resource is a NESTED data frame: %d x %d\n",
            nrow(res), ncol(res)))

# The honest fill measurement, taken from the unsimplified parse where a key is
# either present or it is not. The simplified frame cannot answer this, because
# a nested data-frame column has a row for every record whether or not the
# record had the field.
rl <- lapply(doc$entry, function(e) e$resource)
ks <- lapply(rl, names)
u  <- unique(unlist(ks))
present <- sum(vapply(ks, length, 0L))
cells   <- length(rl) * length(u)
cat(sprintf("   union of keys: %d.  cells present %s of %s\n",
            length(u), format(present, big.mark = ","), format(cells, big.mark = ",")))
cat(sprintf("   THE TABLE IS %.1f%% EMPTY.\n", 100 * (1 - present / cells)))
always <- u[vapply(u, function(k) all(vapply(ks, function(x) k %in% x, TRUE)), TRUE)]
cat(sprintf("   fields present in ALL %d records: %s — and that is all of them\n",
            length(rl), paste(always, collapse = ", ")))
cat(sprintf("   distinct key-sets: %d\n",
            length(unique(vapply(ks, function(x) paste(sort(x), collapse = ","), "")))))
rt <- vapply(rl, function(x) x$resourceType, "")
cat(sprintf("   resourceType takes %d values: %s\n", length(unique(rt)),
            paste(sprintf("%s %d", names(sort(table(rt), decreasing = TRUE))[1:5],
                          sort(table(rt), decreasing = TRUE)[1:5]), collapse = ", ")))
cat("   SCORED WRONG. jsonlite did not decline — it built a 97-column table\n")
cat("   that is 87% holes by folding 20 different kinds of thing together.\n")
cat("   VERDICT.md's fourth operation exists to refuse exactly this move, and\n")
cat("   the discriminator that would fix it — resourceType — is sitting in the\n")
cat("   frame as a column, unused.\n")

# ── Q4. Always vs sometimes — and here jsonlite CAN answer. ──────────────────
cat("\n4. always present vs sometimes:\n")
n_some <- length(u) - length(always)
cat(sprintf("   %d of %d fields are absent from at least one record\n",
            n_some, length(u)))
cat("   AND ON THIS FILE THE ANSWER IS TRUSTWORTHY, unlike 03-natural-earth.\n")
cat("   There the NA in a simplified column could mean absent OR null and the\n")
cat("   two could not be separated. NOTES.md grades this file `ragged by null:\n")
cat("   0` — FHIR omits rather than nulls — so every NA here means absent.\n")
cat("   That is a property of the DOCUMENT rescuing the tool, not the tool.\n")

# ── Q5. value[x]: the path variance this file was chosen for. ────────────────
cat("\n5. does any field change type — FHIR's value[x]:\n")
vcols <- grep("^value", names(res), value = TRUE)
cat(sprintf("   resource has %d columns starting `value`: %s\n",
            length(vcols), paste(vcols, collapse = ", ")))
cat("   — but the simplified frame only shows the ones at the TOP level of a\n")
cat("   resource. The rest are nested, so the honest count needs a recursion,\n")
cat("   which is itself the point: jsonlite has no way to ask this.\n")
acc <- new.env(); acc$v <- character(0)
rec <- function(x) {
  if (is.list(x)) {
    n <- names(x)
    if (!is.null(n)) acc$v <- c(acc$v, grep("^value[A-Z]", n, value = TRUE))
    for (e in x) rec(e)
  }
}
rec(doc)
tv <- sort(table(acc$v), decreasing = TRUE)
cat(sprintf("   document-wide, by hand: %d spellings — %s\n", length(tv),
            paste(sprintf("%s(%d)", names(tv), as.integer(tv)), collapse = " ")))
cat("   EACH SPELLING IS ITS OWN COLUMN AND NOTHING RELATES THEM. By type each\n")
cat("   is consistent, so a type-based check sees no polymorphism — which is\n")
cat("   what NOTES.md predicted and what makes this file's variance invisible.\n")
cat("   This is `first_present`'s justification, restated from the R side.\n")

# ── Q7 / Q8. ─────────────────────────────────────────────────────────────────
cat(sprintf("\n7. %d entries\n", nrow(simp$entry)))

cat("\n8. three named fields, one row per resource:\n")
tbl <- data.frame(
  type = res$resourceType,
  id   = res$id,
  # `status` exists on many resourceTypes and not all — the third field has to
  # be chosen knowing the document, which is Q13's answer in one line.
  status = if ("status" %in% names(res)) res$status else NA_character_)
cat(sprintf("   data.frame(res$resourceType, res$id, res$status) -> %d x %d\n",
            nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat(sprintf("   status is NA on %d of %d rows, because it is not a field every\n",
            sum(is.na(tbl$status)), nrow(tbl)))
cat("   resourceType has. Two of the three columns are the only two fields the\n")
cat("   document guarantees; there is no third safe choice.\n")

# ── Q12. The flattest honest table. ──────────────────────────────────────────
cat("\n12. the flattest honest table, and what was lost:\n")
flat <- jsonlite::flatten(res)
lc <- names(flat)[vapply(flat, function(c) is.list(c) && !is.data.frame(c), TRUE)]
cat(sprintf("   jsonlite::flatten(resource) -> %d x %d\n", nrow(flat), ncol(flat)))
cat(sprintf("   list-columns remaining: %d (%s%s)\n", length(lc),
            paste(utils::head(lc, 6), collapse = ", "),
            if (length(lc) > 6) ", …" else ""))
cat("   WRONG in the same way as question 3: wider, still 20 kinds deep, and\n")
cat("   still one table. Flattening a heterogeneous array makes the holes more\n")
cat("   numerous rather than fewer.\n")

cat("
CONCLUSION — the same feature that made jsonlite the SAFE choice on
03-natural-earth makes it the dangerous one here, and that is the finding.

  On the GeoJSON file, simplification stopped at a ragged boundary and preserved
  a polymorphism polars had erased. **The rule that produced that good outcome is
  \"build the widest table that fits\", and on this document it produces a 564 x 97
  frame that is 87.2% empty** — twenty different kinds of resource folded into
  one shape, with exactly two fields (`resourceType`, `id`) present throughout.

  `VERDICT.md`'s fourth operation is the answer to precisely this, and it was
  added because of this file: partition on a discriminator, then fold. jsonlite
  performs the fold and never considers the partition, **and the discriminator is
  right there as a column of the frame it just built.** Nothing warns. The result
  is a valid data frame, and a person who did not already know FHIR would read
  87% NA as \"this patient has little data\" rather than \"these are twenty
  different tables stacked\".

  WHERE IT IS BETTER THAN ON 03: question 4 is trustworthy here. NA means absent
  because FHIR omits rather than nulls — a property of the document, not of the
  tool, and it is recorded that way.

  ON QUESTION 5 IT HAS NOTHING. The eight spellings of `value[x]` are eight
  columns, each internally consistent, and no operation in jsonlite can ask for
  \"the value, whatever it is called\". That is `first_present`'s case made from
  the R side, and it is the same gap `rows()` hit on its first cold run.
")
