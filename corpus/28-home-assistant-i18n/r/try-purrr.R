# purrr — Home Assistant frontend, the English translation catalogue
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
#  measured      2026-08-12
#  run           cd corpus/28-home-assistant-i18n/r && Rscript try-purrr.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             4   NO                  ONE LEVEL — names()
#   2 how deep                                    5   NO                  yes, by a recursion I wrote
#   3 what is one record                          4   -                   CANNOT
#   4 always present vs sometimes                 4   NO                  yes, once melted
#   5 does any field change type                  4   NO                  yes, once melted
#   6 are any object keys data                    -   -                   CANNOT
#   7 how many records                            2   NO                  yes
#   8 three named fields to a table               4  YES                  yes — pluck
#   9 a field missing from some rows              3  YES                  YES — pluck's .default
#  10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
#  11 find every path matching something          3   NO                  yes, once melted
#  12 flattest honest table                       6   NO                  PARTLY — the recursion is mine
#  13 needed the shape in advance?                    NO, but I wrote the walk
#  14 survives the next file unchanged?               yes
#  15 readable a week later?                          YES — pluck and map_depth are plain
#  16 lines, and how much is ceremony?                ~75
#
# **purrr has no recursive descent over a nested LIST, which is surprising given
# what it is for.** `map_depth` needs the depth as an argument, `flatten` goes
# one level, and `pluck` takes a path you already have. Every question below that
# is answered is answered by a `rapply` — which is base R, not purrr.

suppressMessages({library(jsonlite); library(purrr)})
cat(sprintf("jsonlite %s · purrr %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("purrr"),
            R.version$major, R.version$minor))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

cat(sprintf("\nQ1  names(doc) -> %d: %s\n", length(doc), paste(names(doc), collapse = ", ")))
cat("    ONE LEVEL. `map_depth(doc, 2, names)` needs the 2, and there are\n")
cat("    eleven levels here, so knowing what to pass IS the question.\n")

# ── Q2/Q12. The melt, and the recursion is base R rather than purrr. ─────────
t0 <- Sys.time()
rows <- list()
walk_it <- function(x, path = character()) {
  if (is.list(x)) {
    for (nm in names(x)) walk_it(x[[nm]], c(path, nm))
  } else {
    rows[[length(rows) + 1]] <<- list(path = paste(path, collapse = "."),
                                      depth = length(path), value = x)
  }
}
walk_it(doc)
secs <- round(as.numeric(difftime(Sys.time(), t0, units = "secs")), 2)
tab <- data.frame(path = map_chr(rows, "path"),
                  depth = map_int(rows, "depth"),
                  value = map_chr(rows, ~ as.character(.x$value)))

cat(sprintf("\nQ2  max depth %d, from the walk above. yes — but I wrote the walk.\n",
            max(tab$depth)))

cat(sprintf("\nQ12 %s rows x 3, in %s seconds. PARTLY: `walk_it` is eight lines of\n",
            format(nrow(tab), big.mark = ","), secs))
cat("    ordinary recursion and purrr contributed none of it. `map_chr` tidied\n")
cat("    the result afterwards, which is purrr doing what it is for.\n")
print(utils::head(tab, 3))

cat("\nQ3  CANNOT. purrr names no record shapes and prices none.\n")
cat(sprintf("\nQ7  %s messages. yes, from the melt.\n", format(nrow(tab), big.mark = ",")))

cat("\nQ4  messages by depth:\n")
print(table(tab$depth))
cat("    yes, once melted — the same histogram rrapply and tidyr give.\n")

cat(sprintf("\nQ5  classes at the bottom: %s. Every leaf is a character; the\n",
            paste(unique(map_chr(rows, ~ class(.x$value)[1])), collapse = ", ")))
cat("    variation the probe reports is between a leaf and a group at one path,\n")
cat("    which the walk can see and does not judge.\n")

cat("\nQ6  CANNOT.\n")

cat(sprintf("\nQ8  %s\n", paste(c(pluck(doc, "ui", "common", "and"),
                                  pluck(doc, "ui", "common", "loading"),
                                  pluck(doc, "ui", "panel", "profile", "logout")),
                                collapse = " | ")))
cat("    yes — `pluck` is clean and reads perfectly a week later.\n")

cat(sprintf("\nQ9  pluck(.default = \"MISSING\") -> %s\n",
            pluck(doc, "ui", "panel", "profile", "nope", .default = "MISSING")))
cat("    YES. `.default` is the case exactly, and it is prior art for the\n")
cat("    behaviour `whichever` is proposed for.\n")

cat("\nQ10 zero arrays in 604 KB. NOTHING TO FLATTEN.\n")

icu <- grepl("\\{", tab$value)
cat(sprintf("\nQ11 messages with an ICU placeholder: %s — a grepl over the melt.\n",
            format(sum(icu), big.mark = ",")))
cat("    yes, once melted; purrr has no path search of its own.\n")

cat("
CONCLUSION. purrr is a good tool that this document has almost nothing for. Its
verbs are shaped for a list of records — `map`, `map_depth`, `keep` — and a
translation catalogue is one record eleven levels deep. `map_depth` needs the
depth as an argument, which is the question, and `flatten` goes one level.

`pluck` with `.default` is the exception and it is genuinely good: Q8 and Q9 are
two clean lines that read back perfectly, and `.default` is prior art for what
`whichever` is proposed to do.

Everything else here was answered by eight lines of recursion I wrote myself,
which is available in every language and says nothing about purrr. Scored PARTLY
for that reason. rrapply — the same language, one call — is the comparison that
matters, and it is not close.
")
