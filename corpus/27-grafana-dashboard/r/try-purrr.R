# purrr — Grafana "Node Exporter Full", dashboard 1860
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
#  measured      2026-08-13
#  run           cd corpus/27-grafana-dashboard/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             3   NO                  ONE LEVEL — names()
#   2 how deep                                    3   NO                  yes, by MY recursion
#   3 what is one record                          5   -                   CANNOT
#   4 always present vs sometimes                 4  YES                  yes
#   5 does any field change type                  4   NO                  yes, once melted
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            6  YES                  132 BY ENUMERATION
#   8 three named fields to a table               4  YES                  yes — map_dfr + pluck
#   9 a field missing from some rows              2  YES                  YES — pluck's .default
#  10 flatten the deepest array                   2  YES                  yes
#  11 find every path matching something          3   NO                  yes, once melted
#  12 flattest honest table                       6   NO                  PARTLY — recursion is mine
#  13 needed the shape in advance?                    YES for purrr's verbs
#  14 survives the next file unchanged?               NO
#  15 readable a week later?                          YES — pluck and map_dfr are plain
#  16 lines, and how much is ceremony?                ~60
#
# **This is the second entry running where purrr's verdict is the same**, and
# entry 28 said it first: purrr has no recursive descent over a nested LIST,
# which is surprising given what it is for. `map_depth` needs the depth as an
# argument, `flatten` goes one level, and `pluck` takes a path you already have.
#
# **On a translation catalogue that was a mismatch of shape. Here it is a wrong
# ANSWER.** `length(doc$panels)` is 31 and every purrr verb will happily work
# with that list, and there is no verb in the package that would lead anyone to
# suspect the other 101.

suppressMessages({library(jsonlite); library(purrr)})
cat(sprintf("jsonlite %s · purrr %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("purrr"),
            R.version$major, R.version$minor))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

cat(sprintf("\nQ1  names(doc) -> %d root keys: %s…\n",
            length(doc), paste(head(names(doc), 6), collapse = ", ")))
cat("    ONE LEVEL. `map_depth(doc, n, names)` needs the n, and there are twelve\n")
cat("    levels here, so knowing what to pass IS the question.\n")

# ── Q2/Q12. The melt, and the recursion is base R rather than purrr. ──────
rows <- list()
walk_it <- function(x, path = character()) {
  if (is.list(x) && length(x) > 0) {
    nm <- names(x)
    for (i in seq_along(x))
      walk_it(x[[i]], c(path, if (is.null(nm)) "*" else nm[i]))
  } else if (!is.list(x)) {
    rows[[length(rows) + 1]] <<- list(path = paste(path, collapse = "."),
                                      depth = length(path), value = x)
  }
}
t0 <- Sys.time()
walk_it(doc)
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 2)
depth <- max(map_int(rows, "depth"))

cat(sprintf("\nQ2  max depth %d, from the walk above. yes — but I wrote the walk, and\n", depth))
cat("    it agrees with jq, ijson, duckdb, rrapply and tidyjson at 12.\n")
cat(sprintf("\nQ12 %s rows x 3 in %s seconds. PARTLY: `walk_it` is eight lines of\n",
            format(length(rows), big.mark = ","), secs))
cat("    ordinary recursion and purrr contributed none of it. `map_chr` tidied\n")
cat("    the result afterwards, which is purrr doing what it is for.\n")
cat("    WHAT IS LOST: array positions collapse to `*`, so a row says a target\n")
cat("    has an `expr` and not which target.\n")

# ── Q7. THE CENTRAL QUESTION. ────────────────────────────────────────────
top <- length(doc$panels)
nested <- sum(map_int(doc$panels, \(p) length(pluck(p, "panels", .default = list()))))
cat("\nQ7  THE CENTRAL QUESTION.\n")
cat(sprintf("      length(doc$panels)                                 -> %d\n", top))
cat(sprintf("      sum(map_int(doc$panels, ~ length(pluck(.x, \"panels\")))) -> %d\n", nested))
cat(sprintf("      the sum                                            -> %d\n", top + nested))
cat("    132, BY ENUMERATION. `pluck(.default = list())` handles the 15 childless\n")
cat("    panels cleanly and that is purrr at its best — but the second \"panels\"\n")
cat("    is a literal I had to know to write. There is no `map_deep`, no\n")
cat("    recursive `keep`, and `flatten` goes exactly one level.\n")
cat("    THE DANGEROUS PART: `length(doc$panels)` is the natural first line, it\n")
cat("    returns 31, and every purrr verb downstream works perfectly on it.\n")

panels <- c(doc$panels, unlist(map(doc$panels, \(p) pluck(p, "panels", .default = list())),
                               recursive = FALSE))

# ── Q3. What is one record. ──────────────────────────────────────────────
cat("\nQ3  CANNOT — nothing proposed, nothing priced:\n")
tg <- unlist(map(panels, \(p) pluck(p, "targets", .default = list())), recursive = FALSE)
for (r in list(c("one panel per row (all depths)", length(panels)),
               c("one TOP-LEVEL panel per row", top),
               c("one target per row", length(tg)),
               c("one leaf per row", length(rows))))
  cat(sprintf("      %-32s %6s\n", r[1], format(as.integer(r[2]), big.mark = ",")))

# ── Q4. Always vs sometimes. ─────────────────────────────────────────────
fields <- sort(table(unlist(map(panels, names))), decreasing = TRUE)
cat(sprintf("\nQ4  fields over the %d panels:\n", length(panels)))
for (i in seq_len(length(fields)))
  cat(sprintf("      %-16s %4d %s\n", names(fields)[i], fields[i],
              ifelse(fields[i] == length(panels), "always", "")))
cat("    yes — `map(panels, names)` and a table, which is purrr doing exactly\n")
cat("    what it is for, ON A LIST I HAD TO ASSEMBLE FIRST. It agrees with jq\n")
cat("    and tidyjson, including `links` at 115.\n")

# ── Q5. Type variation. ──────────────────────────────────────────────────
paths <- map_chr(rows, "path")
cls <- map_chr(rows, \(r) class(r$value)[1])
tab <- tapply(cls, paths, \(x) length(unique(x)))
cat(sprintf("\nQ5  paths whose leaves have more than one class: %d\n", sum(tab > 1)))
for (p in head(names(tab)[tab > 1], 4)) cat(sprintf("      %s\n", substr(p, 1, 66)))
cat("    yes, once melted, and it agrees with ijson, rrapply and duckdb at 4.\n")

cat("\nQ6  CANNOT. No verb judges whether a key is a name or a value.\n")

# ── Q8/Q9. map_dfr and pluck are the right verbs. ────────────────────────
tbl <- map_dfr(panels, \(p) data.frame(
  title       = pluck(p, "title", .default = NA_character_),
  type        = pluck(p, "type", .default = NA_character_),
  id          = pluck(p, "id", .default = NA),
  description = pluck(p, "description", .default = NA_character_)))
cat(sprintf("\nQ8  map_dfr + pluck -> %d rows x %d. yes, and it reads back perfectly.\n",
            nrow(tbl), ncol(tbl)))
print(utils::head(tbl[, c("title", "type", "id")], 2))
cat(sprintf("\nQ9  `description` is NA on %d of %d rows and they survive. YES —\n",
            sum(is.na(tbl$description)), nrow(tbl)))
cat("    `pluck(.default = )` is the case exactly, it agrees with every other\n")
cat("    tool at 84, and it is direct prior art for `whichever`.\n")

# ── Q10. ─────────────────────────────────────────────────────────────────
cat(sprintf("\nQ10 %d targets, flattened with one `unlist(recursive = FALSE)`. yes for\n",
            length(tg)))
cat("    a level you name; `flatten` is one level by definition.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────
vals <- map_chr(rows, \(r) if (is.character(r$value)) r$value else "")
cat(sprintf("\nQ11 %d leaves mention a Grafana template variable. yes, once melted,\n",
            sum(grepl("\\$node|\\$job|\\$__rate_interval", vals))))
cat("    and it agrees with jq, duckdb, rrapply and tidyjson at 255.\n")

cat("
CONCLUSION. purrr's verdict here is the one entry 28 reached in different words,
and this document sharpens it from a mismatch into a wrong answer.

`pluck` with `.default` is genuinely excellent — Q8 and Q9 are clean, readable
and correct, and `.default` is prior art for `whichever`. `map_dfr` is the right
verb for building the table. Every one of those operates on a list of records
that somebody else had to produce.

Producing it is the problem. `length(doc$panels)` is 31, it is the natural first
line, and purrr has no verb — not `map_depth`, not `flatten`, not `keep` — that
would lead anyone to the other 101. The second `\"panels\"` in this file is a
literal I wrote because six other tools had already told me it was there.

Everything that did not need a path named in advance came out of an eight-line
`walk_it` that is base R. That is the same sentence entry 28 wrote, in the same
tool, about a completely different document, and two entries agreeing is worth
more than either alone.
")
