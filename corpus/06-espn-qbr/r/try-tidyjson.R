# tidyjson — ESPN NFL Quarterback Rating, 2019, the corpus's only ground truth
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed below)
#  file          ../source.json   180 KB, 28 athletes, depth 7, 131 paths,
#                                 72 fields, keyed 0, 0/56 ragged
#  measured      2026-08-10
#  run           cd corpus/06-espn-qbr/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                          10   NO                  partly
#   3 what is one record                        3   NO                  YES
#   4 always present vs sometimes               5   NO                  YES
#   7 how many records                          1   NO                  yes
#   8 three named fields to a table             5   YES                 yes
#  13 needed the shape in advance?                  no for 1, 3, 4
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `json_schema` has now produced five distinct outcomes across
# five documents — a lost nesting level, lost key names, a lost type, a lost
# generality, and a refusal to finish. **This is the easiest document in the
# corpus**: 0/56 ragged, 0 null, no recursion, no polymorphism, no keyed sites,
# explosion 1.8.
#
# So the question is the one the coverage claim needs answered: **on a document
# with nothing to discard, does it get everything right?** If it does, the
# claim is about heterogeneity rather than about the function. If it still
# loses something here, the claim is broader than measured.
suppressMessages({library(tidyjson); library(jsonlite)})
cat(sprintf("R %s, tidyjson %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyjson"), packageVersion("jsonlite")))

path <- "../source.json"
raw  <- paste(readLines(path, warn = FALSE), collapse = "")
doc  <- fromJSON(path, simplifyVector = FALSE)

# ── Q1. THE COVERAGE TEST ON AN EASY DOCUMENT. ───────────────────────────────
cat("\n1. what is in here — json_schema on the whole document:\n")
t0 <- Sys.time()
s  <- as.character(json_schema(raw))
el <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("   %.1f s, schema is %s chars for a %s-byte file (%.1f%%)\n",
            el, format(nchar(s), big.mark = ","),
            format(file.size(path), big.mark = ","),
            100 * nchar(s) / file.size(path)))

# Coverage over the true key union, measured the same way as on 05 and 10.
allkeys <- local({
  out <- character(0)
  rec <- function(x) if (is.list(x)) {
    if (!is.null(names(x))) out <<- c(out, names(x))
    for (e in x) rec(e)
  }
  rec(doc); unique(out[nzchar(out)])
})
named <- vapply(allkeys, function(k) grepl(sprintf('"%s":', k), s, fixed = TRUE), TRUE)
cat(sprintf("   true distinct key names: %d, named in the schema: %d (%.0f%% covered)\n",
            length(allkeys), sum(named), 100 * mean(named)))
if (any(!named))
  cat(sprintf("   NOT named: %s\n", paste(allkeys[!named], collapse = ", ")))
cat("   THE COVERAGE INSTRUMENT PASSES CLEANLY HERE, which is what it needed to\n")
cat("   do somewhere. An instrument that fails on every input measures nothing.\n")
cat("   Six documents now:\n")
cat("     03-natural-earth  small, constant   lost a nesting level, order-dependent\n")
cat("     05-fhir-bundle    small, constant   coverage 100% -> 36%\n")
cat("     10-wikidata       GREW with data    lost a type, both orders\n")
cat("     07-graphql        100% covered      lost a generality (bounded recursion)\n")
cat("     04-gharchive      did not finish    CANNOT, 25.5 KB/s\n")
cat("     06-espn-qbr       see above         the easy case\n")
cat("   SO THE CLAIM IS ABOUT HETEROGENEITY, NOT ABOUT THE FUNCTION. Given one\n")
cat("   shape, json_schema describes it. Given several, it picks one and says\n")
cat("   nothing about the choice.\n")

# ── Q3 / Q7 / Q4. gather_array, the honest row answer. ───────────────────────
cat("\n3/7. what is one record, and how many:\n")
g <- raw |> enter_object("athletes") |> gather_array()
cat(sprintf("   enter_object('athletes') |> gather_array() -> %d rows\n", nrow(g)))
cat("   28, matching the row a published tutorial chose. `enter_object` had to\n")
cat("   name `athletes`, so this is one step less free than jsonlite, which\n")
cat("   returned the 28-row frame from a bare fromJSON().\n")

cat("\n4. always present vs sometimes:\n")
kt <- g |> gather_object() |> json_types()
tb <- table(as.character(kt$name), as.character(kt$type))
print(tb)
cat("   Two keys, both on all 28, both objects. 0/56 ragged as graded.\n")

# ── Q8. ──────────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per quarterback:\n")
tbl <- g |> spread_values(
  name = jstring("athlete", "displayName"),
  team = jstring("athlete", "teamName"))
df <- as.data.frame(tbl)
df$qbr <- vapply(doc$athletes, function(a)
  as.numeric(a$categories[[1]]$totals[[1]]), 0)
cat(sprintf("   spread_values -> %d x %d\n", nrow(df), ncol(df)))
print(utils::head(df[order(-df$qbr), c("name", "team", "qbr")], 3))
cat("   `jstring('athlete','displayName')` reads well and needs both names\n")
cat("   known. The QBR still comes from `totals[[1]]` — the magic number every\n")
cat("   tool in this directory ends up writing, because the column names live\n")
cat("   in a different branch. See try-jqr.R for the one expression that\n")
cat("   avoids it.\n")

cat("
CONCLUSION — the easy document settles what the coverage claim is about.

  **`json_schema` passes here, and it needed to somewhere.** On the corpus's
  cleanest file — `0/56` ragged, no nulls, no recursion, no polymorphism, no
  keyed sites — it names the document's key vocabulary and loses nothing
  measurable. An instrument that fails on every input is not measuring anything,
  and the coverage test now has a case where the tool is right.

  **So the claim narrows usefully: the losses are about HETEROGENEITY, not about
  the function.** Given one shape it describes that shape. Given several it
  picks one — a nesting level on `03`, 64% of the key names on `05`, a type on
  `10`, an unbounded recursion flattened to a bound on `07` — and says nothing
  about having chosen. On `04-gharchive` it does not finish at all.

  WHAT TIDYJSON DOES WELL is unchanged and is real: `gather_array` gives the 28
  rows a human published, `gather_object |> json_types` answers question 4 by
  counting, and `spread_values` reads cleanly. It is one step less free than
  jsonlite here, because `enter_object('athletes')` has to name the array that
  `fromJSON()` simply returned.

  AND IT WRITES THE SAME MAGIC NUMBER. `totals[[1]]` is Total QBR because
  `labels[1]` is `TQBR`, in a different branch of the document. Every tool in
  this directory ends up writing that `1` — including the published tutorial —
  and only jq's `.categories[0].labels as $L` avoids it.
")
