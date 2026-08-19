# jqr — Jupyter notebook, Norvig Advent-2021
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jqr 1.4.0 (jq's C library through R)
#  file          ../source.json   1.1 MB, 272 cells, 107 outputs, 37 paths
#  measured      2026-08-10
#  run           cd corpus/11-jupyter-notebook/r && Rscript try-jqr.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                             5   NO                  yes
#   2 how deep                                    3   NO                  yes
#   3 what is one record                          4   NO                  PARTLY
#   4 always present vs sometimes                 4   NO                  yes
#   5 does any field change type                  6   NO                  yes
#   6 are any object keys data                    3   NO                  PARTLY
#   7 how many records                            3   NO                  yes
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          5   NO                  yes
#  12 flattest honest table                       4   YES                 yes
#  13 needed the shape in advance?                    NO for 1-7 and 11
#  14 survives the next file unchanged?               the describe half does
#  15 readable a week later?                          the short ones only
#  16 lines, and how much is ceremony?                ~45, the strings are dense
#
# WHAT jqr IS AND IS NOT. It is jq's query language reached from R, so every
# answer here is the same answer corpus/11-jupyter-notebook/python/try-jq.py
# gives — the two are one language through two doors, and they are a CONTROL
# rather than two witnesses. What differs is the binding: `jq()` takes an R
# string and has no slurp, which VERDICT.md measures at 198 MB against the jq
# binary's 4.3 MB on a 50 MB file.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages(library(jqr))
cat(sprintf("R %s, jqr %s\n", getRversion(), packageVersion("jqr")))

j <- paste(readLines("../source.json", warn = FALSE), collapse = "")
q <- function(prog) jq(j, prog)
# jqr returns JSON text, so a string result arrives WITH its quotes. `qs`
# strips them for display. This is a property of the binding and not of jq —
# the jq binary's `-r` has no equivalent here, which is the same class of
# binding gap VERDICT.md records for `jq()` having no slurp.
qs <- function(prog) gsub('\\\\"', "", gsub('^"|"$', "", jq(j, prog)))

# ── Q1. what is in here ──────────────────────────────────────────────────────
cat("\n1. folded path shapes, array indices collapsed to []:\n")
cat(qs('[paths(scalars)|map(if type=="number" then "[]" else . end)|join(".")]
       |group_by(.)|map({p:.[0],n:length})|sort_by(-.n)|.[0:8]|.[]
       |"     \\(.p)  \\(.n)"'), sep = "\n")
cat("   Same expression, same answer as the Python binding — one language,\n")
cat("   two doors. The fold is hand-written in both.\n")

# ── Q2. how deep ─────────────────────────────────────────────────────────────
cat(sprintf("\n2. deepest path: %s segments\n", q('[paths|length]|max')))

# ── Q7, Q3. how many records ─────────────────────────────────────────────────
cat(sprintf("\n7. cells: %s   outputs: %s\n", q('.cells|length'),
            q('[.cells[].outputs[]?]|length')))
cat("\n3. two defensible records and jq prices neither. `?` is what makes the\n")
cat("   output count possible at all — without it `.outputs[]` ERRORS on the\n")
cat("   140 markdown cells rather than yielding nothing, which is jq refusing\n")
cat("   where jmespath would have returned null.\n")

# ── Q4. always vs sometimes ──────────────────────────────────────────────────
cat("\n4. key presence across the 272 cells, nothing named in advance:\n")
cat(qs('[.cells[]|keys[]]|group_by(.)|map({k:.[0],n:length})|sort_by(-.n)|.[]
       |"     \\(.k)  \\(.n) of 272"'), sep = "\n")
cat("   `keys` is presence, so execution_count is 132 — the explicit null is a\n")
cat("   present key. jq, purrr, tidyjson and ijson get this; the frame-shaped\n")
cat("   tools in both languages all collapse it to 131.\n")

# ── Q5. does any field change type ───────────────────────────────────────────
# MEASURED, and it is the same trap the Python binding hit: `paths(scalars)`
# CANNOT SEE A NULL. `paths(f)` is `paths|select(getpath|f)` and `select(null)`
# is false in jq, so every null value is silently absent from the path list.
cat(sprintf("\n5. paths(scalars) at execution_count: %s\n",
            q('[paths(scalars)|select(.[-1]=="execution_count")]|length')))
cat(sprintf("   paths          at execution_count: %s\n",
            q('[paths|select(.[-1]=="execution_count")]|length')))
cat("   One apart, and the missing one is the null. Asking without `scalars`:\n")
cat(qs('[paths as $p|select((getpath($p)|type) as $t|$t!="object" and $t!="array")
       |{p:($p|map(if type=="number" then "[]" else . end)|join(".")),
         t:(getpath($p)|type)}]|group_by(.p)
       |map({p:.[0].p,t:(map(.t)|unique)})|map(select(.t|length>1))|.[]
       |"     \\(.p)  \\(.t)"'), sep = "\n")
cat("   Ragged by null, not a type change — but jq had to be asked correctly\n")
cat("   before it could be right about it, and the idiomatic phrasing is the\n")
cat("   one that is silent.\n")

# ── Q6. are any object keys data ─────────────────────────────────────────────
cat(sprintf("\n6. PARTLY. mime keys: %s\n",
            qs('[.cells[].outputs[]?.data?|select(.!=null)|keys[]]|unique|join(", ")')))
cat("   jq lists them and has no way to say they are values rather than field\n")
cat("   names — the same `keys` call that answered Q4 about real fields.\n")

# ── Q8, Q9. three named fields, one missing from some ────────────────────────
cat("\n8. three fields, one row per cell (first three):\n")
cat(qs('[.cells[]|{type:.cell_type,n:.execution_count,lines:(.source|length)}]
       |.[0:3]|.[]|"     \\(.type)  \\(.n)  \\(.lines)"'), sep = "\n")
cat(sprintf("\n9. n is null on %s of 272 rows, all kept — a missing key is null\n",
            q('[.cells[]|.execution_count]|map(select(.==null))|length')))
cat("   inside an object constructor, so no row is dropped and no guard needed.\n")

# ── Q10. flatten the deepest array ───────────────────────────────────────────
cat(sprintf("\n10. text/plain exploded to lines: %s rows\n",
            q('[.cells[].outputs[]?.data?["text/plain"]?[]?]|length')))
cat('   Four `?` operators in one expression, one per level that may be absent.\n')

# ── Q11. every path whose value matches ──────────────────────────────────────
cat("\n11. values containing a URL, by folded path:\n")
cat(qs('[paths(strings) as $p|select(getpath($p)|test("https?://"))
       |($p|map(if type=="number" then "[]" else . end)|join("."))]
       |group_by(.)|map({p:.[0],n:length})|.[]|"     \\(.p)  \\(.n)"'), sep = "\n")
cat("   jq and rrapply are the only two tools in EITHER language that answer\n")
cat("   this without a hand-written recursion.\n")

# ── Q12. flattest honest table ───────────────────────────────────────────────
cat(sprintf("\n12. flattest: %s rows\n",
            q('[.cells[] as $c|$c.outputs[]?
                |{type:$c.cell_type,kind:.output_type,
                  tp:(.data?["text/plain"]?|length)}]|length')))
cat("   `. as $c` binds the parent, so cell_type rides down onto each output.\n")
cat("   WHAT IS LOST: the 140 markdown cells, which have no output; and the 17\n")
cat("   base64 PNGs, 79% of the file's bytes, kept only as a length.\n")
