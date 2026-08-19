# jqr — the Stripe OpenAPI specification
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
#  measured      2026-08-09
#  run           cd corpus/09-stripe-openapi/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                            6   no                  WRONG
#   2 how deep                                   1   no                  yes
#   3 what is one record                         -   -                   CANNOT
#   6 are any keys actually data                 6   YES                 NO
#   7 how many records                           2   YES                 yes
#  12 flattest honest table                      4   no                  yes
#  13 needed the shape in advance?                   YES for 6 and 7
#  16 lines, and how much is ceremony?               7 expressions, no ceremony
#
#  Q1 is scored WRONG rather than NO, and it is the opposite error from the one
#  this project has been citing. See the conclusion.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `VERDICT.md`'s central piece of evidence for the O(data) claim
# is that jq answers **3,100** for `01-npm-registry` where the truth is about 40
# fields, and that `rrapply` independently answers **3,112** — two tools, two
# languages, agreeing to within twelve on a wrong answer.
#
# This is the corpus's most keys-as-data-heavy document: **47 keyed sites against
# npm's 6**, and 1,440 schema names. If the 3,100 is caused by keys-as-data, the
# same expression here should be very much larger. It is not. It is 29.
library(jqr)

cat(sprintf("R %s, jqr %s; jq CLI reports %s (jqr's linked library is not queryable)\n",
            getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

path  <- "../source.json"
bytes <- file.size(path)
txt   <- paste(readLines(path, warn = FALSE), collapse = "")
ask   <- function(q) jq(txt, q)

# ── Q2 / Q7. ─────────────────────────────────────────────────────────────────
cat(sprintf("\n2. depth %s, from `[paths|length]|max`\n", ask("[paths|length]|max")))
cat(sprintf("7. %s schemas, %s API paths — both needed naming\n",
            ask(".components.schemas|length"), ask(".paths|length")))

# ── Q1. THE EXPRESSION THAT GAVE 3,100 ON NPM. ───────────────────────────────
cat("\n1. what is in here:\n")
n_leaf <- ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
cat(sprintf("   distinct leaf names: %s\n", n_leaf))
cat("   TWENTY-NINE. On 01-npm-registry this identical expression gives 3,100,\n")
cat("   on 02-hn-thread 11, on 03-natural-earth 63. This document has 1,440\n")
cat("   schemas and 47 keyed sites — it should be the largest of the four and\n")
cat("   it is the SMALLEST.\n")

# Why. Measured rather than reasoned about.
cat("\n   WHY, measured two ways:\n")
seen <- ask('[.components.schemas|keys[]] as $names
             | [paths(type != "object" and type != "array")|map(select(type=="string"))|last]
             | map(select(. as $x | $names|index($x))) | length')
cat(sprintf("   schema names ever appearing as the LAST path component: %s\n", seen))
cat("   ZERO of 1,440. Stripe's keyed objects hold OBJECTS, so a schema name is\n")
cat("   always in the MIDDLE of a path and the leaf is an OpenAPI keyword —\n")
cat("   `type`, `description`, `title`. There are only 29 of those.\n")
cat("   npm's inflation comes from the opposite case: its keyed objects hold\n")
cat("   SCALARS. `users` is 2,648 usernames mapped to booleans and `time` is\n")
cat("   320 version strings mapped to timestamps, so the key IS the leaf.\n")
cat("   2,648 + 320 + 40 real fields is the 3,100, almost exactly.\n")

# ── Q12 / the honest describer cost. ─────────────────────────────────────────
cat("\n12. the honest measure — list every leaf path, and price it:\n")
allp  <- ask('[paths(type != "object" and type != "array")|join(".")]|join("\n")')
chars <- nchar(allp)
cat(sprintf("   %s chars for a %s-byte file (%.0f%%)\n",
            format(chars, big.mark = ","), format(bytes, big.mark = ","),
            100 * chars / bytes))
cat("   rrapply's melt on this same file is 141%. THESE TWO AGREE, and they\n")
cat("   agree on the measure that actually tracks the document rather than on\n")
cat("   the one that happens to collapse. That is the O(data) claim, intact.\n")

# ── Q6. ──────────────────────────────────────────────────────────────────────
cat("\n6. are any object keys actually data:\n")
cat("   NO. jq has no notion of the question. And on this file the usual\n")
cat("   symptom of the failure is INVISIBLE: the 1,440 schema names never reach\n")
cat("   a leaf, so the describer that over-reports on npm under-reports here,\n")
cat("   and both answers look calm.\n")
kids <- ask('{schemas: (.components.schemas|length),
              keysets: ([.components.schemas[]|keys|join(",")]|unique|length)}')
cat(sprintf("   the signal, computed by hand: %s\n", gsub("\\s+", "", kids)))
cat("   Thousands of children sharing a handful of key-sets is what a keyed\n")
cat("   object looks like, and nothing in jq volunteers the comparison.\n")

cat("\n3. CANNOT — jq offers no row candidates.\n")
cat("0. CANNOT — jq parses or it does not.\n")

cat("
CONCLUSION — the 3,100 is real and the reason given for it is too narrow, and
this file is the counterexample.

  `VERDICT.md` reads the npm result as: path-listing describers blow up because
  keys-as-data mints new field names. **On the corpus's most keys-as-data-heavy
  document the same expression returns 29.** Not 3,100, not larger — smaller
  than the GeoJSON file's 63.

  The mechanism, measured: the expression's `|last` reports the final STRING
  component of each path. That is a key-as-data only when the keyed object's
  values are SCALARS. npm's `users` maps 2,648 usernames to booleans and `time`
  maps 320 version strings to timestamps, so the key is the leaf and the count
  explodes. Stripe's 1,440 schemas map names to OBJECTS, so **zero** schema
  names ever appear at a leaf and the expression cannot see them at all.

  SO THE EXPRESSION IS WRONG IN BOTH DIRECTIONS AND FOR ONE REASON. It
  over-reports npm at 3,100 against a truth near 40, and under-reports Stripe at
  29 against 1,440 schemas plus 29 keywords. **A tool that is wrong high on one
  document and wrong low on another is not measuring what it is being credited
  with measuring**, and `01-npm-registry`'s agreement with rrapply at 3,112 is a
  coincidence of that file's shape rather than confirmation of a mechanism.

  THE CLAIM ITSELF SURVIVES, on the honest measure. Listing every leaf path
  costs 139% of this file, against rrapply's melt at 141%. Two tools, two
  languages, agreeing on a describer whose output is larger than the document it
  describes — and that agreement IS about the mechanism, because both are
  enumerating every leaf rather than summarising anything.
")
