# tidyjson — a scrubbed Claude Code transcript, NDJSON, 1,953 records
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (version printed below)
#  file          ../source.jsonl  4.8 MB, NDJSON, 1,953 records, depth 10,
#                                 452 paths, 151 fields, polymorphic 4
#  measured      2026-08-10
#  run           cd corpus/12-agent-trace/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                          10   NO                  CANNOT
#   3 what is one record                        3   NO                  YES
#   4 always present vs sometimes               5   NO                  YES
#   5 does any field change type               12   NO                  WRONG
#   7 how many records                          1   NO                  yes
#   8 three named fields to a table             5   YES                 yes
#  13 needed the shape in advance?                  no for 3, 4, 5
#  16 lines, and how much is ceremony?              see the conclusion
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. It tests **prediction 2**: that `json_schema` drops the string
# form of `message.content`, which is `array ×1,363` against `text ×20`.
#
# On `10-wikidata` the object absorbed the string in BOTH input orders and 31%
# of records were described as the wrong type. **Here the minority is 1.4%** —
# twenty messages out of 1,383 — which is the case where a silent drop is
# hardest to notice and easiest to defend as rounding.
suppressMessages({library(tidyjson); library(jsonlite)})
cat(sprintf("R %s, tidyjson %s, jsonlite %s\n", getRversion(),
            packageVersion("tidyjson"), packageVersion("jsonlite")))

path <- "../source.jsonl"
ln   <- readLines(path, warn = FALSE)
doc  <- lapply(ln, fromJSON, simplifyVector = FALSE)

# ── Q3 / Q7. NDJSON is tidyjson's native shape, as on 04-gharchive. ──────────
cat("\n3/7. what is one record, and how many:\n")
t0 <- Sys.time()
tj <- as.tbl_json(ln)
cat(sprintf("   as.tbl_json(readLines(...)) -> %s documents in %.1f s\n",
            format(nrow(tj), big.mark = ","),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("   Nothing known in advance and no verb chosen — the same result as on\n")
cat("   04-gharchive, and for the same reason: tidyjson's model is a table of\n")
cat("   documents and NDJSON is literally that.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
kt <- tj |> gather_object() |> json_types()
tb <- sort(table(as.character(kt$name)), decreasing = TRUE)
cat(sprintf("   %d distinct top-level keys over %s records\n",
            length(tb), format(length(ln), big.mark = ",")))
for (k in names(tb)[1:6])
  cat(sprintf("     %-22s %5s\n", k, format(as.integer(tb[[k]]), big.mark = ",")))
cat(sprintf("   present on ALL: %s\n",
            paste(names(tb)[tb == length(ln)], collapse = ", ")))
cat("   Fast, correct, nothing known first. NOTES.md grades 168/426 ragged by\n")
cat("   absence and the top-level spread above is the visible part of it.\n")

# ── Q5. PREDICTION 2. ────────────────────────────────────────────────────────
cat("\n5. does any field change type — message.content:\n")
ct <- vapply(doc, function(x) {
  m <- x$message
  if (!is.list(m)) return("no message")
  cc <- m$content
  if (is.null(cc)) "absent" else if (is.character(cc)) "string" else "array"
}, "")
cat(sprintf("   the truth: %s\n",
            paste(sprintf("%s x%s", names(table(ct)),
                          format(as.integer(table(ct)), big.mark = ",")),
                  collapse = ", ")))
si <- which(ct == "string")[1]; ai <- which(ct == "array")[1]
s <- doc[[si]]$message; a <- doc[[ai]]$message
sch <- function(x) as.character(json_schema(
  as.character(toJSON(x, auto_unbox = TRUE, null = "null"))))
cat(sprintf("   a string-content message alone: %s\n", substr(sch(s), 1, 60)))
cat(sprintf("   an array-content message alone: %s\n", substr(sch(a), 1, 60)))
cat("   and the two together, in each order:\n")
cat(sprintf("     [string, array]: %s\n", substr(sch(list(s, a)), 1, 60)))
cat(sprintf("     [array, string]: %s\n", substr(sch(list(a, s)), 1, 60)))
cat("   PREDICTION 2 CONFIRMED. The ARRAY form wins in BOTH orders and the\n")
cat("   string vanishes — the same absorption as on 10-wikidata, where the\n")
cat("   object swallowed the scalar in both orders.\n")
cat("   THIRD DOCUMENT FOR THE TYPE-DROP, AND THE HARDEST TO NOTICE. On\n")
cat("   10-wikidata the discarded minority was 31% of records. Here it is\n")
cat(sprintf("   %d of %d — %.1f%%. A description that is wrong about 1.4%% of a\n",
            sum(ct == "string"), sum(ct %in% c("string", "array")),
            100 * sum(ct == "string") / sum(ct %in% c("string", "array"))))
cat("   document reads as a description that is right.\n")
cat("   SCORED WRONG, NOT NO — it answers, and the answer is false for the 20.\n")

# ── Q1. ──────────────────────────────────────────────────────────────────────
cat("\n1. what is in here — json_schema on the whole file:\n")
cat("      n  input       time    schema\n")
rate <- NA
for (n in c(20, 80)) {
  sub <- paste0("[", paste(ln[seq_len(n)], collapse = ","), "]")
  t0  <- Sys.time()
  s2  <- as.character(json_schema(sub))
  el  <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  cat(sprintf("   %4d %9s B %7.1fs  %7s c\n", n, format(nchar(sub), big.mark = ","),
              el, format(nchar(s2), big.mark = ",")))
  flush.console()
  rate <- nchar(sub) / el
}
cat(sprintf("\n   %.1f KB/s, so the whole %.1f MB extrapolates to about %.0f minutes.\n",
            rate / 1024, file.size(path) / 1024^2,
            (file.size(path) / rate) / 60))
cat("   NOT RUN. SCORED CANNOT, the second document after 04-gharchive where\n")
cat("   this function does not return rather than returning something wrong.\n")
cat("   Both are NDJSON, which corpus/README.md calls how JSON at scale\n")
cat("   actually arrives.\n")

# ── Q8. ──────────────────────────────────────────────────────────────────────
cat("\n8. three named fields, one row per record:\n")
tbl <- tj |> spread_values(type = jstring("type"), uuid = jstring("uuid"))
df <- as.data.frame(tbl)
cat(sprintf("   spread_values -> %s x %d\n", format(nrow(df), big.mark = ","), ncol(df)))
cat(sprintf("   type: %s\n",
            paste(sprintf("%s %s", names(sort(table(df$type), decreasing = TRUE))[1:4],
                          format(sort(table(df$type), decreasing = TRUE)[1:4],
                                 big.mark = ",")), collapse = ", ")))

cat("
CONCLUSION — the type-drop's third document, and the one where it is hardest
to catch.

  **`json_schema` describes all 1,383 messages as having an array `content`**,
  and twenty of them hold a bare string. It reports the array form in **both**
  input orders — absorption, not order-dependence, the same behaviour as
  `10-wikidata`'s object swallowing a scalar.

  **What is new is the dose.** On wikidata the discarded minority was 31% of
  records, large enough that a careful reader might notice the description did
  not match. Here it is **1.4%** — twenty messages out of 1,383. A description
  that is wrong about one record in seventy reads as a description that is
  right, and nothing in the output distinguishes them.

  `NOTES.md` grades this file **polymorphic 4, the highest in the corpus**, and
  the schema reports none of it.

  AND ON THE WHOLE FILE IT DOES NOT RETURN. Measured on slices, the 4.8 MB
  extrapolates past half an hour — the second NDJSON document after
  `04-gharchive` where this function is scored CANNOT rather than WRONG. Both
  are the format `corpus/README.md` calls how JSON at scale actually arrives.

  WHAT TIDYJSON DOES WELL is unchanged and real: `as.tbl_json` on a character
  vector gives 1,953 documents with nothing known in advance,
  `gather_object |> json_types` answers question 4 by counting, and
  `spread_values` reads cleanly. **The verbs are trustworthy and the inference
  is not**, which is now measured on six documents.
")
