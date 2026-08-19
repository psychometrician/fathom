# Shared budget + memory harness for entry 26's R attempts.
#
# **Not an attempt file.** This entry grades the fourteen on SCALE, so every
# attempt needs the same two instruments — a wall clock and a peak-memory
# reading — and repeating them in six files is how they drift apart. It does not
# carry the `try-` prefix because it is sourced, not run.
#
# **`setTimeLimit` is honest about its own limits and so is this comment.** It
# interrupts at R-level checkpoints, so it will stop a loop written in R and will
# NOT stop a single call that spends ten minutes inside C. Where that matters the
# attempt says so rather than pretending it was bounded.
BUDGET <- 900
RECORDS <- 286864L

# **BY NAME, NOT BY POSITION.** gc() returns 6 or 7 columns depending on whether
# a memory limit is set, so `gc()[, 6]` is "max used" as a raw CELL COUNT on
# this build and the megabytes on another. A first draft did exactly that and
# printed a peak of 171,548,251 MB.
peak_mb <- function() {
  g <- gc(FALSE)
  i <- which(colnames(g) == "max used")
  sum(g[, i + 1L])                        # the "(Mb)" column that follows it
}

# R's gc() measures R's OWN HEAP. The Python attempts in this entry report
# process peak RSS via getrusage, which also counts the interpreter, the parser
# buffers and anything malloc'd outside R's heap. `ps` gives the process figure
# so the two halves can be compared; both are printed and labelled.
rss_mb <- function() {
  out <- suppressWarnings(system2("ps", c("-o", "rss=", "-p", Sys.getpid()),
                                  stdout = TRUE, stderr = NULL))
  if (length(out) == 0) return(NA_real_)
  as.numeric(trimws(out[1])) / 1024
}

attempt <- function(label, expr) {
  gc(FALSE, full = TRUE)
  t0 <- Sys.time()
  setTimeLimit(elapsed = BUDGET, transient = TRUE)
  val <- tryCatch(force(expr), error = function(e) structure(list(msg = conditionMessage(e)),
                                                             class = "attempt_error"))
  setTimeLimit()
  secs <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  ok <- !inherits(val, "attempt_error")
  cat(sprintf("  %-34s %s %7.1f s  R heap %6.0f MB  process %6.0f MB\n", label,
              if (ok) "   OK" else "FAILED", secs, peak_mb(), rss_mb()))
  if (!ok) cat(sprintf("      %s\n", substr(val$msg, 1, 120)))
  list(ok = ok, secs = secs, mb = peak_mb(), rss = rss_mb(),
       value = if (ok) val else NULL)
}
