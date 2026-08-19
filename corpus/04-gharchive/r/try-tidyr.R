# tidyr — one hour of GitHub Archive events (NDJSON)
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.jsonl   50 MB, 37,883 events, one JSON object per line
#  measured      2026-08-09
#  run           cd corpus/04-gharchive/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this what it claims to be                5   no                  YES
#   3 what is one record                          4   no                  RIGHT
#   4 always vs sometimes                         5   no                  RIGHT
#   7 how many records                            2   no                  RIGHT
#   8 three named fields to a table               5   YES                 YES
#
# WHY THIS FILE. It is NDJSON, so it is NOT valid JSON — question 0 is real here
# rather than hypothetical. And its `payload` differs by event type with the
# discriminator on the PARENT, which is the open case no operation handles.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyr"), packageVersion("jsonlite")))

# 0. The health question, and jsonlite gets it right by having a separate verb.
cat("\n0. is this what it claims to be:\n")
ok <- tryCatch({ fromJSON("../source.jsonl", simplifyVector = FALSE); TRUE },
               error = function(e) { cat("   fromJSON() FAILS:",
                 substr(conditionMessage(e), 1, 70), "\n"); FALSE })
cat("   NDJSON is not valid JSON, and jsonlite says so rather than guessing.\n")
cat("   stream_in() is the right verb, and knowing to reach for it IS the\n")
cat("   question — a naive check calls a sound file broken.\n")

t0 <- Sys.time()
ev <- stream_in(file("../source.jsonl"), simplifyVector = FALSE, verbose = FALSE)
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("   stream_in(): %d records in %.1f s\n", length(ev), el))

# THE PROTOCOL: the container goes in as a ONE-element list-column, so that
# unnest_auto chooses longer or wider itself. Pre-splitting answers question 3.
cat("\n3/7. unnest_auto on the events:\n")
t <- tibble(x = list(ev))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   RIGHT.", length(ev), "events, one row each — an array of records is\n")
cat("   unnest_auto's best case and it takes it.\n")

cat("\n4. the ragged part is one level down, in `payload`:\n")
types <- vapply(ev, function(e) e$type, "")
print(head(sort(table(types), decreasing = TRUE), 5))
pk <- lapply(ev, function(e) names(e$payload))
allk <- unique(unlist(pk))
cat("   payload has", length(allk), "distinct keys across", length(ev), "events\n")
common <- Reduce(intersect, pk)
cat("   keys present in EVERY payload:", length(common),
    if (length(common)) paste(common, collapse = ", ") else "— none at all", "\n")
cat("   THE OPEN CASE. No field is in every payload, and the `type` that\n")
cat("   explains them sits on the enclosing event, not inside the payload.\n")
cat("   That is the discriminator-on-the-parent problem and nothing solves it.\n")

cat("\n8. three named fields:\n")
tbl <- tibble(x = ev) |>
  hoist(x, type = "type", actor = list("actor", "login"), repo = list("repo", "name"))
print(head(select(tbl, type, actor, repo), 3))

cat("
CONCLUSION. unnest_auto RIGHT at the top level and untouched by the thing that
makes this file hard. Rectangling the events is easy; the raggedness is inside
`payload`, where the key-sets have NOTHING in common and the field that would
explain them is one level up.

tidyr can group by `type` the moment a person names it — but naming it requires
already knowing that payload shape depends on it, which is question 5 answered
before question 1. That is the whole ordering problem this project is about.
")
