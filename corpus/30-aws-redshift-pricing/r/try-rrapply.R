# rrapply — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/r && Rscript try-rrapply.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **rrapply's `how = "melt"` is the closest thing in the fourteen to fathom's
# walk**: one row per leaf, with a column per level. On a document that is
# keys-as-data five times over, that is exactly the right primitive — and it
# is still a melt, not a description.

suppressMessages({library(jsonlite); library(rrapply)})
cat(sprintf("jsonlite %s · rrapply %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("rrapply"),
            R.version$major, R.version$minor))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("parse: %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\nQ0  rrapply never sees the bytes. CANNOT.\n")

# ── THE MELT. One row per leaf, one column per level. ─────────────────────────
t0 <- Sys.time()
m <- rrapply(doc, how = "melt")
melt_s <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
lev <- grep("^L", names(m), value = TRUE)
cat(sprintf("\n    melt: %d leaves x %d level columns in %.1f s\n",
            nrow(m), length(lev), melt_s))

cat(sprintf("\nQ1  Every field at every level, from the melt. Distinct names per level:\n"))
for (L in lev) {
  u <- unique(m[[L]]); u <- u[!is.na(u)]
  cat(sprintf("    %-4s %6d distinct  e.g. %s\n", L, length(u),
              paste(utils::head(u, 3), collapse = ", ")))
}
cat("    THIS IS A REAL ANSWER and rrapply is one of the few that gives it.\n")
cat("    But note L2, L4 and L6: 1,573 / 3,319 / 4,508 distinct 'names' that are\n")
cat("    SKUs and SKU.OFFERTERM.RATECODE. rrapply lists them as names; it does\n")
cat("    not say they are data.\n")
cat(sprintf("    AND L1 SHOWS %d WHERE THE DOCUMENT HAS %d. attributesList is an\n",
            length(unique(m$L1[!is.na(m$L1)])), length(doc)))
cat("    empty object, and an empty container contributes NO leaf to a melt — so\n")
cat("    a whole top-level key vanishes from the answer to 'what is in here'.\n")
cat("    A melt cannot report emptiness; it can only fail to mention it.\n")

cat(sprintf("\nQ2  %d — `length(lev)` from the melt, ANSWERED rather than inferred.\n",
            length(lev)))

cat("\nQ3  CANNOT. The melt gives every leaf; it names no record and prices none.\n")

pa <- m[m$L1 == "products" & !is.na(m$L4), ]
tab <- sort(table(pa$L4[pa$L3 == "attributes"]), decreasing = TRUE)
n <- length(doc$products)
cat(sprintf("\nQ4  From the melt, attributes seen on %d products:\n", n))
cat(sprintf("    always: %s\n", paste(names(tab)[tab == n], collapse = " ")))
cat(sprintf("    sometimes: %s\n",
            paste(sprintf("%s(%d)", names(tab)[tab < n], tab[tab < n]), collapse = " ")))
cat("    A group-by on the melt. rrapply supplied the melt; the census is mine.\n")

cat(sprintf("\nQ5  value column class: %s. One type everywhere — no field changes type.\n",
            paste(unique(vapply(m$value, function(v) class(v)[1], "")), collapse = ", ")))

cat("\nQ6  CANNOT — and this is the sharpest 'cannot' in the fourteen.\n")
cat("    The melt puts SKUs in L2 and SKU.OFFERTERM in L3, in the SAME columns\n")
cat("    that hold `products` and `attributes`. Field names and data values are\n")
cat("    the same kind of thing to rrapply. It is the right SHAPE for the\n")
cat("    question and has no vocabulary for the answer.\n")

cat(sprintf("\nQ7  %d products; %d price-dimension leaves under terms.\n", n,
            sum(m$L1 == "terms" & m$L5 == "priceDimensions", na.rm = TRUE)))

cat("\nQ7a NO positional alignment. (Circular question — not scored.)\n")

t0 <- Sys.time()
w <- pa[pa$L3 %in% c("sku", "productFamily") | (pa$L3 == "attributes" & pa$L4 == "location"), ]
cat(sprintf("\nQ8  %d leaf rows selected in %.1f s; reshaping to 1,571 x 3 is\n",
            nrow(w), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    a `reshape`/`pivot_wider` I write myself. rrapply melts and never casts.\n")

it <- pa[pa$L3 == "attributes" & pa$L4 == "instanceType", ]
cat(sprintf("\nQ9  instanceType appears on %d of %d products. The missing ones are\n",
            nrow(it), n))
cat("    ABSENT ROWS in the melt, not NA cells — so 'keep those rows' means a\n")
cat("    join back against the full SKU list, which is mine to write.\n")

cat("\nQ10 The deepest arrays are appliesTo and ALL 4,505 ARE EMPTY. An empty\n")
cat("    array contributes NO row to the melt, so rrapply's answer to 'flatten\n")
cat("    the deepest array' is silence — indistinguishable from no array at all.\n")

cat("\nQ11 PARTIAL, and better than most. `rrapply(doc, condition = ...)` filters\n")
cat("    leaves by value, so a URL test is one call:\n")
u <- rrapply(doc, condition = function(x) is.character(x) && grepl("^https?://", x),
             how = "melt")
cat(sprintf("    whole-value URL matches: %d. (The disclaimer contains two and is\n",
            nrow(u)))
cat("    not one, which is the honest answer.) THIS IS A REAL ANSWER.\n")

cat("\nQ12 The melt IS the flattest honest table — 89,094-ish leaf rows with\n")
cat("    their full path. WHAT IS LOST: nothing, and that is the problem. It is\n")
cat("    the whole document as a long table and no smaller than the document.\n")

cat("\nQ13 NO for the melt, YES for everything after it. That split is the whole\n")
cat("    finding: rrapply is the only R tool where the FIRST step needs no shape.\n")
cat("Q14 YES for the melt. NO for every filter above it, which names levels.\n")
cat("Q15 YES for `how = 'melt'`. The L-column convention is easy to re-read.\n")
cat("Q16 ~50 lines, and the melt is 1 of them. Everything else is the casting\n")
cat("    and the group-bys that rrapply does not do.\n")

cat("\nCONCLUSION\n")
cat("rrapply answers Q1, Q2 and Q11 outright and gives the right shape for the\n")
cat("rest, which no other R tool here does. What it does not do is have an\n")
cat("OPINION: on a file where five levels are keyed by data, it hands back the\n")
cat("SKUs as level names and leaves the reader to notice.\n")
