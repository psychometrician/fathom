# jsonlite — ESPN NFL Quarterback Rating, 2019, the corpus's only ground truth
#
# Header shape copied from ../../01-npm-registry/r/try-purrr.R, the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jsonlite (version printed below)
#  file          ../source.json   180 KB, 28 athletes, depth 7, 131 paths,
#                                 72 fields, keyed 0, 0/56 ragged
#  measured      2026-08-10
#  run           cd corpus/06-espn-qbr/r && Rscript try-jsonlite.R
#
#  question                                    lines  shape known first?  worked
#   1 what is in here                           8   NO                  partly
#   3 what is one record                        5   NO                  YES
#   4 always present vs sometimes               4   NO                  yes
#   7 how many records                          1   NO                  yes
#   8 three named fields to a table             6   YES                 yes
#  7a related by position                      14   YES, fatally        NO
#  13 needed the shape in advance?                  no for 1, 3, 7
#  16 lines, and how much is ceremony?              see the conclusion
#
#  ⚠ 7a is CIRCULAR per QUESTIONS.md — added the same session the probe gained
#  the feature that answers it. The measurement below is a FACT about the
#  document, recorded because it is this file's whole point, and NOT a score.
# ─────────────────────────────────────────────────────────────────────────────
#
# WHY THIS FILE. `VERDICT.md` calls it **the only fair fight available**: the
# competing solution is already written, by an R educator, for publication,
# after four documented approaches — Tom Mock's *Parsing JSON in R with
# jsonlite* — and it uses **this tool**. Every other entry compares a probe
# revised against the document with tools given one attempt.
#
# `NOTES.md` records the probe's failure here: `$.categories[0].labels` names
# every statistic in the file and the probe **never mentions it**, because
# single-copy objects are dropped from the fold. And there is a decoy —
# `$.glossary` carries the same ten abbreviations in a DIFFERENT order, and the
# probe points at it.
suppressMessages(library(jsonlite))
cat(sprintf("R %s, jsonlite %s\n", getRversion(), packageVersion("jsonlite")))

path <- "../source.json"
simp <- fromJSON(path)
doc  <- fromJSON(path, simplifyVector = FALSE)

# ── Q3 / Q7. THE GROUND TRUTH. ───────────────────────────────────────────────
cat("\n3/7. what is one record, and how many:\n")
cat(sprintf("   fromJSON() gives a %s with %d top-level names\n",
            class(simp)[1], length(simp)))
cat(sprintf("   $athletes is a %s: %d x %d\n", class(simp$athletes)[1],
            nrow(simp$athletes), ncol(simp$athletes)))
cat("   PREDICTION 4 CONFIRMED, and this is the corpus's only scored answer to\n")
cat("   question 3. The tutorial's row is one quarterback. jsonlite returns 28\n")
cat("   of them without being asked and without a verb being chosen.\n")
cat("   The frame has 2 columns because both are nested — `athlete` and\n")
cat("   `categories` — so the 32 columns the probe offers and the 14 the\n")
cat("   tutorial keeps are both below this level. That is `take`'s job.\n")

# ── Q1. THE SINGLE-COPY OBJECT THE PROBE SKIPS. ──────────────────────────────
cat("\n1. what is in here — str(), and PREDICTION 3:\n")
for (lv in 2:4) {
  o <- capture.output(str(simp, max.level = lv))
  cat(sprintf("   level %d: %4d lines | mentions glossary %-5s | mentions labels %s\n",
              lv, length(o), any(grepl("glossary", o)), any(grepl("labels", o))))
}
cat("   PREDICTION 3 CONFIRMED. `labels` IS VISIBLE, at every level from 2.\n")
cat("   NOTES.md records the probe never mentioning it in 44 lines, because\n")
cat("   `len(objs) < 2` drops single-copy objects from the fold. jsonlite has\n")
cat("   no such rule, so the thing the load-bearing idea discards is simply\n")
cat("   there. Third time an existing tool surfaces what the probe's own fold\n")
cat("   throws away, after jqr and rrapply on 03-natural-earth.\n")

# ── 7a. THE DECOY. PREDICTION 2, AND IT IS HALF WRONG. ───────────────────────
cat("\n7a. related by position — the decoy, and what simplification does with it:\n")
lab <- unlist(doc$categories[[1]]$labels)
glo <- simp$glossary$abbreviation
cat(sprintf("   $glossary            %s: %d x %d — a clean table\n",
            class(simp$glossary)[1], nrow(simp$glossary), ncol(simp$glossary)))
cat(sprintf("   $categories$labels   %s of %d — nested inside a 1-row frame\n",
            class(simp$categories$labels)[1], length(lab)))
cat(sprintf("   labels   %s   <- the real order\n", paste(lab, collapse = " ")))
cat(sprintf("   glossary %s   <- alphabetical\n", paste(glo, collapse = " ")))
cat("   PREDICTION 2 IS HALF WRONG AND THE CORRECTION MATTERS. I predicted\n")
cat("   simplification would BURY the right array. It does not — `labels` shows\n")
cat("   at str() level 2, same as `glossary`. What it does is make the WRONG\n")
cat("   one INVITING: `glossary` arrives as a 10 x 2 data frame you can join\n")
cat("   against, and `labels` arrives as a list inside a one-row frame that has\n")
cat("   to be unlisted first. Equally visible, not equally usable.\n")

# And what the wrong join actually produces. The reason this file is a trap.
tot <- as.numeric(unlist(doc$athletes[[1]]$categories[[1]]$totals))
who <- doc$athletes[[1]]$athlete$displayName
cat(sprintf("\n   %s's ten totals: %s\n", who, paste(tot, collapse = " ")))
cat("   the same ten numbers under each join:\n")
cat("     position   1        2        3      ...   TQBR\n")
cat(sprintf("     labels    %-8s %-8s %-6s       %s = %s\n",
            lab[1], lab[2], lab[3], "TQBR", tot[which(lab == "TQBR")]))
cat(sprintf("     glossary  %-8s %-8s %-6s       %s = %s\n",
            glo[1], glo[2], glo[3], "TQBR", tot[which(glo == "TQBR")]))
cat(sprintf("   THE LEAGUE'S TOP-RATED QUARTERBACK, TQBR %s OR %s.\n",
            tot[which(lab == "TQBR")], tot[which(glo == "TQBR")]))
cat("   AND THE WRONG JOIN IS PARTLY RIGHT, WHICH IS WHY IT SURVIVES: position\n")
cat(sprintf("   2 is `PA` in BOTH orders, so `PA = %s` is correct either way.\n", tot[2]))
cat("   A join that produces some correct values and plausible numbers for the\n")
cat("   rest, with no error, is the failure this project exists to care about.\n")
cat("   jsonlite does not point at either array. It hands you both and the\n")
cat("   tabular one is the wrong one.\n")

# ── Q4 / Q8. ─────────────────────────────────────────────────────────────────
cat("\n4. always present vs sometimes:\n")
ks <- lapply(doc$athletes, names)
cat(sprintf("   %d athletes, %d distinct key-set(s) — NOTES.md grades 0/56 ragged\n",
            length(ks), length(unique(vapply(ks, function(x)
              paste(sort(x), collapse = ","), "")))))

cat("\n8. three named fields, one row per quarterback:\n")
ath <- simp$athletes$athlete
tbl <- data.frame(name = ath$displayName, team = ath$teamName,
                  qbr = vapply(doc$athletes, function(a)
                    as.numeric(a$categories[[1]]$totals[[1]]), 0))
cat(sprintf("   -> %d x %d, no `%%||%%` needed anywhere\n", nrow(tbl), ncol(tbl)))
print(utils::head(tbl[order(-tbl$qbr), ], 3))
cat("   `totals[[1]]` IS THE PROBLEM IN ONE EXPRESSION. It is correct, and it\n")
cat("   is correct only because `labels[1]` is `TQBR` — a fact from a different\n")
cat("   branch of the document that nothing in this line records. Written as\n")
cat("   `[[1]]`, it is a magic number; the tutorial writes the same thing.\n")

cat("
CONCLUSION — the fair fight, and jsonlite wins the half nobody was arguing about.

  **It answers question 3 unprompted and correctly**, which is the only scored
  answer in the corpus: 28 quarterbacks, the row a published tutorial chose,
  with no verb selected and no shape known first. Question 8 needs no `%||%`
  anywhere — `NOTES.md` grades this file `0/56` ragged — so extraction is three
  clean lines against the tutorial's `pluck` chain per athlete.

  **PREDICTION 3 HELD: `labels` is visible.** The probe never mentions it in 44
  lines, because `len(objs) < 2` drops single-copy objects from the fold, and a
  document's description of itself characteristically appears once. jsonlite has
  no such rule, so the most important object in the file is simply present in
  `str()` from level 2. **Third time an existing tool surfaces what the probe's
  load-bearing idea discards.**

  **PREDICTION 2 WAS HALF WRONG, AND THE CORRECTION IS SHARPER THAN THE
  PREDICTION.** I expected simplification to bury the right array. It does not —
  both appear at level 2. What it does is make the **wrong one inviting**:
  `glossary` becomes a 10 x 2 data frame that is ready to join, `labels` becomes
  a list inside a one-row frame that must be unlisted. Equally visible, not
  equally usable, and the usable one is alphabetical.

  Joined by position against `glossary`, the league's top-rated quarterback has
  a Total QBR of **-7.4** instead of **83.0** — and `PA = 66.7` is correct under
  both orders, because position 2 happens to agree. **A wrong answer that is
  partly right, entirely plausible, and silent.**

  SO THE FAIR FIGHT SPLITS. On extracting, jsonlite and the published tutorial
  are excellent and this project has nothing to add. On the question of *which
  of these two ten-element arrays names your columns*, jsonlite hands you both,
  formats the wrong one more attractively, and says nothing — and the tutorial
  sidesteps it by writing `[[1]]` and knowing what that means.
")
