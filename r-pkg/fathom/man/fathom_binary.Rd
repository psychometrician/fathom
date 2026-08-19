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
Four places, in order, and the order is the point: an explicit override always
wins, a development build outranks the bundled engine, and the \code{PATH} is
last because a \code{fathom} on it has no reason to match this copy of the
package.

\enumerate{
\item \code{$FATHOM_BIN}, if set. If it names a file that does not exist this
  is an error rather than a fallback: it was set on purpose, and quietly
  running some other binary is how a measurement gets attributed to the wrong
  build.
\item \code{target/release/fathom}, in the working directory or any directory
  above it. This is the development build, found by walking upward the way
  \code{uv run} finds a project, so that scripts run from a subdirectory work
  without configuration. It comes BEFORE the bundled engine deliberately: a
  bundled copy is written at install time and then stays exactly as old as that
  install, so preferring it is how a harness spends a day measuring a stale
  engine while every check passes.
\item The engine bundled inside the installed package, which \code{configure}
  compiles and copies to \code{inst/bin} during \code{R CMD INSTALL}. This is
  what makes an installed copy self-contained: nothing else in the package ever
  creates that file, and without it a user who did not build the project has no
  engine at all.
\item \code{fathom} on the \code{PATH}.
}

An installed package carries its own engine, so this needs no configuration. In
a checkout, build one with \code{cargo build --release} from the project root.
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
