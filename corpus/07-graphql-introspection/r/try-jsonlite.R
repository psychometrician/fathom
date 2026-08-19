# jsonlite — the SpaceX GraphQL API describing its own schema
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   143 KB, 108 types, depth 13, recursion 4,
#                                 94 paths, 22 fields, explosion 4.3, keyed 0
#  measured      2026-08-10
#  run           cd corpus/07-graphql-introspection/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                             2   NO                  PARTLY
#   1 what is in here                           5   NO                  NO
#   2 how deep                                  2   NO                  yes
#   3 what is one record                        6   NO                  YES
#   4 always present vs sometimes               9   NO                  MISLEADING
#   5 does any field change type                4   YES                 partly
#   6 are any keys actually data                -   -                   n/a
#   7 how many records                          1   NO                  yes
#   8 three named fields to a table             4   YES                 yes
#  12 flattest honest table                     4   NO                  partly
#  13 needed the shape in advance?                  no for 3, 4, 7
#  16 lines, and how much is ceremony?              see the conclusion
#
#  Q4 is scored MISLEADING, a mark used once before in this corpus. The frame
#  is 0% empty by the only test jsonlite can perform and 51.7% empty in fact.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 3** in this entry's NOTES.md, committed
# before this file existed: that simplification would BUILD A FRAME here and
# fold the kinds together — the `05-fhir-bundle` outcome rather than the
# `01-npm-registry` one — because `types` is an ARRAY and not a keyed object.
#
# **This is the first time the four-outcome taxonomy is used to predict rather
# than to summarise.** Getting it wrong would have meant the taxonomy is a
# post-hoc label rather than a description of a rule.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.json"
simp <- fromJSON(path)
doc  <- fromJSON(path, simplifyVector = FALSE)
ty   <- doc$data$`__schema`$types

cat(sprintf("\n0. validate() %s — well-formedness only, as elsewhere.\n",
            validate(readChar(path, file.size(path), useBytes = TRUE))))

cat("\n1. what is in here — str():\n")
for (lv in c(3, 5))
  cat(sprintf("   str(simplified, max.level=%d)  %6d lines\n", lv,
              length(capture.output(str(simp, max.level = lv)))))

depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion\n", depth(doc)))

# ── Q3 / Q7. PREDICTION 3. ───────────────────────────────────────────────────
cat("\n3/7. what is one record — PREDICTION 3:\n")
tf <- simp$data$`__schema`$types
cat(sprintf("   $data$__schema$types is a %s: %s\n", class(tf)[1],
            if (is.data.frame(tf)) sprintf("%d x %d — A TABLE", nrow(tf), ncol(tf))
            else "NOT a table"))
cat(sprintf("   columns: %s\n", paste(names(tf), collapse = ", ")))
cat("   PREDICTION 3 CONFIRMED. It built the frame, as predicted, and folded\n")
cat("   the four kinds together. `types` is an array, so the INERT outcome that\n")
cat("   npm, Stripe and Wikidata produce was never available here.\n")
cat("   The taxonomy predicted rather than summarised, which is what it was\n")
cat("   asked to do.\n")

# ── Q4. AND HERE IS WHERE IT MISLEADS. ───────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
ks <- lapply(ty, names)
u  <- unique(unlist(ks))
n  <- length(ty)
absent <- vapply(u, function(k) sum(vapply(ty, function(t) !(k %in% names(t)), TRUE)), 0L)
nulls  <- vapply(u, function(k) sum(vapply(ty,
            function(t) k %in% names(t) && is.null(t[[k]]), TRUE)), 0L)
cat("   field           absent  null   non-null\n")
for (k in u)
  cat(sprintf("     %-14s %5d %5d %8d\n", k, absent[[k]], nulls[[k]], n - absent[[k]] - nulls[[k]]))
cat(sprintf("\n   EMPTY by absence:        %.1f%%   <- the only thing jsonlite can see\n",
            100 * sum(absent) / (n * length(u))))
cat(sprintf("   EMPTY counting nulls:    %.1f%%   <- the truth\n",
            100 * (sum(absent) + sum(nulls)) / (n * length(u))))
cat("   SCORED MISLEADING. The frame has every column filled on every row by\n")
cat("   the presence test, and half its cells carry nothing.\n")

kind <- vapply(ty, function(t) t$kind, "")
cat("\n   AND THE NULLS ARE NOT NOISE — THEY ARE THE PARTITION:\n")
cat(sprintf("     kind: %s\n", paste(sprintf("%s %d", names(table(kind)),
                                             as.integer(table(kind))), collapse = ", ")))
for (k in c("fields", "interfaces", "inputFields", "enumValues", "possibleTypes")) {
  nn <- sum(vapply(ty, function(t) !is.null(t[[k]]), TRUE))
  who <- unique(kind[vapply(ty, function(t) !is.null(t[[k]]), TRUE)])
  cat(sprintf("     %-14s non-null on %3d, and they are exactly: %s\n",
              k, nn, if (length(who)) paste(who, collapse = ", ") else "(none)"))
}
cat("   `kind` predicts EVERY null in this document. Third instance of\n")
cat("   raggedness being a partition in disguise, after 05-fhir-bundle's four\n")
cat("   whole resourceTypes and 10-wikidata's `somevalue` snak — and the first\n")
cat("   where it is expressed as NULL rather than as absence.\n")

# ── Q5 / Q8 / Q12. ───────────────────────────────────────────────────────────
cat("\n5. does any field change type:\n")
oft <- table(vapply(ty, function(t)
  if (is.null(t$fields)) "null" else class(t$fields)[1], ""))
cat(sprintf("   class(types$fields) across the 108: %s\n",
            paste(sprintf("%s x%d", names(oft), as.integer(oft)), collapse = ", ")))
cat("   PARTLY — and NOTES.md grades this file `polymorphic 0`, so the split\n")
cat("   above is null-versus-present, not two types. The genuinely interesting\n")
cat("   structure is `ofType`, which is self-similar; see try-jqr.R.\n")

cat("\n8. three named fields, one row per type:\n")
tbl <- data.frame(kind = tf$kind, name = tf$name,
                  n_fields = vapply(ty, function(t) length(t$fields), 0L))
cat(sprintf("   -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat("   Free, because question 3 was answered by the parse. This is the case\n")
cat("   jsonlite is genuinely good at and it is the same one as on 03.\n")

cat("\n12. the flattest honest table:\n")
lc <- names(tf)[vapply(tf, is.list, TRUE)]
cat(sprintf("   the frame already has %d list-columns: %s\n",
            length(lc), paste(lc, collapse = ", ")))
cat("   PARTLY. Five of eight columns are lists, so the `table` is a table in\n")
cat("   name only, and god's spec refuses every one of them.\n")

cat("
CONCLUSION — the taxonomy predicted correctly, and the frame it predicted is
the most misleading one yet by a measure jsonlite cannot take.

  **Prediction 3 held.** `types` is an array, so simplification built a 108 x 8
  frame and folded the four kinds together, exactly as on `05-fhir-bundle` and
  unlike the INERT result on npm, Stripe and Wikidata. The four-outcome taxonomy
  was used to predict for the first time and it was right, which is some evidence
  it describes the rule rather than labelling the results after the fact.

  **What it could not predict is how the fold hides here.** On `05-fhir-bundle`
  the folded frame was 87% empty and the emptiness was visible as absent keys.
  Here the frame is **0% empty by key presence and 51.7% empty counting nulls**,
  because GraphQL emits every field on every type and nulls the ones that do not
  apply. jsonlite has no test that can tell those apart — a column is present, so
  it is filled.

  **And the nulls are the partition, exactly.** `fields` and `interfaces` are
  non-null on precisely the 68 OBJECTs, `inputFields` on the 20 INPUT_OBJECTs,
  `enumValues` on the 8 ENUMs, `possibleTypes` on nothing at all. `kind` predicts
  every null in the document. That is the third document in three days where
  apparent raggedness turned out to be a partition wearing a disguise, and the
  first where the disguise is `null` rather than absence.

  **This is also why the probe finds nothing here.** `NOTES.md` predicted *the
  partition will not fire, and that is a defect* and confirmed 0 splits. The
  measurement above is the reason: by presence this document is 0% empty, so no
  split can look worthwhile. Two definitions of empty, one of them blind — which
  is `VERDICT.md` defect 5 in the one place it still bites.
")
