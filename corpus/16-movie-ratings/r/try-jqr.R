# jqr — movie ratings, Kaggle data-cleaning challenge
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr 1.4.0 (jq's C library through R)
#  file          ../source.json   7 KB, 38 movies, 9 fields, depth 3
#  measured      2026-08-10
#  run           cd corpus/16-movie-ratings/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             4   NO                  yes
#   2 how deep                                    1   NO                  yes
#   3 what is one record                          4   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    3   NO                  PARTLY
#   7 how many records                            1   NO                  YES
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   1   -                   n/a
#  11 find every path matching something          4   NO                  yes
#  12 flattest honest table                       5   YES                 yes
#  13 needed the shape in advance?                    NO for 1-7 and 11
#  14 survives the next file unchanged?               the describe half does
#  15 readable a week later?                          yes, short expressions
#  16 lines, and how much is ceremony?                ~35, dense not ceremonial
#
# Same language as ../python/try-jq.py through a second door, so the answers
# match exactly. They are a CONTROL, not two witnesses.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages(library(jqr))
cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

j <- paste(readLines("../source.json", warn = FALSE), collapse = "")
q  <- function(prog) jq(j, prog)
qs <- function(prog) gsub('\\\\"', "", gsub('^"|"$', "", jq(j, prog)))

cat(sprintf("\n7. %s films.\n", q('.[0]|length')))
cat(sprintf("\n2. deepest path: %s segments\n", q('[paths|length]|max')))

cat("\n6. PARTLY. the keyed object's keys, which ARE data:\n")
cat(sprintf("   %s keys, e.g. %s\n", q('.[0]|keys|length'), qs('.[0]|keys|.[0:2]|join(", ")')))
cat("   `keys` lists the film titles and jqr cannot say they are values. It is\n")
cat("   the same call that lists `Genre` one level down.\n")

cat("\n4. field presence across the 38 films, nothing named:\n")
cat(qs('[.[0]|.[]|keys[]]|group_by(.)|map({k:.[0],n:length})|sort_by(-.n)|.[]
        |"     \\(.k)  \\(.n) of 38"'), sep = "\n")
cat("   NOTHING is on all 38 — the two key-sets are disjoint.\n")

cat("\n5. fields taking more than one type:\n")
cat(qs('[.[0]|.[]|to_entries[]|{k:.key,t:(.value|type)}]|group_by(.k)
        |map({k:.[0].k,t:(map(.t)|unique)})|map(select(.t|length>1))|.[]
        |"     \\(.k)  \\(.t|tostring)"'), sep = "\n")
cat("   `Popcorn Score` and `Tomato Score` are number-or-string, and the\n")
cat("   strings are the SENTINELS. jqr does not unify, so both survive —\n")
cat("   unlike polars and DuckDB, which coerced this file's scores.\n")

cat("\n11. values matching /^unk/, by field:\n")
cat(qs('[.[0]|.[]|to_entries[]|select(.value|type=="string")
        |select(.value|test("^unk";"i"))|.key]|group_by(.)
        |map({k:.[0],n:length})|.[]|"     \\(.k)  \\(.n)"'), sep = "\n")
cat("   All 17, including the five in `Gross` that a structural detector\n")
cat("   cannot reach — because `Gross` is text on all 15 records, so nothing\n")
cat("   about its TYPE is unusual. jqr found them because I supplied `^unk`,\n")
cat("   which is a word list, and this project refuses word lists.\n")

cat("\n8/12. `.Rating // .rating` is jq's first-present operator:\n")
cat(qs('[.[0]|to_entries[]|{title:.key,rating:(.value.Rating // .value.rating)}]
        |.[0:3]|.[]|"     \\(.title)  |  \\(.rating)"'), sep = "\n")
cat(sprintf("   fills %s of 38 in one expression, with both spellings typed by\n",
            q('[.[0]|to_entries[]|(.value.Rating // .value.rating)]|map(select(.!=null))|length')))
cat("   hand. That is the SAME WORD as glom's Coalesce, jmespath's `||`, R's\n")
cat("   `%||%` and design/first_present.py — five spellings, one idea, and\n")
cat("   `QUESTIONS.md`'s stopping rule says a word earns its place only if\n")
cat("   removing it makes a question unanswerable. **It does not: four other\n")
cat("   tools already have it.** What none of them has is a way to KNOW that\n")
cat("   `Rating` and `rating` are the pair to hand it.\n")

cat(sprintf("\n9. `Rating` null on %s of 38, all kept.\n",
            q('[.[0]|.[]|.Rating]|map(select(.==null))|length')))
cat("\n3. one film per row, and TWO tables inside it — 54% empty folded, 0%\n")
cat("   split, and no field to split on: the groups share no key, so the\n")
cat("   discriminator is the naming convention itself.\n")
cat("\n1. see Q4/Q5 — the folded path listing is dominated by the film titles.\n")
cat("\n10. n/a. WHAT IS LOST: nothing jqr touched.\n")
