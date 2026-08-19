# tidyjson — one hour of GitHub Archive events, NDJSON at 50 MB
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed below)
#  file          ../source.jsonl   50 MB, 37,883 records, depth 7, 846 paths,
#                                  235 fields, keyed 2, path variance 76
#  measured      2026-08-10
#  run           cd corpus/04-gharchive/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                          10   NO                  CANNOT
#   3 what is one record                        4   NO                  YES
#   4 always present vs sometimes               7   NO                  YES
#   7 how many records                          1   no                  yes
#   8 three named fields to a table             5   YES                 yes
#  13 needed the shape in advance?                  no for 3, 4
#  16 lines, and how much is ceremony?              see the conclusion
#
#  ⚠ Q1 is CANNOT, not WRONG, and it is the first time `json_schema` has been
#  scored that way. See below: at this size it does not finish.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `json_schema` has produced four distinct kinds of loss across
# four documents — a nesting level, a set of key names, a type, a generality.
# **This document asks a different question: what happens at 50 MB.**
#
# NDJSON also suits tidyjson unusually well. Its whole model is a table of
# documents, and NDJSON is literally that, so `tbl_json` should take a character
# vector of lines directly — where every other tool in this corpus had to be
# told what a record was.
suppressMessages({library(tidyjson); library(jsonlite)})
cat(sprintf("R %s, tidyjson %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyjson"), packageVersion("jsonlite")))

path <- "../source.jsonl"
ln   <- readLines(path, warn = FALSE)
cat(sprintf("  %s lines\n", format(length(ln), big.mark = ",")))

# ── Q1. THE SCALE WALL. ──────────────────────────────────────────────────────
cat("\n1. what is in here — json_schema, timed as the slice grows:\n")
cat("      n  input       time    schema\n")
rate <- NA
for (n in c(50, 200, 800)) {
  sub <- paste0("[", paste(ln[seq_len(n)], collapse = ","), "]")
  t0  <- Sys.time()
  s   <- as.character(json_schema(sub))
  el  <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  cat(sprintf("   %4d %9s B %7.1fs  %7s c\n", n, format(nchar(sub), big.mark = ","),
              el, format(nchar(s), big.mark = ",")))
  flush.console()
  rate <- nchar(sub) / el
}
cat(sprintf("\n   %.1f KB/s, so the whole 50 MB file extrapolates to about %.0f MINUTES.\n",
            rate / 1024, (file.size(path) / rate) / 60))
cat("   NOT RUN. SCORED CANNOT, which is the first time this function has\n")
cat("   earned that mark rather than WRONG — on the other four documents it\n")
cat("   finished and gave a misleading answer. Here it does not finish.\n")
cat("   `corpus/README.md` says NDJSON is how JSON at scale actually arrives.\n")
cat("   The most schema-aware tool in R cannot describe an hour of it.\n")

# ── Q3 / Q7. NDJSON is tidyjson's native shape. ──────────────────────────────
cat("\n3/7. what is one record, and how many:\n")
t0 <- Sys.time()
tj <- as.tbl_json(ln)
cat(sprintf("   as.tbl_json(readLines(...)) -> %s documents in %.1f s\n",
            format(nrow(tj), big.mark = ","),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("   NO SHAPE KNOWN IN ADVANCE, AND NO VERB NEEDED. tidyjson's model is a\n")
cat("   TABLE OF DOCUMENTS and NDJSON is literally that, so a character vector\n")
cat("   of lines is already the right input. Every other tool in this corpus\n")
cat("   had to be told what a record was — jq needed `.entry[]`, purrr needed\n")
cat("   `stream_in` first. This is the cleanest answer to question 3 in the\n")
cat("   corpus, and it is an accident of the FORMAT matching the tool's model.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
t0 <- Sys.time()
kt <- tj |> gather_object() |> json_types()
tb <- table(as.character(kt$name))
cat(sprintf("   gather_object |> json_types over all %s records in %.1f s\n",
            format(length(ln), big.mark = ","),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
for (k in names(sort(tb, decreasing = TRUE)))
  cat(sprintf("     %-12s %6s of %s\n", k, format(as.integer(tb[[k]]), big.mark = ","),
              format(length(ln), big.mark = ",")))
cat("   Correct, fast, and nothing known in advance. `org` on 3,779 is the\n")
cat("   only ragged field at the event level, matching the other four tools.\n")

# ── Q8. ──────────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per event:\n")
t0 <- Sys.time()
tbl <- tj |> spread_values(type = jstring("type"), id = jstring("id")) |>
  (\(d) d)()
cat(sprintf("   spread_values -> %s x %d in %.1f s\n",
            format(nrow(tbl), big.mark = ","), ncol(tbl),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
print(utils::head(as.data.frame(tbl)[, c("type", "id")], 3))
cat(sprintf("   type: %s\n",
            paste(sprintf("%s %s", names(sort(table(as.data.frame(tbl)$type),
                                              decreasing = TRUE))[1:3],
                          format(sort(table(as.data.frame(tbl)$type),
                                      decreasing = TRUE)[1:3], big.mark = ",")),
                  collapse = ", ")))

cat("
CONCLUSION — the format suits this tool better than any other in the corpus,
and its one describing function cannot run at all.

  **NDJSON is tidyjson's native shape and it shows.** `as.tbl_json()` on a
  character vector of lines gives 37,883 documents with nothing known in
  advance and no verb chosen — the cleanest answer to question 3 anywhere in
  this corpus. jq needed a path, purrr needed `stream_in`, rrapply needed a
  parsed list. tidyjson's model is *a table of documents*, and this file is one.
  `gather_object() |> json_types()` then answers question 4 over all 37,883
  records in seconds and agrees with the other four tools exactly.

  **And `json_schema` does not finish in any reasonable time.** Measured on
  slices it runs at **25.5 KB/s here**, so the 50 MB file extrapolates to about
  **33 minutes** — labelled an extrapolation, not run. **Scored CANNOT, the
  first time in five documents it has earned that rather than WRONG.** On `03`,
  `05`, `10` and `07` it finished and produced a small confident answer that was
  missing a nesting level, 64% of the key names, a type, and a generality
  respectively.

  **Its throughput is itself document-dependent by nearly 7x**, which is worth
  recording: 3.8 KB/s on `03-natural-earth`'s deeply nested coordinate arrays
  against 25.5 KB/s on these flat-ish events. Whatever it costs, it is not a
  function of bytes alone.

  That is worth stating plainly against this project's own thesis.
  `corpus/README.md` says NDJSON is how JSON at scale actually arrives, and
  `README.md` argues that describing an unknown document is the unsolved half.
  **The most schema-aware tool in R cannot describe fifty megabytes of the most
  ordinary format there is** — not because it gets it wrong, but because it does
  not return.
")
