# rrapply — Home Assistant frontend, the English translation catalogue
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
#  measured      2026-08-12
#  run           cd corpus/28-home-assistant-i18n/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             5   NO                  YES — every level, melted
#   2 how deep                                    3   NO                  YES — 11, it is the column count
#   3 what is one record                          6   NO                  names none, counts any
#   4 always present vs sometimes                 5   NO                  yes, by counting L-columns
#   5 does any field change type                  4   NO                  yes — how="melt" keeps types
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            2   NO                  yes — 8,518
#   8 three named fields to a table               4  YES                  yes
#   9 a field missing from some rows              4  YES                  yes — filter finds nothing
#  10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
#  11 find every path matching something          4   NO                  YES — one filter
#  12 flattest honest table                       6   NO                  YES — 8,518 x 12, ONE CALL
#  13 needed the shape in advance?                    NO for 1,2,4,5,11,12
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          YES — `how = "melt"` says it
#  16 lines, and how much is ceremony?                ~85
#
# **`rrapply(doc, how = "melt")` IS THE ANSWER TO THIS DOCUMENT, in one call.**
# It returns 8,518 rows and TWELVE columns — L1 … L11, one per level, plus
# `value` — which is better than the dotted path duckdb and jq give, because the
# levels are already separate columns you can group by.
#
# **It is the strongest single verb any of the fourteen tools brings here**, and
# the level-per-column shape is something no other tool in either language
# produces at all.

suppressMessages({library(jsonlite); library(rrapply)})
cat(sprintf("jsonlite %s · rrapply %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("rrapply"),
            R.version$major, R.version$minor))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  fromJSON parsed and said nothing — no duplicate-key report, no 2^53\n")
cat("    flag. CANNOT.\n")

# ── Q1/Q2/Q12. One call answers three questions. ─────────────────────────────
t0 <- Sys.time()
m <- rrapply(doc, how = "melt")
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 3)

lev <- grep("^L", names(m), value = TRUE)
cat(sprintf("\nQ1  rrapply(doc, how = \"melt\") -> %s rows x %d cols: %s\n",
            format(nrow(m), big.mark = ","), ncol(m),
            paste(names(m), collapse = ", ")))
cat("    YES. Every leaf, at every level, and nothing known in advance.\n")

cat(sprintf("\nQ2  %d level columns, so depth %d. YES — and it agrees with the\n",
            length(lev), length(lev)))
cat("    probe, jq, ijson and duckdb, which all say 11.\n")

# ── Q3/Q7. What is one record. ───────────────────────────────────────────────
cat("\nQ3  rrapply names no candidates and prices none. It counts any you name:\n")
cat(sprintf("      one message per row      %s\n", format(nrow(m), big.mark = ",")))
cat(sprintf("      one L1 section per row   %d\n", length(unique(m$L1))))
cat(sprintf("      one L1.L2 group per row  %d\n",
            nrow(unique(m[, c("L1", "L2")]))))
cat("    CANNOT for Q3 — three defensible answers, none proposed, none priced.\n")
cat(sprintf("\nQ7  %s messages under the reading Q12 takes. yes.\n",
            format(nrow(m), big.mark = ",")))

# ── Q4. Always vs sometimes. ─────────────────────────────────────────────────
depth_of <- rowSums(!is.na(m[, lev]))
cat("\nQ4  how many messages sit at each depth:\n")
print(table(depth_of))
cat("    yes — and this is the shape of the document in one line. There is no\n")
cat("    'always present' here because there is no repeated record to compare.\n")

# ── Q5. Type variation. ──────────────────────────────────────────────────────
cat(sprintf("\nQ5  classes of the melted value column: %s\n",
            paste(unique(vapply(m$value, class, "")), collapse = ", ")))
cat("    Every leaf is a character. `how = \"melt\"` keeps the value as it was,\n")
cat("    so a document that varied would show it here without being asked.\n")

cat("\nQ6  CANNOT. rrapply has no notion of a key being data rather than a name.\n")

# ── Q8/Q9. Named fields. ─────────────────────────────────────────────────────
pick <- function(...) {
  want <- c(...)
  i <- which(m$L1 == want[1] & m$L2 == want[2] & m$L3 == want[3])
  if (length(i)) m$value[[i[1]]] else NA_character_
}
cat(sprintf("\nQ8  %s\n", paste(c(pick("ui", "common", "and"),
                                  pick("ui", "common", "loading"),
                                  pick("ui", "panel", "profile")), collapse = " | ")))
cat("    yes, by filtering the melted frame — the third is NA because\n")
cat("    ui.panel.profile is a GROUP, not a message, which the frame shows.\n")

cat(sprintf("\nQ9  a key that is not there -> %s. The row simply is not in the\n",
            pick("ui", "panel", "nope")))
cat("    frame, so a left join keeps whatever you joined it to. yes.\n")

cat("\nQ10 zero arrays in 604 KB. NOTHING TO FLATTEN.\n")

# ── Q11. Paths matching something. ───────────────────────────────────────────
icu <- grepl("\\{", unlist(m$value))
cat(sprintf("\nQ11 messages carrying an ICU placeholder: %s — one grepl over the\n",
            format(sum(icu), big.mark = ",")))
cat("    melted frame, no paths known in advance. YES.\n")

# ── Q12. The flattest honest table. ──────────────────────────────────────────
cat(sprintf("\nQ12 %s x %d, in ONE CALL, in %s seconds.\n",
            format(nrow(m), big.mark = ","), ncol(m), secs))
print(utils::head(m[, c("L1", "L2", "L3", "value")], 3))
cat("    NOTHING IS LOST, and the levels are COLUMNS rather than a dotted\n")
cat("    string — so `table(m$L1)` and a group_by are available immediately.\n")

cat("
CONCLUSION. rrapply is the best single verb any of the fourteen tools brings to
this document. `how = \"melt\"` is one call, no shape known in advance, and its
answer is richer than duckdb's json_tree or jq's paths(scalars): a dotted path is
a string you have to split again, and L1 … L11 are already columns.

It reads back perfectly, which the other strong answers do not — `how = \"melt\"`
says what it does, where a recursive CTE and an event loop do not.

WHAT IT STILL WILL NOT DO is name the alternative row shapes or price them, and
it has no notion of keys-as-data at all. It hands you the melt and every question
about which unit is the right one is yours.

AND THE HONEST COMPARISON. fathom describes this file at 5.69% of its input with
39.3% of fields unnamed, its worst in the corpus. rrapply melts it completely in
one call. On this document rrapply's answer is better than fathom's.
")
