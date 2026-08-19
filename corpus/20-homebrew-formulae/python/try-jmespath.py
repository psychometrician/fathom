"""jmespath — Homebrew's whole formula index

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
  measured      2026-08-11
  run           cd corpus/20-homebrew-formulae/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                            14   NO                  PARTLY — one level
   2 how deep                                    3   -                   CANNOT
   3 what is one record                          1   -                   CANNOT
   4 always present vs sometimes                 9   NO                  YES for absent, no for null
   5 does any field change type                  6   YES                 PARTLY
   6 are any object keys data                    9   YES                 PARTLY
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes — its best answer
   9 a field missing from some rows              9   YES                 yes
  10 flatten the deepest array                  10   YES                 yes, then loses the parent
  11 find every path matching something          8   YES                 CANNOT
  12 flattest honest table                       3   YES                 CANNOT
  13 needed the shape in advance?                    YES for 5, 6, 9, 10, 11 — and for
                                                     1 and 6 you must know the RAGGEDNESS
                                                     too, or the query raises
  14 survives the next file unchanged?               no — every guard is document-specific
  15 readable a week later?                          yes, and that is its real strength
  16 lines, and how much is ceremony?                ~130, expressions are 1 line each
  timing        every query under 0.2s on 29.6 MB, the fastest tool in this directory

  `keys()` RAISES ON A NULL AND KILLS THE WHOLE QUERY. `[].bottle.stable.keys(@)`
  fails with JMESPathTypeError because FIVE formulae of 8,536 have no `bottle`.
  Not a null row in the result — a hard error. THE MIRROR OF PANDAS' record_path
  RAISE: both refuse a ragged path rather than skipping it, and both make you
  know the raggedness before you may ask about it. The guarded form
  `[?bottle].bottle.stable.keys(@) | []` works and had to be written twice here.

  ENTRY 15'S RECLASSIFICATION HOLDS AT SCALE. `[].keys(@) | []` counts PRESENCE,
  so it reports the 3 sometimes-absent fields exactly and is not fooled by the
  17 written nulls. That is why entry 15 moved jmespath out of the frames and in
  with the walkers, and this document confirms it on 8,536 records.

  IT CANNOT COUNT PATHS AT ALL. There is no recursive descent — no `..`, no
  `paths()` — so question 11 is not "hard" here, it is inexpressible. jq, ijson,
  glom and pydash all independently report 65 URL paths naively and 48 strictly;
  jmespath can evaluate any path you write down and enumerate none.

  Its best answer is question 10, `[].patches[].resolves[]` — four tokens for the
  correct 557 — and the same operator is its worst, because flattening DROPS the
  parent. The form that keeps `name` returns a list-column instead of rows. Note
  also that the obvious guard `[?r != null]` returns all 8,536 and looks like it
  worked: an absent `patches` flattens to an EMPTY ARRAY, not null.
"""
import json
import re
import time
from collections import Counter
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")

RAW = "../source.json"
doc = json.load(open(RAW))


def q(expr, data=None):
    t = time.time()
    return jmespath.search(expr, doc if data is None else data), time.time() - t


# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  jmespath is an expression language over a parsed object. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
keys, t = q("[].keys(@) | []")
print(f"\nQ1  `[].keys(@) | []` gives {len(keys):,} key occurrences in {t:.1f}s;")
print(f"    {len(set(keys))} distinct root field names.")
print("    THAT IS ONE LEVEL. jmespath has no recursive descent — no `..`, no")
print("    `paths()` — so 'the fields at every level' means naming every level.")
print("    AND NAMING THE NEXT LEVEL RAISES:")
try:
    q("[].bottle.stable.keys(@) | []")
    print("    [].bottle.stable.keys(@) succeeded — rewrite this note")
except Exception as e:
    print(f"    [].bottle.stable.keys(@)  {type(e).__name__}: {str(e)[:88]}")
    print("    FIVE formulae have no `bottle`, so the projection yields null and")
    print("    `keys(null)` is a hard TypeError that kills the whole query — not")
    print("    a null row in the result. THE MIRROR OF PANDAS' record_path RAISE:")
    print("    both tools refuse a ragged path rather than skipping it, and both")
    print("    need you to know the raggedness before you may ask about it.")
lvl2, _ = q("[?bottle].bottle.stable.keys(@) | []")
print(f"    guarded: `[?bottle].bottle.stable.keys(@) | []` -> {sorted(set(lvl2 or []))}")
print("    The probe reports 1,132 distinct paths. jmespath will report any one")
print("    of them you can already name AND guard, which is the wrong direction")
print("    for question 1 twice over.")

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
print("\nQ2  CANNOT. There is no recursive form, so depth cannot be computed —")
print("    only confirmed, one hand-written level at a time. Entry 18 recorded")
print("    the same CANNOT on the corpus's deepest document.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
n, _ = q("length(@)")
print(f"\nQ3  jmespath names no candidates and prices none. CANNOT.")
print(f"Q7  {n:,} formulae, from `length(@)`")

# ── Q4. Always present vs sometimes. THE ONE ENTRY 15 CORRECTED. ─────────────
present = Counter(keys)
absent = {k: c for k, c in present.items() if c < n}
print(f"\nQ4  from `[].keys(@) | []`, keys not on every record: {absent}")
print("    CORRECT, and it is the reason entry 15 moved jmespath OUT of the")
print("    frames and in with the walkers: `keys(@)` is PRESENCE, so a key")
print("    written as null still counts. This document confirms it at scale.")
null_fields = sorted({k for f in doc for k, v in f.items() if v is None})
print(f"Q4  always-present-but-null fields: {len(null_fields)}")
print("    Those needed python. jmespath has no `is null` predicate that can be")
print("    applied across an unknown key set — you can test one named key at a")
print("    time, which is 61 expressions on this document.")
one, t = q("length([?caveats == null])")
print(f"    e.g. `length([?caveats == null])` -> {one:,}, in {t:.1f}s. One field, one query.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  jmespath has `type()`, and no way to map it over an unknown key set.")
for f in ("uses_from_macos", "service", "license"):
    kinds, t = q(f"[].{f} | [] | [].type(@)")
    print(f"    [].{f} | [] | [].type(@) -> {dict(Counter(kinds or []))}")
print("    `uses_from_macos` shows both element types, correctly — because I")
print("    named the field. The probe found nine such sites without being told")
print("    any of them, and finding them is the whole of question 5.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  the unguarded form RAISES for the second time, same cause:")
try:
    q("[].bottle.stable.files.keys(@) | []")
    print("    unguarded succeeded — rewrite this note")
except Exception as e:
    print(f"    [].bottle.stable.files.keys(@)  {type(e).__name__}: {str(e)[:70]}")
plat, t = q("[?bottle].bottle.stable.files.keys(@) | []")
print(f"    guarded: {len(set(plat or [])):,} distinct keys over {len(plat or []):,} "
      f"occurrences, {t:.1f}s")
print("    The ingredients again, and no verdict again — and this time you had")
print("    to know the path AND that it is sometimes missing. jq finds the site")
print("    by walking; jmespath needs it named and guarded before it will look.")

# ── Q8. Three named fields into a table. THE THING IT IS BEST AT. ────────────
tbl, t = q("[].{name: name, desc: desc, homepage: homepage}")
print(f"\nQ8  one multiselect-hash: {len(tbl):,} rows x 3, {t:.1f}s")
print(f"    {tbl[0]}")

# ── Q9. A field missing from some records, keeping those rows. ───────────────
kept, t = q("[].{name: name, ex: executables}")
n_null = sum(r["ex"] is None for r in kept)
print(f"\nQ9  {len(kept):,} rows kept, `ex` null on {n_null:,}, {t:.1f}s")
print("    A multiselect-hash keeps the row and writes null for the missing key,")
print("    which is right. It is also indistinguishable from a written null:")
both = q("[].{name: name, ex: executables, cav: caveats}")[0]
row = next(r for r in both if r["ex"] is None and r["cav"] is None)
src = next(f for f in doc if f["name"] == row["name"])
print(f"    `executables` is ABSENT on 185 records and `caveats` is written NULL")
print(f"    on 8,010. On {row['name']!r} both are true: 'executables' in record = "
      f"{'executables' in src}, record['caveats'] = {src['caveats']!r}")
print(f"    and in the jmespath table they are the same value: "
      f"ex={row['ex']!r}, cav={row['cav']!r}")
print("    Q4's distinction survives `keys(@)` and dies the moment you build a")
print("    table, which is the same boundary every frame in this corpus sits on.")

# ── Q10. Flatten the deepest array into rows. THE FLATTENING TRAP. ───────────
res, t = q("[].patches[].resolves[]")
print(f"\nQ10 `[].patches[].resolves[]` -> {len(res or []):,} rows, {t:.1f}s")
print("    THE TRUE COUNT IS 557 and the expression is four tokens — jmespath's")
print("    flattening operator is the best answer to Q10 in either language.")
withname, t = q("[].{n: name, r: patches[].resolves[]} | [?length(r) > `0`]")
rows = sum(len(x["r"]) for x in (withname or []))
print(f"    keeping the formula name: {len(withname or []):,} formulae, {rows:,} resolves, {t:.1f}s")
print("    and THAT is the trap — the flat form DROPS the parent, and the form")
print("    that keeps it returns a LIST-COLUMN, not rows. Getting one row per")
print("    resolve WITH its formula name needs a python loop after jmespath.")
print("    NOTE the guard is `length(r) > \\`0\\`` and not `r != null`: a formula")
print("    with no patches yields an EMPTY ARRAY here, not null, so the obvious")
print("    filter returns all 8,536 and looks like it worked.")
print("    Entry 18 recorded `[].patches[].resolves[]`-shaped flattening as both")
print("    jmespath's best and worst answer on one document; same here.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
print("\nQ11 CANNOT, in the sense the question means. There is no recursive")
print("    descent, so 'every path' cannot be expressed. Named paths work:")
for expr in ("[].homepage", "[].urls.stable.url", "[].patches[].url"):
    v, t = q(expr)
    vals = [x for x in (v or []) if isinstance(x, str)]
    nn = sum(x.startswith("http") for x in vals)
    ns = sum(bool(re.match(r"^https?://", x)) for x in vals)
    print(f"    {expr:26} {len(vals):>6,} strings, {nn:>6,} http-prefixed, {ns:>6,} ^https?://")
print("    jq, ijson, glom and pydash all report 65 and 48 distinct URL PATHS.")
print("    jmespath cannot report a path count at all, because it has no way to")
print("    enumerate paths — only to evaluate ones you already wrote down.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 a multiselect-hash naming all 61 root fields would work and would")
print("    stop at the first nested value. There is no auto-flatten and no")
print("    `**`. What is lost is everything below level 1, silently.")
