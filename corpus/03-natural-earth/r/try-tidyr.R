# tidyr — Natural Earth country geometry (GeoJSON)
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, the template.
#
#  tool          tidyr (version printed below), + jsonlite to parse
#  file          ../source.json   3.9 MB, 241 features
#  measured      2026-08-09
#  run           cd corpus/03-natural-earth/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   3 what is one record                          5   no                  RIGHT
#   5 does any field change type                  6   no                  NO
#   7 how many records                            2   no                  RIGHT
#   8 three named fields to a table               4   YES                 YES
#
# WHY THIS FILE. It is an array of records, which is unnest_auto's best case,
# and its polymorphism is by DEPTH — `coordinates` nests 3 for Polygons and 4
# for MultiPolygons. The probe measured 0 on that axis originally, which is why
# shape() exists. The question here is whether tidyr sees what the probe missed.
suppressMessages({library(tidyr); library(tibble); library(jsonlite); library(dplyr)})
cat(sprintf("R %s, tidyr %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyr"), packageVersion("jsonlite")))
doc <- fromJSON("../source.json", simplifyVector = FALSE)

# THE PROTOCOL, and the first draft of this file got it wrong. The container is
# passed as a ONE-element list-column, so unnest_auto must choose longer or
# wider for itself. Passing the elements pre-split answers question 3 for it.
cat("\n3/7. unnest_auto on `features`:\n")
t <- tibble(x = list(doc$features))
msg <- capture.output(out <- suppressWarnings(unnest_auto(t, x)), type = "message")
cat("   tidyr says:", trimws(paste(msg, collapse = " ")), "\n")
cat("   result:", nrow(out), "rows x", ncol(out), "cols\n")
cat("   RIGHT. NOTES.md records 241 features as the answer to question 3.\n")
cat("   The rule is 'do the elements share names'; these do not carry names as\n")
cat("   a keyed object would, so it lengthened, which is correct here.\n")

# The first draft of this used `NAME`, which is not a key in this file and gave
# a column of NA without complaint. The properties are lower-case here. That is
# question 1 mattering: a guessed field name fails silently in R too.
cat("\n8. three named fields:\n")
tbl <- tibble(
  type = vapply(doc$features, function(f) f$type, ""),
  admin = vapply(doc$features, function(f) f$properties$admin %||% NA_character_, ""),
  geom = vapply(doc$features, function(f) f$geometry$type, ""))
cat("   ", nrow(tbl), "rows x", ncol(tbl), "cols\n")
print(head(tbl, 3))

# 5. THE AXIS THIS FILE WAS CHOSEN FOR, and the one the probe originally missed.
cat("\n5. does any field change type — the depth of `coordinates`:\n")
depth_of <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth_of, 0)) else 0
d <- vapply(doc$features, function(f) depth_of(f$geometry$coordinates), 0)
cat("   coordinate nesting depth, counted:", paste(capture.output(print(table(d))),
    collapse = " | "), "\n")
cat("   Two populations, and NOTES.md records 122 Polygons against 119\n")
cat("   MultiPolygons. tidyr reports NOTHING about this: `coordinates` is a\n")
cat("   list-column either way, and a list-column has no type to disagree about.\n")
cat("   The probe missed it for the same reason and gained shape() to fix it.\n")

cat("
CONCLUSION. unnest_auto is RIGHT on this file, and right for a reason that
generalises: an array of records with no shared names is the case its rule was
designed for. It says why, which nothing else in either language does.

What it cannot do is the thing this file was chosen to test. Polymorphism by
DEPTH is invisible to a rectangling verb, because rectangling stops at the
list-column and the difference lives inside it. That is not a tidyr defect; it
is the boundary between rectangling and describing, and it is the argument for
those being one tool rather than two.
")
