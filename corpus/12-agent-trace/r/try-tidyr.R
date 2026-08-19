# tidyr — a scrubbed Claude Code transcript, NDJSON, 1,953 records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.jsonl  4.8 MB, NDJSON, 1,953 records, depth 10,
#                                 452 paths, 151 fields, polymorphic 4
#  measured      2026-08-11
#  run           cd corpus/12-agent-trace/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   CANNOT
#   1 what is in here                             3   NO                  ONE LEVEL — 40
#   2 how deep                                    -   -                   CANNOT
#   3 what is one record                          6   NO                  ATTEMPTS IT, WRONGLY
#   4 always present vs sometimes                 6   NO                  YES — 18 of 40 rare
#   5 does any field change type                  6   NO                  YES, AND IT NAMES
#                                                                         THE TWO RECORDS
#   6 are any object keys data                    2   -                   NO, correctly
#   7 how many records                            2   NO                  yes — 1,953
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              7  YES                  yes — keep_empty
#  10 flatten the deepest array                   5  YES                  yes
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       6  YES                  1,953 x 40, 31% full
#  13 needed the shape in advance?                    NO for 1, 4, 5, 7
#  14 survives the next file unchanged?               yes, and see Q3
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~95
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS DOCUMENT DECIDES ENTRY 24's FINDING, AND IT IS THE SHARPEST CASE THERE IS.
# Entry 24 found that `unnest_auto` chooses between one row per key and one
# column per key on an INTERSECTION — any single name shared by every element
# sends it wide — where the probe uses a RATE. Entry 24's intersection was empty
# and it guessed right.
#
# HERE THE INTERSECTION IS EXACTLY ONE KEY, AND THAT KEY IS `type`. Ten record
# kinds, seventeen distinct key-sets, and the only field every record carries is
# THE DISCRIMINATOR — the field whose entire job is to say these records are not
# one kind. unnest_auto reads it as grounds for one wide table of 40 columns
# that is 31% full.
#
# THE EVIDENCE AGAINST WIDENING IS THE THING IT WIDENS ON. That is not a near
# miss; it is the rule inverting on the document type README calls the most
# likely polymorphism specimen.
#
# AND QUESTION 5 IS ANSWERED BETTER THAN BY ANY OTHER TOOL HERE. unnest_longer
# on `toolUseResult` REFUSES, and names the two records and both types:
#   Can't combine `..1$toolUseResult` <list> and `..426$toolUseResult` <character>
# Not "there is polymorphism" — WHICH TWO RECORDS, and what each one is.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

ln   <- readLines("../source.jsonl", warn = FALSE)
recs <- lapply(ln, fromJSON, simplifyVector = FALSE)

cat("\nQ0  CANNOT. tidyr never saw the bytes, and NDJSON had to be recognised\n")
cat("    by a human before `readLines` was reached for instead of `fromJSON`.\n")
cat(sprintf("    That decision is question 0 and it was made outside the tool. %d lines.\n",
            length(ln)))

# ── Q1 / Q7. ────────────────────────────────────────────────────────────────
w <- tibble(x = recs) |> unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ1  unnest_wider -> %d x %d — one level, and it is the only level\n",
            nrow(w), ncol(w)))
cat(sprintf("Q7  %d records. Q2 CANNOT: depth needs a verb per level.\n", nrow(w)))

# ── Q3 / Q6. THE CENTREPIECE. ───────────────────────────────────────────────
inter <- Reduce(intersect, map(recs, names))
ksets <- length(unique(map_chr(recs, \(r) paste(sort(names(r)), collapse = ","))))
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = recs), x)),
                    type = "message")
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d\n", nrow(a), ncol(a)))
cat(sprintf("    THE INTERSECTION IS %d KEY AND IT IS `%s`.\n", length(inter), inter))
cat(sprintf("    %d record kinds, %d distinct key-sets:\n",
            n_distinct(w$type), ksets))
byt <- w |> group_by(type) |> summarise(n = n(), filled = sum(map_lgl(pick(everything()),
         \(c) any(if (is.list(c)) lengths(c) > 0 else !is.na(c)))), .groups = "drop")
print(as.data.frame(byt))
cat("    ══ THE ONE SHARED KEY IS THE DISCRIMINATOR. ══\n")
cat("    `type` is the field that exists to say these records are NOT one kind,\n")
cat("    and it is the whole of the evidence unnest_auto widens on. Entry 24\n")
cat("    showed the rule ignores the vocabulary; this document shows it can\n")
cat("    read the strongest available evidence AGAINST widening as the reason\n")
cat("    to widen. Same rule, and here it inverts.\n")
cat("Q6  NO object keys are data here, and unnest_auto is right about that —\n")
cat("    which is why the failure above is about question 3 alone.\n")

# ── Q4 / Q12. how empty the wide answer is. ────────────────────────────────
fill <- map_dbl(w, \(c) mean(if (is.list(c)) lengths(c) > 0 else !is.na(c)))
cat(sprintf("\nQ4  of %d columns, %d are filled on under 5%% of rows\n",
            ncol(w), sum(fill < .05)))
cat(sprintf("Q12 mean fill across all columns: %.1f%%. THAT IS THE PRICE the\n",
            100 * mean(fill)))
cat("    probe would have printed as the cost of this row shape, and tidyr\n")
cat("    produces the table without ever pricing it. The number is only here\n")
cat("    because this attempt computed it afterwards.\n")

# ── Q5. THE OTHER RESULT, and it is the best of the fourteen. ──────────────
cat("\nQ5  unnest_longer(toolUseResult):\n")
e <- tryCatch(w |> unnest_longer(toolUseResult), error = \(e) conditionMessage(e))
cat(sprintf("    %s\n", trimws(gsub("\n", " ", if (is.character(e)) e else "no error"))))
cat("    IT NAMES THE TWO RECORDS AND BOTH TYPES. Every other tool in this\n")
cat("    comparison either reports a count of polymorphic fields or says\n")
cat("    nothing; this one refuses the operation and hands you the two\n")
cat("    positions to go and look at. A refusal that says where is a better\n")
cat("    answer to question 5 than a tally.\n")

# ── Q8 / Q9 / Q10. ─────────────────────────────────────────────────────────
three <- tibble(x = recs) |>
  hoist(x, type = "type", uuid = "uuid", role = c("message", "role")) |>
  select(type, uuid, role)
cat(sprintf("\nQ8  hoist() through `message` -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 3))
cat(sprintf("\nQ9  `role` present on %d of %d records — hoist keeps the rest as NA,\n",
            sum(!is.na(three$role)), nrow(three)))
cat("    which is question 9 answered by construction rather than by a flag.\n")

msg <- w |> select(type, message) |> unnest_longer(message, indices_to = "field")
cat(sprintf("\nQ10 unnest_longer(message) -> %d rows, and unnest_longer on an\n", nrow(msg)))
cat(sprintf("    OBJECT gives one row per FIELD, not per element — %d records\n", nrow(w)))
cat("    became that many because the message objects average several keys.\n")
cat("    THE SAME VERB MEANS TWO THINGS depending on whether the thing below\n")
cat("    it is an array or an object, and nothing in the call says which.\n")

cat("\nQ11 CANNOT. tidyr selects columns by name; there is no predicate on values.\n")

cat("
13. NO for 1, 4, 5 and 7 — the strongest showing of any tool on this document,
    because question 5 came back with row numbers.

14. YES for the verbs. The Q3 VERDICT would survive too, and that is the
    problem: another transcript would also share exactly `type`, so
    unnest_auto would build the same 31%-full table every time, confidently.

16. ~95 lines. The rectangling is three calls; everything else is this file
    measuring what the three calls decided.
")
