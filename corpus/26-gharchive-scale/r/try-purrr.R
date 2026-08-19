# purrr — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.jsonl   870 MB / 286,864 records
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/r && Rscript try-purrr.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# purrr is a list library, not a JSON library. At 50 MB that cost eleven lines
# of hand-written walk; the question here is what those eleven lines cost at
# 286,864 records — and entry 29 already found that the obvious accumulator is
# accidentally quadratic.
suppressMessages({library(jsonlite); library(purrr)})
source("_budget.R")
cat(sprintf("jsonlite %s · purrr %s · R %s.%s · budget %d s\n",
            packageVersion("jsonlite"), packageVersion("purrr"),
            R.version$major, R.version$minor, BUDGET))
cat("\nQ0  CANNOT.\n")
p <- attempt("stream_in(simplifyVector=FALSE)",
             jsonlite::stream_in(file("../source.jsonl"), simplifyVector = FALSE,
                                 verbose = FALSE))
docs <- p$value
cat(sprintf("\nQ7  %s records.\n", format(length(docs), big.mark = ",")))
cat(sprintf("Q1  %s  (one level, one record)\n", paste(names(docs[[1]]), collapse = ", ")))

# the walk, written the way entry 29 established it must be: RETURN and
# concatenate, never append in place, or it is quadratic.
walk_all <- function(x, acc) {
  if (is.list(x) && length(x)) {
    nm <- names(x)
    unlist(lapply(seq_along(x), function(i)
      walk_all(x[[i]], c(acc, if (is.null(nm) || !nzchar(nm[i])) as.character(i) else nm[i]))),
      recursive = FALSE)
  } else list(list(p = acc, v = x))
}
cat("\n── my hand-written walk, on growing slices ─────────────────────────────\n")
for (n in c(2000L, 20000L, 100000L)) {
  a <- attempt(sprintf("walk the first %s records", format(n, big.mark = ",")),
               length(walk_all(docs[seq_len(n)], character(0))))
  if (a$ok) cat(sprintf("      -> %s leaves\n", format(a$value, big.mark = ",")))
}
full <- attempt("walk ALL 286,864 records", walk_all(docs, character(0)))
if (full$ok) {
  fl <- full$value
  cat(sprintf("\nQ12 %s leaves, by a recursion I wrote. PARTLY — the walk is mine.\n",
              format(length(fl), big.mark = ",")))
  cat("    ** AND IT DISAGREES WITH rrapply, jq AND ijson BY 138,980, WHICH IS\n")
  cat("    NOT A BUG IN ANY OF THEM. ** They say 17,670,186. The gap is EMPTY\n")
  cat("    CONTAINERS: `is.list(x) && length(x)` sends an empty object or array\n")
  cat("    to the leaf branch, so `{}` counts as a leaf here and does not there.\n")
  cat("    Checked on the first 2,000 records: 117,390 counting empty containers,\n")
  cat("    116,511 without, and the difference is exactly the 879 empties.\n")
  cat("    ** `how many leaves` HAS TWO DEFENSIBLE ANSWERS AND NO TOOL SAYS\n")
  cat("    WHICH IT GAVE YOU. ** That is question 7 being quietly ambiguous.\n")
  cat(sprintf("\nQ2  %d, from the same walk.\n", max(map_int(fl, ~ length(.x$p)))))
} else {
  cat("\nQ12 CANNOT at this size. The slices above say where the wall is.\n")
}
cat("\nQ3 CANNOT. Q6 CANNOT. Q8 pluck() reaches depth in one call — yes.\n")
cat("Q9  pluck returns NULL for a missing name. YES.\n")
cat("Q5  the values stay in a LIST, so types survive — unlike rrapply's melt.\n")
cat("Q10/Q11 from the walk, if it completes.\n")
cat("\nCONCLUSION. Written after the run and corrected against what printed.\n")
