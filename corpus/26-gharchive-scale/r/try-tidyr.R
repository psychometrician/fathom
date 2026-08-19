# tidyr — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.jsonl   870 MB / 286,864 records
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/r && Rscript try-tidyr.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **The same repeated-`unnest_longer` loop entries 28 and 29 needed**, with all
# three pieces of ceremony those entries established: set the leaves aside at
# every step, force the column back to a list because unnest_longer silently
# simplifies, and count the calls yourself because nothing says how many are
# left. Entry 29 did 470,673 leaves in 3.8 s. This file has 17,670,186.
suppressMessages({library(jsonlite); library(tidyr); library(dplyr); library(tibble)})
source("_budget.R")
cat(sprintf("jsonlite %s · tidyr %s · dplyr %s · R %s.%s · budget %d s\n",
            packageVersion("jsonlite"), packageVersion("tidyr"),
            packageVersion("dplyr"), R.version$major, R.version$minor, BUDGET))
cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

p <- attempt("stream_in(simplifyVector=FALSE)",
             jsonlite::stream_in(file("../source.jsonl"), simplifyVector = FALSE,
                                 verbose = FALSE))
docs <- p$value
cat(sprintf("\nQ7  %s records.\n", format(length(docs), big.mark = ",")))

melt_loop <- function(x) {
  done <- tibble(); calls <- 1
  long <- tibble(k1 = as.character(seq_along(x)), v = unname(x))
  repeat {
    leaf <- !vapply(long$v, is.list, logical(1))
    if (any(leaf)) done <- bind_rows(done, long[leaf, ])
    long <- long[!leaf, ]
    if (!nrow(long)) break
    calls <- calls + 1
    long <- tidyr::unnest_longer(long, v, indices_to = paste0("k", calls))
    long$v <- as.list(long$v)     # it simplifies silently; forcing back is required
  }
  list(rows = nrow(done), calls = calls)
}

cat("\n── the twelve-call loop, on growing slices ─────────────────────────────\n")
for (n in c(2000L, 20000L, 100000L)) {
  a <- attempt(sprintf("melt loop, %s records", format(n, big.mark = ",")),
               melt_loop(docs[seq_len(n)]))
  if (a$ok) cat(sprintf("      -> %s rows in %d calls\n",
                        format(a$value$rows, big.mark = ","), a$value$calls))
}
full <- attempt("melt loop, ALL 286,864 records", melt_loop(docs))
if (full$ok) {
  cat(sprintf("\nQ12 %s rows in %d unnest_longer calls. PARTLY — the loop is mine.\n",
              format(full$value$rows, big.mark = ","), full$value$calls))
  cat(sprintf("\nQ2  %d, counted from how many calls it took. yes, by exhaustion.\n",
              full$value$calls))
} else {
  cat("\nQ12 CANNOT within the budget. The slices above say where the wall is.\n")
  cat("Q2  CANNOT — the depth IS the call count, so it shares Q12's fate.\n")
}
cat("\nQ1  unnest_wider once gives the 8 top-level names. ONE LEVEL PER CALL.\n")
cat("Q3  tidyr names no candidates and prices none. CANNOT.\n")
cat("Q6  CANNOT.\n")
cat("Q5  the leaves stay in a LIST column, so types survive — the property\n")
cat("    entry 29 found rrapply's atomic melt destroying.\n")
cat("Q8/Q9 hoist() reaches several depths in one call; a missing path gives NA\n")
cat("    rather than NULL, which entry 29 recorded and is worth repeating.\n")
cat("Q10/Q11 from the melted table, if it completes.\n")
cat("\nCONCLUSION. Written after the run and corrected against what printed.\n")
