# The two wrappers that let this book compute its numbers instead of quoting
# them.
#
# `CLAUDE.md` gives every fact one owner and records that a number living in two
# places has gone stale in one of them five times. A book is the most tempting
# possible sixth place: it wants to say "336 copies" in running prose. So it
# does not say it — it runs the probe and prints what came back. A chapter can
# then be wrong about what a number MEANS, which review catches, but it cannot
# be wrong about what the number IS.

ROOT <- normalizePath(file.path(dirname(getwd()), basename(getwd()), "..")
                      , mustWork = FALSE)
if (!dir.exists(file.path(ROOT, "corpus"))) ROOT <- normalizePath("..")

BIN <- file.path(ROOT, "target", "release", "fathom")

# Everything runs with the working directory at the repository root, because
# `uv run` finds the project by walking up from where it starts and the corpus
# paths in the text are written from the root. Restored on exit so a chapter
# that reads a file by relative path still works.
at_root <- function(expr) {
  old <- setwd(ROOT)
  on.exit(setwd(old), add = TRUE)
  force(expr)
}

#' The frozen probe's report on a corpus file, as a character vector of lines.
#'
#' `design/probe.py` is the instrument and the oracle. It is frozen; this
#' invokes it and does not import it, so nothing here can be a freeze event.
probe <- function(rel) {
  at_root(system2("uv", c("run", "design/probe.py", rel),
                  stdout = TRUE, stderr = FALSE))
}

#' The Rust core, through the CLI R and Python will invoke as a subprocess.
#'
#' Not a library call: `design/implementation.md` chose a binary and a pipe over
#' FFI, and the book should reach the core the same way a binding does.
fathom <- function(verb, rel, flags = character()) {
  if (!file.exists(BIN)) {
    return(paste0("(no binary — run `cargo build --release` at the repository ",
                  "root, then render again)"))
  }
  at_root(system2(BIN, c(verb, flags, rel), stdout = TRUE, stderr = FALSE))
}

#' Print lines as plain output, which is what the probe's report is.
say <- function(x) cat(x, sep = "\n")

#' How big a corpus file is, measured rather than typed.
bytes_of <- function(rel) file.size(file.path(ROOT, rel))

kb <- function(rel) sprintf("%.0f KB", bytes_of(rel) / 1024)
