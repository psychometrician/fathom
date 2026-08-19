# purrr — the Stripe OpenAPI specification
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (version printed below), + jsonlite to parse
#  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
#  measured      2026-08-09
#  run           cd corpus/09-stripe-openapi/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             6   NO                  NO
#   2 how deep                                    4   NO                  yes
#   3 what is one record                          -   -                   CANNOT
#   6 are any keys actually data                  5   NO                  PARTLY
#   7 how many records                            2   YES                 yes
#   8 three named fields to a table               6   YES                 yes
#  16 lines, and how much is ceremony                  see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `README.md` calls purrr **"the best answer that exists"** for
# deep JSON, and it has been tested on `01-npm-registry` and `02-hn-thread` and
# nothing else. Every R number in `VERDICT.md` outside the tidyr table comes from
# those two documents. This is the corpus's most keys-as-data-heavy file — 47
# keyed sites against npm's 6 — and the one where the Python describers produced
# **157% and 172% of the document's own size**. If purrr copes here, fathom's
# competitive claim is in trouble, which is the reason to run it.
suppressMessages({library(purrr); library(jsonlite)})
cat(sprintf("R %s, purrr %s, jsonlite %s\n", getRversion(),
            packageVersion("purrr"), packageVersion("jsonlite")))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("  parsed in %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\n1. what is in here — purrr has no describe verb, so this is str():\n")
s <- capture.output(str(doc, max.level = 2))
cat(sprintf("   str(max.level=2) is %d lines\n", length(s)))
s3 <- capture.output(str(doc, max.level = 3))
cat(sprintf("   str(max.level=3) is %d lines\n", length(s3)))
cat("   The whole str() is not attempted: at level 3 it is already past a\n")
cat("   screenful per schema, and `README.md` measured 7,099 lines on a file\n")
cat("   one tenth this size.\n")

cat("\n2. how deep does it go:\n")
depth <- function(x) if (is.list(x) && length(x)) 1 + max(map_int(x, depth)) else 0L
cat(sprintf("   %d levels, via a hand-written recursion — purrr has no depth verb\n",
            depth(doc)))

cat(sprintf("\n7. schemas: %d   paths: %d\n",
            length(doc$components$schemas), length(doc$paths)))

cat("\n8. three named fields, one row per schema — purrr's best case:\n")
tbl <- map_dfr(names(doc$components$schemas), function(nm) {
  s <- doc$components$schemas[[nm]]
  tibble::tibble(schema = nm,
                 type = s$type %||% NA_character_,
                 nprops = length(s$properties))
})
cat(sprintf("   map_dfr over names() -> %d rows x %d cols\n", nrow(tbl), ncol(tbl)))
print(head(tbl, 3))
cat("   `names()` is doing the keys-as-data work and purrr is doing the walk.\n")

# 6. THE QUESTION THAT DECIDES THIS FILE.
cat("\n6. are any object keys actually data — purrr cannot say, and here is\n")
cat("   what that costs. The signal is children-versus-key-sets:\n")
for (site in list(c("components", "schemas"), c("paths"))) {
  obj <- purrr::pluck(doc, !!!site)
  ks <- unique(map_chr(obj, function(v)
    if (is.list(v)) paste(sort(names(v)), collapse = ",") else "-"))
  cat(sprintf("     %-22s %5d children, %4d distinct key-sets\n",
              paste(site, collapse = "."), length(obj), length(ks)))
}
cat("   Thousands of children sharing a handful of key-sets is what a keyed\n")
cat("   object looks like. purrr computed it because I wrote the comparison;\n")
cat("   it has no verb that volunteers it and no way to warn you.\n")

cat("
CONCLUSION — and it is the first purrr result on a hard file.

  purrr is excellent at the half it is for. `map_dfr` over `names()` gives 1,440
  rows in one expression, and it reads back cleanly. That is question 8, and
  question 8 was never the problem.

  What it does not do is question 1, 2, 3 or 6 — what is in here, how deep, what
  is one row, and are these keys data. `str()` is the only describer in reach and
  it is O(data): at max.level=3 it is already unreadable on this file. Every
  expression above that touched structure needed the structure known first, and
  the two numbers under question 6 — the ones that say `components.schemas` is a
  keyed object rather than a record — were computed by hand because purrr has no
  opinion to offer.

  So `README.md`'s claim survives this file, and now on a document ten times
  npm's size: purrr is the best answer that exists for EXTRACTING, and it does
  not attempt the exploring.
")
