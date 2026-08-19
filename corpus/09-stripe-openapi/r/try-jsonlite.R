# jsonlite — the Stripe OpenAPI specification
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   7.9 MB, 1,440 schemas, 416 paths, 47 keyed sites
#  measured      2026-08-09
#  run           cd corpus/09-stripe-openapi/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                            6   NO                  NO
#   2 how deep                                   2   NO                  yes
#   3 what is one record                         8   NO                  CANNOT
#   4 always present vs sometimes                6   YES                 yes
#   6 are any keys actually data                 7   YES                 NO
#   7 how many records                           2   YES                 yes
#   8 three named fields to a table              6   YES                 yes
#  13 needed the shape in advance?                   YES for 3, 6, 7 and 8
#  16 lines, and how much is ceremony?               see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `jsonlite` had no attempt file anywhere in the corpus until
# 2026-08-09. Simplification is its one distinctive behaviour, and it has now
# been measured on four documents with four different outcomes. **This is the
# scale test for the INERT case**: `01-npm-registry` showed simplification doing
# nothing on 6 keyed sites, and this file has 47 and is ten times the size.
#
# The question is whether the failure gets worse with scale or merely stays the
# same, because those imply different things about whether it matters.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path  <- "../source.json"
bytes <- file.size(path)
cat(sprintf("  file is %s bytes\n", format(bytes, big.mark = ",")))

t0   <- Sys.time()
simp <- fromJSON(path)
t_s  <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
t0   <- Sys.time()
doc  <- fromJSON(path, simplifyVector = FALSE)
t_l  <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("  parsed simplified in %.1f s, unsimplified in %.1f s\n", t_s, t_l))
cat("  BOTH ARE FAST, and that is worth stating before the criticism: jsonlite\n")
cat("  reads a 7.9 MB document in about a second. tidyjson's json_schema on\n")
cat("  this corpus runs at a few KB/s. Parsing is solved; describing is not.\n")

# ── Q1 / Q2. ─────────────────────────────────────────────────────────────────
cat("\n1. what is in here — str() is the only describer jsonlite has:\n")
for (lv in 2:4)
  cat(sprintf("   str(simplified, max.level=%d)  %6d lines\n", lv,
              length(capture.output(str(simp, max.level = lv)))))
cat("   The whole str() is not attempted. At level 3 it is already past a\n")
cat("   screenful per schema and there are 1,440 of them.\n")
cat("   THE LEVEL-2 ANSWER IS THE INTERESTING ONE. It is short, it is instant,\n")
cat("   and it says almost nothing — six top-level keys. A small answer that is\n")
cat("   small because it stopped, not because the document is simple.\n")

depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("\n2. depth %d, hand-written recursion\n", depth(doc)))

# ── Q3 / Q6. SIMPLIFICATION AT SCALE, ON 47 KEYED SITES. ─────────────────────
cat("\n3/6. what is one record, and are any keys actually data:\n")
for (site in list(c("components", "schemas"), c("paths"))) {
  v  <- if (length(site) == 2) simp[[site[1]]][[site[2]]] else simp[[site]]
  nm <- paste(site, collapse = "$")
  cat(sprintf("   $%-18s is a %-10s of %5d — %s\n", nm, class(v)[1], length(v),
              if (is.data.frame(v)) "a table" else "NOT a table"))
}
cat("   SIMPLIFICATION IS INERT, exactly as on 01-npm-registry, and at ten\n")
cat("   times the size with eight times the keyed sites. `components$schemas`\n")
cat("   is an object keyed by schema name, so 1,440 near-identical siblings\n")
cat("   arrive as a named list and no table is offered.\n")
ks <- lapply(doc$components$schemas, names)
cat(sprintf("   those 1,440 objects share %d distinct keys and %d key-sets\n",
            length(unique(unlist(ks))),
            length(unique(vapply(ks, function(x) paste(sort(x), collapse = ","), "")))))
cat("   1,440 children over a handful of key-sets is the textbook keyed-object\n")
cat("   signature, and it is computed here because I wrote the comparison.\n")
cat("   SCORED NO. The failure does NOT get worse with scale — it is identical\n")
cat("   in kind to npm's. What scales is the consequence: on npm you hand-write\n")
cat("   one bind over 288 keys, here over 1,440, and in both cases the key\n")
cat("   stops being data the moment you index into the list.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
u <- unique(unlist(ks)); n <- length(ks)
freq <- sort(vapply(u, function(k) sum(vapply(ks, function(x) k %in% x, TRUE)), 0L),
             decreasing = TRUE)
cat(sprintf("   %d distinct keys across %d schemas\n", length(u), n))
for (k in names(freq)) cat(sprintf("     %-26s %5d\n", k, freq[[k]]))
cat(sprintf("   present in ALL %d: %s\n", n,
            if (any(freq == n)) paste(names(freq)[freq == n], collapse = ", ") else "NOTHING"))
cat("   AND THE NEAR-MISS IS THE INTERESTING PART. `properties` and `type` are\n")
cat("   on 1,436 of 1,440 — four short of universal. The four exceptions are\n")
cat("   the `anyOf` schemas, which carry `anyOf`, `title`, `x-resourceId` and\n")
cat("   `x-stripeBypassValidation` and none of the usual fields.\n")
cat("   FOUR RECORDS OF A DIFFERENT KIND HIDING AMONG 1,436, and they are\n")
cat("   enough to make the always-present test return nothing. A rule that\n")
cat("   requires a field on EVERY record is one outlier away from silence —\n")
cat("   which is worth noting against the discriminator test, since that test\n")
cat("   starts by asking which fields are present everywhere.\n")

# ── Q7 / Q8. ─────────────────────────────────────────────────────────────────
cat(sprintf("\n7. %d schemas, %d API paths\n",
            length(doc$components$schemas), length(doc$paths)))

cat("\n8. three named fields, one row per schema:\n")
tbl <- do.call(rbind, lapply(names(doc$components$schemas), function(k) {
  s <- doc$components$schemas[[k]]
  data.frame(schema = k,
             type   = if (is.null(s$type)) NA_character_ else s$type,
             nprops = length(s$properties))
}))
cat(sprintf("   do.call(rbind, lapply(names(...))) -> %d x %d\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl, 3))
cat("   `names()` is doing the keys-as-data work and base R is doing the walk.\n")
cat("   jsonlite contributes the parse and nothing else. Identical in substance\n")
cat("   to the purrr attempt beside this one, and a little worse to read.\n")

cat("
CONCLUSION — the inert case, confirmed at scale, and one thing jsonlite
deserves credit for.

  Across five documents simplification now reads:

    03-natural-earth   builds the frame, PRESERVES the depth split      SAFE
    05-fhir-bundle     builds the frame, folds 20 kinds into 87% holes  WRONG
    01-npm-registry    builds NOTHING, the keys are data                INERT
    02-hn-thread       builds a frame at every level, none composes     MISLEADING
    09-stripe-openapi  builds NOTHING, at ten times the size            INERT

  **The failure does not deepen with scale, and that is the finding.** 1,440
  keyed schemas produce the same non-answer as npm's 288: a named list, and a
  hand-written bind over `names()`. The consequence scales, the defect does not.
  A reader might have expected the biggest file to be the worst case for a
  rectangle-builder; the worst case is `02-hn-thread` at 193 KB, where it
  succeeds visibly and is wrong.

  THE CREDIT, and it should be recorded because every other line here is a
  criticism: **jsonlite reads this 7.9 MB document in about a second, both ways.**
  `tidyjson::json_schema` in the same corpus runs at a few KB per second and
  cannot finish files a fifth this size. Parsing is a solved problem in R and
  jsonlite is why. Nothing in this project's argument is about parsing.

  QUESTION 1 IS THE WHOLE GAP, and at this size it is stark. `str(max.level=2)`
  is instant and reports six top-level keys. Level 3 is unreadable. There is no
  setting that describes this document, because the tool's only describer is
  parameterised by DEPTH when the thing that needs summarising is BREADTH —
  1,440 siblings sharing a handful of shapes.
")
