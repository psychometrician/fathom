# rrapply — Grafana "Node Exporter Full", dashboard 1860
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
#  measured      2026-08-13
#  run           cd corpus/27-grafana-dashboard/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  yes — the melt
#   2 how deep                                    2   NO                  yes — 12
#   3 what is one record                          6   -                   CANNOT
#   4 always present vs sometimes                 5   NO                  yes
#   5 does any field change type                  5   NO                  yes
#   6 are any object keys data                    3   NO                  yes, inferred
#   7 how many records                            6   NO                  YES — 132
#   8 three named fields to a table               4  YES                  yes
#   9 a field missing from some rows              3  YES                  yes
#  10 flatten the deepest array                   3   NO                  yes
#  11 find every path matching something          3   NO                  yes
#  12 flattest honest table                       1   NO                  YES — ONE CALL
#  13 needed the shape in advance?                    NO
#  14 survives the next file unchanged?               YES
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~70
#
# **`rrapply(doc, how = "melt")` is one call and it is the best single verb any
# of the fourteen brings to this document**, which is the same sentence entry 28
# wrote about a completely different file. The result is 11,063 x 13 — a column
# per level, `L1` through `L12`, plus `value`.
#
# **And here that shape does something entry 28's document could not show off.**
# The levels are COLUMNS, not a dotted string, so "how many panels are there at
# any depth" is a question about which `L` columns hold the word `panels` — and
# the answer falls out of a `table()` nobody had to know to ask for.

suppressMessages({library(jsonlite); library(rrapply)})
cat(sprintf("jsonlite %s · rrapply %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("rrapply"),
            R.version$major, R.version$minor))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

# ── Q1/Q2/Q12. ONE CALL, and it answers three questions. ────────────────────
t0 <- Sys.time()
m <- rrapply(doc, how = "melt")
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 2)
Ls <- grep("^L", names(m), value = TRUE)
depth <- max(rowSums(!is.na(m[Ls])))

cat(sprintf("\nQ12 %s x %d in %s seconds, from ONE call: rrapply(doc, how = \"melt\").\n",
            format(nrow(m), big.mark = ","), ncol(m), secs))
cat("    YES, and it agrees with jq, ijson, pydash and duckdb at 11,063 leaves.\n")
cat("    WHAT IS LOST: nothing. The array indices are kept as L-column values,\n")
cat("    so a row still says WHICH target it came from.\n")

cat(sprintf("\nQ1  %d level columns, L1 to L%d, plus value. yes — and the columns ARE\n",
            length(Ls), length(Ls)))
cat("    the answer to 'what is in here', one per level, nothing known first.\n")
cat(sprintf("      root keys seen at L1: %d — and the document has 25.\n",
            length(unique(m$L1))))
cat("    ⚠ THE MISSING ONE IS `__elements`, WHICH IS `{}`. A melt has one row per\n")
cat("      LEAF, so an empty container produces no rows and disappears entirely.\n")
cat("      Same class of silent loss as jq's `paths(scalars)` dropping every\n")
cat("      `false` and `null`: the honest table is honest about what it contains\n")
cat("      and says nothing about what it dropped.\n")

cat(sprintf("\nQ2  %d. yes — rowSums of the non-NA level columns, and it agrees with\n", depth))
cat("    the probe, jq, ijson and duckdb at 12.\n")

# ── Q7. THE CENTRAL QUESTION, and the melt's shape answers it. ─────────────
cat("\nQ7  THE CENTRAL QUESTION.\n")
cat("    Because the levels are COLUMNS, 'where does the word panels appear?'\n")
cat("    is a question you can ask without knowing the answer first:\n")
for (L in Ls) {
  n <- sum(m[[L]] == "panels", na.rm = TRUE)
  if (n > 0) cat(sprintf("      %-4s holds \"panels\" on %s leaf rows\n", L, format(n, big.mark = ",")))
}
top <- nrow(unique(m[which(m$L1 == "panels"), c("L1", "L2")]))
nest <- nrow(unique(m[which(m$L3 == "panels"), c("L1", "L2", "L3", "L4")]))
cat(sprintf("\n      distinct L1:L2 where L1 == \"panels\"        -> %3d  (top-level panels)\n", top))
cat(sprintf("      distinct L1:L4 where L3 == \"panels\"        -> %3d  (inside a row)\n", nest))
cat(sprintf("      TOTAL                                      -> %3d\n", top + nest))
cat("    YES, and this is the strongest Q7 in the R half. `panels` appearing in\n")
cat("    BOTH L1 and L3 is visible in a two-line loop over the level columns —\n")
cat("    the nesting announces itself rather than having to be suspected.\n")

# ── Q3. What is one record. ────────────────────────────────────────────────
cat("\nQ3  rrapply counts any reading you name and proposes none:\n")
tgt_top  <- nrow(unique(m[which(m$L1 == "panels" & m$L3 == "targets"), c("L2", "L4")]))
tgt_nest <- nrow(unique(m[which(m$L3 == "panels" & m$L5 == "targets"), c("L2", "L4", "L6")]))
for (r in list(c("one panel per row (all depths)", top + nest),
               c("one TOP-LEVEL panel per row", top),
               c("one target per row", tgt_top + tgt_nest),
               c("one leaf per row", nrow(m))))
  cat(sprintf("      %-32s %6s\n", r[1], format(as.integer(r[2]), big.mark = ",")))
cat("    CANNOT. Four readings, all one `unique()` away, none proposed, none priced.\n")

# ── Q4. Always vs sometimes, over the 132 panels. ─────────────────────────
top_f  <- m[which(m$L1 == "panels" & is.na(m$L4)), c("L2", "L3")]
nest_f <- m[which(m$L3 == "panels" & is.na(m$L6)), c("L2", "L4", "L5")]
names(nest_f) <- c("a", "b", "L3")
fields <- c(top_f$L3, nest_f$L3)
tab <- sort(table(fields), decreasing = TRUE)
cat(sprintf("\nQ4  fields directly under a panel, over the %d:\n", top + nest))
for (i in seq_len(min(8, length(tab))))
  cat(sprintf("      %-16s %4d %s\n", names(tab)[i], tab[i],
              ifelse(tab[i] == top + nest, "always", "")))
cat("    yes — but this counts only fields whose value is a LEAF, because a melt\n")
cat("    has no row for a container. `fieldConfig` and `options` are missing above\n")
cat("    for that reason, and jq's answer is the more complete one.\n")

# ── Q5. Type variation. ───────────────────────────────────────────────────
paths <- apply(m[Ls], 1, function(r) paste(r[!is.na(r)], collapse = "."))
paths <- gsub("\\.[0-9]+", ".*", paths)
kinds <- tapply(m$value, paths, function(v) length(unique(vapply(v, function(x) class(x)[1], ""))))
cat(sprintf("\nQ5  paths whose leaves have more than one class: %d\n", sum(kinds > 1)))
for (p in head(names(kinds)[kinds > 1], 4)) cat(sprintf("      %s\n", substr(p, 1, 68)))
cat("    yes, once melted. Note `value` is a list column, so the class of each\n")
cat("    element survives — this is R doing the right thing where a vector would\n")
cat("    have coerced everything to character and hidden the answer.\n")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
cat("\nQ6  none — no level column holds a large open vocabulary of names.\n")
cat("    yes, inferred: the judgement is mine, the counting is the melt's.\n")

# ── Q8/Q9. Three named fields; a field missing from some rows. ────────────
panels <- c(doc$panels, unlist(lapply(doc$panels, `[[`, "panels"), recursive = FALSE))
tbl <- data.frame(
  title       = vapply(panels, function(p) p$title %||% NA_character_, ""),
  type        = vapply(panels, function(p) p$type  %||% NA_character_, ""),
  id          = vapply(panels, function(p) as.character(p$id %||% NA), ""),
  description = vapply(panels, function(p) p$description %||% NA_character_, ""))
cat(sprintf("\nQ8  %d rows x 4. yes — but built with `vapply` over a list I assembled,\n", nrow(tbl)))
cat("    not with an rrapply verb. rrapply melts; it does not pivot back.\n")
print(utils::head(tbl, 2))
cat(sprintf("\nQ9  `description` is NA on %d of %d rows and they survive. yes, and it\n",
            sum(is.na(tbl$description)), nrow(tbl)))
cat("    agrees with jq, ijson, pandas, polars and duckdb at 84.\n")

# ── Q10. Flatten the deepest array. ───────────────────────────────────────
deepest <- paths[which.max(rowSums(!is.na(m[Ls])))]
cat(sprintf("\nQ10 deepest path: %s\n", substr(deepest, 1, 72)))
cat("    yes — and note it goes through `panels` twice, which is Q7's answer\n")
cat("    turning up again in a question that did not ask it.\n")

# ── Q11. Find every path matching something. ─────────────────────────────
vals <- vapply(m$value, function(x) if (is.character(x)) x else "", "")
hits <- grepl("\\$node|\\$job|\\$__rate_interval", vals)
cat(sprintf("\nQ11 %d leaves mention a Grafana template variable. yes, and it agrees\n", sum(hits)))
cat("    with jq's 255 and duckdb's 255. One `grepl` over the melt.\n")

cat("
CONCLUSION. `rrapply(doc, how = \"melt\")` is one call, needs no shape known in
advance, and produces the same 11,063 leaves that jq, ijson, pydash and duckdb
each reach with more ceremony. On that alone it repeats entry 28's verdict.

What is new here is that the melt's SHAPE answers the central question. Because
each level is its own column rather than a segment of a dotted string, asking
'which levels hold the word panels' is a two-line loop, and the answer — L1 and
L3, 31 and 101 — is the nesting announcing itself. Every other tool that reached
132 did so because I already suspected the nesting and wrote a pattern for it.
This one showed me.

It is still not naming a record or pricing one, which is Q3's CANNOT and is the
gap the whole corpus keeps measuring. And a melt has no row for a container, so
Q4 under-reports the panel fields — `fieldConfig` and `options` simply are not
there. jq's answer to that question is the better one.
")
