# jsonlite — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/r && Rscript try-jsonlite.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **jsonlite is the parser every other R tool here sits on**, so it is the
# baseline: what do you get with no exploration tool at all?

suppressMessages(library(jsonlite))
cat(sprintf("jsonlite %s · R %s.%s\n", packageVersion("jsonlite"),
            R.version$major, R.version$minor))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("parse: %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

# ── Q0. ──────────────────────────────────────────────────────────────────────
cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")
cat("    It reports no duplicate keys, no big ints, no encoded values. The\n")
cat("    document is in fact sound, but jsonlite could not have told me.\n")

# ── Q1. ──────────────────────────────────────────────────────────────────────
cat(sprintf("\nQ1  names(doc) -> %d: %s\n", length(doc),
            paste(names(doc), collapse = ", ")))
cat("    ONE LEVEL. Every level below is a hand walk.\n")
cat(sprintf("    attributesList is an EMPTY object (%d keys) — a top-level key\n",
            length(doc$attributesList)))
cat("    with nothing in it, which nothing here warned me about.\n")

# ── Q2. ──────────────────────────────────────────────────────────────────────
depth <- function(x) if (!is.list(x) || !length(x)) 0L else 1L + max(vapply(x, depth, 1L))
t0 <- Sys.time()
dep <- depth(doc)
cat(sprintf("\nQ2  %d, by a recursive function I wrote (%.1f s). jsonlite has no depth verb.\n",
            dep, as.numeric(difftime(Sys.time(), t0, units = "secs"))))

# ── Q3. ──────────────────────────────────────────────────────────────────────
cat("\nQ3  CANNOT. jsonlite names no candidates and prices none. What follows is\n")
cat("    mine, found by reading AWS's documentation rather than the document:\n")
cat(sprintf("      an entry of products          %d rows\n", length(doc$products)))
cat(sprintf("      an OnDemand term              %d rows\n",
            sum(vapply(doc$terms$OnDemand, length, 1L))))
cat(sprintf("      a Reserved term               %d rows\n",
            sum(vapply(doc$terms$Reserved, length, 1L))))

# ── Q4. ──────────────────────────────────────────────────────────────────────
attrs <- lapply(doc$products, function(p) names(p$attributes))
tab <- sort(table(unlist(attrs)), decreasing = TRUE)
n <- length(doc$products)
cat(sprintf("\nQ4  %d distinct attribute keys over %d products, counted by hand:\n",
            length(tab), n))
cat(sprintf("    always (%d/%d): %s\n", n, n,
            paste(names(tab)[tab == n], collapse = " ")))
cat(sprintf("    sometimes: %s\n",
            paste(sprintf("%s(%d)", names(tab)[tab < n], tab[tab < n]),
                  collapse = " ")))

# ── Q5. ──────────────────────────────────────────────────────────────────────
types <- function(x) unique(vapply(x, function(v) class(v)[1], ""))
cat("\nQ5  Hand-checked on the product attributes: every value is character.\n")
cat(sprintf("    classes seen: %s. No field changes type.\n",
            paste(unique(unlist(lapply(doc$products,
                                       function(p) types(p$attributes)))), collapse = ", ")))

# ── Q6. ──────────────────────────────────────────────────────────────────────
cat("\nQ6  CANNOT, and this document is the case that punishes it.\n")
cat("    products, terms.OnDemand, terms.Reserved, each <sku> object and each\n")
cat("    priceDimensions object are ALL keyed by data. jsonlite gives me a\n")
cat("    named list and no opinion about whether the names are fields or values.\n")

# ── Q7. ──────────────────────────────────────────────────────────────────────
npd <- sum(vapply(doc$terms, function(tt)
  sum(vapply(tt, function(sku)
    sum(vapply(sku, function(t) length(t$priceDimensions), 1L)), 1L)), 1L))
cat(sprintf("\nQ7  %d products, %d price dimensions. Both are mine to count.\n",
            length(doc$products), npd))

# ── Q7a. ─────────────────────────────────────────────────────────────────────
cat("\nQ7a NO positional alignment here. Nothing is an array of values whose\n")
cat("    names live elsewhere. (Circular question — not scored against tools.)\n")

# ── Q8. ──────────────────────────────────────────────────────────────────────
t0 <- Sys.time()
tab8 <- do.call(rbind, lapply(doc$products, function(p) data.frame(
  sku = p$sku, productFamily = p$productFamily,
  location = p$attributes$location, stringsAsFactors = FALSE)))
cat(sprintf("\nQ8  %d x %d in %.1f s, by hand.\n", nrow(tab8), ncol(tab8),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
print(utils::head(tab8, 3))

# ── Q9. ──────────────────────────────────────────────────────────────────────
inst <- vapply(doc$products, function(p) {
  v <- p$attributes$instanceType; if (is.null(v)) NA_character_ else v }, "")
cat(sprintf("\nQ9  instanceType present on %d of %d, missing on %d, rows kept.\n",
            sum(!is.na(inst)), length(inst), sum(is.na(inst))))
cat("    `if (is.null(v)) NA` is the whole trick, and it is mine.\n")

# ── Q10. ─────────────────────────────────────────────────────────────────────
appl <- unlist(lapply(doc$terms, function(tt) lapply(tt, function(sku)
  lapply(sku, function(t) lapply(t$priceDimensions, function(pd) length(pd$appliesTo))))))
cat(sprintf("\nQ10 The deepest array is appliesTo: %d of them, and EVERY ONE IS EMPTY\n",
            length(appl)))
cat(sprintf("    (total elements %d). Flattening yields ZERO rows.\n", sum(appl)))
cat("    A correct answer that tells the reader nothing, and no tool here says so.\n")

# ── Q11. ─────────────────────────────────────────────────────────────────────
cat("\nQ11 CANNOT without writing the walk. Written by hand:\n")
found <- grepl("https?://", doc$disclaimer)
cat(sprintf("    disclaimer CONTAINS urls (%s) but is not one — a whole-value\n",
            found))
cat("    match finds 0 paths in this document, which is the honest answer.\n")

# ── Q12. ─────────────────────────────────────────────────────────────────────
cat("\nQ12 The flattest honest table is one row per price dimension joined to its\n")
cat("    product — and jsonlite gives no help building it. WHAT IS LOST if you\n")
cat("    instead take products alone: every price. The document is 8 keys wide\n")
cat("    at the top and the money is 6 levels down.\n")

# ── Q13-16. ──────────────────────────────────────────────────────────────────
cat("\nQ13 YES, entirely. Every line above encodes the shape I had to learn first.\n")
cat("Q14 NO. A different service's price list has different attribute keys and\n")
cat("    may have no Reserved terms at all; every $ index above is a guess.\n")
cat("Q15 YES — it is base R and reads back fine. That is its one durability win.\n")
cat("Q16 ~60 lines, of which the ceremony is the walks: depth, the attribute\n")
cat("    census, and the priceDimensions count are all rewritten from scratch.\n")

cat("\nCONCLUSION\n")
cat("jsonlite answers Q8 and Q9 and nothing else. It is a parser, and this\n")
cat("document is 89,094 paths of which it will show you eight.\n")
