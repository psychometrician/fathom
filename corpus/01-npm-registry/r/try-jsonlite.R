# jsonlite — npm registry metadata for `express`
#
# Header shape copied from ./try-purrr.R, the template in this directory.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   786 KB, 288 versions, 25,044 paths, 6 keyed sites
#  measured      2026-08-09
#  run           cd corpus/01-npm-registry/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              5   NO                  PARTLY
#   1 what is in here                            6   NO                  NO
#   2 how deep                                   2   NO                  yes
#   3 what is one record                         7   NO                  CANNOT
#   4 always present vs sometimes                6   YES                 partly
#   6 are any keys actually data                 7   YES                 NO
#   7 how many records                           2   YES                 yes
#   8 three named fields to a table              6   YES, all four       yes
#  13 needed the shape in advance?                   YES for everything but 0-2
#  16 lines, and how much is ceremony?               see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE, AND IT COMPLETES A THREE-WAY COMPARISON. `jsonlite` had **no
# attempt file anywhere in the corpus** until 2026-08-09 — it has been imported
# as a parser inside every other R attempt and never scored as a tool, even
# though `README.md` lists it among the five R tools in the comparison.
#
# Its one distinctive behaviour is simplification: build the widest rectangle
# that fits. Measured on two other files that rule went two different ways —
# on `03-natural-earth` it was SAFE, preserving a polymorphism polars erased;
# on `05-fhir-bundle` it was WRONG, folding 20 resourceTypes into a 97-column
# frame that is 87% holes. **This file is the third case: 6 keys-as-data sites,
# the most in the corpus outside Stripe.** The prediction is that simplification
# does nothing at all here, and that is worth measuring rather than assuming.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.json"
cat(sprintf("  file is %s bytes\n", format(file.size(path), big.mark = ",")))

# ── Q0. Is this sound? ───────────────────────────────────────────────────────
cat("\n0. is this sound:\n")
raw <- readChar(path, file.size(path), useBytes = TRUE)
cat(sprintf("   validate() %s — well-formedness only.\n", validate(raw)))
dup <- fromJSON('{"a":1,"a":2}')
cat(sprintf("   duplicate keys: {\"a\":1,\"a\":2} -> a=%s, %s wins, no warning\n",
            dup$a, if (dup$a == 1) "the FIRST" else "the last"))
cat("   Python and JavaScript take the LAST. Two languages reading one damaged\n")
cat("   document disagree about its contents and neither says so.\n")

simp <- fromJSON(path)
doc  <- fromJSON(path, simplifyVector = FALSE)

# ── Q1. What is in here? AND A CORRECTION TO A NUMBER IN VERDICT.md. ─────────
cat("\n1. what is in here — str() is the only describer jsonlite has:\n")
n_simp <- length(capture.output(str(simp)))
n_list <- length(capture.output(str(doc)))
cat(sprintf("   str(fromJSON(path))                    %s lines\n",
            format(n_simp, big.mark = ",")))
cat(sprintf("   str(fromJSON(path, simplify=FALSE))    %s lines\n",
            format(n_list, big.mark = ",")))
cat(sprintf("   str(simplified, max.level=2)           %s lines\n",
            format(length(capture.output(str(simp, max.level = 2))), big.mark = ",")))
cat("   VERDICT.md and README.md both say `str() runs to 7,099 lines` on this\n")
cat("   file. THAT IS THE UNSIMPLIFIED NUMBER. The default `fromJSON()` — what\n")
cat("   a person actually types — gives the smaller figure above. Both are\n")
cat("   catastrophic and the claim survives, but the number as published names\n")
cat("   a non-default parse and does not say so.\n")

# ── Q2 / Q7. ─────────────────────────────────────────────────────────────────
depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion\n", depth(doc)))
cat(sprintf("7. %d versions — after knowing to look at `versions`\n",
            length(doc$versions)))

# ── Q3 / Q6. THE KEYS-AS-DATA FILE, AND SIMPLIFICATION IS INERT. ─────────────
cat("\n3/6. what is one record, and are any keys actually data:\n")
cat(sprintf("   fromJSON() returned a %s, not a data frame\n", class(simp)[1]))
for (site in c("versions", "time", "users")) {
  v <- simp[[site]]
  if (is.null(v)) next
  cat(sprintf("   $%-9s is a %-10s of %4d — %s\n", site, class(v)[1], length(v),
              if (is.data.frame(v)) "a table" else "NOT a table"))
}
cat("   SIMPLIFICATION DID NOTHING, and this is the third distinct outcome for\n")
cat("   one rule. It cannot build a frame from `versions` because `versions` is\n")
cat("   an OBJECT keyed by version string, and jsonlite has no notion that a key\n")
cat("   might be a value. 288 siblings of near-identical shape sit there as a\n")
cat("   named list.\n")
ks <- lapply(doc$versions, names)
u  <- unique(unlist(ks))
cat(sprintf("   those 288 objects share %d distinct keys and %d key-sets\n",
            length(u), length(unique(vapply(ks, function(x) paste(sort(x), collapse = ","), "")))))
cat("   THE ONE-LINE FIX A PERSON MUST KNOW TO WRITE: bind them by hand.\n")
tbl0 <- do.call(rbind, lapply(names(doc$versions), function(k)
  data.frame(version = k, n_fields = length(doc$versions[[k]]))))
cat(sprintf("   do.call(rbind, ...) over names() -> %d x %d, and `version` is\n",
            nrow(tbl0), ncol(tbl0)))
cat("   only a column because I put it there. jsonlite would have lost it.\n")
cat("   SCORED NO on question 6: the tool has no opinion, and the harm is that\n")
cat("   the key silently stops being data the moment you index into the list.\n")

# ── Q4. Always vs sometimes. ─────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
n <- length(ks)
freq <- vapply(u, function(k) sum(vapply(ks, function(x) k %in% x, TRUE)), 0L)
cat(sprintf("   %d of %d keys are absent from at least one version\n",
            sum(freq < n), length(u)))
cat(sprintf("   present in ALL %d: %s\n", n,
            paste(names(freq)[freq == n], collapse = ", ")))
cat("   PARTLY: correct, and computed by hand. The simplified object cannot be\n")
cat("   asked this at all, because it never became a table.\n")

# ── Q8. Three named fields. ──────────────────────────────────────────────────
cat("\n8. three named fields, one row per version:\n")
tbl <- do.call(rbind, lapply(names(doc$versions), function(k) {
  v <- doc$versions[[k]]
  data.frame(version = k,
             author  = if (is.null(v$author$name)) NA_character_ else v$author$name,
             tarball = v$dist$tarball)
}))
cat(sprintf("   -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat("   Four things had to be known first — that `versions` is the thing, that\n")
cat("   one row is a version, that the author is at `author$name`, and that the\n")
cat("   tarball is at `dist$tarball`. Identical to the purrr attempt beside\n")
cat("   this one, and jsonlite adds nothing: without purrr it is a base-R\n")
cat("   `do.call(rbind, lapply(...))` and slightly worse to read.\n")

cat("
CONCLUSION — the first jsonlite attempt in the corpus completes a three-way
result about ONE rule.

  Simplification is jsonlite's whole contribution, and across three documents it
  produces three different outcomes:

    03-natural-earth   builds the frame, PRESERVES the 3-deep/4-deep split  SAFE
    05-fhir-bundle     builds the frame, folds 20 kinds into 87% holes      WRONG
    01-npm-registry    builds NOTHING, because the keys are data            INERT

  **The rule is `build the widest rectangle that fits`, and it has no idea which
  of those three it is doing.** Here it is inert: `versions`, `time` and `users`
  are objects keyed by data, so 288 near-identical siblings arrive as a named
  list and every question after that is hand-written base R. `README.md` puts
  this file in the corpus precisely because of those 6 keyed sites, and the most
  widely used JSON reader in R walks straight past them.

  ONE NUMBER IN THIS REPOSITORY NEEDS A FOOTNOTE. `VERDICT.md` and `README.md`
  both cite `str()` at **7,099 lines** on this file. That is `str()` on the
  UNSIMPLIFIED parse. The default `fromJSON()` gives fewer, printed above. The
  argument is unaffected — both are far past readable — but the published figure
  describes a call nobody makes by default, and it does not say so.

  QUESTION 0 IS WHERE JSONLITE IS QUIETLY DIFFERENT FROM PYTHON: duplicate keys
  resolve to the FIRST, where every Python parser in this corpus takes the last.
")
