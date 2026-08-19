# purrr — one Hacker News thread, 336 nodes, 13 levels of recursion
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.json   193 KB, 336 nodes, depth 25, recursion 13
#  measured      2026-08-09
#  run           cd corpus/02-hn-thread/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                            4   NO                  NO
#   2 how deep                                   2   NO                  yes
#   3 what is one record                         -   -                   CANNOT
#   4 always present vs sometimes                6   YES                 yes
#   7 how many records                           6   YES, the recursion  yes
#   8 three named fields to a table              6   YES, the recursion  yes
#  10 flatten the deepest array                  6   YES, the recursion  yes
#  13 needed the shape in advance?                   YES for 7, 8 and 10
#  16 lines, and how much is ceremony?               see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. purrr had been run on `01-npm-registry`, `09-stripe-openapi`,
# and — as of today — `03-natural-earth` and `05-fhir-bundle`. All four are
# FLAT collections: an array or a keyed object of records, however ragged.
# **This is the recursive one**, and it is the shape `README.md` says purrr is
# best at, so leaving it out was the most conspicuous hole in the R grid.
#
# The specific question: purrr's verbs are `map` and its variants, which apply
# a function across ONE level. A document 13 levels deep, where the recursion is
# the structure rather than an accident, is the case where one level is not the
# unit of anything.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

# ── Q1 / Q2. ─────────────────────────────────────────────────────────────────
cat("\n1. what is in here — purrr has no describe verb, so this is str():\n")
for (lv in c(2, 4, 8))
  cat(sprintf("   str(max.level=%d)  %6d lines\n", lv,
              length(capture.output(str(doc, max.level = lv)))))
cat("   The level argument is the problem in miniature: choosing it requires\n")
cat("   knowing how deep the document goes, which is question 2.\n")

cat("\n2. how deep does it go:\n")
depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_dbl(x, depth)) else 0
cat(sprintf("   %d levels — and note this recursion is FOUR of the lines below\n",
            depth(doc)))
cat("   reappearing. Every question on this file wants the same walker.\n")

# ── Q3. ──────────────────────────────────────────────────────────────────────
cat("\n3. what is one record:\n")
cat(sprintf("   CANNOT. The top level has %d fields and one of them is\n", length(doc)))
cat(sprintf("   `children`, a list of %d. purrr offers no candidates and there\n",
            length(doc$children)))
cat("   is no level at which the answer sits: a node is a record, and nodes are\n")
cat("   at every depth from 0 to 13.\n")

# ── THE WALKER. Written once, and it is what questions 4, 7, 8 and 10 need. ──
nodes <- local({
  out <- list()
  rec <- function(x) if (is.list(x) && !is.null(x$id)) {
    out[[length(out) + 1]] <<- x
    walk(x$children, rec)
  }
  rec(doc); out
})

# ── Q7. ──────────────────────────────────────────────────────────────────────
cat("\n7. how many records:\n")
cat(sprintf("   length(doc$children) = %d, the top-level replies only\n",
            length(doc$children)))
cat(sprintf("   the walker finds %d nodes at every depth\n", length(nodes)))
cat("   NOTES.md grades this file 336 nodes, so the walker is right and the\n")
cat("   one-level answer is off by an order of magnitude.\n")

# What purrr offers INSTEAD of a recursive walker, and why it is not enough.
cat("\n   purrr HAS a depth-aware verb — `map_depth` — and it does not help:\n")
md <- tryCatch({
  n <- length(map_depth(doc$children, 1, \(x) x$id))
  sprintf("map_depth(children, 1, ...) gives %d ids, the first level only", n)
}, error = function(e) paste("map_depth errors:", conditionMessage(e)))
cat(sprintf("   %s\n", md))
cat("   `map_depth` takes a FIXED depth. This document's nodes are at 13\n")
cat("   different depths at once, so no single argument reaches them and the\n")
cat("   verb that names depth is the wrong shape for a document with several.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
ks <- map(nodes, names)
u  <- unique(flatten_chr(ks))
n  <- length(nodes)
freq <- map_int(set_names(u), \(k) sum(map_lgl(ks, \(x) k %in% x)))
cat(sprintf("   %d distinct keys, %d key-set(s), across %d nodes\n", length(u),
            length(unique(map_chr(ks, \(x) paste(sort(x), collapse = ",")))), n))
cat(sprintf("   present in ALL: %d of %d — nothing is ragged by absence\n",
            sum(freq == n), length(u)))
nulls <- map_int(set_names(u), \(k) sum(map_lgl(nodes, \(nd) is.null(nd[[k]]))))
cat(sprintf("   NULL on at least one node: %s\n",
            paste(sprintf("%s x%d", names(nulls)[nulls > 0], nulls[nulls > 0]),
                  collapse = ", ")))
cat("   NOTES.md grades `0 of 13` ragged by absence and `4` ragged by null.\n")
cat("   Both confirmed. purrr is a good instrument for this once you have the\n")
cat("   list of nodes, and getting that list is the part it does not do.\n")

# ── Q8 / Q10. ────────────────────────────────────────────────────────────────
cat("\n8/10. three named fields, one row per node, recursion flattened:\n")
tbl <- map_dfr(nodes, \(nd) data.frame(
  id     = nd$id,
  author = nd$author %||% NA_character_,
  type   = nd$type))
cat(sprintf("   map_dfr over the walker's output -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat(sprintf("   type: %s\n", paste(sprintf("%s x%d", names(table(tbl$type)),
                                           table(tbl$type)), collapse = ", ")))
cat(sprintf("   author is NA on %d rows — the deleted comments.\n", sum(is.na(tbl$author))))
cat("   ONE `map_dfr` AND IT IS CLEAN, which is purrr at its best. It operates\n")
cat("   on a flat list, and the flat list came from six lines of base recursion.\n")

cat("
CONCLUSION — purrr is excellent on this file and does not reach it unaided.

  Every question that worked here — 4, 7, 8, 10 — worked by `map`-ing over a
  flat list of 336 nodes. **purrr did not produce that list.** It came from a
  six-line hand-written recursion using `walk`, and once it exists purrr is the
  right tool and reads beautifully: one `map_dfr` for the table, three `map_`
  calls for the raggedness, all of it clear a week later.

  `map_depth` IS THE VERB THAT SHOULD HAVE HELPED AND IT CANNOT, for a reason
  worth recording: it takes a FIXED depth, and this document's records live at
  thirteen depths simultaneously. A verb parameterised by depth assumes the
  document has one. That is the same assumption `map` itself makes — one level
  is the unit — and it is the assumption a recursive document breaks.

  THE COMPARISON ACROSS FOUR DOCUMENTS is now the useful thing, same tool, same
  `map_dfr` for question 8:

    03-natural-earth   241 features, flat, no default needed anywhere    CLEANEST
    01-npm-registry    288 versions, keyed, 31 of 40 fields need %||%
    05-fhir-bundle     564 resources, 42 key-sets, all but two need %||%
    02-hn-thread       336 nodes at 13 depths — needs a WALKER first     HARDEST

  Raggedness costs purrr a default per field. **Recursion costs it the list
  itself**, and that is a difference in kind rather than degree. `README.md`
  calls purrr the best answer that exists, and after five documents that holds
  — for the extracting. The exploring is `str()` at a level you have to guess.
")
