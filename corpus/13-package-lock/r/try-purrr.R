# purrr — an npm lockfile, 1,657 packages keyed by install path
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   759 KB, 1,657 packages, depth 5
#  measured      2026-08-11
#  run           cd corpus/13-package-lock/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                            13   NO                  by hand
#   2 how deep                                    2   NO                  by hand
#   3 what is one record                          3   YES                 CANNOT
#   4 always present vs sometimes                 5   YES                 yes
#   5 does any field change type                  8   YES                 yes, with a hand type fn
#   6 are any object keys data                    6   -                   NO
#   7 how many records                            1   YES                 yes
#   8 three named fields to a table              16   YES                 yes — imap keeps the key
#   9 a field missing from some rows              3   YES                 yes — pluck default
#  10 flatten the deepest array                   6   YES                 PARTLY
#  11 find every path matching something         13   NO                  by hand
#  12 flattest honest table                       6   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 4, 5, 7
#  14 survives the next file unchanged?               Q4/Q5 yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~130, and the two walks are 26
#
# **`imap` IS THE RIGHT VERB FOR A KEYED COLLECTION AND purrr HAS IT.** On a
# document where the record's identity is its KEY — the install path — most tools
# in this comparison either lose it (jmespath's `values()`) or make you zip it
# back on. `imap(pkgs, \(r, path) ...)` hands you both, and it is the one place
# purrr's vocabulary fits this file better than it fits a plain array.
#
# **BUT IT COUNTS KEYS AS PRESENCE, AND HERE THAT IS THE EASY HALF.** Question 4
# comes out 21 fields with only `version` on all 1,657 — the probe's answer — and
# it was never in doubt, because this document has no nulls either. Two corpus
# files running, the absent-vs-null distinction has cost nothing.
#
# **THE `$` TRAP FIRES AGAIN, ON DIFFERENT FIELDS.** `dev`/`devDependencies`,
# `optional`/`optionalDependencies` and `peerDependencies`/`peerDependenciesMeta`
# are three prefix pairs, and `$` partial-matches all three — silently returning
# a LIST where a BOOLEAN was expected. `14-nyc-311` had one such pair; this has
# three, and the trap is now a property of ragged R records rather than a quirk
# of one file. `[[` is used everywhere below.
#
# **AND THE ROOT PACKAGE IS UNREACHABLE BY NAME.** npm keys the project itself
# with the EMPTY STRING, and **R's `[[` by name cannot retrieve it**:
# `match("", names(pkgs))` is 1 and `pkgs[[""]]` is `NULL`. The first draft of
# this file looked each record up by `pkgs[[path]]` and row 1 came back all NA.
# **DuckDB REFUSES the entire document over that same key.** One zero-length key,
# two tools, one loud failure and one silent one — and `imap`, which iterates
# positionally, sidesteps it without ever mentioning why.
#
# **AND QUESTION 1 IS 13 LINES OF RECURSION THAT PRODUCES THE WRONG SHAPE OF
# ANSWER.** Enumerating paths gives **16,545** — right, and useless. Folding the
# seven keyed collections gives **49**. purrr supplies neither the walk nor the
# fold, and the fold is the part that turns a listing into a description.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
pkgs <- doc$packages
n <- length(pkgs)
cat(sprintf("    parsed %d packages in %.1fs\n", n,
            as.numeric(Sys.time() - t0, units = "secs")))

KEYED <- c("dependencies", "devDependencies", "optionalDependencies",
           "peerDependencies", "peerDependenciesMeta", "bin")

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  purrr never saw the bytes; jsonlite parsed and said nothing. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — by hand, twice. ───────────────────
raw <- new.env(hash = TRUE); folded <- new.env(hash = TRUE); maxd <- 0
walk_paths <- function(x, p = "$", f = "$", d = 1) {
  if (is.list(x)) {
    maxd <<- max(maxd, d)
    nm <- names(x)
    keyed <- f == "$.packages" || sub("^.*\\.", "", f) %in% KEYED
    if (is.null(nm)) {
      assign(paste0(p, "[]"), TRUE, raw); assign(paste0(f, "[]"), TRUE, folded)
      walk(x, \(v) walk_paths(v, paste0(p, "[]"), paste0(f, "[]"), d + 1))
    } else {
      iwalk(x, \(v, k) {
        nf <- if (keyed) paste0(f, ".<key>") else paste0(f, ".", k)
        assign(paste0(p, ".", k), TRUE, raw); assign(nf, TRUE, folded)
        walk_paths(v, paste0(p, ".", k), nf, d + 1)
      })
    }
  }
}
t1 <- Sys.time()
walk_paths(doc)
cat(sprintf("\nQ1  %s distinct RAW paths in %.1fs — the probe prints 16,545 too\n",
            format(length(ls(raw)), big.mark = ","),
            as.numeric(Sys.time() - t1, units = "secs")))
cat("Q1 ", length(ls(folded)), "once the seven keyed collections fold to <key>\n")
cat("    A ratio of", length(ls(raw)) %/% length(ls(folded)), "to 1. The raw listing is not a\n")
cat("    description of this document; it is the document's keys as paths.\n")
cat("Q2  depth", maxd, "— same recursion, and it agrees with the probe.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  purrr names no row candidates and prices none. The probe names EIGHT\n")
cat("    with costs, including `an entry of packages 1,657 x 1394 99% empty`,\n")
cat("    which is the one a reader would otherwise build by accident. CANNOT.\n")
cat("Q7 ", n, "packages\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
present <- table(unlist(map(pkgs, names)))
cat("\nQ4 ", length(present), "distinct fields; always", sum(present == n),
    "-", names(present)[present == n], "\n")
cat("Q4  sometimes", sum(present < n), ", rarest five:\n")
print(head(sort(present), 5))
cat("    Matches the probe. `names()` counts PRESENCE, and this document has no\n")
cat("    nulls, so presence-counting and frame-counting agree — as on 14-nyc-311.\n")

# ── Q5. Does any field change type between records. ──────────────────────────
# class() is NOT enough: with simplifyVector = FALSE an object and an array are
# both `list`. All 310 `funding` values report class `list`.
json_type <- function(v) {
  if (is.null(v)) "null"
  else if (is.list(v)) if (is.null(names(v))) "array" else "object"
  else if (is.character(v)) "string"
  else if (is.logical(v)) "boolean"
  else "number"
}
kinds <- map(set_names(names(present)), \(k)
  table(map_chr(keep(pkgs, \(r) !is.null(r[[k]])), \(r) json_type(r[[k]]))))
varying <- keep(kinds, \(t) length(t) > 1)
cat("\nQ5  fields whose JSON type varies:\n")
iwalk(varying, \(t, k) cat("   ", k, ":",
                           paste(names(t), t, collapse = ", "), "\n"))
cat("    Matches the probe. `class()` alone reports NOTHING here, because a\n")
cat("    parsed object and a parsed array are both `list` — the distinguishing\n")
cat("    test is is.null(names(x)), and it had to be written.\n")

# ── Q6. Are any object keys actually data? AND THE `$` TRAP. ────────────────
cat("\nQ6  YES, and purrr cannot say so: a named list is a named list, and\n")
cat("    nothing separates 1,657 install paths from 21 field names.\n")
cat("Q6b `$` PARTIAL-MATCHES, and this file has THREE prefix pairs:\n")
for (s in c("dev", "optional", "peerDependencies")) {
  risky <- keep(pkgs, \(r) !(s %in% names(r)) && any(startsWith(names(r), s)))
  cat(sprintf("    $%-17s hits a sibling on %4d of %d", s, length(risky), n))
  if (length(risky)) {
    r <- risky[[1]]
    cat(sprintf("  |  r[[\"%s\"]] = %s, r$%s = %s",
                s, class(r[[s]])[1], s, class(eval(call("$", r, s)))[1]))
  }
  cat("\n")
}
cat("    `dev` and `optional` are BOOLEANS wherever they appear, so this is a\n")
cat("    silent type change. 14-nyc-311 had one such pair; this has three.\n")

# ── Q8. Three named fields into a table. imap KEEPS THE KEY. ────────────────
# imap gives (value, name) and iterates POSITIONALLY. Looking each record up by
# `pkgs[[path]]` instead returns NULL for the root package — see Q8b.
tbl <- imap_dfr(pkgs, \(r, path) data.frame(
  path    = path,
  version = r[["version"]] %||% NA_character_,
  license = r[["license"]] %||% NA_character_))
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cat("    The install path is the row's IDENTITY here, not a field, and purrr's\n")
cat("    `imap` carries it. jmespath's `values()` discards it entirely.\n")

cat("\nQ8b THE ROOT PACKAGE IS UNREACHABLE BY NAME IN R.\n")
cat("    npm keys the project itself with the EMPTY STRING, so names(pkgs)[1]\n")
cat("    is \"\". R's `[[` by name cannot retrieve it:\n")
cat("      match(\"\", names(pkgs))  ->", match("", names(pkgs)), "\n")
cat("      is.null(pkgs[[\"\"]])     ->", is.null(pkgs[[""]]), "   <- SILENT\n")
cat("      pkgs[[1]][[\"version\"]]  ->", pkgs[[1]][["version"]], "\n")
cat("    The first draft of this file built the table with `pkgs[[path]]` and\n")
cat("    row 1 came back all NA. DuckDB REFUSES this whole document over the\n")
cat("    same key — `a table cannot be created from an unnamed struct`. One\n")
cat("    zero-length key, two tools, one loud failure and one silent one.\n")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
lic <- map_chr(pkgs, \(r) pluck(r, "license", .default = NA_character_))
cat("\nQ9  license non-NA on", sum(!is.na(lic)), "of", length(lic),
    "— `pluck(.default=)` keeps the row\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
arr <- keep(pkgs, \(r) !is.null(r[["funding"]]) && is.null(names(r[["funding"]])))
rows <- imap_dfr(arr, \(r, path) map_dfr(r[["funding"]], \(e) data.frame(
  pkg  = path,
  type = if (is.list(e)) (e[["type"]] %||% NA_character_) else NA_character_,
  url  = if (is.list(e)) (e[["url"]] %||% NA_character_) else e)))
cat("\nQ10", nrow(rows), "funding[] rows over", length(arr), "packages\n")
print(head(rows[, c("pkg", "type")], 2))
cat("    PARTLY. Two type tests are needed — funding is object-or-array and its\n")
cat("    elements are object-or-string — and neither is a purrr verb.\n")

# ── Q11. Find every path whose value matches something — by hand. ────────────
hits <- new.env(hash = TRUE)
find_url <- function(x, f = "$") {
  if (is.list(x)) {
    nm <- names(x)
    keyed <- f == "$.packages" || sub("^.*\\.", "", f) %in% KEYED
    iwalk(x, \(v, k) find_url(v, if (is.null(nm)) paste0(f, "[]")
                                 else if (keyed) paste0(f, ".<key>")
                                 else paste0(f, ".", k)))
  } else if (is.character(x) && length(x) == 1 && grepl("https?://", x)) {
    # inherits = FALSE, or an environment used as a dictionary reaches base::
    # for names like `url`. That cost entry 25 three fields.
    assign(f, get0(f, hits, inherits = FALSE, ifnotfound = 0) + 1, hits)
  }
}
find_url(doc)
cat("\nQ11 URL-valued paths, FOLDED:\n")
for (k in ls(hits)) cat("   ", k, get(k, hits, inherits = FALSE), "\n")
cat("    13 lines of recursion AND the fold written into it. jqr does the same\n")
cat("    in one expression. Unfolded this is ~1,700 paths.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
scalar <- names(present)[map_lgl(set_names(names(present)), \(k)
  all(map_lgl(keep(pkgs, \(r) !is.null(r[[k]])), \(r) !is.list(r[[k]]))))]
flat <- imap_dfr(pkgs, \(r, path) {
  as.data.frame(c(list(path = path),
                  map(set_names(scalar), \(k) {
                    v <- r[[k]]; if (is.null(v)) NA_character_ else as.character(v)
                  })))
})
cat("\nQ12", nrow(flat), "x", ncol(flat), "— the", length(scalar), "scalar fields plus the path\n")
cat("    PARTLY. The scalar list was COMPUTED rather than typed, which is better\n")
cat("    than jsonlite's hand-written exclusion — but the ten list-valued fields\n")
cat("    are simply dropped, and six of them are the keyed collections the probe\n")
cat("    prices as separate tables of 2,841, 128, 104, 101, 78 and 25 rows.\n")
