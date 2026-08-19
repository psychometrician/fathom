# tidyr — 38 films keyed by title, with three fields spelled two ways each
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   8 KB, 38 films keyed by title
#  measured      2026-08-11
#  run           cd corpus/16-movie-ratings/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  YES — 9 fields
#   2 how deep                                    -   -                   CANNOT
#   3 what is one record                         12   NO                  WRONG — see below
#   4 always present vs sometimes                 8   NO                  YES — the 15/23 split
#   5 does any field change type                  4   NO                  YES, incidentally
#   6 are any object keys data                    8   NO                  FALSE POSITIVE
#   7 how many records                            2   NO                  yes — 38 / 159
#   8 three named fields to a table               3  YES                  yes
#   9 a field missing from some rows              4  YES                  yes
#  10 flatten the deepest array                   3  YES                  shallow document
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       6  YES                  38 x 10 FOR 7 FIELDS
#  13 needed the shape in advance?                    NO for 1, 4, 5, 7
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~90
#
# THE FOURTEENTH TOOL. See ../../24-cargo-metadata/r/try-tidyr.R for why entries
# 12–25 were missing it.
#
# THIS ENTRY IS WHY `path variance by RENAMING` HAS NO INSTRUMENT. README records
# that `Rating`/`rating`, `Popcorn Score`/`popcornscore` and `Tomato
# Score`/`tomatoscore` are one field under two names each, that no axis measures
# it, and that the obvious rule — fields under one container that never co-occur
# — catches `Genre` with `popcornscore` instead, which are different fields.
#
# TIDYR MAKES THE RENAMING VISIBLE WITHOUT DETECTING IT. `unnest_wider` produces
# TEN COLUMNS FOR SEVEN FIELDS, arriving as two contiguous blocks: the six
# capitalised names filled on 15 films, the three lowercase names filled on the
# other 23. A person reading that table sees the duplication instantly. Nothing
# in tidyr knows it is duplication, AND THIS FILE DOES NOT SUPPLY THE MISSING
# INSTRUMENT — the blocks are complementary because the two SOURCES are, so
# `Genre` and `popcornscore` sit in complementary blocks too, which is README's
# rejected rule exactly. What tidyr adds is a display, not a detector.
#
# AND THE RENAMING MAKES `unnest_auto` INVENT KEYS-AS-DATA THAT ARE NOT THERE.
# It says "elements are named, but have no names in common" and melts the FIELD
# names into a column: 159 rows of `Genre`, `Rating`, `popcornscore` treated as
# values. THEY ARE NOT DATA — they are ordinary field names. The intersection is
# empty only because every field is spelled one way on 15 films and the other
# way on 23, so THE RENAMING INDUCES A FALSE POSITIVE. Meanwhile the 38 titles,
# which ARE keys-as-data, are discarded entirely: they appear nowhere in the
# output unless a person supplies them as a column first.
#
# SET THAT BESIDE ENTRY 24 AND THE PAIR IS THE WHOLE POINT. Empty intersection,
# same verb, same decision to melt — and on entry 24 the melted keys were data
# and the answer was right, and here they are not and it is wrong. ONE SIGNAL,
# TWO DOCUMENTS, OPPOSITE CORRECTNESS: the intersection carries no information
# about whether keys are data, and this document is the proof that its successes
# elsewhere are luck rather than measurement.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

films <- fromJSON("../source.json", simplifyVector = FALSE)[[1]]

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q3 / Q6. unnest_auto invents keys-as-data and loses the real ones. ─────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(x = films), x)),
                    type = "message")
inter <- Reduce(intersect, map(films, names))
cat(sprintf("\nQ3  unnest_auto -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d, columns: %s\n", nrow(a), ncol(a),
            paste(names(a), collapse = ", ")))
print(head(as.data.frame(a), 4))
cat(sprintf("    THAT IS ONE ROW PER (FILM, FIELD) PAIR, NOT PER FILM, and the\n"))
cat(sprintf("    index column holds the %d FIELD NAMES as if they were values:\n",
            n_distinct(a$x_id)))
cat(sprintf("      %s\n", paste(sort(unique(a$x_id)), collapse = ", ")))
cat(sprintf("Q6  A FALSE POSITIVE. Those are ordinary field names, not data.\n"))
cat(sprintf("    Meanwhile the %d TITLES, which really are keys-as-data, appear\n",
            length(films)))
cat(sprintf("    nowhere in the output: %s.\n",
            if (any(grepl("Strong", unlist(a)))) "they survived" else
              "no title occurs anywhere in it"))
cat(sprintf("    the intersection across all %d films is %d fields, because the\n",
            length(films), length(inter)))
cat("    renaming spells every field one way on 15 films and the other on 23.\n")
cat("    ══ ENTRY 24 GOT THE SAME SIGNAL AND THE OPPOSITE RESULT. ══\n")
cat("    There the empty intersection melted feature names that WERE data, and\n")
cat("    the answer was right. Here it melts field names that are NOT, and the\n")
cat("    answer is wrong. One rule, two documents, opposite correctness — so\n")
cat("    the intersection carries no information about whether keys are data,\n")
cat("    and entry 24's success was luck rather than measurement.\n")

# ── Q1 / Q4. the ten columns for seven fields. ─────────────────────────────
w <- tibble(title = names(films), x = unname(films)) |>
  unnest_wider(x, names_repair = "unique_quiet")
cat(sprintf("\nQ1  unnest_wider -> %d x %d\n", nrow(w), ncol(w)))
cat("Q4  column, how many films carry it, and its class:\n")
for (cn in setdiff(names(w), "title"))
  cat(sprintf("      %-16s %2d of %d   %s\n", cn,
              sum(if (is.list(w[[cn]])) lengths(w[[cn]]) > 0 else !is.na(w[[cn]])),
              nrow(w), class(w[[cn]])[1]))
cat("    TWO CONTIGUOUS BLOCKS, 15 AND 23, AND 15 + 23 IS 38. The columns\n")
cat("    arrive grouped by spelling because unnest_wider orders them by first\n")
cat("    appearance, so the duplication is laid out for a human to see.\n")
cat("    ══ AND THAT IS A DISPLAY, NOT A DETECTOR. ══\n")
cat("    `Genre` and `popcornscore` are in complementary blocks too and are\n")
cat("    NOT the same field. Complementarity is a property of the two SOURCES,\n")
cat("    which is exactly why README rejected the never-co-occur rule. tidyr\n")
cat("    does not measure renaming; it just puts the evidence side by side.\n")

# ── Q5. type variation, arriving as a side effect. ────────────────────────
cat("\nQ5  the two spellings of one field DISAGREE ON TYPE:\n")
for (p in list(c("Popcorn Score", "popcornscore"), c("Tomato Score", "tomatoscore"),
               c("Rating", "rating")))
  cat(sprintf("      %-16s %-10s   vs  %-14s %s\n",
              p[1], class(w[[p[1]]])[1], p[2], class(w[[p[2]]])[1]))
cat("    A list-column beside an integer column is the same logical value read\n")
cat("    two ways. Nothing asked question 5; rectangling answered it.\n")

# ── Q7 / Q10 / Q12. ───────────────────────────────────────────────────────
long <- tibble(title = names(films), x = unname(films)) |>
  unnest_longer(x, indices_to = "field", values_to = "value")
cat(sprintf("\nQ7  %d films, or %d title-field pairs.\n", nrow(w), nrow(long)))
cat("Q10 the document is two levels deep — there is no deep array to flatten,\n")
cat("    and `unnest_longer` on the films gives the melted long form instead.\n")
cat(sprintf("\nQ12 %d x %d IS THE FLATTEST HONEST TABLE, AND IT IS DISHONEST BY\n",
            nrow(w), ncol(w)))
cat("    THREE COLUMNS. Seven fields are spread over ten, every row is half\n")
cat("    empty by construction, and a mean or a sort over `rating` silently\n")
cat("    covers 23 films of 38. WHAT IS LOST is that the two blocks are one\n")
cat("    dataset — and no verb here can say so.\n")

# ── Q8 / Q9. ──────────────────────────────────────────────────────────────
three <- w |> select(title, Rating, rating)
cat(sprintf("\nQ8  three named fields -> %d x %d\n", nrow(three), ncol(three)))
print(head(as.data.frame(three), 3))
cat(sprintf("\nQ9  `Rating` is absent on %d films and `rating` on %d, and every\n",
            sum(is.na(w$Rating)), sum(is.na(w$rating))))
cat("    row is kept either way, because unnest_wider keeps rows by\n")
cat("    construction. The repair a person wants is `first_present(Rating,\n")
cat("    rating)`, which is QUESTIONS.md's one proven shared word — and\n")
cat("    tidyr's nearest offer is `coalesce`, at depth one only.\n")

cat("\nQ11 CANNOT. No predicate over values.\n")

cat("
13. NO for 1, 4, 5 and 7. Questions 3 and 6 were attempted without the shape
    and answered wrongly, which is a different cell from `cannot` and has to
    be scored as one.

14. THE VERB SURVIVES AND THE VERDICT SURVIVES BEING WRONG. Another scrape
    joining the same two sources would again have an empty intersection, and
    unnest_auto would again melt the field names and again drop the titles —
    reliably, quietly, every time.

16. ~90 lines, and the rectangling is two.
")
