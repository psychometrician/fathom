"""DuckDB — agent trace, scrubbed, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          duckdb (version printed at run time)
  file          ../source.jsonl   4.8 MB NDJSON, 1,953 records, 40 top-level keys
  measured      2026-08-10
  run           cd corpus/12-agent-trace/python && uv run try-duckdb.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  yes
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          5   YES                 PARTLY
   4 always present vs sometimes                 5   NO                  yes
   5 does any field change type                  7   NO                  yes
   6 are any object keys data                    4   YES                 CANNOT
   7 how many records                            3   YES                 YES
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   5   YES                 yes
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   YES                 PARTLY
  13 needed the shape in advance?                    NO for 1, 4, 5, 7
  14 survives the next file unchanged?               DESCRIBE does
  15 readable a week later?                          yes, it is SQL
  16 lines, and how much is ceremony?                ~45, some SQL ceremony
"""
import sys
from importlib.metadata import version

import duckdb

print(f"python {sys.version.split()[0]}, duckdb {version('duckdb')}")
con = duckdb.connect()
SRC = ("read_json_auto('../source.jsonl', format='newline_delimited', "
       "maximum_object_size=100000000, sample_size=-1)")

# `sample_size=-1` is not tidiness: the DEFAULT samples the leading rows and this
# document's rarer shapes arrive late. polars refuses the file outright for the
# same reason (see try-polars.py). DuckDB gives you a flag that works.
print("\n0. `sample_size=-1` is required. The default samples leading rows and")
print("   this document does not describe itself in its opening lines. polars")
print("   REFUSES the same file for the same reason; DuckDB has a flag.")

# ── 1. what is in here ───────────────────────────────────────────────────────
d = con.sql(f"DESCRIBE SELECT * FROM {SRC}").df()
total = sum(len(str(t)) for t in d["column_type"])
widest = max((len(str(t)), c) for c, t in zip(d["column_name"], d["column_type"]))
print(f"\n1. DESCRIBE: {len(d)} rows. All type cells together {total:,} chars "
      f"({100 * total / 4813294:.1f}% of the file)")
print(f"   widest type cell: {widest[0]:,} chars, in `{widest[1]}`")
print(f"   {list(d['column_name'])[:10]} …")
print("   Eighteen tidy rows on npm hid a 378,036-char type; here 40 tidy rows")
print("   hide the whole document's shape in a handful of cells.")

# ── 2. how deep ──────────────────────────────────────────────────────────────
print("\n2. CANNOT. The depth is inside those type strings and DuckDB has no")
print("   verb for it. The true depth is 10.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. non-null count per column, nothing named in advance:")
cols = list(d["column_name"])
q = ", ".join(f'count("{c}") AS "{c}"' for c in cols)
row = con.sql(f"SELECT {q} FROM {SRC}").df().iloc[0].sort_values(ascending=False)
for k, v in list(row.items())[:6]:
    print(f"     {k:26} {int(v):>5} of 1953")
print(f"     … and {len(row) - 6} more, emptiest {row.index[-1]} at {int(row.iloc[-1])}")
print("   Only `type` is on every record. DuckDB reads NDJSON natively, so this")
print("   is one query and no field was named by me — the column list came")
print("   from DESCRIBE.")

# ── 5. does any field change type ────────────────────────────────────────────
t = con.sql(f"SELECT typeof(toolUseResult) a, typeof(message.content) b "
            f"FROM {SRC} LIMIT 1").fetchone()
print(f"\n5. toolUseResult typed {str(t[0])[:40]}, message.content {str(t[1])[:40]}")
print("   In the document: toolUseResult is object x452 / string x6, and")
print("   message.content is array x1,363 / string x20. DuckDB unifies to build")
print("   a column and lands on JSON/VARCHAR — but UNLIKE polars it keeps the")
print("   value queryable: `->` and `json_extract` still work on a JSON column,")
print("   so the structure is reachable rather than re-serialised out of reach.")
print("   Same unification, opposite consequence. That difference is the whole")
print("   distance between a schema and a JSON type.")

# ── 6. are any object keys data ──────────────────────────────────────────────
print("\n6. CANNOT. `snapshot.trackedFileBackups` is keyed by FILE PATH, 50")
print("   distinct keys over 19 sites. DuckDB types keyed objects as STRUCTs,")
print("   so each path becomes a field name needing double quotes — the same")
print("   silent promotion of a value to a field name as everywhere else.")

# ── 3, 7. what is one record, and how many ───────────────────────────────────
n = con.sql(f"SELECT count(*) FROM {SRC}").fetchone()[0]
nm = con.sql(f"SELECT count(*) FROM {SRC} WHERE message IS NOT NULL").fetchone()[0]
nb = con.sql(f"SELECT count(*) FROM (SELECT unnest("
             f"from_json(message.content, '[\"json\"]')) b FROM {SRC} "
             f"WHERE message IS NOT NULL AND message.content LIKE '[%')").fetchone()[0]
print(f"\n3. three defensible records:")
print(f"     an event          {n:>5} rows x {len(d)} cols")
print(f"     a message         {nm:>5} rows")
print(f"     a content block   {nb:>5} rows  (via from_json, see Q10)")
print("   DuckDB proposes the first by reading NDJSON and prices none.")
print(f"\n7. {n} events, {nm} messages, {nb} content blocks.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
q8 = con.sql(f'SELECT "type", sessionId, version FROM {SRC} LIMIT 3').df()
print(f"\n8. three fields, one row per event:\n{q8.to_string(index=False)}")
miss = con.sql(f"SELECT count(*) FROM {SRC} WHERE version IS NULL").fetchone()[0]
print(f"\n9. `version` NULL on {miss} of {n} rows, all kept.")

# ── 10. flatten the deepest array ────────────────────────────────────────────
tu = con.sql(f"""
  SELECT count(*) FROM (
    SELECT unnest(from_json(message.content, '["json"]')) AS b FROM {SRC}
    WHERE message IS NOT NULL AND message.content LIKE '[%')
  WHERE b->>'$.type' = 'tool_use'""").fetchone()[0]
print(f"\n10. tool_use blocks: {tu} rows")
print("   `from_json(..., '[\"json\"]')` re-parses the stringified content and")
print("   `->>` reaches inside. THREE hand-written steps to undo a type")
print("   unification the tool performed on its own — but it IS undoable here,")
print("   which is more than polars offers.")

# ── 11. every path whose value matches ───────────────────────────────────────
print("\n11. CANNOT. No path search over an arbitrary document; every column is")
print("   named. `json_extract` needs a path, which is the thing being asked for.")

# ── 12. flattest honest table ────────────────────────────────────────────────
inp = con.sql(f"""
  SELECT b->>'$.name' AS name, json_keys(b->'$.input') AS fields FROM (
    SELECT unnest(from_json(message.content, '["json"]')) AS b FROM {SRC}
    WHERE message IS NOT NULL AND message.content LIKE '[%')
  WHERE b->>'$.type' = 'tool_use'""").df()
allf = sorted({f for fs in inp["fields"] for f in fs})
print(f"\n12. {len(inp)} tool uses, {len(allf)} distinct input fields: {allf}")
common = set.intersection(*[set(fs) for fs in inp["fields"]])
print(f"   fields present in EVERY input: {common or 'NONE'}")
print("   THE FINDING THIS FILE EXISTS FOR, reached in SQL: 15 input fields")
print("   plus `name` is a 16-column table of which NONE is universal. The")
print("   field that explains it is")
print("   `name`, a SIBLING of `input`. DuckDB can GROUP BY it and will never")
print("   suggest doing so.")
print("   WHAT IS LOST: nothing irrecoverably — which is the DuckDB result on")
print("   this document, and it is the opposite of the polars one.")
