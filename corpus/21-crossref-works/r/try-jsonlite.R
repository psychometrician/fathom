# jsonlite — Crossref works, 1,000 records
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
#  measured      2026-08-11
#  run           cd corpus/21-crossref-works/r && Rscript try-jsonlite.R
#
#  Header numbers filled in from the run.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

RAW <- "../source.json"
cat("\nQ0  jsonlite parses or errors. It REFUSES bare NaN, which is more than\n")
cat("    most parsers here; no duplicate-key or big-int report. PARTLY.\n")

t0 <- Sys.time()
simple <- fromJSON(RAW)
t_s <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
t0 <- Sys.time()
raw <- fromJSON(RAW, simplifyVector = FALSE)
t_r <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
items <- raw$message$items
cat(sprintf("\n     fromJSON()                      %.1fs\n", t_s))
cat(sprintf("     fromJSON(simplifyVector = FALSE) %.1fs\n", t_r))

# ── Q1. THE WRAPPER, and jsonlite handles it better than every frame here. ──
cat(sprintf("\nQ1  the root is a %s with names: %s\n",
            class(simple), paste(names(simple), collapse = ", ")))
df <- simple$message$items
cat(sprintf("Q1  $message$items simplified to a %s: %d x %d\n",
            paste(class(df), collapse = "/"), nrow(df), ncol(df)))
cat("    jsonlite FOLLOWED THE WRAPPER because `fromJSON` returns a nested R\n")
cat("    list and simplifies each array it meets. pandas, polars and DuckDB all\n")
cat("    returned the one-row ENVELOPE when pointed at the file; jsonlite hands\n")
cat("    you the envelope AND the records, and `$message$items` is how you ask.\n")
nested <- names(df)[vapply(df, \(c) is.list(c) || is.data.frame(c), logical(1))]
cat(sprintf("Q1  %d of %d columns are themselves lists or data frames\n",
            length(nested), ncol(df)))
cat("Q2  no depth verb. CANNOT — the probe says 9.\n")

cat(sprintf("\nQ3  ONE candidate, priced only if you ask. %d rows.\n", nrow(df)))
cat(sprintf("Q7  %d works; total-results is %s\n", length(items),
            format(raw$message$`total-results`, big.mark = ",")))

# ── Q4. THE simplifyVector EXPERIMENT, second document. ─────────────────────
atomic <- vapply(df, \(c) !(is.list(c) || is.data.frame(c)), logical(1))
na_any <- sum(vapply(df[atomic], \(c) any(is.na(c)), logical(1)))
present <- table(unlist(lapply(items, names)))
absent <- present[present < length(items)]
nulls <- sum(vapply(names(present), \(k)
  any(vapply(items, \(w) k %in% names(w) && is.null(w[[k]]), logical(1))), logical(1)))
cat(sprintf("\nQ4  simplified: %d of %d ATOMIC columns hold an NA\n", na_any, sum(atomic)))
cat(sprintf("Q4  simplifyVector = FALSE + names(): %d keys sometimes ABSENT, %d null\n",
            length(absent), nulls))
cat("    ENTRY 15 AND ENTRY 20 BOTH FOUND THE FLAG DECIDING THIS ANSWER. Here it\n")
cat("    does NOT, because the document has zero written nulls — so the two\n")
cat("    routes cannot disagree about absent-versus-null. They still disagree\n")
cat("    about the COUNT, because simplification turned 57 keys into columns of\n")
cat("    which many are list-columns that hold no NA at all.\n")

# ── Q5. ─────────────────────────────────────────────────────────────────────
cat(sprintf("\nQ5  the probe's ONE site: issued$`date-parts`\n"))
cat(sprintf("    simplified class: %s\n", paste(class(df$issued$`date-parts`), collapse = "/")))
dp <- table(vapply(items, \(w) {
  v <- w$issued$`date-parts`[[1]][[1]]
  if (is.null(v)) "null" else class(v)[1]
}, character(1)))
cat(sprintf("    unsimplified, indexed twice: %s\n",
            paste(sprintf("%s=%d", names(dp), dp), collapse = ", ")))
cat("    jsonlite RESOLVES it silently — the list-column holds both without a\n")
cat("    word, which is honest representation and is not a report.\n")

# ── Q6. ─────────────────────────────────────────────────────────────────────
refk <- unique(unlist(lapply(items, \(w) lapply(w$reference, names))))
refn <- sum(vapply(items, \(w) length(w$reference), integer(1)))
cat(sprintf("\nQ6  reference[]: %d keys over %s copies. The probe DECLINES it.\n",
            length(refk), format(refn, big.mark = ",")))

# ── HYPHENS. ────────────────────────────────────────────────────────────────
hy <- grep("-", names(df), value = TRUE)
cat(sprintf("\n     HYPHENATED COLUMNS: %d of %d\n", length(hy), ncol(df)))
cat("     `df$reference-count` is a SUBTRACTION in R too, so every one needs\n")
cat("     backticks or [[ ]]. Same hazard as DuckDB's quoting and pandas'\n")
cat("     `query` backticks; polars alone does not care.\n")
cat(sprintf("     df$`reference-count`[1] = %s, and df$reference-count is an error.\n",
            df$`reference-count`[1]))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
tbl <- df[, c("DOI", "type", "publisher")]
cat(sprintf("\nQ8  %d x %d, already a frame\n", nrow(tbl), ncol(tbl))); print(head(tbl, 2))
cat(sprintf("\nQ9  abstract non-NA on %d of %d; rows kept\n",
            sum(!is.na(df$abstract)), nrow(df)))
t0 <- Sys.time()
res <- do.call(rbind, lapply(items, \(w) {
  rs <- w$reference; if (is.null(rs)) return(NULL)
  data.frame(work_DOI = w$DOI,
             key = vapply(rs, \(r) r$key %||% NA_character_, character(1)))
}))
cat(sprintf("\nQ10 reference[] -> %d rows x %d, %.1fs\n", nrow(res), ncol(res),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
chr <- names(df)[vapply(df, is.character, logical(1))]
nu <- sum(vapply(chr, \(k) any(grepl("^https?://", df[[k]])), logical(1)))
cat(sprintf("\nQ11 %d of %d character columns hold a URL. jq says 13 distinct PATHS.\n",
            nu, length(chr)))
t0 <- Sys.time()
flat <- flatten(df)
cat(sprintf("\nQ12 jsonlite::flatten -> %d x %d, %.1fs\n", nrow(flat), ncol(flat),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
still <- sum(vapply(flat, \(c) is.list(c) || is.data.frame(c), logical(1)))
cat(sprintf("    %d columns are STILL lists after flattening. Honest, not flat.\n", still))
cat("    NOTE `jsonlite::flatten` masks `purrr::flatten` — entry 18 lost a run to it.\n")
