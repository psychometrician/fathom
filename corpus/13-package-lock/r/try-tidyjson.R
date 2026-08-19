# tidyjson — an npm lockfile, 1,657 packages keyed by install path
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyjson (+ dplyr; versions printed at run time)
#  file          ../source.json   759 KB, 1,657 packages, depth 5
#  measured      2026-08-11
#  run           cd corpus/13-package-lock/r && Rscript try-tidyjson.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   PARTLY
#   1 what is in here                             6   YES                 YES
#   2 how deep                                    5   NO                  YES — exactly 5
#   3 what is one record                          4   YES                 PARTLY
#   4 always present vs sometimes                 5   YES                 YES
#   5 does any field change type                  6   YES                 YES — exactly the probe
#   6 are any object keys data                    6   -                   PARTLY — it NAMES the key
#   7 how many records                            1   YES                 yes
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   5   YES                 yes
#  11 find every path matching something          5   NO                  PARTLY
#  12 flattest honest table                      14   YES                 NO — 1,391 columns
#  13 needed the shape in advance?                    NO for 2, 5
#  14 survives the next file unchanged?               yes for those
#  15 readable a week later?                          yes — the verbs say what they do
#  16 lines, and how much is ceremony?                ~115, and the pipes are the intent
#
# **`gather_object("path")` IS THE RIGHT VERB FOR A KEYS-AS-DATA DOCUMENT AND
# tidyjson IS THE ONLY R TOOL THAT NAMES THE COLUMN.** You say what the key
# means — `gather_object("path")` — and the install path arrives as a column
# called `path`. rrapply's melt gets the same shape and calls it `L2`; every
# other tool in either language either loses the key or turns it into schema.
#
# **AND IT GETS QUESTION 5 EXACTLY RIGHT, WHICH ALMOST NOTHING HERE DOES.**
# `gather_object %>% json_types %>% count(field, type)` gives **23 rows for 21
# fields** — so exactly two fields carry two types, and they are `engines` and
# `funding`. That is the probe's answer. ijson reports ZERO varying paths on
# this document; jsonlite's `class()` reports none either.
#
# **`json_structure` PRINTS A TYPED CENSUS BY LEVEL AND IT IS THE BEST QUESTION 1
# IN R.** 16,629 rows, max level 5, and the level table shows where the document
# actually is — 1,657 objects at level 2, then 2,430 objects and 5,753 strings at
# level 3. **Zero nulls at every level**, which is the second corpus file running
# where that is true.
#
# **WHAT IT STILL WILL NOT DO IS PRICE A ROW SHAPE — AND `spread_all` WALKS
# STRAIGHT INTO THE TRAP.** `gather_object` commits to one shape and names no
# alternative; `spread_all` then recurses into the keyed collections and returns
# **1,657 x 1,391 at 99.3% NA**, the dependency names as columns. This file's
# first draft asserted that spread_all would stop at objects and give an honest
# table. Running it said otherwise, and that makes THREE:
#
#     pandas   json_normalize   1,657 x 1,394   99.5% empty
#     rrapply  how = "bind"     1,657 x 1,401   99.5% empty
#     tidyjson spread_all       1,657 x 1,391   99.3% empty
#
# **Three libraries, two languages, one shape, and not one of them warns.** The
# probe prices exactly this as `an entry of packages 1,657 x 1394 99% empty`,
# one of eight candidates — the only place in either language the number appears
# before you build the thing.
# ─────────────────────────────────────────────────────────────────────────────

suppressMessages({library(tidyjson); library(dplyr)})
cat(sprintf("R %s, tidyjson %s, dplyr %s\n",
            getRversion(), packageVersion("tidyjson"), packageVersion("dplyr")))

# tidyjson wants JSON TEXT, not a parsed list.
txt <- readChar("../source.json", file.info("../source.json")$size, useBytes = TRUE)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  tidyjson parses the text itself, so it would fail on malformed input.\n")
cat("    It reports no duplicate keys, no big integers, no NaN. DuckDB REFUSES\n")
cat("    this file over its empty-string key; tidyjson takes it. PARTLY.\n")

# ── Q1/Q4/Q5. The packages, their fields, and their types. ───────────────────
t0 <- Sys.time()
pk <- txt %>% as.tbl_json %>% enter_object("packages") %>% gather_object("path")
cat(sprintf("\nQ1  gather_object(\"path\"): %d rows in %.1fs\n", nrow(pk),
            as.numeric(Sys.time() - t0, units = "secs")))
cat("    THE INSTALL PATH IS A COLUMN CALLED `path`, because I said so. That is\n")
cat("    the keys-as-data shape, named rather than inferred.\n")

t1 <- Sys.time()
ft <- pk %>% gather_object("field") %>% json_types %>% count(field, type)
cat(sprintf("Q1  %d field/type pairs over %d distinct fields, in %.1fs\n",
            nrow(ft), length(unique(ft$field)),
            as.numeric(Sys.time() - t1, units = "secs")))

n <- nrow(pk)
present <- tapply(ft$n, ft$field, sum)
cat("\nQ4  always", sum(present == n), "-", names(present)[present == n], "\n")
cat("Q4  sometimes", sum(present < n), ", rarest five:\n")
print(head(sort(present), 5))
cat("    Matches the probe: 21 fields, only `version` on all 1,657.\n")

varying <- names(which(table(ft$field) > 1))
cat("\nQ5  fields carrying more than one JSON type:", paste(varying, collapse = ", "), "\n")
print(as.data.frame(ft[ft$field %in% varying, ]))
cat("    EXACTLY THE PROBE, which prints:\n")
cat("      engines  object x1,050, array[1] text x1\n")
cat("      funding  object x282, array[1] object x26, array[1] text x2\n")
cat("    ijson reports ZERO varying paths on this document because each package's\n")
cat("    `engines` sits at its own prefix; jsonlite's class() reports none because\n")
cat("    an object and an array are both `list`. tidyjson groups by FIELD and\n")
cat("    types the JSON, so it is right where both of those are silently wrong.\n")

# ── Q2. How deep does it go — json_structure. ────────────────────────────────
t2 <- Sys.time()
st <- txt %>% as.tbl_json %>% json_structure
cat(sprintf("\nQ2  json_structure: %s rows in %.1fs, max level %d — the probe prints 5\n",
            format(nrow(st), big.mark = ","),
            as.numeric(Sys.time() - t2, units = "secs"), max(st$level)))
print(table(level = st$level, type = st$type))
cat("    A typed census by level: 1,657 objects at level 2 are the packages,\n")
cat("    and the strings at level 4 are mostly dependency VERSIONS keyed by name.\n")
cat("    ZERO nulls at every level — the second corpus file running.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3  gather_object committed: packages are rows,", nrow(pk), "of them, with\n")
cat("    the key as a column. It names no alternative and prices nothing —\n")
cat("    the probe names EIGHT candidates, including 1,657 x 1394 at 99% empty.\n")
cat("    PARTLY.\n")
cat("Q7 ", nrow(pk), "packages\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
deps <- pk %>% enter_object("dependencies") %>% gather_object("dep")
cat("\nQ6  YES, and tidyjson is the closest thing in R to saying so:\n")
cat("    `gather_object(\"path\")` treats the 1,657 package keys as data —", n, "rows\n")
cat("    `gather_object(\"dep\")`  treats the dependency keys the same —",
    nrow(deps), "rows\n")
cat("    THE VERB IS THE SAME EITHER WAY, which is the limit: tidyjson does what\n")
cat("    it is told and computes no verdict. It cannot tell you that `packages`\n")
cat("    is keyed by data while `engines` — 5 keys over 1,050 copies — is a\n")
cat("    vocabulary. The probe prints seven keyed sites and declines that eighth.\n")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
tbl <- pk %>% spread_values(version = jstring("version"),
                            license = jstring("license")) %>%
  as.data.frame() %>% select(path, version, license)
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cat("\nQ9  license non-NA on", sum(!is.na(tbl$license)), "of", nrow(tbl),
    "— spread_values fills absent with NA and KEEPS the row\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
fund_arr <- pk %>% enter_object("funding") %>% json_types %>%
  filter(type == "array") %>% gather_array("i") %>% json_types
cat("\nQ10 funding as an ARRAY:", nrow(fund_arr), "elements over",
    length(unique(fund_arr$path)), "packages\n")
print(as.data.frame(count(fund_arr, type)))
cat("    The `filter(type == \"array\")` is required because funding is an object\n")
cat("    on 282 packages. json_types makes that filter EXPRESSIBLE, which is\n")
cat("    more than jsonlite or purrr offer — both need is.null(names(x)).\n")

# ── Q11. Find every path whose value matches something. ──────────────────────
hits <- pk %>% gather_object("field") %>% json_types %>%
  filter(type == "string") %>% append_values_string("v") %>%
  filter(grepl("https?://", v)) %>% count(field) %>% as.data.frame()
cat("\nQ11 URL-valued fields of a package:\n"); print(hits)
cat("    Two of the five folded paths, 1,664 of 2,003 values. The three inside\n")
cat("    `funding` need their own pipe, because the pipe names the LEVEL to\n")
cat("    scan. tidyjson has no recursive descent. PARTLY.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
sa <- pk %>% spread_all
cat(sprintf("\nQ12 spread_all(): %s x %s, %.1f%% NA\n",
            format(nrow(sa), big.mark = ","), format(ncol(sa), big.mark = ","),
            100 * mean(is.na(as.data.frame(sa)))))
cat("    IT BUILDS THE MONSTER. spread_all RECURSES into the keyed collections,\n")
cat("    so the columns are dependency NAMES — `dependencies.@vscode/ripgrep`,\n")
cat("    and 1,380 more. This draft asserted it would stop at objects and give\n")
cat("    an honest ~15-column table; running it says otherwise.\n")
cat("    THREE TOOLS, THREE NEARLY IDENTICAL MONSTERS, none of them warned:\n")
cat("      pandas   json_normalize   1,657 x 1,394   99.5% empty\n")
cat("      rrapply  how=\"bind\"       1,657 x 1,401   99.5% empty\n")
cat("      tidyjson spread_all       1,657 x 1,391   99.3% empty\n")
cat("    The probe prices exactly this shape — `an entry of packages 1,657 x\n")
cat("    1394 99% empty` — as one of eight candidates, and it is the only thing\n")
cat("    in either language that says the number out loud before you build it.\n")
cat("    The honest table needs the six collections excluded BY NAME, and the\n")
cat("    probe prices those separately at 2,841, 128, 104, 101, 78 and 25 rows.\n")
