# tidyjson — cargo metadata for this repository
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.json   27 KB, 8 packages, depth 8
#  measured      2026-08-11
#  run           cd corpus/24-cargo-metadata/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             6   YES                 PARTLY — one level
#   2 how deep                                    1   -                   CANNOT
#   3 what is one record                          2   -                   CANNOT
#   4 always present vs sometimes                 4   NO                  YES — nothing absent
#   5 does any field change type                 12   NO                  THE PREDICTION
#   6 are any object keys data                    8   YES                 gather_object, and it
#                                                                          is the RIGHT shape
#   7 how many records                             2  YES                 yes
#   8 three named fields to a table                4 YES                 yes
#   9 a field missing from some rows                3 NO                  YES — both halves
#  10 flatten the deepest array                     6 YES                 yes
#  11 find every path matching something            4 YES                 CANNOT
#  12 flattest honest table                         6 NO                  yes
#  13 needed the shape in advance?                    YES — `packages` by name
#  14 survives the next file unchanged?               Q4/Q5/Q6 YES — gather_object
#                                                     puts feature names in a COLUMN
#  15 readable a week later?                          YES
#  16 lines, and how much is ceremony?                ~100
#
# THE STANDING PREDICTION, LAST TEST. tidyjson mistypes the fields that are
# SOMETIMES null and sometimes a value — entry 20 narrowed it, entry 22 confirmed
# it one level down, entry 23 confirmed it where six null-bearing fields yielded
# only three mistypable. THIS DOCUMENT HAS TWELVE NULL-BEARING PACKAGE FIELDS
# AND FOUR OF THEM ARE NULL ON ALL EIGHT — `default_run`, `license_file`,
# `links`, `publish`. SO THE PREDICTION IS EIGHT.
#
# AND QUESTION 6 IS WHERE tidyjson IS RIGHT WHERE THE FRAMES ARE WRONG.
# `gather_object` puts the 28 feature names in a `name` COLUMN, not in a schema
# — so it is the only R tool here whose output survives a `cargo add`.
# ─────────────────────────────────────────────────────────────────────────────

library(tidyjson)
library(dplyr)
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

src <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
cat("\nQ0  tidyjson parses through jsonlite and reports no health. CANNOT.\n")

g <- as_tibble(src %>% enter_object("packages") %>% gather_array() %>%
                 gather_object() %>% json_types())
n <- src %>% enter_object("packages") %>% gather_array() %>% nrow()
cat(sprintf("\nQ1  enter_object + gather_array + gather_object -> %d rows\n", nrow(g)))
cat(sprintf("    %d distinct package field names over %d packages\n",
            n_distinct(g$name), n))
cat("Q2  CANNOT. No depth verb; the probe says 8.\n")
cat(sprintf("\nQ3  no candidates, no pricing. CANNOT.\nQ7  %d packages\n", n))

# ── Q6. WHERE tidyjson IS RIGHT. ────────────────────────────────────────────
f <- as_tibble(src %>% enter_object("packages") %>% gather_array() %>%
                 enter_object("features") %>% gather_object())
cnt <- f %>% count(name)
cat(sprintf("\nQ6  `enter_object('features') %%>%% gather_object()` -> %d rows,\n", nrow(f)))
cat(sprintf("    %d distinct feature names, %d appearing ONCE\n",
            nrow(cnt), sum(cnt$n == 1)))
cat(sprintf("Q6  %d of them contain a HYPHEN, and tidyjson does not care —\n",
            sum(grepl("-", cnt$name))))
cat("    the names are VALUES in a `name` column, not identifiers.\n")
cat("    ══ THIS IS THE RIGHT SHAPE, AND IT IS THE ONLY R TOOL THAT GIVES IT. ══\n")
cat("    jsonlite simplifies `features` into 28 COLUMNS and pandas and polars\n")
cat("    do the same in their own way, so their schema is this repository's\n")
cat("    dependency graph and `cargo add` changes it. `gather_object` puts the\n")
cat("    keys in a COLUMN, which is what question 6 says they are — so this\n")
cat("    output survives the next file unchanged and theirs does not.\n")
cat("    IT IS STILL NOT A VERDICT: `gather_object` does the same to genuine\n")
cat("    field names one level up, so it is a representation, as rrapply's melt is.\n")

# ── Q4/Q5. THE PREDICTION. ──────────────────────────────────────────────────
ty <- g %>% count(name, type)
vary <- ty %>% count(name, name = "k") %>% filter(k > 1)
wn <- ty %>% filter(type == "null") %>% pull(name)
alln <- ty %>% group_by(name) %>%
  summarise(nulls = sum(n[type == "null"]), tot = sum(n)) %>% filter(nulls == tot)
cat(sprintf("\nQ5  fields with MORE THAN ONE json_type: %d\n", nrow(vary)))
cat(sprintf("    %s\n", paste(sort(vary$name), collapse = ", ")))
cat(sprintf("Q5  of those, %d include `null`\n", sum(vary$name %in% wn)))
cat(sprintf("Q5  fields null on ALL %d packages: %s\n", n,
            paste(sort(alln$name), collapse = ", ")))
cat("    THE PREDICTION SAID EIGHT — twelve null-bearing fields minus the four\n")
cat("    that are null on every package and so have ONE type. Read the number.\n")
cat("    FOURTH DOCUMENT TESTING ENTRY 20's REFINEMENT, and the probe reports\n")
cat("    NO type change on this document at all.\n")
miss <- ty %>% group_by(name) %>% summarise(rows = sum(n)) %>% filter(rows < n)
cat(sprintf("\nQ4  fields on fewer than all %d packages: %d — nothing is ever absent\n",
            n, nrow(miss)))

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8 <- src %>% enter_object("packages") %>% gather_array() %>%
  spread_values(name = jstring("name"), version = jstring("version"),
                edition = jstring("edition"))
cat(sprintf("\nQ8  spread_values -> %d x %d\n", nrow(t8), ncol(t8)))
d <- g %>% filter(name == "description")
cat(sprintf("\nQ9  `description` emits %d rows of %d packages, %d typed `null`\n",
            nrow(d), n, sum(d$type == "null")))
cat("    PRESENCE and NULL separately — both halves, which no frame here can do.\n")
tg <- src %>% enter_object("packages") %>% gather_array() %>%
  spread_values(pkg = jstring("name")) %>%
  enter_object("targets") %>% gather_array("ti") %>%
  spread_values(target = jstring("name"))
dk <- src %>% enter_object("resolve") %>% enter_object("nodes") %>% gather_array() %>%
  spread_values(node = jstring("id")) %>%
  enter_object("deps") %>% gather_array("di") %>%
  enter_object("dep_kinds") %>% gather_array("ki") %>%
  spread_values(kind = jstring("kind"))
cat(sprintf("\nQ10 targets -> %d x %d; dep_kinds -> %d x %d at depth 6\n",
            nrow(tg), ncol(tg), nrow(dk), ncol(dk)))
cat("    EIGHT chained verbs for the second, and `node` survives all of them —\n")
cat("    which no frame in this directory could do, because that branch is not\n")
cat("    under `packages` at all.\n")
cat("\nQ11 CANNOT enumerate paths — no recursive descent.\n")
u <- src %>% enter_object("packages") %>% gather_array() %>%
  spread_values(r = jstring("repository"))
cat(sprintf("    a NAMED path: `repository` matches ^https?:// on %d of %d\n",
            sum(grepl("^https?://", u$r)), nrow(u)))
sa <- src %>% enter_object("packages") %>% gather_array() %>% spread_all()
at <- vapply(sa, is.atomic, logical(1))
cat(sprintf("\nQ12 spread_all -> %d x %d, %.1f%% NA over %d atomic columns\n",
            nrow(sa), ncol(sa), 100 * mean(is.na(as.matrix(sa[, at]))), sum(at)))
cat("    Compare pandas' 8 x 57 at 63% and the probe's 8 x 57 at 63%.\n")
