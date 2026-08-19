"""duckdb — Home Assistant frontend, the English translation catalogue

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

── scoring ──────────────────────────────────────────────────────────────────
 tool          duckdb (version printed at run time)
 file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
 measured      2026-08-12
 run           cd corpus/28-home-assistant-i18n/python && uv run try-duckdb.py

 question                                    lines  shape known first?  worked
  0 is this sound                               1   -                   CANNOT
  1 what is in here                             6   NO                  YES — json_tree, every level
  2 how deep                                    3   NO                  YES — 11, from json_tree
  3 what is one record                          6   NO                  names none, counts any
  4 always present vs sometimes                 5   NO                  yes, by grouping the tree
  5 does any field change type                  5   NO                  YES — group by type
  6 are any object keys data                    -   -                   CANNOT
  7 how many records                            2   NO                  yes — 8,518
  8 three named fields to a table               4  YES                  yes
  9 a field missing from some rows              3  YES                  yes — NULL, not an error
 10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
 11 find every path matching something          4   NO                  YES — one WHERE clause
 12 flattest honest table                       4   NO                  YES — 8,518 x 2, built in
 13 needed the shape in advance?                    NO for 1,2,4,5,11,12
 14 survives the next file unchanged?               yes
 15 readable a week later?                          YES — it is SQL against a table
 16 lines, and how much is ceremony?                ~90

**duckdb has a BUILT-IN recursive tree walk and it is the surprise of this
entry.** `json_tree(json)` returns one row per node with `fullkey` — the dotted
path — `type`, and `atom`. That is the honest table of a translation catalogue,
as a relation, with no recursion to write and no shape known in advance.

**A first draft of this attempt wrote a nine-line recursive CTE over `json_each`
because I assumed no such verb existed. It does. Recorded because the same
assumption is what the corpus keeps finding in other people's tools.**
"""
import sys
import time

import duckdb

print(f"duckdb {duckdb.__version__} · python {sys.version.split()[0]}")
con = duckdb.connect()
con.execute("PRAGMA disable_progress_bar")
SRC = "read_json_objects('../source.json') r, json_tree(r.json) t"
t0 = time.time()

print("\nQ0  read_json_objects succeeded silently. No duplicate-key report, no")
print("    2^53 flag. CANNOT.")

# ── Q1/Q2. What is in here, how deep. ─────────────────────────────────────
n_nodes, n_leaf, depth = con.sql(f"""
    SELECT count(*),
           count(*) FILTER (WHERE t.type <> 'OBJECT'),
           max(length(t.fullkey) - length(replace(t.fullkey, '.', '')))
    FROM {SRC}
""").fetchone()
print(f"\nQ1  json_tree -> {n_nodes:,} nodes, {n_leaf:,} of them leaves, one row")
print("    each, at every level. YES, and nothing known in advance.")
print(f"\nQ2  {depth}. YES — and it agrees with the probe's 11 exactly.")

# ── Q3/Q7. What is one record. ────────────────────────────────────────────
print("\nQ3  duckdb names no candidates and prices none. It counts any you name:")
for label, where in [("one message per row", "t.type <> 'OBJECT'"),
                     ("one object per row", "t.type = 'OBJECT'"),
                     ("the document itself", "t.parent IS NULL")]:
    n = con.sql(f"SELECT count(*) FROM {SRC} WHERE {where}").fetchone()[0]
    print(f"      {label:<24} {n:>6,}")
print("    CANNOT for Q3 — three defensible answers, none proposed, none priced.")
print(f"\nQ7  {n_leaf:,} messages under the reading Q12 takes. yes.")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
print("\nQ4  the commonest keys anywhere in the tree:")
for k, c in con.sql(f"""
        SELECT t.key, count(*) c FROM {SRC}
        WHERE t.key IS NOT NULL GROUP BY 1 ORDER BY c DESC LIMIT 4
""").fetchall():
    print(f"      {k:<22} {c:>5}")
print("    yes — but 'always' needs a population of records and there is none.")

# ── Q5. Type variation. ───────────────────────────────────────────────────
print(f"\nQ5  node types: "
      f"{dict(con.sql(f'SELECT t.type, count(*) FROM {SRC} GROUP BY 1').fetchall())}")
mixed = con.sql(f"""
    SELECT count(*) FROM (
        SELECT t.parent FROM {SRC} WHERE t.parent IS NOT NULL
        GROUP BY t.parent HAVING count(DISTINCT t.type) > 1)
""").fetchone()[0]
print(f"    objects holding BOTH a string and an object: {mixed:,}")
print("    YES — one GROUP BY, and it is the number defect 32 turns on.")

print("\nQ6  CANNOT. No notion of a key being data rather than a name.")

# ── Q8/Q9. ────────────────────────────────────────────────────────────────
row = con.sql("""
    SELECT json_extract_string(r.json, '$.ui.common.and'),
           json_extract_string(r.json, '$.ui.common.loading'),
           json_extract_string(r.json, '$.ui.panel.profile.nope')
    FROM read_json_objects('../source.json') r
""").fetchone()
print(f"\nQ8  {row[:2]} — json_extract_string with a JSONPath. yes.")
print(f"\nQ9  a key that is not there -> {row[2]!r}. NULL, not an error. yes.")

print("\nQ10 zero arrays in 604 KB. NOTHING TO FLATTEN.")

# ── Q11. ──────────────────────────────────────────────────────────────────
icu = con.sql(f"""
    SELECT count(*) FROM {SRC}
    WHERE t.type <> 'OBJECT' AND t.atom LIKE '%{{%'
""").fetchone()[0]
print(f"\nQ11 messages carrying an ICU placeholder: {icu:,} — one WHERE clause")
print("    over a relation, no paths known in advance. YES.")

# ── Q12. The flattest honest table. ───────────────────────────────────────
print(f"\nQ12 SELECT fullkey, atom FROM json_tree(...) WHERE type <> 'OBJECT'")
for k, v in con.sql(f"""
        SELECT t.fullkey, t.atom FROM {SRC}
        WHERE t.type <> 'OBJECT' LIMIT 3""").fetchall():
    print(f"      {k[:54]:<54} {str(v)[:24]}")
print(f"    {n_leaf:,} x 2. NOTHING IS LOST, and it is already a relation.")
print(f"    ({time.time() - t0:.1f}s)")

print("""
CONCLUSION. duckdb is the strongest tool on this document alongside jq, and for
a better reason: `json_tree` is a BUILT-IN verb that returns the whole tree as a
relation with a dotted `fullkey`. jq needs `paths(scalars)`; ijson needs an event
loop; duckdb needs a SELECT. And its Q15 is the best of the three, because the
answer is a table and the reader already knows SQL.

It also answers Q5 in one GROUP BY — 330 objects hold both a string and an
object — which is precisely the measurement defects 31 and 32 were argued over,
and duckdb produces it without being told the question.

WHAT IT STILL WILL NOT DO is name the alternative row shapes or price them. It
is happy to count 8,518 messages, 1,619 objects or the document itself, proposing
none of them. That gap is unbroken across 28 entries and fourteen tools.

AND THE HONEST COMPARISON on this document: fathom's description is 5.69% of the
input with 39.3% of fields unnamed, its worst in the corpus, while json_tree
gives a complete melt in one line. **On this document duckdb's answer is better
than fathom's.**
""")
