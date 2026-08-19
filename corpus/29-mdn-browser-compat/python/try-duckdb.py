# duckdb — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          duckdb (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/python && uv run try-duckdb.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# ⚠ **THIS ATTEMPT IS ALSO A RE-TEST OF ENTRY 27's TIMING DEFECT.**
# `27-grafana-dashboard` measured an **880x cliff** between
# `CREATE TABLE AS SELECT … json_tree` (0.24 s) and `SELECT count(*)` over the
# same `json_tree` (211 s). Entry 28's attempt used the slow form throughout and
# its timings were flagged as worth re-reading. **Both forms are timed here on
# the same document**, because a tool's verdict should not depend on which of
# two equivalent-looking queries the author happened to write.

import json
import time
import duckdb

print(f"duckdb {duckdb.__version__}")

SRC = "../source.json"
con = duckdb.connect()


def timed(label, sql, fetch=True):
    t0 = time.perf_counter()
    r = con.execute(sql)
    out = r.fetchall() if fetch else None
    s = time.perf_counter() - t0
    print(f"  {label:<52} {s:8.2f} s")
    return out, s


print("\nQ0  duckdb parsed and said nothing about soundness.")
dup = con.execute("""SELECT json_extract('{"a":1,"a":2}', '$.a')""").fetchone()
print(f"    duplicate keys {{'a':1,'a':2}} -> {dup[0]}  (silent)")
big = con.execute("""SELECT json_extract('{"n":9007199254740993}', '$.n')""").fetchone()
print(f"    9007199254740993 -> {big[0]}")
print("    CANNOT — it reads, it does not report.")

# ── THE TIMING TEST. Two forms of the same json_tree. ────────────────────────
print("\n── the two forms of the same json_tree, entry 27's cliff re-tested ──────")
_, s_ctas = timed("CREATE TABLE t AS SELECT … json_tree(…)",
                  f"""CREATE OR REPLACE TABLE t AS
                      SELECT * FROM json_tree((SELECT content FROM read_text('{SRC}')))""",
                  fetch=False)
n_rows, s_count_tbl = timed("SELECT count(*) FROM t   (materialised)",
                            "SELECT count(*) FROM t")
_, s_count_inline = timed("SELECT count(*) FROM json_tree(…)   (inline)",
                          f"""SELECT count(*) FROM
                              json_tree((SELECT content FROM read_text('{SRC}')))""")
print(f"    materialised then counted : {s_ctas + s_count_tbl:8.2f} s total")
print(f"    counted inline            : {s_count_inline:8.2f} s")
ratio = s_count_inline / max(s_ctas + s_count_tbl, 1e-9)
print(f"    ratio: {ratio:.1f}x")

print(f"\nQ12 json_tree -> {n_rows[0][0]:,} rows. ONE CALL, no shape known first.")
cols = con.execute("DESCRIBE t").fetchall()
print(f"    columns: {', '.join(c[0] for c in cols)}")

# ── Q1/Q2. ───────────────────────────────────────────────────────────────────
# `fullkey` is THIS node's path; `path` is its PARENT's; an array element is the
# parent key with `[n]` appended. A first draft filtered on `path` and printed
# 1,163 "top-level keys" — every node whose PARENT was one level down. The
# root's id is 0, so `parent = 0` is the honest filter.
top = con.execute("""SELECT key, type FROM t WHERE parent = 0 ORDER BY key""").fetchall()
print(f"\nQ1  {len(top)} top-level keys: {', '.join(k for k, _ in top)}")
print("    and the FULL field list is in the tree above, which is Q12 doing Q1's job.")

d = con.execute("""SELECT max(length(fullkey)
                     - length(replace(replace(fullkey, '.', ''), '[', ''))) FROM t""").fetchone()
print(f"\nQ2  {d[0]}. YES — from `fullkey`, counting BOTH separators.")
print("    Counting only '.' gives 11, because an array step is written `chrome[0]`")
print("    and carries no dot. The document is 12 deep and every other tool here")
print("    says so; a dot-count is a wrong answer that looks like a right one.")

# ── Q7/Q5. ───────────────────────────────────────────────────────────────────
by_type = con.execute("""SELECT type, count(*) FROM t GROUP BY type ORDER BY 2 DESC""").fetchall()
print("\nQ5  node types over the whole document:")
for t_, n in by_type:
    print(f"      {t_:<10} {n:>10,}")
va = con.execute("""SELECT type, count(*) FROM t WHERE key = 'version_added'
                    GROUP BY type ORDER BY 2 DESC""").fetchall()
print("    version_added by type — the tri-typed field:")
for t_, n in va:
    print(f"      {t_:<10} {n:>10,}")
print("    YES. `type` is a column, so this is a GROUP BY rather than an inference.")

leaves = con.execute("""SELECT count(*) FROM t WHERE type NOT IN ('OBJECT','ARRAY')""").fetchone()
print(f"\nQ7  {leaves[0]:,} leaves.")

# ── Q3. ──────────────────────────────────────────────────────────────────────
print("\nQ3  duckdb names no candidates and prices none. Counts per depth:")
for lvl in range(1, 5):
    n = con.execute(f"""SELECT count(DISTINCT path) FROM t
                        WHERE length(path) - length(replace(path,'.','')) = {lvl}""").fetchone()
    print(f"      depth {lvl}   {n[0]:>10,} distinct paths")
print("    CANNOT.")

# ── Q6. ──────────────────────────────────────────────────────────────────────
print("\nQ6  duckdb can count keys per container but decides nothing:")
kc = con.execute("""SELECT count(*) FROM t WHERE path LIKE '$.api.%'
                    AND path NOT LIKE '$.api.%.%'""").fetchone()
print(f"      $.api has {kc[0]:,} direct children")
print("    CANNOT — the threshold is mine.")

# ── Q11. THE URL QUESTION, AND THE FOLD. ─────────────────────────────────────
# `LIKE '"http%'` was the first draft and it over-counts: it matches `httpEquiv`
# and every other string merely beginning `http`. The other five tools use
# `^https?://`, so this uses it too or the numbers are not comparable.
URL = "regexp_matches(json_extract_string(value, '$'), '^https?://')"
t0 = time.perf_counter()
u = con.execute(f"""SELECT count(*) FROM t WHERE type = 'VARCHAR' AND {URL}""").fetchone()
print(f"\nQ11 {u[0]:,} URL leaves in {time.perf_counter()-t0:.2f} s. YES.")
loose = con.execute("""SELECT count(*) FROM t
                       WHERE type = 'VARCHAR' AND value LIKE '"http%'""").fetchone()
print(f"    (the loose `LIKE '\"http%'` gives {loose[0]:,} — {loose[0]-u[0]:,} more,")
print("     strings that begin `http` without being URLs. Worth stating because")
print("     it is the shape of expression a person writes first.)")
up = con.execute(f"""SELECT count(DISTINCT fullkey) FROM t
                     WHERE type = 'VARCHAR' AND {URL}""").fetchone()
print(f"    distinct literal URL paths: {up[0]:,} — one per value, no folding")
uf = con.execute(f"""SELECT count(DISTINCT regexp_replace(fullkey,
                       '\\.[^.\\[]+\\.__compat', '.<key>.__compat', 'g')) FROM t
                     WHERE type = 'VARCHAR' AND {URL}""").fetchone()
print(f"    after ONE hand-written regexp_replace: {uf[0]:,}")
print("    duckdb CAN fold. It cannot decide what to fold, and the regex is mine.")

# ── Q8/Q9/Q10. ───────────────────────────────────────────────────────────────
print("\nQ8  three named fields, by json_extract:")
row = con.execute(f"""SELECT
    json_extract_string(j, '$.api.ANGLE_instanced_arrays.__compat.mdn_url')  AS mdn_url,
    json_extract_string(j, '$.api.ANGLE_instanced_arrays.__compat.source_file') AS src,
    json_extract_string(j, '$.api.ANGLE_instanced_arrays.__compat.nope')     AS missing
    FROM (SELECT content AS j FROM read_text('{SRC}'))""").fetchall()
print(f"      mdn_url = {row[0][0]}")
print(f"      src     = {row[0][1]}")
print(f"\nQ9  the missing one -> {row[0][2]!r}. NULL, the row survives. YES.")

# TWO WRONG ANSWERS FIRST, both from picking the wrong column.
#   `path ~ '\[[0-9]+\]'`  -> 0, because `~` needed doubling in a Python string
#   regexp_matches(path,…) -> 47,459, because `path` is the PARENT's path, so a
#                             scalar that IS an array element does not carry the
#                             index — only its `fullkey` does.
by_path = con.execute("""SELECT count(*) FROM t
                         WHERE regexp_matches(path, '\\[[0-9]+\\]')
                           AND type NOT IN ('OBJECT', 'ARRAY')""").fetchone()
arr = con.execute("""SELECT count(*) FROM t
                     WHERE regexp_matches(fullkey, '\\[[0-9]+\\]')
                       AND type NOT IN ('OBJECT', 'ARRAY')""").fetchone()
print(f"\nQ10 leaves under an array index, via `path`   : {by_path[0]:,}  (WRONG)")
print(f"    the same, via `fullkey`                   : {arr[0]:,}")
print("    ** YES, AND ONLY TWO OF THE FOURTEEN CAN. ** An array step is written")
print("    `chrome[0]` and a key step `.chrome`, so the distinction survives")
print("    into the path string. jq gets the same 70,420 by a different route —")
print("    a jq path is an ARRAY OF STEPS where an index is a number and a key")
print("    is a string, so the types carry it. Every melted-path tool")
print("    here loses it: 1,076 object keys in this document are all digits")
print("    (browser release versions), and once a key and an index are both")
print("    plain strings in a column, nothing tells them apart.")
print("    70,420 is confirmed by two independent walks, in R and in Python.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

THE 880x CLIFF DID NOT REPRODUCE, AND THE PREDICTION THAT IT WOULD WAS WRONG.
Entry 27 measured CREATE TABLE AS at 0.24 s against SELECT count(*) over the
same json_tree at 211 s. Here the materialised route takes 0.47 s and the
INLINE count takes 0.11 s — the inline form is four times FASTER, a ratio of
0.2x where 880x was expected. On duckdb 1.5.5, on this document, there is no
cliff to avoid. Entry 27's measurement stands as recorded for its own document
and version; what does not stand is treating it as a property of duckdb.

json_tree IS THE BEST SINGLE ANSWER IN THE PYTHON HALF, and it is the same
shape of answer rrapply gives in R: one call, no shape known first, 865,598
rows. Its node-type counts agree with tidyjson EXACTLY — OBJECT 367,647,
VARCHAR 353,345, BOOLEAN 117,328, ARRAY 27,278 — which is two independent
implementations landing on the same four numbers.

AND IT IS ONE OF ONLY TWO TOOLS THAT CAN ANSWER QUESTION 10. `fullkey`
writes an array step as `chrome[0]` and a key step as `.chrome`, so the
distinction between an index and a key survives into the path. Every
melted-path tool loses it, and this document proves the loss matters: 1,076 of
its object keys are all digits, because browser releases are keyed `1`, `10`,
`58`. rrapply over-counts by 5,371 and tidyr under-counts by 65,046; duckdb
gets 70,420, which two independent walks and jq confirm. jq reaches the same
number a different way — its paths are arrays of steps, and an index is a
NUMBER where a key is a STRING, so the distinction is in the type rather than
in the spelling. Two tools, two mechanisms, one answer.

WHAT IT STILL CANNOT DO is question 3 and question 6, for the 29th entry
running. It counts 8,893 direct children under `$.api` and says nothing about
whether that means the keys are data. The fold is available — one
regexp_replace takes 35,392 literal URL paths to 7,243 — and it is available
to a person who already knows what to fold. jq's identical fold gives the same
7,243, which is worth stating: two tools, two languages, one hand-written rule,
the same answer. The rule is the part no tool supplies.

A NOTE ON THE THREE QUERIES THIS FILE GOT WRONG BEFORE IT GOT THEM RIGHT.
`path` versus `fullkey` produced 47,459 instead of 70,420; a dot-count gave
depth 11 instead of 12; and `LIKE '"http%'` gave 35,804 URLs instead of 35,392
by matching `httpEquiv`. All three are the kind of error that returns a
plausible number rather than an exception, and all three were caught only by
disagreeing with another tool.
""")
