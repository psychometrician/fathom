\name{fathom_binary}
\alias{fathom_binary}
\title{Locate the fathom binary}
\usage{
fathom_binary(error = TRUE)
}
\arguments{
\item{error}{Whether to stop when nothing is found. \code{FALSE} returns
\code{NULL} instead, which is what a test harness wants.}
}
\value{
The path to the binary, or \code{NULL}.
}
\description{
This package does no JSON work of its own. It runs the \code{fathom}
command-line binary as a subprocess and hands back what it printed, so the
binary has to be findable.
}
\details{
Three places, in order, and the order is the point: an explicit override always
wins, an installed binary is next, and the development build is last so that
working inside the project needs no configuration.

\enumerate{
\item \code{$FATHOM_BIN}, if set. If it names a file that does not exist this
  is an error rather than a fallback: it was set on purpose, and quietly
  running some other binary is how a measurement gets attributed to the wrong
  build.
\item \code{fathom} on the \code{PATH}.
\item \code{target/release/fathom}, in the working directory or any directory
  above it. This is the development build, found by walking upward the way
  \code{uv run} finds a project, so that scripts run from a subdirectory work
  without configuration.
}

Build it with \code{cargo build --release} from the project root.
}
\examples{
\dontrun{
fathom_binary()
fathom_binary(error = FALSE)   # NULL rather than an error when absent
}
}
\seealso{
\code{\link{fathom}}
}
