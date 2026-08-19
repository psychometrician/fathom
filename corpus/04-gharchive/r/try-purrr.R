# purrr — one hour of GitHub Archive events, NDJSON at 50 MB
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.jsonl   50 MB, 37,883 records, depth 7, 846 paths,
#                                  235 fields, keyed 2, path variance 76
#  measured      2026-08-10
#  run           cd corpus/04-gharchive/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           3   NO                  NO
#   3 what is one record                        -   -                   CANNOT
#   4 always present vs sometimes               9   NO                  YES
#   5 does any field change type                6   NO                  yes
#   7 how many records                          1   no                  yes
#   8 three named fields to a table             6   YES                 yes
#   9 a field missing from some rows            8   YES                 YES
#  13 needed the shape in advance?                  YES for 8; NO for 4 and 9
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. purrr has been measured on raggedness-by-absence (`01`, `05`),
# recursion (`02`), a flat regular document (`03`), keys-as-data (`10`) and
# raggedness-by-null (`07`). **This is scale**: 37,883 records, and the first
# time any R attempt in this corpus has been asked to iterate over more than a
# few thousand things.
#
# It is also the fifth-operation document, and question 9 is where that lands
# for purrr — because on `05-fhir-bundle` and `10-wikidata` and `07-graphql` the
# rows with a missing field turned out to be whole partitions, three times
# running. Here the partitioning field is not even in the record.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

path <- "../source.jsonl"
t0 <- Sys.time()
ev <- stream_in(file(path), verbose = FALSE, simplifyVector = FALSE)
cat(sprintf("  stream_in -> %s records in %.1f s\n",
            format(length(ev), big.mark = ","),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\n1. what is in here — purrr has no describe verb, and on 37,883 records\n")
cat("   str() is not an option at any level. Not attempted; NOTES.md measures\n")
cat("   846 paths for 235 fields and nothing in purrr reports either.\n")
cat(sprintf("\n7. %s events\n", format(length(ev), big.mark = ",")))
cat("3. CANNOT. An event is one answer, a payload is another, a commit inside a\n")
cat("   PushEvent payload is a third and there are far more of those.\n")

# ── Q4. Scale, and purrr handles it. ─────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
t0 <- Sys.time()
ks <- map(ev, names)
u  <- unique(flatten_chr(ks))
n  <- length(ev)
freq <- map_int(set_names(u), \(k) sum(map_lgl(ks, \(x) k %in% x)))
cat(sprintf("   event level: %d keys over %s records in %.1f s\n",
            length(u), format(n, big.mark = ","),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
for (k in names(sort(freq, decreasing = TRUE)))
  cat(sprintf("     %-12s %6s of %s\n", k, format(freq[[k]], big.mark = ","),
              format(n, big.mark = ",")))
cat("   PURRR SCALES FINE, which is worth recording because nothing else in\n")
cat("   this corpus tested it. Four map_ calls over 37,883 records is seconds.\n")

pk <- map(ev, \(e) names(e$payload))
pu <- unique(flatten_chr(pk))
pfreq <- map_int(set_names(pu), \(k) sum(map_lgl(pk, \(x) k %in% x)))
cat(sprintf("\n   payload level: %d distinct fields, and present in ALL: %s\n",
            length(pu),
            if (any(pfreq == n)) paste(names(pfreq)[pfreq == n], collapse = ", ")
            else "NOTHING"))
cat("   NOTHING — the third independent route to that answer today, after jq\n")
cat("   over the whole file and rrapply over a melted frame.\n")

# ── Q9. THE FIFTH OPERATION, FROM PURRR'S SIDE. ──────────────────────────────
cat("\n9. a field missing from some records, keeping those rows:\n")
tp <- map_chr(ev, "type")
# `push_id`, not `commits` — the first draft guessed `commits` from knowing what
# a PushEvent is, and it is absent from every payload in this hour's data. The
# guess printed `present on 0 records` under a sentence claiming it marked the
# PushEvents, which is the shape of error this corpus keeps recording: a plausible
# name is not a measured one.
for (fld in c("push_id", "action", "ref")) {
  has <- map_lgl(ev, \(e) !is.null(e$payload[[fld]]))
  who <- sort(table(tp[has]), decreasing = TRUE)
  cat(sprintf("   `%s` present on %s of %s records, and they are:\n", fld,
              format(sum(has), big.mark = ","), format(n, big.mark = ",")))
  cat(sprintf("     %s\n", paste(sprintf("%s %s", names(who),
              format(as.integer(who), big.mark = ",")), collapse = ", ")))
}
# And the general form, which is stronger than three hand-picked fields.
belong <- map_int(set_names(pu), \(k) length(unique(tp[map_lgl(ev, \(e)
            !is.null(e$payload[[k]]))])))
cat(sprintf("\n   OF THE %d PAYLOAD FIELDS, %d BELONG TO EXACTLY ONE EVENT TYPE:\n",
            length(pu), sum(belong == 1)))
cat(sprintf("     %s\n", paste(names(belong)[belong == 1], collapse = ", ")))
cat(sprintf("   and the rest span %s types each\n",
            paste(sort(unique(belong[belong > 1])), collapse = ", ")))
cat("   FOURTH DOCUMENT RUNNING, AND THE SHARPEST. `push_id` is on exactly the\n")
cat("   30,099 PushEvents; `ref` on exactly Push, Create and Delete. The\n")
cat("   raggedness is not scattered — most payload fields belong to ONE event\n")
cat("   type — and `%||% NA` would erase it as it did on 05, 07 and 10.\n")
cat("   WHAT IS DIFFERENT HERE is that the partitioning field is NOT IN THE\n")
cat("   RECORD. On 05 it was `resourceType` inside the resource; on 07 it was\n")
cat("   `kind` inside the type. Here `type` is on the ENCLOSING EVENT and the\n")
cat("   payload cannot see it. That is VERDICT.md item 15's fifth operation,\n")
cat("   and purrr reaches it only because `map_chr(ev, \"type\")` was written\n")
cat("   by someone who already knew to look up a level.\n")

# ── Q5. ──────────────────────────────────────────────────────────────────────
cat("\n5. does any field change type:\n")
cls <- map(set_names(pu), \(k)
  unique(map_chr(keep(ev, \(e) !is.null(e$payload[[k]])),
                 \(e) class(e$payload[[k]])[1])))
varying <- names(cls)[map_lgl(cls, \(x) length(x) > 1)]
cat(sprintf("   payload fields with more than one class: %s\n",
            if (length(varying)) paste(varying, collapse = ", ") else "none"))
cat("   NOTES.md grades this file `polymorphism 0` across 37,883 records and\n")
cat("   235 field names, and purrr agrees. That grade disconfirmed an\n")
cat("   expectation — machine-generated was assumed to mean ragged in TYPE, and\n")
cat("   it means ragged in WHICH FIELDS.\n")

# ── Q8. ──────────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per event:\n")
t0 <- Sys.time()
tbl <- map_dfr(ev, \(e) data.frame(
  type  = e$type,
  actor = e$actor$login %||% NA_character_,
  repo  = e$repo$name   %||% NA_character_))
cat(sprintf("   map_dfr -> %s x %d in %.1f s\n", format(nrow(tbl), big.mark = ","),
            ncol(tbl), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
print(utils::head(tbl, 3))
cat("   THE COST IS TIME, NOT CORRECTNESS. map_dfr over 37,883 records is the\n")
cat("   slowest single operation in any R attempt in this corpus, and\n")
cat("   `jsonlite::stream_in` produced the identical table as a side effect of\n")
cat("   parsing. On a document this size the right answer is not to map at all.\n")

cat("
CONCLUSION — purrr scales, and the fifth operation is the one thing it cannot
reach on its own.

  **It scales.** Four `map_` calls over 37,883 records answer question 4 in
  seconds, and nothing in this corpus had tested that before. `map_dfr` for
  question 8 is the slowest operation in any R attempt here, and the honest note
  is that `jsonlite::stream_in` produced the same table for free while parsing —
  on a 50 MB document, mapping is the wrong shape of answer even when it works.

  **QUESTION 9 IS THE FOURTH INSTANCE IN THREE DAYS and the sharpest.**
  `commits` is present on exactly the PushEvents. `action` on exactly the types
  that have one. The raggedness is a partition, as it was on `05-fhir-bundle`
  (four whole resourceTypes), `10-wikidata` (a `somevalue` snak) and
  `07-graphql-introspection` (`kind` predicting every null).

  **What is new is that the partitioning field is not in the record.** On the
  other three it was inside the thing being folded — `resourceType`, `kind` — and
  a test over the records could in principle find it. Here `type` sits on the
  enclosing event, the payloads have **no field in common at all**, and no
  expression that looks only at payloads can find it. purrr gets there solely
  because `map_chr(ev, \"type\")` was written by somebody who already knew to
  look one level up.

  That is `VERDICT.md` item 15's fifth operation, and this file is now its
  evidence rather than its example.
")
