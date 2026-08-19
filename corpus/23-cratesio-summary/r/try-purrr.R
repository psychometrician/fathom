# purrr — crates.io summary
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   41 KB, six collections at the root, depth 4
#  measured      2026-08-11
#  run           cd corpus/23-cratesio-summary/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                            14   NO                  by hand — 140
#   2 how deep                                    1   NO                  by hand — 4
#   3 what is one record                         12   NO                  computed, not volunteered
#   4 always present vs sometimes                 8   NO                  YES — three always-null
#   5 does any field change type                  6   NO                  yes — NONE
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                             2  NO                  THREE answers
#   8 three named fields to a table                4  YES                 yes
#   9 a field missing from some rows                6 YES                 yes, and see the trap
#  10 flatten the deepest array                     4 -                   NO ARRAY TO FLATTEN
#  11 find every path matching something           14 NO                  by hand — 11, folds to 3
#  12 flattest honest table                         2 -                   CANNOT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 11
#  14 survives the next file unchanged?               the walks do
#  15 readable a week later?                          the walks, no
#  16 lines, and how much is ceremony?                ~120
#
# THE DEFECT-25 DOCUMENT. purrr can prove the four collections share a key-set
# with one `map(names)` and a `unique`, and volunteers nothing — the corpus's
# usual sentence. THE OVERLAP is the thing nobody reports: 40 crate rows, 33
# distinct crates, seven crates in two collections each.
#
# `pluck(.default=)` FIRES ON WRITTEN NULLS here, as entry 22 measured and as
# glom's `Coalesce` and pydash's `get` do NOT. Third document, same split.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
CRATE <- c("new_crates", "most_downloaded", "most_recently_downloaded", "just_updated")
crates <- list_flatten(map(doc[CRATE], identity))

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
cat(sprintf("Q2  depth %d — the probe says 140 and 4.\n", maxd))
cat(sprintf("Q1  the root is an OBJECT of %d keys: %s\n",
            length(doc), paste(names(doc), collapse = ", ")))

# ── Q3. THE FOUR-IN-ONE, AND THE OVERLAP. ───────────────────────────────────
sigs <- map(doc[CRATE], \(lst) sort(names(lst[[1]])))
cat(sprintf("\nQ3  distinct key-sets across the four collections: %d\n",
            length(unique(sigs))))
allsig <- unique(map(crates, \(c) sort(names(c))))
cat(sprintf("Q3  over all %d crate records: %d distinct key-set(s)\n",
            length(crates), length(allsig)))
cat("    ONE — and it took `unique(map(crates, sort∘names))` on purpose.\n")
cat("    The probe prints `same shape as $.new_crates[]` unasked; that is\n")
cat("    defect 25's repair, and NO TOOL HERE VOLUNTEERS IT.\n")
ids <- map_chr(crates, "id")
nms <- map_chr(crates, "name")
dup <- sort(names(which(table(nms) > 1)))
cat(sprintf("\n     THE OVERLAP: %d rows, %d DISTINCT crates\n", length(ids), length(unique(ids))))
cat(sprintf("     appearing twice: %s\n", paste(dup, collapse = ", ")))
cat("     Concatenating the four — the obvious move once you know they share a\n")
cat("     shape — double-counts seven crates. THE PROBE DOES NOT SAY SO EITHER.\n")

# ── Q4. ─────────────────────────────────────────────────────────────────────
pres <- table(unlist(map(crates, names)))
nulls <- map_int(set_names(names(pres)),
                 \(k) sum(map_lgl(crates, \(c) is.null(c[[k]]))))
cat(sprintf("\nQ4  crate fields sometimes ABSENT: %d — every crate has all %d keys\n",
            sum(pres < length(crates)), length(pres)))
cat("Q4  written NULL:\n"); print(nulls[nulls > 0])
cat(sprintf("Q4  NULL ON ALL %d: %s\n", length(crates),
            paste(names(nulls)[nulls == length(crates)], collapse = ", ")))

# ── THE `$` TRAP. ───────────────────────────────────────────────────────────
ks <- names(pres)
pairs <- list()
for (a in ks) for (b in ks) if (a != b && startsWith(b, a)) pairs[[length(pairs) + 1]] <- c(a, b)
cat(sprintf("\n     THE `$` TRAP: %d prefix pairs among %d crate keys\n", length(pairs), length(ks)))
if (length(pairs)) for (p in pairs)
  cat(sprintf("       %-18s prefix of %-22s short key absent on %d\n",
              p[1], p[2], sum(map_lgl(crates, \(c) !(p[1] %in% names(c))))))
cat("     ZERO EXPOSURE — no key in this document is ever ABSENT, which is the\n")
cat("     condition entry 21 established. A document where everything is\n")
cat("     present cannot spring it however many pairs it has.\n")

# ── Q5/Q6/Q7. ───────────────────────────────────────────────────────────────
kind_of <- function(v) {
  if (is.null(v)) return("null")
  if (is.list(v)) return(if (is.null(names(v))) "array" else "object")
  unname(c(integer = "number", numeric = "number", double = "number",
           character = "string", logical = "boolean")[class(v)[1]])
}
kinds <- map(set_names(ks), \(k) unique(map_chr(crates, \(c) kind_of(c[[k]]))))
vary <- keep(kinds, \(v) length(setdiff(v, "null")) > 1)
cat(sprintf("\nQ5  crate fields varying, ignoring null: %s — the probe says NONE\n",
            if (length(vary)) paste(names(vary), collapse = ", ") else "NONE"))
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")
cat(sprintf("\nQ7  num_crates %s; num_downloads %s; %d rows, %d distinct\n",
            format(doc$num_crates, big.mark = ","),
            format(doc$num_downloads, big.mark = ","),
            length(ids), length(unique(ids))))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
tbl <- data.frame(name = map_chr(doc$new_crates, "name"),
                  version = map_chr(doc$new_crates, "max_version"),
                  downloads = map_dbl(doc$new_crates, "downloads"))
cat(sprintf("\nQ8  %d x %d\n", nrow(tbl), ncol(tbl))); print(head(tbl, 2))
hp <- map(crates, \(c) pluck(c, "homepage", .default = "<default>"))
cat(sprintf("\nQ9  `homepage`: %d NULL, %d defaulted, of %d\n",
            sum(map_lgl(hp, is.null)),
            sum(map_lgl(hp, \(x) identical(x, "<default>"))), length(hp)))
cat("    THE DEFAULT FIRES ON WRITTEN NULLS, on a document where nothing is\n")
cat("    ever absent — so every one of those defaults is a null that purrr\n")
cat("    turned into the default. `../python/try-glom.py` and `try-pydash.py`\n")
cat("    run the same test and print the OPPOSITE. Third document, same split.\n")
cat("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is an object of six\n")
cat("    fields; question 10 has no target here, the first time in the corpus.\n")
lk <- list_rbind(map(crates, \(c) data.frame(crate = c$name, link = names(c$links),
                                            url = unlist(c$links))))
cat(sprintf("    flattening `links` instead: %d x %d\n", nrow(lk), ncol(lk)))
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nm <- names(x)
    iwalk(x, \(v, i) find_url(v, if (is.null(nm)) paste0(p, "[]") else paste0(p, ".", i)))
  } else if (is.character(x) && length(x) == 1 && !is.na(x) && grepl("^https?://", x))
    assign(p, TRUE, hits)
}
find_url(doc)
folded <- unique(sub("^\\$\\.(new_crates|most_downloaded|most_recently_downloaded|just_updated)\\[\\]\\.",
                     "$.<one of the four>[].", ls(hits)))
cat(sprintf("\nQ11 %d distinct URL paths, folding to %d: %s\n",
            length(ls(hits)), length(folded), paste(folded, collapse = ", ")))
cat("    Same numbers as jq, ijson, glom and pydash.\n")
cat("\nQ12 purrr has no rectangling verb. The honest table is the four lists\n")
cat("    concatenated — 40 rows holding 33 distinct crates.\n")
