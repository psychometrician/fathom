# tidyjson — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.jsonl   870 MB / 286,864 records
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/r && Rscript try-tidyjson.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **json_structure() completed entry 29's 865,598 nodes in about 55 seconds.**
# This file holds 17,670,186 leaves — 20x more — and entry 29 measured the verb
# as SUBLINEAR, so the honest test is a scaling curve first and the whole file
# after, exactly as there.
#
# **THE RESULT: it is the only one of the fourteen that did not finish**, and
# the curve is why it is recorded as a cost rather than a failure. See the
# bottom of this file.
suppressMessages({library(tidyjson); library(dplyr)})
source("_budget.R")
cat(sprintf("tidyjson %s · dplyr %s · R %s.%s · budget %d s\n",
            packageVersion("tidyjson"), packageVersion("dplyr"),
            R.version$major, R.version$minor, BUDGET))
cat("\nQ0  tidyjson parses and says nothing. CANNOT.\n")
lines <- readLines("../source.jsonl", n = 120000L)
cat(sprintf("read %s lines for the curve\n", format(length(lines), big.mark = ",")))
cat("\n── json_structure() scaling ────────────────────────────────────────────\n")
curve <- data.frame()
for (n in c(1000L, 5000L, 20000L, 60000L)) {
  a <- attempt(sprintf("json_structure, %s records", format(n, big.mark = ",")),
               nrow(json_structure(lines[seq_len(n)])))
  if (a$ok) {
    cat(sprintf("      -> %s nodes\n", format(a$value, big.mark = ",")))
    curve <- rbind(curve, data.frame(n = n, nodes = a$value, secs = a$secs))
  }
}
if (nrow(curve) > 2) {
  fit <- lm(log(secs) ~ log(n), data = curve[curve$secs > 0.05, ])
  e <- unname(coef(fit)[2])
  per <- curve$secs[nrow(curve)] / curve$n[nrow(curve)]
  est <- per * RECORDS * (RECORDS / curve$n[nrow(curve)])^(e - 1)
  cat(sprintf("\n  log-log slope %.2f  ->  extrapolated for all %s records: %.0f s (%.1f min)\n",
              e, format(RECORDS, big.mark = ","), est, est / 60))
}
cat("\n── and the whole file ──────────────────────────────────────────────────\n")
cat("  NOT ATTEMPTED BY DEFAULT, and the reason is recorded rather than argued.\n")
cat("  It WAS attempted on 2026-08-14 and ran for 10 min 39 s without returning,\n")
cat("  at which point it was killed from outside. `setTimeLimit` did not fire,\n")
cat("  exactly as _budget.R warns: it interrupts at R-level checkpoints and\n")
cat("  `json_structure()` is one long call into C.\n")
cat("  Set FULL=TRUE below to run it yourself; expect to kill it.\n")
FULL <- FALSE
if (FULL) {
  full <- attempt("json_structure, ALL 286,864 records",
                  nrow(json_structure(readLines("../source.jsonl"))))
}
cat("\nQ12 CANNOT in any time a person will wait. ** AND THE VERB DOES NOT FAIL —\n")
cat("    IT IS LINEAR AND SIMPLY COSTS TOO MUCH. ** The curve above has a\n")
cat("    log-log slope of 1.00 and extrapolates to about 466 s of pure compute;\n")
cat("    the observed run passed 639 s and was still going, because memory\n")
cat("    pressure at 4.5 million nodes per 60,000 records is not in the curve.\n")
cat("    ** tidyjson IS THE ONLY ONE OF THE FOURTEEN THAT DID NOT FINISH. **\n")
cat("\nQ1/Q2/Q5 come from the structure table, which is why they share Q12's fate.\n")
cat("Q3  CANNOT. Q6 CANNOT — `name` is a column, but nothing decides a key is data.\n")
cat("Q7  286,864 records, known from the line count rather than from tidyjson.\n")
cat("Q11 json_structure keeps no VALUE column; a search needs a second pass.\n")
cat("\nCONCLUSION. Written after the run and corrected against what printed.\n")
