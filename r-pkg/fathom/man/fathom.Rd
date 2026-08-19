\name{fathom}
\alias{fathom}
\title{Describe a JSON document}
\usage{
fathom(path)
}
\arguments{
\item{path}{Path to one file: JSON, NDJSON, or gzipped.}
}
\value{
A \code{fathom_report}: the printed text, with a \code{print} method.
Returned rather than printed eagerly, so that \code{x <- fathom(f)} is silent
and \code{fathom(f)} at the console is not. That is R's own convention, and it
makes this behave exactly like the Python binding, which the design requires:
the two languages differ by the pipe alone.
}
\description{
Reads a JSON document and prints what is in it: whether it is sound, the shapes
it holds folded to their structure, the fields that change type, and what one
row could be with every candidate priced.

The output is proportional to the \strong{structure}, not to the data. That is
the whole claim, and it is why this is worth running on a file too large to
open.
}
\details{
All of the work happens in the \code{fathom} command-line binary, which this
function invokes as a subprocess. See \code{\link{fathom_binary}} for where it
is looked for and what to do when it is not found.
}
\examples{
\dontrun{
fathom("package-lock.json")

# It is text, so it can be kept, written out, or searched.
report <- fathom("package-lock.json")
writeLines(as.character(report), "described.txt")
}
}
\seealso{
\code{\link{fathom_binary}}
}
