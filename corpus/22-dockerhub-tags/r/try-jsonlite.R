# jsonlite — Docker Hub tags, 100 tags
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   476 KB, 100 tags under $.results, depth 5
#  measured      2026-08-11
#  run           cd corpus/22-dockerhub-tags/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   PARTLY
#   1 what is in here                             8   NO                  PARTLY
#   2 how deep                                    1   -                   CANNOT
#   3 what is one record                          4   YES                 BOTH
#   4 always present vs sometimes                12  NO                   see below
#   5 does any field change type                  4  NO                   yes — NONE
#   6 are any object keys data                    1  -                    n/a
#   7 how many records                             2 NO                   yes, both numbers
#   8 three named fields to a table                3 YES                  yes
#   9 a field missing from some rows                6 YES                 PARTLY
#  10 flatten the deepest array                     6 YES                 yes — 1,388
#  11 find every path matching something            4 NO                  1, in the envelope
#  12 flattest honest table                         6 NO                  yes
#  13 needed the shape in advance?                    only for 8, 9, 10
#  14 survives the next file unchanged?               Q1/Q3/Q12 yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~110
#
# THE NESTED CONTROL, AND `simplifyVector` DOES NOT DECIDE ANYTHING HERE.
# Entries 15 and 20 both found the flag deciding question 4's answer, and both
# documents had written nulls at the RECORD level. This one has none — every tag
# key is present and filled — so the two parses agree about the tags and differ
# only about how the images arrive. The flag is dangerous where nulls are, and
# this is the control that says so.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

RAW <- "../source.json"
cat("\nQ0  jsonlite parses or errors; it REFUSES bare NaN. No duplicate-key or\n")
cat("    big-int report. PARTLY.\n")

simple <- fromJSON(RAW)
raw <- fromJSON(RAW, simplifyVector = FALSE)
tags <- raw$results
images <- unlist(lapply(tags, \(t) t$images), recursive = FALSE)

cat(sprintf("\nQ1  the root simplifies to a %s: %s\n",
            class(simple), paste(names(simple), collapse = ", ")))
df <- simple$results
cat(sprintf("Q1  $results -> a %s, %d x %d\n",
            paste(class(df), collapse = "/"), nrow(df), ncol(df)))
cat("    jsonlite FOLLOWS THE WRAPPER: the envelope and the records are both\n")
cat("    in the same object, and `$results` is how you ask. pandas, polars and\n")
cat("    DuckDB all returned a one-row envelope instead.\n")
cat("Q2  no depth verb. CANNOT — the probe says 5.\n")

cat(sprintf("\nQ3  an item of results: %d x %d\n", nrow(df), ncol(df)))
cat(sprintf("    `images` is a %s column — the child table, unflattened.\n",
            class(df$images)))
cat(sprintf("Q7  %d tags here; `count` says %s, `next` is a URL\n",
            nrow(df), format(simple$count, big.mark = ",")))

# ── Q4. THREE STATES. ───────────────────────────────────────────────────────
atomic <- vapply(df, \(c) !(is.list(c) || is.data.frame(c)), logical(1))
cat(sprintf("\nQ4  simplified tags: %d of %d atomic columns hold an NA\n",
            sum(vapply(df[atomic], \(c) any(is.na(c)), logical(1))), sum(atomic)))
ipres <- table(unlist(lapply(images, names)))
inull <- vapply(names(ipres), \(k) sum(vapply(images, \(im) is.null(im[[k]]), logical(1))),
                integer(1))
iempty <- vapply(names(ipres), \(k) sum(vapply(images, \(im) identical(im[[k]], ""), logical(1))),
                 integer(1))
cat(sprintf("Q4  image keys not on every image: %d\n", sum(ipres < length(images))))
cat("Q4  written NULL:\n"); print(inull[inull > 0])
cat("Q4  written \"\":\n"); print(iempty[iempty > 0])
cat("    THE FLAG CHANGES NOTHING ABOUT THE TAGS, because no tag key is ever\n")
cat("    absent or null. Entries 15 and 20 both had record-level nulls and both\n")
cat("    found `simplifyVector` deciding question 4. This is the control.\n")

cat("\nQ5  what jsonlite chose for each tag column:\n")
cat(sprintf("    %s\n", paste(sprintf("%s=%s", names(df)[1:6],
                                      vapply(df[1:6], \(c) class(c)[1], character(1))),
                              collapse = ", ")))
cat("    The probe reports NO type change; every column is one R type.\n")
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")

tbl <- df[, c("name", "full_size", "last_updated")]
cat(sprintf("\nQ8  %d x %d, already a frame\n", nrow(tbl), ncol(tbl))); print(head(tbl, 2))
v <- vapply(images, \(im) if (is.null(im$variant)) NA_character_ else im$variant,
            character(1))
cat(sprintf("\nQ9  `variant` non-NA on %d of %d\n", sum(!is.na(v)), length(v)))
cat("    Every image HAS the key and 1,125 write null. jsonlite turns that into\n")
cat("    NA, which is right and is the same NA an absent key would produce —\n")
cat("    and this document has no absent keys, so nothing is lost by it.\n")
t0 <- Sys.time()
res <- do.call(rbind, lapply(tags, \(t) data.frame(
  tag = t$name,
  architecture = vapply(t$images, \(im) im$architecture %||% NA_character_, character(1)),
  os = vapply(t$images, \(im) im$os %||% NA_character_, character(1)))))
cat(sprintf("\nQ10 images[] -> %d x %d, %.2fs, parent kept\n", nrow(res), ncol(res),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
chr <- names(df)[vapply(df, is.character, logical(1))]
cat(sprintf("\nQ11 %d of %d character columns in `results` hold a URL; the one URL\n",
            sum(vapply(chr, \(k) any(grepl("^https?://", df[[k]])), logical(1))), length(chr)))
cat(sprintf("    in the document is $.next, in the ENVELOPE: %s…\n",
            substr(simple[["next"]], 1, 46)))
cat("    jsonlite is the only frame here that HAS the envelope to look in.\n")
flat <- flatten(df)
cat(sprintf("\nQ12 jsonlite::flatten -> %d x %d; `images` is still a list column\n",
            nrow(flat), ncol(flat)))
cat("    or 1,388 rows unnested. Both honest, and the probe prices both.\n")
cat("    NOTE `jsonlite::flatten` masks `purrr::flatten` — entry 18 lost a run.\n")
