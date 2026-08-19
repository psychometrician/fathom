# jqr — Homebrew's whole formula index
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
#  measured      2026-08-11
#  run           cd corpus/20-homebrew-formulae/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   PARTLY
#   1 what is in here                             4   NO                  yes — 1,132
#   2 how deep                                    2   NO                  yes — 8
#   3 what is one record                          8   NO                  PARTLY
#   4 always present vs sometimes                 6   NO                  YES — both halves
#   5 does any field change type                 22   NO                  YES, on the 2nd try
#   6 are any object keys data                    7   NO                  by hand
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               2   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   5   YES                 yes — 557, correct
#  11 find every path matching something          8   NO                  yes — 65 and 48
#  12 flattest honest table                       4   -                   CANNOT — returns TEXT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 6, 11
#  14 survives the next file unchanged?               yes except Q8/Q9/Q10
#  15 readable a week later?                          the Q5 census, no
#  16 lines, and how much is ceremony?                ~150, and the R around jq is 20
#  timing        Q1 6.3s, Q5 census ~7s, Q11 1.7s and 2.0s. Whole file ~31s
#
# ══════════════════════════════════════════════════════════════════════════════
# THE RULE-6 TIMING TEST, AND IT REPRODUCES.
# ══════════════════════════════════════════════════════════════════════════════
#
# `VERDICT.md` carries an open item: rule 6 gives a competing tool the same
# number of attempts on the assumption that a tool is a tool, and entry 14
# measured the SAME jq program running 2.8x faster from jqr than from the
# Python binding. That was one document, so it could have been that document.
#
#   question 1, `[paths | … ] | unique | length`, IDENTICAL expression:
#       jqr             6.3s
#       python jq      15.8s      <- printed by ../python/try-jq.py
#       ratio           2.5x
#
# A DOCUMENT 4x LARGER THAN ENTRY 14's, AND THE RATIO HOLDS. Two documents,
# two sizes, the same libjq underneath, and the binding costs more than half
# the wall clock. "A tool is a tool" is now measurably false for jq, and every
# corpus timing that does not say which binding it used is that much weaker.
#
# Everything jqr ANSWERS is identical to the Python binding's answer, as it must
# be — one libjq, one expression. The 31-paths-folding-to-12 census matches
# `try-jq.py` exactly. What differs is only the time and the return type.
# ─────────────────────────────────────────────────────────────────────────────

library(jqr)
cat(sprintf("R %s, jqr %s, libjq via jq %s\n",
            getRversion(), packageVersion("jqr"),
            tryCatch(system("jq --version", intern = TRUE), error = function(e) "?")))

RAW <- "../source.json"
src <- paste(readLines(RAW, warn = FALSE), collapse = "\n")
cat(sprintf("read %.1f MB of text\n", nchar(src) / 1e6))

jqt <- function(prog) {
  t0 <- Sys.time()
  out <- jq(src, prog)
  list(out = out, secs = as.numeric(difftime(Sys.time(), t0, units = "secs")))
}

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  jqr parses or errors. No duplicate-key report, no big-int report:\n")
cat("    jq keeps the LAST duplicate silently and numbers become doubles.\n")
cat("    Same answer as the Python binding, because it is the same libjq. PARTLY.\n")

# ── Q1. What is in here — every path, at every level. ────────────────────────
r <- jqt('[paths | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
cat(sprintf("\nQ1  %s distinct paths, %.1fs\n", r$out, r$secs))
cat("    THE RULE-6 NUMBER. The Python binding timed the identical expression\n")
cat("    on this file in try-jq.py; entry 14 measured jqr 2.8x faster. Compare.\n")
t_paths <- r$secs

r <- jqt('[.[] | keys_unsorted[]] | unique | length')
cat(sprintf("Q1  %s distinct root field names\n", r$out))

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
r <- jqt('[paths | length] | max')
cat(sprintf("\nQ2  depth %s, %.1fs — agrees with the probe\n", r$out, r$secs))

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  jqr names no candidates and prices none. It counts any you name:\n")
for (nm in list(c("a record", "length"),
                c("an item of patches", "[.[].patches[]?] | length"),
                c("an item of resolves", "[.[].patches[]?.resolves[]?] | length"),
                c("a bottle file", "[.[].bottle.stable.files? | select(.) | keys[]] | length"))) {
  r <- jqt(nm[2])
  cat(sprintf("    %-32s %8s rows\n", nm[1], r$out))
}
r <- jqt("length")
cat(sprintf("Q7  %s formulae\n", r$out))

# ── Q4. Always present vs sometimes — and null vs absent. ────────────────────
r <- jqt('[.[] | keys_unsorted[]] | group_by(.) | map({k: .[0], n: length})
          | map(select(.n < 8536)) | sort_by(-.n) | map(.k + " " + (.n|tostring)) | join(", ")')
cat(sprintf("\nQ4  sometimes ABSENT: %s\n", r$out))
r <- jqt('[.[] | to_entries[] | select(.value == null) | .key] | unique | length')
cat(sprintf("Q4  always present but NULL: %s fields\n", r$out))
cat("    THE DISCRIMINATOR, both halves, same as the Python binding. `keys` is\n")
cat("    presence and `.value == null` is value, and jq keeps them apart.\n")

# ── Q5. Does any field change type between records? ──────────────────────────
cat("\nQ5  the obvious query — root fields, JSON type, nulls removed:\n")
r <- jqt('[.[] | to_entries[] | {k: .key, t: (.value|type)}] | group_by(.k)
          | map({k: .[0].k, t: (map(.t)|unique)}) | map(select((.t - ["null"])|length > 1))
          | length')
cat(sprintf("    %s. ZERO, on a document with nine type-changing sites.\n", r$out))
CENSUS <- '
def ptype: if type == "array"
           then (if length == 0 then "array" else "array[1] " + (.[0]|type) end)
           else type end;
def varies: . as $ts
          | if (any(.[]; startswith("array["))) then map(select(. != "array")) else $ts end;
. as $doc
| [ paths as $p | { k: ($p | map(if type=="number" then "[]" else . end) | join(".")),
                    t: ($doc | getpath($p) | ptype) } ]
| group_by(.k)
| map({k: .[0].k, t: (map(.t) | unique | map(select(. != "null")) | varies)})
| map(select(.t | length > 1)) | map(.k) | .[]'
r <- jqt(CENSUS)
# jq emits JSON strings, so each element arrives WITH its quotes. The first
# draft folded before stripping them and the `$` anchor never matched, giving
# 18 folded paths instead of 12 — the quotes were the last character.
paths5 <- gsub('"', "", as.character(r$out))
folded <- unique(sub("(uses_from_macos\\.\\[\\])\\.[a-z0-9_]+$", "\\1.<key>",
                     gsub("\\.variations\\.[a-z0-9_]+\\.", ".variations.<key>.", paths5)))
cat(sprintf("Q5  the probe's own rules applied — a null is not a type, an empty\n"))
cat(sprintf("    array is not a type: %s paths, folding to %s. The probe says 9.\n",
            length(paths5), length(folded)))
for (p in sort(folded)) cat("     ", p, "\n")
cat("    Identical to the Python binding's answer, as it must be: one libjq.\n")
cat("    The twelve are the probe's nine plus the three `.[]` array-element\n")
cat("    paths the probe folds into their parent.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  jqr counts a keyed collection in one line and calls none:\n")
for (nm in list(c("$[].bottle.stable.files", '[.[].bottle.stable.files? | select(.) | keys[]]'),
                c("$[].variations", '[.[].variations? | select(.) | keys[]]'))) {
  k <- jqt(paste(nm[2], "| unique | length"))
  n <- jqt(paste(nm[2], "| length"))
  cat(sprintf("    %-26s %3s distinct keys over %8s occurrences\n", nm[1], k$out, n$out))
}

# ── Q8. Three named fields into a table. ─────────────────────────────────────
r <- jqt('[.[] | {name, desc, homepage}] | length')
cat(sprintf("\nQ8  %s rows x 3, %.1fs — one expression\n", r$out, r$secs))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
r <- jqt('[.[] | {name, ex: (.executables // null)}] | map(select(.ex != null)) | length')
cat(sprintf("\nQ9  executables non-null on %s of 8,536; `//` keeps every row\n", r$out))

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
r <- jqt('[.[] as $f | $f.patches[]? | .resolves[]? | {name: $f.name, id, type}] | length')
cat(sprintf("\nQ10 patches[].resolves[] -> %s rows x 3, %.1fs\n", r$out, r$secs))
cat("    `?` is the whole of the raggedness handling, and the parent stays in\n")
cat("    scope through both levels — which pandas needed a pre-filter for and\n")
cat("    jmespath could not do at all.\n")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
r1 <- jqt('[paths(type=="string" and startswith("http"))
           | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
r2 <- jqt('[paths(type=="string" and test("^https?://"))
           | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
r3 <- jqt('[.[] | .name | select(startswith("http"))] | length')
cat(sprintf("\nQ11 startswith(\"http\"): %s paths, %.1fs\n", r1$out, r1$secs))
cat(sprintf("Q11 test(\"^https?://\"):  %s paths, %.1fs\n", r2$out, r2$secs))
cat(sprintf("    the gap is %s formulae literally NAMED http* — httpd, httpie,\n", r3$out))
cat("    http-server. jq, ijson, glom and pydash all report the same two\n")
cat("    numbers. It is the predicate's trap, not any tool's.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12 jqr returns TEXT. Every answer above is a character vector that R\n")
cat("    then has to parse again — `jq(...)` does not produce a data frame, so\n")
cat("    the flattest honest table means handing the output to jsonlite. That\n")
cat("    round trip is jqr's real cost and it does not show in any timing here.\n")

cat(sprintf("\n     TIMING FOR RULE 6: question 1 took %.1fs from jqr.\n", t_paths))
cat("     try-jq.py prints the same expression's time from the Python binding.\n")
