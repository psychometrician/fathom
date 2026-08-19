# jqr — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/r && Rscript try-jqr.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# ⚠ **THIS FILE USES THE CORRECTED LEAF EXPRESSION AND SAYS SO LOUDLY.**
#
#     paths(scalars)                                   <- WRONG, drops false and null
#     path(.. | select(type != "object" and type != "array"))   <- correct
#
# `select` emits its input when the FILTER'S OUTPUT is truthy, and `scalars`
# returns the value itself — so a leaf that IS `false` or `null` fails its own
# filter and vanishes silently. That defect was found on 2026-08-13 and repaired
# across 40 sites in 24 entries.
#
# **This document is the corpus's most exposed and that is why it is stated
# here rather than in a footnote**: it is measured below, and the broken idiom
# is what a reader would otherwise copy out of an older attempt file.

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("jqr %s · jsonlite %s · jq %s · R %s.%s\n",
            packageVersion("jqr"), packageVersion("jsonlite"),
            tryCatch(jq_version(), error = function(e) "?"),
            R.version$major, R.version$minor))

raw <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)
cat(sprintf("read: %s bytes\n", format(nchar(raw, type = "bytes"), big.mark = ",")))

cat("\nQ0  jq parsed and said nothing. Duplicate keys: last wins, silently. CANNOT.\n")

secs <- function(expr) {
  t0 <- Sys.time()
  v <- force(expr)
  attr(v, "secs") <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
  v
}

# ── Q1/Q2. keys, and depth by leaf path length. ──────────────────────────────
top <- jq(raw, "keys")
cat(sprintf("\nQ1  jq 'keys' -> %s\n", top))
cat("    ONE LEVEL, and every deeper level costs another expression.\n")

# ── THE MEASUREMENT THE WARNING ABOVE IS ABOUT. ──────────────────────────────
t0 <- Sys.time()
n_broken <- as.integer(jq(raw, "[paths(scalars)] | length"))
s_broken <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
t0 <- Sys.time()
n_right <- as.integer(jq(raw,
  '[path(.. | select(type != "object" and type != "array"))] | length'))
s_right <- as.numeric(difftime(Sys.time(), t0, units = "secs"))

cat("\n── the broken idiom, measured on the document it hurts most ─────────────\n")
cat(sprintf("  paths(scalars)                       %s leaves  (%.1f s)\n",
            format(n_broken, big.mark = ","), s_broken))
cat(sprintf("  path(.. | select(type != obj/arr))   %s leaves  (%.1f s)\n",
            format(n_right, big.mark = ","), s_right))
cat(sprintf("  DROPPED SILENTLY: %s leaves, %.2f%% of the document\n",
            format(n_right - n_broken, big.mark = ","),
            100 * (n_right - n_broken) / n_right))

by_type <- jq(raw,
  '[.. | select(type != "object" and type != "array")] | group_by(type)
   | map({type: .[0] | type, n: length}) | from_entries? // .')
cat(sprintf("  leaves by type: %s\n", by_type))

cat(sprintf("\nQ7  %s leaves. yes, with the CORRECT expression.\n",
            format(n_right, big.mark = ",")))

# ── Q2. depth. ───────────────────────────────────────────────────────────────
d <- as.integer(jq(raw,
  '[path(.. | select(type != "object" and type != "array")) | length] | max'))
cat(sprintf("\nQ2  %d. yes — max leaf path length.\n", d))

# ── Q5. THE TRI-TYPED FIELD. ─────────────────────────────────────────────────
va <- jq(raw, '[.. | objects | select(has("version_added")) | .version_added | type]
               | group_by(.) | map({(.[0]): length}) | add')
cat(sprintf("\nQ5  version_added by JSON type: %s\n", va))
cat("    YES, and jq is one of the few that can say so — `type` is a first-class\n")
cat("    function, so the polymorphism is directly askable rather than inferred.\n")

# ── Q6. keys as data. ────────────────────────────────────────────────────────
cat("\nQ6  jq can COUNT keys but has no notion of a key being data:\n")
kc <- jq(raw, '{api: (.api | keys | length), browsers: (.browsers | keys | length),
                css_properties: (.css.properties | keys | length)}')
cat(sprintf("      %s\n", kc))
cat("    CANNOT — those counts are mine to interpret, and the threshold is mine.\n")

# ── Q11. URLs, and the FOLD question. ────────────────────────────────────────
t0 <- Sys.time()
nu <- as.integer(jq(raw,
  '[.. | select(type == "string") | select(test("^https?://"))] | length'))
cat(sprintf("\nQ11 %s URL values in %.1f s. YES.\n",
            format(nu, big.mark = ","),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))

# The paths, and then the SHAPES — jq can do the fold, if you tell it where.
up <- jq(raw,
  '[path(.. | select(type == "string") | select(test("^https?://")))
    | map(tostring) | join(".")] | unique | length')
cat(sprintf("    distinct literal URL paths: %s — one per value, no folding\n", up))

us <- jq(raw,
  '[path(.. | select(type == "string") | select(test("^https?://")))
    | map(tostring) | join(".")] | map(gsub("\\\\.[^.]*\\\\.__compat"; ".<key>.__compat"))
   | unique | length')
cat(sprintf("    after ONE hand-written gsub folding the level above __compat: %s\n", us))
cat("    jq CAN fold. It cannot decide WHAT to fold, and the regex is mine.\n")

cat("
CONCLUSION. Written after the run and corrected against what printed.

THE BROKEN IDIOM COSTS 90,624 LEAVES HERE, 19.25% of the document, and this is
the corpus's worst case by a wide margin. It is confirmed rather than assumed:
paths(scalars) returns 380,049 and the corrected expression returns 470,673.

AND THE REASON IS VISIBLE IN THE TYPE BREAKDOWN. Every leaf in this 19.9 MB
document is a string or a boolean — 353,345 and 117,328 — and there are NO
numbers and NO nulls anywhere. So `false` is not an edge case here, it is a
quarter of the data, and an expression that drops booleans drops a quarter of
the file while looking like it worked.

jq IS THE BEST ANSWER TO QUESTION 5 IN EITHER LANGUAGE. `type` is a first-class
function, so `group_by(type)` answers `does this field change type` directly:
version_added is 228,083 strings and 57,103 booleans. rrapply's melt silently
coerces exactly this field to character; jq is asked and answers.

IT IS ALSO FAST. Full-document scans in 0.8 to 1.0 seconds on 19.9 MB, which is
faster than anything else in the R half including the parse most of them need.

WHAT IT CANNOT DO IS DECIDE. jq folds when told to: one gsub over the paths
collapses the level above __compat and takes 35,392 literal URL paths down to
7,243. rrapply's melt with a >40-distinct-keys rule takes the same URLs to 176.
BOTH NUMBERS ARE HAND-MADE AND THEY DISAGREE BY 41x, which is the whole point:
the answer to `where do the URLs live` depends entirely on what you chose to
fold, and no tool in the fourteen chooses. fathom chooses and gets 11,320,
which is defect 36 — but choosing badly and not choosing are different failures,
and only one of them can be improved.

Q3 and Q6 remain CANNOT, for the 29th entry running.
")
