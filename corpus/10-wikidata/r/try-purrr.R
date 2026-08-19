# purrr — Wikidata entity Q30 (United States), full JSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.json   1.47 MB, depth 13, 19,149 paths, 48 fields,
#                                 7 keyed sites, explosion 398.9
#  measured      2026-08-10
#  run           cd corpus/10-wikidata/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                            4   NO                  NO
#   2 how deep                                   2   NO                  yes
#   3 what is one record                         -   -                   CANNOT
#   4 always present vs sometimes                7   YES                 yes
#   5 does any field change type                 7   YES                 yes
#   6 are any keys actually data                 -   -                   n/a
#   7 how many records                           2   YES                 yes
#   8 three named fields to a table              6   YES                 yes
#   9 a field missing from some rows             4   YES                 yes
#  13 needed the shape in advance?                   YES for everything but 2
#  16 lines, and how much is ceremony?               see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. purrr has now been measured on both ends of the RAGGEDNESS axis
# (`03-natural-earth` needed no `%||%` anywhere, `05-fhir-bundle` needed one on
# every field but two) and on RECURSION (`02-hn-thread` needed a hand-written
# walker before purrr could start).
#
# This is the fifth axis and the one `map` is least suited to by construction: a
# document whose repetition is **keyed by identifier**. `claims` is 469 property
# ids and `labels` is 393 language codes, so the thing to iterate is `names()`
# and the thing you want to keep is the name itself.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
ent <- doc$entities$Q30

# ── Q1 / Q2 / Q7. ────────────────────────────────────────────────────────────
cat("\n1. what is in here — purrr has no describe verb, so this is str():\n")
for (lv in c(2, 4))
  cat(sprintf("   str(max.level=%d)  %6d lines\n", lv,
              length(capture.output(str(doc, max.level = lv)))))

depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_dbl(x, depth)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion over map_dbl\n", depth(doc)))
cat(sprintf("7. %d claims, %d labels — after naming both\n",
            length(ent$claims), length(ent$labels)))

# ── Q3. ──────────────────────────────────────────────────────────────────────
cat("\n3. what is one record:\n")
cat("   CANNOT. Defensible answers include one property (469), one statement\n")
cat("   (more), one label (393) and one sitelink (425). purrr offers none of\n")
cat("   them and prices none of them, which is question 3's whole point.\n")

# ── Q8. imap IS THE VERB, and it is the one purrr has for this. ──────────────
cat("\n8. three named fields, one row per claim:\n")
tbl <- imap_dfr(ent$claims, \(stmts, pid) {
  s <- stmts[[1]]
  data.frame(property = pid,
             rank     = s$rank %||% NA_character_,
             snaktype = s$mainsnak$snaktype %||% NA_character_)
})
cat(sprintf("   imap_dfr over claims -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat("   `imap_dfr` IS THE RIGHT VERB AND IT IS PURRR'S BEST ANSWER ON THIS FILE.\n")
cat("   It hands the function the name alongside the value, so the property id\n")
cat("   survives as a column instead of becoming an address. jsonlite needed\n")
cat("   `do.call(rbind, lapply(names(...)))` for the same thing.\n")
cat("   WHAT IT DOES NOT DO is tell you the names are data. `imap` is equally\n")
cat("   happy over a record's fields, where the name is NOT data, and nothing\n")
cat("   distinguishes the two cases.\n")

# ── Q4 / Q9. ─────────────────────────────────────────────────────────────────
cat("\n4/9. always present vs sometimes, across the 469 mainsnaks:\n")
snaks <- map(ent$claims, \(p) p[[1]]$mainsnak)
ks <- map(snaks, names)
u  <- unique(flatten_chr(ks))
n  <- length(ks)
freq <- map_int(set_names(u), \(k) sum(map_lgl(ks, \(x) k %in% x)))
for (k in names(sort(freq, decreasing = TRUE)))
  cat(sprintf("     %-12s %4d of %d\n", k, freq[[k]], n))
missing <- names(freq)[freq < n]
cat(sprintf("   %d of %d keys are absent from at least one — %s\n",
            length(missing), length(u), paste(missing, collapse = ", ")))
if (length(missing)) {
  who <- keep(names(snaks), \(p) !(missing[1] %in% names(snaks[[p]])))
  cat(sprintf("   the %d without `%s`: %s\n", length(who), missing[1],
              paste(who, collapse = ", ")))
  cat(sprintf("   snaktype there: %s\n",
              paste(unique(map_chr(who, \(p) snaks[[p]]$snaktype)), collapse = ", ")))
  cat("   AND THAT EXPLAINS IT RATHER THAN PAPERING OVER IT. The missing\n")
  cat("   `datavalue` is not a hole — it is a `somevalue`/`novalue` snak, which\n")
  cat("   is Wikidata saying 'this property applies and the value is unknown'.\n")
  cat("   Same shape as 05-fhir-bundle's question 9: the NA rows were four whole\n")
  cat("   resourceTypes. Raggedness keeps turning out to be a partition.\n")
}

# ── Q5. ──────────────────────────────────────────────────────────────────────
cat("\n5. does any field change type:\n")
dv <- local({
  out <- character(0)
  rec <- function(x) if (is.list(x)) {
    if (!is.null(x$datavalue) && !is.null(x$datavalue$value))
      out <<- c(out, if (is.character(x$datavalue$value)) "text" else "object")
    walk(x, rec)
  }
  rec(doc); table(out)
})
cat(sprintf("   datavalue.value: %s\n",
            paste(sprintf("%s x%s", names(dv), format(as.integer(dv), big.mark = ",")),
                  collapse = ", ")))
cat("   YES, via a hand-written `walk` recursion. purrr has no verb that finds\n")
cat("   a polymorphic field; it has verbs that count one once you name it.\n")

cat("\n6. n/a as a verb — but see question 8: `imap` is the mechanism for keys\n")
cat("   as data, with no diagnosis attached.\n")

cat("
CONCLUSION — the fifth axis, and purrr has exactly the right verb and no
opinion about when to use it.

  `imap_dfr` is the answer to this document's extraction, and it is a better
  answer than any other R tool here gives: it hands the function the KEY
  alongside the value, so 469 property ids arrive as a column rather than
  becoming addresses. jsonlite needs `do.call(rbind, lapply(names(...)))` for the
  same result and tidyjson needs `gather_object`. purrr's version is the
  shortest and the clearest.

  **And it is equally happy in the case where the name is NOT data.** `imap` over
  a record's fields is the same call, and nothing in purrr distinguishes a
  registry keyed by version string from an object whose keys are field names.
  That is operation 2 stated as an absence: the mechanism is present in every one
  of these tools, the diagnosis is present in none.

  THE ACROSS-FILE COMPARISON, same tool, question 8 each time:

    03-natural-earth   flat, regular          — no default, no imap    CLEANEST
    10-wikidata        keyed by identifier    — imap_dfr, key kept
    01-npm-registry    keyed, ragged          — 31 of 40 need %||%
    05-fhir-bundle     42 key-sets            — all but two need %||%
    02-hn-thread       recursive, 13 depths   — needs a WALKER first   HARDEST

  QUESTION 9 REPEATED A PATTERN. The one mainsnak without a `datavalue` is not a
  hole: it is a `somevalue` snak, Wikidata's way of asserting a property with an
  unknown value. On `05-fhir-bundle` the rows missing `status` were four whole
  resourceTypes. **Twice now, on unrelated documents, what looked like
  raggedness turned out to be a partition wearing a disguise**, and `%||% NA`
  is the idiom that hides it both times.
")
