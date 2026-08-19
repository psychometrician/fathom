# fathom's words in R — the parity test for the project's premise.
#
#   Rscript design/fathom.R <file> <path> [<field> …]
#
# EXPERIMENT, NOT A PACKAGE, same status as probe.py, rows.py, first_present.py,
# take.py and where.py.
#
# WHY THIS EXISTS
# ---------------
# `README.md`'s premise is **one way of seeing and extracting that works the same
# in R and in Python**. Four words now run — `rows`, `first_present`, `take`,
# `where` — and every one of them is Python. **The premise had never been tested
# at all.**
#
# This is a genuine re-implementation rather than a subprocess call to the Python,
# and that is the point. `design/implementation.md` proposes one Rust core with
# thin bindings, which would make the two languages agree *by construction* and
# would therefore test nothing about the vocabulary. **The question here is
# whether the same sentence reads the same and returns the same answer when
# somebody writes it independently in the other language.**
#
# `README.md` also warns that a word shared with god needs a test on both sides
# from the day it is shared, "or the two will drift and the drift will be
# invisible". `design/parity.py` is that test.
#
# WHAT R MAKES HARDER, AND IT IS NOT NOTHING
# ------------------------------------------
# jsonlite with simplifyVector = FALSE gives nested lists, and an R list does not
# distinguish an object from an array the way a Python dict does from a list. The
# test is `!is.null(names(x))`. That is a real difference in the medium and it is
# handled in `children()`, in one place, exactly as `rows.py` does it in one.

suppressMessages({library(jsonlite)})

# `.` alone is the empty path: the document. Quoted segments keep their dots.
parse_path <- function(path) {
  path <- trimws(path)
  if (path %in% c(".", "")) return(character(0))
  m <- gregexpr('"[^"]*"|[^.]+', path)[[1]]
  segs <- regmatches(path, gregexpr('"[^"]*"|[^.]+', path))[[1]]
  gsub('^"|"$', "", segs)
}

# (key, value) for every child — an object's items or an array's positions.
# The unification is the point and it is the same sentence as rows.py's.
children <- function(node) {
  if (!is.list(node) || length(node) == 0) return(list())
  nm <- names(node)
  keys <- if (is.null(nm)) seq_along(node) - 1L else nm
  Map(function(k, v) list(key = k, val = v), keys, node)
}

is_object <- function(node) is.list(node) && !is.null(names(node))

# Yield (captured keys, value) for every match of `segs` against `node`.
match_path <- function(node, segs, keys = list()) {
  if (length(segs) == 0) return(list(list(keys = keys, val = node)))
  head <- segs[[1]]; rest <- if (length(segs) > 1) segs[-1] else character(0)
  out <- list()

  if (head == "*") {
    for (ch in children(node))
      out <- c(out, match_path(ch$val, rest, c(keys, list(ch$key))))

  } else if (nchar(head) > 2 && endsWith(head, "**")) {
    # `children**` — follow a NAMED step repeatedly. Same reasoning as rows.py:
    # a recursive document is one step taken again, not a firehose.
    name <- substr(head, 1, nchar(head) - 2)
    stack <- list(node)
    while (length(stack)) {
      n <- stack[[length(stack)]]; stack[[length(stack)]] <- NULL
      if (is_object(n) && !is.null(n[[name]])) {
        for (ch in children(n[[name]])) {
          out <- c(out, match_path(ch$val, rest, c(keys, list(ch$key))))
          stack[[length(stack) + 1]] <- ch$val
        }
      }
    }

  } else if (head == "**") {
    stack <- children(node)
    while (length(stack)) {
      ch <- stack[[length(stack)]]; stack[[length(stack)]] <- NULL
      out <- c(out, match_path(ch$val, rest, c(keys, list(ch$key))))
      stack <- c(stack, children(ch$val))
    }

  } else if (is_object(node) && !is.null(node[[head]])) {
    out <- c(out, match_path(node[[head]], rest, keys))
  }
  # a segment that does not match yields nothing, which is the honest answer
  out
}

# ── the words ────────────────────────────────────────────────────────────────

rows <- function(doc, path) {
  found <- match_path(doc, parse_path(path))
  list(n = length(found), records = lapply(found, function(f) f$val),
       keys = lapply(found, function(f) f$keys))
}

# The first of these paths that is actually there. A zero comes back; only a
# missing path and an explicit null are skipped.
first_present <- function(node, ..., default = NULL) {
  for (p in c(...)) {
    for (m in match_path(node, parse_path(p)))
      if (!is.null(m$val)) return(m$val)
  }
  default
}

# One row per record, one column per path. Nothing else is built.
take <- function(records, ...) {
  paths <- c(...)
  nms <- vapply(paths, function(p) {
    s <- parse_path(p); s[[length(s)]]
  }, "")
  lapply(records, function(r) {
    setNames(lapply(paths, function(p) {
      m <- match_path(r, parse_path(p))
      if (length(m)) m[[1]]$val else NULL
    }), nms)
  })
}

# ── where(): every path whose value matches, FOLDED ──────────────────────────
#
# The fourth word, and the one that brings R to four of four. Added 2026-08-10,
# closing VERDICT.md item 23 D12's "`where` has no R version".
#
# WHY THIS PORTS ONLY ONE BRANCH OF classify(), AND SAYS SO
# --------------------------------------------------------
# `where.py` folds a container's keys to `<key>` by asking `probe.classify()`,
# which is a hundred lines carrying five corpus files' worth of repair. It hands
# it ONE instance, and with one instance every multi-copy signal — sibling
# overlap, type homogeneity, vocabulary growth — is unreachable by construction.
# What remains is the branch below, and porting the rest would be dead code
# dressed as fidelity.
#
# `where.py` explains at length why one instance is the right call rather than a
# shortcut: handing `classify` the node's VALUES as siblings looks more correct
# and is measurably worse, taking npm's URL report from 7 path shapes to 659.
# **That reasoning lives there and is not restated here** — this is the same
# decision, reached by reading it, which is exactly what a re-implementation is
# supposed to be.
#
# WHAT R MAKES HARDER, AND IT IS THE SAME THING AS EVER
# ----------------------------------------------------
# `{}` and `[]` both arrive from jsonlite as an unnamed empty list, so this
# cannot tell an empty object from an empty array. `rows()` has the same limit
# for the same reason and the header above states it once.

KEYED_MIN <- 20  # probe.py's constant, and the only one this word reaches

WHERE_URL   <- "^(https?|git\\+https?|ftp)://"
WHERE_EMAIL <- "^[^@[:space:]]+@[^@[:space:]]+\\.[^@[:space:]]+$"
WHERE_ISO   <- "^[0-9]{4}-[0-9]{2}-[0-9]{2}([T ][0-9]{2}:[0-9]{2})?"

predicates <- list(
  url   = function(v) is.character(v) && grepl(WHERE_URL, v[1], ignore.case = TRUE),
  email = function(v) is.character(v) && grepl(WHERE_EMAIL, v[1]),
  date  = function(v) is.character(v) && grepl(WHERE_ISO, v[1]),
  # An empty container is empty. R cannot tell `[]` from `{}` — both arrive as an
  # unnamed zero-length list — and does not need to, because both match. Writing
  # this clause is what exposed the Python bug: there the same two cases were
  # listed and could never fire, because the walk descended a container before
  # testing it. Both sides now test the node first. See FINDINGS.md, 2026-08-10.
  empty = function(v) is.null(v) || (is.list(v) && length(v) == 0) ||
                      (is.character(v) && v[1] == "")
)

# classify()'s single-instance branch: `n > KEYED_MIN`, or exactly KEYED_MIN
# values that are all objects of one shape — a collection addressed by name.
keys_are_data <- function(node) {
  n <- length(node)
  if (n >= KEYED_MIN) {
    vals <- unname(node)
    if (all(vapply(vals, is_object, TRUE))) {
      shapes <- vapply(vals, function(v) paste(sort(names(v)), collapse = ""), "")
      if (length(unique(shapes)) == 1) return(TRUE)
    }
  }
  n > KEYED_MIN
}

where <- function(doc, predicate = "url") {
  test <- if (is.function(predicate)) predicate else predicates[[predicate]]
  if (is.null(test)) stop("no such predicate: ", predicate)
  hits <- new.env(hash = TRUE, parent = emptyenv())

  walk <- function(node, parts) {
    # The node is tested BEFORE the descent, so a container can match. The
    # ordering is the whole of the 2026-08-10 repair; see `empty` above.
    if (isTRUE(test(node))) {
      p <- if (length(parts)) paste(parts, collapse = ".") else "."
      cur <- if (exists(p, envir = hits, inherits = FALSE)) get(p, envir = hits) else 0L
      assign(p, cur + 1L, envir = hits)
    }
    if (is.list(node)) {
      if (is_object(node)) {
        many <- keys_are_data(node)
        for (ch in children(node))
          walk(ch$val, c(parts, if (many) "<key>" else ch$key))
      } else {
        for (ch in children(node)) walk(ch$val, c(parts, "[]"))
      }
    }
  }

  walk(doc, character(0))
  ks <- ls(hits)
  if (!length(ks)) return(integer(0))
  setNames(vapply(ks, function(k) get(k, envir = hits), 0L), ks)
}

# Guarded so that `source("fathom.R")` loads the words WITHOUT running the CLI.
# Without this, design/parity.py's driver sourced the file, the block below ran
# with the driver's own arguments, and jsonlite tried to parse this R source as
# JSON — eleven identical "Execution halted" mismatches that were the harness
# failing rather than the words disagreeing.
if (!interactive() && !exists(".fathom_sourced")) {
  a <- commandArgs(trailingOnly = TRUE)
  cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))
  doc <- fromJSON(a[1], simplifyVector = FALSE)
  r <- rows(doc, a[2])
  cat(sprintf("\n  rows(%s) -> %d rows\n", sQuote(a[2]), r$n))
  if (length(a) > 2) {
    fp <- vapply(r$records, function(rec) {
      v <- first_present(rec, a[-(1:2)])
      if (is.null(v)) NA_character_ else as.character(v)[1]
    }, NA_character_)
    cat(sprintf("  first_present(%s) filled %d of %d\n",
                paste(a[-(1:2)], collapse = ", "), sum(!is.na(fp)), length(fp)))
    cat(sprintf("  first three: %s\n", paste(head(fp, 3), collapse = ", ")))
  }
}
