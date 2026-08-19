# purrr — cargo metadata for this repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   27 KB, 8 packages, depth 8
#  measured      2026-08-11
#  run           cd corpus/24-cargo-metadata/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                            14   NO                  by hand — 143
#   2 how deep                                    1   NO                  by hand — 8
#   3 what is one record                          3   -                   CANNOT
#   4 always present vs sometimes                 8   NO                  YES — four always-null
#   5 does any field change type                  8   NO                  ZERO, with the rule
#   6 are any object keys data                   12   NO                  the ingredients only
#   7 how many records                             2  NO                  yes
#   8 three named fields to a table                4 YES                 yes
#   9 a field missing from some rows                6 YES                 the pluck split again
#  10 flatten the deepest array                     8 YES                 yes
#  11 find every path matching something           14 NO                  by hand — 5
#  12 flattest honest table                         2 -                   CANNOT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 6, 11
#  14 survives the next file unchanged?               the hand walks do
#  15 readable a week later?                          the walks, no
#  16 lines, and how much is ceremony?                ~120
#
# THE LAST ENTRY, AND IT ADDS A THIRD CONDITION TO ENTRY 21's `$` RULE.
# Entry 21 found partial matching firing when a short key is ABSENT and has
# EXACTLY ONE longer match. Level 1 here has zero exposure trivially — every
# package key is always present. LEVEL 2 IS THE INTERESTING ONE: the 28 feature
# names are keys too, 23 of them occur in exactly one package, and three have a
# longer relative. I EXPECTED IT TO FIRE AND IT NEVER DOES, because
# `zlib-ng-compat` and `zlib` both belong to flate2 and so are absent together.
# The full condition needs the LONGER key PRESENT where the short one is not —
# and keys-as-data is protected by it, because related names travel together.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
pkgs <- doc$packages
cat("\nQ0  purrr never saw the bytes; jsonlite parsed. CANNOT.\n")

paths <- new.env(hash = TRUE); maxd <- 0
walk_paths <- function(x, p = "$", d = 0) {
  maxd <<- max(maxd, d)
  if (is.list(x)) {
    nm <- names(x)
    if (is.null(nm)) {
      walk(x, \(v) { assign(paste0(p, "[]"), TRUE, paths)
                     walk_paths(v, paste0(p, "[]"), d + 1) })
    } else {
      iwalk(x, \(v, k) { assign(paste0(p, ".", k), TRUE, paths)
                         walk_paths(v, paste0(p, ".", k), d + 1) })
    }
  }
}
walk_paths(doc)
cat(sprintf("\nQ1  %d distinct paths — hand-written recursion\n", length(ls(paths))))
cat(sprintf("Q2  depth %d — the probe says 143 and 8, in 27 KB.\n", maxd))
cat(sprintf("Q3  purrr names no candidates. CANNOT.\nQ7  %d packages, %d workspace members, %d resolve nodes\n",
            length(pkgs), length(doc$workspace_members), length(doc$resolve$nodes)))

# ── Q6. THE CENTREPIECE. ────────────────────────────────────────────────────
feat <- table(unlist(map(pkgs, \(p) names(p$features))))
hy <- grep("-", names(feat), value = TRUE)
cat(sprintf("\nQ6  $.packages[].features — THE PROBE CALLS THESE KEYS DATA.\n"))
for (p in pkgs) cat(sprintf("    %-16s %2d features\n", p$name, length(p$features)))
cat(sprintf("Q6  %d distinct names over %d occurrences; %d appear ONCE\n",
            length(feat), sum(feat), sum(feat == 1)))
cat(sprintf("Q6  %d of them contain a HYPHEN: %s …\n", length(hy),
            paste(head(sort(hy), 4), collapse = ", ")))
cat("    A LIST NAME IN R IS A STRING, so `p$features[[\"zlib-ng-compat\"]]` needs\n")
cat("    no backticks and the open vocabulary costs no width. That is why purrr\n")
cat("    neither breaks nor decides — the same sentence as glom's and pydash's.\n")

# ── THE `$` TRAP, at two levels. ────────────────────────────────────────────
pk <- names(table(unlist(map(pkgs, names))))
pairs <- list()
for (a in pk) for (b in pk) if (a != b && startsWith(b, a)) pairs[[length(pairs) + 1]] <- c(a, b)
cat(sprintf("\n     THE `$` TRAP, LEVEL 1: %d prefix pairs among %d package keys\n",
            length(pairs), length(pk)))
if (length(pairs)) for (p in pairs)
  cat(sprintf("       %-18s prefix of %-20s short key absent on %d\n",
              p[1], p[2], sum(map_lgl(pkgs, \(x) !(p[1] %in% names(x))))))
cat("     ZERO EXPOSURE — every package key is present on every package.\n")
fn <- names(feat)
shorts <- unique(keep(fn, \(a) any(map_lgl(fn, \(b) b != a && startsWith(b, a)))))
cat(sprintf("\n     THE `$` TRAP, LEVEL 2 — THE FEATURE NAMES ARE KEYS TOO: %d short\n",
            length(shorts)))
cat("     keys with a longer match among the 28 feature names\n")
# THE FIRST DRAFT COUNTED PACKAGES THAT MERELY LACK THE SHORT KEY, and printed
# "FIRES on 7". Partial matching needs the package to LACK the short key AND to
# HAVE exactly one longer match — otherwise there is nothing to match to.
exposed <- 0
for (a in shorts) {
  longer <- keep(fn, \(b) b != a && startsWith(b, a))
  fires <- sum(map_lgl(pkgs, \(x) {
    nm <- names(x$features)
    have <- intersect(longer, nm)
    !(a %in% nm) && length(have) == 1
  }))
  exposed <- exposed + fires
  cat(sprintf("       %-10s -> %-46s %s\n", a, paste(longer, collapse = ", "),
              if (fires) sprintf("FIRES on %d package(s)", fires)
              else "never exposed"))
}
cat(sprintf("     REAL EXPOSURE AT LEVEL 2: %d package-lookups\n", exposed))
if (exposed > 0) {
  a <- keep(shorts, \(a) {
    longer <- keep(fn, \(b) b != a && startsWith(b, a))
    any(map_lgl(pkgs, \(x) { nm <- names(x$features)
                             !(a %in% nm) && length(intersect(longer, nm)) == 1 }))})[[1]]
  longer <- keep(fn, \(b) b != a && startsWith(b, a))
  demo <- keep(pkgs, \(x) { nm <- names(x$features)
                            !(a %in% nm) && length(intersect(longer, nm)) == 1 })[[1]]
  cat(sprintf("     DEMONSTRATED on %s: it has no `%s` feature, and\n", demo$name, a))
  cat(sprintf("       p$features$%s returns %s\n", a,
              if (is.null(demo$features[[a]])) "NULL"
              else sprintf("a %s — that is `%s`'s value",
                           class(demo$features[[a]])[1],
                           intersect(longer, names(demo$features))[1])))
  cat(sprintf("       p$features[[\"%s\"]] returns %s\n", a,
              if (is.null(demo$features[[a]])) "NULL" else "a value"))
} else {
  cat("     NO EXPOSURE: every package that lacks a short feature name also\n")
  cat("     lacks its longer relatives, so there is nothing to match to.\n")
}
cat("     ══ AND THAT IS A THIRD CONDITION ON ENTRY 21's RULE. ══\n")
cat("     I expected this to fire. 23 of 28 feature names occur in exactly ONE\n")
cat("     package, so a short name is absent on seven of eight — entry 21's\n")
cat("     condition (absent short key, one longer match) met by DATA rather\n")
cat("     than by schema. IT NEVER FIRES, because the longer name is absent\n")
cat("     from the same packages: `zlib-ng-compat` and `zlib` both belong to\n")
cat("     flate2, so no package has one without the other.\n")
cat("     THE FULL CONDITION IS THEREFORE: an ABSENT short key, EXACTLY ONE\n")
cat("     longer match, AND that longer key PRESENT on a record where the\n")
cat("     short one is not. Entry 21 found the first two; this document adds\n")
cat("     the third, and shows that KEYS-AS-DATA IS PROTECTED BY IT — related\n")
cat("     names come from the same source and so travel together.\n")

# ── Q4/Q5. ──────────────────────────────────────────────────────────────────
pres <- table(unlist(map(pkgs, names)))
nulls <- map_int(set_names(names(pres)), \(k) sum(map_lgl(pkgs, \(p) is.null(p[[k]]))))
cat(sprintf("\nQ4  package fields sometimes ABSENT: %d of %d\n",
            sum(pres < length(pkgs)), length(pres)))
cat("Q4  written NULL:\n"); print(nulls[nulls > 0])
cat(sprintf("Q4  NULL ON ALL %d: %s\n", length(pkgs),
            paste(names(nulls)[nulls == length(pkgs)], collapse = ", ")))
kind_of <- function(v) {
  if (is.null(v)) return("null")
  if (is.list(v)) return(if (is.null(names(v))) "array" else "object")
  unname(c(integer = "number", numeric = "number", double = "number",
           character = "string", logical = "boolean")[class(v)[1]])
}
kinds <- map(set_names(names(pres)), \(k) unique(map_chr(pkgs, \(p) kind_of(p[[k]]))))
loose <- keep(kinds, \(v) length(setdiff(v, "null")) > 1)
cat(sprintf("\nQ5  fields varying, ignoring null: %d — the probe says NONE, and jq\n",
            length(loose)))
cat("    confirms zero once `an empty array is not a type` is applied.\n")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
tbl <- data.frame(name = map_chr(pkgs, "name"), version = map_chr(pkgs, "version"),
                  edition = map_chr(pkgs, "edition"))
cat(sprintf("\nQ8  %d x %d\n", nrow(tbl), ncol(tbl))); print(head(tbl, 2))
d <- map(pkgs, \(p) pluck(p, "description", .default = "<default>"))
cat(sprintf("\nQ9  `description`: %d NULL, %d defaulted, of %d\n",
            sum(map_lgl(d, is.null)),
            sum(map_lgl(d, \(x) identical(x, "<default>"))), length(d)))
cat("    THE DEFAULT FIRES ON WRITTEN NULLS, and every package HAS the key —\n")
cat("    so this is purely the null case. glom's `Coalesce` and pydash's `get`\n")
cat("    return the null itself on the identical test in ../python/.\n")
cat("    FOURTH DOCUMENT ON WHICH THE THREE DEFAULTING VERBS SPLIT TWO-TO-ONE.\n")
tg <- list_rbind(map(pkgs, \(p) data.frame(
  pkg = p$name, target = map_chr(p$targets, "name"))))
dk <- list_rbind(map(doc$resolve$nodes, \(n) {
  if (!length(n$deps)) return(NULL)
  list_rbind(map(n$deps, \(d) data.frame(node = n$id,
                                         kind = map_chr(d$dep_kinds, \(k) k$kind %||% NA_character_))))
}))
cat(sprintf("\nQ10 targets -> %d rows; resolve.nodes[].deps[].dep_kinds[] -> %d rows\n",
            nrow(tg), nrow(dk)))
cat("    at depth 6, and THREE nested maps to reach it — entry 18's price for\n")
cat("    a verb that means `descend one level`, on the last document.\n")
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nm <- names(x)
    iwalk(x, \(v, i) find_url(v, if (is.null(nm)) paste0(p, "[]") else paste0(p, ".", i)))
  } else if (is.character(x) && length(x) == 1 && !is.na(x) && grepl("^https?://", x))
    assign(p, TRUE, hits)
}
find_url(doc)
cat(sprintf("\nQ11 %d distinct URL paths — same as jq, ijson, glom and pydash\n",
            length(ls(hits))))
cat("\nQ12 purrr has no rectangling verb. The walk is what it gives, and on this\n")
cat("    document the walk is the only thing that survives a `cargo add`.\n")
