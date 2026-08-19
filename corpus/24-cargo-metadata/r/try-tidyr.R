# tidyr — cargo metadata for this repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   27 KB, 8 packages, depth 8
#  measured      2026-08-11
#  run           cd corpus/24-cargo-metadata/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  ONE LEVEL — 9, then 24
#   2 how deep                                    -   -                   CANNOT
#   3 what is one record                          6   NO                  ATTEMPTS IT, and says why
#   4 always present vs sometimes                 6   NO                  YES — four always-null
#   5 does any field change type                  3   -                   CANNOT — 7 list-columns
#   6 are any object keys data                   22   NO                  BOTH ANSWERS, as two verbs
#   7 how many records                            3   NO                  yes — 8 / 40 / 42
#   8 three named fields to a table                3  YES                 yes
#   9 a field missing from some rows               8  YES                 YES — `keep_empty`
#  10 flatten the deepest array                    7  YES                 yes — 8 rows, 5 verbs
#  11 find every path matching something           1  -                   CANNOT
#  12 flattest honest table                        4  YES                 8 x 51, 28 list-cols left
#  13 needed the shape in advance?                    NO for 1, 3, 4, 6, 7
#  14 survives the next file unchanged?               THE VERB DOES; THE VERDICT DOES NOT
#  15 readable a week later?                          yes — the verbs are named after the answer
#  16 lines, and how much is ceremony?                ~110
#
# THE FOURTEENTH TOOL, AND ON THIS DOCUMENT IT IS THE ONE THAT MATTERS. tidyr was
# added to CLAUDE.md's R list on 2026-08-09, was written for entries 01–11, and
# then was not run again — so entries 12–25 were graded "in thirteen tools" while
# missing the package CLAUDE.md itself calls the closest prior art to `rows()`
# and `take()` in either language. This is the first of the fourteen catching up.
#
# WHAT IT ADDS TO QUESTION 6, WHICH IS THIS ENTRY'S CENTREPIECE. VERDICT.md
# records that question 6 splits the thirteen three ways — four tools build the
# 28 feature names into a schema, two put them in a column, seven leave them as
# keys — and that only the middle group's output survives a `cargo add`.
#
# TIDYR IS IN TWO GROUPS AT ONCE, AND THAT IS THE FINDING. `unnest_wider` builds
# the schema (8 x 29) and `unnest_longer(indices_to=)` puts the names in a column
# (40 x 3). Same package, same document, two verbs, and THE USER PICKS. No other
# tool in this comparison offers the choice as a named pair.
#
# AND `unnest_auto` PICKS THE SURVIVOR — FOR A REASON THAT IS NOT THE VOCABULARY.
# It chooses longer and prints "elements are named, but have no names in common".
# The intersection is empty because `fathom-cli` and `fathom-core` have ZERO
# features, not because 23 of 28 names occur once. Drop the three packages that
# lack `default` and the same call says "1 names in common" and builds the 29-
# column schema. RIGHT ANSWER, WRONG REASON — and it is entry 24's own thesis
# arriving through a fourth door: the open vocabulary is lost in the schema, and
# here it was never consulted.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

# Printed rather than typed. The header records what produced the scores below;
# this line records what just ran, and a difference means the re-run is not
# comparable.
cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

doc  <- fromJSON("../source.json", simplifyVector = FALSE)
pkgs <- doc$packages

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q2. one level at a time, and that is the whole shape of the tool ────
root <- tibble(d = list(doc)) |> unnest_wider(d)
pk   <- tibble(p = pkgs)      |> unnest_wider(p)
cat(sprintf("\nQ1  root  unnest_wider -> %d x %d: %s\n", nrow(root), ncol(root),
            paste(names(root), collapse = ", ")))
cat(sprintf("Q1  packages unnest_wider -> %d x %d\n", nrow(pk), ncol(pk)))
cat(sprintf("Q2  CANNOT. Depth needs repeated unnesting, which needs the depth.\n"))
cat(sprintf("    The probe says 143 paths and depth 8; tidyr says 9 then 24.\n"))

# ── Q6. THE CENTREPIECE: both answers, as two verbs. ────────────────────────
feat <- tibble(name = map_chr(pkgs, "name"), features = map(pkgs, "features"))
wide <- feat |> unnest_wider(features, names_repair = "unique_quiet")
long <- feat |> unnest_longer(features, indices_to = "feature")
cat(sprintf("\nQ6  unnest_wider(features)             -> %d x %d  THE SCHEMA\n",
            nrow(wide), ncol(wide)))
cat(sprintf("      columns are feature names: %s …\n",
            paste(head(setdiff(names(wide), "name"), 4), collapse = ", ")))
cat(sprintf("Q6  unnest_longer(features, indices_to) -> %d x %d  THE NAMES AS DATA\n",
            nrow(long), ncol(long)))
cat(sprintf("      %d distinct names over %d occurrences; %d appear ONCE\n",
            n_distinct(long$feature), nrow(long), sum(table(long$feature) == 1)))
cat("    ONE PACKAGE, TWO VERBS, TWO GROUPS OF VERDICT.md's THREE-WAY SPLIT.\n")
cat("    The wide answer is DuckDB's STRUCT reached by another road: 28 names\n")
cat("    become 28 columns and `cargo add` invalidates the header. The long\n")
cat("    answer is `gather_object` and `melt`'s: it survives, and it reports\n")
cat("    the RAW-JSON figures — 40 occurrences with 23 names appearing once —\n")
cat("    which is exactly the evidence DuckDB's schema destroyed.\n")

# ── Q3. unnest_auto attempts the question, and states its reason. ───────────
msg <- capture.output(auto <- suppressWarnings(unnest_auto(feat, features)),
                      type = "message")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(msg, collapse = " "))))
cat(sprintf("    result %d x %d — IT PICKS THE SURVIVOR.\n", nrow(auto), ncol(auto)))

# ── and the reason is NOT the open vocabulary. This is the measurement. ─────
nm <- map(pkgs, \(p) names(p$features)); names(nm) <- map_chr(pkgs, "name")
empty <- names(nm)[lengths(nm) == 0]
cat(sprintf("    intersection across all %d packages: %d names\n",
            length(nm), length(Reduce(intersect, nm))))
cat(sprintf("    and it is empty because %s have ZERO features.\n",
            paste(empty, collapse = " and ")))
has_default <- map_lgl(nm, \(x) "default" %in% x)
cat(sprintf("    `default` is on %d of %d packages, missing from %s.\n",
            sum(has_default), length(nm),
            paste(names(nm)[!has_default], collapse = ", ")))
sub  <- feat |> filter(!name %in% names(nm)[!has_default])
msg2 <- capture.output(flip <- suppressWarnings(unnest_auto(sub, features)),
                       type = "message")
cat(sprintf("    DROP THOSE %d -> %s\n", sum(!has_default),
            trimws(paste(msg2, collapse = " "))))
cat(sprintf("    -> %d x %d. THE VERDICT FLIPS TO THE SCHEMA.\n",
            nrow(flip), ncol(flip)))
cat("    ══ THE RULE IS AN INTERSECTION, AND THE PROBE'S IS A RATE. ══\n")
cat("    23 of 28 names occurring exactly once is what makes this an open\n")
cat("    vocabulary, and unnest_auto never looks at it. ANY single shared name\n")
cat("    flips it to wider, so on this document the right answer is bought by\n")
cat("    two packages happening to have no features at all. Question 14 asked\n")
cat("    of the VERDICT rather than of the code: it does not survive the next\n")
cat("    file, and it need not even survive this one being subset.\n")

# ── Q4 / Q5. ────────────────────────────────────────────────────────────────
allna <- names(pk)[map_lgl(pk, \(c) if (is.list(c)) all(lengths(c) == 0) else all(is.na(c)))]
cat(sprintf("\nQ4  columns empty on ALL %d packages: %s\n", nrow(pk),
            paste(allna, collapse = ", ")))
cat("Q4  unnest_wider gives every package every column, so ABSENT and NULL\n")
cat("    arrive as the same NA. The distinction entry 21 turns on is gone.\n")
cat(sprintf("\nQ5  CANNOT. %d of %d columns are list-columns and a list-column\n",
            sum(map_lgl(pk, is.list)), ncol(pk)))
cat("    holds whatever it holds. tidyr never types a value.\n")

# ── Q7 / Q9. the row count, and the rows that vanish to get it. ────────────
keep <- feat |> unnest_longer(features, indices_to = "feature", keep_empty = TRUE)
cat(sprintf("\nQ7  %d packages; unnest_longer gives %d feature rows, or %d with\n",
            nrow(pk), nrow(long), nrow(keep)))
cat("    keep_empty = TRUE.\n")
cat(sprintf("Q9  THE DEFAULT SILENTLY DROPS %d PACKAGES — the ones with no\n",
            nrow(keep) - nrow(long)))
cat("    features. `keep_empty = TRUE` is question 9 answered by a named\n")
cat("    argument, which no other tool here has; the cost is that the default\n")
cat("    is the lossy one and nothing is printed when it fires.\n")

# ── Q10. the deepest array, and the same drop again. ───────────────────────
nodes <- tibble(n = doc$resolve$nodes) |> unnest_wider(n)
deep  <- nodes |> unnest_longer(deps) |>
  unnest_wider(deps, names_repair = "unique_quiet") |>
  unnest_longer(dep_kinds) |>
  unnest_wider(dep_kinds, names_repair = "unique_quiet")
cat(sprintf("\nQ10 resolve.nodes[].deps[].dep_kinds[] -> %d x %d, FIVE verbs\n",
            nrow(deep), ncol(deep)))
cat(sprintf("    %d nodes -> %d after unnest_longer(deps), because %d nodes have\n",
            nrow(nodes), nrow(nodes |> unnest_longer(deps)),
            sum(map_int(doc$resolve$nodes, \(x) length(x$deps)) == 0)))
cat("    no deps. purrr needed three nested maps and got the same 8 rows.\n")
cat("    THE VERB IS `descend one level` AND YOU WRITE IT ONCE PER LEVEL —\n")
cat("    which is entry 18's price, paid in a named verb instead of a loop.\n")

# ── Q8 / Q11 / Q12. ────────────────────────────────────────────────────────
three <- tibble(p = pkgs) |>
  hoist(p, name = "name", version = "version", edition = "edition") |>
  select(name, version, edition)
cat(sprintf("\nQ8  hoist() -> %d x %d, one expression\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))

cat("\nQ11 CANNOT. tidyr selects columns by name; it has no predicate over paths.\n")

flat     <- pk |> unnest_wider(features, names_repair = "unique_quiet")
featcols <- setdiff(names(flat), names(pk))
cat(sprintf("\nQ12 packages + features wide -> %d x %d, with %d list-columns still\n",
            nrow(flat), ncol(flat), sum(map_lgl(flat, is.list))))
cat(sprintf("    unflattened. THE TWO %d's ARE A COINCIDENCE and are not the same\n",
            length(featcols)))
cat(sprintf("    set: %d feature columns, and of the %d list-columns %d are feature\n",
            length(featcols), sum(map_lgl(flat, is.list)),
            sum(map_lgl(flat[featcols], is.list))))
cat(sprintf("    columns and %d are original ones.\n",
            sum(map_lgl(flat[intersect(names(pk), names(flat))], is.list))))
cat("    WHAT IS LOST: the feature columns are an open vocabulary frozen into a\n")
cat("    header, and `dependencies`, `targets` and `metadata` are still lists,\n")
cat("    so the honest flat table is not reachable without deciding what a row\n")
cat("    is — which is question 3, unanswered.\n")

cat("
13. NO for 1, 3, 4, 6 and 7 — and question 3 is the one that counts. tidyr is
    the only tool in this comparison that VOLUNTEERS a row shape and prints the
    rule it used. Being wrong out loud is a different category from not
    attempting, and on this document it is right out loud, for the wrong reason.

14. THE VERB SURVIVES AND THE VERDICT DOES NOT. `unnest_longer(features,
    indices_to = \"feature\")` is unchanged by a `cargo add`; `unnest_auto` on
    the same document with three packages removed changes its mind. A tool that
    decides for you has to be judged on the decision, not on the call.

15. YES, and it is the clearest of the fourteen. `unnest_wider` and
    `unnest_longer` are named after what comes out, so a week later the code
    says which of question 6's two answers it took.
")
