# jsonlite — cargo metadata for this repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   27 KB, 8 packages, depth 8
#  measured      2026-08-11
#  run           cd corpus/24-cargo-metadata/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   PARTLY
#   1 what is in here                             8   NO                  PARTLY
#   2 how deep                                    1   -                   CANNOT
#   3 what is one record                          4   YES                 one of nine
#   4 always present vs sometimes                10   NO                  PARTLY
#   5 does any field change type                  4   NO                  yes — NONE
#   6 are any object keys data                   14   NO                  IT BUILDS COLUMNS
#   7 how many records                             2  NO                  yes
#   8 three named fields to a table                3 YES                 yes
#   9 a field missing from some rows                3 YES                 PARTLY
#  10 flatten the deepest array                     6 YES                 yes
#  11 find every path matching something            4 NO                  PARTLY
#  12 flattest honest table                         6 NO                  yes, and 28 of the
#                                                                          columns are DATA
#  13 needed the shape in advance?                    only `packages` by name
#  14 survives the next file unchanged?               NO — THE COLUMN SET IS THE DATA
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~100
#
# jsonlite SIMPLIFIES `features` INTO A NESTED DATA FRAME with one column per
# Cargo feature name — the same wrong answer to question 6 that pandas gives,
# reached by a different route. So the column names of this frame are this
# repository's dependency graph, and `cargo add` changes them.
#
# AND R's BACKTICKS ARE NEEDED FOR 14 OF THE 28, because the feature names are
# hyphenated. Entries 21 and 23 met that on genuine FIELD names; here the
# escaping chore is a property of the DATA.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

RAW <- "../source.json"
cat("\nQ0  jsonlite parses or errors; it REFUSES bare NaN. No duplicate-key or\n")
cat("    big-int report. PARTLY.\n")

simple <- fromJSON(RAW)
raw <- fromJSON(RAW, simplifyVector = FALSE)
pkgs <- raw$packages
df <- simple$packages

cat(sprintf("\nQ1  the root simplifies to a %s of %d: %s\n",
            class(simple), length(simple), paste(names(simple), collapse = ", ")))
cat(sprintf("Q1  $packages -> a %s, %d x %d\n", paste(class(df), collapse = "/"),
            nrow(df), ncol(df)))
cat("    jsonlite FOLLOWED THE WRAPPER — pandas, polars and DuckDB all returned\n")
cat("    a one-row envelope and had to be pointed at `packages` by name.\n")
cat("Q2  no depth verb. CANNOT — the probe says 8.\n")

# ── Q6. THE CENTREPIECE. ────────────────────────────────────────────────────
ft <- df$features
cat(sprintf("\nQ6  THE PROBE CALLS $.packages[].features KEYS THAT ARE DATA.\n"))
cat(sprintf("    jsonlite simplified it to a %s of %d x %d\n",
            paste(class(ft), collapse = "/"), nrow(ft), ncol(ft)))
cat(sprintf("    %d COLUMNS, one per Cargo feature: %s …\n", ncol(ft),
            paste(head(names(ft), 5), collapse = ", ")))
hy <- grep("-", names(ft), value = TRUE)
cat(sprintf("Q6  %d of the %d contain a HYPHEN, so `ft$zlib-ng-compat` is a\n",
            length(hy), ncol(ft)))
cat("    SUBTRACTION and every one needs backticks or [[ ]]:\n")
cat(sprintf("    ft$`zlib-ng-compat`[[6]] = %s\n",
            paste(ft$`zlib-ng-compat`[[6]], collapse = ", ")))
filled <- vapply(ft, \(c) sum(!vapply(c, is.null, logical(1))), integer(1))
cat(sprintf("Q6  of the %d columns, %d are filled on exactly ONE package\n",
            ncol(ft), sum(filled == 1)))
cat("    THE COLUMN NAMES ARE THIS REPOSITORY'S DEPENDENCY GRAPH — the same\n")
cat("    wrong answer pandas gives, by a different route, and Q14 is NO for\n")
cat("    the same reason: `cargo add` changes the schema.\n")
cat("    COMPARE ../python/try-duckdb.py, where the STRUCT typing made every\n")
cat("    package carry all 28 names and the once-only signal vanished. Here\n")
cat("    the simplified frame keeps NULLs, so the signal survives — one R\n")
cat("    frame and one SQL type, same choice, different consequence.\n")

# ── Q3/Q4/Q5/Q7. ────────────────────────────────────────────────────────────
atomic <- vapply(df, \(c) !(is.list(c) || is.data.frame(c)), logical(1))
cat(sprintf("\nQ3  an item of packages: %d x %d, of which %d are atomic\n",
            nrow(df), ncol(df), sum(atomic)))
cat("    the probe prices it at 8 x 57, 63% empty — counting `features`'s 28\n")
cat("    columns flat, which is where the emptiness lives.\n")
pres <- table(unlist(lapply(pkgs, names)))
nulls <- vapply(names(pres), \(k) sum(vapply(pkgs, \(p) is.null(p[[k]]), logical(1))),
                integer(1))
cat(sprintf("\nQ4  simplified: %d of %d atomic columns hold an NA\n",
            sum(vapply(df[atomic], \(c) any(is.na(c)), logical(1))), sum(atomic)))
cat(sprintf("Q4  unsimplified: %d keys ever ABSENT; written NULL:\n",
            sum(pres < length(pkgs))))
print(nulls[nulls > 0])
cat(sprintf("Q4  NULL ON ALL %d: %s\n", length(pkgs),
            paste(names(nulls)[nulls == length(pkgs)], collapse = ", ")))
cat("    `simplifyVector` decides nothing about ABSENCE — nothing is absent —\n")
cat("    and everything about question 6, which is this document's finding.\n")
cat("\nQ5  the probe reports NO type change, and jq confirms zero once `an empty\n")
cat("    array is not a type` is applied. Every simplified column is one R type.\n")
cat(sprintf("\nQ7  %d packages, %d workspace members, %d resolve nodes\n",
            nrow(df), length(simple$workspace_members), nrow(simple$resolve$nodes)))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8 <- df[, c("name", "version", "edition")]
cat(sprintf("\nQ8  %d x %d, already a frame\n", nrow(t8), ncol(t8))); print(head(t8, 2))
cat(sprintf("\nQ9  `description` non-NA on %d of %d, rows kept\n",
            sum(!is.na(df$description)), nrow(df)))
tg <- do.call(rbind, lapply(seq_len(nrow(df)), \(i) {
  t <- df$targets[[i]]; data.frame(pkg = df$name[i], target = t$name) }))
dk <- do.call(rbind, lapply(pkgs, \(p) NULL))
nodes <- raw$resolve$nodes
dkn <- sum(vapply(nodes, \(n) sum(vapply(n$deps, \(d) length(d$dep_kinds), integer(1))),
                  integer(1)))
cat(sprintf("\nQ10 targets -> %d rows; resolve.nodes[].deps[].dep_kinds[] -> %d rows\n",
            nrow(tg), dkn))
cat("    at depth 6, and NOT under `packages` — a different root branch, so the\n")
cat("    packages frame cannot reach it.\n")
chr <- names(df)[vapply(df, is.character, logical(1))]
nu <- sum(vapply(chr, \(k) any(grepl("^https?://", df[[k]])), logical(1)))
cat(sprintf("\nQ11 %d of %d character columns hold a URL; jq reports 5 distinct URL\n",
            nu, length(chr)))
cat("    PATHS, two of them inside `metadata.release.pre-release-replacements[]`.\n")
fl <- flatten(df)
cat(sprintf("\nQ12 jsonlite::flatten -> %d x %d, and %d of those columns are FEATURE\n",
            nrow(fl), ncol(fl), ncol(ft)))
cat("    NAMES. THE HONEST TABLE IS NARROWER THAN THE FLAT ONE, and the\n")
cat("    difference is exactly question 6.\n")
cat("    NOTE `jsonlite::flatten` masks `purrr::flatten` — entry 18 lost a run.\n")
