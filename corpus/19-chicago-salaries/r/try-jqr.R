# jqr — Chicago employee salaries
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr 1.4.0 (jq's C library through R)
#  file          ../source.json   923 KB, 5,000 records, 8 fields, depth 2
#  measured      2026-08-10
#  run           cd corpus/19-chicago-salaries/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             4   NO                  yes
#   2 how deep                                    1   NO                  yes
#   3 what is one record                          5   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  4   NO                  yes
#   6 are any object keys data                    2   -                   n/a
#   7 how many records                            1   NO                  YES
#   8 three named fields to a table               3   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   2   -                   n/a
#  11 find every path matching something          4   NO                  yes
#  12 flattest honest table                       5   NO                  yes
#  13 needed the shape in advance?                    NO for everything but 8
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          yes, expressions are short
#  16 lines, and how much is ceremony?                ~35, dense not ceremonial
#
# jqr is jq through a second door, so every answer here matches
# ../python/try-jq.py exactly. They are a CONTROL, not two witnesses.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages(library(jqr))
cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

j <- paste(readLines("../source.json", warn = FALSE), collapse = "")
q  <- function(prog) jq(j, prog)
qs <- function(prog) gsub('\\\\"', "", gsub('^"|"$', "", jq(j, prog)))

cat("\n1. folded path shapes:\n")
cat(qs('[paths(scalars)|map(if type=="number" then "[]" else . end)|join(".")]
        |group_by(.)|map({p:.[0],n:length})|sort_by(-.n)|.[]
        |"     \\(.p)  \\(.n)"'), sep = "\n")

cat(sprintf("\n2. deepest path: %s segments\n", q('[paths|length]|max')))
cat(sprintf("\n7. %s records.\n", q('length')))

cat("\n4. key presence across the 5,000 records, nothing named:\n")
cat(qs('[.[]|keys[]]|group_by(.)|map({k:.[0],n:length})|sort_by(-.n)|.[]
        |"     \\(.k)  \\(.n) of 5000"'), sep = "\n")
cat("   3,938 + 1,062 = 5,000. jq computes both and does not add them up.\n")

cat("\n5. types per folded path:\n")
cat(qs('[paths as $p|select((getpath($p)|type) as $t|$t!="object" and $t!="array")
        |{p:($p|map(if type=="number" then "[]" else . end)|join(".")),
          t:(getpath($p)|type)}]|group_by(.p)
        |map({p:.[0].p,t:(map(.t)|unique|join(","))})|.[]
        |"     \\(.p)  \\(.t)"'), sep = "\n")
cat("   Every path is `string`. Correct, and the trap: `annual_salary` holds\n")
cat("   \"165624\". A document uniformly wrong about its own types looks exactly\n")
cat("   like one that is right, to every type report in both languages.\n")

cat("\n3. one employee per row, and TWO defensible tables:\n")
cat(qs('[.[]|{k:.salary_or_hourly,n:(keys|length)}]|group_by(.k)
        |map({k:.[0].k,rows:length,cols:(map(.n)|max)})|sort_by(-.rows)|.[]
        |"     \\(.k)  \\(.rows) rows x \\(.cols) cols, all filled"'), sep = "\n")
cat("   `group_by(.salary_or_hourly)` is one expression. The union is 8 columns\n")
cat("   at 22% empty; the split is 6 and 7 at 0%. jq has every number needed to\n")
cat("   notice and volunteers nothing — which is the corpus's recurring result.\n")

cat("\n8. three fields (first three):\n")
cat(qs('[.[]|{name,department,annual_salary}]|.[0:3]|.[]
        |"     \\(.name)  |  \\(.department)  |  \\(.annual_salary)"'), sep = "\n")
cat(sprintf("\n9. annual_salary null on %s of 5000, all kept — a missing key is\n",
            q('[.[]|.annual_salary]|map(select(.==null))|length')))
cat("   null inside an object constructor, so no guard is needed.\n")

cat("\n11. values matching /DEPARTMENT/, by folded path:\n")
cat(qs('[paths(strings) as $p|select(getpath($p)|test("DEPARTMENT"))
        |($p|map(if type=="number" then "[]" else . end)|join("."))]
        |group_by(.)|map({p:.[0],n:length})|.[]|"     \\(.p)  \\(.n)"'), sep = "\n")
cat("   Found without naming a column — the thing every frame-shaped tool has\n")
cat("   to fake by enumerating its own column list first.\n")

cat("\n10, 6. n/a. No nested array, no keys that are data.\n")
cat(sprintf("\n12. flattest honest table: %s x 8, already flat.\n", q('length')))
cat("   WHAT IS LOST: nothing. jq is complete on this document and silent\n")
cat("   about the two things worth saying.\n")
