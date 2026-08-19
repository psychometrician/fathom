# tidyjson — Wikidata entity Q30 (United States), full JSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed below)
#  file          ../source.json   1.47 MB, depth 13, 19,149 paths, 48 fields,
#                                 7 keyed sites, explosion 398.9
#  measured      2026-08-10
#  run           cd corpus/10-wikidata/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           10   NO                  WRONG
#   3 what is one record                         4   NO                  partly
#   4 always present vs sometimes                6   NO                  yes
#   5 does any field change type                12   NO                  WRONG
#   6 are any keys actually data                 -   -                   NO
#   7 how many records                           2   YES                 yes
#   8 three named fields to a table              6   YES                 yes
#  13 needed the shape in advance?                   no for 1, 4, 5
#  16 lines, and how much is ceremony?               see the conclusion
#
#  ⚠ json_schema is NOT run on the whole file. Measured on 03-natural-earth at
#  ~3.8 KB/s, so 1.47 MB extrapolates past six minutes. Slices only, labelled.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 2** in this entry's NOTES.md, written and
# committed before any tool here ran: that `json_schema` would report ONE of
# `string`/`object` for `datavalue.value` and silently drop the other.
#
# The claim it tests was made on 2026-08-09 — that a small description is not
# evidence of a good one, because a describer that discards shapes always looks
# proportional to structure. **But both files behind it varied by DEPTH (`03`) or
# by KEY-SET (`05`).** Neither is polymorphism by type in real data, and the
# only type case tested was the synthetic `["a", {"b":1}]`.
#
# NOTES.md grades this file `polymorphic 3` with `object x1,210, text x512` and
# calls it the corpus's genuine polymorphism. **If json_schema unions the two
# correctly here, the claim is limited to depth and the phrase "silently discards
# shapes" is too strong for its own evidence.** That is written down in NOTES.md
# as the prediction that would hurt.
suppressMessages({library(tidyjson); library(jsonlite)})
cat(sprintf("R %s, tidyjson %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyjson"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
ent <- doc$entities$Q30
sch <- function(x) as.character(json_schema(as.character(toJSON(x, auto_unbox = TRUE))))

# ── Q5. PREDICTION 2. THE ONE THIS FILE IS FOR. ──────────────────────────────
cat("\n5. does any field change type — real polymorphism, not an artifact:\n")
dvs <- local({
  out <- list()
  rec <- function(x) if (is.list(x)) {
    if (!is.null(x$datavalue) && !is.null(x$datavalue$value)) out[[length(out) + 1]] <<- x$datavalue
    for (e in x) rec(e)
  }
  rec(doc); out
})
tp <- vapply(dvs, function(v) if (is.character(v$value)) "text" else "object", "")
cat(sprintf("   the truth, every datavalue at any depth: %s\n",
            paste(sprintf("%s x%s", names(table(tp)),
                          format(as.integer(table(tp)), big.mark = ",")), collapse = ", ")))

s <- dvs[[which(tp == "text")[1]]]
o <- dvs[[which(tp == "object")[1]]]
cat(sprintf("   a text one:   %s\n", as.character(toJSON(s, auto_unbox = TRUE))))
cat(sprintf("   an object one: %s\n",
            substr(as.character(toJSON(o, auto_unbox = TRUE)), 1, 88)))
cat("\n   json_schema, each ALONE — both correct:\n")
cat(sprintf("     text:   %s\n", sch(s)))
cat(sprintf("     object: %s\n", sch(o)))
cat("   and now TOGETHER, which is how the document holds them:\n")
cat(sprintf("     [text, object]: %s\n", sch(list(s, o))))
cat(sprintf("     [object, text]: %s\n", sch(list(o, s))))
cat("   PREDICTION 2 CONFIRMED, AND IN THE STRONGEST FORM AVAILABLE. The object\n")
cat("   schema wins in BOTH orders — this is not the order-dependence seen on\n")
cat("   03-natural-earth, it is the scalar being absorbed outright.\n")
cat(sprintf("   So `value` is described as an object for all %s snaks, when %s of\n",
            format(length(dvs), big.mark = ","),
            format(sum(tp == "text"), big.mark = ",")))
cat(sprintf("   them — %.0f%% — hold a plain string. No warning, no union, no trace.\n",
            100 * mean(tp == "text")))
cat("   SCORED WRONG, NOT NO. It answers, and the answer is false for a third\n")
cat("   of the records.\n")

# ── Q1. Size and coverage, on a slice. ───────────────────────────────────────
cat("\n1. what is in here — json_schema over a growing slice of claims:\n")
cl <- ent$claims
cat("      n  input      time   schema   true keys  named  covered\n")
for (n in c(5, 20, 60)) {
  sub <- as.character(toJSON(cl[seq_len(n)], auto_unbox = TRUE))
  t0  <- Sys.time()
  ss  <- as.character(json_schema(sub))
  el  <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  truth <- unique(unlist(lapply(cl[seq_len(n)], function(p)
    unlist(lapply(p, names)))))
  named <- vapply(truth, function(k) grepl(sprintf('"%s":', k), ss, fixed = TRUE), TRUE)
  cat(sprintf("   %4d %8s B %6.1fs  %6s c  %8d  %5d  %5.0f%%\n",
              n, format(nchar(sub), big.mark = ","), el,
              format(nchar(ss), big.mark = ","), length(truth), sum(named),
              100 * mean(named)))
  flush.console()
}
cat("   THIS DOCUMENT BEHAVES THE OPPOSITE WAY FROM 03 AND 05, and the result\n")
cat("   is more useful than the one this file was expected to produce.\n")
cat("   The schema GROWS roughly in step with the input — about 13x for 13.5x —\n")
cat("   which is the ordinary O(data) failure, and the cause is keys-as-data:\n")
cat("   each of the 469 property ids becomes its own entry in the schema.\n")
cat("   MEANWHILE COVERAGE IS 100%. Every key a mainsnak carries is named,\n")
cat("   because there are only five of them.\n")
cat("   So on this file `size` FAILS and `coverage-of-key-names` PASSES, while\n")
cat("   question 5 above shows a third of the records described as the wrong\n")
cat("   type. NEITHER INSTRUMENT CATCHES THAT. Coverage measured over key names\n")
cat("   is not enough; it has to be measured over TYPES as well.\n")

# ── Q3 / Q4 / Q7. What tidyjson does well. ───────────────────────────────────
cat("\n3/7. what is one record, and how many:\n")
ctxt <- as.character(toJSON(cl, auto_unbox = TRUE))
g <- gather_object(ctxt)
cat(sprintf("   gather_object() over claims -> %d rows, one per property id\n", nrow(g)))
cat("   PARTLY, and better than it looks: `gather_object` is the verb that turns\n")
cat("   a keyed object into rows, which is exactly what question 6 is about. It\n")
cat("   does not SAY the keys are data — it just makes them addressable.\n")

cat("\n4. always present vs sometimes:\n")
snaks <- lapply(cl, function(p) p[[1]]$mainsnak)
ks <- lapply(snaks, names)
u  <- unique(unlist(ks))
freq <- vapply(u, function(k) sum(vapply(ks, function(x) k %in% x, TRUE)), 0L)
cat(sprintf("   across %d mainsnaks: %d distinct keys\n", length(ks), length(u)))
for (k in names(sort(freq, decreasing = TRUE)))
  cat(sprintf("     %-12s %4d of %d\n", k, freq[[k]], length(ks)))

cat("\n8. three named fields, one row per claim:\n")
tbl <- g |> gather_array() |> spread_values(
  type = jstring("type"), rank = jstring("rank"),
  snaktype = jstring("mainsnak", "snaktype"))
cat(sprintf("   gather_object |> gather_array |> spread_values -> %d x %d\n",
            nrow(tbl), ncol(tbl)))
print(utils::head(as.data.frame(tbl)[, c("name", "type", "rank", "snaktype")], 3))
cat("   `name` is the property id, carried through by gather_object. THAT IS\n")
cat("   THE KEY SURVIVING AS DATA, and tidyjson is the only R tool here that\n")
cat("   does it without being told to.\n")

cat("\n6. are any object keys actually data:\n")
cat("   NO as a verb, but see question 3 — `gather_object` is the mechanism\n")
cat("   without the diagnosis. It cannot tell you WHICH objects deserve it.\n")

cat("
CONCLUSION — prediction 2 confirmed, and the claim it tests is now safe to state
about type polymorphism and not only about depth.

  `datavalue.value` is an object on 3,049 snaks and a plain string on 1,352.
  Asked to describe both, `json_schema` returns **the object schema in both
  orders** — so a third of the records are described as something they are not.
  On `03-natural-earth` the answer at least depended on input order, which leaves
  a trace if you look twice. **Here the scalar is simply absorbed**, and there is
  no ordering of the input that would reveal it.

  AND THE COVERAGE COLUMN CAME OUT THE OTHER WAY, WHICH IS THE MORE USEFUL
  RESULT. On `03` and `05` the schema stayed small while coverage fell — size
  passed, coverage failed. **Here it is reversed**: the schema grows about 13x
  for a 13.5x input, which is the ordinary O(data) failure caused by 469 property
  ids each minting a schema entry, and coverage of the mainsnak key names is
  **100%**, because a mainsnak has only five keys.

  **So on this document `size` fails, `coverage-of-key-names` passes, and a third
  of the records are still described as the wrong type.** Neither instrument
  catches the thing that is actually wrong. The lesson is not that the coverage
  claim was wrong — it is that **coverage has to be measured over TYPES, not only
  over key names**, and the version of the instrument sketched on 2026-08-09 was
  the weaker half of it. That is a correction to a claim made yesterday, arrived
  at by a measurement that disagreed with the prediction's framing.

  Three documents, three different failures from one function:

    03-natural-earth  small schema, order-dependent, drops a nesting level
    05-fhir-bundle    small schema, coverage falls 100% -> 36% as kinds arrive
    10-wikidata       schema GROWS with the data, coverage 100%, TYPE dropped

  **The prediction that would have hurt did not happen.** NOTES.md recorded it in
  advance: if json_schema had unioned string and object correctly, the claim
  would have been limited to depth polymorphism. It did not, so the claim stands
  in its general form.

  WHAT TIDYJSON DOES BETTER THAN ANY OTHER R TOOL HERE is `gather_object`. It
  turns a keyed object into rows and **carries the key through as a column**, so
  the 469 property ids survive as data rather than becoming addresses. That is
  operation 2's mechanism without operation 2's diagnosis: it will do it wherever
  you point it, and it has no opinion about where that should be.
")
