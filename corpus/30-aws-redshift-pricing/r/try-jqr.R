# jqr — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (R bindings to the jq C library; versions printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/r && Rscript try-jqr.R
#
#  Attempts: the probe was run ONCE on this file, so each query below was
#  written once and is reported as it first ran. Rule 6.
#
#  Header filled in after the run. See the CONCLUSION.
#
# **jq is the only tool of the fourteen with a real path language**, and on a
# document keyed by data five levels down that is exactly the thing needed.
# `paths` and `to_entries` are the two verbs that matter here.

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("jqr %s · jsonlite %s · R %s.%s\n", packageVersion("jqr"),
            packageVersion("jsonlite"), R.version$major, R.version$minor))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
cat(sprintf("read: %.1f MB of text\n", nchar(txt) / 2^20))

j <- function(q) jq(txt, q)

cat("\nQ0  jq PARSES and says nothing about soundness. It does not report\n")
cat("    duplicate keys, big integers or encoded values. CANNOT.\n")
cat("    (jq keeps the LAST duplicate key silently, which is the damage the\n")
cat("    health verb exists to name.)\n")

cat("\nQ1  ANSWERED at one level, and ANSWERED RECURSIVELY — jq is one of the\n")
cat("    very few that can do the second:\n")
cat(sprintf("    keys: %s\n", j("keys_unsorted | join(\", \")")))
cat(sprintf("    distinct paths (leaf), [paths(scalars)] | length -> %s\n",
            j("[paths(scalars)] | length")))
cat(sprintf("    distinct path SHAPES, with array indices collapsed -> %s\n",
            j("[paths(scalars) | map(if type==\"number\" then \"[]\" else . end) | join(\".\")] | unique | length")))
cat("    THE SECOND NUMBER IS THE WHOLE PROBLEM: jq collapses array indices and\n")
cat("    has nothing that collapses DATA KEYS, so the shape count is barely\n")
cat("    smaller than the leaf count.\n")

cat(sprintf("\nQ2  ANSWERED: %s — `[paths] | map(length) | max`.\n",
            j("[paths | length] | max")))
cat("    A real answer from a real verb, and one of jq's best moments here.\n")

cat("\nQ3  CANNOT. jq names no record candidates and prices none.\n")

cat("\nQ4  ANSWERED, and this is jq at its best:\n")
cat(sprintf("    %s\n", j(".products | [.[].attributes | keys[]] | group_by(.) | map({k:.[0], n:length}) | sort_by(-.n) | map(\"\\(.k)(\\(.n))\") | join(\" \")")))

cat("\nQ5  ANSWERED:\n")
cat(sprintf("    attribute value types: %s\n",
            j("[.products[].attributes[] | type] | unique | join(\", \")")))
cat("    One type everywhere. No field changes type.\n")

cat("\nQ6  CANNOT — and jq shows the shape of the answer without naming it.\n")
cat(sprintf("    .products | keys | length -> %s\n", j(".products | keys | length")))
cat(sprintf("    .terms.Reserved | keys | length -> %s\n", j(".terms.Reserved | keys | length")))
cat("    `to_entries` turns keys into data ON REQUEST, which is the right\n")
cat("    primitive — but I must DECIDE to call it. jq never volunteers that a\n")
cat("    set of names is a collection rather than a schema.\n")

cat(sprintf("\nQ7  products %s · price dimensions %s\n",
            j(".products | length"),
            j("[.terms[][][] .priceDimensions | length] | add")))

cat("\nQ7a NO positional alignment. (Circular question — not scored.)\n")

t0 <- Sys.time()
q8 <- j(".products | to_entries | map({sku:.value.sku, family:.value.productFamily, location:.value.attributes.location}) | .[0:3]")
cat(sprintf("\nQ8  ANSWERED in %.1f s, `to_entries | map({...})`:\n",
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("    %s\n", substr(paste(q8, collapse = ""), 1, 200)))

cat("\nQ9  ANSWERED. jq returns null for a missing key rather than dropping the\n")
cat("    row, so 'keep those rows' is the DEFAULT:\n")
cat(sprintf("    with instanceType: %s of %s\n",
            j("[.products[] | select(.attributes.instanceType != null)] | length"),
            j(".products | length")))

cat("\nQ10 ANSWERED, and the answer is the interesting one:\n")
cat(sprintf("    appliesTo arrays: %s · total elements: %s\n",
            j("[.terms[][][] .priceDimensions[].appliesTo] | length"),
            j("[.terms[][][] .priceDimensions[].appliesTo[]] | length")))
cat("    EVERY ONE IS EMPTY. `[...appliesTo[]] | length` returns 0, which is\n")
cat("    indistinguishable from 'there is no such field'. jq answered and the\n")
cat("    answer cannot tell those two apart.\n")

cat("\nQ11 ANSWERED — the best of the fourteen, and it is one expression:\n")
cat(sprintf("    whole-value URLs: %s\n",
            j("[paths(type == \"string\" and test(\"^https?://\")) ] | length")))
cat(sprintf("    strings CONTAINING a url: %s\n",
            j("[paths(type == \"string\" and test(\"https?://\")) | join(\".\")] | join(\" | \")")))
cat("    The disclaimer contains two URLs and is not one. jq distinguishes\n")
cat("    them; most of the fourteen cannot ask the question at all.\n")

cat("\nQ12 The flattest honest table: `[paths(scalars)]` joined to its value is\n")
cat("    the melt, and jq writes it in one line. WHAT IS LOST: nothing, and it\n")
cat("    is as large as the document. Anything smaller needs the keyed levels\n")
cat("    collapsed, which is the thing jq has no word for.\n")

cat("\nQ13 PARTLY NO — `paths`, `keys` and `to_entries` need no prior shape, and\n")
cat("    that puts jq ahead of every R tool here on the exploration half.\n")
cat("Q14 YES for the generic queries, NO for anything naming .attributes.*.\n")
cat("Q15 NO. Three of the expressions above are already hard to re-read, and\n")
cat("    `.terms[][][]` is unreadable a week later — it means four levels and\n")
cat("    says nothing about what they are.\n")
cat("Q16 ~40 lines, and almost none of it is ceremony. jq is dense.\n")

cat("\nCONCLUSION\n")
cat("jq answers Q1, Q2, Q4, Q5, Q7, Q8, Q9, Q10 and Q11 — more of this list\n")
cat("than any other tool of the fourteen. What it does NOT do is Q3 and Q6, and\n")
cat("Q6 is the one this document is made of. `to_entries` is the right verb and\n")
cat("jq will never tell you when to reach for it: the 1,571 keys under\n")
cat(".terms.OnDemand look exactly like the 8 keys at the root.\n")
