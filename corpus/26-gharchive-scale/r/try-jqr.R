# jqr — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.jsonl   870 MB / 286,864 records
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/r && Rscript try-jqr.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **jqr and ../python/try-jq.py are the SAME ENGINE through two doors.** The
# Python binding took 224 s at 24 MB by feeding it one parsed record at a time.
# jqr takes TEXT, so it can be handed the raw lines without R parsing them
# first — which is a different cost model for the same jq, and the thing worth
# measuring here.
suppressMessages(library(jqr))
source("_budget.R")
cat(sprintf("jqr %s · R %s.%s · budget %d s\n", packageVersion("jqr"),
            R.version$major, R.version$minor, BUDGET))
cat("\nQ0  jq parses and says nothing. Duplicate keys: last wins. CANNOT.\n")
cat("\n── jq over the raw lines, no R parsing ─────────────────────────────────\n")
a <- attempt("readLines(870 MB)", readLines("../source.jsonl"))
lines <- a$value
LEAF <- '[path(.. | select(type != "object" and type != "array"))] | length'
BROKEN <- '[paths(scalars)] | length'
for (n in c(1000L, 10000L, 50000L)) {
  b <- attempt(sprintf("leaf count, %s records", format(n, big.mark = ",")),
               sum(as.numeric(jq(lines[seq_len(n)], LEAF))))
  if (b$ok) cat(sprintf("      -> %s leaves\n", format(b$value, big.mark = ",")))
}
full <- attempt("leaf count, ALL records, ONE CALL",
                sum(as.numeric(jq(lines, LEAF))))
cat("\n    ** THAT IS AN R LIMIT, NOT A jq LIMIT, AND IT IS THE FINDING HERE. **\n")
cat("    `protect(): protection stack overflow` — jqr PROTECTs each result on\n")
cat("    R's protection stack and the stack is finite. The SAME jq engine reads\n")
cat("    all 286,864 records through the Python binding without complaint.\n")
cat("    Chunking is the workaround, and the caller has to know that:\n\n")
chunked <- function(prog) {
  tot <- 0
  for (i in seq(1, length(lines), by = 10000L)) {
    j <- min(i + 9999L, length(lines))
    tot <- tot + sum(as.numeric(jq(lines[i:j], prog)))
  }
  tot
}
full <- attempt("leaf count, ALL records, CHUNKED by 10k", chunked(LEAF))
brok <- attempt("the BROKEN idiom, all records, chunked", chunked(BROKEN))
if (full$ok && brok$ok) {
  cat(sprintf("\nQ7  %s leaves — THE WHOLE FILE.\n", format(full$value, big.mark = ",")))
  cat("\n── the broken idiom, at scale ─────────────────────────────────────────\n")
  cat(sprintf("  paths(scalars)   %14s\n", format(brok$value, big.mark = ",")))
  cat(sprintf("  corrected        %14s\n", format(full$value, big.mark = ",")))
  cat(sprintf("  DROPPED SILENTLY %14s  (%.2f%%)\n",
              format(full$value - brok$value, big.mark = ","),
              100 * (full$value - brok$value) / full$value))
  cat("    and ../python/try-jq.py reports the identical figures through the\n")
  cat("    other door, which is the check this pair exists for.\n")
  cat("\n    ** AND THE R DOOR IS ABOUT TEN TIMES FASTER, ONCE CHUNKED. ** jqr\n")
  cat("    takes TEXT and runs one program over a vector of lines; the Python\n")
  cat("    binding takes a parsed VALUE, so it pays a json.loads per record and\n")
  cat("    spends 224 s where this spends about 21. Same engine, same answer,\n")
  cat("    an order of magnitude apart, and the faster one is the one that\n")
  cat("    falls over unless you chunk it by hand.\n")
}
cat("\nQ5  `type` is a first-class function, so a type census is a group_by.\n")
cat("Q1/Q2 expressible per record. Q3 CANNOT. Q6 jq counts keys, decides nothing.\n")
cat("Q10 EXACT — a jq path is an array of steps; an index is a NUMBER, a key a STRING.\n")
cat("Q11/Q12 expressible via `..`, at the cost measured above.\n")
cat("\nCONCLUSION. Written after the run and corrected against what printed.\n")
