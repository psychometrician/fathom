# purrr — Crossref works, 1,000 records
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
#  measured      2026-08-11
#  run           cd corpus/21-crossref-works/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                            18   NO                  by hand — 236
#   2 how deep                                    2   NO                  by hand — 9
#   3 what is one record                          1   -                   CANNOT
#   4 always present vs sometimes                 6   NO                  YES — 40, 0 nulls
#   5 does any field change type                 14   NO                  NO at the root
#   6 are any object keys data                    5   NO                  by hand
#   7 how many records                            2   NO                  yes, both numbers
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   9   YES                 yes — 18,155
#  11 find every path matching something         14   NO                  by hand — 13, agrees
#  12 flattest honest table                       2   -                   CANNOT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 11 — and all four
#                                                     are recursions I wrote
#  14 survives the next file unchanged?               the walks do
#  15 readable a week later?                          the walks, no
#  16 lines, and how much is ceremony?                ~160, the walks are 30
#
# ══════════════════════════════════════════════════════════════════════════════
# THE `$` PARTIAL-MATCHING TRAP FIRES HERE, FOR THE FIRST TIME IN SEVEN GRADED
# DOCUMENTS, AND THE RULE THE OTHER SIX PRODUCED WAS RIGHT FOR THE WRONG REASON.
# ══════════════════════════════════════════════════════════════════════════════
#
# Entries 13, 14, 15, 18, 20 and 25 all recorded prefix pairs and ZERO exposure,
# and concluded "more pairs is not more danger". Every one of those documents
# had the short key present on every record. THIS ONE HAS 40 OF 57 FIELDS
# SOMETIMES ABSENT, which is the condition the other six lacked.
#
#   issue      -> issued                                    absent on 905  FIRES
#   published  -> published-online, -other, -print          absent on   2  SAFE
#   publisher  -> publisher-location                        absent on   0  n/a
#   reference  -> reference-count, references-count         absent on 465  SAFE
#
# ON 905 OF 1,000 WORKS, `w$issue` SILENTLY RETURNS `issued` — the publication
# date standing in for an issue number, with no warning and no error.
# `w[["issue"]]` is NULL, correctly.
#
# AND AMBIGUITY PROTECTS. R partial-matches only when the longer match is
# UNIQUE, so `reference` — absent on 465 works and a prefix of BOTH
# `reference-count` and `references-count` — returns NULL and is safe.
# MORE PAIRS ON ONE SHORT KEY MAKES IT SAFER. The real condition is an ABSENT
# short key plus EXACTLY ONE longer match, which no earlier entry could see
# because no earlier entry had an absent short key at all.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
items <- doc$message$items

cat("\nQ0  purrr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1/Q2. BY HAND, and the `[]`-on-empty bug entry 20 found is fixed here. ──
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
cat(sprintf("\nQ1  %s distinct paths — hand-written recursion, %.1fs\n",
            length(ls(paths)), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("Q2  depth %s — same recursion, and both agree with the probe.\n", maxd))
cat("    The assignment is INSIDE the loop. Entry 20's first draft had it\n")
cat("    outside and reported 49 phantom paths from empty arrays; that fix is\n")
cat("    carried here rather than rediscovered.\n")
cat("    The walk started at the ROOT and found $.message.items itself. Every\n")
cat("    frame in this comparison had to be told where the records are.\n")

cat(sprintf("\nQ3  purrr names no candidates and prices none. CANNOT.\n"))
cat(sprintf("Q7  %d works; message$`total-results` is %s\n",
            length(items), format(doc$message$`total-results`, big.mark = ",")))

# ── Q4. ──────────────────────────────────────────────────────────────────────
present <- table(unlist(map(items, names)))
absent <- present[present < length(items)]
nulls <- keep(set_names(names(present)),
              \(k) any(map_lgl(items, \(w) k %in% names(w) && is.null(w[[k]]))))
cat(sprintf("\nQ4  %d of %d keys sometimes ABSENT; %d written null\n",
            length(absent), length(present), length(nulls)))
cat("    ZERO written nulls, so `names()` and any NA-based test agree here.\n")
cat("    Entry 20's document had 17 nulls and split the tools; this one cannot.\n")

# ── THE `$` PARTIAL-MATCHING TRAP — AND ON THIS DOCUMENT IT FINALLY FIRES. ──
# Six documents in a row recorded "more pairs is not more danger" because every
# short key was always PRESENT. This document has 40 of 57 fields sometimes
# absent, which is the condition those six lacked.
#
# R's `$` partial-matches on a list, but ONLY when the prefix match is UNIQUE.
# That turns out to matter more than the pair count:
ks <- names(present)
pairs <- list()
for (a in ks) for (b in ks) if (a != b && startsWith(b, a)) pairs[[length(pairs) + 1]] <- c(a, b)
shorts <- unique(map_chr(pairs, 1))
cat(sprintf("\n     THE `$` TRAP: %d prefix pairs over %d distinct short keys, among\n",
            length(pairs), length(shorts)))
cat(sprintf("     %d record keys — and 40 of those are sometimes absent.\n", length(ks)))
total <- 0
for (a in shorts) {
  longer <- keep(ks, \(b) b != a && startsWith(b, a))
  miss <- sum(map_lgl(items, \(w) !(a %in% names(w))))
  unique_match <- length(longer) == 1
  fires <- if (unique_match) miss else 0
  total <- total + fires
  cat(sprintf("       %-12s -> %-42s absent on %4d  %s\n",
              a, paste(longer, collapse = ", "), miss,
              if (unique_match) sprintf("FIRES on %d", fires) else "ambiguous, SAFE"))
}
cat(sprintf("     REAL EXPOSURE: %d records\n", total))
cat("\n     TWO THINGS, AND BOTH ARE NEW TO THE CORPUS.\n")
w <- keep(items, \(x) !("issue" %in% names(x)) && "issued" %in% names(x))[[1]]
cat(sprintf("     1. IT FIRES. On a work with no `issue`, w$issue returns a %s of\n",
            class(w$issue)))
cat(sprintf("        length %d — that is `issued`, THE PUBLICATION DATE, silently\n",
            length(w$issue)))
cat("        standing in for an issue number. w[[\"issue\"]] is NULL, correctly.\n")
cat(sprintf("        First real exposure in seven graded documents: %d records.\n",
            sum(map_lgl(items, \(x) !("issue" %in% names(x))))))
cat("     2. AMBIGUITY PROTECTS. `reference` is absent on 465 works and is a\n")
cat("        prefix of BOTH `reference-count` and `references-count`, so R\n")
cat("        refuses to guess and returns NULL. `published` has three longer\n")
cat("        matches and is safe for the same reason.\n")
cat("        SO MORE PAIRS ON ONE SHORT KEY MAKES IT SAFER, and the rule the\n")
cat("        first six documents produced was right for the wrong reason: it is\n")
cat("        not the pair count, it is ABSENT SHORT KEY plus a UNIQUE longer one.\n")

# ── Q5. ──────────────────────────────────────────────────────────────────────
kind_of <- function(v) {
  if (is.null(v)) return("null")
  if (is.list(v)) return(if (is.null(names(v))) "array" else "object")
  c(integer = "number", numeric = "number", double = "number",
    character = "string", logical = "boolean")[class(v)[1]] |> unname()
}
kinds <- map(set_names(ks), \(k)
  unique(map_chr(items, \(w) if (k %in% names(w)) kind_of(w[[k]]) else "absent")))
varying <- keep(kinds, \(v) length(setdiff(v, c("null", "absent"))) > 1)
cat(sprintf("\nQ5  ROOT fields varying, ignoring null and absent: %s\n",
            if (length(varying)) paste(names(varying), collapse = ", ") else "NONE"))
dp <- table(map_chr(items, \(w) kind_of(w$issued$`date-parts`[[1]][[1]])))
cat(sprintf("Q5  the probe's ONE site, issued$`date-parts`[[1]][[1]]: %s\n",
            paste(sprintf("%s=%d", names(dp), dp), collapse = ", ")))
cat("    Reached by indexing twice into a list, which is knowing the answer.\n")
cat("    NOTE the backticks: `date-parts` is not a syntactic R name.\n")

# ── Q6. ──────────────────────────────────────────────────────────────────────
refk <- unique(unlist(map(items, \(w) map(w$reference %||% list(), names))))
refn <- sum(map_int(items, \(w) length(w$reference %||% list())))
cat(sprintf("\nQ6  reference[]: %d keys over %s copies\n", length(refk),
            format(refn, big.mark = ",")))
cat("    The probe DECLINES it as a vocabulary. purrr counts and judges nothing.\n")

# ── Q8/Q9/Q10. ───────────────────────────────────────────────────────────────
tbl <- data.frame(DOI = map_chr(items, "DOI"),
                  type = map_chr(items, "type"),
                  publisher = map_chr(items, \(w) w$publisher %||% NA_character_))
cat(sprintf("\nQ8  %d rows x %d\n", nrow(tbl), ncol(tbl))); print(head(tbl, 2))
ab <- map(items, \(w) pluck(w, "abstract", .default = NULL))
cat(sprintf("\nQ9  abstract non-NULL on %d of %d\n",
            sum(!map_lgl(ab, is.null)), length(ab)))
t0 <- Sys.time()
res <- list_rbind(map(items, \(w) {
  rs <- w$reference %||% list()
  if (!length(rs)) return(NULL)
  data.frame(work_DOI = w$DOI, key = map_chr(rs, \(r) r$key %||% NA_character_))
}))
cat(sprintf("\nQ10 reference[] -> %d rows x %d, %.1fs\n", nrow(res), ncol(res),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))

# ── Q11. ─────────────────────────────────────────────────────────────────────
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nm <- names(x)
    iwalk(x, \(v, i) find_url(v, if (is.null(nm)) paste0(p, "[]") else paste0(p, ".", i)))
  } else if (is.character(x) && length(x) == 1 && !is.na(x) && grepl("^https?://", x)) {
    assign(p, TRUE, hits)
  }
}
t0 <- Sys.time()
find_url(doc)
cat(sprintf("\nQ11 %d URL paths, %.1fs — jq, ijson, glom and pydash all say 13\n",
            length(ls(hits)), as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\nQ12 purrr has no rectangling verb. The walk is what it gives; the table\n")
cat("    is what it does not.\n")
