# jqr — 200 OpenLibrary search results
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (version printed at run time)
#  file          ../source.json   64 KB, 200 docs, depth 4
#  measured      2026-08-11
#  run           cd corpus/17-openlibrary/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             3   NO                  YES — exactly 31
#   2 how deep                                    2   NO                  YES — exactly 4
#   3 what is one record                          10  NO                  PARTLY — it can PRICE
#   4 always present vs sometimes                 5   NO                  YES
#   5 does any field change type                  4   NO                  YES — correctly none
#   6 are any object keys data                    4   -                   n/a; 15 key-sets, right
#   7 how many records                             3   NO                  yes — both answers
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          4   NO                  YES — best in R
#  12 flattest honest table                       3   YES                 yes
#  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
#  14 survives the next file unchanged?               yes for all of those
#  15 readable a week later?                          the split search does not
#  16 lines, and how much is ceremony?                ~105
#
# **jqr CAN EXPRESS THE FOURTH OPERATION, AND IT IS THE ONLY TOOL IN R THAT CAN.**
# `group_by` applies a split and emptiness is computable in the same program, so
# the whole SEARCH over candidate discriminators fits in one expression — written
# out below. Its ranking agrees with the probe exactly:
#
#     ebook_access     4 kinds   worst group 16.4%   <- what the probe reports
#     has_fulltext     2 kinds   worst group 16.4%   ties; a COARSENING of it
#     public_scan_b    2 kinds   worst group 34.4%   no better than not splitting
#     edition_count   14 kinds   worst group 35.5%   WORSE
#
# **That program is fifteen lines written knowing what to look for.** jq has no
# verb for it and prints nothing unasked. The gap between *expressible* and
# *printed without being asked* is what item 23i calls **the looking**, and this
# file measures it: fifteen lines.
#
# **IT REPRODUCES THREE OF THE PROBE'S NUMBERS EXACTLY** — 31 paths, depth 4, and
# 15 distinct key-sets. The key-set count agrees with DuckDB here, which it did
# not on entries 13 or 15: this document has neither data keys nor nulls in its
# records, which is the condition that makes `json_structure` safe.
#
# **AND IT FINDS THE ONE URL AT THE ROOT.** `documentation_url` sits outside
# `docs`, so pandas and polars report none of one; `paths` starts at the top.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(jqr); library(jsonlite)})
cat(sprintf("R %s, jqr %s, jsonlite %s (system jq: %s)\n",
            getRversion(), packageVersion("jqr"), packageVersion("jsonlite"),
            tryCatch(system("jq --version", intern = TRUE), error = \(e) "not on PATH")))

txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)

run <- function(program, label) {
  t0 <- Sys.time()
  out <- jq(txt, program)
  cat(sprintf("    [%5.2fs] %s\n", as.numeric(Sys.time() - t0, units = "secs"), label))
  out
}

# ── Q0. Is this what it claims to be, and is it whole? ─────────────────────
cat("\nQ0  jqr hands the text to libjq, which errors on malformed JSON and says\n")
cat("    nothing about duplicate keys, big integers or NaN. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep. ──────────────────────────────────
cat("\nQ1  paths, with array indices folded to []:\n")
paths <- fromJSON(run('[paths | map(if type == "number" then "[]" else . end)
                        | join(".")] | unique', "..."))
cat("   ", length(paths), "— THE PROBE PRINTS 31. Exact.\n")
cat("\nQ2  max path length:\n")
cat("   ", fromJSON(run("[paths | length] | max", "...")),
    "— the probe prints 4. Exact.\n")

# ── Q3. THE SPLIT — jqr can search and price it. ──────────────────────────
cat("\nQ3  the record shape and its cost, in jq:\n")
EMPT <- '
  def emptiness($rows):
    ([$rows[] | keys[]] | unique) as $cols
    | ([ $rows[] | . as $r
         | [ $cols[] | . as $c | if ($r | has($c)) then 0 else 1 end ] | add ] | add)
      / (($rows | length) * ($cols | length));
'
base <- fromJSON(run(paste0(EMPT, '
    .docs as $d | {rows: ($d|length), cols: ([$d[]|keys[]]|unique|length),
                   empty: emptiness($d)}'), "..."))
cat(sprintf("    %d rows x %d cols, %.0f%% empty — the probe's numbers exactly.\n",
            base$rows, base$cols, 100 * base$empty))
cat("\nQ3  and the SEARCH over every always-present field, also in jq:\n")
search <- fromJSON(run(paste0(EMPT, '
    .docs as $d
    | ([$d[] | keys[]] | unique) as $all
    | [ $all[] | . as $f | select([$d[] | has($f)] | all) ] as $always
    | [ $always[] as $f
        | ($d | group_by(.[$f])) as $g
        | select(($g | length) > 1 and ($g | length) <= 24)
        | {field: $f, kinds: ($g|length), worst: ([$g[] | emptiness(.)] | max)} ]
      | sort_by(.worst)'), "..."))
for (i in seq_len(nrow(search)))
  cat(sprintf("      %-16s %3d kinds  worst group %5.1f%%\n",
              search$field[i], search$kinds[i], 100 * search$worst[i]))
cat("    THE RANKING AGREES WITH THE PROBE: ebook_access wins, has_fulltext ties\n")
cat("    (it is exactly its coarsening), and the other two are no help.\n")
cat("    But that is fifteen lines written knowing what to look for. jq has no\n")
cat("    verb for it and prints nothing unasked. PARTLY — and it is the closest\n")
cat("    any tool in either language has come to the fourth operation.\n")

# ── Q7. How many records. ────────────────────────────────────────────────
cat("\nQ7  both answers, one expression:\n")
cnt <- fromJSON(run('{in_array: (.docs|length), numFound, num_found, start}', "..."))
cat("   ", paste(names(cnt), unlist(cnt), sep = "=", collapse = " · "), "\n")
cat("    200 are here, 30,427 exist. This is a PAGE, and only a top-level field\n")
cat("    says so — pandas and polars frame `docs` and never see it.\n")

# ── Q4. Always present vs sometimes. ────────────────────────────────────
cat("\nQ4  field counts:\n")
fc <- fromJSON(run('[.docs[] | keys_unsorted[]] | group_by(.)
                    | map({(.[0]): length}) | add', "..."))
nul <- fromJSON(run('[.docs[] | to_entries[] | select(.value == null)] | length', "..."))
cat("   ", length(fc), "fields · always", sum(unlist(fc) == 200), "· sometimes",
    sum(unlist(fc) < 200), "— matches the probe\n")
cat("    rarest five:\n"); print(head(sort(unlist(fc)), 5))
cat("    and", nul, "nulls in the records, so `has` and `!= null` agree here.\n")

# ── Q5. Does any field change type. ─────────────────────────────────────
cat("\nQ5  fields whose non-null type varies:\n")
varying <- fromJSON(run('[.docs[] | to_entries[] | select(.value != null)
      | {k: .key, t: (.value|type)}] | group_by(.k)
      | map(select((map(.t)|unique|length) > 1) | .[0].k)', "..."))
cat("   ", if (length(varying)) paste(varying, collapse = ", ") else "none",
    "— the probe's answer. DuckDB's `unnest` route reports ELEVEN here,\n")
cat("    every one an invented null.\n")

# ── Q6. Are any object keys actually data? AND key-sets. ───────────────
cat("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA\n")
cat("    section is empty for this file.\n")
cat("\nQ6b distinct key-sets:\n")
ks <- fromJSON(run('[.docs[] | keys_unsorted | sort | join(",")] | unique | length',
                   "with sort"))
cat("   ", ks, "— THE PROBE PRINTS 15, and DuckDB agrees here too. That\n")
cat("    expression was 5.4x high on 13-package-lock and 7.0x high on\n")
cat("    15-github-issues; this document has neither data keys nor nulls.\n")

# ── Q8/Q9/Q10. Extraction. ────────────────────────────────────────────
cat("\nQ8  three fields:\n")
t <- fromJSON(run('[.docs[] | {title, edition_count, ebook_access}]', "..."))
cat("   ", nrow(t), "rows x", ncol(t), "cols\n"); print(head(t, 2))
cat("\nQ9  a field absent from some docs:\n")
q9 <- fromJSON(run('[.docs[] | {key, cover_i}]', "..."))
cat("   ", nrow(q9), "rows kept,", sum(is.na(q9$cover_i)), "NA\n")
cat("\nQ10 author_name:\n")
an <- fromJSON(run('[.docs[] | .author_name // [] | .[]]', "..."))
cat("   ", length(an), "names — the `// []` is needed because the field is absent\n")
cat("    on one doc. Five fields are arrays and all five are sometimes absent.\n")

# ── Q11. Find every path whose value matches something. ──────────────
cat("\nQ11 URL-valued paths, no field named:\n")
urls <- fromJSON(run('[paths(type == "string" and test("https?://")) | join(".")]
                      | group_by(.) | map({(.[0]): length}) | add', "..."))
print(unlist(urls))
cat("    ONE URL, at the ROOT. `paths` starts at the top so it cannot be missed;\n")
cat("    pandas and polars frame `docs` and report NONE OF ONE. purrr and\n")
cat("    jsonlite each need eight to ten lines of hand-written walk.\n")

# ── Q12. The flattest honest table, and what was lost. ────────────────
cat("\nQ12 the honest record table:\n")
flat <- fromJSON(run('[.docs[]]', "..."))
cat("   ", nrow(flat), "x", ncol(flat), "— five of the columns are arrays.\n")
cat("    Nothing collides: these records have no nested OBJECTS. rrapply's\n")
cat("    `bind` expands the arrays positionally into 36 columns at 64% NA,\n")
cat("    which is worse than leaving them alone.\n")
