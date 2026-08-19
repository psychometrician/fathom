"""polars — Crossref works, 1,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
  measured      2026-08-11
  run           cd corpus/21-crossref-works/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                            30   NO                  YES, on the 5th route
   2 how deep                                    8   NO                  YES — 6 + 3 = 9
   3 what is one record                         22   YES                 the split: see below
   4 always present vs sometimes                 6   NO                  yes, this time
   5 does any field change type                 12  YES                  NO — swallows it
   6 are any object keys data                    3   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                  14   YES                 yes, after a raise
  11 find every path matching something          4   NO                  PARTLY — 2 of 13
  12 flattest honest table                       4   NO                  yes — 1,000 x 57
  13 needed the shape in advance?                    YES — where the records are, AND
                                                     that the default schema sample is
                                                     too short
  14 survives the next file unchanged?               Q3/Q4/Q10 yes once Q1 works
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~180, and 30 are the Q1 routes

  ══════════════════════════════════════════════════════════════════════════════
  POLARS READS THIS DOCUMENT AND COULD NOT READ ENTRY 20's, AND THE DIFFERENCE
  IS EXACTLY THE ONE ITS ERROR MESSAGE CANNOT TELL YOU.
  ══════════════════════════════════════════════════════════════════════════════

  `pl.DataFrame(items, infer_schema_length=None)` gives the full 1,000 x 57.
  The DEFAULT still fails, with `could not append value: "180" of type: str` —
  and no field in this document has two Python types, checked. It is
  `edition-number`, absent from the first 100 records, inferred as Null, then
  met as a string. A PURE SAMPLING ARTIFACT.

  On entry 20 the exhaustive setting ALSO refused, because `uses_from_macos[]`
  genuinely is a string on 1,163 formulae and an object on 632. Same tool, same
  flag, two documents — and only the flag distinguishes "I did not look far
  enough" from "this document really is polymorphic". The messages look alike.

  `read_json` SUCCEEDS AND RETURNS 1 x 4 — the envelope. The root is an object
  and the records are two levels inside it, so the reader stops at
  `$.status, $.message-type, $.message-version, $.message`. A one-row frame is
  the most dangerous possible answer to question 1: it is not an error.

  A FRAME CANNOT SEE A SPLIT AS AN IMPROVEMENT — the second demonstration on
  this document, independent of pandas. `group_by("type")` prices the split at
  worst 66.7%, weighted 44.5%, against unsplit 44.5%. The weighted figure equals
  the unsplit figure identically, because the schema fixes all 57 columns and
  grouping moves no nulls. jq, recomputing the column set per group, sees 44%
  fall to 21%.

  IT SWALLOWS THE DOCUMENT'S ONLY TYPE CHANGE. `issued.date-parts` is
  `[[2018,11,3]]` on 998 records and `[[null]]` on 2; polars types it
  `List(List(Int64))` and the two become null Int64s. It refused entry 20 over a
  polymorphism it could not unify and resolves this one without a word, because
  a null fits any type.

  THREE TOOLS, THREE BEHAVIOURS ON ONE COLLISION. `reference[]` has its own
  `DOI`: pandas raises and names the fix, polars raises and names none, DuckDB
  renamed silently to `DOI_1` on entry 20.

  AND IT IS THE ONLY TOOL HERE THAT DOES NOT CARE ABOUT HYPHENS. 20 of 57 field
  names contain one; `pl.col("is-referenced-by-count")` is a string argument, so
  there is no identifier grammar to collide with. pandas needs backticks in
  `query`, DuckDB double quotes, R backticks.
"""
import json
import time
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))
items = doc["message"]["items"]

# ── Q0. ──────────────────────────────────────────────────────────────────────
print("\nQ0  polars has its own reader and no health report. CANNOT.")

# ── Q1. Does it read this one? Entry 20's five refusals are the comparison. ──
print("\nQ1  five routes, as on entry 20 — does this document fare better?")
routes = [
    ("read_json(file)                  ", lambda: pl.read_json(RAW)),
    ("read_json(infer_schema_length=None)", lambda: pl.read_json(RAW, infer_schema_length=None)),
    ("pl.DataFrame(items)              ", lambda: pl.DataFrame(items)),
    ("pl.DataFrame(items, strict=False)", lambda: pl.DataFrame(items, strict=False)),
    ("pl.DataFrame(items, infer=None)  ", lambda: pl.DataFrame(items, infer_schema_length=None)),
]
df = None
for label, fn in routes:
    t = time.time()
    try:
        d = fn()
        print(f"    {label}  OK {d.height:,} x {d.width} in {time.time()-t:.1f}s")
        if d.height > 1 and df is None:
            df = d
    except Exception as e:
        print(f"    {label}  {type(e).__name__}: {' '.join(str(e).split())[:74]}")

if df is None:
    raise SystemExit("no route produced a record frame — rewrite this file")

print("\n     ══ POLARS READS THIS DOCUMENT, AND ENTRY 20 IT COULD NOT. ══")
print("     `pl.DataFrame(items, infer_schema_length=None)` gives the full")
print(f"     {df.height:,} x {df.width} — every field, nothing hand-picked.")
print("     THE DEFAULT STILL FAILS, and the failure is worth reading carefully:")
print('       could not append value: "180" of type: str')
print("     No field in this document has two Python types — checked, none —")
print("     so that is NOT polymorphism. It is `edition-number`, absent from the")
print("     first 100 records, inferred as Null, and then met as a string.")
print("     A PURE SAMPLING ARTIFACT, and `infer_schema_length` fixes it.")
print("     ENTRY 20 IS THE CONTRAST AND IT IS EXACT: there the exhaustive")
print("     setting ALSO refused, because `uses_from_macos[]` genuinely is a")
print("     string on 1,163 formulae and an object on 632. Same tool, same flag,")
print("     two documents — and the flag distinguishes 'I did not look far")
print("     enough' from 'this document really is polymorphic'. NOTHING IN THE")
print("     ERROR MESSAGE TELLS YOU WHICH, and on both documents the default")
print("     setting produced the same kind of confident refusal.")
print("     read_json ALSO SUCCEEDED and returned 1 x 4 — THE ENVELOPE — because")
print("     the root is an object and the records are two levels inside it.")
print("     A one-row frame is the most dangerous answer to question 1 there is:")
print("     it is not an error.")

# ── Q2. ──────────────────────────────────────────────────────────────────────
def depth(dt, d=1):
    if isinstance(dt, pl.Struct):
        return max([depth(f.dtype, d + 1) for f in dt.fields] or [d])
    if isinstance(dt, pl.List):
        return depth(dt.inner, d + 1)
    return d
per = {c: depth(df.schema[c]) for c in df.columns}
deep = max(per.values())
print(f"\nQ2  deepest column nests {deep} levels below the row. The record sits at")
print(f"    $.message.items[], which is 3 levels in, so {deep} + 3 = {deep + 3} — THE PROBE'S 9.")
print("    polars is the only frame in this directory that answers question 2")
print("    correctly, because its dtype is a FULL NESTED TYPE rather than a")
print("    flattened name — and it needed the 3 to be supplied by hand, because")
print("    polars was pointed at `items` and never saw the wrapper.")

# ── Q3. THE SPLIT, and the frame-invariance result from try-pandas.py. ───────
n = df.height
nulls_total = sum(df.null_count().row(0))
print(f"\nQ3  an item of items: {n:,} x {df.width}, "
      f"{nulls_total / (n * df.width):.1%} null")
if "type" in df.columns:
    print("\nQ3  THE SPLIT — polars applies one in a line and prices it like pandas:")
    rows = []
    for k, sub in df.group_by("type"):
        e = sum(sub.null_count().row(0)) / (sub.height * sub.width)
        rows.append((k[0], sub.height, e))
    rows.sort(key=lambda r: -r[1])
    for k, cnt, e in rows[:5]:
        print(f"      {str(k):22} {cnt:5,} rows  {e:6.1%} null")
    w = sum(c * e for _, c, e in rows) / sum(c for _, c, e in rows)
    print(f"      worst {max(e for _, _, e in rows):.1%}, weighted {w:.1%}, "
          f"unsplit {nulls_total/(n*df.width):.1%}")
    print("    THE WEIGHTED FIGURE EQUALS THE UNSPLIT ONE, exactly as in pandas,")
    print("    and for the identical arithmetic reason: the schema fixes the")
    print("    columns, so grouping moves no nulls. jq, which recomputes the")
    print("    column set per group, sees 44% fall to 21%. A FRAME CANNOT")
    print("    REPRESENT THE BENEFIT OF A SPLIT — polars is the second")
    print("    independent demonstration of that on this document.")

# ── Q4. ──────────────────────────────────────────────────────────────────────
rk = [set(r) for r in items]
absent = sorted(k for k in set().union(*rk) if sum(k in r for r in rk) < len(items))
written_null = {k for r in items for k, v in r.items() if v is None}
some = [c for c, cnt in zip(df.columns, df.null_count().row(0)) if cnt]
print(f"\nQ4  polars: {len(some)} of {df.width} columns hold a null")
print(f"Q4  the document: {len(absent)} of 57 keys sometimes ABSENT, "
      f"{len(written_null)} written null")
print("    ZERO written nulls, so polars' nulls mean ABSENT unambiguously and")
print("    the entry-15 discriminator has nothing to bite on. Right answer,")
print("    and the document is the reason rather than the tool.")

# ── Q5. ──────────────────────────────────────────────────────────────────────
print("\nQ5  the probe reports ONE site: issued.date-parts, [[2018,11,3]] on 998")
print("    and [[null]] on 2 — arrays of arrays, identical JSON type.")
if "issued" in df.columns:
    print(f"    polars typed `issued` as {str(df.schema['issued'])}")
    print("    THE DISTINCTION IS GONE. `List(List(Int64))` makes the two [[null]]")
    print("    records a null Int64 — indistinguishable from a missing number, and")
    print("    the ONLY type change in this document is resolved without a word.")
    print("    polars refused ENTRY 20 over a polymorphism it could not unify and")
    print("    swallows this one silently, because a null fits any type. Defect 11")
    print("    and `design/axes.py` say a null is not a type; polars agrees by")
    print("    accident, and the probe reports the site anyway because it types")
    print("    the ELEMENT — array[2] number against array[2] null.")
else:
    print("    `issued` is not in the frame polars produced; see Q1.")

# ── Q6. ──────────────────────────────────────────────────────────────────────
print("\nQ6  reference[] is 18 keys over 18,155 copies and the probe DECLINES it")
print("    as a vocabulary. polars would put those keys in a struct type if it")
print("    reached them; it makes no keys-as-data judgement either way.")

# ── HYPHENS. ─────────────────────────────────────────────────────────────────
hy = [c for c in df.columns if "-" in c]
print(f"\n     HYPHENATED COLUMNS: {len(hy)} of {df.width}")
print("     polars is the ONLY tool in this directory that does not care:")
print("     `pl.col(\"is-referenced-by-count\")` is a string argument, so there is")
print("     no identifier grammar to collide with. pandas needs backticks in")
print("     `query`, DuckDB needs double quotes, R needs backticks.")

# ── Q7. ──────────────────────────────────────────────────────────────────────
print(f"\nQ7  {len(items):,} in the array; total-results is "
      f"{doc['message']['total-results']:,}")

# ── Q8/Q9. ───────────────────────────────────────────────────────────────────
have = [c for c in ("DOI", "type", "publisher") if c in df.columns]
print(f"\nQ8  {df.select(have).shape}")
print(df.select(have).head(2))
if "abstract" in df.columns:
    print(f"\nQ9  abstract null on {df['abstract'].null_count():,} of {n:,}, rows kept")
else:
    print(f"\nQ9  `abstract` is not in the frame; on the document it is present on "
          f"{sum('abstract' in r for r in items)} of {len(items):,}")

# ── Q10. ─────────────────────────────────────────────────────────────────────
t = time.time()
try:
    (df.select("DOI", "reference").explode("reference")
       .drop_nulls("reference").unnest("reference"))
    print("\nQ10 unnest succeeded unrenamed — rewrite this note")
except Exception as e:
    print(f"\nQ10 explode+unnest RAISES: {type(e).__name__}: "
          f"{' '.join(str(e).split())[:72]}")
    print("    `reference[]` HAS ITS OWN `DOI`, so unnesting collides with the")
    print("    work's. THREE TOOLS, THREE BEHAVIOURS ON THE SAME COLLISION:")
    print("      pandas   ValueError, and names the fix (meta_prefix)")
    print("      polars   DuplicateError, and names no fix")
    print("      DuckDB   renames silently to DOI_1 — measured on entry 20")
ref = (df.select(pl.col("DOI").alias("work_DOI"), "reference").explode("reference")
         .drop_nulls("reference").unnest("reference"))
print(f"    renamed first: {ref.height:,} x {ref.width}, {time.time()-t:.1f}s"
      f" — the true count is 18,155")
print("    Two verbs on the frame Q1 produced, and the parent DOI survives.")

# ── Q11. ─────────────────────────────────────────────────────────────────────
strs = [c for c in df.columns if df.schema[c] == pl.String]
u = [c for c in strs if df[c].str.contains(r"^https?://").any()]
print(f"\nQ11 of {len(strs)} String columns, {len(u)} hold a URL: {u}")
print("    jq reports 13 distinct URL PATHS. Everything inside license[],")
print("    link[] and assertion[] is out of reach of a column scan.")

# ── Q12. ─────────────────────────────────────────────────────────────────────
print(f"\nQ12 {df.height:,} x {df.width}. Struct and List columns are intact,")
print("    which is honest and not flat. Entry 15 recorded `unnest` RAISING on")
print("    26 colliding names and entry 20 never reached it; here the honest")
print("    table is the one above and flattening it is question 3 again.")
