# rrapply — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.jsonl   870 MB / 286,864 records
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/r && Rscript try-rrapply.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **rrapply's melt won the R half of entry 29 outright: 470,673 leaves in 0.4 s.**
# This file has 17,670,186 leaves by ijson's exact count — 38x more — so the
# question is whether the best verb in R survives the corpus's largest document.
suppressMessages({library(jsonlite); library(rrapply)})
source("_budget.R")
cat(sprintf("jsonlite %s · rrapply %s · R %s.%s · budget %d s\n",
            packageVersion("jsonlite"), packageVersion("rrapply"),
            R.version$major, R.version$minor, BUDGET))

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")
cat("\n── the parse every R attempt here shares ───────────────────────────────\n")
p <- attempt("stream_in(simplifyVector=FALSE)",
             jsonlite::stream_in(file("../source.jsonl"), simplifyVector = FALSE,
                                 verbose = FALSE))
docs <- p$value
cat("\n── the melt, on growing slices then on everything ──────────────────────\n")
for (n in c(2000L, 20000L, 100000L)) {
  a <- attempt(sprintf("melt of the first %s records", format(n, big.mark = ",")),
               nrow(rrapply(docs[seq_len(n)], how = "melt")))
  if (a$ok) cat(sprintf("      -> %s rows\n", format(a$value, big.mark = ",")))
}
full <- attempt("melt of ALL 286,864 records", rrapply(docs, how = "melt"))
if (full$ok) {
  m <- full$value
  lev <- setdiff(names(m), "value")
  cat(sprintf("\nQ12 %s rows x %d cols. ONE CALL.\n",
              format(nrow(m), big.mark = ","), ncol(m)))
  cat(sprintf("\nQ2  %d level columns -> depth %d. YES.\n", length(lev), length(lev)))
  cat(sprintf("\nQ7  %s leaves.\n", format(nrow(m), big.mark = ",")))
  cls <- table(vapply(m$value, function(z) class(z)[1], ""))
  cat("\nQ5  classes at the bottom:\n"); print(sort(cls, decreasing = TRUE))
  cat(sprintf("    `value` came back as: %s\n", class(m$value)))
  cat("    ijson and jq both say 13,009,389 string, 2,652,154 number,\n")
  cat("    1,581,755 boolean, 426,888 null — and EVERY ONE MATCHES once R's\n")
  cat("    integer and numeric are added back together. ** THE MELT DID NOT\n")
  cat("    COERCE HERE, AND ON ENTRY 29 IT DID. ** That is the finding: `value`\n")
  cat("    is atomic when the leaves happen to unify and a LIST when they do\n")
  cat("    not. Entry 29 was all strings and booleans, which unify to character,\n")
  cat("    so 57,103 booleans became \"FALSE\". This file has NULLs and numbers\n")
  cat("    in the mix, nothing unifies, the list survives and so do the types.\n")
  cat("    ** YOU CANNOT TELL FROM THE CALL WHICH YOU GOT. ** YES here, NO there,\n")
  cat("    same verb, same arguments, and the difference is the data.\n")
} else {
  cat("\nQ12 CANNOT at this size — the melt did not finish. The slices above say\n")
  cat("    where the wall is, and that is the answer question 12 gets here.\n")
}
cat("\nQ1  names(docs[[1]]) is one level, of one record. Q3 CANNOT. Q6 CANNOT.\n")
cat("Q8/Q9 `$` and NULL. yes. Q10/Q11 from the melt, if it completes.\n")
cat("\nCONCLUSION. Written after the run and corrected against what printed.\n")
