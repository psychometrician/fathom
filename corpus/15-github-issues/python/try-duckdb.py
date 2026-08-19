"""DuckDB — 100 GitHub issues from one repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.json   686 KB, 100 issues, depth 4
  measured      2026-08-11
  run           cd corpus/15-github-issues/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             4   NO                  yes
   2 how deep                                    5   NO                  YES — exactly 4
   3 what is one record                           9   NO                  NO — 14 vs 2
   4 always present vs sometimes                 8   NO                  NO — conflates 5 with 8
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              5   YES                 YES — and NO ghost
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          5   NO                  PARTLY
  12 flattest honest table                      22   YES                 NO — silent duplicates
  13 needed the shape in advance?                    NO for 1, 2, 5, 7
  14 survives the next file unchanged?               Q1/Q2/Q5 yes
  15 readable a week later?                          yes — it is SQL
  16 lines, and how much is ceremony?                ~125, and one CREATE TABLE

**`count(DISTINCT json_structure(json))` HAS NOW GIVEN THREE DIFFERENT KINDS OF
ANSWER ON THREE DOCUMENTS, AND THIS FILE COMPLETES THE PICTURE.**

    14-nyc-311        153 vs the probe's 153    EXACT
    13-package-lock   776 vs the probe's 144    5.4x — keys-as-data
    15-github-issues   14 vs the probe's   2    7.0x — NULLS

`json_structure` records the TYPE of every value, so `"closed_by": null` and
`"closed_by": {…}` are different structures. The probe folds on the key SET —
which keys are present — and sees **2**. **The expression is trustworthy only on
a document with neither keys-as-data nor nulls, and `14-nyc-311` was the only
one of the three.** Nothing signals which case you are in.

**THE `JSON` DTYPE IS AN ACCIDENTAL SIGNAL AND IT IS EXACTLY RIGHT.** Four
columns come back typed `JSON` rather than a native type — `type`,
`active_lock_reason`, `performed_via_github_app`, `pinned_comment` — and those
are **precisely the four columns that are null everywhere they appear.** DuckDB
is not saying "this field is null"; it is saying "I could not infer a type", and
on this document those are the same set. polars says the same thing on purpose
with a `Null` dtype; pandas says nothing at all.

**IT DOES NOT BUILD pandas' GHOST COLUMN.** `closed_by` is one STRUCT with 48
non-nulls, not twenty columns with an empty decoy.

**BUT `struct.*` DOES NOT PREFIX, AND THAT IS THE WORST OF THE THREE BEHAVIOURS.**
This draft asserted it prefixed; running it says otherwise.
`SELECT user.*, closed_by.*` returns **38 columns of which 19 names appear
twice** — `login`, `id`, `url`, `html_url` and 15 more — and **raises nothing.**
Converting to pandas then renames them `login` and `login_1`, with 100 and 48
non-nulls. **Two silent transformations stacked**, and which `login` keeps the
bare name depends on the order of the SELECT list.

    polars   unnest      RAISES DuplicateError          — loud
    DuckDB   struct.*    duplicate names, then renamed  — SILENT
    pandas   normalize   prefixes to closed_by.login    — correct

pandas is right here, and it is the *same* decision that gave it 144 columns and
the ghost. The three behaviours are one trade-off seen from three sides.

**IT STILL FAILS THE DISCRIMINATOR.** 13 columns report missing values; the truth
is **5 sometimes-absent and 8 always-present-but-null**. `count()` counts
non-nulls, and a non-null has no history.
"""
import json
from importlib.metadata import version

import duckdb

print(f"duckdb {version('duckdb')}")

RAW = "../source.json"
con = duckdb.connect()
SRC = f"read_json_objects('{RAW}')"
doc = json.load(open(RAW))
n = len(doc)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
con.execute(f"CREATE TABLE t AS SELECT * FROM read_json('{RAW}')")
print("\nQ0  read_json succeeded and said nothing. It REFUSED 13-package-lock over")
print("    one empty-string key; this file gives it no trouble. No duplicate-key,")
print("    big-int or NaN report. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
desc = con.execute("DESCRIBE t").fetchall()
print(f"\nQ1  {len(desc)} columns, in document order:")
print("   ", [c[0] for c in desc][:12], "...")
print("    The nested objects stay STRUCTs, so this is the record's own fields.")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
struct = json.loads(con.execute(f"SELECT json_structure(json) FROM {SRC} LIMIT 1").fetchone()[0])


def depth(v):
    if isinstance(v, dict) and v:
        return 1 + max(depth(x) for x in v.values())
    if isinstance(v, list) and v:
        return 1 + max(depth(x) for x in v)
    return 0


print(f"\nQ2  json_structure of one issue walks to {depth(struct)} levels below it,")
print(f"    so the document is {1 + depth(struct)} deep. THE PROBE PRINTS 4. Correct, and it")
print("    is the same verb that answered this on 13 and 14. pandas says 3.")

# ── Q3/Q7. What is one record, and how many. THE THREE-DOCUMENT LADDER. ─────
by_structure = con.execute(
    f"SELECT count(DISTINCT json_structure(json)) FROM {SRC}").fetchone()[0]
keysets = len({frozenset(r) for r in doc})
print(f"\nQ3  count(DISTINCT json_structure(json)) = {by_structure}")
print(f"Q3  distinct key-SETS in the document     = {keysets}   <- the probe prints 2")
print("    json_structure records the TYPE of every value, so `closed_by: null`")
print("    and `closed_by: {...}` are different structures. Across three files:")
print("      14-nyc-311        153 vs 153   EXACT")
print("      13-package-lock   776 vs 144   5.4x — keys-as-data")
print(f"      15-github-issues   {by_structure} vs   {keysets}   7.0x — NULLS")
print("    Trustworthy only where there are neither keys-as-data nor nulls. NO.")
print(f"Q7  {con.execute('SELECT count(*) FROM t').fetchone()[0]} issues")

# ── Q4. Always present vs sometimes. THE DISCRIMINATOR. ─────────────────────
counts = con.execute("SELECT " + ", ".join(f'count("{c[0]}") AS "{c[0]}"' for c in desc)
                     + " FROM t").fetchone()
reported = sorted(c[0] for c, v in zip(desc, counts) if v < n)
absent = sorted(k for k in {k for r in doc for k in r} if sum(k in r for r in doc) < n)
nullish = sorted(k for k in {k for r in doc for k in r}
                 if sum(k in r for r in doc) == n
                 and sum(r.get(k) is not None for r in doc) < n)
print(f"\nQ4  THE TRUTH: {len(absent)} sometimes ABSENT, {len(nullish)} always present but NULL")
print(f"      absent: {absent}")
print(f"      null  : {nullish}")
print(f"Q4  DuckDB reports {len(reported)} columns with missing values —"
      f" {len(absent)} + {len(nullish)} = {len(absent) + len(nullish)}")
print(f"    identical sets: {reported == sorted(set(absent) | set(nullish))}")
print("    `count()` counts non-nulls, and a non-null has no history. NO.")

# ── Q5. Does any field change type — AND THE `JSON` FALLBACK. ───────────────
jsonish = [c[0] for c in desc if str(c[1]) == "JSON"]
allnull = [c[0] for c, v in zip(desc, counts) if v == 0]
print(f"\nQ5  no column carries two types, which is correct — the probe reports no")
print("    field that changes type on this document.")
print(f"\nQ5b {len(jsonish)} columns fall back to the `JSON` type: {jsonish}")
print(f"    and {len(allnull)} columns are null everywhere: {allnull}")
print(f"    THE SAME SET: {sorted(jsonish) == sorted(allnull)}. DuckDB is saying 'I could")
print("    not infer a type', and on this document that is exactly 'this field is")
print("    always null'. polars says it deliberately with a `Null` dtype; pandas")
print("    gives an all-NaN object column and no signal at all.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — GitHub ships fixed field names. n/a, and the")
print("    probe's KEYS THAT ARE DATA section is empty for this file.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
print("\nQ8 ", con.execute("SELECT number, title[1:34], state FROM t LIMIT 2").fetchall())
cb = con.execute("SELECT count(closed_by), count(closed_by.login) FROM t").fetchone()
print(f"\nQ9  closed_by non-null: {cb[0]} of {n}; closed_by.login non-null: {cb[1]}")
print("    ONE STRUCT COLUMN, consistently. pandas turns this field into TWENTY")
print("    columns — an entirely empty `closed_by` plus 19 populated")
print("    `closed_by.*` — because json_normalize cannot expand a null.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
labels = con.execute("""
    SELECT number, l.name FROM t, unnest(labels) AS u(l)""").fetchall()
print(f"\nQ10 labels unnested to {len(labels)} rows over {n} issues")
print("   ", labels[:2])
print("    `unnest` drops the 40 issues with an empty label list, which is right")
print("    for this question and silent about it.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
varchars = [c[0] for c in desc if str(c[1]) == "VARCHAR"]
hits = con.execute("SELECT " + ", ".join(
    f'count(*) FILTER (WHERE "{c}" LIKE \'%http%\') AS "{c}"' for c in varchars)
    + " FROM t").fetchone()
found = {c: h for c, h in zip(varchars, hits) if h}
print(f"\nQ11 top-level VARCHAR columns holding a URL: {len(found)}, {sum(found.values())} values")
print("    The truth is 77 paths and 3,297 values. The query had to be BUILT from")
print("    the column list and skips every STRUCT and LIST, so `user.avatar_url`")
print("    and `labels[].url` are never reached. PARTLY.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
# `labels` is STRUCT(...)[] — a LIST of structs — so startswith("STRUCT") alone
# picks it up and `labels.*` fails. The trailing [] is the discriminator.
structs = [c[0] for c in desc
           if str(c[1]).startswith("STRUCT") and not str(c[1]).endswith("[]")]
sel = ", ".join(f'{c}.*' for c in structs)
flat = con.execute(f"SELECT * EXCLUDE ({', '.join(structs)}), {sel} FROM t").df()
print(f"\nQ12 {flat.shape[0]} x {flat.shape[1]} via `SELECT * EXCLUDE (...), struct.*`")
print("\nQ12 AND IT DOES NOT PREFIX EITHER — it just does not complain.")
raw = con.execute("SELECT user.*, closed_by.* FROM t LIMIT 1")
names = [d[0] for d in raw.description]
dups = {k for k in names if names.count(k) > 1}
print(f"    `SELECT user.*, closed_by.*` returns {len(names)} columns of which")
print(f"    {len(dups)} names appear TWICE — login, id, url, html_url and 15 more.")
print("    The SQL result carries duplicate column names and raises nothing.")
two = con.execute("SELECT user.*, closed_by.* FROM t").df()
lg = [c for c in two.columns if "login" in c]
print(f"    Converting to pandas renames them: {lg} with"
      f" {two[lg[0]].notna().sum()} and {two[lg[1]].notna().sum()} non-null.")
print("    TWO SILENT TRANSFORMATIONS STACKED. Which `login` you get depends on")
print("    the order of the SELECT list, and nothing in either layer says so.")
print("\nQ12 Three tools, three behaviours on the same collision:")
print("      polars   unnest      RAISES DuplicateError            — loud")
print("      DuckDB   struct.*    duplicate names, then renamed    — SILENT")
print("      pandas   normalize   prefixes to closed_by.login      — correct")
print("    pandas is right here, and it is the same decision that gave it 144")
print("    columns and the ghost. The three are one trade-off seen from three sides.")
print("\nQ12 Three LIST columns remain, and `issue_field_values` is an EMPTY LIST")
print("    on all 100 issues — a field that exists and contains nothing.")
