# jqr — ESPN NFL Quarterback Rating, 2019, the corpus's only ground truth
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr (versions printed below)
#  file          ../source.json   180 KB, 28 athletes, depth 7, 131 paths,
#                                 72 fields, keyed 0, 0/56 ragged
#  measured      2026-08-10
#  run           cd corpus/06-espn-qbr/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           2   no                  yes
#   2 how deep                                  1   no                  yes
#   3 what is one record                        -   -                   CANNOT
#   4 always present vs sometimes               2   no                  YES
#   7 how many records                          1   YES                 yes
#   8 three named fields to a table             3   YES                 yes
#  7a related by position                       8   YES, fatally        see below
#  12 flattest honest table                     4   YES                 yes
#  13 needed the shape in advance?                  NO for 1, 2, 4
#  16 lines, and how much is ceremony?              8 expressions, no ceremony
#
#  ⚠ 7a is CIRCULAR per QUESTIONS.md and is NOT scored. What is recorded below
#  is a structural test jq can express — *are there two arrays of equal length
#  holding the same set of strings in different orders* — which is a fact about
#  the document rather than a mark against any tool.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `NOTES.md` calls the `glossary`/`labels` pair a **trap rather
# than a gap**: two arrays of ten holding the same abbreviations in different
# orders, and joining against the wrong one gives the league's best quarterback
# a Total QBR of -7.4 instead of 83.0, with no error.
#
# jsonlite hands you both and formats the wrong one more attractively. **The
# question here is whether the trap is DETECTABLE** — not whether jq volunteers
# it, which nothing does, but whether the collision can be stated at all.
library(jqr)

cat(sprintf("R %s, jqr %s; jq CLI reports %s\n", getRversion(), packageVersion("jqr"),
            tryCatch(sub("^jq-", "", system("jq --version", intern = TRUE)),
                     error = function(e) "not on PATH")))

txt <- paste(readLines("../source.json", warn = FALSE), collapse = "")
ask <- function(q) jq(txt, q)

cat(sprintf("\n2. depth %s, unaided\n", ask("[paths|length]|max")))
cat(sprintf("7. %s athletes\n", ask(".athletes|length")))
cat(sprintf("1. %s distinct leaf names, against NOTES.md's 72 fields\n",
            ask('[paths(type != "object" and type != "array")|map(select(type=="string"))|last]|unique|length')))
cat("   The sixth document for this expression. This one is flat-ish with no\n")
cat("   keyed sites, so it lands in the same place 03-natural-earth did: close\n")
cat("   to right, and short of the field count because structural fields never\n")
cat("   reach a leaf.\n")

cat("\n3. CANNOT — jq proposes no rows, on the one file where the right answer\n")
cat("   is published. `athletes` is correct and I had to name it.\n")

# ── Q4. ──────────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
ks <- ask('[.athletes[]] as $a | ($a|map(keys)|add|unique) as $ks
           | [ $ks[] as $k | select($a|all(has($k))) ]')
cat(sprintf("   fields present in EVERY athlete: %s\n", gsub("\\s+", "", ks)))
cat("   All of them — NOTES.md grades 0/56 ragged. On 04-gharchive this same\n")
cat("   expression returned `[]`. Same three lines, opposite documents.\n")

# ── 7a. THE TRAP, AND WHETHER IT CAN BE STATED. ──────────────────────────────
cat("\n7a. two arrays of ten, and the collision test (NOT SCORED — circular):\n")
lab <- ask('.categories[0].labels')
glo <- ask('[.glossary[].abbreviation]')
cat(sprintf("   categories[0].labels  %s\n", gsub("\\s+", " ", lab)))
cat(sprintf("   glossary abbreviations %s\n", gsub("\\s+", " ", glo)))

# The structural statement: same length, same SET, different ORDER.
coll <- ask('[.categories[0].labels] as $L
             | [[.glossary[].abbreviation]] as $G
             | {same_length: (($L[0]|length) == ($G[0]|length)),
                same_set:    (($L[0]|sort) == ($G[0]|sort)),
                same_order:  ($L[0] == $G[0])}')
cat(sprintf("   %s\n", gsub("\\s+", "", coll)))
cat("   THE TRAP IS EXPRESSIBLE, in one expression, with no knowledge of\n")
cat("   football. Two arrays of equal length holding the SAME SET of strings in\n")
cat("   a DIFFERENT ORDER is a structural fact, and it is exactly the condition\n")
cat("   under which a positional join is a coin flip.\n")
cat("   NOTHING VOLUNTEERS IT. I wrote the test because NOTES.md told me the\n")
cat("   trap was there. But this is not `no existing tool can express it` —\n")
cat("   it is `no existing tool looks`, which is a weaker and truer claim.\n")

# What the wrong join costs, stated in jq.
cost <- ask('[.categories[0].labels] as $L
             | [[.glossary[].abbreviation]] as $G
             | (.athletes[0].categories[0].totals) as $t
             | {athlete: .athletes[0].athlete.displayName,
                by_labels:   $t[($L[0]|index("TQBR"))],
                by_glossary: $t[($G[0]|index("TQBR"))]}')
cat(sprintf("   %s\n", gsub("\\s+", "", cost)))
cat("   Same ten numbers, same position-join, two answers, no error.\n")

# ── Q8 / Q12. ────────────────────────────────────────────────────────────────
cat("\n8/12. three named fields, and the honest wide table:\n")
n <- ask('[.athletes[]|{name:.athlete.displayName, team:.athlete.teamName,
                        qbr:(.categories[0].totals[0])}]|length')
cat(sprintf("   %s rows, one per quarterback\n", n))
top <- ask('[.athletes[]|{name:.athlete.displayName,
                          qbr:(.categories[0].totals[0]|tonumber)}]
            |sort_by(-.qbr)|.[0:3]')
cat(sprintf("   top three: %s\n", gsub("\\s+", "", top)))
wide <- ask('.categories[0].labels as $L
             | [.athletes[] | [.athlete.displayName] + .categories[0].totals]
             | {cols: (["name"] + $L), rows: length}')
cat(sprintf("   the honest wide table: %s\n", gsub("\\s+", "", wide)))
cat("   `.categories[0].labels as $L` IS THE WHOLE ANSWER and it is one clause.\n")
cat("   jq can name the columns from the document itself rather than from a\n")
cat("   magic number — which the published tutorial cannot, because it writes\n")
cat("   `totals[1]` and knows what the 1 means.\n")

cat("\n0. CANNOT. 6. n/a — keys-as-data 0.\n")

cat("
CONCLUSION — the trap is expressible, nobody looks, and that is a weaker claim
than the one this project has been making.

  `NOTES.md` calls `glossary` versus `labels` a trap rather than a gap: two
  arrays of ten, the same abbreviations, different orders, and the wrong join
  produces **-7.4** where **83.0** belongs with no error and some values correct
  by coincidence.

  **jq states the collision in one expression** — same length, same set,
  different order — with no knowledge of football and no field named beyond the
  two arrays. And `.categories[0].labels as $L` then names the columns *from the
  document*, which is strictly better than the published tutorial's `totals[1]`,
  a magic number that is correct because its author checked.

  **So the honest form of this file's finding is not `no existing tool can do
  this`.** It is: the test is one line, the fix is one clause, and **nothing
  looks unprompted**. I wrote both because `NOTES.md` told me the trap existed.
  A person meeting this endpoint cold gets two ten-element arrays, one of them
  formatted as a tidy data frame by jsonlite, and no reason to suspect the
  other exists.

  That is a smaller claim than `nobody helps you explore`, and it is the one the
  evidence supports. It is also a more useful specification: the thing to build
  is not a new capability, it is the *looking*.
")
