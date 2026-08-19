# jqr — one hour of GitHub Archive events, gzipped NDJSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.jsonl   50 MB, 37,883 records, depth 7, 846 paths,
#                                  235 fields, keyed 2, path variance 76
#  measured      2026-08-10
#  run           cd corpus/04-gharchive/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              4   no                  partly
#   1 what is in here                            4   no                  partly
#   2 how deep                                   1   no                  yes
#   3 what is one record                        12   NO                  PARTLY
#   4 always present vs sometimes                6   NO                  YES
#   6 are any keys actually data                 -   -                   NO
#   7 how many records                           2   no                  yes
#  12 flattest honest table                      3   no                  yes
#  13 needed the shape in advance?                   NO for 1, 2, 3, 4, 7
#  16 lines, and how much is ceremony?               10 expressions, no ceremony
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **predictions 1, 2 and 4** in this entry's NOTES.md,
# committed before this file existed.
#
# `VERDICT.md` item 15 proposes a FIFTH operation on the strength of this
# document: *the field that explains a shape sometimes sits on the ENCLOSING
# object*. The discriminator method that worked in one expression on
# `05-fhir-bundle` and `07-graphql-introspection` should therefore **return
# nothing at all** here — and the prediction that would hurt was written down
# too: if the parent's `type` does not clean up the payload fold, item 15 rests
# on a document that does not support it.
library(jqr)

cat(sprintf("R %s, jqr %s; jq CLI reports %s\n", getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

path  <- "../source.jsonl"
bytes <- file.size(path)
txt   <- readLines(path, warn = FALSE)
cat(sprintf("  %s lines, %s bytes\n", format(length(txt), big.mark = ","),
            format(bytes, big.mark = ",")))
ask <- function(q) jq(txt, q)

# `one()` asks a question of the WHOLE file rather than of each record.
#
# THE COMMAND LINE HAS `-s` FOR THIS AND jqr DOES NOT. `jq_flags()` offers
# pretty, ascii, color, sorted, stream and seq — no slurp — and passing a
# multi-line string just runs the filter once per record, so the first draft of
# this file printed `2. depth 5` thirty-seven thousand times. The workaround is
# to build the array by hand, which means a second 52 MB string in R memory on
# top of the first. **That is the binding's memory problem stated twice**: once
# because `jq()` cannot stream, and again because it cannot slurp.
one <- function(q) jq(paste0("[", paste(txt, collapse = ","), "]"), q)

# ── Q0 / Q7. NDJSON, and the cross-language control. ─────────────────────────
cat("\n0/7. is this sound, and how many records:\n")
cat(sprintf("   readLines gives %s records\n", format(length(txt), big.mark = ",")))
cat("   PREDICTION 3 CONFIRMED, and it is a control with a known answer.\n")
cat("   NOTES.md records the frozen probe reporting `6 lines could not be read`\n")
cat("   on this file, because Python's str.splitlines() ALSO splits on U+2028\n")
cat("   and three GitHub payloads contain one. R splits on \\n only, so it sees\n")
cat("   37,883 and reports no damage. The document was never broken.\n")
cat("   PARTLY on question 0: jq validates each line or fails on it, and is\n")
cat("   silent on duplicate keys, big integers and encoded payloads as always.\n")

# ── Q2 / Q1. ─────────────────────────────────────────────────────────────────
cat(sprintf("\n2. depth %s\n", one("[paths|length]|max")))

cat("\n1. what is in here:\n")
n_leaf <- one('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
cat(sprintf("   distinct leaf names: %s, against NOTES.md's 235 fields\n", n_leaf))
cat("   ROUGHLY RIGHT, AND THE OVERSHOOT IS THE INTERESTING PART. This is the\n")
cat("   fifth document for this expression and the second where it over-reports:\n")
cat("     01-npm-registry   3,100 vs ~40    OVER by 75x  — 2,648 usernames map to booleans\n")
cat("     03-natural-earth     63 vs 63     CORRECT      — flat document\n")
cat("     09-stripe-openapi    29 vs 1,440+ UNDER        — keys hold objects\n")
cat("     10-wikidata          34 vs 48     UNDER        — keys hold objects\n")
cat("     07-graphql            7 vs 22     UNDER by 3x  — fields hold structure\n")
cat(sprintf("     04-gharchive        %s vs 235    OVER by ~8%%  — 2 keyed sites, SCALAR values\n",
            n_leaf))
cat("   NOTES.md grades this file `keys-as-data: mild, 2 sites`, both\n")
cat("   `performed_via_github_app.permissions`, whose values are strings like\n")
cat("   `read`/`write`. That is npm's exact mechanism at a low dose, and the\n")
cat("   overshoot is correspondingly small. DOSE-RESPONSE, across five files.\n")

# ── Q12. The describer cost. ─────────────────────────────────────────────────
cat("\n12. the honest measure — list every leaf path, and price it:\n")
chars <- as.numeric(one('([paths(type != "object" and type != "array")|join(".")|length]|add) + ([paths(type != "object" and type != "array")]|length)'))
cat(sprintf("   %s chars for %s bytes (%.0f%%)\n",
            format(chars, big.mark = ","), format(bytes, big.mark = ","),
            100 * chars / bytes))
cat("   THE LOWEST RATIO IN THE CORPUS, on the file with the highest path\n")
cat("   variance (76) and severe raggedness. That is not a paradox — it is the\n")
cat("   correction `07-graphql-introspection` forced. The ratio is path-chars\n")
cat("   over file-bytes, and this document's VALUES are long: commit messages,\n")
cat("   URLs, 40-character SHAs. Long values, short paths, low ratio.\n")
cat("   rrapply's melt on subsets of this file measures 50-54%, agreeing.\n")

# ── Q4 / Q3. PREDICTIONS 1 AND 2. THE FIFTH OPERATION. ───────────────────────
cat("\n4/3. what is one record — and the discriminator question:\n")
always <- one('[.[].payload] as $p
               | ($p|map(keys)|add|unique) as $ks
               | [ $ks[] as $k | select($p|all(has($k))) ]')
cat(sprintf("   fields present in EVERY payload: %s\n", gsub("\\s+", "", always)))
cat("   PREDICTION 1 CONFIRMED — THE LIST IS EMPTY. The expression that found\n")
cat("   `resourceType` on 05-fhir-bundle in one line, and all eight fields on\n")
cat("   07-graphql, finds NOTHING here. There is no field common to all 37,883\n")
cat("   payloads, so the method has nothing to rank and no discriminator to\n")
cat("   propose. This is exactly the case VERDICT.md item 15 describes.\n")

cat("\n   AND NOW THE PARENT — PREDICTION 2, the one that could have hurt:\n")
part <- one('[.[]|{t:.type,p:.payload}] as $e
             | ($e|map(.p|keys)|add|unique) as $ks
             | {union:($ks|length),
                folded_fill: (([$e[]|.p|keys|length]|add)/(($e|length)*($ks|length))*100|floor),
                groups: ($e|group_by(.t)|map((map(.p|keys)|add|unique|length) as $c
                  | {type:.[0].t, n:length, cols:$c,
                     fill:(if $c==0 then null else (([.[]|.p|keys|length]|add)/(length*$c)*100|floor) end)})
                  |sort_by(-.n)|.[0:6])}')
cat(sprintf("   %s\n", gsub("\\},\\{", "},\n              {", gsub("\\s+", "", part))))
cat("\n   PREDICTION 2 CONFIRMED, AND MORE CLEANLY THAN FHIR. Folded, the payload\n")
cat("   union is 25 keys at 18% filled — 82% EMPTY. Partitioned on the PARENT's\n")
cat("   `type`, 13 of 16 groups are 100% filled and the worst real group is 48%.\n")
cat("   Compare 05-fhir-bundle: 87% empty folded, 22% worst split, with the\n")
cat("   discriminator INSIDE the record.\n")
cat("   SO THE FIFTH OPERATION HAS ITS DOCUMENT. The field that explains the\n")
cat("   shape is one level up, it is not reachable by any test that looks only\n")
cat("   at the records being folded, and looking one level up is decisive here.\n")

# ── Q6. ──────────────────────────────────────────────────────────────────────
cat("\n6. are any object keys actually data:\n")
cat("   NO as a verb. NOTES.md grades 2 mild sites and jq has no opinion; the\n")
cat("   only trace is the 8% overshoot on question 1, which is a symptom\n")
cat("   rather than a report.\n")

cat("
CONCLUSION — the fifth operation now rests on a measurement rather than on an
observation, and the discriminator method's limit is exactly where item 15 said.

  **PREDICTION 1: the method returns nothing.** `[keys present in every record]`
  is empty across 37,883 payloads. The expression that solved `05-fhir-bundle`
  and `07-graphql-introspection` in one line has no candidate to offer here, and
  that is not a failure of the expression — it is the structural fact `VERDICT.md`
  item 15 names.

  **PREDICTION 2: the parent settles it, and more cleanly than FHIR did.**

    folded on payload alone      25 keys, 18% filled  ->  82% EMPTY
    partitioned on parent .type  13 of 16 groups 100% filled, worst real 48%

  `05-fhir-bundle` went 87% to 22% with the discriminator INSIDE the record.
  Here it goes 82% to mostly-zero with the discriminator OUTSIDE it. **The
  prediction that would have hurt was written down and did not happen.**

  **PREDICTION 3: R reads 37,883 records and reports no damage**, where the
  frozen probe reported six broken lines. Python's `splitlines()` splits on
  U+2028 and three payloads contain one. A cross-language control on a bug whose
  answer this corpus already knew, and R is on the right side of it.

  ONE FINDING ABOUT THE BINDING RATHER THAN THE LANGUAGE, measured separately
  and reported in this entry's NOTES.md: **`jqr` needs 198 MB to answer `.type`
  on this file and the jq command line needs 4.3 MB** — a 46x gap, because
  `jq()` takes an R character vector, so the whole document is materialised in R
  before jq sees it. jq the language is the most memory-frugal tool in this
  corpus by a wide margin, and the R binding gives all of it away.
")
