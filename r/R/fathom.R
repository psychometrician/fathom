# The R half of fathom. It is deliberately thin: `design/implementation.md`
# decided one Rust core and two bindings that invoke a binary and read a pipe —
# no FFI, no ABI, nothing compiled on a user's machine. Everything intricate
# lives in `fathom-core`, so this file has no opinion about JSON at all.
#
# THE TEST OF THIS FILE IS THAT IT ADDS NOTHING. `test/bindings.py` diffs what
# `fathom()` returns against what the binary printed, byte for byte, on every
# corpus document. A binding that reformats, re-wraps or re-encodes is a second
# implementation of the report, which is the thing the architecture exists to
# prevent.

#' Locate the fathom binary
#'
#' Three places, in order, and the order is the point: an explicit override
#' always wins, an installed binary is next, and the development build is last
#' so that working inside the project needs no configuration.
#'
#' @param error Whether to stop when nothing is found. `FALSE` returns `NULL`,
#'   which is what a test harness wants.
#' @return The path to the binary, or `NULL`.
#' @export
fathom_binary <- function(error = TRUE) {
  override <- Sys.getenv("FATHOM_BIN", unset = "")
  if (nzchar(override)) {
    # An override that does not exist is an error rather than a fallback. It was
    # set on purpose, and quietly using a different binary than the one asked
    # for is how a measurement gets attributed to the wrong build.
    if (!file.exists(override)) {
      stop("FATHOM_BIN is set to a file that does not exist: ", override,
           call. = FALSE)
    }
    return(override)
  }

  installed <- unname(Sys.which("fathom"))
  if (nzchar(installed)) return(installed)

  dev <- fathom_dev_binary()
  if (!is.null(dev)) return(dev)

  if (!error) return(NULL)
  stop("cannot find the `fathom` binary. It is looked for in three places:\n",
       "  1. $FATHOM_BIN, if set\n",
       "  2. `fathom` on your PATH\n",
       "  3. target/release/fathom, in this directory or any above it\n",
       "Build it with `cargo build --release` from the project root, or set ",
       "FATHOM_BIN to a copy you already have.", call. = FALSE)
}

# Walk UP from the working directory looking for a cargo build.
#
# The same trick `uv run` uses, and for the same reason: attempts and scripts in
# this project are run from deep subdirectories, so anything resolved relative
# to the caller has to search upward or it works only from the root. Resolving
# it relative to the INSTALLED package would be wrong in the other direction —
# once installed there is no project above it, which is exactly when PATH is the
# right answer.
fathom_dev_binary <- function(start = getwd()) {
  dir <- normalizePath(start, winslash = "/", mustWork = FALSE)
  repeat {
    candidate <- file.path(dir, "target", "release", "fathom")
    if (file.exists(candidate)) return(candidate)
    parent <- dirname(dir)
    if (identical(parent, dir)) return(NULL)
    dir <- parent
  }
}

# Every verb takes either a view or a bare path, so `fathom("f.json")` keeps
# working and `read_json("f.json") |> fathom()` also does. One place, rather
# than the same checks written into each verb.
#
# A bare path becomes a view WITHOUT running the health check, because
# `fathom()` is about to report soundness anyway and paying for it twice would
# be the one waste this design set out to avoid.
.view_of <- function(x) {
  if (inherits(x, "fathom_view")) {
    return(x)
  }
  if (!is.character(x) || length(x) != 1L || is.na(x)) {
    stop("give a path or a view from `read_json()`", call. = FALSE)
  }
  if (!file.exists(x)) {
    stop("no such file: ", x, call. = FALSE)
  }
  structure(list(source = x, at = character(0), health = ""),
            class = "fathom_view")
}

# `--at name` once per name. The binding never resolves anything: it hands the
# core the names in order and the core decides what each one means.
.at_args <- function(v) {
  # `rbind("--at", character(0))` does not give an empty vector, it recycles,
  # which sent a bare `--at` to the core with nothing after it.
  if (!length(v$at)) return(character(0))
  as.character(rbind("--at", v$at))
}

#' Go into a part of the document, and come back out
#'
#' `into()` moves you one name deeper; `back()` moves you out one level.
#' Neither reads the document — a view is a source and a path, so navigating is
#' list arithmetic and costs nothing until you ask a question.
#'
#' **Going in is how you make the expensive question cheap.** Describing a whole
#' 18 MB document takes about 6 seconds; describing one part of it takes a
#' fraction, because the walk, the fold, the classifier and the pricing all run
#' on what you are standing on. Measured: `--at webassembly` is 66x faster than
#' the root.
#'
#' **It is also how you look inside a nested cell.** `rows()` hands nested
#' values back as JSON text rather than parsing them, because a parser in the
#' binding would be a second implementation and the two languages' parsers do
#' not agree. So the way in is to stand there instead.
#'
#' A name resolves three ways, and the report says which one happened:
#' on an object with that field you get the field; on an array you get that
#' field from every item; on an object without it you get that field from every
#' value, which is a keyed collection. The resolved path is printed by
#' `fathom()` as `at $.versions.*.dependencies`, so the `*` that means *mapped
#' over every value here* is something you are shown rather than something you
#' type.
#'
#' @param x A view from `read_json()`, or a path.
#' @param name The name to go into.
#' @return A `fathom_view`, one level deeper or shallower.
#' @examples
#' \dontrun{
#' read_json("package.json") |> into("versions") |> fathom()
#' read_json("package.json") |> into("versions") |> into("dependencies") |> fathom()
#' read_json("package.json") |> into("versions") |> back() |> fathom()
#' }
#' @export
into <- function(x, name) {
  if (!is.character(name) || length(name) != 1L || is.na(name)) {
    stop("`name` must be a single name to go into", call. = FALSE)
  }
  v <- .view_of(x)
  v$at <- c(v$at, name)
  v
}

#' @rdname into
#' @export
back <- function(x) {
  v <- .view_of(x)
  if (!length(v$at)) {
    stop("already at the top of the document; there is nowhere to go back to",
         call. = FALSE)
  }
  v$at <- v$at[-length(v$at)]
  v
}

#' Read a JSON source, and say whether it is sound
#'
#' The first word. Everything else takes what this returns.
#'
#' A view is a source and where you are standing in it. It cannot hold the
#' parsed document — that lives in the core and ends with the call — so it holds
#' the source and a path, which is what makes `into()` and `back()` free and what
#' makes a chain possible at all.
#'
#' **It reports damage rather than raising on it.** A truncated file gives you a
#' view that says so; it does not throw. `fathom()` on that view still prints the
#' full diagnosis, with the parser's line and column. Refusing would replace a
#' good report with a worse exception, and there is no such thing as a broken
#' data frame, so nothing in the rectangular world prepares you for the reply.
#'
#' Checking costs about 1% of a `fathom()` — a parse is 0.05s on 18 MB, where
#' describing the same document is 4.7s — so soundness is answered up front and
#' the expensive question is asked only when you ask it.
#'
#' @param source Path to one file: JSON, NDJSON, or gzipped.
#' @param text A JSON document already in memory, as one string. Give exactly
#'   one of `source` or `text`. Named rather than guessed, because a string that
#'   might be either is the wart every other reader has.
#' @return A `fathom_view`. Print it to see the source, its soundness, and where
#'   you are standing.
#' @examples
#' \dontrun{
#' read_json("package.json")
#' read_json(text = '{"a": [1, 2, 3]}')
#' }
#' @export
read_json <- function(source = NULL, text = NULL) {
  if (is.null(source) == is.null(text)) {
    stop("give exactly one of `source` (a path) or `text` (a JSON string)",
         call. = FALSE)
  }

  if (!is.null(text)) {
    if (!is.character(text) || length(text) != 1L || is.na(text)) {
      stop("`text` must be a single string", call. = FALSE)
    }
    # The core reads files, so a document already in memory is written to one.
    # Handing bytes to a subprocess is plumbing, not behaviour. It lives in the
    # session's temp directory and goes when the session does.
    source <- tempfile("fathom-source-", fileext = ".json")
    con <- file(source, "wb")
    writeBin(charToRaw(text), con)
    close(con)
  } else {
    if (!is.character(source) || length(source) != 1L || is.na(source)) {
      stop("`source` must be a single file path", call. = FALSE)
    }
    if (!file.exists(source)) {
      stop("no such file: ", source, call. = FALSE)
    }
  }

  # The health line as TEXT, not as JSON. A binding that parsed JSON would be a
  # second parser, and R cannot represent JSON's number range anyway.
  binary <- fathom_binary()
  out <- tempfile("fathom-health-")
  on.exit(unlink(out), add = TRUE)
  status <- system2(binary, c("health", source), stdout = out, stderr = FALSE)
  health <- if (identical(as.integer(status), 0L) && file.exists(out)) {
    trimws(paste(readLines(out, warn = FALSE), collapse = "\n"))
  } else {
    "could not be read"
  }

  structure(list(source = source, at = character(0), health = health),
            class = "fathom_view")
}

#' @export
print.fathom_view <- function(x, ...) {
  where <- if (length(x$at)) paste0("$.", paste(x$at, collapse = ".")) else "$"
  cat(sprintf("<view %s>\n  %s\n", where, x$health))
  invisible(x)
}

#' Describe a JSON document
#'
#' Reads a JSON, NDJSON or gzipped file and prints what is in it: whether it is
#' sound, the shapes it holds folded to their structure, the fields that change
#' type, and what one row could be with every candidate priced.
#'
#' The output is proportional to the STRUCTURE, not to the data. That is the
#' whole claim, and it is why this is worth running on a file too large to open.
#'
#' @param path Path to one file.
#' @return A `fathom_report`: the printed text, with a `print` method. Returned
#'   rather than printed eagerly so that `x <- fathom(f)` is silent and
#'   `fathom(f)` at the console is not — which is R's own convention, and which
#'   makes this behave exactly like the Python binding. `design/vocabulary.md`
#'   requires the two languages to differ by the pipe alone.
#' @examples
#' \dontrun{
#' fathom("package.json")
#' }
#' @export
fathom <- function(path) {
  v <- .view_of(path)

  binary <- fathom_binary()

  # Captured through FILES rather than `stdout = TRUE`, which returns a
  # character vector of lines and silently loses the difference between text
  # ending in one newline and text ending in two. The report ends in a blank
  # line, and `test/bindings.py` compares bytes.
  out <- tempfile("fathom-out-")
  err <- tempfile("fathom-err-")
  on.exit(unlink(c(out, err)), add = TRUE)

  status <- system2(binary, c("probe", v$source, .at_args(v)),
                    stdout = out, stderr = err)
  if (!identical(as.integer(status), 0L)) {
    message <- if (file.exists(err) && file.size(err) > 0) {
      paste(readLines(err, warn = FALSE), collapse = "\n")
    } else {
      paste0("the fathom binary exited with status ", status)
    }
    stop(message, call. = FALSE)
  }

  text <- if (file.size(out) > 0) {
    readChar(out, file.size(out), useBytes = TRUE)
  } else {
    ""
  }
  Encoding(text) <- "UTF-8"
  structure(text, class = "fathom_report")
}

#' Take a table out of a JSON document
#'
#' `fathom()` prints a menu under `ONE ROW COULD BE`, with every candidate
#' priced. `rows()` takes one of those labels, verbatim, and returns that table.
#'
#' The label is the whole argument. You are not guessing at a path — you are
#' naming a row shape the report just showed you and told you the size of.
#'
#' Every cell holds a JSON value, as text: a string arrives quoted, a number
#' bare, and a nested array or object arrives as JSON. That is deliberate.
#' 17 of 19 corpus extracts carry a column whose values are nested, and a data
#' frame has nowhere to put one — so fathom hands it to you intact rather than
#' flattening it behind your back. Parse the columns you care about with
#' whatever you already use.
#'
#' **An empty cell means the field was ABSENT. A cell reading `null` means the
#' field was there and null.** Those are different things and this keeps them
#' apart.
#'
#' @param path Path to one file.
#' @param candidate The label to take, exactly as `fathom()` printed it.
#' @return A `data.frame`, one row per thing, every column character.
#' @examples
#' \dontrun{
#' fathom("package.json")
#' rows("package.json", "an entry of versions")
#' }
#' @export
rows <- function(path, candidate) {
  v <- .view_of(path)
  if (!is.character(candidate) || length(candidate) != 1L || is.na(candidate)) {
    stop("`candidate` must be one label, exactly as the report printed it",
         call. = FALSE)
  }

  binary <- fathom_binary()
  out <- tempfile("fathom-rows-")
  err <- tempfile("fathom-err-")
  on.exit(unlink(c(out, err)), add = TRUE)

  status <- system2(binary,
                    c("rows", v$source, "--candidate", shQuote(candidate), "--tsv",
                      .at_args(v)),
                    stdout = out, stderr = err)
  if (!identical(as.integer(status), 0L)) {
    message <- if (file.exists(err) && file.size(err) > 0) {
      paste(readLines(err, warn = FALSE), collapse = "\n")
    } else {
      paste0("the fathom binary exited with status ", status)
    }
    stop(message, call. = FALSE)
  }

  # Split on the tab. Every cell is ALREADY a JSON value and its quotes are part
  # of it, so nothing may strip them — that would turn the string "1" into the
  # number 1, which is the distinction the format exists to keep. An empty field
  # means absent and the four characters `null` mean present-and-null.
  #
  # This is decoding a declared wire format, which is the only thing a binding
  # is allowed to do. Anything that reshaped or re-typed the result would be a
  # second implementation, which is what the architecture exists to prevent.
  .read_tsv(out)
}

#' Find every path whose value matches, and take whichever name is there
#'
#' `find()` answers *where* — it searches by value and gives you back paths.
#' `whichever()` answers *which of these fields actually exists here*.
#'
#' @section What `find()` returns, and why it is folded:
#' Paths, FOLDED, with a count. The unfolded answer on a real document is
#' thousands of rows — the cost-proportional-to-data failure this project exists
#' to name, committed by fathom's own word. **A word that answers a question by
#' printing the data has not answered it.** So `versions.<key>.dist.tarball` and
#' its 288 matches is one row, not 288.
#'
#' @section Why the test is a NAME and not a function:
#' `find(view, "url")`, not `find(view, \(x) grepl("^http", x))`. A function
#' cannot cross a subprocess boundary, and it could not be the same function in
#' both languages if it did. A regular expression would need a regex engine in a
#' core that has one dependency on purpose. The tests are `url`, `email`,
#' `date` and `empty`, and a name still reads a year later.
#'
#' @param x A view from `read_json()`, or a path.
#' @param test One of `"url"`, `"email"`, `"date"`, `"empty"`.
#' @param ... For `whichever()`, the names to try, in the order you would try
#'   them by hand.
#' @return `find()`: a `data.frame` of `path` and `count`. `whichever()`: a
#'   `data.frame` of `key` and `value`, one row per thing where you are
#'   standing, with an empty value where none of the names was there.
#' @examples
#' \dontrun{
#' read_json("package.json") |> find("url")
#' read_json("package.json") |> into("versions") |> whichever("author", "_npmUser")
#' }
#' @export
find <- function(x, test) {
  if (!is.character(test) || length(test) != 1L || is.na(test)) {
    stop("`test` must be one of \"url\", \"email\", \"date\", \"empty\"",
         call. = FALSE)
  }
  .tsv_verb(.view_of(x), c("where", .view_of(x)$source, test))
}

#' @rdname find
#' @export
whichever <- function(x, ...) {
  names <- c(...)
  if (!length(names) || !is.character(names)) {
    stop("give at least one name to try", call. = FALSE)
  }
  v <- .view_of(x)
  .tsv_verb(v, c("whichever", v$source, names))
}

# Every table-returning verb reads the same way: run the binary with --tsv, and
# read what it printed. The reading is `read.delim` with quoting off, because
# each cell is already a JSON value and its quotes are part of it.
.tsv_verb <- function(v, argv) {
  binary <- fathom_binary()
  out <- tempfile("fathom-out-")
  err <- tempfile("fathom-err-")
  on.exit(unlink(c(out, err)), add = TRUE)
  status <- system2(binary, c(argv, "--tsv", .at_args(v)), stdout = out, stderr = err)
  if (!identical(as.integer(status), 0L)) {
    message <- if (file.exists(err) && file.size(err) > 0) {
      paste(readLines(err, warn = FALSE), collapse = "\n")
    } else {
      paste0("the fathom binary exited with status ", status)
    }
    stop(message, call. = FALSE)
  }
  .read_tsv(out)
}

# Read the wire format: split on the tab, and NOT with `read.delim`.
#
# **`read.delim` is pathological on a very long line.** The candidate `the whole
# document` puts an entire document in one row, so one line is the size of the
# file; on `01-npm-registry` that is 805 KB, and `read.delim` took **22.75
# seconds** to parse two lines of it where `readLines` took 0.00. Every document
# offers that candidate, so every document paid it — found because the binding
# test crawled, not because anything looked wrong.
#
# Splitting is also exactly what the Python binding does, so the two are the
# same operation rather than two libraries that happen to agree. Every cell is a
# JSON value, so no cell can contain a raw tab or newline, which is what makes
# the delimiter unambiguous without any quoting rules.
.read_tsv <- function(path) {
  lines <- readLines(path, warn = FALSE, encoding = "UTF-8")
  if (!length(lines)) return(data.frame())
  # `strsplit` DROPS TRAILING EMPTY FIELDS, which would lose an absent cell at
  # the end of a row and make R disagree with Python. The sentinel keeps them.
  split_row <- function(s) {
    parts <- strsplit(paste0(s, "\t."), "\t", fixed = TRUE)[[1]]
    parts[-length(parts)]
  }
  cols <- split_row(lines[1])
  if (length(lines) == 1L) {
    d <- as.data.frame(matrix(character(0), nrow = 0, ncol = length(cols)),
                       stringsAsFactors = FALSE)
    names(d) <- cols
    return(d)
  }
  m <- do.call(rbind, lapply(lines[-1], split_row))
  # An absent cell is an EMPTY FIELD and becomes NA; a cell holding JSON `null`
  # is the four characters "null" and survives as itself. That keeps the two
  # apart, which four defects in this project have turned on, and it matches
  # what the Python binding returns for the same bytes.
  m[m == ""] <- NA_character_
  d <- as.data.frame(m, stringsAsFactors = FALSE, optional = TRUE)
  names(d) <- cols
  rownames(d) <- NULL
  d
}

#' @export
print.fathom_report <- function(x, ...) {
  cat(unclass(x))
  invisible(x)
}

#' @export
as.character.fathom_report <- function(x, ...) {
  unclass(x)
}
