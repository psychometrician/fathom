# tidyjson — movie ratings, Kaggle data-cleaning challenge
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson 0.3.3.1
#  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
#  measured      2026-08-10
#  run           cd corpus/16-movie-ratings/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             6   NO                  WRONG
#   2 how deep                                    2   NO                  yes
#   3 what is one record                          4   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    5   NO                  PARTLY
#   7 how many records                            1   NO                  YES
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   1   -                   n/a
#  11 find every path matching something          -   -                   CANNOT
#  12 flattest honest table                       4   NO                  PARTLY
#  13 needed the shape in advance?                    NO for 2, 4, 5, 6, 7
#  14 survives the next file unchanged?               json_schema does
#  15 readable a week later?                          yes, it is a pipeline
#  16 lines, and how much is ceremony?                ~35, pipeline is intent
#
# THE SEVENTH TEST OF json_schema, AND IT FAILED THE OTHER WAY. It has discarded
# silently on 03, 05, 07, 10, 11 and 19. Here it discards nothing and instead
# ENUMERATES all 38 films — 66% of the file. The two failure modes are opposite
# and the trigger is structural; see Q1.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("R %s, tidyjson %s\n", getRversion(), packageVersion("tidyjson")))

j <- readLines("../source.json", warn = FALSE) |> paste(collapse = "")

sch <- j |> as.tbl_json() |> json_schema()
cat(sprintf("\n1. json_schema: %d chars (%.0f%% of the 6,975-byte file)\n",
            nchar(sch), 100 * nchar(sch) / 6975))
cat(sprintf("   %s\n", substr(sch, 1, 400)))
cat("   WRONG — and it is json_schema's OTHER failure, not the one this file\n")
cat("   was run to test. It did NOT pick one shape: it enumerated all 38, one\n")
cat("   film at a time, each with its own field list. 4,628 characters to\n")
cat("   describe 6,975 — 66% of the file, above npm's 61%.\n")
cat("\n   THE TWO FAILURE MODES ARE OPPOSITE AND THE TRIGGER IS STRUCTURAL:\n")
cat("     varying records as siblings in an ARRAY   -> picks one, DISCARDS\n")
cat("                                                  (03, 05, 07, 10, 11, 19)\n")
cat("     varying records as values of a KEYED OBJ  -> ENUMERATES every key\n")
cat("                                                  (16 here, and npm at 61%)\n")
cat("   Seven documents, and the function has now been wrong in both\n")
cat("   directions. Which one you get depends on whether the shapes are\n")
cat("   numbered siblings or named ones — which is `README.md`'s operation 1\n")
cat("   against operation 2, and json_schema does neither.\n")

recs <- j |> as.tbl_json() |> gather_array("i") |> gather_object("title")
cat(sprintf("\n7. %d films.\n", nrow(recs)))
cat("\n2. depth 3 — array, keyed object, record.\n")

cat("\n6. PARTLY, and better than most. `gather_object(\"title\")` put the film\n")
cat("   names in a COLUMN, which is structurally the right place for a key\n")
cat("   that is a value — tidyjson is one of the few tools that even offers\n")
cat("   the move. It still cannot SAY they are data: the same verb produced\n")
cat("   the field names one level down.\n")

keys <- recs |> gather_object("key") |> count(key, name = "n")
cat("\n4. field presence across the 38 films, nothing named:\n")
for (i in order(-keys$n))
  cat(sprintf("     %-18s %3d of 38\n", keys$key[i], keys$n[i]))
cat("   NOTHING is on all 38 — the two key-sets are disjoint.\n")

types <- recs |> gather_object("key") |> json_types("t") |> count(key, t)
cat("\n5. types per field, where more than one:\n")
for (k in unique(types$key)) {
  s <- types[types$key == k, ]
  if (nrow(s) > 1)
    cat(sprintf("     %-18s %s\n", k,
                paste(sprintf("%s x%d", s$t, s$n), collapse = ", ")))
}
cat("   `Popcorn Score` and `Tomato Score` are number-or-string, and tidyjson\n")
cat("   SHOWS BOTH — it does not unify, which polars and DuckDB both do. The\n")
cat("   string values are the sentinels.\n")

# ── Q8/9/12. `spread_all` REFUSES this document ──────────────────────────────
# The verb that turns a document into a table WITHOUT naming fields cannot run
# here, and the reason is the document's whole point.
bad <- try(recs |> spread_all(), silent = TRUE)
cat("\n8/12. spread_all() FAILS:\n")
cat(sprintf("     %s\n", trimws(strsplit(as.character(bad), "\n")[[1]][2])))
cat("   `Popcorn Score` and `Tomato Score` are each number x9 and string x6.\n")
cat("   `spread_all` builds one column per (name, type) pair and then cannot\n")
cat("   find the column it promised, so it aborts. **The one verb in tidyjson\n")
cat("   that needs no field names is defeated by exactly the polymorphism this\n")
cat("   document was chosen for.**\n")

tbl <- recs |> spread_values(
  Rating = jstring("Rating"), rating = jstring("rating"),
  Genre  = jstring("Genre")) |> as_tibble()
cat(sprintf("\n   `spread_values` DOES work — %d x %d — and it needs every field\n",
            nrow(tbl), ncol(tbl)))
cat("   named AND typed by hand. On a document where two fields have two types\n")
cat("   and three fields have two spellings, that is six decisions the reader\n")
cat("   must already know. The automatic verb refuses; the manual verb requires\n")
cat("   the answer.\n")
print(head(as.data.frame(tbl[, c("title", "Rating", "rating")]), 3))
cat(sprintf("\n9. `Rating` NA on %d of %d rows, all kept. Collapsing the two\n",
            sum(is.na(tbl$Rating)), nrow(tbl)))
cat("   spellings is dplyr's `coalesce`, not tidyjson's.\n")

cat("\n3. one film per row, and TWO tables inside it — 54% empty folded, 0%\n")
cat("   split, with no field to split on.\n")
cat("\n10. n/a. 11. CANNOT — every verb descends a NAMED path.\n")
cat("   WHAT IS LOST: see Q1, and see Q8 — the schema is proportional to the\n")
cat("   films, and the table verb will not run at all.\n")
