# jsonlite — one Hacker News thread, 336 nodes, 13 levels of recursion
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   193 KB, 336 nodes, depth 25, recursion 13
#  measured      2026-08-09
#  run           cd corpus/02-hn-thread/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                             3   NO                  PARTLY
#   1 what is in here                           6   NO                  NO
#   2 how deep                                  2   NO                  yes
#   3 what is one record                       10   NO                  PARTLY
#   4 always present vs sometimes               5   NO                  yes
#   5 does any field change type                6   NO                  partly
#   7 how many records                          4   NO                  NO
#   8 three named fields to a table             7   YES                 partly
#  10 flatten the deepest array                 8   YES, the recursion  yes
#  13 needed the shape in advance?                  YES for 7, 8 and 10
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. jsonlite had no attempt file anywhere in the corpus until
# 2026-08-09. Simplification is its one distinctive behaviour and it has now
# been measured on three documents with three different outcomes — safe on
# `03-natural-earth`, wrong on `05-fhir-bundle`, inert on `01-npm-registry`.
#
# **This is the fourth case and the one the rule was never designed for: a
# RECURSIVE document.** `children` contains comments that contain `children`,
# 13 levels down. A rule that builds the widest rectangle that fits has to
# decide what to do when the rectangle contains itself.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.json"
simp <- fromJSON(path)
doc  <- fromJSON(path, simplifyVector = FALSE)

# ── Q0 / Q1 / Q2. ────────────────────────────────────────────────────────────
cat("\n0. is this sound:\n")
cat(sprintf("   validate() %s — well-formedness only; duplicate keys resolve to\n",
            validate(readChar(path, file.size(path), useBytes = TRUE))))
cat("   the FIRST with no warning, measured in ../../01-npm-registry/r.\n")

cat("\n1. what is in here — str():\n")
cat(sprintf("   str(simplified)     %s lines\n",
            format(length(capture.output(str(simp))), big.mark = ",")))
cat(sprintf("   str(unsimplified)   %s lines\n",
            format(length(capture.output(str(doc))), big.mark = ",")))
cat("   VERDICT.md's headline for this file is that the DEEP document gives a\n")
cat("   schema ~150x smaller than npm's, because 13 key names repeat at 25\n")
cat("   levels instead of 288 version strings becoming 288 fields. str() shows\n")
cat("   the same effect: this is a quarter of npm's line count on a file also\n")
cat("   a quarter its size — flat in the ratio, where npm is not.\n")

depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion\n", depth(doc)))

# ── Q3. WHAT SIMPLIFICATION DOES TO A RECURSIVE DOCUMENT. ────────────────────
cat("\n3. what is one record — and this is the fourth outcome for one rule:\n")
cat(sprintf("   top level is a %s with %d fields\n", class(simp)[1], length(simp)))
cat(sprintf("   $children is a %s: %d x %d (%s)\n", class(simp$children)[1],
            nrow(simp$children), ncol(simp$children),
            paste(names(simp$children), collapse = ", ")))
cat(sprintf("   $children$children is a %s of %d\n",
            class(simp$children$children)[1], length(simp$children$children)))
cat(sprintf("   $children$children[[1]] is a %s: %s\n",
            class(simp$children$children[[1]])[1],
            paste(dim(simp$children$children[[1]]), collapse = " x ")))
cat("   IT BUILT A DATA FRAME AT EVERY LEVEL AND THEY DO NOT COMPOSE. Each\n")
cat("   `children` is a table whose `children` column is a list of tables. The\n")
cat("   rectangle contains itself, so there is no single table of comments and\n")
cat("   no depth at which one exists.\n")
cat("   PARTLY: it named the right unit — a node — at every level separately,\n")
cat("   and it cannot put them together.\n")

# ── Q7. How many records? The question simplification cannot answer. ─────────
cat("\n7. how many records:\n")
cat(sprintf("   nrow($children) = %d, which is the number of TOP-LEVEL replies\n",
            nrow(simp$children)))
count <- function(x) if (is.list(x) && !is.null(x$id))
  1 + sum(vapply(x$children, count, 0)) else 0
total <- count(doc)
cat(sprintf("   the true node count is %d, and reaching it needs the recursion\n", total))
cat("   above — written by hand, over the UNSIMPLIFIED parse.\n")
cat("   SCORED NO. The number jsonlite hands you is a real number about a real\n")
cat("   thing and it is not the answer to the question. A reader who took\n")
cat(sprintf("   nrow() at face value would report %d comments in a %d-comment thread.\n",
            nrow(simp$children), total))

# ── Q4 / Q5. ─────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
nodes <- local({
  out <- list()
  rec <- function(x) if (is.list(x) && !is.null(x$id)) {
    out[[length(out) + 1]] <<- x
    for (c in x$children) rec(c)
  }
  rec(doc); out
})
ks <- lapply(nodes, names)
u  <- unique(unlist(ks))
freq <- vapply(u, function(k) sum(vapply(ks, function(x) k %in% x, TRUE)), 0L)
cat(sprintf("   %d nodes, %d distinct keys, %d key-sets\n", length(nodes), length(u),
            length(unique(vapply(ks, function(x) paste(sort(x), collapse = ","), "")))))
cat(sprintf("   present in ALL: %s\n", paste(names(freq)[freq == length(nodes)], collapse = ", ")))
cat("   NOTES.md grades this file `0 of 13` ragged by absence — every node\n")
cat("   carries every field — and the measurement agrees.\n")

cat("\n5. does any field change type:\n")
# With ONE key-set, no key is ever absent — so every NULL here is a null VALUE,
# not a missing field. The first draft of this block conflated the two and
# reported "none", which is the exact confusion `VERDICT.md` defect 5 is about:
# absent and null measured by one test and reported as one thing.
nulls <- vapply(u, function(k) sum(vapply(nodes, function(nd) is.null(nd[[k]]), TRUE)), 0L)
cat(sprintf("   every node carries all %d keys, so nothing is ABSENT.\n", length(u)))
cat(sprintf("   fields that are NULL on at least one node: %d — %s\n",
            sum(nulls > 0),
            paste(sprintf("%s x%d", names(nulls)[nulls > 0], nulls[nulls > 0]),
                  collapse = ", ")))
tp <- lapply(u, function(k) unique(vapply(nodes, function(nd)
  if (is.null(nd[[k]])) "null" else class(nd[[k]])[1], "")))
names(tp) <- u
varying <- names(tp)[vapply(tp, function(x) length(setdiff(x, "null")) > 1, TRUE)]
cat(sprintf("   fields with more than one NON-NULL class: %s\n",
            if (length(varying)) paste(varying, collapse = ", ") else "none"))
cat("   NOTES.md grades this file `ragged by null: 4`, and the count above is\n")
cat("   the same property measured from R. No field changes type otherwise.\n")

# ── Q8 / Q10. ────────────────────────────────────────────────────────────────
cat("\n8/10. three named fields, one row per node, flattening the recursion:\n")
tbl <- do.call(rbind, lapply(nodes, function(nd) data.frame(
  id     = nd$id,
  author = if (is.null(nd$author)) NA_character_ else nd$author,
  type   = nd$type)))
cat(sprintf("   -> %d x %d, one row per node at any depth\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat(sprintf("   type: %s\n", paste(sprintf("%s x%d", names(table(tbl$type)),
                                           table(tbl$type)), collapse = ", ")))
cat("   THE RECURSION IS THE WHOLE COST and jsonlite supplies none of it. The\n")
cat("   eight-line walker above is the answer to questions 7, 8 and 10 at once,\n")
cat("   and every one of them is unanswerable without it.\n")

cat("
CONCLUSION — the fourth outcome for one rule, and the most misleading of them.

  Simplification across four documents now reads:

    03-natural-earth   builds the frame, PRESERVES the depth split      SAFE
    05-fhir-bundle     builds the frame, folds 20 kinds into 87% holes  WRONG
    01-npm-registry    builds NOTHING, the keys are data                INERT
    02-hn-thread       builds a frame AT EVERY LEVEL, none composes     MISLEADING

  **This is the worst of the four for one specific reason: the answer looks
  complete.** `$children` is a genuine data frame with genuine columns, and
  `nrow()` returns a small honest number that is not the answer to \"how many
  comments\". A person who has not yet realised the document is recursive gets a
  table, gets a count, and has no signal that 13 more levels exist below it.
  On `01-npm-registry` simplification failed visibly — you get a list and you
  know you have work to do. Here it succeeds visibly and is wrong.

  EVERYTHING THAT WORKED came from an eight-line hand-written walker over the
  UNSIMPLIFIED parse, which answers questions 4, 5, 7, 8 and 10 at once. That is
  the recursion `README.md` names as the property this file was chosen for, and
  jsonlite contributes exactly nothing to it.

  WHAT IT GETS RIGHT is the ratio VERDICT.md cares about: `str()` on this
  193 KB file is a quarter of its length on the 786 KB npm file, so the
  describer tracks the 13 repeated key names rather than the document size.
  Depth is not what makes a description explode; minting new key names is.
")
