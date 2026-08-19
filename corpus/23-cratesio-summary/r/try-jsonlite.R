# jsonlite — crates.io summary
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   41 KB, six collections at the root, depth 4
#  measured      2026-08-11
#  run           cd corpus/23-cratesio-summary/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   PARTLY
#   1 what is in here                             8   NO                  PARTLY
#   2 how deep                                    1   -                   CANNOT
#   3 what is one record                         14   YES                 THE COLUMN TYPES DIFFER
#   4 always present vs sometimes                10   NO                  see below
#   5 does any field change type                  4   NO                  yes — NONE
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                             3  NO                  three answers
#   8 three named fields to a table                3 YES                 yes
#   9 a field missing from some rows                4 YES                 PARTLY
#  10 flatten the deepest array                     4 -                   NO ARRAY TO FLATTEN
#  11 find every path matching something            4 NO                  PARTLY
#  12 flattest honest table                         6 NO                  rbind, and it DUPLICATES
#  13 needed the shape in advance?                    YES — the four collections by name
#  14 survives the next file unchanged?               Q1/Q3 yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~105
#
# jsonlite SIMPLIFIES THE WHOLE DOCUMENT IN ONE CALL and hands back the envelope
# AND the six collections, which pandas, polars and DuckDB could not do. Four of
# them come out as data frames of 10 x 23.
#
# AND IT LANDS ON THE SAME SPLIT polars and DuckDB found: the four have one
# key-set and NOT one set of column types, because `recent_downloads` is null on
# all ten `new_crates`. `rbind` on the four therefore has to reconcile a logical
# NA column with an integer one — and R does it silently, landing with pandas.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

RAW <- "../source.json"
CRATE <- c("new_crates", "most_downloaded", "most_recently_downloaded", "just_updated")
cat("\nQ0  jsonlite parses or errors; it REFUSES bare NaN. No duplicate-key or\n")
cat("    big-int report. PARTLY.\n")

simple <- fromJSON(RAW)
raw <- fromJSON(RAW, simplifyVector = FALSE)
crates <- unlist(lapply(CRATE, \(k) raw[[k]]), recursive = FALSE)

cat(sprintf("\nQ1  the root simplifies to a %s of %d: %s\n",
            class(simple), length(simple), paste(names(simple), collapse = ", ")))
for (k in CRATE) {
  d <- simple[[k]]
  cat(sprintf("Q1  %-26s -> %s, %d x %d\n", k, paste(class(d), collapse = "/"),
              nrow(d), ncol(d)))
}
cat("    ONE CALL gave the envelope AND all six collections. pandas, polars and\n")
cat("    DuckDB each returned a one-row envelope and had to be pointed at a\n")
cat("    collection by name; jsonlite hands you the whole tree.\n")
cat("Q2  no depth verb. CANNOT — the probe says 4.\n")

# ── Q3. THE COLUMN TYPES, AND THEY DIFFER. ──────────────────────────────────
sig <- lapply(CRATE, \(k) sort(names(simple[[k]])))
cat(sprintf("\nQ3  distinct COLUMN-NAME sets across the four: %d\n", length(unique(sig))))
types <- lapply(CRATE, \(k) vapply(simple[[k]], \(c) class(c)[1], character(1)))
names(types) <- CRATE
base <- types[["new_crates"]]
cat(sprintf("Q3  distinct COLUMN-TYPE vectors across the four: %d\n", length(unique(types))))
for (k in CRATE) {
  d <- names(which(types[[k]] != base[names(types[[k]])]))
  if (length(d))
    cat(sprintf("    %-26s differs in %s\n", k,
                paste(sprintf("%s (%s vs %s)", d, base[d], types[[k]][d]), collapse = ", ")))
}
cat("    ONE KEY-SET, MORE THAN ONE TYPE VECTOR — the identical split polars and\n")
cat("    DuckDB found, reached by a third mechanism. `recent_downloads` is null\n")
cat("    on all ten `new_crates`, so jsonlite makes it a LOGICAL NA column there\n")
cat("    and an integer one elsewhere.\n")
cat("    THE PROBE FOLDS ON KEY-SETS and says the four are one shape. THREE\n")
cat("    TYPE-INFERRING TOOLS SAY THEY ARE NOT. Both answers are correct, about\n")
cat("    different questions, and this document is where they separate.\n")

cat("\nQ3  and `rbind` of the four:\n")
allrows <- tryCatch(do.call(rbind, lapply(CRATE, \(k) cbind(simple[[k]], .list = k))),
                    error = function(e) e)
if (inherits(allrows, "error")) {
  cat(sprintf("    RAISES: %s\n", conditionMessage(allrows)))
  cat("    ON ROW NAMES — not on the type conflict, and nothing to do with the\n")
  cat("    data at all. Each of the four frames carries row names 1..10.\n")
  cat("    A FOURTH DISTINCT BEHAVIOUR ON ONE CONCATENATION:\n")
  cat("      pandas   succeeds silently, and mixes NaN with None in one column\n")
  cat("      polars   RAISES on the type: Int64 incompatible with Null\n")
  cat("      DuckDB   builds the view; count(*) works and EVERY FIELD ERRORS\n")
  cat("      R rbind  RAISES on ROW NAMES, before it ever looks at a type\n")
  cat("    STRIPPING THE OUTER ROW NAMES IS NOT ENOUGH EITHER — the nested\n")
  cat("    `links` data frame carries its own. The route that works is\n")
  cat("    `dplyr::bind_rows`, which is not jsonlite at all:\n")
  allrows <- dplyr::bind_rows(lapply(CRATE, \(k) dplyr::mutate(simple[[k]], .list = k)))
  cat(sprintf("    bind_rows: %d x %d, recent_downloads is now %s\n",
              nrow(allrows), ncol(allrows), class(allrows$recent_downloads)[1]))
  cat("    AND IT COERCED THE LOGICAL NA COLUMN INTO THE INTEGER ONE SILENTLY,\n")
  cat("    which is pandas' behaviour reached by a different library. So R has\n")
  cat("    BOTH failure modes on one document, depending which verb you use.\n")
} else {
  cat(sprintf("    OK %d x %d — rewrite this note\n", nrow(allrows), ncol(allrows)))
}
cat(sprintf("    AND %d ROWS HOLD ONLY %d DISTINCT CRATES: %s\n",
            nrow(allrows), length(unique(allrows$id)),
            paste(sort(names(which(table(allrows$name) > 1))), collapse = ", ")))
cat("    FIVE ROUTES, FIVE BEHAVIOURS, ONE CAUSE — a column that is null on\n")
cat("    every row of one collection. And R holds two of the five by itself.\n")

# ── Q4/Q5/Q6/Q7. ────────────────────────────────────────────────────────────
atomic <- vapply(allrows, \(c) !(is.list(c) || is.data.frame(c)), logical(1))
nas <- vapply(allrows[atomic], \(c) sum(is.na(c)), integer(1))
pres <- table(unlist(lapply(crates, names)))
nulls <- vapply(names(pres),
                \(k) sum(vapply(crates, \(c) is.null(c[[k]]), logical(1))), integer(1))
cat("\nQ4  simplified: atomic columns holding an NA:\n"); print(nas[nas > 0])
cat(sprintf("Q4  unsimplified: %d keys ever ABSENT; written NULL:\n",
            sum(pres < length(crates))))
print(nulls[nulls > 0])
cat(sprintf("Q4  NULL ON ALL %d: %s\n", length(crates),
            paste(names(nulls)[nulls == length(crates)], collapse = ", ")))
cat("    `simplifyVector` decides nothing about ABSENCE here — nothing is ever\n")
cat("    absent — but it decides everything about TYPE, which is question 3's\n")
cat("    finding. Entries 15 and 20 found the flag deciding question 4; this is\n")
cat("    the first document where it decides question 3 instead.\n")
cat("\nQ5  the probe reports NO type change, and every simplified column is one\n")
cat("    R type. jsonlite agrees.\n")
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")
cat(sprintf("\nQ7  num_crates %s; num_downloads %s; %d rows, %d distinct\n",
            format(simple$num_crates, big.mark = ","),
            format(simple$num_downloads, big.mark = ","),
            nrow(allrows), length(unique(allrows$id))))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8 <- simple$new_crates[, c("name", "max_version", "downloads")]
cat(sprintf("\nQ8  %d x %d, already a frame\n", nrow(t8), ncol(t8))); print(head(t8, 2))
cat(sprintf("\nQ9  `homepage` non-NA on %d of %d, rows kept\n",
            sum(!is.na(allrows$homepage)), nrow(allrows)))
cat("    Every crate HAS the key; 19 write null. jsonlite turns that into NA,\n")
cat("    which is right, and it is the same NA an absent key would make.\n")
cat("\nQ10 THERE IS NO ARRAY BELOW THE COLLECTIONS. `links` is an object of six\n")
cat("    fields, simplified into a nested data frame.\n")
cat(sprintf("    `simple$new_crates$links` is a %s of %d x %d\n",
            paste(class(simple$new_crates$links), collapse = "/"),
            nrow(simple$new_crates$links), ncol(simple$new_crates$links)))
chr <- names(allrows)[vapply(allrows, is.character, logical(1))]
nu <- sum(vapply(chr, \(k) any(grepl("^https?://", allrows[[k]])), logical(1)))
cat(sprintf("\nQ11 %d of %d character columns hold a URL. jq reports 11 distinct URL\n",
            nu, length(chr)))
cat("    PATHS folding to 3; a column scan over ONE concatenated frame is\n")
cat("    already the folded form.\n")
fl <- flatten(allrows)
cat(sprintf("\nQ12 flatten(rbind of four) -> %d x %d, holding %d distinct crates.\n",
            nrow(fl), ncol(fl), length(unique(allrows$id))))
cat("    NOTE `jsonlite::flatten` masks `purrr::flatten` — entry 18 lost a run.\n")
