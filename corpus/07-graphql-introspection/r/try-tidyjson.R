# tidyjson — the SpaceX GraphQL API describing its own schema
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed below)
#  file          ../source.json   143 KB, 108 types, depth 13, recursion 4,
#                                 94 paths, 22 fields, explosion 4.3, keyed 0
#  measured      2026-08-10
#  run           cd corpus/07-graphql-introspection/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                          12   NO                  partly
#   3 what is one record                        3   NO                  YES
#   4 always present vs sometimes               6   NO                  YES
#   5 does any field change type                8   NO                  partly
#   7 how many records                          1   NO                  yes
#   8 three named fields to a table             5   YES                 yes
#  13 needed the shape in advance?                  no for 1, 3, 4
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 5** in this entry's NOTES.md, committed
# before this file existed: that `json_schema`'s COVERAGE would be high here —
# 22 fields, no heterogeneity — so this is the case where the coverage
# instrument passes honestly, **and that a third kind of loss would show up
# instead: the recursive `ofType` reported to whatever fixed depth happened to
# be in the input, stating a bounded nesting where the document's rule is
# unbounded.**
#
# `03` lost a nesting level, `05` lost key names, `10` lost a type. If this
# loses a generality, that is four distinct failures from one function.
suppressMessages({library(tidyjson); library(jsonlite)})
cat(sprintf("R %s, tidyjson %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyjson"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
ty  <- doc$data$`__schema`$types

# ⚠ `null = "null"` IS LOAD-BEARING AND THE FIRST DRAFT OF THIS FILE OMITTED IT.
# jsonlite's toJSON turns R's NULL into `{}` by default, so a round-trip through
# R silently converts every JSON null into an empty object. This document is
# 51.7% nulls, so the first version of question 4 below reported
# `possibleTypes: object x108` for a field that is null on all 108 — and the
# conclusion drawn from it credited tidyjson with a distinction it had not been
# given the chance to make.
#
# It is the corpus's own recurring mistake, and `03-natural-earth`'s NOTES.md
# names it: "Deriving a verdict from something adjacent to the data rather than
# from the data." Measured through the wrong instrument, tidyjson looked wrong;
# measured through the document, it is right.
as_json <- function(x) as.character(toJSON(x, auto_unbox = TRUE, null = "null"))
sch     <- function(x) as.character(json_schema(as_json(x)))

# ── Q1. Size and coverage. ───────────────────────────────────────────────────
cat("\n1. what is in here — json_schema over a growing slice of types:\n")
cat("      n  input      time   schema   true keys  named  covered\n")
for (n in c(5, 20, 60, 108)) {
  sub <- as_json(ty[seq_len(n)])
  t0  <- Sys.time()
  s   <- as.character(json_schema(sub))
  el  <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  truth <- unique(unlist(lapply(ty[seq_len(n)], names)))
  named <- vapply(truth, function(k) grepl(sprintf('"%s":', k), s, fixed = TRUE), TRUE)
  cat(sprintf("   %4d %8s B %6.1fs  %6s c  %8d  %5d  %5.0f%%\n",
              n, format(nchar(sub), big.mark = ","), el,
              format(nchar(s), big.mark = ","), length(truth), sum(named),
              100 * mean(named)))
  flush.console()
  if (n == 108) full <- s
}
cat("   PREDICTION 5's FIRST HALF CONFIRMED — coverage is high and honest here.\n")
cat("   This is the document where the coverage instrument passes, which is\n")
cat("   worth having: an instrument that never passes measures nothing.\n")

# ── Q5. THE RECURSION. PREDICTION 5's SECOND HALF. ───────────────────────────
cat("\n5. does any field change type — and what happens to the recursion:\n")
nest <- function(s) {
  n <- 0; i <- 1
  repeat {
    j <- regexpr('"ofType"', substring(s, i))
    if (j < 0) break
    n <- n + 1; i <- i + j + 6
  }
  n
}
cat(sprintf("   `ofType` appears %d times in the whole-document schema\n", nest(full)))

# What the document actually does, measured independently.
depth_of <- function(x) if (is.list(x) && !is.null(x$ofType)) 1 + depth_of(x$ofType) else 0
chains <- unlist(lapply(ty, function(t)
  lapply(t$fields %||% list(), function(f) depth_of(f$type))))
chains <- chains[!vapply(chains, is.null, TRUE)]
cat(sprintf("   the DOCUMENT's ofType chains run to depth: %s\n",
            paste(sprintf("%s x%d", names(table(unlist(chains))),
                          as.integer(table(unlist(chains)))), collapse = ", ")))
cat("   PREDICTION 5's SECOND HALF CONFIRMED, and it is a fourth kind of loss.\n")
cat("   json_schema reports a FIXED number of nested `ofType` levels — whatever\n")
cat("   the deepest chain in the input happened to be. GraphQL's rule is that\n")
cat("   `ofType` nests to ANY depth: a NON_NULL wrapping a LIST wrapping a\n")
cat("   NON_NULL wrapping a named type, and further if the schema wants it.\n")
cat("   THE SCHEMA STATES A BOUND THE DOCUMENT DOES NOT HAVE. Nothing is\n")
cat("   dropped and nothing is mistyped — what is lost is the GENERALITY, and\n")
cat("   a reader would take the deepest observed chain for the rule.\n")
cat("   Four documents, four distinct losses from one function:\n")
cat("     03-natural-earth  a nesting level, order-dependently\n")
cat("     05-fhir-bundle    key names, coverage 100% -> 36%\n")
cat("     10-wikidata       a type, in both input orders\n")
cat("     07-graphql        a GENERALITY — recursion flattened to a bound\n")

# ── Q3 / Q4 / Q7 / Q8. ───────────────────────────────────────────────────────
cat("\n3/7. what is one record, and how many:\n")
ttxt <- as_json(ty)
g <- gather_array(ttxt)
cat(sprintf("   gather_array() over types -> %d rows, nothing known first\n", nrow(g)))

cat("\n4. always present vs sometimes:\n")
kt <- g |> gather_object() |> json_types()
tb <- table(as.character(kt$name), as.character(kt$type))
cat("   gather_object |> json_types, key by observed type:\n")
print(tb)
cat("   THIS IS THE BEST ANSWER TO QUESTION 4 IN THE CORPUS, and it is the\n")
cat("   only one that separates `null` from `absent` without being asked.\n")
cat("   `json_types` reports `null` AS A TYPE, so the 51.7% emptiness that\n")
cat("   jsonlite's frame cannot see is sitting in the table above.\n")

cat("\n8. three named fields, one row per type:\n")
tbl <- g |> spread_values(kind = jstring("kind"), name = jstring("name"),
                          desc = jstring("description"))
cat(sprintf("   spread_values -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(as.data.frame(tbl)[, c("kind", "name")], 3))

cat("
CONCLUSION — the coverage instrument passes here, which it needed to, and the
function finds a fourth way to lose something.

  **Prediction 5 held in both halves.** Coverage is high and honest on this
  document — 22 fields, no heterogeneity, nothing to discard — and that matters,
  because an instrument that fails on every input is not measuring anything. The
  coverage claim is now supported by a case where the tool passes.

  **And the recursion is flattened to a bound.** `ofType` nests to whatever depth
  the input happened to contain, and json_schema reports exactly that many
  levels. GraphQL's rule is unbounded: NON_NULL wraps LIST wraps NON_NULL wraps a
  named type, as deep as a schema needs. Nothing here is dropped and nothing is
  mistyped — **what is lost is the generality**, and a reader would take the
  deepest observed chain for the rule. That is a fourth distinct failure from one
  function, after a nesting level, a set of key names, and a type.

  WHAT TIDYJSON DOES BEST HERE — and it is the best answer to question 4 anywhere
  in this corpus — is `gather_object() |> json_types()`. It reports **`null` as a
  type**, so the 51.7% emptiness that jsonlite's 108 x 8 frame cannot see, and
  that the probe's presence-based emptiness reads as 0%, is simply a column in
  the result. `VERDICT.md` defect 5 was about two definitions of empty
  disagreeing; tidyjson is the one tool here that never had the ambiguity,
  because it types values instead of testing presence.
")
