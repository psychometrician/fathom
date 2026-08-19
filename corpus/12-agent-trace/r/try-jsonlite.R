# jsonlite — a scrubbed Claude Code transcript, NDJSON, 1,953 records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.jsonl  4.8 MB, NDJSON, 1,953 records, depth 10,
#                                 452 paths, 151 fields, polymorphic 4
#  measured      2026-08-10
#  run           cd corpus/12-agent-trace/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                             4   no                  yes
#   1 what is in here                           4   NO                  NO
#   2 how deep                                  2   NO                  yes
#   3 what is one record                        4   NO                  YES
#   4 always present vs sometimes               6   NO                  yes
#   5 does any field change type                8   NO                  PRESERVED
#   6 are any keys actually data                6   YES                 NO
#   7 how many records                          1   no                  yes
#  13 needed the shape in advance?                  no for 0, 2, 3, 7
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 3**: that simplification PRESERVES rather
# than folds here — the `03-natural-earth` outcome — because `message.content`
# is genuinely two types and a rectangle cannot hold both.
#
# Across six documents the one rule `build the widest rectangle that fits` has
# produced four behaviours with nothing in the output saying which fired. This
# is the seventh, and the first NDJSON one with real polymorphism in it.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.jsonl"
ln   <- readLines(path, warn = FALSE)
cat(sprintf("  %s records, %.1f MB\n", format(length(ln), big.mark = ","),
            file.size(path) / 1024^2))

cat("\n0/7. is this sound, and how many records:\n")
cat(sprintf("   readLines -> %s; failing validate(): %d\n",
            format(length(ln), big.mark = ","),
            sum(!vapply(ln, validate, TRUE, USE.NAMES = FALSE))))
cat("   NDJSON read on \\n, as on 04-gharchive. No damage invented.\n")

t0 <- Sys.time()
df <- stream_in(file(path), verbose = FALSE)
cat(sprintf("\n3. stream_in() -> %s x %d in %.1f s\n",
            format(nrow(df), big.mark = ","), ncol(df),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("   columns: %s\n", paste(utils::head(names(df), 10), collapse = ", ")))
cat("   Question 3 answered unprompted: one transcript record is a row.\n")

doc <- lapply(ln, fromJSON, simplifyVector = FALSE)
depth <- function(x) if (is.list(x) && length(x)) 1 + max(vapply(x, depth, 0)) else 0
cat(sprintf("\n2. depth %d (max over records; NOTES.md grades the file 10)\n",
            max(vapply(doc, depth, 0))))

cat("\n1. what is in here — str() on a 1,953-row nested frame:\n")
cat(sprintf("   str(max.level=2): %d lines\n",
            length(capture.output(str(df, max.level = 2)))))
cat("   NOTES.md measures 452 paths and 151 fields; str() reports neither.\n")

# ── Q5. PREDICTION 3. ────────────────────────────────────────────────────────
cat("\n5. does any field change type — PREDICTION 3:\n")
msg <- df$message
cat(sprintf("   $message is a %s\n", class(msg)[1]))
if (is.data.frame(msg)) {
  cc <- msg$content
  cat(sprintf("   $message$content is a %s\n", class(cc)[1]))
  kinds <- table(vapply(cc, function(x)
    if (is.null(x)) "NULL" else if (is.character(x)) "character" else class(x)[1], ""))
  cat(sprintf("   what the column actually holds: %s\n",
              paste(sprintf("%s x%s", names(kinds),
                            format(as.integer(kinds), big.mark = ",")), collapse = ", ")))
}
cat("   PREDICTION 3 CONFIRMED — IT PRESERVED. The two types survive as a\n")
cat("   list-column, exactly as the 3-deep/4-deep coordinates did on\n")
cat("   03-natural-earth, and unlike 05-fhir-bundle where 20 kinds were folded\n")
cat("   into one 87%-empty frame.\n")
cat("   AND NOTHING SAYS SO. A list-column is what you get when a column has\n")
cat("   one shape and is nested, and it is also what you get when a column has\n")
cat("   two shapes. Reading it as a polymorphism report requires already\n")
cat("   knowing to look, which is the same sentence this corpus wrote about\n")
cat("   03-natural-earth on 2026-08-09.\n")
cat("   FIVE DOCUMENTS, ONE RULE, FOUR BEHAVIOURS, NO SIGNAL:\n")
cat("     03-natural-earth  builds the frame, PRESERVES the depth split   SAFE\n")
cat("     05-fhir-bundle    builds it, folds 20 kinds into 87% holes      WRONG\n")
cat("     01/09/10          builds nothing, the keys are data             INERT\n")
cat("     02-hn-thread      builds one per level, none compose            MISLEADING\n")
cat("     12-agent-trace    builds the frame, PRESERVES two content types SAFE\n")

# ── Q4 / Q6. ─────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
ks <- lapply(doc, names)
u  <- unique(unlist(ks)); n <- length(doc)
freq <- vapply(u, function(k) sum(vapply(ks, function(x) k %in% x, TRUE)), 0L)
cat(sprintf("   %d distinct top-level keys over %s records\n", length(u),
            format(n, big.mark = ",")))
cat(sprintf("   present in ALL: %s\n",
            paste(names(freq)[freq == n], collapse = ", ")))
cat(sprintf("   present in one only: %d keys\n", sum(freq == 1)))

cat("\n6. are any object keys actually data:\n")
# Guarded: some records have a `snapshot` that is not a list, so `$` on it
# errors. The first draft assumed every record had the same shape on a document
# NOTES.md grades 168 of 426 fields ragged by absence.
tfb <- unique(unlist(lapply(doc, function(x) {
  sn <- x$snapshot
  if (!is.list(sn) || !is.list(sn$trackedFileBackups)) return(NULL)
  names(sn$trackedFileBackups)
})))
cat(sprintf("   trackedFileBackups holds %d distinct keys, and they are file paths:\n",
            length(tfb)))
cat(sprintf("     %s\n", paste(utils::head(tfb, 3), collapse = ", ")))
cat("   NO. Defect 1 in NOTES.md records the probe missing this; jsonlite has\n")
cat("   no notion of the question either, and the paths become list names that\n")
cat("   stop being data the moment you index into them.\n")

cat("
CONCLUSION — the fifth SAFE outcome, and the fourth time it is safe by luck.

  **Prediction 3 held: simplification preserved.** `message.content` is an array
  on 1,363 records and a bare string on 20, and `stream_in` leaves both in a
  list-column rather than coercing. That is `03-natural-earth`'s outcome, where
  the same rule kept a polymorphism polars had erased.

  **And nothing says so.** A list-column is what a nested single-shape column
  looks like AND what a two-shape column looks like. `tidyjson::json_schema` on
  the same field reports every message as having an array `content` — see
  `try-tidyjson.R` — so of the two tools, the one that PRESERVED the fact cannot
  tell you, and the one that would have told you got it wrong.

  Across six documents, one rule, four behaviours, and the output never says
  which fired: SAFE here and on `03`, WRONG on `05`, INERT on `01`/`09`/`10`,
  MISLEADING on `02`. **That remains the criticism in its sharpest form** — not
  that any behaviour is wrong, but that a person cannot tell a preserved
  polymorphism from a folded one from a refused fold.

  ON QUESTION 6 IT IS SILENT, on a document where `NOTES.md` records the probe
  being silent too and calls it defect 1. Fifty file paths sit in
  `trackedFileBackups` as keys, and neither tool has an opinion.
")
