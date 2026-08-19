\name{into}
\alias{into}
\alias{back}
\title{Go into a part of the document, and come back out}
\usage{
into(x, name)

back(x)
}
\arguments{
\item{x}{A view from \code{\link{read_json}}, or a path.}

\item{name}{The name to go into.}
}
\value{
A \code{fathom_view}, one level deeper or shallower.
}
\description{
\code{into()} moves you one name deeper; \code{back()} moves you out one level.
Neither reads the document. A view is a source and a path, so navigating is list
arithmetic and costs nothing until you ask a question.
}
\details{
\strong{Going in is how you make the expensive question cheap.} The walk, the
fold, the classifier and the pricing all run on what you are standing on, so
describing one part of a large document costs a fraction of describing the whole
of it. Measured on an 18 MB file: the root takes about 6 seconds and one part of
it takes 0.09 seconds.

\strong{It is also how you look inside a nested cell.} \code{\link{rows}} hands
nested values back as JSON text rather than parsing them, because a parser in
the binding would be a second implementation of the one thing the core exists to
do -- and the two languages' JSON parsers do not agree on numbers past 2^53. So
the way in is to stand there instead.

A name resolves three ways. On an object that has that field, you get the field.
On an array, you get that field from every item. On an object that does not have
it, you get that field from every value, which is a keyed collection.

The resolved path is printed by \code{\link{fathom}} as
\code{at $.versions.*.dependencies}, so the \code{*} that means \emph{mapped over
every value here} is something you are shown rather than something you type.
}
\examples{
\dontrun{
read_json("package.json") |> into("versions") |> fathom()

read_json("package.json") |>
  into("versions") |>
  into("dependencies") |>
  rows("an entry of $[]")

read_json("package.json") |> into("versions") |> back() |> fathom()
}
}
\seealso{\code{\link{read_json}}, \code{\link{fathom}}, \code{\link{rows}}}
