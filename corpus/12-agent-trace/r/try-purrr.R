# purrr — a scrubbed Claude Code transcript, NDJSON, 1,953 records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.jsonl  4.8 MB, NDJSON, 1,953 records, depth 10,
#                                 452 paths, 151 fields, polymorphic 4
#  measured      2026-08-10
#  run           cd corpus/12-agent-trace/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           2   NO                  NO
#   2 how deep                                  2   NO                  yes
#   3 what is one record                        -   -                   CANNOT
#   4 always present vs sometimes               6   NO                  yes
#   5 does any field change type                6   NO                  yes
#   7 how many records                          1   no                  yes
#   8 three named fields to a table             6   YES                 yes
#   9 a field missing from some rows            9   YES                 YES
#  13 needed the shape in advance?                  YES for 8 and 9
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. Question 9 has now been the interesting one four times running
# — on `05-fhir-bundle` the rows missing `status` were four whole
# resourceTypes, on `10-wikidata` the one missing `datavalue` was a `somevalue`
# snak, on `07-graphql` `kind` predicted every null, on `04-gharchive` 13 of 25
# payload fields belonged to exactly one event type.
#
# **This is the fifth, and the partitioning field is a SIBLING** rather than a
# parent or a member of the record. Whether `%||% NA` erases it in the same way
# is the question.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

ln  <- readLines("../source.jsonl", warn = FALSE)
doc <- lapply(ln, fromJSON, simplifyVector = FALSE)
cat(sprintf("  %s records\n", format(length(doc), big.mark = ",")))

cat("\n1. what is in here — str() is not attempted on 1,953 nested records.\n")
cat("   NOTES.md measures 452 paths and 151 fields; purrr reports neither.\n")
depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_dbl(x, depth)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion\n", max(map_dbl(doc, depth))))
cat(sprintf("7. %s records\n", format(length(doc), big.mark = ",")))
cat("3. CANNOT. A transcript record is one answer; a content block is another\n")
cat("   and there are more of them; a tool input is a third.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
ks <- map(doc, names)
u  <- unique(flatten_chr(ks)); n <- length(doc)
freq <- map_int(set_names(u), \(k) sum(map_lgl(ks, \(x) k %in% x)))
cat(sprintf("   %d top-level keys, present in ALL: %s\n", length(u),
            paste(names(freq)[freq == n], collapse = ", ")))
cat(sprintf("   %d keys appear on fewer than half the records\n", sum(freq < n / 2)))

# ── Q5. ──────────────────────────────────────────────────────────────────────
cat("\n5. does any field change type:\n")
ct <- map_chr(doc, \(x) {
  m <- x$message
  if (!is.list(m)) return("no message")
  if (is.null(m$content)) "absent" else if (is.character(m$content)) "string" else "array"
})
cat(sprintf("   message.content: %s\n",
            paste(sprintf("%s x%s", names(table(ct)),
                          format(as.integer(table(ct)), big.mark = ",")), collapse = ", ")))
cat("   YES, in one map_chr — once you know to ask about `message.content`.\n")
cat("   purrr has no verb that finds a polymorphic field; it has verbs that\n")
cat("   count one after you name it.\n")

# ── Q8 / Q9. THE SIBLING DISCRIMINATOR, FROM PURRR'S SIDE. ──────────────────
cat("\n8/9. tool inputs, and the field that explains them:\n")
blocks <- doc |>
  map(\(x) { m <- x$message; if (is.list(m) && is.list(m$content)) m$content else list() }) |>
  list_flatten() |>
  keep(\(b) is.list(b) && !is.null(b$input))
cat(sprintf("   %d content blocks carry an `input`\n", length(blocks)))

iks <- map(blocks, \(b) names(b$input))
iu  <- unique(flatten_chr(iks))
ifreq <- map_int(set_names(iu), \(k) sum(map_lgl(iks, \(x) k %in% x)))
cat(sprintf("   %d distinct input fields; present in ALL: %s\n", length(iu),
            if (any(ifreq == length(blocks)))
              paste(names(ifreq)[ifreq == length(blocks)], collapse = ", ") else "NOTHING"))
cat("   NOTHING — the third independent route to that answer, after jq over the\n")
cat("   whole file and the melted frame in try-rrapply.R.\n")

nm <- map_chr(blocks, \(b) b$name %||% NA_character_)
cat(sprintf("\n   the SIBLING `name`: %s\n",
            paste(sprintf("%s %d", names(sort(table(nm), decreasing = TRUE))[1:4],
                          sort(table(nm), decreasing = TRUE)[1:4]), collapse = ", ")))
belong <- map_int(set_names(iu), \(k)
  length(unique(nm[map_lgl(blocks, \(b) !is.null(b$input[[k]]))])))
cat(sprintf("   of the %d input fields, %d belong to exactly ONE tool name:\n",
            length(iu), sum(belong == 1)))
cat(sprintf("     %s\n", paste(names(belong)[belong == 1], collapse = ", ")))
cat("   FIFTH DOCUMENT RUNNING, AND THE PARTITIONING FIELD IS A SIBLING. On\n")
cat("   05-fhir-bundle it was `resourceType` INSIDE the record; on 04-gharchive\n")
cat("   the enclosing event's `type`; here `name`, a key of the same object as\n")
cat("   `input` but not of `input` itself.\n")
cat("   `b$input$old_string %||% NA` would turn `this is an Edit` into a hole,\n")
cat("   exactly as `%||%` did on the other four.\n")

cat("
CONCLUSION — the fifth instance of raggedness-as-partition, and the first where
the explaining field is a sibling.

  **Zero fields are present in every tool input**, over a union of 15 — reached
  here by `map`, and independently by jq and by a melted frame. And most input
  fields belong to exactly one tool: `command` is Bash's, `old_string` is
  Edit's, and nothing is common to both.

  **The partitioning field is `name`, a sibling.** Across five documents now:

    05-fhir-bundle   `resourceType`  INSIDE the record
    07-graphql       `kind`          INSIDE the record
    10-wikidata      `snaktype`      INSIDE the record
    04-gharchive     `type`          on the PARENT
    12-agent-trace   `name`          a SIBLING key

  The first three are reachable by a test over the records being folded. **The
  last two are not**, and they are not the same relationship either — which is
  why `VERDICT.md` item 15's wording, *discriminator-on-the-parent*, is too
  narrow. The property they share is that the field is **outside the record**.

  AND `%||% NA` ERASES IT EVERY TIME. `b$input$old_string %||% NA` converts
  *this is an Edit* into a missing value, silently, one field at a time. That is
  the fifth document in four days on which the idiom that makes purrr pleasant
  on ragged JSON is the idiom that hides why the JSON is ragged.
")
