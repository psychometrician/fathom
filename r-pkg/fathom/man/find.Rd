\name{find}
\alias{find}
\alias{whichever}
\title{Find every path whose value matches, and take whichever name is there}
\usage{
find(x, test)

whichever(x, ...)
}
\arguments{
\item{x}{A view from \code{\link{read_json}}, or a path.}

\item{test}{One of \code{"url"}, \code{"email"}, \code{"date"}, \code{"empty"}.}

\item{...}{For \code{whichever()}, the names to try, in the order you would try
them by hand.}
}
\value{
\code{find()}: a \code{data.frame} of \code{path} and \code{count}.

\code{whichever()}: a \code{data.frame} of \code{key} and \code{value}, one row
per thing where you are standing, with an empty value where none of the names
was there.
}
\description{
\code{find()} answers \emph{where} -- it searches by value and gives you back
paths. \code{whichever()} answers \emph{which of these fields actually exists
here}.
}
\section{What find() returns, and why it is folded}{
Paths, folded, with a count. The unfolded answer on a real document is thousands
of rows -- the cost-proportional-to-data failure this project exists to name,
committed by fathom's own word. \strong{A word that answers a question by
printing the data has not answered it.} So \code{versions.<key>.dist.tarball}
and its 288 matches is one row, not 288.
}
\section{Why the test is a name and not a function}{
\code{find(view, "url")}, not \code{find(view, function(x) grepl("^http", x))}.

A function cannot cross a subprocess boundary, and it could not be the same
function in both languages if it did. A regular expression would need a regex
engine in a core that has one dependency on purpose. The tests are \code{url},
\code{email}, \code{date} and \code{empty} -- and a name still reads a year
later, which is the bar this vocabulary is held to.
}
\section{Path variance, which is what whichever is for}{
A document that spells the same field \code{Rating} in some records and
\code{rating} in others is answered by asking for both. A null counts as absent,
because a field that is present and null has not told you anything, so the next
name gets its turn.
}
\examples{
\dontrun{
read_json("package.json") |> find("url")
read_json("package.json") |> find("empty")

read_json("package.json") |>
  into("versions") |>
  whichever("author", "_npmUser")
}
}
\seealso{\code{\link{read_json}}, \code{\link{into}}, \code{\link{rows}}}
