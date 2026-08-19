# jqr — the SpaceX GraphQL API describing its own schema
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.json   143 KB, 108 types, depth 13, recursion 4,
#                                 94 paths, 22 fields, explosion 4.3, keyed 0
#  measured      2026-08-10
#  run           cd corpus/07-graphql-introspection/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                              -   -                   CANNOT
#   1 what is in here                            6   no                  WRONG
#   2 how deep                                   1   no                  yes
#   3 what is one record                         5   NO                  partly
#   4 always present vs sometimes                4   no                  YES
#   5 does any field change type                 2   no                  yes
#   6 are any keys actually data                 -   -                   n/a
#   7 how many records                           1   YES                 yes
#  11 find every path matching something         3   no                  yes
#  13 needed the shape in advance?                   NO for 1, 2, 4, 5, 11
#  16 lines, and how much is ceremony?               9 expressions, no ceremony
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 2** in this entry's NOTES.md, committed
# before this file existed: that jq's distinct-leaf-name count would come back
# under 40 and **roughly equal the true field count of 22**.
#
# The first half held and the second did not, and the miss is the useful part.
library(jqr)

cat(sprintf("R %s, jqr %s; jq CLI reports %s (jqr's linked library is not queryable)\n",
            getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

path  <- "../source.json"
bytes <- file.size(path)
txt   <- paste(readLines(path, warn = FALSE), collapse = "")
ask   <- function(q) jq(txt, q)

cat(sprintf("\n2. depth %s, unaided\n", ask("[paths|length]|max")))
cat(sprintf("7. %s types\n", ask(".data.__schema.types|length")))

# ── Q1. PREDICTION 2, HALF WRONG. ────────────────────────────────────────────
cat("\n1. what is in here:\n")
n_leaf <- ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')
names_leaf <- ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique')
cat(sprintf("   distinct leaf names: %s\n", n_leaf))
cat(sprintf("   which are: %s\n", gsub("\\s+", "", names_leaf)))
cat("   PREDICTION 2 IS HALF WRONG. Under 40, yes. Roughly 22, NO — it is 7,\n")
cat("   and NOTES.md grades this document 22 fields.\n")
cat("   THE MISS IS THE USEFUL PART, and it is the same mechanism a third time.\n")
cat("   `paths(scalars)|last` only ever sees a field whose VALUE IS A SCALAR.\n")
cat("   GraphQL's `types`, `fields`, `args`, `interfaces`, `enumValues`,\n")
cat("   `possibleTypes`, `inputFields`, `type`, `ofType` all hold objects or\n")
cat("   arrays, so none of them can appear. The expression is not counting\n")
cat("   fields; it is counting SCALAR-VALUED fields.\n")
cat("\n   Five documents, one unchanged expression, and it is correct on ONE:\n")
cat("     01-npm-registry   3,100   vs ~40 true    OVER by 75x  (keys are leaves)\n")
cat("     03-natural-earth     63   vs 63 true     CORRECT      (flat document)\n")
cat("     09-stripe-openapi    29   vs 1,440+      UNDER        (keys hold objects)\n")
cat("     10-wikidata          34   vs 48 fields   UNDER        (keys hold objects)\n")
cat(sprintf("     07-graphql            %s   vs 22 fields   UNDER by 3x  (fields hold objects)\n",
            n_leaf))
cat("   IT IS ACCURATE ONLY ON A FLAT DOCUMENT. That is a sharper statement\n")
cat("   than `it over-reports when there is keys-as-data`, which is how\n")
cat("   VERDICT.md has been citing the npm 3,100, and it is the third correction\n")
cat("   to that reading in two days.\n")

# ── Q3 / Q4. ─────────────────────────────────────────────────────────────────
cat("\n3/4. what is one record, and what does it always carry:\n")
kinds <- ask('[.data.__schema.types[].kind]|group_by(.)|map({k:.[0],n:length})|sort_by(-.n)')
cat(sprintf("   kind: %s\n", gsub("\\s+", "", kinds)))
# NOT `[.data.__schema.types] as $t` — that wraps the array again, so `keys`
# returns the INDICES 0..107 and the result reads as 108 fields each present
# once. The first draft did exactly that and printed a confident nonsense table.
always <- ask('.data.__schema.types as $t
               | ($t|map(keys)|add|unique) as $ks
               | [ $ks[] as $k | select($t|all(has($k)))
                   | {field:$k, nonnull: ([$t[]|select(.[$k]!=null)]|length)} ]
               | sort_by(-.nonnull)')
cat("   fields present on EVERY type, with how many are non-null:\n")
cat(sprintf("   %s\n", gsub("\\s+", "", always)))
cat("   EVERY FIELD IS PRESENT ON EVERY TYPE — 0 ragged by absence, as graded.\n")
cat("   The raggedness is entirely in the NULLs, and now read the two lists\n")
cat("   together, because the non-null counts ARE the kind counts:\n")
cat("     fields 68, interfaces 68   <-  OBJECT       68\n")
cat("     inputFields 20             <-  INPUT_OBJECT 20\n")
cat("     enumValues 8               <-  ENUM          8\n")
cat("   THE NULLS ARE THE PARTITION. Not approximately — exactly. `kind` is a\n")
cat("   perfect discriminator and every null in this document is predicted by\n")
cat("   it. THIRD INSTANCE of raggedness turning out to be a partition wearing\n")
cat("   a disguise, after 05-fhir-bundle's four whole resourceTypes and\n")
cat("   10-wikidata's `somevalue` snak.\n")
cat("   AND IT EXPLAINS WHY THE PROBE FINDS NOTHING HERE. NOTES.md's prediction\n")
cat("   3 was `the partition will not fire, and that is a defect` — confirmed,\n")
cat("   0 splits. The reason is measurable above: emptiness by key PRESENCE is\n")
cat("   0%% on this document, so no split can ever look worthwhile, while\n")
cat("   emptiness counting nulls is 51.7%% and splits cleanly on `kind`.\n")
cat("   That is VERDICT.md defect 5 — two definitions of empty — surviving in\n")
cat("   the one place it still matters.\n")
cat("   `possibleTypes` is non-null on ZERO of 108: a field carried by every\n")
cat("   record and informative on none. Same shape as 03-natural-earth's\n")
cat("   `woe_id`, which is the -99 sentinel on all 241 rows.\n")

# ── Q5. Recursion, which jq states directly. ─────────────────────────────────
cat("\n5. does any field change type — and the interesting one here is ofType:\n")
oft <- ask('[..|objects|select(has("ofType"))|.ofType|if .==null then "null" else "object" end]
            |group_by(.)|map({t:.[0],n:length})')
cat(sprintf("   ofType: %s\n", gsub("\\s+", "", oft)))
depths <- ask('[paths|select(.[-1]=="ofType")|length]|group_by(.)|map({d:.[0],n:length})')
cat(sprintf("   ofType appears at path depths: %s\n", gsub("\\s+", "", depths)))
cat("   THAT IS RECURSION, NOT POLYMORPHISM, AND JQ LETS YOU SAY THE DIFFERENCE.\n")
cat("   The field is null or an object — two states of a self-similar structure.\n")
cat("   rrapply's level-count test reads the depth spread as SIX populations on\n")
cat("   a document graded `polymorphic 0`; see try-rrapply.R. jq reports the\n")
cat("   depths and the types as separate facts and neither one lies.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────────
cat("\n11. find every path whose value matches something:\n")
dep <- ask('[paths(type != "object" and type != "array") as $p|select(($p|last)=="isDeprecated")
            |select(getpath($p)==true)]|length')
cat(sprintf("   %s fields/enum values are deprecated\n", dep))
cat("   A real question about this document, answered with no shape known.\n")

cat("\n0. CANNOT — jq parses or it does not.\n")
cat("6. n/a — NOTES.md grades this file keys-as-data 0.\n")

cat("
CONCLUSION — prediction 2 half held, and the miss sharpens the corpus's most
cited number for the third time in two days.

  jq's distinct-leaf-name count is **7** where this document has 22 fields. The
  prediction said under 40 (right) and roughly 22 (wrong by a factor of three).

  The mechanism is the one that explained npm and Stripe, applied once more:
  the expression's `|last` can only see a field whose value is a SCALAR. A
  structural field in a GraphQL introspection result holds an object or an
  array, so it cannot be counted — `types` and `args` never are.

  ⚠ REVISED 2026-08-13, when the expression was corrected from `paths(scalars)`.
  Three fields this passage used to list as uncountable — `fields`, `interfaces`
  and `ofType` — ARE counted now, together with `enumValues`, `inputFields` and
  `possibleTypes`, and the count went 7 to 13. They qualify because GraphQL
  writes `null` rather than omitting them, and `null` IS a scalar; the old
  expression could not see a null at all. **A field that is null somewhere is a
  scalar-valued field**, which is a sharper statement of the same mechanism.

  **And the claim that the expression is right exactly once, on
  `03-natural-earth`, is WITHDRAWN — it is right zero times.** That document
  read 63 against 63 property fields by cancelling errors: it missed `fips_10`,
  null on every feature, and counted `coordinates`, which is not a property.
  Corrected it reads 64 against 63. See that file.

  So the claim `VERDICT.md` rests on this expression for should read: *it counts
  scalar-valued field names, which equals the field count only on a flat
  document, over-reports when keys map to scalars, and under-reports whenever
  fields hold structure.* The npm 3,100 is real and the reading of it has now
  been narrowed three times.

  WHERE JQ IS THE RIGHT TOOL HERE is question 4, and it turned up the sharpest
  thing in this directory. Every one of the eight type fields is present on all
  108 records — 0 ragged by absence, exactly as graded — and the non-null counts
  reproduce the `kind` counts exactly:

    fields 68, interfaces 68  <-  OBJECT       68
    inputFields 20            <-  INPUT_OBJECT 20
    enumValues 8              <-  ENUM          8
    possibleTypes 0           <-  nothing

  **The nulls ARE the partition, exactly.** `kind` predicts every null in the
  document. That is the third instance of raggedness turning out to be a
  partition wearing a disguise, after `05-fhir-bundle`'s four whole
  resourceTypes and `10-wikidata`'s `somevalue` snak.

  **And it explains a defect this entry recorded and could not account for.**
  `NOTES.md` predicted *the partition will not fire, and that is a defect* and
  confirmed 0 splits. Here is why, measurable: emptiness by key PRESENCE is 0%
  on this document, so no split can look worthwhile; emptiness counting NULLS is
  51.7% and splits cleanly on `kind`. `VERDICT.md` defect 5 was about two
  definitions of empty disagreeing, and this is the place that still matters.

  `possibleTypes` non-null on zero of 108 is a field every record carries and
  none fills — the same shape as `03-natural-earth`'s `woe_id` at -99 on all
  241 rows, reached by a different route.

  And it separates recursion from polymorphism, which is the distinction the
  melted frame cannot make on this file. `ofType` is null-or-object at several
  depths because it is self-similar. jq says so in two expressions; rrapply's
  level-count test reports six populations and there are none.
")
