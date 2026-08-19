# jsonlite — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite alone (version printed at run time)
#  file          ../source.jsonl   870 MB / 286,864 records
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/r && Rscript try-jsonlite.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **jsonlite is the parser every other R attempt here depends on**, so this file
# measures the ceiling all six of them share. Two readers are compared:
# `fromJSON` on the whole text, and `stream_in`, which is jsonlite's own answer
# to NDJSON.
suppressMessages(library(jsonlite))
source("_budget.R")
cat(sprintf("jsonlite %s · R %s.%s · budget %d s\n", packageVersion("jsonlite"),
            R.version$major, R.version$minor, BUDGET))

cat("\nQ0  parses and says nothing. And base R cannot hold JSON's integers:\n")
cat(sprintf("      9007199254740993 -> %s   ** the 2^53 problem, jsonlite's **\n",
            format(fromJSON('{"n":9007199254740993}')$n, digits = 22)))
cat("    Python's json reads it exactly. CANNOT.\n")

cat("\n── the whole file, two readers ─────────────────────────────────────────\n")
a <- attempt("stream_in(simplifyVector=FALSE)",
             jsonlite::stream_in(file("../source.jsonl"), simplifyVector = FALSE,
                                 verbose = FALSE))
b <- attempt("stream_in(simplifyVector=TRUE)",
             jsonlite::stream_in(file("../source.jsonl"), verbose = FALSE))

docs <- a$value
if (!is.null(docs)) {
  cat(sprintf("\nQ7  %s records. yes.\n", format(length(docs), big.mark = ",")))
  cat(sprintf("\nQ1  names(doc[[1]]) -> %s\n", paste(names(docs[[1]]), collapse = ", ")))
  cat("    ONE LEVEL, and only of one record. jsonlite has no field listing.\n")
  depth <- function(x) if (!is.list(x) || !length(x)) 0L else 1L + max(vapply(x, depth, 0L))
  d <- attempt("depth(), a recursion I wrote", max(vapply(docs[1:20000], depth, 0L)))
  if (d$ok) cat(sprintf("\nQ2  %d over the first 20,000 records, by MY recursion.\n", d$value))
}
if (b$ok) {
  df <- b$value
  cat(sprintf("\nQ12 simplifyVector=TRUE -> %s x %d\n",
              format(nrow(df), big.mark = ","), ncol(df)))
  cat("    ** AND THAT IS THE ONE THING jsonlite CONTRIBUTES HERE. ** The\n")
  cat("    simplifier turns an array of records into a data frame, which is\n")
  cat("    exactly this file's shape — unlike entries 28 and 29, where every\n")
  cat("    level was an object keyed by an open vocabulary and it did nothing.\n")
  cat(sprintf("    columns: %s\n", paste(names(df), collapse = ", ")))
}
cat("\nQ3  jsonlite names no candidates and prices none. CANNOT.\n")
cat("Q6  CANNOT.  Q10/Q11 CANNOT — no walk, no search.\n")
cat("Q5  PARTLY: with simplifyVector=FALSE the type of every leaf survives.\n")
cat("Q8/Q9 `$` one field at a time; a missing name gives NULL. yes.\n")
cat("\nCONCLUSION. Written after the run and corrected against what printed.\n")
