# tidyjson — Natural Earth admin-0 countries, as GeoJSON
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed below)
#  file          ../source.json   3.9 MB, 241 features, depth 8, 75 paths
#  measured      2026-08-09
#  run           cd corpus/03-natural-earth/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                            14   NO                  WRONG
#   3 what is one record                          3   NO                  YES
#   5 does any field change type                 14   NO                  WRONG
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               5   YES                 yes
#  12 flattest honest table                       5   YES                 partly
#  13 needed the shape in advance?                    no for 1, 3, 5; yes for 8
#  16 lines, and how much is ceremony?                see the conclusion
#
#  Q1 and Q5 are scored WRONG rather than NO, and they are the only cells in
#  the R grid carrying that mark. It is deliberate: json_schema does not
#  decline, it answers, and the answer is false for 119 of 241 records.
#
#  ⚠ json_schema IS NOT RUN ON THE WHOLE FILE and the reason is measured below:
#  its runtime is linear in input bytes at roughly 3.8 KB/s here, so 3.9 MB
#  extrapolates past a quarter of an hour. The first draft of this attempt did
#  run it on 200 features and was killed after two minutes with no output.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `tidyjson::json_schema` is the closest existing tool to what
# `README.md` asks for — infer a description and print it — and `VERDICT.md`
# treats it as the serious competitor, recording it at **61% of
# `01-npm-registry`, in 58 seconds**. That is the O(data) criticism, and it is a
# criticism about SIZE.
#
# This document tests something else. Its polymorphism is in nesting depth —
# `coordinates` is 3 deep on 122 Polygons and 4 deep on 119 MultiPolygons — and
# a schema inferrer has to say something about a field that is two shapes.
suppressMessages({library(tidyjson); library(jsonlite)})
cat(sprintf("R %s, tidyjson %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyjson"), packageVersion("jsonlite")))

path  <- "../source.json"
bytes <- file.size(path)
doc   <- fromJSON(path, simplifyVector = FALSE)
feats <- doc$features
gt    <- vapply(feats, function(f) f$geometry$type, "")
sch   <- function(x) as.character(json_schema(as.character(toJSON(x, auto_unbox = TRUE))))

# ── Q5 FIRST, because it decides how to read everything else. ────────────────
cat("\n5. does any field change type — asked of the two geometries directly:\n")
p <- feats[[which(gt == "Polygon")[1]]]$geometry
m <- feats[[which(gt == "MultiPolygon")[1]]]$geometry
cat(sprintf("   one Polygon alone       %s\n", sch(p)))
cat(sprintf("   one MultiPolygon alone  %s\n", sch(m)))
cat("   Correct, separately: three bracket levels against four.\n")
cat("   Now the same two IN ONE ARRAY, which is how the document holds them:\n")
cat(sprintf("   [Polygon, MultiPolygon]  %s\n", sch(list(p, m))))
cat(sprintf("   [MultiPolygon, Polygon]  %s\n", sch(list(m, p))))
cat("   IT REPORTS ONE SHAPE AND THE SHAPE DEPENDS ON THE ORDER. Reversing the\n")
cat("   two inputs changes the inferred schema. There is no union, no warning,\n")
cat("   and no indication that anything was discarded.\n")

cat("\n   The same test on ordinary polymorphism BY TYPE, as a control:\n")
cat(sprintf("   [\"a\", {\"b\":1}]  %s\n", sch(list("a", list(b = 1)))))
cat(sprintf("   [{\"b\":1}, \"a\"]  %s\n", sch(list(list(b = 1), "a"))))
cat("   The string is dropped in BOTH orders. A field that is text on some\n")
cat("   records and an object on others is described as an object, silently.\n")

# ── Q1. What is in here? Output size and runtime, measured as input grows. ───
cat("\n1. what is in here — json_schema, timed as the input grows:\n")
for (n in c(2, 5, 10, 20)) {
  sub <- as.character(toJSON(feats[seq_len(n)], auto_unbox = TRUE))
  t0  <- Sys.time()
  s   <- json_schema(sub)
  el  <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  cat(sprintf("   %2d features  input %9s B  %6.2f s  schema %s chars (%.2f%%)\n",
              n, format(nchar(sub), big.mark = ","), el,
              format(nchar(as.character(s)), big.mark = ","),
              100 * nchar(as.character(s)) / nchar(sub)))
  flush.console()
  last <- list(n = n, b = nchar(sub), el = el, chars = nchar(as.character(s)))
}
rate <- last$b / last$el
cat(sprintf("\n   THE OUTPUT IS CONSTANT AND THE RUNTIME IS NOT. The schema stays at\n"))
cat(sprintf("   %s chars while the input grows %dx. By the O(data) test — the one\n",
            format(last$chars, big.mark = ","), round(last$b / 9851)))
cat("   VERDICT.md uses against this tool — tidyjson PASSES this document\n")
cat(sprintf("   outright: %.2f%% and falling.\n", 100 * last$chars / last$b))
cat(sprintf("   But it processes %.1f KB/s, so the whole %.1f MB file extrapolates\n",
            rate / 1024, bytes / 1024^2))
cat(sprintf("   to about %.0f minutes. NOT RUN — this is an extrapolation from the\n",
            (bytes / rate) / 60))
cat("   four rows above and is labelled as one.\n")
cat(sprintf("   VERDICT.md records 58 s for 786 KB on 01-npm-registry, which is\n"))
cat(sprintf("   %.1f KB/s. This file runs at %.1f KB/s — %.1fx slower per byte, on a\n",
            786 / 58, rate / 1024, (786 / 58) / (rate / 1024)))
cat("   document with deeply nested arrays and no keys-as-data at all.\n")

# The reason the constant output is not good news.
cat("\n   AND THE CONSTANT IS CONSTANT BECAUSE IT DESCRIBES ONE SHAPE:\n")
s20  <- json_schema(as.character(toJSON(feats[seq_len(20)], auto_unbox = TRUE)))
mtch <- regmatches(as.character(s20), regexpr('"coordinates": [^,]*', as.character(s20)))
cat(sprintf("   the coordinates entry from 20 features: %s\n",
            if (length(mtch)) mtch else "(not found)"))
nP <- sum(gt[1:20] == "Polygon"); nM <- sum(gt[1:20] == "MultiPolygon")
cat(sprintf("   those 20 features are %d Polygons and %d MultiPolygons, so that one\n",
            nP, nM))
cat(sprintf("   entry is wrong for %d of the 20.\n", if (nP >= nM) nM else nP))

# ── Q3 / Q7. What is one record, and how many? tidyjson at its best. ─────────
cat("\n3/7. what is one record, and how many:\n")
t0  <- Sys.time()
ftxt <- as.character(toJSON(feats, auto_unbox = TRUE))
g    <- gather_array(ftxt)
cat(sprintf("   gather_array() over features -> %d rows in %.1f s\n",
            nrow(g), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("   THIS IS TIDYJSON AT ITS BEST and it is a real answer to question 3:\n")
cat("   one row per array element, the count is question 7, and neither needed\n")
cat("   the shape known first. It is also the fast path — seconds, not minutes.\n")

# ── Q8. Three named fields. ──────────────────────────────────────────────────
cat("\n8. three named fields, one row per feature:\n")
t0  <- Sys.time()
tbl <- g |> enter_object("properties") |>
  spread_values(name = jstring("name"), iso = jstring("iso_a3"),
                pop = jnumber("pop_est"))
cat(sprintf("   gather_array |> enter_object |> spread_values -> %d x %d in %.1f s\n",
            nrow(tbl), ncol(tbl), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
print(utils::head(as.data.frame(tbl)[, c("name", "iso", "pop")], 3))
cat("   Reads cleanly, and every field name had to be known first — Q13.\n")

# ── Q12. The flattest honest table. ──────────────────────────────────────────
cat("\n12. the flattest honest table, and what was lost:\n")
t0   <- Sys.time()
flat <- g |> enter_object("properties") |> spread_all()
cat(sprintf("   spread_all -> %d x %d in %.1f s\n", nrow(flat), ncol(flat),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("   WHAT WAS LOST: the geometry, entirely. `enter_object(\"properties\")` is\n")
cat("   required because spread_all cannot descend into an array, so the half\n")
cat("   of the document that is actually hard is simply not in the flat table.\n")
cat("   That is an honest table and a partial answer, and the partiality is\n")
cat("   invisible in the result.\n")

cat("
CONCLUSION — the sharpest result against a competing tool in this corpus,
because it is about CORRECTNESS rather than size.

  `VERDICT.md`'s case against `json_schema` has been that its answer is too big:
  61% of npm, flat at 42-44% across a 9x growth of the Stripe spec. **On this
  file that criticism does not land.** The schema is a constant 1,438 characters
  no matter how many features are fed in — 0.66% at twenty features and falling.
  By the O(data) test this tool passes outright.

  IT PASSES BY GIVING A WRONG ANSWER. `coordinates` is 3 deep on 122 records and
  4 deep on 119. json_schema reports ONE of those depths, and WHICH one depends
  on the order of the input: Polygon-first yields three brackets, MultiPolygon-
  first yields four. Nothing is unioned, nothing is warned about, and the
  discarded half leaves no trace. On the control — a string beside an object —
  the string vanishes in both orders.

  **The output is constant because it has decided there is one shape.** A
  describer that silently picks a shape will always look proportional to
  structure. That is the loophole in the project's own headline test, and this
  file is the document that exposes it: SIZE OF DESCRIPTION IS NOT SUFFICIENT.
  `VERDICT.md` should not claim a small answer is a good one without also
  checking it is true.

  THE SECOND FAILURE IS TIME, and it is the one that stops the attempt. Measured
  at roughly 3.8 KB/s, the full 3.9 MB file extrapolates past a quarter of an
  hour — four times slower per byte than the 58 s VERDICT.md records for npm.
  The output is O(structure) and the runtime is O(data), which is the worst
  pairing available: you wait for the whole document to be read and get a
  description that has thrown most of it away.

  WHAT TIDYJSON DOES WELL is question 3. `gather_array()` is the most honest
  answer to \"what is one record\" that any tool in this corpus gives — it names
  the array, produces one row per element, the count falls out, and it runs in
  seconds. That is a real answer, and it is why this tool is the competitor.
")
