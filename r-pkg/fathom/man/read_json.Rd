\name{read_json}
\alias{read_json}
\alias{print.fathom_view}
\title{Read a JSON source, and say whether it is sound}
\usage{
read_json(source = NULL, text = NULL)
}
\arguments{
\item{source}{Path to one file: JSON, NDJSON, or gzipped.}

\item{text}{A JSON document already in memory, as one string. Give exactly one
of \code{source} or \code{text}. Named rather than guessed, because a string
that might be either is the wart every other reader has.}
}
\value{
A \code{fathom_view}: a source, and where you are standing in it. Print it to
see the source, its soundness, and your position.
}
\description{
The first word. Everything else takes what this returns.

A view cannot hold the parsed document -- that lives in the core and ends with
the call -- so it holds the source and a path. That is what makes navigation
free, and what makes a chain possible at all.
}
\details{
\strong{It reports damage rather than raising on it.} A truncated file gives you
a view that says \code{chopped off}; it does not throw. \code{\link{fathom}} on
that view still prints the full diagnosis, with the parser's line and column.
Refusing would replace a good report with a worse exception -- and there is no
such thing as a broken data frame, so nothing in the rectangular world prepares
you for the reply.

Checking costs about 1\% of a \code{fathom()}. A parse is 0.05s on 18 MB where
describing the same document is 4.7s, so soundness is answered up front and the
expensive question is asked only when you ask it.
}
\examples{
\dontrun{
read_json("package.json")
read_json(text = '{"a": [1, 2, 3]}')

read_json("package.json") |> fathom()
read_json("package.json") |> rows("an entry of versions")
}
}
\seealso{\code{\link{fathom}}, \code{\link{rows}}}
