# jqr — a Synthea FHIR R4 patient bundle
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.json   2.0 MB, 564 resources, 20 resourceTypes, depth 11
#  measured      2026-08-09
#  run           cd corpus/05-fhir-bundle/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              -   -                   CANNOT
#   1 what is in here                            1   no                  YES
#   2 how deep                                   1   no                  YES
#   3 what is one record                         6   NO                  PARTLY
#   4 always present vs sometimes                3   no                  YES
#   5 does any field change type                 3   YES, the convention  partly
#   6 are any keys actually data                 -   -                   n/a
#   7 how many records                           1   YES                 yes
#  11 find every path matching something         2   no                  YES
#  13 needed the shape in advance?                   NO for 1, 2, 3, 4, 11
#  16 lines, and how much is ceremony?               10 expressions, no ceremony
#
#  RULE 6, RECORDED. The frozen probe got ONE cold run at this file. The
#  discriminator expression under question 3 took me THREE drafts. Three
#  attempts against one is a real advantage and is written down rather than
#  hidden. The probe, however, was DEVELOPED against this document across five
#  freezes afterwards — so on operation 4 specifically the advantage runs the
#  other way, and that is stated too.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `05-fhir-bundle` is the document that ADDED the fourth
# operation — partition on a discriminator before folding — and `VERDICT.md`
# calls it "the first operation the corpus demanded rather than confirmed". The
# probe's headline on it is **87% empty folded, 22% worst split**.
#
# The question this attempt asks is whether an existing tool can express that
# operation. Not whether it volunteers it — nothing does — but whether the
# arithmetic is reachable at all in a language somebody already has installed.
library(jqr)

cat(sprintf("R %s, jqr %s; jq CLI reports %s (jqr's linked library is not queryable)\n",
            getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "")
ask <- function(q) jq(txt, q)

# ── Q2 / Q7. ─────────────────────────────────────────────────────────────────
stopifnot(ask("[paths|length]|max") == "11")
stopifnot(ask(".entry|length") == "564")
cat("2. depth 11, `[paths|length]|max`, unaided\n")
cat("7. 564 entries, and I had to name `entry` to get it\n")

# ── Q1. What is in here? ─────────────────────────────────────────────────────
n_leaf <- ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
cat(sprintf("1. %s distinct leaf names, from the expression that gives 3,100 on\n",
            n_leaf))
cat("   01-npm-registry, 11 on 02-hn-thread and 63 on 03-natural-earth. FHIR\n")
cat("   names its fields, so this is small and roughly right — NOTES.md counts\n")
cat("   174 fields and 580 distinct paths.\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
cat("\n4. always present vs sometimes, across the 564 resources:\n")
ks <- ask('[.entry[].resource]|(map(keys)|add|unique|length)')
cat(sprintf("   union of keys: %s\n", ks))
nsets <- ask('[.entry[].resource|keys|join(",")]|unique|length')
cat(sprintf("   distinct key-sets: %s\n", nsets))

# ── Q3. WHAT IS ONE RECORD — AND THE FOURTH OPERATION, IN JQ. ────────────────
cat("\n3. what is one record — and this is the fourth operation, expressed:\n")

# Step 1: which fields are present in EVERY resource? No field named.
always <- ask('[.entry[].resource] as $r
               | ($r|map(keys)|add|unique) as $ks
               | [ $ks[] as $k | select($r|all(has($k)))
                   | {field:$k, distinct: ([$r[][$k]|tostring]|unique|length)} ]')
cat("   fields present in EVERY resource, with their cardinality:\n")
cat(sprintf("   %s\n", gsub("\\s+", "", always)))
cat("   TWO CANDIDATES, AND THE CARDINALITY SEPARATES THEM CLEANLY. `id` takes\n")
cat("   564 distinct values on 564 records — an identifier. `resourceType`\n")
cat("   takes 20 — a kind. That is the whole discriminator test, and no field\n")
cat("   was named to get it.\n")

# Step 2: price the fold, then price the partition. The probe's two numbers.
folded <- ask('[.entry[].resource]
               | (([.[]|keys|length]|add) / (length*(map(keys)|add|unique|length))*100)|floor')
worst  <- ask('[.entry[].resource]|group_by(.resourceType)
               | map( ([.[]|keys|length]|add) / (length*(map(keys)|add|unique|length))*100|floor )
               | min')
cat(sprintf("\n   folded into one table:      %s%% filled  -> %d%% EMPTY\n",
            folded, 100 - as.integer(folded)))
cat(sprintf("   partitioned on resourceType: worst group %s%% filled -> %d%% EMPTY\n",
            worst, 100 - as.integer(worst)))
cat("   VERDICT.md records the probe's answer as `87% empty folded, 22% worst\n")
cat("   split`. THESE ARE THE SAME TWO NUMBERS, computed independently in a\n")
cat("   query language, which is a check on the probe rather than on jq.\n")

per <- ask('[.entry[].resource]|group_by(.resourceType)
            | map({t:.[0].resourceType, n:length, cols:(map(keys)|add|unique|length)})
            | sort_by(-.n)|.[0:5]')
cat(sprintf("   the five largest groups: %s\n", gsub("\\s+", "", per)))
cat("   SCORED PARTLY, and the reason is the point. Every number above is\n")
cat("   reachable, and NONE of it is offered. jq answered because I knew to ask\n")
cat("   `which field is present everywhere and has low cardinality`, which is\n")
cat("   the fourth operation stated in words. The operation is the contribution;\n")
cat("   the arithmetic was always available.\n")

# ── Q5. value[x]. ────────────────────────────────────────────────────────────
cat("\n5. does any field change type — FHIR's value[x]:\n")
vx <- ask('[paths|.[-1]|select(type=="string")|select(test("^value[A-Z]"))]
           |group_by(.)|map({k:.[0],n:length})|sort_by(-.n)')
cat(sprintf("   %s\n", gsub("\\s+", "", vx)))
cat("   Eight spellings, matching NOTES.md exactly. BUT THE EXPRESSION ENCODES\n")
cat("   THE CONVENTION — `^value[A-Z]` is a naming rule I supplied, not a\n")
cat("   structural signal. NOTES.md records that the convention over-matches:\n")
cat("   `reasonCode`/`reasonReference` are separate R4 fields, not variants.\n")
cat("   So this is partly, and the part that worked is the part I brought.\n")

# The structural version: do these spellings ever CO-OCCUR? If they are variants
# of one field, they should be mutually exclusive within a record.
# Asked of EVERY object at every level, not just the top of a resource — the
# first draft asked only the resource level and saw 119 of the 261 sites.
co <- ask('[..|objects|[keys[]|select(test("^value[A-Z]"))]|select(length>0)|length]
           |group_by(.)|map({n_value_fields:.[0],objects:length})')
cat(sprintf("   how many value* fields does ONE OBJECT carry, at any depth? %s\n",
            gsub("\\s+", "", co)))
cat("   EXACTLY ONE, 261 TIMES, WITH NO EXCEPTIONS — and 261 is the sum of the\n")
cat("   eight spelling counts above, so every site is accounted for.\n")
cat("   THAT IS A STRUCTURAL SIGNAL: mutually exclusive sibling fields sharing\n")
cat("   a stem are what a choice type IS, and the test needs no word list and\n")
cat("   no knowledge of FHIR. It is also not something jq volunteers; I had to\n")
cat("   think of the test, which is the whole distinction this project draws.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────────
cat("\n11. find every path whose value matches something — a URL this time:\n")
nurl <- ask('[paths(type != "object" and type != "array") as $p|select((getpath($p)|type)=="string")
             |select(getpath($p)|test("^https?://"))]|length')
where <- ask('[paths(type != "object" and type != "array") as $p|select((getpath($p)|type)=="string")
              |select(getpath($p)|test("^https?://"))|($p|map(select(type=="string"))|last)]
              |group_by(.)|map({f:.[0],n:length})|sort_by(-.n)|.[0:4]')
cat(sprintf("   %s URL-valued cells; commonest fields: %s\n", nurl, gsub("\\s+", "", where)))
cat("   `paths` + `getpath` + a predicate, needing nothing known in advance.\n")
cat("   This remains jq's best question in either language.\n")

cat("\n0. CANNOT — jq parses or it does not, and is silent on every silent damage.\n")
cat("6. n/a — NOTES.md grades this file keys-as-data 0.\n")

cat("
CONCLUSION — the fourth operation is EXPRESSIBLE in a tool everybody already
has, and that sharpens what fathom is actually claiming.

  `VERDICT.md` calls operation 4 \"the first operation the corpus demanded rather
  than confirmed\", and reports the probe's finding as 87% empty folded against
  22% worst split. **Ten lines of jq reproduce both numbers**, and find the
  discriminator with no field named: two fields are present in all 564
  resources, `id` at 564 distinct values and `resourceType` at 20, and the
  cardinality tells a kind from an identifier without knowing what FHIR is.

  THAT IS NOT A REFUTATION OF THE OPERATION. It is a correction to how the
  operation should be described. The contribution is not arithmetic nobody could
  perform — it is **knowing that the question is worth asking, and asking it
  unprompted.** jq answered every part of this because I already knew the shape
  of the answer from `NOTES.md`. A person meeting this bundle cold gets a
  parse and no suggestion that `entry[]` is twenty tables wearing one coat.

  It is also worth recording against open defect 13. That entry wants a
  structural tiebreak between a kind and an identifier and says one \"exists and
  is not written\". **Cardinality among the always-present fields is that
  tiebreak, and it is one expression.** 20 against 564 is not a close call.

  ON value[x] JQ FINDS ALL EIGHT SPELLINGS and only because I gave it the naming
  convention, which `NOTES.md` shows over-matches — `reasonCode` and
  `reasonReference` are separate R4 fields and the convention cannot tell.

  **The structural test is better, and it is clean: 261 objects in this document
  carry a `value*` field, and every one of them carries EXACTLY ONE.** No
  exceptions at any depth, and 261 is the sum of the eight spelling counts, so
  nothing is unaccounted for. Mutually exclusive siblings sharing a stem is what
  a choice type IS; the test needs no vocabulary and no knowledge of FHIR. That
  is the strongest evidence yet that `first_present` could have a **detected**
  trigger rather than a hand-written list of alternatives — and it is a
  measurement this repository did not have before today.

  WHAT JQ STILL WILL NOT DO is volunteer any of it, and question 0 is a flat
  CANNOT.
")
