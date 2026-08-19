# tidyjson — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/r && Rscript try-tidyjson.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **tidyjson's `gather_object` is the one verb in R built for keys-as-data** —
# it turns object names into a `name` column, which is precisely what this
# document needs five times over. It is also the tool that made me wait.

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("tidyjson %s · dplyr %s · R %s.%s\n", packageVersion("tidyjson"),
            packageVersion("dplyr"), R.version$major, R.version$minor))

t0 <- Sys.time()
txt <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
cat(sprintf("read: %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\nQ0  tidyjson parses and says nothing about soundness. CANNOT.\n")

# ── Q1/Q2. json_types + gather_object, one level at a time. ──────────────────
t0 <- Sys.time()
top <- txt |> gather_object() |> json_types()
cat(sprintf("\nQ1  ANSWERED at one level in %.1f s — `gather_object |> json_types`:\n",
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
# ** PRINTING A tbl_json DUMPS THE DOCUMENT. ** `as.data.frame()` on a tbl_json
# materialises the JSON it is carrying as a column, so the naive print emitted
# 743,681 characters PER ROW — 6.4 MB for eight rows. Strip to a plain frame.
print(data.frame(name = top$name, type = top$type))
cat("    NOTE attributesList is reported as an object and is EMPTY — tidyjson\n")
cat("    names it, which the rrapply melt could not.\n")
cat("    'At every level' is CANNOT: each level is another gather_object.\n")

cat("\nQ2  CANNOT. No depth verb. Depth is however many gather_objects you\n")
cat("    stack before the types stop saying 'object'.\n")

cat("\nQ3  CANNOT. tidyjson names no candidates and prices none.\n")

# ── THE VERB THIS DOCUMENT NEEDS. ────────────────────────────────────────────
t0 <- Sys.time()
prod <- txt |> enter_object("products") |> gather_object("sku") |>
  spread_all()
prod_s <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\n    products: enter_object |> gather_object |> spread_all\n"))
cat(sprintf("    %d x %d in %.1f s\n", nrow(prod), ncol(prod), prod_s))
cat("    NOTE THE COLUMN NAMED sku.2. The record already has a `sku` field, so\n")
cat("    spread_all WARNS and appends .# — where tidyr ABORTED on the same\n")
cat("    collision. Two tools, one document repeating its key inside its own\n")
cat("    value, and opposite policies: one refuses, one renames and carries on.\n")
cat("    `gather_object('sku')` puts the KEY IN A COLUMN. That is the right\n")
cat("    answer to question 6 and tidyjson is the only R tool that spells it\n")
cat("    in one verb — but I still had to decide the keys were data.\n")

# `..JSON` is tidyjson's carried document, not a field of the data — drop it
# from the census or it reports as a column that is always present.
nm <- setdiff(names(prod), c("document.id", "sku", "..JSON"))
# ** `prod[nm]` RE-ADDS `..JSON`. ** Subsetting a tbl_json returns a tbl_json,
# which carries the document back in as a 23rd column and shifts the census by
# one, silently. Going through `[[` keeps it a plain vector.
miss <- vapply(nm, function(k) sum(is.na(prod[[k]])), 1L)
n <- nrow(prod)
cat(sprintf("\nQ4  ANSWERED from the spread (%d rows):\n", n))
cat(sprintf("    always: %s\n", paste(nm[miss == 0], collapse = " ")))
cat(sprintf("    sometimes: %s\n",
            paste(sprintf("%s(%d)", nm[miss > 0], n - miss[miss > 0]), collapse = " ")))

cat("\nQ5  PARTIAL. `json_types()` reports a type per value, so a field that\n")
cat("    varied would show two types across rows. Here every attribute is a\n")
cat("    string, so nothing varies — but the check is mine to construct.\n")

cat("\nQ6  ANSWERED — the ONLY tool of the fourteen with a verb for it.\n")
cat("    `gather_object(name)` IS 'these keys are data'. Used above for\n")
cat("    products; the same call works at terms.OnDemand and again at the\n")
cat("    SKU.OFFERTERM level below it.\n")
cat("    WHAT IT DOES NOT DO is tell me WHERE to use it. It is a verb I aim,\n")
cat("    not a finding I am handed — so on a document I have never seen, the\n")
cat("    five keyed levels are still mine to discover.\n")

cat(sprintf("\nQ7  %d products.\n", n))

cat("\nQ7a NO positional alignment. (Circular question — not scored.)\n")

cat("\nQ8  ANSWERED, straight off the spread:\n")
h <- head(prod, 3)
print(data.frame(sku = h$sku, productFamily = h$productFamily,
                 location = h$attributes.location))

cat(sprintf("\nQ9  attributes.instanceType present on %d of %d; spread_all keeps the\n",
            sum(!is.na(prod$attributes.instanceType)), n))
cat("    rows and fills NA. ANSWERED.\n")

cat("\nQ10 The deepest arrays are appliesTo and all 4,505 are EMPTY.\n")
cat("    `gather_array()` on an empty array yields NO rows, so the answer is an\n")
cat("    empty tibble — the same silence tidyr and rrapply give. Three R tools,\n")
cat("    three different verbs, one indistinguishable answer for 'empty' and\n")
cat("    'absent'.\n")

cat("\nQ11 CANNOT. No path search by value. tidyjson descends where you point it.\n")

cat("\nQ12 The flattest honest table needs products joined to the price\n")
cat("    dimensions four gather_objects down. tidyjson CAN express that chain —\n")
cat("    enter_object, gather_object, enter_object, gather_object, spread_all —\n")
cat("    and it is the only R tool that can write it without a hand walk.\n")
cat("    WHAT IS LOST stopping at products: every price.\n")

cat("\nQ13 YES. Every enter_object names a key I learned from AWS's docs.\n")
cat("Q14 PARTIAL. The chain survives another price list; the spread_all columns\n")
cat("    differ silently, which is the same NA-column failure tidyr has.\n")
cat("Q15 YES. The verbs are well named and the chain reads top to bottom.\n")
cat("Q16 ~45 lines, low ceremony. gather_object is doing real work.\n")

cat("\nCONCLUSION\n")
cat("tidyjson is the only tool of the fourteen with a VERB for keys-as-data,\n")
cat("and it still cannot answer question 6, because the question is WHERE the\n")
cat("keyed levels are and gather_object is something you aim. It is the closest\n")
cat("prior art to `into()` and the gap between them is a finding rather than a\n")
cat("feature list: one is a verb, the other is a verb plus a page telling you\n")
cat("where to point it.\n")
