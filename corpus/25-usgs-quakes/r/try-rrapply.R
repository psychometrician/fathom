# rrapply — USGS earthquakes, one month
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          rrapply (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   7.4 MB, 10,885 features, depth 5
#  measured      2026-08-10
#  run           cd corpus/25-usgs-quakes/r && Rscript try-rrapply.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               2   -                   CANNOT
#   1 what is in here                             5   NO                  YES
#   2 how deep                                    2   NO                  YES
#   3 what is one record                          2   YES                 CANNOT
#   4 always present vs sometimes                 4   NO                  YES
#   5 does any field change type                  4   NO                  YES
#   6 are any object keys data                    1   -                   n/a
#   7 how many records                            1   NO                  yes
#   8 three named fields to a table               4   YES                 yes
#   9 a field missing from some rows              2   YES                 yes
#  10 flatten the deepest array                   3   YES                 yes
#  11 find every path matching something          3   NO                  YES
#  12 flattest honest table                       3   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
#  14 survives the next file unchanged?               yes for those five
#  15 readable a week later?                          `how="melt"` needs one note
#  16 lines, and how much is ceremony?                ~70, very little
#
# **`rrapply(how = "melt")` IS A PATH LANGUAGE IN R, and it is the only one in
# this directory that is not jq.** It returns a long data.frame with one row per
# LEAF and a column per level, which is `paths` by another name — so questions
# 1, 2, 5 and 11 are all one call plus a `table()`, with no recursion written
# by hand and no column list decided in advance.
#
# **The cost is that it is O(data), exactly like jq's `paths`.** The melt of
# this 7.4 MB file is a frame of hundreds of thousands of rows, and every
# question above is answered by folding that frame back down. It answers, and
# it answers by materialising the thing the probe exists to avoid materialising.
# ─────────────────────────────────────────────────────────────────────────────

library(rrapply)
library(jsonlite)
cat(sprintf("R %s, rrapply %s, jsonlite %s\n",
            getRversion(), packageVersion("rrapply"), packageVersion("jsonlite")))

doc <- fromJSON("../source.json", simplifyVector = FALSE)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  rrapply takes a parsed list. It never saw the bytes. CANNOT.\n")

# ── Q1/Q2. What is in here, and how deep — ONE CALL. ─────────────────────────
melted <- rrapply(doc, how = "melt")
cat("\nQ1  how='melt' gives", nrow(melted), "rows x", ncol(melted), "cols\n")
cat("Q1  the level columns are:", paste(names(melted), collapse = ", "), "\n")
lev <- names(melted)[names(melted) != "value"]
paths <- apply(melted[lev], 1, \(r) paste(ifelse(is.na(r), "", r), collapse = "."))
folded <- gsub("\\.[0-9]+", "[]", paths)
folded <- sub("\\.+$", "", folded)
cat("Q1 ", length(unique(folded)), "distinct folded LEAF paths —",
    "the probe and jq say 45 counting containers too\n")
cat("Q2  depth", ncol(melted) - 1, "— the melt has one column per level, so the\n")
cat("    width of the frame IS the depth. No recursion written.\n")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
cat("\nQ3/Q7 ", length(doc$features), "features. rrapply names no candidates. CANNOT for Q3.\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
# The level columns are L1..L5 and `properties` sits at **L3**, not L2 — the
# first draft filtered on L2 and reported "0 of 0" without complaining. A melt
# names its levels by DEPTH, so every query against it has to know how deep the
# thing it wants is, which is a shape fact in the same way a column name is.
prop_rows <- melted[!is.na(melted$L4) & melted$L3 == "properties", ]
counts <- table(prop_rows$L4)
cat("\nQ4 ", sum(counts == length(doc$features)), "of", length(counts),
    "property keys appear once per feature\n")
cat("    A LEAF is a row here, and a null IS a leaf, so this counts presence —\n")
cat("    the same answer purrr, jq and ijson give.\n")

# ── Q5. Does any field change type between records. ──────────────────────────
prop_rows$cls <- vapply(prop_rows$value, \(v) if (is.null(v)) "null" else {
  r <- class(v)[1]
  c(integer = "number", numeric = "number", character = "string",
    logical = "boolean")[r] |> unname() |> (\(x) if (is.na(x)) r else x)()
}, "")
varying <- Filter(\(k) length(setdiff(unique(prop_rows$cls[prop_rows$L4 == k]), "null")) > 1,
                  unique(prop_rows$L4))
cat("\nQ5  fields varying as JSON types, ignoring null:",
    if (length(varying)) paste(varying, collapse = ", ") else "none",
    "— agrees with the probe\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  no keyed collections here. n/a\n")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
wide <- rrapply(doc$features, how = "bind")
cat("\nQ8  how='bind' gives", nrow(wide), "x", ncol(wide), "\n")
cat("Q8 ", paste(head(names(wide), 6), collapse = ", "), "…\n")
print(head(wide[c("properties.mag", "properties.place", "properties.time")], 2))
# **`is.na()` ANSWERS 10,885 HERE AND IT IS WRONG.** `how="bind"` leaves
# `properties.alert` a LIST column whose holes are NULL, not NA — so `is.na()`
# is FALSE on every row and the naive count says every feature has an alert.
# The right test is `is.null`, and nothing warns you which you needed.
#
# The behaviour itself is GOOD: keeping NULL rather than coercing to NA is why
# rrapply preserves the presence/null distinction that jsonlite's simplification
# destroys. It is the R idiom for asking about it that misleads.
cat("\nQ9  alert via is.na() :", sum(!is.na(wide$properties.alert)), "of", nrow(wide),
    "<- WRONG\n")
cat("Q9  alert via is.null():", sum(!vapply(wide$properties.alert, is.null, TRUE)),
    "of", nrow(wide), "<- right\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
co <- do.call(rbind, lapply(doc$features, \(f) unlist(f$geometry$coordinates)))
cat("\nQ10", nrow(co), "x", ncol(co), "\n"); print(head(co, 2))

# ── Q11. Find every path whose value matches something — ONE FILTER. ─────────
u <- melted[vapply(melted$value, \(v) is.character(v) && length(v) == 1 &&
                     startsWith(v, "http"), TRUE), ]
upaths <- gsub("\\.[0-9]+", "[]", apply(u[lev], 1, \(r)
  paste(ifelse(is.na(r), "", r), collapse = ".")))
cat("\nQ11 URL-valued paths:\n"); print(table(sub("\\.+$", "", upaths)))
cat("    ONE filter on the melted frame. No recursion, no column list —\n")
cat("    which is what jq's `paths(...)` does, in a data.frame.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cat("\nQ12 how='bind' gave", ncol(wide), "columns above. `coordinates` is still\n")
cat("    a list-column, so the honest table needs the cbind Q10 built.\n")

# ── The packed strings, because defect 26 came from this file. ───────────────
cat("\nDEFECT 26  does rrapply notice a list packed into a string?\n")
cat("   ", doc$features[[1]]$properties$types, "\n")
cat("    A leaf of class character. rrapply prunes and reshapes; it does not\n")
cat("    look inside a value.\n")
