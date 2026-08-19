# purrr — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          purrr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/r && Rscript try-purrr.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **purrr is a list library, not a JSON library, and that is the whole result.**
# Everything below works. Nothing below is contributed BY purrr except the
# spelling — the walk is mine in every case, and `map_depth` needs the depth
# passed in, which is question 2 assumed rather than answered.

suppressMessages({library(jsonlite); library(purrr)})
cat(sprintf("jsonlite %s · purrr %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("purrr"),
            R.version$major, R.version$minor))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("parse: %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

# ── Q1. ──────────────────────────────────────────────────────────────────────
cat(sprintf("\nQ1  names(doc) -> %d: %s\n", length(doc),
            paste(names(doc), collapse = ", ")))
cat("    ONE LEVEL. Deeper needs the recursion below, which purrr does not give.\n")

# ── Q2. THE WALK, WRITTEN BY HAND. ───────────────────────────────────────────
t0 <- Sys.time()
depth <- function(x) if (!is.list(x) || !length(x)) 0L else 1L + max(map_int(x, depth))
dep <- depth(doc)
cat(sprintf("\nQ2  %d, by a recursive function I wrote (%.1f s).\n",
            dep, as.numeric(difftime(Sys.time(), t0, units = "secs"))))
cat("    `map_int` is the spelling; the recursion is mine. purrr has no depth verb.\n")

# ── Q12/Q7. The melt, by hand. ───────────────────────────────────────────────
#
# ** THE FIRST VERSION OF THIS WALK NEVER FINISHED AND THE REASON IS WORTH THE
# COMMENT. ** It accumulated with
#
#     paths$p[[length(paths$p) + 1L]] <- acc
#
# which reallocates the list on every append — QUADRATIC, and at 470,673 leaves
# it was still running after twenty minutes with no output and no error. R grows
# a list by copying it. The fix is to let the recursion RETURN its results and
# concatenate once per node, which is the functional shape purrr is for.
#
# It is my bug rather than purrr's, and it is recorded because it is the exact
# trap this question sets: everything here is hand-written, so every performance
# property is the author's problem and none of them is documented anywhere.
t0 <- Sys.time()
walk_all <- function(x, acc) {
  if (is.list(x) && length(x)) {
    nm <- names(x)
    unlist(lapply(seq_along(x), function(i)
      walk_all(x[[i]], c(acc, if (is.null(nm) || !nzchar(nm[i])) as.character(i) else nm[i]))),
      recursive = FALSE)
  } else {
    list(list(p = acc, v = x))
  }
}
flat <- walk_all(doc, character(0))
paths <- list(p = lapply(flat, `[[`, "p"), v = lapply(flat, `[[`, "v"))
secs <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
cat(sprintf("\nQ12 %s leaves in %.1f s, by a hand-written recursion.\n",
            format(length(paths$p), big.mark = ","), secs))
cat("    PARTLY — and every line of that walk is mine. purrr contributed the\n")
cat("    absence of a for loop, which is not the same as contributing a melt.\n")
cat("    The first version of it was accidentally quadratic and never returned;\n")
cat("    see the comment above. rrapply does this in 0.4 s with no walk at all.\n")
cat(sprintf("\nQ7  %s leaves. yes, once the walk exists.\n",
            format(length(paths$p), big.mark = ",")))

# ── Q4. ──────────────────────────────────────────────────────────────────────
d <- map_int(paths$p, length)
cat("\nQ4  leaves by depth:\n"); print(table(d))

# ── Q5. ──────────────────────────────────────────────────────────────────────
cls <- map_chr(paths$v, ~ class(.x)[1])
cat("\nQ5  classes at the bottom:\n"); print(sort(table(cls), decreasing = TRUE))
cat("    YES — the values stay in a list, so the types survive. Same as tidyr's\n")
cat("    list-column and unlike rrapply's atomic melt.\n")
va <- map_lgl(paths$p, ~ "version_added" %in% .x)
cat("    version_added:\n"); print(sort(table(cls[va]), decreasing = TRUE))

# ── Q3. ──────────────────────────────────────────────────────────────────────
cat("\nQ3  purrr names no candidates and prices none. CANNOT.\n")
cat("\nQ6  CANNOT.\n")

# ── Q8/Q9. pluck, which reaches depth in one call. ───────────────────────────
got <- pluck(doc, "api", "ANGLE_instanced_arrays", "__compat", "mdn_url")
cat(sprintf("\nQ8  pluck() -> %s\n", got))
cat("    yes. `pluck` IS the reach-several-levels verb, and it is the closest\n")
cat("    purrr comes to contributing something here.\n")
miss <- pluck(doc, "api", "ANGLE_instanced_arrays", "__compat", "nope")
cat(sprintf("\nQ9  a missing name -> %s. YES — pluck returns NULL, no error.\n",
            ifelse(is.null(miss), "NULL", "?")))

# ── Q10/Q11. ─────────────────────────────────────────────────────────────────
idx <- map_lgl(paths$p, ~ any(grepl("^[0-9]+$", .x)))
cat(sprintf("\nQ10 %s leaves under an array index. yes, from the same walk.\n",
            format(sum(idx), big.mark = ",")))

isu <- map_lgl(paths$v, ~ is.character(.x) && length(.x) && grepl("^https?://", .x[1]))
cat(sprintf("\nQ11 %s URL leaves. yes — keep_at over the walk's output.\n",
            format(sum(isu), big.mark = ",")))
cat("    But the walk is mine, so this is Q12's answer filtered, not a search.\n")

cat("
CONCLUSION. Written after the run and corrected against what printed.

EVERYTHING IN THIS FILE WORKS AND ALMOST NONE OF IT IS purrr's. The walk is
mine, the depth function is mine, the URL filter is a comprehension over the
walk's output. purrr supplies `map_int` and `map_chr` as the spelling of a loop
and `pluck` as a reach-several-levels accessor. It is a list library meeting a
document, and the meeting is polite rather than useful.

`pluck` IS THE ONE REAL CONTRIBUTION: a path of names, NULL rather than an
error when one is missing, no ceremony. That is question 8 and question 9
answered together, and it is the same shape as tidyr's `hoist` and glom's spec.

IT ANSWERS QUESTION 5 CORRECTLY, WHICH rrapply DOES NOT. The leaves stay in a
LIST, so 353,345 characters and 117,328 logicals survive side by side, and
version_added comes out 228,083 and 57,103 — matching jq exactly. The
difference between purrr and rrapply here is entirely list-column versus atomic
vector, and it decides the question this document was chosen for.

ITS Q10 NUMBER IS THE PATH-STRING OVER-COUNT, 75,791 against the true 70,420,
identical to rrapply's and pydash's. Same reasoning, same blind spot: 1,076
object keys in this document are all digits.

AND THE FIRST VERSION OF THE WALK NEVER RETURNED. It appended to a list inside
the recursion, which is quadratic in R, and at 470,673 leaves it ran for twenty
minutes with no output and no error before being killed. Rewritten to return
and concatenate, it finishes in under three seconds. THAT IS THE REAL COST OF
`the walk is mine`: not the eleven lines, but that every performance property
of those eleven lines is the author's problem and none of them is written down
anywhere. rrapply does the same job in 0.4 s and cannot be got wrong.
")
