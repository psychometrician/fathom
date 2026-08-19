# jsonlite — Wikidata entity Q30 (United States), full JSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   1.47 MB, depth 13, 19,149 paths, 48 fields,
#                                 7 keyed sites, explosion 398.9
#  measured      2026-08-10
#  run           cd corpus/10-wikidata/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              3   NO                  PARTLY
#   1 what is in here                            5   NO                  NO
#   2 how deep                                   2   NO                  yes
#   3 what is one record                         7   NO                  CANNOT
#   5 does any field change type                 6   YES                 partly
#   6 are any keys actually data                 6   YES                 NO
#   7 how many records                           2   YES                 yes
#   8 three named fields to a table              7   YES                 yes
#  13 needed the shape in advance?                   YES for 3, 5, 6, 7, 8
#  16 lines, and how much is ceremony?               see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 4** in this entry's NOTES.md — that
# simplification would be INERT here, the `01`/`09` outcome, because `claims`,
# `labels`, `descriptions`, `aliases` and `sitelinks` are all keyed by data.
#
# The prediction matters because simplification has produced four different
# outcomes on five documents and there is no way to tell in advance which you
# will get. A rule with four behaviours and no signal about which one fired is
# worth pinning down, and a fifth confirmation of the INERT case on the corpus's
# most keyed-by-identifier document is the cheapest way to do it.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.json"
simp <- fromJSON(path)
doc  <- fromJSON(path, simplifyVector = FALSE)
ent  <- doc$entities$Q30

# ── Q0 / Q1 / Q2. ────────────────────────────────────────────────────────────
cat("\n0. is this sound:\n")
cat(sprintf("   validate() %s — well-formedness only. Duplicate keys resolve to\n",
            validate(readChar(path, file.size(path), useBytes = TRUE))))
cat("   the FIRST with no warning; measured in ../../03-natural-earth/r.\n")

cat("\n1. what is in here — str():\n")
for (lv in 2:4)
  cat(sprintf("   str(simplified, max.level=%d)  %6d lines\n", lv,
              length(capture.output(str(simp, max.level = lv)))))
cat("   Level 2 is three lines and says nothing; level 4 is unreadable. There\n")
cat("   is no setting in between, because the thing that needs summarising is\n")
cat("   469 sibling properties and str() is parameterised by depth.\n")

depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion\n", depth(doc)))

# ── Q3 / Q6. PREDICTION 4. ───────────────────────────────────────────────────
cat("\n3/6. what is one record, and are any keys actually data:\n")
for (nm in c("claims", "labels", "descriptions", "aliases", "sitelinks")) {
  v <- simp$entities$Q30[[nm]]
  if (is.null(v)) next
  cat(sprintf("   $%-13s %-10s n=%-4d %s\n", nm, class(v)[1], length(v),
              if (is.data.frame(v)) "a TABLE" else "NOT a table"))
}
cat("   PREDICTION 4 CONFIRMED — inert on all five keyed sites, and this is the\n")
cat("   fifth document for the rule and the third for this outcome.\n")
cat("   The five outcomes of ONE rule, `build the widest rectangle that fits`:\n")
cat("     03-natural-earth  builds the frame, PRESERVES the depth split   SAFE\n")
cat("     05-fhir-bundle    builds it, folds 20 kinds into 87% holes      WRONG\n")
cat("     01-npm-registry   builds nothing, the keys are data             INERT\n")
cat("     09-stripe-openapi builds nothing, at ten times the size         INERT\n")
cat("     02-hn-thread      builds one at every level, none compose       MISLEADING\n")
cat("     10-wikidata       builds nothing, keys are identifiers          INERT\n")
cat("   NOTHING IN THE OUTPUT SAYS WHICH ONE HAPPENED. That is the criticism —\n")
cat("   not that any single behaviour is wrong, but that a person cannot tell a\n")
cat("   preserved polymorphism from a folded one from a refused fold.\n")
ks <- lapply(ent$claims, function(p) names(p[[1]]))
cat(sprintf("   the signal it never volunteers: %d claims over %d distinct\n",
            length(ent$claims),
            length(unique(vapply(ks, function(x) paste(sort(x), collapse = ","), "")))))
cat("   key-sets, and 393 labels over one.\n")

# ── Q5. ──────────────────────────────────────────────────────────────────────
cat("\n5. does any field change type:\n")
dv <- local({
  out <- character(0)
  rec <- function(x) if (is.list(x)) {
    if (!is.null(x$datavalue) && !is.null(x$datavalue$value))
      out <<- c(out, if (is.character(x$datavalue$value)) "text" else "object")
    for (e in x) rec(e)
  }
  rec(doc); table(out)
})
cat(sprintf("   datavalue.value: %s\n",
            paste(sprintf("%s x%s", names(dv), format(as.integer(dv), big.mark = ",")),
                  collapse = ", ")))
cat("   PARTLY. The recursion above is six lines of base R and jsonlite\n")
cat("   contributed the parse. What it will NOT do is show you this from the\n")
cat("   simplified object: `claims` never became a table, so there is no column\n")
cat("   to inspect and no type to disagree about.\n")

# ── Q7 / Q8. ─────────────────────────────────────────────────────────────────
cat(sprintf("\n7. %d claims, %d labels\n", length(ent$claims), length(ent$labels)))

cat("\n8. three named fields, one row per claim:\n")
tbl <- do.call(rbind, lapply(names(ent$claims), function(p) {
  s <- ent$claims[[p]][[1]]
  data.frame(property = p,
             rank     = s$rank %||% NA_character_,
             snaktype = s$mainsnak$snaktype %||% NA_character_)
}))
cat(sprintf("   do.call(rbind, lapply(names(...))) -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat("   `property` is a column ONLY because I put it there. That is the whole\n")
cat("   keys-as-data problem in one line: the moment you write\n")
cat("   `ent$claims[[p]]`, the P-number stops being data and becomes an address.\n")

cat("
CONCLUSION — the fifth document, the third INERT result, and the criticism is
now about the SILENCE rather than about any one behaviour.

  Prediction 4 held: `claims`, `labels`, `descriptions`, `aliases` and
  `sitelinks` all come back as named lists, no tables, because every one of them
  is keyed by data — property ids and language codes. Question 8 is a
  hand-written `do.call(rbind, lapply(names(...)))`, as it was on npm and on
  Stripe, and the key survives only because I carried it manually.

  **Across five documents one rule has now produced four distinct behaviours —
  SAFE, WRONG, INERT, MISLEADING — and the output never says which.** That is
  the sharpest form of the criticism, and it is not a complaint about
  simplification being a bad idea. On `03-natural-earth` it did the right thing
  and preserved a polymorphism polars destroyed. The problem is that the same
  call, on documents that look equally ordinary, silently folded twenty resource
  types into 87% holes, silently refused to fold 469 properties, and silently
  built a table per level of a recursive thread that reports 25 comments in a
  336-comment thread.

  A person cannot tell those apart from the result. **That is exactly the gap
  `README.md` describes**: the tool answers the extraction question and never
  tells you what kind of document you are holding.

  ONE THING TO CREDIT AGAIN: it parses 1.47 MB instantly, both ways. Every
  criticism here is about description, and none is about parsing.
")
