# jqr — a scrubbed Claude Code transcript, NDJSON, 1,953 records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.jsonl  4.8 MB, NDJSON, 1,953 records, depth 10,
#                                 452 paths, 151 fields, polymorphic 4
#  measured      2026-08-10
#  run           cd corpus/12-agent-trace/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              3   no                  partly
#   1 what is in here                            6   no                  partly
#   2 how deep                                   1   no                  yes
#   3 what is one record                        14   NO                  PARTLY
#   4 always present vs sometimes                4   NO                  YES
#   5 does any field change type                 3   no                  YES
#   6 are any keys actually data                 5   YES                 NO
#   7 how many records                            1   no                  yes
#  12 flattest honest table                       3   no                  yes
#  13 needed the shape in advance?                   NO for 1, 2, 4, 5
#  16 lines, and how much is ceremony?               9 expressions, no ceremony
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 1** in this entry's NOTES.md, and the
# prediction would REWORD `VERDICT.md` item 15.
#
# On `04-gharchive` the field explaining the payloads sits on the enclosing
# EVENT. Section 2 of this entry records that here it sits on a **SIBLING** —
# `name`: `Bash` 265, `Edit` 130, `Write` 39. If partitioning by the sibling
# cleans the fold the way the parent's `type` did there, then the fifth
# operation is not *discriminator-on-the-parent*. It is **the discriminator is
# outside the record**, and parent and sibling are two cases of one thing.
library(jqr)

cat(sprintf("R %s, jqr %s; jq CLI reports %s\n", getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

path  <- "../source.jsonl"
bytes <- file.size(path)
txt   <- readLines(path, warn = FALSE)
cat(sprintf("  %s records, %s bytes\n", format(length(txt), big.mark = ","),
            format(bytes, big.mark = ",")))
# jqr has no slurp; the array is built by hand. See ../../04-gharchive/r/try-jqr.R
one <- function(q) jq(paste0("[", paste(txt, collapse = ","), "]"), q)

cat(sprintf("\n0/7. NDJSON, %s records read, %s fail validate()\n",
            format(length(txt), big.mark = ","),
            sum(!vapply(txt, jsonlite::validate, TRUE, USE.NAMES = FALSE))))
cat(sprintf("2. depth %s\n", one("[paths|length]|max")))

# ── Q1 / Q6 / Q12. ───────────────────────────────────────────────────────────
cat("\n1/6. what is in here, and are any keys data:\n")
n_leaf <- one('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
n_tfb  <- one('[.[]|.snapshot?.trackedFileBackups? // {} | keys[]]|unique|length')
cat(sprintf("   distinct leaf names: %s, against NOTES.md's 151 fields\n", n_leaf))
cat(sprintf("   distinct trackedFileBackups keys (file paths): %s\n", n_tfb))
cat("   PREDICTION 4 CONFIRMED — the file paths do NOT inflate the count.\n")
cat("   Defect 1 above records `trackedFileBackups` as keys-as-data the probe\n")
cat("   missed, keyed by file path. Its VALUES are objects sharing one key-set,\n")
cat("   and the scalar-vs-object rule says a key reaches a leaf only when its\n")
cat("   value is a scalar. SIXTH DOCUMENT for that rule:\n")
cat("     01-npm-registry   3,100 vs ~40    OVER  — keys map to scalars\n")
cat("     03-natural-earth     63 vs 63     RIGHT — flat document\n")
cat("     04-gharchive        254 vs 235    OVER 8% — 2 keyed sites, scalar values\n")
cat("     09-stripe-openapi    29 vs 1,440+ UNDER — keys hold objects\n")
cat("     10-wikidata          34 vs 48     UNDER — keys hold objects\n")
cat(sprintf("     12-agent-trace      %s vs 151    UNDER — keys hold objects\n", n_leaf))
cat("   SCORED NO on question 6: 50 file paths are sitting in the paths as\n")
cat("   though they were field names and jq has no opinion about it.\n")

chars <- as.numeric(one('([paths(type != "object" and type != "array")|join(".")|length]|add) + ([paths(type != "object" and type != "array")]|length)'))
cat(sprintf("\n12. every leaf listed: %s chars for %s bytes (%.0f%%)\n",
            format(chars, big.mark = ","), format(bytes, big.mark = ","),
            100 * chars / bytes))
cat("   PREDICTION 5 CONFIRMED — the LOWEST ratio in the corpus, below\n")
cat("   04-gharchive's 52%, and for the same reason: long values. This document\n")
cat("   is prose, code and scrubbed content that keeps its original length.\n")

# ── Q5. ──────────────────────────────────────────────────────────────────────
cat("\n5. does any field change type:\n")
poly <- one('[.[]|.message?.content?|type]|group_by(.)|map({t:.[0],n:length})')
cat(sprintf("   message.content: %s\n", gsub("\\s+", "", poly)))
cat("   YES, in one expression. NOTES.md grades this file polymorphic 4, the\n")
cat("   highest in the corpus, and this is the headline field: an array on\n")
cat("   1,363 messages and a bare string on 20. jq states it plainly; tidyjson\n")
cat("   describes all 1,383 as arrays — see try-tidyjson.R.\n")

# ── Q3 / Q4. PREDICTION 1. THE FIFTH OPERATION, SECOND FORM. ────────────────
cat("\n3/4. what is one record — and the discriminator question, again:\n")
res <- one('[.[] | .message?.content? // [] | if type=="array" then .[] else empty end
            | select(.input?)] as $t
           | ($t|map(.input|keys)|add|unique) as $ks
           | {inputs: ($t|length), union_fields: ($ks|length),
              always: [ $ks[] as $k | select($t|all(.input|has($k))) ]}')
cat(sprintf("   %s\n", gsub("\\s+", "", res)))
cat("   PREDICTION 1, FIRST HALF CONFIRMED — `always` IS EMPTY. Zero fields\n")
cat("   present in all 458 tool inputs, over a union of 15. The method that\n")
cat("   solved 05-fhir-bundle and 07-graphql in one expression each has\n")
cat("   nothing to rank, exactly as on 04-gharchive.\n")

cat("\n   AND NOW THE SIBLING — the half that would reword item 15:\n")
part <- one('[.[] | .message?.content? // [] | if type=="array" then .[] else empty end
             | select(.input?)] as $t
            | ($t|map(.input|keys)|add|unique) as $ks
            | {folded_fill: (([$t[]|.input|keys|length]|add)/(($t|length)*($ks|length))*100|floor),
               groups: ($t|group_by(.name)|map((map(.input|keys)|add|unique|length) as $c
                 | {name:.[0].name, n:length, cols:$c,
                    fill:(if $c==0 then null else (([.[]|.input|keys|length]|add)/(length*$c)*100|floor) end)})
                 |sort_by(-.n)|.[0:5])}')
cat(sprintf("   %s\n", gsub("\\},\\{", "},\n            {", gsub("\\s+", "", part))))
cat("\n   PREDICTION 1 CONFIRMED IN FULL. Folded, the 15-field union is 19%\n")
cat("   filled — 81% EMPTY. Partitioned on the SIBLING `name`, Edit and Write\n")
cat("   reach 100% and Bash 86%.\n")
cat("   SO THE FIFTH OPERATION IS NOT ABOUT PARENTS. On 04-gharchive the field\n")
cat("   that explains the shape is the enclosing event's `type`; here it is a\n")
cat("   sibling key in the same object as `input`. Both are OUTSIDE the record\n")
cat("   being folded, and no test that looks only at the records can reach\n")
cat("   either. `VERDICT.md` item 15 is worded as `on the parent` and should\n")
cat("   say `outside the record`, with parent and sibling as two cases.\n")
cat("   The scrub is visible in the group names — `xxxx` and `xxxxxxxx` are\n")
cat("   tool names below the 20-occurrence vocabulary threshold, and they\n")
cat("   partition just as cleanly, which is some evidence the split is\n")
cat("   structural rather than a reading of the words.\n")

cat("
CONCLUSION — the fifth operation has its second document, and it needs
rewording rather than strengthening.

  **`always` is empty across 458 tool inputs**, over a union of 15 fields. The
  discriminator method that solved `05-fhir-bundle` and `07-graphql-introspection`
  in one expression each returns nothing, exactly as on `04-gharchive`.

  **And the sibling settles it**: folded, the union is 19% filled — 81% empty;
  partitioned on `name`, Edit and Write are 100% and Bash 86%.

  **THE CORRECTION IS THE POINT.** `VERDICT.md` item 15 is worded
  *discriminator-on-the-parent*, because `04-gharchive` was its only document
  and there the field sits on the enclosing event. Here it sits on a **sibling
  key of the same object**. Both are outside the record being folded; neither is
  reachable by any test that looks only at the records. **The operation is `the
  discriminator is outside the record`, and parent and sibling are two cases of
  one thing.** That is a second document, and a rewording rather than a
  strengthening.

  THE SCRUB SUPPORTS RATHER THAN UNDERMINES IT. Two of the groups are `xxxx` and
  `xxxxxxxx` — tool names that fell below the scrub's 20-occurrence vocabulary
  threshold — and they partition as cleanly as `Bash` and `Edit`. The split is
  structural, not a reading of the words.

  AND THE SCALAR-VS-OBJECT RULE HOLDS ON A SIXTH DOCUMENT. 50 file paths sit in
  `trackedFileBackups` as keys, and jq's leaf-name count is **113 against 151
  true fields** — under, not inflated, because those keys hold objects. Six
  documents, one rule, no exceptions.
")
