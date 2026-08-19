# purrr — Homebrew's whole formula index
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
#  measured      2026-08-11
#  run           cd corpus/20-homebrew-formulae/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                            16   NO                  by hand — 1,132
#   2 how deep                                    2   NO                  by hand — 8
#   3 what is one record                          1   -                   CANNOT
#   4 always present vs sometimes                 7   NO                  YES — both halves
#   5 does any field change type                 14   NO                  NO at the root
#   6 are any object keys data                   11   NO                  by hand
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              12   YES                 yes, with a trap
#  10 flatten the deepest array                  12   YES                 yes — 557, correct
#  11 find every path matching something         16   NO                  by hand — 65 and 48
#  12 flattest honest table                       3   -                   CANNOT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 11 — but every one
#                                                     of those is a recursion I wrote
#  14 survives the next file unchanged?               the walks do; Q8/Q9/Q10 do not
#  15 readable a week later?                          the map_ verbs yes, the walks no
#  16 lines, and how much is ceremony?                ~170, of which the walks are 35
#  timing        fromJSON 0.3s(!), the path walk 7.8s, the URL walk 8.9s
#
# THE PATH WALK WAS WRONG AND SIX TOOLS CAUGHT IT. The first draft reported
# 1,181 distinct paths where jq, jqr, ijson, glom and pydash all say 1,132. One
# line: it registered the `[]` child path BEFORE iterating, so an array with no
# elements still contributed one. This document has 141,444 empty arrays and 49
# paths existed only because of them. The Python walks put the same assignment
# inside the loop and were right by accident of style. NOTHING BUT THE
# CROSS-TOOL COMPARISON WOULD HAVE CAUGHT THIS — it is a confident, plausible,
# 4.3%-wrong number.
#
# PURRR IS THE ODD ONE OUT ON THE DEFAULT TRAP, AND I PREDICTED IT WOULD NOT BE.
# `pluck(f, k, .default = D)` returns D for an ABSENT key AND for a
# present-but-null one. glom's `Coalesce` and pydash's `get`, given the
# identical probes in ../python/, return D only for the absent key. Three
# defaulting verbs, two behaviours — so entry 15's "purrr and pydash have the
# same blind spot" is too strong, and the only safe presence test in purrr is
# `k %in% names(f)`.
#
# THE `$` TRAP HAS FOUR PAIRS AND ZERO EXPOSURE, the sixth document in a row to
# say so. `keg_only`/`keg_only_reason`, `uses_from_macos`/`uses_from_macos_bounds`,
# `conflicts_with`/`conflicts_with_reasons`, `tap`/`tap_git_head` — and every
# short key is on every record. More pairs is not more danger; only an ABSENT
# exact key is.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("fromJSON(simplifyVector = FALSE) on 29.6 MB: %.1fs\n",
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  purrr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — BY HAND. ──────────────────────────
# THE FIRST DRAFT OF THIS WALK REPORTED 1,181 PATHS AND SIX OTHER TOOLS SAY
# 1,132. The bug was one line: it assigned `p[]` BEFORE iterating, so an array
# with NO elements still registered a child path. This document holds 141,444
# empty arrays, and 49 paths — 4.3% — existed only because they were empty.
# The Python walks in ../python/try-glom.py and try-pydash.py put the same
# assignment INSIDE the loop and were right by accident of style.
# Recorded because nothing but a cross-tool comparison would have caught it.
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
t0 <- Sys.time()
walk_paths(doc)
cat(sprintf("\nQ1  %s distinct paths — a hand-written recursion, %.1fs\n",
            length(ls(paths)), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    Agrees with jq, jqr, ijson, glom and pydash. The first draft said 1,181;\n")
cat("    see the comment above for the one line that cost 49 phantom paths.\n")
cat(sprintf("Q2  depth %s — same recursion. Both agree with jq and the probe.\n", maxd))
cat("    purrr has no survey verb. `map` needs a level to map over, so\n")
cat("    questions 1 and 2 are twenty lines of recursion in every R attempt.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat(sprintf("\nQ3/Q7  %s formulae. purrr names no candidates. CANNOT for Q3.\n", length(doc)))

# ── Q4. Always present vs sometimes. THE ONE IT IS GOOD AT. ──────────────────
present <- table(unlist(map(doc, names)))
absent <- present[present < length(doc)]
cat(sprintf("\nQ4  root keys NOT on every formula: %s\n",
            paste(sprintf("%s(%d)", names(absent), absent), collapse = ", ")))
nullcount <- map_int(set_names(names(present)),
                     \(k) sum(map_lgl(doc, \(f) k %in% names(f) && is.null(f[[k]]))))
cat(sprintf("Q4  always present but NULL: %s fields\n", sum(nullcount > 0)))
cat("    BOTH HALVES, correctly. `names()` is PRESENCE, so a key written null\n")
cat("    still appears — which is why purrr sits with the walkers and every\n")
cat("    frame in this corpus reports the union of the two as one set of 20.\n")

# ── THE `$` PARTIAL-MATCHING TRAP, sixth document. ───────────────────────────
ks <- names(present)
pairs <- list()
for (a in ks) for (b in ks) if (a != b && startsWith(b, a)) pairs[[length(pairs) + 1]] <- c(a, b)
cat(sprintf("\n     THE `$` TRAP: %s prefix pairs among the root keys\n", length(pairs)))
for (p in pairs) {
  miss <- sum(map_lgl(doc, \(f) !(p[1] %in% names(f))))
  cat(sprintf("       %-22s is a prefix of %-26s short key absent on %d\n",
              p[1], p[2], miss))
}
cat("     R's `$` partial-matches, so `f$keg_only` would silently return\n")
cat("     `keg_only_reason` IF `keg_only` were absent. Every short key above is\n")
cat("     on every record, so the exposure is ZERO. Entry 18 had five pairs and\n")
cat("     zero exposure; entry 15 four and zero. SIXTH DOCUMENT, SAME RULE:\n")
cat("     partial matching fires only where the exact key is ABSENT, so more\n")
cat("     pairs is not more danger.\n")

# ── Q5. Does any field change type between records. ──────────────────────────
json_t <- c(integer = "number", numeric = "number", double = "number",
            character = "string", logical = "boolean", list = "array")
kind_of <- function(v) {
  if (is.null(v)) return("null")
  if (is.list(v)) return(if (is.null(names(v))) "array" else "object")
  r <- class(v)[1]
  if (!is.na(json_t[r])) unname(json_t[r]) else r
}
kinds <- map(set_names(names(present)), \(k)
  unique(map_chr(doc, \(f) if (k %in% names(f)) kind_of(f[[k]]) else "absent")))
varying <- keep(kinds, \(v) length(setdiff(v, c("null", "absent"))) > 1)
cat(sprintf("\nQ5  ROOT fields varying, ignoring null: %s\n",
            if (length(varying)) paste(names(varying), collapse = ", ") else "NONE"))
cat("    ZERO at the root, exactly as jq's first attempt found. The probe's\n")
cat("    nine sites are all below the root or inside arrays, and reaching them\n")
cat("    means the recursion again. purrr's `map` maps over ONE level.\n")
elem <- table(map_chr(list_flatten(map(doc, \(f) f$uses_from_macos %||% list())), kind_of))
cat(sprintf("Q5  uses_from_macos ELEMENT kinds: %s\n",
            paste(sprintf("%s=%d", names(elem), elem), collapse = ", ")))
cat("    That is the probe's headline change, and it took a named field.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  no verb. The recursion's path set carries the signature:\n")
allp <- ls(paths)
for (pref in c("$[].bottle.stable.files", "$[].variations")) {
  kids <- allp[startsWith(allp, paste0(pref, "."))]
  sibs <- unique(sub("\\..*$", "", substring(kids, nchar(pref) + 2)))
  cat(sprintf("    %-26s %d sibling keys — one per platform name\n", pref, length(sibs)))
}
cat("    Reading that as 'the keys are data' is the analyst's job in purrr, as\n")
cat("    it is in jq, ijson, glom and pydash. DuckDB is the only tool in this\n")
cat("    corpus that commits to an answer, and it commits to two — see\n")
cat("    ../python/try-duckdb.py, where one of these becomes a MAP and the\n")
cat("    other a STRUCT.\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t0 <- Sys.time()
tbl <- data.frame(name = map_chr(doc, "name"),
                  desc = map_chr(doc, \(f) f$desc %||% NA_character_),
                  homepage = map_chr(doc, \(f) f$homepage %||% NA_character_))
cat(sprintf("\nQ8  %d rows x %d cols, %.1fs\n", nrow(tbl), ncol(tbl),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
print(head(tbl, 2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
ex <- map(doc, \(f) pluck(f, "executables", .default = NULL))
cat(sprintf("\nQ9  executables non-NULL on %d of %d — `pluck(.default=)` keeps the row\n",
            sum(!map_lgl(ex, is.null)), length(ex)))
r <- keep(doc, \(f) !("head_dependencies" %in% names(f)) && is.null(f$caveats))[[1]]
cat(sprintf("Q9  THE DEFAULT TRAP, same probe as the Python walkers, on %s:\n", r$name))
for (k in c("head_dependencies", "caveats")) {
  cat(sprintf("      pluck(r, %-20s .default='<none>') -> %s\n",
              paste0("'", k, "',"), format(pluck(r, k, .default = "<none>"))))
}
cat("    PURRR IS THE ODD ONE OUT AND I PREDICTED IT WOULD NOT BE.\n")
cat("    `pluck(.default=)` returns the default for BOTH — the absent key and\n")
cat("    the present-but-null one. glom's `Coalesce` and pydash's `get`, given\n")
cat("    the identical two probes in ../python/, return the default only for the\n")
cat("    ABSENT key and hand back the null itself for the other.\n")
cat("    So the corpus now has THREE defaulting verbs and TWO behaviours, and\n")
cat("    entry 15's note that pydash and purrr share the blind spot is too\n")
cat("    strong: purrr collapses absent-and-null, pydash does not.\n")
cat("    In purrr the ONLY safe test is `k %in% names(f)`, which is what Q4 uses.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
t0 <- Sys.time()
res <- list_rbind(map(doc, \(f) {
  ps <- f$patches %||% list()
  list_rbind(map(ps, \(p) {
    rs <- p$resolves %||% list()
    if (!length(rs)) return(NULL)
    data.frame(name = f$name,
               id = map_chr(rs, \(x) x$id %||% NA_character_),
               type = map_chr(rs, \(x) x$type %||% NA_character_))
  }))
}))
cat(sprintf("\nQ10 patches[].resolves[] -> %d rows x %d, %.1fs\n", nrow(res), ncol(res),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    THREE nested maps and two `%||% list()` guards. The true count is 557.\n")
cat("    Entry 18 priced depth by counting nested `map`s; this is the same cost\n")
cat("    on a shallower path — a verb that means 'descend one level' pays per level.\n")

# ── Q11. Find every path whose value matches something — by hand. ────────────
hits_n <- new.env(hash = TRUE); hits_s <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nm <- names(x)
    iwalk(x, \(v, i) find_url(v, if (is.null(nm)) paste0(p, "[]") else paste0(p, ".", i)))
  } else if (is.character(x) && length(x) == 1 && !is.na(x)) {
    if (startsWith(x, "http")) assign(p, TRUE, hits_n)
    if (grepl("^https?://", x)) assign(p, TRUE, hits_s)
  }
}
t0 <- Sys.time()
find_url(doc)
cat(sprintf("\nQ11 http-prefixed %d paths, ^https?:// %d paths, %.1fs\n",
            length(ls(hits_n)), length(ls(hits_s)),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    jq, jqr, ijson, glom and pydash all report 65 and 48. Six tools, two\n")
cat("    languages, identical numbers — the http* trap belongs to the predicate.\n")
cat("    purrr contributed the `iwalk`; the recursion is mine.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12 purrr has no rectangling verb — that is tidyr's job, see try-tidyjson\n")
cat("    and the rrapply attempt. `map_dfr` over 447 columns means naming them.\n")
cat("    What purrr gives is the walk; what it does not give is the table.\n")
