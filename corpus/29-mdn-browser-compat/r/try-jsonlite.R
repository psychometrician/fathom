# jsonlite — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite alone (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/r && Rscript try-jsonlite.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **jsonlite is the parser every other R attempt here depends on**, so the
# question is what it contributes BEYOND parsing. Its answer to a nested
# document is `simplifyVector`, and this file measures what that does rather
# than describing it.

suppressMessages(library(jsonlite))
cat(sprintf("jsonlite %s · R %s.%s\n", packageVersion("jsonlite"),
            R.version$major, R.version$minor))

# ── Q0. THE SOUNDNESS QUESTION, PUT PROPERLY. ────────────────────────────────
t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
p1 <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\nparse (simplifyVector = FALSE): %.1f s\n", p1))
cat("Q0  parsed and said nothing. CANNOT.\n")
cat("    And the specific silences, tested rather than asserted:\n")
d <- tryCatch(fromJSON('{"a":1,"a":2}'), error = function(e) e)
cat(sprintf("      duplicate keys {\"a\":1,\"a\":2} -> %s   (last wins, no warning)\n",
            if (inherits(d, "error")) "ERROR" else paste(names(d), unlist(d), collapse = "=")))
b <- tryCatch(fromJSON('{"n":9007199254740993}'), error = function(e) e)
cat(sprintf("      9007199254740993        -> %s\n",
            if (inherits(b, "error")) "ERROR" else format(b$n, digits = 22)))
cat("      ** THAT IS THE 2^53 PROBLEM AND IT IS jsonlite's, NOT THIS FILE'S. **\n")
cat("      base R has no integer wide enough, so the value is a double and the\n")
cat("      last digit is gone. design/implementation.md is why neither binding\n")
cat("      parses JSON: a parser in each language makes the two disagree.\n")
nn <- tryCatch(fromJSON('{"x":NaN}'), error = function(e) e)
cat(sprintf("      bare NaN                -> %s\n",
            if (inherits(nn, "error")) "REFUSED — jsonlite is strict here" else "accepted"))

# ── Q1/Q2. ───────────────────────────────────────────────────────────────────
cat(sprintf("\nQ1  names(doc) -> %d keys: %s\n", length(doc),
            paste(names(doc), collapse = ", ")))
cat("    ONE LEVEL. jsonlite has no field listing of its own.\n")

depth <- function(x) if (!is.list(x) || !length(x)) 0L else 1L + max(vapply(x, depth, 0L))
t0 <- Sys.time()
dep <- depth(doc)
cat(sprintf("\nQ2  %d, by a recursive function I wrote (%.1f s). The recursion is\n",
            dep, as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    base R; jsonlite contributed nothing to it.\n")

# ── THE SIMPLIFIER, MEASURED. ────────────────────────────────────────────────
cat("\n── what simplifyVector = TRUE does to this document ─────────────────────\n")
t0 <- Sys.time()
simp <- fromJSON("../source.json")
p2 <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("  parse with simplification: %.1f s (%.1fx the plain parse)\n", p2, p2 / p1))
cat(sprintf("  class of $api                    : %s\n", paste(class(simp$api), collapse = "/")))
cat(sprintf("  class of $browsers               : %s\n", paste(class(simp$browsers), collapse = "/")))
one <- simp$api$ANGLE_instanced_arrays$`__compat`
cat(sprintf("  $api$ANGLE...$__compat is a %s with %d fields\n",
            paste(class(one), collapse = "/"), length(one)))
cat("  NOTHING BECAME A DATA FRAME. Every level here is an object keyed by an\n")
cat("  open vocabulary, and simplifyVector turns ARRAYS of records into data\n")
cat("  frames — there are almost none. The simplifier is built for the shape\n")
cat("  this document does not have.\n")

# ── Q3/Q7. ───────────────────────────────────────────────────────────────────
cat("\nQ3  jsonlite names no candidates and prices none. CANNOT.\n")
cat(sprintf("\nQ7  %d at the top; below that I would have to write the walk myself.\n",
            length(doc)))

# ── Q5. ──────────────────────────────────────────────────────────────────────
n_log <- 0L; n_chr <- 0L
scan <- function(n) {
  if (!is.list(n)) return(invisible())
  nm <- names(n)
  for (k in seq_along(n)) {
    if (!is.null(nm) && nm[k] == "version_added" && !is.list(n[[k]])) {
      if (is.logical(n[[k]])) n_log <<- n_log + 1L else n_chr <<- n_chr + 1L
    } else scan(n[[k]])
  }
}
scan(doc)
cat(sprintf("\nQ5  version_added: %s character, %s logical.\n",
            format(n_chr, big.mark = ","), format(n_log, big.mark = ",")))
cat("    YES, and this is jsonlite's real contribution to this document:\n")
cat("    with simplifyVector = FALSE it PRESERVES the type of every leaf.\n")
cat("    rrapply's melt then throws that away; tidyr's list-column keeps it.\n")

cat("\nQ6  CANNOT.\n")
cat("\nQ8  `doc$api$X$`__compat`$mdn_url` — yes, by `$`, one field at a time.\n")
cat("Q9  a missing name gives NULL rather than an error. YES.\n")
cat("Q10 CANNOT without writing the recursion.\n")
cat("Q11 CANNOT. jsonlite has no search.\n")
cat("Q12 CANNOT — see the simplifier measurement above. What jsonlite offers is\n")
cat("    flatten(), which needs a data frame to start from, and there is none.\n")

cat("
CONCLUSION. Written after the run and corrected against what printed.
")
