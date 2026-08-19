# tidyr — Home Assistant frontend, the English translation catalogue
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
#  measured      2026-08-12
#  run           cd corpus/28-home-assistant-i18n/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             5   NO                  ONE LEVEL PER CALL
#   2 how deep                                    4   NO                  only by counting calls
#   3 what is one record                          6   NO                  CANNOT — see below
#   4 always present vs sometimes                 5   NO                  yes, after unnesting a level
#   5 does any field change type                  5   NO                  YES — unnest_longer shows it
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            3   NO                  yes, per level
#   8 three named fields to a table               4  YES                  yes — hoist
#   9 a field missing from some rows              4  YES                  YES — hoist gives NULL
#  10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       8   NO                  PARTLY — eleven calls
#  13 needed the shape in advance?                    NO for 1 per level, 4, 5
#  14 survives the next file unchanged?               NO — the call depth is the shape
#  15 readable a week later?                          YES, line by line
#  16 lines, and how much is ceremony?                ~90
#
# **tidyr is the closest prior art fathom has and this is its worst document.**
# Its rectangling verbs take ONE LEVEL PER CALL, and this file is eleven levels
# of objects with no arrays at all. Reaching the honest table means eleven
# `unnest_longer` calls written by someone who already counted the levels.
#
# **`unnest_longer` on an object gives one row per KEY, which is the right move
# here** — and it is the same verb, repeated, with nothing to tell you when to
# stop.

suppressMessages({library(jsonlite); library(tidyr); library(dplyr); library(tibble)})
cat(sprintf("jsonlite %s · tidyr %s · dplyr %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("tidyr"),
            packageVersion("dplyr"), R.version$major, R.version$minor))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

# ── Q1. One level per call. ──────────────────────────────────────────────────
one <- tibble(x = list(doc)) |> unnest_wider(x)
cat(sprintf("\nQ1  unnest_wider once -> %d x %d: %s\n",
            nrow(one), ncol(one), paste(names(one), collapse = ", ")))
cat("    ONE LEVEL PER CALL. To see level two you call it again, and tidyr\n")
cat("    never tells you how many calls are left.\n")

# ── Q12/Q2. The melt, by repeated unnest_longer. ─────────────────────────────
# THE NAIVE LOOP FAILS, and the failure is the finding.
#
#   Error in col_to_long(): Can't combine `..1$v` <character> and `default$v` <list>
#
# After one pass the `v` column holds BOTH finished messages (character) and
# groups still to open (list), and `unnest_longer` refuses a column that mixes
# them. That is the same property polars' `unnest` refuses and the same one
# defects 31 and 32 turned on: a level with a leaf and a group side by side.
# 330 objects here are like that.
#
# So the leaves have to be set aside at every step, by hand.
t0 <- Sys.time()
done <- tibble()
long <- tibble(k1 = names(doc), v = unname(doc))
calls <- 1
repeat {
  leaf <- !vapply(long$v, is.list, logical(1))
  if (any(leaf)) done <- bind_rows(done, long[leaf, ])
  long <- long[!leaf, ]
  if (!nrow(long)) break
  calls <- calls + 1
  long <- tidyr::unnest_longer(long, v, indices_to = paste0("k", calls))
  # AND A THIRD PIECE OF CEREMONY. unnest_longer SIMPLIFIES the column when a
  # level happens to be all characters, so `v` stops being a list and the next
  # bind_rows refuses to combine it with the list-column collected earlier.
  # Forcing it back is not optional and nothing warns you.
  long$v <- as.list(long$v)
}
long <- done
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 2)
kcols <- grep("^k", names(long), value = TRUE)
cat(sprintf("\nQ12 %d unnest_longer calls -> %s rows x %d cols (%s keys + value)\n",
            calls, format(nrow(long), big.mark = ","), ncol(long), length(kcols)))
cat(sprintf("    %s seconds. PARTLY, and TWICE qualified: the loop is mine, AND\n", secs))
cat("    the leaves must be set aside by hand at every step because\n")
cat("    unnest_longer refuses a column holding a leaf and a group together —\n")
cat("    and THEN forced back to a list, because it silently simplifies.\n")
cat("    Written straight, it is eleven identical lines by someone who already\n")
cat("    knew there were eleven levels — which is question 13, failed.\n")

cat(sprintf("\nQ2  %d, counted from how many calls it took. yes, by exhaustion.\n",
            length(kcols)))

# ── Q3/Q7. ───────────────────────────────────────────────────────────────────
cat("\nQ3  tidyr names no candidates and prices none. Each unnest gives a count:\n")
cat(sprintf("      after 1 call    %d\n", ncol(one)))
cat(sprintf("      after %d calls  %s\n", calls, format(nrow(long), big.mark = ",")))
cat("    CANNOT — every intermediate is defensible and tidyr proposes none.\n")
cat(sprintf("\nQ7  %s messages at the bottom. yes.\n",
            format(sum(!vapply(long$v, is.list, logical(1))), big.mark = ",")))

# ── Q4/Q5. ───────────────────────────────────────────────────────────────────
depth_of <- rowSums(!is.na(long[, kcols]))
cat("\nQ4  messages by depth:\n")
print(table(depth_of))
cat("    yes, once melted — and it is the same histogram rrapply gives in one call.\n")

cat(sprintf("\nQ5  classes at the bottom: %s\n",
            paste(unique(vapply(long$v, function(z) class(z)[1], "")), collapse = ", ")))
cat("    YES in principle: unnest_longer keeps a list-column when types differ,\n")
cat("    and here they do not — every leaf is a character.\n")

cat("\nQ6  CANNOT.\n")

# ── Q8/Q9. hoist, which IS `take`. ───────────────────────────────────────────
h <- tibble(x = list(doc)) |>
  hoist(x,
        and     = list("ui", "common", "and"),
        loading = list("ui", "common", "loading"),
        missing = list("ui", "panel", "profile", "nope"))
cat(sprintf("\nQ8  hoist() -> and = %s, loading = %s\n", h$and, h$loading))
cat("    yes, and `hoist` is exactly what design/vocabulary.md proposed `take`\n")
cat("    for. It is shipped prior art and reaches several depths in one call.\n")

cat(sprintf("\nQ9  the missing one -> %s. hoist gives NULL rather than an error,\n",
            ifelse(is.null(h$missing[[1]]), "NULL", "?")))
cat("    so the row survives. YES.\n")

cat("\nQ10 zero arrays in 604 KB. NOTHING TO FLATTEN.\n")
cat("\nQ11 CANNOT. tidyr has no search over paths.\n")

cat("
CONCLUSION. tidyr is the closest prior art fathom has and this document is where
that closeness runs out. Its verbs take ONE LEVEL PER CALL, and a translation
catalogue is eleven levels of objects with no arrays anywhere — so the honest
table costs eleven identical calls, written by someone who already knew the
number. rrapply does it in one call and tidyjson in one, both without knowing.

`unnest_longer` on an OBJECT giving one row per key is the right primitive and
it is genuinely good. What is missing is any signal about when to stop calling
it, which is question 13 and question 3 at once.

`hoist` remains the shipped answer to what `take` was proposed for, and this
file is a clean demonstration: three paths at three different depths, one call,
NULL where a key is absent.

AND THE COMPARISON THAT MATTERS HERE. fathom describes this file worse than any
other in the corpus — 5.69%, 39.3% unnamed — while rrapply, tidyjson, duckdb and
jq each melt it completely. On this document four tools beat fathom, and tidyr is
not one of them.
")
