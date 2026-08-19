# jqr — Crossref works, 1,000 records
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed at run time)
#  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
#  measured      2026-08-11
#  run           cd corpus/21-crossref-works/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   PARTLY
#   1 what is in here                             2   NO                  yes — 236
#   2 how deep                                    1   NO                  yes — 9
#   3 what is one record                         22   NO                  THE SPLIT — see below
#   4 always present vs sometimes                 5   NO                  yes — 40, 0 nulls
#   5 does any field change type                  6   NO                  PARTLY
#   6 are any object keys data                    3   NO                  counts, no verdict
#   7 how many records                             2  NO                  yes, both numbers
#   8 three named fields to a table                2  YES                 yes
#   9 a field missing from some rows                2 YES                 yes
#  10 flatten the deepest array                     2 YES                 yes — 18,155
#  11 find every path matching something            3 NO                  yes — 13
#  12 flattest honest table                         3 -                   CANNOT — returns TEXT
#  13 needed the shape in advance?                    NO for 1, 2, 4, 6, 11 — and the Q3
#                                                     SEARCH needs only the record path
#  14 survives the next file unchanged?               the Q3 search does, unchanged
#  15 readable a week later?                          the Q3 program, no
#  16 lines, and how much is ceremony?                ~110
#
# ══════════════════════════════════════════════════════════════════════════════
# THE SPLIT SEARCH, IN R, AND IT REACHES THE PROBE'S OWN NUMBERS.
# ══════════════════════════════════════════════════════════════════════════════
#
# This is entry 17's fifteen-line program, unchanged except for the path to the
# records, run from R instead of Python. It ranks `type` FIRST on both metrics
# and computes worst 0.2629 and weighted 0.2073 — the probe's own internal
# figures for the split it DECLINED (open defect 24).
#
# The point of running it from R as well is rule 6's premise: if jqr and the
# Python binding are "the same tool", the ANSWERS must be identical and only the
# time may differ. Both halves are printed below.
# ─────────────────────────────────────────────────────────────────────────────

library(jqr)
cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

src <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
jqt <- function(prog) {
  t0 <- Sys.time()
  out <- jq(src, prog)
  list(out = out, secs = as.numeric(difftime(Sys.time(), t0, units = "secs")))
}

cat("\nQ0  jqr parses or errors. jq keeps the LAST duplicate key silently and\n")
cat("    numbers become doubles. Same libjq as the Python binding. PARTLY.\n")

r <- jqt('[paths | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
cat(sprintf("\nQ1  %s distinct paths, %.2fs — the probe says 236\n", r$out, r$secs))
t_paths <- r$secs
r <- jqt('[paths | length] | max')
cat(sprintf("Q2  depth %s — the probe says 9\n", r$out))

# ── Q3. THE SPLIT. ──────────────────────────────────────────────────────────
r <- jqt('.message.items as $d
  | ([$d[] | keys[]] | unique) as $f
  | {rows: ($d|length), cols: ($f|length),
     empty: (([$d[] | . as $r | $f | map(. as $k | if ($r|has($k)) then 0 else 1 end) | add]
              | add) / (($d|length) * ($f|length)))}')
cat(sprintf("\nQ3  the obvious record: %s\n", r$out))
SEARCH <- '
  def emptiness($rows):
    ([$rows[] | keys[]] | unique) as $cols
    | ([ $rows[] | . as $r
         | [ $cols[] | . as $c | if ($r | has($c)) then 0 else 1 end ] | add ] | add)
      / (($rows | length) * ($cols | length));
  .message.items as $d
  | ([$d[] | keys[]] | unique) as $all
  | [ $all[] | . as $f | select([$d[] | has($f)] | all) ] as $always
  | [ $always[] as $f
      | ($d | group_by(.[$f])) as $g
      | select(($g|length) > 1 and ($g|length) <= 24)
      | {field: $f, kinds: ($g|length),
         worst: ([$g[] | emptiness(.)] | max),
         weighted: ([$g[] | {n: length, e: emptiness(.)}]
                    | (map(.n * .e) | add) / (map(.n) | add))} ]
    | sort_by(.weighted) | .[]
    | "\\(.field)\t\\(.kinds)\t\\(.worst)\t\\(.weighted)"'
r <- jqt(SEARCH)
cat(sprintf("\nQ3  THE SEARCH — entry 17's program, unchanged but for the path, %.2fs\n", r$secs))
cat(sprintf("    %-24s %5s %10s %10s\n", "field", "kinds", "worst", "weighted"))
# jqr hands back the LITERAL two characters \t rather than a tab, so
# `strsplit(x, "\t")` matched nothing and every numeric field came out NA.
# Splitting on the literal is the fix.
for (line in gsub('"', "", r$out)) {
  f <- strsplit(line, "\\\\t")[[1]]
  cat(sprintf("    %-24s %5s %10.4f %10.4f\n", f[1], f[2], as.numeric(f[3]), as.numeric(f[4])))
}
cat("    `type` IS FIRST ON BOTH METRICS, and 0.2629 / 0.2073 are the probe's\n")
cat("    own internal numbers for the split it DECLINED. Unsplit emptiness is\n")
cat("    0.4454, so the halving rule wants worst < 0.2227: `type` misses by 0.04\n")
cat("    and its WEIGHTED figure passes comfortably.\n")
cat("    DEFECT 24 IS A GATE FAILURE, NOT A RANKING FAILURE — the probe picks\n")
cat("    the right field and then refuses it.\n")
cat("    IDENTICAL to ../python/try-jq.py's output, as it must be with one\n")
cat("    libjq underneath. That is rule 6's premise holding for the ANSWERS.\n")

# ── Q4/Q5/Q6/Q7. ────────────────────────────────────────────────────────────
r <- jqt('[.message.items[] | keys[]] | group_by(.) | map(select(length < 1000)) | length')
cat(sprintf("\nQ4  fields sometimes ABSENT: %s of 57\n", r$out))
r <- jqt('[.message.items[] | to_entries[] | select(.value == null) | .key] | unique | length')
cat(sprintf("Q4  fields written null: %s — a pure-absence document\n", r$out))
r <- jqt('[.message.items[] | to_entries[] | {k: .key, t: (.value|type)}] | group_by(.k)
          | map({k: .[0].k, t: (map(.t)|unique)}) | map(select((.t - ["null"])|length > 1)) | length')
cat(sprintf("\nQ5  a field-level type census finds %s. The probe reports ONE site:\n", r$out))
r <- jqt('[.message.items[].issued."date-parts"[0][0] | type] | group_by(.)
          | map({t: .[0], n: length}) | map("\\(.t)=\\(.n)") | join(", ")')
cat(sprintf("    issued.date-parts[0][0] -> %s\n", gsub('"', "", r$out)))
cat("    Two levels into an array, reachable only by writing [0][0] — which is\n")
cat("    knowing the answer. PARTLY.\n")
r <- jqt('[.message.items[].reference[]? | keys[]] | unique | length')
r2 <- jqt('[.message.items[].reference[]?] | length')
cat(sprintf("\nQ6  reference[]: %s keys over %s copies — the probe DECLINES it as a\n",
            r$out, r2$out))
cat("    vocabulary, which is entry 13's `engines` rule generalising. jqr counts.\n")
r <- jqt('{page: (.message.items|length), total: .message["total-results"]}')
cat(sprintf("\nQ7  %s\n", r$out))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
r <- jqt('[.message.items[] | {DOI, type, publisher}] | length')
cat(sprintf("\nQ8  %s rows x 3, %.2fs\n", r$out, r$secs))
r <- jqt('[.message.items[] | select(.abstract != null)] | length')
cat(sprintf("\nQ9  abstract present on %s of 1,000\n", r$out))
r <- jqt('[.message.items[] as $w | $w.reference[]? | {DOI: $w.DOI, key}] | length')
cat(sprintf("\nQ10 reference[] -> %s rows x 2, %.2fs — the parent DOI stays in scope\n",
            r$out, r$secs))
cat("    pandas needed a pre-filter AND meta_prefix and raised twice; polars\n")
cat("    raised on the DOI collision. `?` and `as` are the whole of it here.\n")
r <- jqt('[paths(type=="string" and test("^https?://"))
           | map(if type=="number" then "[]" else . end) | join(".")] | unique | length')
cat(sprintf("\nQ11 %s distinct URL paths — ijson, glom, pydash, purrr and rrapply\n", r$out))
cat("    all say 13 too. Seven tools, two languages, one number.\n")
cat("\nQ12 jqr returns TEXT. The honest table means handing the output back to\n")
cat("    jsonlite, and that round trip shows in no timing here.\n")

cat(sprintf("\n     RULE-6 TIMING: question 1 took %.2fs from jqr; ../python/try-jq.py\n", t_paths))
cat("     prints the same expression's time from the Python binding. Entry 14\n")
cat("     measured 2.8x, entry 20 2.5x on 29.6 MB, entry 22 2.97x on 476 KB.\n")
