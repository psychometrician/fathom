# jsonlite — an npm lockfile, 1,657 packages keyed by install path
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed at run time)
#  file          ../source.json   759 KB, 1,657 packages, depth 5
#  measured      2026-08-11
#  run           cd corpus/13-package-lock/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   0 is this sound                               3   -                   CANNOT
#   1 what is in here                             6   YES                 PARTLY
#   2 how deep                                    2   -                   CANNOT
#   3 what is one record                           8   NO                  NO — it declines
#   4 always present vs sometimes                 5   YES                 yes
#   5 does any field change type                 14   YES                 NO by class; yes by hand
#   6 are any object keys data                    4   -                   NO
#   7 how many records                            1   YES                 yes
#   8 three named fields to a table               6   YES                 yes, with a default
#   9 a field missing from some rows              3   YES                 yes
#  10 flatten the deepest array                   5   YES                 PARTLY
#  11 find every path matching something          9   NO                  by hand
#  12 flattest honest table                       5   YES                 PARTLY
#  13 needed the shape in advance?                    NO for 4, 5, 7
#  14 survives the next file unchanged?               Q4/Q5 yes
#  15 readable a week later?                          yes
#  16 lines, and how much is ceremony?                ~120, and the URL walk is 9
#
# **jsonlite ANSWERED QUESTION 3 ON `14-nyc-311` AND DECLINES IT HERE, AND THE
# DIFFERENCE IS THE WHOLE POINT OF THIS FILE.** On entry 14, `fromJSON()` alone
# returned a 20,000 x 48 data.frame — it decided the array elements were rows and
# the union of their keys were columns, unasked. That was called the best answer
# to question 3 anywhere in the entry.
#
# **Here `fromJSON()` returns a nested LIST and stops.** `packages` is a keyed
# OBJECT, not an array, so the simplification never fires: 1,657 named elements,
# each a list. jsonlite's rectangling is triggered by arrays, and **this
# document's records live in the keys.**
#
# > That is not a bug and it is exactly the finding. The one tool that guesses a
# > row shape guesses only when the shape is announced by a JSON array. A
# > keys-as-data collection announces nothing, and the guess does not happen.
#
# **AND THE NAIVE RECOVERY FAILS LOUDLY.**
# `do.call(rbind, lapply(packages, as.data.frame))` raises
# `names do not match previous names`, because the packages are ragged — 21
# fields, only `version` on all of them, 144 distinct key-sets. Loud is better
# than silent, and it is still a wall.
#
# **AND `class()` REPORTS NO TYPE VARIATION ON A DOCUMENT THAT HAS TWO FIELDS OF
# IT.** With `simplifyVector = FALSE` a JSON object and a JSON array are **both
# `list`**, so the obvious R test finds nothing: all 310 `funding` values report
# class `list`, and they are 282 objects and 28 arrays. The JSON type has to be
# reconstructed by hand — an unnamed list is an array — and only then does R
# agree with the probe. **The obvious tool answers "nothing varies", silently.**
#
# **THE `$` PARTIAL-MATCHING TRAP IS BACK AND IT IS WORSE THAN ON ENTRY 14.**
# Three field names are prefixes of siblings — `dev`/`devDependencies`,
# `optional`/`optionalDependencies`, `peerDependencies`/`peerDependenciesMeta` —
# and all three fire. **`dev` and `optional` are BOOLEANS**, so `r$dev` returns
# TRUE or FALSE on 1,372 packages and a **list of dependency names** on one.
# A silent type change, from an accessor nobody thinks twice about.
# ─────────────────────────────────────────────────────────────────────────────

library(jsonlite)
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
pkgs <- doc$packages
cat(sprintf("    fromJSON: %.1fs\n", as.numeric(Sys.time() - t0, units = "secs")))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
cat("\nQ0  fromJSON parses and reports nothing: no duplicate-key warning, no\n")
cat("    big-integer notice, no NaN. DuckDB refuses this same file over one\n")
cat("    empty-string key; jsonlite reads it without comment. CANNOT.\n")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
fields <- table(unlist(lapply(pkgs, names)))
cat("\nQ1  top level:", names(doc), "\n")
cat("Q1 ", length(pkgs), "packages,", length(fields), "distinct fields among them\n")
cat("    PARTLY — `packages` had to be named. jsonlite has no survey verb and\n")
cat("    no path enumeration; the table above is base R over `names()`.\n")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
cat("\nQ2  jsonlite reports no depth, and here the frame gives no hint either,\n")
cat("    because there IS no frame — everything is a nested list. CANNOT.\n")

# ── Q3. What is one record — AND THE SIMPLIFICATION DECLINES. ────────────────
simplified <- fromJSON("../source.json")
cat("\nQ3  fromJSON(simplifyVector = TRUE) returns:", class(simplified$packages),
    "of length", length(simplified$packages), "\n")
cat("    NOT a data.frame. On 14-nyc-311 this same call returned 20,000 x 48\n")
cat("    unasked, and it was the best question-3 answer in that entry. Here the\n")
cat("    records live in a keyed OBJECT rather than an array, so nothing fires.\n")
naive <- try(do.call(rbind, lapply(pkgs, as.data.frame)), silent = TRUE)
cat("    do.call(rbind, lapply(pkgs, as.data.frame)) ->",
    if (inherits(naive, "try-error")) "ERROR:" else "worked?",
    trimws(strsplit(as.character(naive), ":")[[1]][2]), "\n")
cat("    The packages are ragged — 144 distinct key-sets — so the naive rbind\n")
cat("    refuses. LOUD, which beats silent, and still a wall. The probe names\n")
cat("    EIGHT candidates with costs. NO.\n")

# ── Q7. How many records. ────────────────────────────────────────────────────
cat("\nQ7 ", length(pkgs), "packages\n")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
n <- length(pkgs)
cat("\nQ4  always", sum(fields == n), "-", names(fields)[fields == n], "\n")
cat("Q4  sometimes", sum(fields < n), ", rarest five:\n")
print(head(sort(fields), 5))
cat("    Matches the probe: 21 fields and only `version` on every package.\n")

# ── Q5. Does any field change type between records. ──────────────────────────
by_class <- lapply(setNames(names(fields), names(fields)), function(k)
  unique(vapply(Filter(function(r) !is.null(r[[k]]), pkgs),
                function(r) class(r[[k]])[1], character(1))))
cat("\nQ5  by R class, fields whose class varies:",
    if (length(Filter(function(v) length(v) > 1, by_class))) "some" else "NONE", "\n")
cat("    THAT IS A FALSE NEGATIVE, and it is jsonlite's parse rather than R's.\n")
cat("    With simplifyVector = FALSE a JSON object and a JSON array are BOTH\n")
cat("    `list`, so `class()` cannot tell them apart. All 310 `funding` values\n")
cat("    report class `list` — 282 objects and 28 arrays.\n")

# The JSON type has to be reconstructed: an unnamed list is an array.
json_type <- function(v) {
  if (is.null(v)) "null"
  else if (is.list(v)) if (is.null(names(v))) "array" else "object"
  else if (is.character(v)) "string"
  else if (is.logical(v)) "boolean"
  else "number"
}
by_json <- lapply(setNames(names(fields), names(fields)), function(k)
  table(vapply(Filter(function(r) !is.null(r[[k]]), pkgs),
               function(r) json_type(r[[k]]), character(1))))
varying <- Filter(function(v) length(v) > 1, by_json)
cat("\nQ5  by JSON type, reconstructed with is.null(names(x)):\n")
for (k in names(varying)) {
  cat("   ", k, ":", paste(names(varying[[k]]), varying[[k]], collapse = ", "), "\n")
}
cat("    NOW it matches the probe:\n")
cat("      engines  object x1,050, array[1] text x1\n")
cat("      funding  object x282, array[1] object x26, array[1] text x2\n")
cat("    The right answer needed a hand-written type function. `class()` is the\n")
cat("    obvious tool and it silently reports no variation at all.\n")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
cat("\nQ6  YES — `packages` is keyed by install path and four nested collections\n")
cat("    by package name — and jsonlite cannot say so. A named list is a named\n")
cat("    list; nothing distinguishes 1,657 data keys from 21 field names.\n")
cat("    The probe prints seven keyed sites and declines an eighth.\n")

# ── THE `$` TRAP, measured. ──────────────────────────────────────────────────
cat("\nQ6b R's `$` PARTIAL-MATCHES, and three field names here are prefixes:\n")
for (s in c("dev", "optional", "peerDependencies")) {
  risky <- which(vapply(pkgs, function(r)
    !(s %in% names(r)) && any(startsWith(names(r), s)), logical(1)))
  cat(sprintf("    $%-17s silently returns a sibling on %4d of %d packages",
              s, length(risky), n))
  if (length(risky)) {
    r <- pkgs[[risky[1]]]
    got <- r[[s]]                      # exact:   NULL
    par <- eval(call("$", r, s))       # partial: the sibling
    cat(sprintf("\n    %-18s   r[[\"%s\"]] -> %s   |   r$%s -> %s of %d",
                "", s, class(got)[1], s, class(par)[1], length(par)))
  }
  cat("\n")
}
cat("    `dev` and `optional` are BOOLEANS on every package that has them, so\n")
cat("    this is a silent TYPE change: TRUE/FALSE most of the time, a list of\n")
cat("    dependency names occasionally. `[[` is exact and is used everywhere here.\n")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
tbl <- data.frame(
  path     = names(pkgs),
  version  = vapply(pkgs, function(r) r[["version"]]  %||% NA_character_, character(1)),
  license  = vapply(pkgs, function(r) r[["license"]]  %||% NA_character_, character(1)),
  row.names = NULL)
cat("\nQ8 ", nrow(tbl), "rows x", ncol(tbl), "cols\n"); print(head(tbl, 2))
cat("    `names(pkgs)` carries the install path — the row's identity is the KEY,\n")
cat("    and it has to be lifted into a column by hand.\n")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
cat("\nQ9  license non-NA on", sum(!is.na(tbl$license)), "of", nrow(tbl),
    "— `%||% NA` keeps the row\n")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
arr <- Filter(function(r) !is.null(r[["funding"]]) && is.null(names(r[["funding"]])),
              pkgs)
rows <- do.call(rbind, lapply(names(arr), function(k)
  do.call(rbind, lapply(arr[[k]][["funding"]], function(e)
    data.frame(pkg  = k,
               type = if (is.list(e)) (e[["type"]] %||% NA_character_) else NA_character_,
               url  = if (is.list(e)) (e[["url"]] %||% NA_character_) else e)))))
cat("\nQ10", nrow(rows), "funding[] rows over", length(arr), "packages\n")
print(head(rows, 2))
cat("    PARTLY: `funding` is object-or-array and its elements are\n")
cat("    object-or-string, so the test `is.null(names(...))` is doing the work\n")
cat("    of a type check R has no direct word for on a parsed list.\n")

# ── Q11. Find every path whose value matches something — by hand. ────────────
hits <- new.env(hash = TRUE)
KEYED <- c("dependencies", "devDependencies", "optionalDependencies",
           "peerDependencies", "peerDependenciesMeta", "bin")
find_url <- function(x, f = "$") {
  if (is.list(x)) {
    nm <- names(x)
    keyed <- f == "$.packages" || sub("^.*\\.", "", f) %in% KEYED
    for (i in seq_along(x)) {
      nf <- if (is.null(nm)) paste0(f, "[]")
            else if (keyed) paste0(f, ".<key>") else paste0(f, ".", nm[i])
      find_url(x[[i]], nf)
    }
  } else if (is.character(x)) {
    k <- sum(grepl("https?://", x))
    # inherits = FALSE, or an environment used as a dictionary reaches base::
    # for names like `url`. That cost entry 25 three fields.
    if (k > 0) assign(f, get0(f, hits, inherits = FALSE, ifnotfound = 0) + k, hits)
  }
}
find_url(doc)
cat("\nQ11 URL-valued paths, FOLDED by hand:\n")
for (k in ls(hits)) cat("   ", k, get(k, hits, inherits = FALSE), "\n")
cat("    Nine lines of recursion AND a hand-written fold. Without the fold this\n")
cat("    is ~1,700 paths, one per package. jqr does the same in one expression.\n")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
scalars <- names(fields)[!names(fields) %in% c(KEYED, "engines", "funding",
                                               "os", "cpu", "libc", "workspaces")]
flat <- as.data.frame(lapply(setNames(scalars, scalars), function(k)
  vapply(pkgs, function(r) {
    v <- r[[k]]
    if (is.null(v) || is.list(v)) NA_character_ else as.character(v)
  }, character(1))), row.names = NULL)
flat <- cbind(path = names(pkgs), flat)
cat("\nQ12", nrow(flat), "x", ncol(flat), "scalar columns\n")
cat("    PARTLY. The six keyed collections and the four list-valued fields had\n")
cat("    to be EXCLUDED BY NAME to keep it rectangular — a list I could only\n")
cat("    write after questions 4 and 5. Those collections are separate tables\n")
cat("    the probe prices at 2,841, 128, 104, 101, 78 and 25 rows.\n")
