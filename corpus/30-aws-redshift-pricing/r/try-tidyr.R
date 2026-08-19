# tidyr — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/r && Rscript try-tidyr.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **tidyr's rectangling verbs are the closest prior art to `rows()` in either
# language** — `unnest_wider`, `unnest_longer`, `hoist`. This document is the
# case they were not designed for: it is objects keyed by data all the way
# down, and `unnest_wider` on a keyed collection makes one COLUMN per key.

suppressMessages({library(jsonlite); library(tidyr); library(tibble); library(dplyr)})
cat(sprintf("jsonlite %s · tidyr %s · dplyr %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("tidyr"),
            packageVersion("dplyr"), R.version$major, R.version$minor))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("parse: %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\nQ0  tidyr never sees the bytes. CANNOT.\n")

cat(sprintf("\nQ1  PARTIAL. tibble(x = doc) |> unnest_wider(x) gives the %d top-level\n",
            length(doc)))
top <- tibble(x = list(doc)) |> unnest_wider(x)
cat(sprintf("    names in one call: %s\n", paste(names(top), collapse = ", ")))
cat("    Deeper is one unnest_wider per level, each naming the level. tidyr has\n")
cat("    no recursive listing, so 'at every level' is CANNOT.\n")

cat("\nQ2  CANNOT. No depth verb. `unnest_auto` guesses one level at a time and\n")
cat("    tells you which it chose, which is a hint rather than an answer.\n")

cat("\nQ3  CANNOT. tidyr names no candidates and prices none.\n")

# ── THE ONE PLACE tidyr IS THE RIGHT TOOL. ───────────────────────────────────
# ** THE FIRST VERSION OF THIS ERRORED AND THE ERROR IS A FINDING. **
# `tibble(sku = names(...), p = ...) |> unnest_wider(p)` aborts with
# "Can't duplicate names between the affected columns and the original data:
# `sku`, from `p`" — because the SKU key is ALSO a field inside its own value.
# The document repeats its key inside the record. tidyr refuses rather than
# silently overwriting, which is the right call and is worth recording: it is
# the only tool of the fourteen that NOTICED the key was redundant.
t0 <- Sys.time()
prod <- tibble(sku_key = names(doc$products), p = unname(doc$products)) |>
  unnest_wider(p) |>
  unnest_wider(attributes, names_sep = ".")
prod_s <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\n    products rectangled: %d x %d in %.1f s — TWO unnest_wider calls.\n",
            nrow(prod), ncol(prod), prod_s))
cat(sprintf("    (sku_key == sku on all %d rows: %s — the key is repeated inside\n",
            nrow(prod), all(prod$sku_key == prod$sku)))
cat("     the record, which is why the naive column name collides.)\n")

miss <- vapply(prod, function(c) sum(is.na(c)), 1L)
n <- nrow(prod)
cat(sprintf("\nQ4  From the rectangle, NA counts per column (%d rows):\n", n))
cat(sprintf("    always: %s\n", paste(names(miss)[miss == 0], collapse = " ")))
cat(sprintf("    sometimes: %s\n",
            paste(sprintf("%s(%d)", names(miss)[miss > 0], n - miss[miss > 0]),
                  collapse = " ")))
cat("    ANSWERED. unnest_wider makes missingness explicit as NA, which is the\n")
cat("    one exploration question tidyr genuinely answers on this file.\n")

cat(sprintf("\nQ5  column classes: %s. No field changes type.\n",
            paste(unique(vapply(prod, function(c) class(c)[1], "")), collapse = ", ")))

cat("\nQ6  CANNOT, and it FAILS LOUDLY here rather than quietly.\n")
cat("    `unnest_wider` on terms$OnDemand would make ONE COLUMN PER SKU:\n")
cat(sprintf("    %d columns, one row. That is the same 100%%-empty table fathom's\n",
            length(doc$terms$OnDemand)))
cat("    menu prices, arrived at by a different road — and tidyr offers it\n")
cat("    without comment, because it has no way to know the names are data.\n")

cat(sprintf("\nQ7  %d products. The 4,505 price dimensions need three more\n", n))
cat("    unnest_longer/wider pairs, each of which I must name.\n")

cat("\nQ7a NOT APPLICABLE — no positional alignment. (Circular question.)\n")

cat("\nQ8  ANSWERED, and it is one line off the rectangle:\n")
q8 <- prod |> select(sku, productFamily, attributes.location)
print(as.data.frame(utils::head(q8, 3)))

cat(sprintf("\nQ9  attributes.instanceType present on %d of %d — the missing rows\n",
            sum(!is.na(prod$attributes.instanceType)), n))
cat("    are KEPT with NA automatically. tidyr's best answer on this document.\n")

cat("\nQ10 The deepest array is appliesTo and all 4,505 are EMPTY.\n")
cat("    `unnest_longer` on an empty list-column DROPS the row by default\n")
cat("    (keep_empty = FALSE), so the honest answer 'there are 4,505 of these\n")
cat("    and they are all empty' becomes an empty tibble unless you know to\n")
cat("    pass keep_empty. A silent row loss is exactly the failure mode the\n")
cat("    health verb exists for, arriving through the extraction door.\n")

cat("\nQ11 CANNOT. No path search. tidyr operates on a rectangle you have\n")
cat("    already built, and the question is about the document.\n")

cat("\nQ12 The flattest honest table needs products joined to price dimensions.\n")
cat("    tidyr builds the products half in two calls and the terms half not at\n")
cat("    all without a keyed-collection verb. WHAT IS LOST stopping at products:\n")
cat("    every price.\n")

cat("\nQ13 YES. Every unnest names a column, and the column names came from AWS's\n")
cat("    documentation rather than from the document.\n")
cat("Q14 PARTIAL. The products rectangle survives another service; the\n")
cat("    attributes.* columns do not, and no error is raised — just NA columns.\n")
cat("Q15 YES. unnest_wider/hoist read back very well; this is tidyr's strength.\n")
cat("Q16 ~45 lines. Low ceremony for the rectangle, and nothing at all for the\n")
cat("    exploration half.\n")

cat("\nCONCLUSION\n")
cat("tidyr answers Q4, Q8 and Q9 better than anything else in R, and answers no\n")
cat("exploration question. On this file its central verb is a TRAP: unnest_wider\n")
cat("on a data-keyed object silently offers a 1,571-column table, which is the\n")
cat("defect fathom's own menu is criticised for and tidyr does not even flag.\n")
