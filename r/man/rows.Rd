\name{rows}
\alias{rows}
\title{Take a table out of a JSON document}
\usage{
rows(path, candidate)
}
\arguments{
\item{path}{Path to one file: JSON, NDJSON, or gzipped.}

\item{candidate}{The label to take, exactly as \code{fathom()} printed it under
\code{ONE ROW COULD BE}. The label is the whole argument.}
}
\value{
A \code{data.frame}, one row per thing, every column character. Each cell holds
a JSON value as text: a string arrives quoted, a number bare, and a nested array
or object arrives as JSON.

An empty cell means the field was \strong{absent}. A cell reading \code{null}
means the field was there and null. Those are different things and this keeps
them apart.
}
\description{
\code{fathom()} prints a menu of row shapes, each one priced. \code{rows()}
takes one of those labels and returns that table.

You are not guessing at a path. You are naming a row shape the report just
showed you and told you the size of, which is why the label is the whole
argument and why there is no path language to learn.
}
\details{
Cells are not flattened. 17 of 19 corpus extracts carry a column whose values
are nested, and a data frame has nowhere to put one, so fathom hands it over
intact rather than flattening it behind your back. Parse the columns you care
about with whatever you already use.

This package has no dependencies, so the table crosses from the binary as
tab-separated JSON values and is read with \code{read.delim}. Nothing is
reshaped or re-typed on the way: a binding that did either would be a second
implementation of the answer.
}
\examples{
\dontrun{
fathom("package.json")
rows("package.json", "an entry of versions")
}
}
\seealso{\code{\link{fathom}}}
