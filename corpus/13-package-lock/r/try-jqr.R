# jqr — an npm lockfile, 1,657 packages keyed by install path
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (version printed at run time)
#  file          ../source.json   759 KB, 1,657 packages, depth 5
#  measured      2026-08-11
#  run           cd corpus/13-package-lock/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             6   NO                  YES — 16,545 exactly
#   2 how deep                                    2   NO                  YES — exactly 5
#   3 what is one record                          6   NO                  PARTLY — 144 with `sort`
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  4   NO                  YES — exactly the probe
#   6 are any object keys data                    6   -                   PARTLY — best in R
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               3   YES                 yes — to_entries
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          5   NO                  YES — best in R
#  12 flattest honest table                       4   YES                 yes
#  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
#  14 survives the next file unchanged?               yes for all of those
#  15 readable a week later?                          the Q1 reduce does not
#  16 lines, and how much is ceremony?                ~110, and the programs are the intent
#
# **jqr IS 2.8x FASTER THAN THE PYTHON `jq` BINDING ON THIS FILE, WHICH IS THE
# SAME RATIO `14-nyc-311` MEASURED ON A DOCUMENT 37x LARGER.** Identical program,
# identical answer, best of three runs each:
#
#     question 1, `paths` ....... jqr  0.085 s    python jq  0.236 s
#
# Entry 14 got 3.6 s against 9.9 s on 28 MB — **2.8x there, 2.8x here.** It also
# tested and rejected the obvious explanation: `input_text()` on the raw string
# is no faster than passing a parsed object. Two documents, three orders of
# magnitude apart in size, one constant factor. The cause is still open and it
# is not conversion overhead.
#
# **jq'S PATHS ARE ARRAYS AND THAT IS WHAT SAVES IT HERE.** `paths` yields
# `["packages", "node_modules/@nodelib/fs.scandir", "resolved"]` as three kept-
# apart segments. pandas' column names and ijson's prefixes are **dot-joined
# strings**, and 33 of this document's package keys contain a dot, so neither can
# be split back into the path that made it — measured in `../python/try-ijson.py`,
# where `resolved` comes out 1,623 against a true 1,656.
#
# **IT REPRODUCES FOUR OF THE PROBE'S NUMBERS EXACTLY** — 16,545 paths, depth 5,
# 144 key-sets and both polymorphic fields with their counts.
#
# **AND `sort` IS THE DIFFERENCE BETWEEN 144 AND 152.** `keys_unsorted|join(",")`
# gives 152 because 8 packages carry the same fields in another order. DuckDB's
# `json_keys(...)::VARCHAR` is that same unsorted form and reports 152 too.
#
# **QUESTION 6 IS WHERE IT STOPS.** `keys`, `to_entries` and `paths` give every
# ingredient and jqr computes no verdict: it will not tell you `packages` is
# keyed by data while `engines` — 5 keys over 1,050 copies — is a vocabulary.
# The probe prints seven keyed sites and declines exactly that eighth.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("R %s, jqr %s, jsonlite %s (system jq: %s)\n",
            getRversion(), packageVersion("jqr"), packageVersion("jsonlite"),
            tryCatch(system("jq --version", intern = TRUE), error = \(e) "not on PATH")))

txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)
cat(sprintf("    read %.0f KB of text\n", nchar(txt) / 1024))

run <- function(program, label) {
  t0 <- Sys.time()
  out <- jq(txt, program)
  cat(sprintf("    [%5.2fs] %s\n", as.numeric(Sys.time() - t0, units = "secs"), label))
  out
}

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  jqr hands the text to libjq, which errors on malformed JSON and says\n")
cat("    nothing about duplicate keys, big integers or NaN. DuckDB REFUSES this\n")
cat("    file over its empty-string key; libjq is untroubled. CANNOT.\n")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
cat("\nQ1  paths, with array indices folded to []:\n")
n_raw <- fromJSON(run('[paths | map(if type == "number" then "[]" else . end)
                        | join(".")] | unique | length', "..."))
cat("   ", format(n_raw, big.mark = ","), "— THE PROBE PRINTS 16,545. Exact.\n")
cat("    And that number is the failure, not the answer: 16,545 paths for a\n")
cat("    document with about 49 real ones, because every install path and every\n")
cat("    dependency name is its own path. jq's paths are ARRAYS, though, so the\n")
cat("    fold is expressible — pandas and ijson dot-join and cannot recover.\n")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
cat("\nQ2  max path length:\n")
cat("   ", fromJSON(run("[paths | length] | max", "...")),
    "— the probe prints '5 levels deep'. Exact.\n")

# ── Q3/Q7. What is one record, and how many. AND THE `sort` WARNING. ─────────
cat("\nQ3  distinct key-sets over the 1,657 packages, two ways:\n")
unsorted <- fromJSON(run('[.packages[] | keys_unsorted | join(",")] | unique | length',
                         "keys_unsorted"))
sorted_ <- fromJSON(run('[.packages[] | keys_unsorted | sort | join(",")] | unique | length',
                        "with sort"))
cat("    keys_unsorted ->", unsorted, "\n")
cat("    with sort     ->", sorted_, "  <- THE PROBE PRINTS 144\n")
cat("   ", unsorted - sorted_, "packages carry the same fields in a different ORDER.\n")
cat("    DuckDB's json_keys(...)::VARCHAR is the unsorted form and returns 152\n")
cat("    for exactly this reason. One word, and nothing says which you meant.\n")
cat("    jqr still names no row candidate and prices none. PARTLY.\n")
cat("Q7 ", fromJSON(jq(txt, ".packages | length")), "packages\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
cat("\nQ4  field counts:\n")
counts <- fromJSON(run('[.packages[] | keys_unsorted[]] | group_by(.)
                        | map({(.[0]): length}) | add', "..."))
n <- 1657
cat("   ", length(counts), "fields · always", sum(unlist(counts) == n),
    "·", names(counts)[unlist(counts) == n], "\n")
cat("    sometimes", sum(unlist(counts) < n), ", rarest five:\n")
print(head(sort(unlist(counts)), 5))

# ── Q5. Does any field change type between records. ──────────────────────────
cat("\nQ5  fields whose type varies across the packages:\n")
varying <- fromJSON(run('[.packages[] | to_entries[] | {k: .key, t: (.value | type)}]
      | group_by(.k)
      | map(select((map(.t) | unique | length) > 1)
            | {(.[0].k): (map(.t) | group_by(.) | map({(.[0]): length}) | add)})
      | add', "..."))
print(varying)
cat("    EXACTLY THE PROBE. jq groups by KEY rather than by path, which is what\n")
cat("    makes this answerable — ijson groups by prefix and reports ZERO here,\n")
cat("    because each package's `engines` sits at its own prefix.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  jqr gets closer than anything else in R and still computes no verdict.\n")
kv <- fromJSON(run('[.packages | keys[]] | length', "keys of packages"))
eng <- fromJSON(run('[.packages[].engines? | objects | keys[]] | unique | length',
                    "distinct engine keys"))
cat("    packages has", format(kv, big.mark = ","), "keys, each occurring once -> DATA\n")
cat("    engines has", eng, "distinct keys over 1,050 copies -> A VOCABULARY\n")
cat("    The probe prints seven keyed sites and DECLINES `engines` by name.\n")
cat("    PARTLY: every ingredient, no verdict.\n")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
cat("\nQ8  three fields, keyed by install path:\n")
tbl <- fromJSON(run('[.packages | to_entries[] | {path: .key, version: .value.version,
                      license: .value.license}]', "..."))
cat("   ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cat("    `to_entries` KEEPS THE INSTALL PATH as data. jmespath's `values()`\n")
cat("    throws it away, and on a keys-as-data document that is the row's identity.\n")
cat("\nQ9  a field missing from some packages:\n")
q9 <- fromJSON(run('[.packages[] | {version, license}]', "..."))
cat("   ", nrow(q9), "rows kept,", sum(is.na(q9$license)), "NA\n")
cat("    Object construction fills absent keys with null and KEEPS the row.\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
cat("\nQ10 funding[], object-or-array with string-or-object elements:\n")
fund <- fromJSON(run('[.packages | to_entries[] | select(.value.funding | type == "array")
                      | .key as $p | .value.funding[]
                      | if type == "string" then {pkg: $p, url: .}
                        else {pkg: $p} + . end]', "..."))
cat("   ", nrow(fund), "rows\n"); print(head(fund[, c("pkg", "type")], 2))

# ── Q11. Find every path whose value matches something. ──────────────────────
cat("\nQ11 URL-valued paths, folded on the packages key:\n")
urls <- fromJSON(run('[paths(type == "string" and test("https?://")) | . as $p
      | reduce range(0; length) as $i ([];
          . + [ if ($i > 0 and ($p[$i-1] | tostring) == "packages") then "<key>"
                elif ($p[$i] | type) == "number" then "[]"
                else $p[$i] end ])
      | join(".")] | group_by(.) | map({(.[0]): length}) | add', "..."))
print(unlist(urls))
cat("    ", sum(unlist(urls)), "values over", length(urls), "paths — the truth, and it matches\n")
cat("    the probe's folding. purrr and jsonlite each need 9-13 lines of\n")
cat("    hand-written recursion for the same answer; ijson's dot-joined prefixes\n")
cat("    produce 47 paths, 42 of them invented. Best question 11 in R.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12 the honest table, with the six keyed collections removed:\n")
flat <- fromJSON(run('[.packages | to_entries[] | {path: .key}
                      + (.value | del(.dependencies, .devDependencies,
                         .optionalDependencies, .peerDependencies,
                         .peerDependenciesMeta, .bin))]', "..."))
cat("   ", nrow(flat), "x", ncol(flat), "\n")
cat("    `del` makes the exclusion one clause and the path survives as a column.\n")
cat("    pandas, rrapply's bind and tidyjson's spread_all all build the 1,390-\n")
cat("    column version instead, at 99% empty, without warning. The six\n")
cat("    collections are separate tables the probe prices at 2,841, 128, 104,\n")
cat("    101, 78 and 25 rows — and jqr will not name them either.\n")
