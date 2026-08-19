# tidyr — crates.io front-page summary
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   41 KB, 8 top-level keys, 140 paths, depth 4
#  measured      2026-08-11
#  run           cd corpus/23-cratesio-summary/r && Rscript try-tidyr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             5   NO                  ONE LEVEL — 8, then 23
#   2 how deep                                    -   -                   CANNOT
#   3 what is one record                          5   NO                  ATTEMPTS IT, unhelpfully
#   4 always present vs sometimes                 6   NO                  YES, and see Q5
#   5 does any field change type                 16   NO                  YES — BY ACCIDENT
#   6 are any object keys data                    3   -                   NO, correctly
#   7 how many records                            4   NO                  yes — 10 / 40, not 33
#   8 three named fields to a table               4  YES                  yes
#   9 a field missing from some rows              5  YES                  yes — 16 of 40
#  10 flatten the deepest array                   6  YES                  NOTHING TO FLATTEN
#  11 find every path matching something          1   -                   CANNOT
#  12 flattest honest table                       7  YES                  40 x 29
#  13 needed the shape in advance?                    NO for 1, 4, 5, 7
#  14 survives the next file unchanged?               yes — no name is hard-coded
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~105
#
# THE FOURTEENTH TOOL, second of fourteen catching up. See ../../24-cargo-metadata
# /r/try-tidyr.R for why these were missing.
#
# THIS ENTRY'S FINDING IS THAT `same shape` AND `same schema` ARE DIFFERENT
# QUESTIONS. NOTES.md records four correct answers: the probe, jq, jqr, ijson,
# glom, pydash and purrr fold on KEY-SETS and say ONE SHAPE; polars, DuckDB and
# jsonlite compare VALUE TYPES and find THREE, because `recent_downloads` is null
# on all ten `new_crates` and `documentation` on all ten `just_updated`.
#
# TIDYR LANDS IN THE SECOND GROUP, AND THAT IS WORTH RECORDING BECAUSE IT IS A
# RECTANGLING TOOL RATHER THAN A TYPE-INFERRING ONE. It never asks for a schema.
# It gets one anyway, because a column has to have a type, and the four
# collections' columns then disagree in two places and in OPPOSITE DIRECTIONS.
#
# AND IT MEASURES THE THRESHOLD, WHICH NO OTHER TOOL HERE DID. `documentation` is
# null on EIGHT of ten `new_crates` and still types character; it is null on TEN
# of ten `just_updated` and types logical. NOT THE NULL RATE — TOTAL ABSENCE, and
# nothing else.
#
# THE WORST OF IT IS A THING I DID NOT PREDICT. I expected `unnest_longer` on the
# empty `versions`/`keywords`/`categories`/`badges` to drop all forty rows. It
# drops none, because those columns ARE NOT LIST-COLUMNS: total absence typed
# them logical too, so FIVE of the 23 crate fields arrive as `NA<lgl>`. `badges`
# is a real empty ARRAY in the JSON and `yanked` is a real BOOLEAN, and in the
# finished frame the two are the same type. THE ERASURE IS NOT OF THE VALUE, IT
# IS OF THE FIELD'S KIND.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({
  library(tidyr); library(tibble); library(dplyr); library(purrr); library(jsonlite)
})

cat(sprintf("R %s, tidyr %s, jsonlite %s\n",
            getRversion(), packageVersion("tidyr"), packageVersion("jsonlite")))

doc  <- fromJSON("../source.json", simplifyVector = FALSE)
FOUR <- c("new_crates", "most_downloaded", "most_recently_downloaded", "just_updated")
# Distinct short labels. The obvious `sub("_.*", "", FOUR)` prints `most` twice,
# which is exactly the kind of ambiguity this corpus keeps finding in other
# people's output.
ABBR <- c("new", "most_dl", "most_rec", "just")

cat("\nQ0  tidyr never saw the bytes; jsonlite parsed. CANNOT.\n")

# ── Q1 / Q2 / Q6. ───────────────────────────────────────────────────────────
root <- tibble(d = list(doc)) |> unnest_wider(d)
cat(sprintf("\nQ1  root unnest_wider -> %d x %d: %s\n", nrow(root), ncol(root),
            paste(names(root), collapse = ", ")))
tbls <- map(set_names(FOUR), \(k) tibble(x = doc[[k]]) |> unnest_wider(x))
cat(sprintf("Q1  each of the four collections -> %d x %d\n",
            nrow(tbls[[1]]), ncol(tbls[[1]])))
cat("Q2  CANNOT — one level per verb, and the depth is what you needed.\n")
cat("Q6  NO, correctly. The eight root keys are field names, not data, and\n")
cat("    unnest_wider on the root makes eight columns rather than eight rows.\n")

# ── Q7. the key-sets, which is the probe's answer. ──────────────────────────
ks <- map(FOUR, \(k) sort(unique(unlist(map(doc[[k]], names)))))
cat(sprintf("\nQ7  all four key-sets identical: %s, %d keys each\n",
            length(unique(map_chr(ks, paste, collapse = ","))) == 1, length(ks[[1]])))
cat("    THAT IS THE PROBE'S `same shape as $.new_crates[]`, and tidyr agrees\n")
cat("    about the KEYS. It is about to disagree about the VALUES.\n")

# ── Q5. THE CENTREPIECE, answered by accident. ─────────────────────────────
cat("\nQ5  columns whose CLASS disagrees across the four collections:\n")
for (cn in names(tbls[[1]])) {
  cl <- map_chr(tbls, \(t) class(t[[cn]])[1])
  if (length(unique(cl)) > 1)
    cat(sprintf("      %-17s %s\n", cn,
                paste(sprintf("%s=%s", ABBR, cl), collapse = "  ")))
}
cat("    TWO COLUMNS, IN OPPOSITE DIRECTIONS — a different collection is the\n")
cat("    odd one out for each. tidyr never asked for a type and got one anyway,\n")
cat("    because a column must have one. It joins polars, DuckDB and jsonlite.\n")

cat("\n    THE THRESHOLD, which is the part no other tool here measured:\n")
for (cn in c("recent_downloads", "documentation"))
  cat(sprintf("      %-17s nulls out of 10: %s\n", cn,
              paste(map_chr(seq_along(FOUR), \(i) sprintf("%s %2d", ABBR[i],
                    sum(map_lgl(doc[[FOUR[i]]], \(x) is.null(x[[cn]]))))), collapse = "  ")))
cat("    `documentation` is null on EIGHT of ten new_crates and still types\n")
cat("    character. It is null on TEN of ten just_updated and types logical.\n")
cat("    ══ TOTAL ABSENCE FLIPS IT; AN 80% NULL RATE DOES NOT. ══\n")

# ── the erasure I did not predict. ─────────────────────────────────────────
nc <- tbls$new_crates
lg <- names(nc)[map_lgl(nc, \(c) is.logical(c) && all(is.na(c)))]
cat(sprintf("\n    AND IT IS NOT ONLY THE TWO. %d of the %d crate fields arrive as\n",
            length(lg), ncol(nc)))
cat(sprintf("    all-NA logical on new_crates: %s\n", paste(lg, collapse = ", ")))
cat(sprintf("      `badges`  in the JSON: %s -> column class %s\n",
            if (is.null(doc$new_crates[[1]]$badges)) "null" else "an empty ARRAY",
            class(nc$badges)[1]))
cat(sprintf("      `yanked`  in the JSON: a real BOOLEAN     -> column class %s\n",
            class(nc$yanked)[1]))
cat("    I PREDICTED unnest_longer(keywords) WOULD DROP EVERY ROW. It drops\n")
cat(sprintf("    none — %d in, %d out on new_crates — because the column is not\n",
            nrow(nc), nrow(nc |> unnest_longer(keywords))))
cat("    a list column at all. THE FIELD'S KIND IS ERASED, NOT JUST ITS VALUE: an\n")
cat("    array field and a boolean field are now the same type, and nothing in\n")
cat("    the frame distinguishes them.\n")

# ── Q4. ────────────────────────────────────────────────────────────────────
cat(sprintf("\nQ4  unnest_wider gives every record every column, so ABSENT and NULL\n"))
cat("    are one NA. On this document that is harmless — the key-sets really\n")
cat("    are identical — and it is exactly why Q5's answer had to come from\n")
cat("    the column CLASS rather than from a missingness count.\n")

# ── Q3. ────────────────────────────────────────────────────────────────────
m <- capture.output(a <- suppressWarnings(unnest_auto(tibble(d = list(doc)), d)),
                    type = "message")
cat(sprintf("\nQ3  unnest_auto on the root -> %s\n", trimws(paste(m, collapse = " "))))
cat(sprintf("    -> %d x %d. It attempts the question and the answer is useless\n",
            nrow(a), ncol(a)))
cat("    here: one row of eight list-columns is the document unchanged. On a\n")
cat("    single-record document the `names in common` rule is trivially true,\n")
cat("    which is the same failure entry 01 recorded and entry 24 explains.\n")

# ── Q8 / Q9 / Q10 / Q12. ───────────────────────────────────────────────────
all40 <- bind_rows(tbls, .id = "collection")
cat(sprintf("\nQ7  %d rows over the four collections", nrow(all40)))
cat(sprintf(" — holding %d DISTINCT crates.\n", n_distinct(all40$name)))
cat("    bind_rows COERCED BOTH mismatched columns and warned about neither:\n")
cat(sprintf("      recent_downloads -> %s   documentation -> %s\n",
            class(all40$recent_downloads)[1], class(all40$documentation)[1]))
cat("    Both coercions are CORRECT. The silence is the defect, not the result,\n")
cat("    and the overlap of seven crates is invisible to tidyr as to everything.\n")

three <- tibble(x = doc$new_crates) |>
  hoist(x, name = "name", downloads = "downloads", owners = c("links", "owners")) |>
  select(name, downloads, owners)
cat(sprintf("\nQ8  hoist(), reaching through `links` to depth 4 -> %d x %d\n",
            nrow(three), ncol(three)))
print(head(as.data.frame(three), 2))

cat(sprintf("\nQ9  `documentation` present on %d of %d rows, absent on %d, and the\n",
            sum(!is.na(all40$documentation)), nrow(all40), sum(is.na(all40$documentation))))
cat("    rows are kept because unnest_wider keeps rows by construction.\n")

cat("\nQ10 NOTHING TO FLATTEN, and that is the answer. Every array-valued field\n")
cat("    inside a crate — versions, keywords, categories, badges — is empty on\n")
cat("    all 40 records, so the deepest ARRAY in this document is the top-level\n")
cat("    collection itself. `links` is the deepest OBJECT, at depth 4.\n")

flat <- all40 |> unnest_wider(links, names_repair = "unique_quiet")
cat(sprintf("\nQ12 the four collections + links -> %d x %d, %d list-columns left\n",
            nrow(flat), ncol(flat), sum(map_lgl(flat, is.list))))
cat("    AND ZERO LIST-COLUMNS LOOKS LIKE TOTAL SUCCESS. It is the erasure\n")
cat("    wearing the face of a clean result: the frame is fully rectangular\n")
cat("    only because every nested field in every crate was empty, so nothing\n")
cat("    survived to need a list. A document where one crate had keywords\n")
cat("    would not flatten at all.\n")
cat("    WHAT IS LOST: the collection a crate came from survives only because\n")
cat("    `.id` was asked for, seven crates are double-counted, and five fields\n")
cat("    that are arrays in the schema are indistinguishable from booleans.\n")

cat("
13. NO for 1, 4, 5 and 7. Question 5 is the interesting one — tidyr answers it
    WITHOUT BEING ASKED and without being able to ask it, because rectangling
    forces a type and four tables then disagree. A tool that cannot express the
    question can still expose the answer, which is not a category this project
    had.

14. YES. Nothing here hard-codes a crate name or a field name, so the next
    crates.io summary runs unchanged — and would silently change types again if
    a different collection went all-null.

16. ~105 lines, and the ceremony is the four-way comparison rather than the
    rectangling: the actual work is `unnest_wider(x)` and `hoist`.
")
