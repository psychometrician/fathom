# tidyr — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          tidyr (+ jsonlite to parse; versions printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/r && Rscript try-tidyr.R
#
#  Header filled in after the run. See the CONCLUSION.
#
# **This is the same loop entry 28 needed, on a document 33x larger.** That
# entry established the shape of the problem: `unnest_longer` takes ONE LEVEL
# PER CALL, refuses a column holding a leaf and a group together, and silently
# simplifies a list-column when a level happens to be homogeneous. All three
# pieces of ceremony are kept here, unchanged, because the question is whether
# they still work at 470,673 leaves — not whether they can be avoided.

suppressMessages({library(jsonlite); library(tidyr); library(dplyr); library(tibble)})
cat(sprintf("jsonlite %s · tidyr %s · dplyr %s · R %s.%s\n",
            packageVersion("jsonlite"), packageVersion("tidyr"),
            packageVersion("dplyr"), R.version$major, R.version$minor))

t0 <- Sys.time()
doc <- fromJSON("../source.json", simplifyVector = FALSE)
cat(sprintf("parse: %.1f s\n", as.numeric(difftime(Sys.time(), t0, units = "secs"))))

cat("\nQ0  fromJSON parsed and said nothing. CANNOT.\n")

# ── Q1. One level per call. ──────────────────────────────────────────────────
one <- tibble(x = list(doc)) |> unnest_wider(x)
cat(sprintf("\nQ1  unnest_wider once -> %d x %d\n", nrow(one), ncol(one)))
cat(sprintf("    %s\n", paste(names(one), collapse = ", ")))
cat("    ONE LEVEL PER CALL, and tidyr never says how many calls are left.\n")

# ── Q12/Q2. The melt, by repeated unnest_longer. ─────────────────────────────
t0 <- Sys.time()
done <- tibble()
long <- tibble(k1 = names(doc), v = unname(doc))
calls <- 1
repeat {
  leaf <- !vapply(long$v, is.list, logical(1))
  if (any(leaf)) done <- bind_rows(done, long[leaf, ])
  long <- long[!leaf, ]
  if (!nrow(long)) break
  calls <- calls + 1
  long <- tidyr::unnest_longer(long, v, indices_to = paste0("k", calls))
  # unnest_longer SIMPLIFIES when a level is homogeneous, so `v` stops being a
  # list and the next bind_rows refuses to combine it. Forcing it back is not
  # optional and nothing warns you. Entry 28 found this; it still holds.
  long$v <- as.list(long$v)
  cat(sprintf("    call %2d -> %s rows still open\n", calls,
              format(nrow(long), big.mark = ",")))
}
long <- done
secs <- as.numeric(difftime(Sys.time(), t0, units = "secs"))
kcols <- grep("^k", names(long), value = TRUE)
cat(sprintf("\nQ12 %d unnest_longer calls -> %s rows x %d cols in %.1f s (%.1f min)\n",
            calls, format(nrow(long), big.mark = ","), ncol(long), secs, secs / 60))
cat("    PARTLY, and the loop is mine. Written straight it is twelve identical\n")
cat("    lines by someone who already knew there were twelve levels — Q13 failed.\n")

cat(sprintf("\nQ2  %d, counted from how many calls it took. yes, by exhaustion.\n",
            length(kcols)))

# ── Q3/Q7. ───────────────────────────────────────────────────────────────────
cat("\nQ3  tidyr names no candidates and prices none.\n")
cat(sprintf("      after 1 call     %d columns\n", ncol(one)))
cat(sprintf("      after %d calls   %s rows\n", calls, format(nrow(long), big.mark = ",")))
cat("    CANNOT.\n")
cat(sprintf("\nQ7  %s leaves. yes.\n", format(nrow(long), big.mark = ",")))

# ── Q4. ──────────────────────────────────────────────────────────────────────
depth_of <- rowSums(!is.na(long[, kcols]))
cat("\nQ4  leaves by depth:\n")
print(table(depth_of))

# ── Q5. THE QUESTION THIS DOCUMENT WAS CHOSEN FOR. ───────────────────────────
cls <- vapply(long$v, function(z) class(z)[1], "")
cat(sprintf("\nQ5  classes at the bottom: %s\n",
            paste(names(sort(table(cls), decreasing = TRUE)), collapse = ", ")))
print(sort(table(cls), decreasing = TRUE))
cat("    YES — and unlike rrapply's melt, the leaves stay in a LIST column, so\n")
cat("    logical and character survive side by side. That is the difference\n")
cat("    between a list-column and an atomic one, and it decides this question.\n")

cat("\nQ6  CANNOT.\n")

# ── Q8/Q9. hoist, which IS `take`. ───────────────────────────────────────────
h <- tibble(x = list(doc)) |>
  hoist(x,
        version  = list("__meta", "version"),
        mdn_url  = list("api", "ANGLE_instanced_arrays", "__compat", "mdn_url"),
        missing  = list("api", "ANGLE_instanced_arrays", "__compat", "nope"))
cat(sprintf("\nQ8  hoist() -> version = %s, mdn_url = %s\n", h$version, h$mdn_url))
cat("    yes. hoist reaches several depths in one call and is the shipped\n")
cat("    prior art for what vocabulary.md proposed `take` for.\n")
cat(sprintf("\nQ9  the missing one -> %s (%s). The row survives. YES.\n",
            format(h$missing[[1]]), class(h$missing)))
cat("    ** AND IT IS `NA`, NOT `NULL`. ** Entry 28 recorded NULL for the same\n")
cat("    call; here the hoisted column has no list to hold and tidyr simplifies\n")
cat("    it to a logical NA. Both keep the row, which is what Q9 asks — but a\n")
cat("    reader testing `is.null()` on the strength of entry 28 gets FALSE.\n")

# ── Q10. THE MELTED TABLE CANNOT ANSWER IT, AND THAT IS THE FINDING. ─────────
# A first draft indexed kcols[6] and printed 0, which is wrong on its own terms:
# bind_rows does not guarantee k1..k12 in order and indices occur at many levels.
tot <- sum(apply(long[, kcols], 1,
                 function(r) any(grepl("^[0-9]+$", trimws(as.character(r))),
                                 na.rm = TRUE)))
n_true <- 0L
tw <- function(x, ua) {
  if (is.list(x) && length(x)) {
    nm <- names(x)
    for (i in seq_along(x)) tw(x[[i]], if (is.null(nm)) TRUE else ua)
  } else if (ua) n_true <<- n_true + 1L
}
tw(doc, FALSE)
cat(sprintf("\nQ10 leaves whose melted path holds an all-digits segment: %s\n",
            format(tot, big.mark = ",")))
cat(sprintf("    leaves ACTUALLY under an array, by a typed walk        : %s\n",
            format(n_true, big.mark = ",")))
cat("    ** PARTLY, AND THE GAP IS 13x. ** Two facts were established rather\n")
cat("    than assumed, and together they say the melted table has lost it:\n")
cat("      1. unnest_longer DOES emit an integer position for an array and a\n")
cat("         character name for an object — both were reproduced in isolation.\n")
cat("      2. bind_rows then REFUSES to combine them: `Can't combine <integer>\n")
cat("         and <character>`. Every k column here arrives character.\n")
cat("    So the array/object distinction exists at unnest time and is not in\n")
cat("    the finished table. ** By what exact route the loop loses it is NOT\n")
cat("    ESTABLISHED ** and is recorded that way rather than guessed.\n")
cat("    What IS settled is that no regex over the melted path could recover\n")
cat("    it anyway: 1,076 object keys in this document are all digits —\n")
cat("    browser release versions, keyed `1`, `10`, `58`.\n")

isu <- vapply(long$v, function(z) is.character(z) && grepl("^https?://", z[1]), logical(1))
cat(sprintf("\nQ11 %s URL leaves. yes, but only after the twelve-call melt —\n",
            format(sum(isu), big.mark = ",")))
cat("    tidyr has no path search of its own.\n")

cat("
CONCLUSION. Written after the run and corrected against what printed.
")
