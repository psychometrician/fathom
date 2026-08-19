# tidyjson — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/r && Rscript try-tidyjson.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **This attempt is a SCALING TEST and says so up front.** `json_structure()`
# won entry 28 outright at 10,137 nodes. This document has 838,880 paths, 83x
# more, and the verb builds one data-frame row per node. Entry 28's own notes
# call it *"the TREE: parent.id, level, name, type"* — richer than a melt, and
# richer per node is exactly what does not survive a factor of 83.
#
# So the attempt measures the verb on growing slices FIRST and reports the
# curve, rather than starting a call that may not return. **A tool that cannot
# finish is a "cannot", and the honest way to record it is with the number that
# shows why.**

suppressMessages({library(tidyjson); library(dplyr); library(jsonlite)})
cat(sprintf("tidyjson %s · dplyr %s · jsonlite %s · R %s.%s\n",
            packageVersion("tidyjson"), packageVersion("dplyr"),
            packageVersion("jsonlite"), R.version$major, R.version$minor))

raw <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)
cat(sprintf("read: %s bytes\n", format(nchar(raw, type = "bytes"), big.mark = ",")))

cat("\nQ0  tidyjson parsed and said nothing about soundness. CANNOT.\n")

# ── Q1. gather_object, one level. ────────────────────────────────────────────
t0 <- Sys.time()
top <- raw %>% gather_object() %>% json_types()
cat(sprintf("\nQ1  gather_object() -> %d top-level keys in %.1f s\n",
            nrow(top), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
# `top` is a tbl_json and carries the whole 19.9 MB document as an attribute, so
# printing it naively dumps the file. Strip to a plain data frame first.
print(data.frame(name = top$name, type = as.character(top$type)))
cat("    ONE LEVEL. tidyjson's gather verbs descend one step per call, same as\n")
cat("    tidyr's — the difference is json_structure(), tested next.\n")

# ── THE SCALING TEST. json_structure() on growing slices. ────────────────────
doc <- fromJSON(raw, simplifyVector = FALSE)
cat("\n── json_structure() scaling ─────────────────────────────────────────────\n")
cat("  slice                        nodes        seconds\n")
sizes <- c(5, 20, 60, 150)
curve <- data.frame()
for (n in sizes) {
  # as.character(), because toJSON() returns class "json" and json_structure()
  # dispatches as.tbl_json on character. The error names the method, not the cause.
  sl <- as.character(toJSON(doc$api[seq_len(min(n, length(doc$api)))], auto_unbox = TRUE))
  t0 <- Sys.time()
  st <- sl %>% json_structure()
  s <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  cat(sprintf("  api[1:%-4d] %20s %12.2f\n", n, format(nrow(st), big.mark = ","), s))
  curve <- rbind(curve, data.frame(n = n, nodes = nrow(st), secs = s))
}

# Fit seconds against nodes on a log-log scale: the exponent says whether this
# is linear or worse, which is the whole question.
fit <- lm(log(secs) ~ log(nodes), data = curve[curve$secs > 0.01, ])
expo <- unname(coef(fit)[2])
cat(sprintf("\n  log-log slope: %.2f   (1.0 = linear; above 1 = superlinear)\n", expo))

per <- curve$secs[nrow(curve)] / curve$nodes[nrow(curve)]
est <- per * 838880 * (838880 / curve$nodes[nrow(curve)])^(expo - 1)
cat(sprintf("  extrapolated to this document's 838,880 paths: %s seconds (%.1f min)\n",
            format(round(est), big.mark = ","), est / 60))

cat("\nQ12 the honest table. THE FULL CALL IS ATTEMPTED, with a wall clock.\n")
t0 <- Sys.time()
full <- tryCatch(raw %>% json_structure(), error = function(e) e)
secs <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
if (inherits(full, "error")) {
  cat(sprintf("    FAILED after %.1f s: %s\n", secs, conditionMessage(full)))
} else {
  cat(sprintf("    %s rows x %d cols in %.1f s (%.1f min)\n",
              format(nrow(full), big.mark = ","), ncol(full), secs, secs / 60))
  cat(sprintf("    columns: %s\n", paste(names(full), collapse = ", ")))
  cat(sprintf("    levels seen: %s\n", paste(range(full$level), collapse = " to ")))
}

if (!inherits(full, "error")) {
  st <- data.frame(level = full$level, name = full$name,
                   type = as.character(full$type), stringsAsFactors = FALSE)

  # ── Q2. ───────────────────────────────────────────────────────────────────
  cat(sprintf("\nQ2  %d. YES — `level` is a column, so depth is max(level).\n",
              max(st$level)))

  # ── Q7/Q4. ────────────────────────────────────────────────────────────────
  cat("\nQ4  nodes by level:\n")
  print(table(st$level))
  cat("\nQ7  leaves, i.e. nodes whose type is neither object nor array:\n")
  leaves <- st[!st$type %in% c("object", "array"), ]
  cat(sprintf("      %s\n", format(nrow(leaves), big.mark = ",")))

  # ── Q5. THE QUESTION THIS DOCUMENT WAS CHOSEN FOR. ────────────────────────
  cat("\nQ5  node types over the whole document:\n")
  print(sort(table(st$type), decreasing = TRUE))
  va <- st[st$name %in% "version_added", ]
  cat("\n    version_added by type — the tri-typed field:\n")
  print(sort(table(va$type), decreasing = TRUE))
  cat("    YES. `type` is a column, so the polymorphism is a group_by and not\n")
  cat("    an inference. tidyjson and jq are the two that answer this cleanly.\n")

  # ── Q3. ───────────────────────────────────────────────────────────────────
  cat("\nQ3  tidyjson names no candidates and prices none. Nodes per level are\n")
  cat("    a menu of sorts, but nothing says which level is a record:\n")
  for (l in 1:4) cat(sprintf("      level %d  %s nodes\n", l,
                             format(sum(st$level == l), big.mark = ",")))
  cat("    CANNOT.\n")

  # ── Q6. ───────────────────────────────────────────────────────────────────
  cat("\nQ6  CANNOT. `name` is a column so keys are visible as values, which is\n")
  cat("    closer than most — but nothing decides that a key IS data.\n")

  # ── Q11. ──────────────────────────────────────────────────────────────────
  cat("\nQ11 tidyjson keeps no value column in json_structure(), so a search over\n")
  cat("    VALUES needs a second pass with append_values_string(). PARTLY.\n")
}

cat("
CONCLUSION. Written after the run and corrected against what printed.

THE PREDICTION WAS WRONG AND IT WAS WRONG IN THE INTERESTING DIRECTION. This
attempt was written expecting `json_structure()` to fail or hang: it won entry
28 at 10,137 nodes and this document has 83x that. It COMPLETED — see the Q12
line above for this run's wall clock — and the scaling probe explains why: the
log-log slope is well BELOW 1, which is sublinear. The verb does not degrade
with size the way one row per node suggests it must.

SO THE SCALING TEST BUILT INTO THIS FILE FOUND THE OPPOSITE OF WHAT IT WAS
BUILT FOR, and it is kept exactly as written because its extrapolation lands
within a factor of about two of the time actually measured. A guess that was
checked is worth more than a guess that was not.

THE TIMES AND THE SLOPE ARE DELIBERATELY NOT REPEATED IN THIS PROSE. They move
by ten percent or more between runs on the same machine — 53.7 s and slope 0.77
on the first run, 58.2 s and 0.67 on the second — and a figure typed into a
conclusion is a figure that goes stale the next time anyone runs the file. The
printed output above is the record.

WHAT IT COSTS is roughly fifty seconds against rrapply's 0.4, a factor of over
a hundred. Both are one call and neither needs the shape in advance. rrapply is
the one to reach for; tidyjson is the one whose output answers more questions.

BECAUSE IT KEEPS `type` AS A COLUMN, IT ANSWERS QUESTION 5. That is the
question this document was chosen for, and it separates tidyjson and jq from
rrapply, whose melt coerces the same field to character silently.

WHAT IT DOES NOT KEEP is the VALUE. `json_structure()` gives the shape and not
the contents, so question 11 needs a second pass. rrapply's melt carries both.
Neither tool gives both the type and the value in one call, which is a real gap
and not a preference.
")
