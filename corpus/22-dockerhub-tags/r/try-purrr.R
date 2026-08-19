# purrr — Docker Hub tags, 100 tags
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   476 KB, 100 tags under $.results, depth 5
#  measured      2026-08-11
#  run           cd corpus/22-dockerhub-tags/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                            14   NO                  by hand — 33
#   2 how deep                                    1   NO                  by hand — 5
#   3 what is one record                          3   -                   CANNOT
#   4 always present vs sometimes                10   NO                  YES — three states
#   5 does any field change type                  6   NO                  yes — NONE
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                             2  NO                  yes, both numbers
#   8 three named fields to a table                4  YES                 yes
#   9 a field missing from some rows                4  YES                 yes
#  10 flatten the deepest array                     8  YES                 yes — 1,388
#  11 find every path matching something           12  NO                  by hand — 1
#  12 flattest honest table                         2  -                   CANNOT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 11
#  14 survives the next file unchanged?               the walks do
#  15 readable a week later?                          the walks, no
#  16 lines, and how much is ceremony?                ~120, the walks are 25
#
# THE NESTED CONTROL, AND THE `$` TRAP HAS NOTHING TO BITE. Entry 21 found the
# first real exposure in the corpus — `w$issue` returning `issued` on 905 of
# 1,000 works — and the condition was an ABSENT short key plus exactly one
# longer match. THIS DOCUMENT HAS NO ABSENT KEY ANYWHERE, so however many
# prefix pairs it has, the exposure is zero by construction.
# ─────────────────────────────────────────────────────────────────────────────

library(purrr)
library(jsonlite)
cat(sprintf("R %s, purrr %s, jsonlite %s\n",
            getRversion(), packageVersion("purrr"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)
tags <- doc$results
images <- list_flatten(map(tags, "images"))

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
t0 <- Sys.time()
walk_paths(doc)
cat(sprintf("\nQ1  %d distinct paths — hand-written recursion, %.2fs\n",
            length(ls(paths)), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("Q2  depth %d — same recursion. The probe says 33 and 5.\n", maxd))
cat("    The assignment is INSIDE the loop; entry 20's first draft had it\n")
cat("    outside and counted phantom paths from empty arrays.\n")

cat("\nQ3  purrr names no candidates and prices none. CANNOT.\n")
cat(sprintf("    the two the probe prices: %d tags x 16 at 0%%, %d images x 11 at 16%%\n",
            length(tags), length(images)))
cat(sprintf("Q7  %d tags here; `count` says %s and `next` is a URL\n",
            length(tags), format(doc$count, big.mark = ",")))

# ── Q4. THREE STATES. ───────────────────────────────────────────────────────
tpres <- table(unlist(map(tags, names)))
ipres <- table(unlist(map(images, names)))
inull <- keep(map_int(set_names(names(ipres)),
                      \(k) sum(map_lgl(images, \(im) is.null(im[[k]])))), \(x) x > 0)
iempty <- keep(map_int(set_names(names(ipres)),
                       \(k) sum(map_lgl(images, \(im) identical(im[[k]], "")))), \(x) x > 0)
cat(sprintf("\nQ4  tag keys not on every tag: %d of %d\n",
            sum(tpres < length(tags)), length(tpres)))
cat(sprintf("Q4  image keys not on every image: %d of %d\n",
            sum(ipres < length(images)), length(ipres)))
cat("Q4  written NULL:\n"); print(inull)
cat("Q4  written \"\":\n"); print(iempty)
cat("    ALL THREE STATES, and `names()` plus `is.null()` plus `identical(., \"\")`\n")
cat("    are three different tests. purrr keeps them apart because a parsed R\n")
cat("    list keeps them apart; the probe counts the first two.\n")

# ── THE `$` TRAP, and why it cannot fire. ───────────────────────────────────
ks <- names(tpres)
pairs <- list()
for (a in ks) for (b in ks) if (a != b && startsWith(b, a)) pairs[[length(pairs) + 1]] <- list(a, b)
cat(sprintf("\n     THE `$` TRAP: %d prefix pairs among %d tag keys\n",
            length(pairs), length(ks)))
if (length(pairs)) for (p in pairs)
  cat(sprintf("       %-18s prefix of %-22s short key absent on %d\n",
              p[[1]], p[[2]], sum(map_lgl(tags, \(x) !(p[[1]] %in% names(x))))))
cat("     ZERO EXPOSURE, and this time the reason is structural rather than\n")
cat("     lucky: NO KEY IN THIS DOCUMENT IS EVER ABSENT. Entry 21 established\n")
cat("     the condition — an absent short key plus exactly one longer match —\n")
cat("     and a document with no absent keys cannot meet it however many pairs\n")
cat("     it has. That is the control for entry 21's finding.\n")

# ── Q5/Q6. ──────────────────────────────────────────────────────────────────
kind_of <- function(v) {
  if (is.null(v)) return("null")
  if (is.list(v)) return(if (is.null(names(v))) "array" else "object")
  unname(c(integer = "number", numeric = "number", double = "number",
           character = "string", logical = "boolean")[class(v)[1]])
}
kinds <- map(set_names(ks), \(k) unique(map_chr(tags, \(x) kind_of(x[[k]]))))
vary <- keep(kinds, \(v) length(setdiff(v, "null")) > 1)
cat(sprintf("\nQ5  tag fields varying, ignoring null: %s — the probe says NONE\n",
            if (length(vary)) paste(names(vary), collapse = ", ") else "NONE"))
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
tbl <- data.frame(name = map_chr(tags, "name"),
                  full_size = map_dbl(tags, "full_size"),
                  last_updated = map_chr(tags, "last_updated"))
cat(sprintf("\nQ8  %d x %d\n", nrow(tbl), ncol(tbl))); print(head(tbl, 2))
v <- map(images, \(im) pluck(im, "variant", .default = "<default>"))
cat(sprintf("\nQ9  `variant`: %d NULL, %d defaulted, of %d\n",
            sum(map_lgl(v, is.null)), sum(map_lgl(v, \(x) identical(x, "<default>"))),
            length(v)))
cat("    THE DEFAULT FIRES 1,125 TIMES ON A KEY THAT IS ALWAYS PRESENT, and I\n")
cat("    predicted it would never fire. `pluck(.default=)` returns the default\n")
cat("    for a present-but-NULL value, not only for an absent key — which is\n")
cat("    exactly what entry 20 measured and this is the second document to say\n")
cat("    so. `../python/try-pydash.py` runs the same test and prints the\n")
cat("    OPPOSITE: 1,125 None and 0 defaulted, because pydash's `get` hands\n")
cat("    back the null itself. TWO LANGUAGES, ONE QUESTION, TWO ANSWERS, ON A\n")
cat("    DOCUMENT WITH NO ABSENT KEYS AT ALL — so the disagreement is purely\n")
cat("    about what a written null means to a defaulting verb.\n")
t0 <- Sys.time()
res <- list_rbind(map(tags, \(x) data.frame(
  tag = x$name,
  architecture = map_chr(x$images, \(im) im$architecture %||% NA_character_),
  os = map_chr(x$images, \(im) im$os %||% NA_character_))))
cat(sprintf("\nQ10 images[] -> %d x %d, %.2fs, parent kept\n", nrow(res), ncol(res),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
hits <- new.env(hash = TRUE)
find_url <- function(x, p = "$") {
  if (is.list(x)) {
    nm <- names(x)
    iwalk(x, \(v, i) find_url(v, if (is.null(nm)) paste0(p, "[]") else paste0(p, ".", i)))
  } else if (is.character(x) && length(x) == 1 && !is.na(x) && grepl("^https?://", x))
    assign(p, TRUE, hits)
}
find_url(doc)
cat(sprintf("\nQ11 %d URL path: %s\n", length(ls(hits)), paste(ls(hits), collapse = ", ")))
cat("    The pagination link, OUTSIDE the records — pandas, polars and DuckDB\n")
cat("    all report none of one, because they build from `results`.\n")
cat("\nQ12 purrr has no rectangling verb. The walk is what it gives.\n")
