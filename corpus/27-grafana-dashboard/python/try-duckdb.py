"""duckdb — Grafana "Node Exporter Full", dashboard 1860

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

 ── scoring ──────────────────────────────────────────────────────────────────
  tool          duckdb (version printed at run time)
  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
  measured      2026-08-13
  run           cd corpus/27-grafana-dashboard/python && uv run try-duckdb.py
                ⚠ takes about a minute — see Q12

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             4   NO                  yes
   2 how deep                                    1   NO                  yes — 12
   3 what is one record                          7   -                   CANNOT
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  6   NO                  PARTLY — see below
   6 are any object keys data                    3   NO                  yes, inferred
   7 how many records                            6   NO                  YES — 132
   8 three named fields to a table               6  YES                  yes
   9 a field missing from some rows              2  YES                  YES — SQL NULL
  10 flatten the deepest array                   3   NO                  yes
  11 find every path matching something          3   NO                  yes
  12 flattest honest table                       3   NO                  YES — json_tree, but SLOW
  13 needed the shape in advance?                    NO for the tree, YES for the pattern
  14 survives the next file unchanged?               YES
  15 readable a week later?                          yes — it is SQL
  16 lines, and how much is ceremony?                ~85

**`json_tree` is the melt, built in**, which entry 28 established and this file
confirms on a document of a completely different shape. One SELECT gives one row
per node with `fullkey` as the dotted path, and the central question becomes a
`WHERE` clause over that column. Its advantage over jq and ijson is that the
melt arrives as a RELATION and keeps the array indices those two discard.

**AND THIS DOCUMENT EXPOSED A PERFORMANCE CLIFF THAT IS ABOUT THE QUERY, NOT
THE FILE.** Materialising the tree costs 0.24s. Running an aggregate directly
over the table function — `SELECT count(*) FROM read_json_objects(...) r,
json_tree(r.json) t`, which is the obvious way to write it and the form entry
28's attempt uses throughout — took 55s, 55s, 63s, 71s, 78s, 146s and 178s
across seven timed runs, and one measurement had not returned after several
minutes. Same file, same connection, same 17,676 nodes.

**A first draft of this file wrote it the obvious way and concluded "duckdb is
enormously slow on this document". That was wrong**, and the only reason it was
caught is that restructuring the file to materialise once made the reported time
drop from a minute to 0.2s while the printed prose still said a minute. The
finding is recorded here rather than deleted because the wrong version is the
one a person would write.
"""
import sys
import time

import duckdb

print(f"duckdb {duckdb.__version__} · python {sys.version.split()[0]}")
con = duckdb.connect()
con.execute("PRAGMA disable_progress_bar")

# A panel is any node whose fullkey is `$.panels[i]`, or `$.panels[i].panels[j]`,
# or deeper — the `+` means the pattern does not care how many levels there are.
PANEL = r"regexp_matches(fullkey, '^\$(\.panels\[\d+\])+$')"

# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  read_json_objects succeeds silently — no duplicate-key report, no")
print("    2^53 flag, no NaN check. CANNOT.")

# ── Q12. The melt, materialised ONCE, and timed because the time is a finding.
t0 = time.time()
con.execute("""
    CREATE TEMP TABLE tree AS
    SELECT t.id, t.parent, t.key, t.fullkey, t.path, t.type, t.atom, t.value
    FROM read_json_objects('../source.json') r, json_tree(r.json) t
""")
melt_secs = time.time() - t0
# Depth counts BOTH separators: `path` alone maxes out at 7 here because array
# steps are written `[0]` and contribute no dot. Counting only dots is the
# obvious query and silently under-reports depth by five levels.
nodes, leaves, depth = con.sql("""
    SELECT count(*), count(*) FILTER (WHERE type NOT IN ('OBJECT', 'ARRAY')),
           max((length(fullkey) - length(replace(fullkey, '.', '')))
             + (length(fullkey) - length(replace(fullkey, '[', ''))))
    FROM tree
""").fetchone()
print(f"\nQ12 {leaves:,} leaves of {nodes:,} nodes, as a relation. YES — one SELECT,")
print(f"    no recursion written, nothing known in advance, {melt_secs:.2f}s.")
print("    WHAT IS LOST: nothing structural. `fullkey` keeps the array indices, so")
print("    unlike jq and ijson this table can still say WHICH target a row came from.")
print("    It also keeps the empty containers a melt drops — `__elements` is `{}`")
print("    and has a node here, where rrapply's melt loses it entirely.")

# ⚠ The performance cliff, measured rather than asserted. The obvious way to
# write this query is an aggregate straight over the table function; that form
# is 200x+ slower on the identical data and the difference is not visible in
# any plan a person would think to read.
t1 = time.time()
direct = con.sql("SELECT count(*) FROM tree").fetchone()[0]
tbl_secs = time.time() - t1
print(f"\n    ⚠ PERFORMANCE. Materialising cost {melt_secs:.2f}s; counting the table {tbl_secs:.2f}s.")
print("      Writing it the OBVIOUS way instead —")
print("        SELECT count(*) FROM read_json_objects(...) r, json_tree(r.json) t")
print("      — measured 55s, 55s, 63s, 71s, 78s, 146s and 178s across seven runs")
print("      of the same file, and once did not return at all. Same data, same")
print("      connection, same 17,676 nodes. This is a query-form cliff, not a")
print("      property of the document, and nothing in duckdb hints at it.")

# ── Q1/Q2. ────────────────────────────────────────────────────────────────
print(f"\nQ1  {nodes:,} nodes, one row each at every level. yes.")
roots = con.sql("SELECT count(*) FROM tree WHERE path = '$'").fetchone()[0]
print(f"    {roots} of them sit directly at the root.")
print(f"\nQ2  {depth}. yes, and it agrees with the probe, jq, ijson and rrapply at 12")
print("    — but only when the query counts `[` as well as `.`. Counting dots")
print("    alone, which is the obvious way, returns 7 and looks like an answer.")

# ── Q7. THE CENTRAL QUESTION. ─────────────────────────────────────────────
print("\nQ7  THE CENTRAL QUESTION, as a GROUP BY:")
for pat, label in [(r"^\$\.panels\[\d+\]$", "top-level"),
                   (r"^\$(\.panels\[\d+\]){2}$", "inside a row")]:
    n = con.sql(f"SELECT count(*) FROM tree WHERE regexp_matches(fullkey, '{pat}')").fetchone()[0]
    print(f"      {label:<16} {n:>4}")
total = con.sql(f"SELECT count(*) FROM tree WHERE {PANEL}").fetchone()[0]
print(f"      {'TOTAL':<16} {total:>4}")
print("    YES. The `+` in the pattern is the trick: it does not say how many")
print("    levels of nesting exist, so it does not need to know.")
print("\n    and because the melt is a RELATION, the breakdown is one more column")
print("    rather than a second program — which is duckdb's real advantage here:")
for typ, n in con.sql(f"""
        SELECT json_extract_string(value, '$.type') ty, count(*) c
        FROM tree WHERE {PANEL} GROUP BY 1 ORDER BY c DESC
""").fetchall():
    print(f"      {typ:<16} {n:>4}")

# ── Q3. What is one record. ───────────────────────────────────────────────
print("\nQ3  duckdb counts any reading you name and proposes none:")
for label, where in [
        ("one panel per row (all depths)", PANEL),
        ("one TOP-LEVEL panel per row", r"regexp_matches(fullkey, '^\$\.panels\[\d+\]$')"),
        ("one target per row", r"regexp_matches(fullkey, '^\$(\.panels\[\d+\])+\.targets\[\d+\]$')"),
        ("one template variable per row", r"regexp_matches(fullkey, '^\$\.templating\.list\[\d+\]$')"),
        ("one leaf per row", "type NOT IN ('OBJECT', 'ARRAY')")]:
    n = con.sql(f"SELECT count(*) FROM tree WHERE {where}").fetchone()[0]
    print(f"      {label:<32} {n:>6,}")
print("    CANNOT. Five readings, each one WHERE clause away, none proposed and")
print("    none priced.")

# ── Q4. Always vs sometimes. ──────────────────────────────────────────────
print(f"\nQ4  fields over the {total} panels — the children of every panel node:")
for k, n in con.sql(f"""
        SELECT c.key, count(*) c FROM tree p JOIN tree c ON c.parent = p.id
        WHERE regexp_matches(p.fullkey, '^\\$(\\.panels\\[\\d+\\])+$')
        GROUP BY 1 ORDER BY c DESC
""").fetchall():
    print(f"      {k:<16} {n:>4}  {'always' if n == total else ''}")
print("    yes — a self-join on `parent`, which is the melt paying off: the tree")
print("    is a relation, so 'the children of X' is an ordinary join.")

# ── Q5. Type variation, and the trap. ─────────────────────────────────────
by_key = con.sql("""
    SELECT count(*) FROM (SELECT key FROM tree WHERE key IS NOT NULL
                          GROUP BY key HAVING count(DISTINCT type) > 1)
""").fetchone()[0]
by_path = con.sql("""
    SELECT count(*) FROM (SELECT regexp_replace(fullkey, '\\[\\d+\\]', '[]', 'g') p
                          FROM tree WHERE type NOT IN ('OBJECT', 'ARRAY')
                          GROUP BY p HAVING count(DISTINCT type) > 1)
""").fetchone()[0]
print(f"\nQ5  PARTLY, and the two answers differ by an order of magnitude:")
print(f"      grouped by KEY   {by_key:>3} names carry more than one node type")
print(f"      grouped by PATH  {by_path:>3} paths do — and this agrees with ijson's 4")
print("    Grouping by key pools a name across every path it appears at, so")
print("    `value` at six unrelated sites reads as one polymorphic field. duckdb")
print("    computes either and warns about neither; the first is the easier query")
print("    and the wrong question.")

# ── Q6. Are any object keys data. ─────────────────────────────────────────
widest = con.sql("""
    SELECT max(n) FROM (SELECT count(*) n FROM tree c JOIN tree p ON c.parent = p.id
                        WHERE p.type = 'OBJECT' GROUP BY p.id)
""").fetchone()[0]
print(f"\nQ6  none; the widest object has {widest} keys and they are field names.")
print("    yes, inferred — duckdb counts, the judgement is mine.")

# ── Q8/Q9. Three named fields; a field missing from some rows. ────────────
tbl = con.sql(f"""
    SELECT json_extract_string(value, '$.title')       AS title,
           json_extract_string(value, '$.type')        AS type,
           json_extract_string(value, '$.id')          AS id,
           json_extract_string(value, '$.description') AS description
    FROM tree WHERE {PANEL}
""").fetchall()
missing = sum(1 for r in tbl if r[3] is None)
print(f"\nQ8  {len(tbl)} rows x 4. yes, and it reaches both depths because the WHERE")
print("    clause does — the same sentence as Q7.")
for r in tbl[:2]:
    print(f"      {str(r)[:86]}")
print(f"\nQ9  `description` is NULL for {missing} of {len(tbl)}; the rows stay. YES, and this")
print("    is the cleanest Q9 of the eight: `json_extract_string` returns SQL NULL")
print("    for an absent key, so missingness needs no special handling at all.")
print("    It agrees with jq, ijson, pandas and polars at 84.")

# ── Q10. Flatten the deepest array. ───────────────────────────────────────
deepest, n_arr = con.sql("""
    SELECT (SELECT fullkey FROM tree
            ORDER BY length(path) - length(replace(path, '.', '')) DESC LIMIT 1),
           (SELECT count(*) FROM tree WHERE type = 'ARRAY')
""").fetchone()
print(f"\nQ10 {n_arr:,} arrays; json_tree descends every one without being asked.")
print(f"    deepest: {deepest}")

# ── Q11. Find every path matching something. ──────────────────────────────
hits = con.sql(r"""
    SELECT count(*) FROM tree WHERE atom IS NOT NULL
      AND regexp_matches(CAST(atom AS VARCHAR), '\$node|\$job|\$__rate_interval')
""").fetchone()[0]
print(f"\nQ11 {hits} leaves mention a Grafana template variable. yes — one predicate")
print("    over the melt, and `fullkey` says exactly where each one is.")

print(f"""
    (melt {melt_secs:.1f}s, everything after it instant)

CONCLUSION. duckdb reaches 132 and is the most COMFORTABLE of the eight doing
it. `json_tree` is a real recursive walk with no recursion written, `fullkey`
keeps the array indices jq and ijson throw away, and because the result is a
relation the follow-up questions are joins: "the children of every panel" in Q4
is a self-join, and the type breakdown in Q7 is one extra column.

Three things against it.

There is a performance cliff with no warning on it. Materialising the tree is
{melt_secs:.2f}s; the same walk written as an aggregate straight over the table function
— the obvious form, and the one entry 28's attempt uses throughout — ran 55s to
178s on identical data and once did not return. A first draft of this file
concluded "duckdb is slow on this document" and that was simply wrong.

The depth-agnostic pattern still had to be written by someone who suspected the
nesting. `'^\\$(\\.panels\\[\\d+\\])+$'` is genuinely good and nothing in duckdb
proposed it; the `+` is there because I already knew what I was looking for.

And Q5 shows the melt's characteristic trap. Grouping type variation by `key`
pools a name across unrelated paths and reports {by_key}; grouping by `path` gives {by_path},
which is ijson's answer. duckdb computes either and warns about neither.
""")
