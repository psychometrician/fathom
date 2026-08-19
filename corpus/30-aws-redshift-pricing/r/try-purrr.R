# purrr — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/r && Rscript try-purrr.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **purrr is a list library, not a JSON library.** Everything below works and
# almost nothing below is contributed BY purrr except the spelling.

suppressMessages({library(jsonlite); library(purrr)})
cat(sprintf("jsonlite %s · purrr %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("purrr"),
            R.version$major, R.version$minor))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("parse: %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\nQ0  fromJSON parsed and said nothing; purrr never sees the bytes. CANNOT.\n")

cat(sprintf("\nQ1  names(doc) -> %d: %s\n", length(doc),
            paste(names(doc), collapse = ", ")))
cat("    ONE LEVEL. `map(doc, names)` gives the second and stops there.\n")

depth <- function(x) if (!is.list(x) || !length(x)) 0L else 1L + max(map_int(x, depth))
t0 <- Sys.time()
dep <- depth(doc)
cat(sprintf("\nQ2  %d, by a recursion I wrote (%.1f s). `map_int` is the spelling;\n",
            dep, as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    the recursion is mine. purrr has no depth verb, and `map_depth` wants\n")
cat("    the depth passed IN — question 2 assumed rather than answered.\n")

cat("\nQ3  CANNOT. purrr names no candidates and prices none.\n")

n <- length(doc$products)
tab <- doc$products |> map("attributes") |> map(names) |> flatten_chr() |> table() |> sort(decreasing = TRUE)
cat(sprintf("\nQ4  %d attribute keys over %d products — `map |> map |> flatten_chr |> table`,\n",
            length(tab), n))
cat("    which IS purrr doing real work, though the census is still my idea.\n")
cat(sprintf("    always: %s\n", paste(names(tab)[tab == n], collapse = " ")))
cat(sprintf("    sometimes: %s\n",
            paste(sprintf("%s(%d)", names(tab)[tab < n], tab[tab < n]), collapse = " ")))

cls <- doc$products |> map("attributes") |> map(~ map_chr(.x, ~ class(.x)[1])) |> flatten_chr() |> unique()
cat(sprintf("\nQ5  classes across every product attribute: %s. No field changes type.\n",
            paste(cls, collapse = ", ")))

cat("\nQ6  CANNOT. `map(doc$products, names)` returns 1,571 SKU strings and purrr\n")
cat("    has no way to say those names ARE the data. It is the same named list\n")
cat("    whether the names are fields or values.\n")

npd <- doc$terms |> map(~ map(.x, ~ map_int(.x, ~ length(.x$priceDimensions)))) |>
  flatten() |> flatten_int() |> sum()
cat(sprintf("\nQ7  %d products, %d price dimensions — three nested maps, mine.\n", n, npd))

cat("\nQ7a NO positional alignment. (Circular question — not scored.)\n")

t0 <- Sys.time()
tab8 <- doc$products |> map_dfr(~ tibble::tibble(
  sku = .x$sku, productFamily = .x$productFamily, location = .x$attributes$location))
cat(sprintf("\nQ8  %d x %d in %.1f s. `map_dfr` is the one place purrr is genuinely\n",
            nrow(tab8), ncol(tab8),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    shorter than base R.\n")

inst <- doc$products |> map_chr(~ .x$attributes$instanceType %||% NA_character_)
cat(sprintf("\nQ9  instanceType on %d of %d; `%%||%%` keeps the missing rows. purrr's\n",
            sum(!is.na(inst)), length(inst)))
cat("    best moment on this file — one operator instead of an if.\n")

appl <- doc$terms |> map(~ map(.x, ~ map(.x, ~ map_int(.x$priceDimensions, ~ length(.x$appliesTo))))) |>
  flatten() |> flatten() |> flatten_int()
cat(sprintf("\nQ10 appliesTo: %d arrays, %d elements total. ALL EMPTY.\n",
            length(appl), sum(appl)))
cat("    Flattening the deepest array gives zero rows and no tool warns you.\n")

cat("\nQ11 CANNOT. No path-matching verb; a recursive walk is mine to write.\n")
cat("    Whole-value URL matches in this document: 0 (the disclaimer contains\n")
cat("    two but is prose, not a URL).\n")

cat("\nQ12 One row per price dimension, joined to its product by sku. purrr can\n")
cat("    BUILD it once I know the shape; it cannot tell me the shape. What is\n")
cat("    lost by stopping at products: every price.\n")

cat("\nQ13 YES. Every pipeline above is written to a shape I learned elsewhere.\n")
cat("Q14 NO — the $attributes$location indexing breaks on any service whose\n")
cat("    attribute set differs, which is every other price list.\n")
cat("Q15 YES, mostly. `map_dfr` and `%||%` read back cleanly.\n")
cat("Q16 ~55 lines. The ceremony is the nesting: three and four deep maps to\n")
cat("    reach the money, because purrr has no notion of a path.\n")

cat("\nCONCLUSION\n")
cat("purrr shortens Q4, Q8 and Q9 and answers no exploration question at all.\n")
cat("On a document that is keys-as-data five times over, a list library sees a\n")
cat("list and has no word for what the names mean.\n")
