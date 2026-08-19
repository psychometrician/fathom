# tidyjson — Docker Hub tags, 100 tags
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (versions printed at run time)
#  file          ../source.json   476 KB, 100 tags under $.results, depth 5
#  measured      2026-08-11
#  run           cd corpus/22-dockerhub-tags/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               1   -                   CANNOT
#   1 what is in here                             6   YES                 PARTLY — one level
#   2 how deep                                    1   -                   CANNOT
#   3 what is one record                          2   -                   CANNOT
#   4 always present vs sometimes                 6   NO                  yes — nothing absent
#   5 does any field change type                 12   NO                  see the prediction
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                            2   YES                 yes, both numbers
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   NO                  yes
#  10 flatten the deepest array                   6   YES                 YES — parent kept
#  11 find every path matching something          4   YES                 PARTLY
#  12 flattest honest table                       8   NO                  yes
#  13 needed the shape in advance?                    YES — `results` must be named
#  14 survives the next file unchanged?               Q4/Q5 yes
#  15 readable a week later?                          YES
#  16 lines, and how much is ceremony?                ~100
#
# THE STANDING PREDICTION, AND THIS DOCUMENT SPLITS IT FROM ITS USUAL ANSWER.
# tidyjson mistypes fields because `json_types()` counts `null` as a type. Entry
# 20 narrowed that to "the fields that are SOMETIMES null and sometimes a
# value", and entry 21 confirmed ZERO on a document with no nulls at all.
# THIS DOCUMENT HAS NO NULLS AT THE TAG LEVEL AND TWO NULL-BEARING FIELDS ONE
# LEVEL DOWN, in `images`. So the prediction is: ZERO mistyped TAG fields, and
# TWO mistyped IMAGE fields — `os_version` and `variant`. If the mechanism is
# what four entries say, the level should not matter.
# ─────────────────────────────────────────────────────────────────────────────

library(tidyjson)
library(dplyr)
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

src <- paste(readLines("../source.json", warn = FALSE), collapse = "\n")
cat("\nQ0  tidyjson parses through jsonlite and reports no health. CANNOT.\n")

t0 <- Sys.time()
tagk <- src %>% enter_object("results") %>% gather_array() %>% gather_object() %>% json_types()
cat(sprintf("\nQ1  enter_object + gather_array + gather_object -> %d rows, %.2fs\n",
            nrow(tagk), as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat(sprintf("    %d distinct tag field names\n", n_distinct(tagk$name)))
imgk <- src %>% enter_object("results") %>% gather_array() %>%
  enter_object("images") %>% gather_array("ii") %>% gather_object() %>% json_types()
cat(sprintf("Q1  one level down: %d distinct image field names over %d rows\n",
            n_distinct(imgk$name), nrow(imgk)))
cat("Q2  CANNOT. No depth verb; the probe says 5.\n")

n <- src %>% enter_object("results") %>% gather_array() %>% nrow()
cat(sprintf("\nQ3  no candidates, no pricing. CANNOT.\nQ7  %d tags on this page\n", n))

# ── Q4/Q5. THE PREDICTION, AT TWO LEVELS. ───────────────────────────────────
for (lbl in c("TAG", "IMAGE")) {
  d <- if (lbl == "TAG") tagk else imgk
  # `distinct()` on a tbl_json ERRORS — "The `[` method for class <tbl_json>
  # must return a data frame with 3 columns. It returned ... 4 columns."
  # A tbl_json is not a well-behaved tibble for every dplyr verb, which is the
  # same class of surprise as its having no `json` COLUMN (entry 20).
  tot <- if (lbl == "TAG") n else nrow(distinct(as_tibble(imgk)[, c("document.id", "array.index", "ii")]))
  ty <- d %>% count(name, type) %>% as_tibble()
  vary <- ty %>% count(name, name = "k") %>% filter(k > 1)
  wn <- ty %>% filter(type == "null") %>% pull(name)
  cat(sprintf("\nQ5  %-5s fields with more than one json_type: %d %s\n", lbl, nrow(vary),
              if (nrow(vary)) paste0("— ", paste(vary$name, collapse = ", ")) else ""))
  cat(sprintf("    of those, %d include `null`\n", sum(vary$name %in% wn)))
  miss <- ty %>% group_by(name) %>% summarise(rows = sum(n)) %>% filter(rows < tot)
  cat(sprintf("Q4  %-5s fields on fewer than every record: %d\n", lbl, nrow(miss)))
}
cat("\n    THE PREDICTION SAID ZERO TAG FIELDS AND TWO IMAGE FIELDS —\n")
cat("    `os_version` and `variant`, the two written null. Read the numbers.\n")
cat("    THE POINT IS THE LEVEL: four entries measured this mechanism at the\n")
cat("    RECORD level only. If it fires one level down on exactly the two\n")
cat("    null-bearing fields, the mechanism is about the NULL and not the depth.\n")
cat("    Note also `features` and `os_features` are EMPTY STRINGS on all 1,388\n")
cat("    and are correctly typed `string` — an empty string is a string, and\n")
cat("    tidyjson is right about that where the probe counts neither.\n")

cat("\n     A NOTE ON tbl_json AND dplyr: `distinct()` on the gathered object\n")
cat("     ERRORS — 'The `[` method for class <tbl_json> must return a data\n")
cat("     frame with 3 columns. It returned ... 4 columns.' It works after\n")
cat("     `as_tibble()`. Entry 20 found the same class of surprise from the\n")
cat("     other side: a tbl_json has no `json` COLUMN for dplyr to see.\n")
cat("     A tidyjson table looks like a tibble and is not one.\n")
cat("\nQ6  no keyed collections. n/a, and the probe agrees.\n")

tbl <- src %>% enter_object("results") %>% gather_array() %>%
  spread_values(name = jstring("name"), size = jnumber("full_size"),
                updated = jstring("last_updated"))
cat(sprintf("\nQ8  spread_values -> %d x %d\n", nrow(tbl), ncol(tbl)))
va <- imgk %>% filter(name == "variant")
cat(sprintf("\nQ9  `variant` emits %d gathered rows — PRESENT on every image, and\n", nrow(va)))
cat(sprintf("    %d of them are typed `null`. gather_object counts PRESENCE and\n",
            sum(va$type == "null")))
cat("    json_types reports the null separately, so tidyjson answers question 9\n")
cat("    with both halves — which it could not do if the key were absent.\n")
t0 <- Sys.time()
res <- src %>% enter_object("results") %>% gather_array() %>%
  spread_values(tag = jstring("name")) %>%
  enter_object("images") %>% gather_array("ii") %>%
  spread_values(arch = jstring("architecture"), os = jstring("os"))
cat(sprintf("\nQ10 images[] -> %d x %d, %.2fs — the tag name survives\n", nrow(res), ncol(res),
            as.numeric(difftime(Sys.time(), t0, units = "secs"))))
u <- src %>% spread_values(nxt = jstring("next"))
cat(sprintf("\nQ11 CANNOT enumerate paths. The one URL is `$.next` and tidyjson\n"))
cat(sprintf("    reaches it by name at the ROOT: %s…\n", substr(u$nxt, 1, 44)))
cat("    Like jsonlite, it can see the envelope; pandas, polars and DuckDB\n")
cat("    built from `results` and report none of one.\n")
t0 <- Sys.time()
sa <- src %>% enter_object("results") %>% gather_array() %>% spread_all()
at <- vapply(sa, is.atomic, logical(1))
cat(sprintf("\nQ12 spread_all -> %d x %d, %.2fs, %.1f%% NA over %d atomic columns\n",
            nrow(sa), ncol(sa), as.numeric(difftime(Sys.time(), t0, units = "secs")),
            100 * mean(is.na(as.matrix(sa[, at]))), sum(at)))
cat("    Compare pandas 100 x 16, jsonlite flatten 100 x 16, rrapply bind\n")
cat("    100 x 213. On a REGULAR document the four libraries nearly agree,\n")
cat("    which is the whole point of running a control.\n")
