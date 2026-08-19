"""polars — agent trace, scrubbed, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.jsonl   4.8 MB NDJSON, 1,953 records, 40 top-level keys
  measured      2026-08-10
  run           cd corpus/12-agent-trace/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this what it claims to be              6   NO                  REFUSED
   1 what is in here                             5   NO                  yes (with infer_schema_length=None)
   2 how deep                                    4   NO                  yes
   3 what is one record                          5   NO                  PARTLY
   4 always present vs sometimes                 5   NO                  PARTLY
   5 does any field change type                 12   NO                  DANGEROUS
   6 are any object keys data                    4   YES                 CANNOT
   7 how many records                            2   NO                  PARTLY
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   8   -                   CANNOT
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       5   -                   PARTLY
  13 needed the shape in advance?                    NO for 1, 2, 4, 7
  14 survives the next file unchanged?               the schema half does
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~45, little ceremony
"""
import sys
from importlib.metadata import version

import polars as pl

print(f"python {sys.version.split()[0]}, polars {version('polars')}")

# ── Q0/Q1. THE DEFAULT CALL REFUSES THIS DOCUMENT, and the natural fix CRASHES.
# Measured, all three, because "cannot" is the most useful cell in the grid:
#
#   read_ndjson(path)                          ComputeError: expected null in
#                                              json value, got object
#   read_ndjson(path, ignore_errors=True)      PanicException from the Rust core:
#                                              "should not fail: SchemaMismatch"
#   read_ndjson(path, infer_schema_length=None)  OK, 1953 x 40
#
# The default infers a schema from a SAMPLE of the leading rows, and this
# document does not describe itself in its opening lines — a shape that first
# appears late is a schema mismatch rather than a new column. VERDICT.md records
# polars aborting on `04-gharchive` "by default with advice that does not work";
# **this is that failure on a second document, and here the advice does not
# merely fail, it panics the process.**
print("\n0. read_ndjson(...) default:            ComputeError, refuses the file")
print("   read_ndjson(..., ignore_errors=True): PanicException from the Rust")
print("                                          core — a crash, not an error")
print("   read_ndjson(..., infer_schema_length=None): works. Used below.")
print("   Sampling the leading rows is the cause: this document's rarer shapes")
print("   arrive late, and polars treats a late shape as a mismatch.")

df = pl.read_ndjson("../source.jsonl", infer_schema_length=None)
schema = str(df.schema)
print(f"\n1. read_ndjson: {df.height} rows x {df.width} cols")
print(f"   schema: {len(schema):,} chars for a 4,813,294-byte file "
      f"({100 * len(schema) / 4813294:.2f}% of it)")
print(f"   {sorted(df.columns)[:12]} …")

# ── 2. how deep ──────────────────────────────────────────────────────────────
def depth(dt):
    if isinstance(dt, pl.Struct):
        return 1 + max((depth(f.dtype) for f in dt.fields), default=0)
    if isinstance(dt, (pl.List, pl.Array)):
        return 1 + depth(dt.inner)
    return 0


print(f"\n2. deepest nesting: {1 + max(depth(d) for d in df.schema.values())}")
print("   (+1 for the record object itself, which became the row.) The true")
print("   depth is 10 and polars reports it, because it descends arrays as")
print("   well as objects — pandas stops at the first array and reports 2.")

# ── 4. always vs sometimes ───────────────────────────────────────────────────
print("\n4. PARTLY. null counts per column, biggest first:")
nulls = sorted(((c, df[c].null_count()) for c in df.columns), key=lambda kv: kv[1])
for c, n in nulls[:6]:
    print(f"     {c:26} {df.height - n:>5} of {df.height}")
print(f"     … and {len(nulls) - 6} more, emptiest {nulls[-1][0]} "
      f"at {df.height - nulls[-1][1]}")
print("   Only `type` is on every record. Correct — but polars unified all")
print("   1,953 records into one schema first, so an ABSENT key and a null key")
print("   are the same null and this is presence only by luck of the data.")

# ── 5. does any field change type — DANGEROUS, and this is the finding ───────
# MEASURED. Two paths in this document hold more than one type, and polars
# resolves BOTH by making the column a STRING and re-serialising the structure
# back into JSON text.
print(f"\n5. DANGEROUS. toolUseResult dtype: {df.schema['toolUseResult']}")
print(f"   message.content  dtype: "
      f"{[f.dtype for f in df.schema['message'].fields if f.name == 'content'][0]}")
v = df.filter(pl.col("toolUseResult").is_not_null())["toolUseResult"]
asjson = sum(1 for x in v if x.strip().startswith("{"))
print(f"   {asjson} of {len(v)} toolUseResult values are now JSON TEXT.")
print("   In the document: toolUseResult is object x452, string x6, and")
print("   message.content is array x1,363, string x20.")
print("   polars must unify to build a column, and it unified DOWNWARD — the")
print("   minority string type won, and every structured value was serialised")
print("   into it. **1,363 arrays of content blocks became strings because 20")
print("   of 1,383 were strings.** 1.4% of the values decided the type of the")
print("   other 98.6%.")
print("   Nothing warns. The schema reads String and looks deliberate.")

# ── The comparison this completes ────────────────────────────────────────────
print("\n   THREE TOOLS, THREE RESOLUTIONS of the same polymorphism:")
print("     tidyjson::json_schema  keeps the ARRAY form, the 20 strings vanish")
print("                            — 1.4% discarded, FINDINGS.md 2026-08-10")
print("     jsonlite::stream_in    keeps BOTH as a list-column, and says nothing")
print("     polars                 keeps the STRING form and stringifies 1,363")
print("                            arrays — 98.6% converted")
print("   polars' is the most destructive and the least visible. VERDICT.md")
print("   already records it 'silently rewriting data to fit an inferred type'")
print("   on 03-natural-earth; that was a nesting depth, this is the whole")
print("   structure of the document's most important field.")

# ── 6. are any object keys data ──────────────────────────────────────────────
print("\n6. CANNOT. `snapshot.trackedFileBackups` is keyed by FILE PATH — 50")
print("   distinct keys over 19 sites — and polars makes every one a STRUCT")
print("   FIELD, so a path becomes a column name. That is the keys-as-data")
print("   failure at its most literal.")

# ── 3, 7. what is one record, and how many ───────────────────────────────────
msg = df.filter(pl.col("message").is_not_null())
print("\n3. two records reachable, and the interesting one is NOT:")
print(f"     an event          {df.height:>5} rows x {df.width} cols   "
      f"{100 * sum(df[c].null_count() for c in df.columns) / (df.height * df.width):.0f}% empty")
print(f"     a message         {msg.height:>5} rows")
print("     a content block   UNREACHABLE — see Q10")
print(f"\n7. {df.height} events, {msg.height} messages. The 1,363 content blocks")
print("   and 458 tool uses cannot be counted through polars at all.")

# ── 8, 9. three named fields, one missing from some ──────────────────────────
t = df.select("type", "sessionId", "version")
print(f"\n8. three fields, one row per event:\n{t.head(3)}")
print(f"\n9. `version` null on {t['version'].null_count()} of {t.height} rows, "
      f"all kept.")

# ── 10. flatten the deepest array — CANNOT, and Q5 is why ────────────────────
try:
    msg.select(pl.col("message").struct.field("content")).explode("content")
    print("\n10. unexpected: explode succeeded")
except Exception as e:
    print(f"\n10. CANNOT: {type(e).__name__}: {str(e).splitlines()[0][:60]}")
print("   `explode` is not supported on a String column, and Q5 is why the")
print("   column is a String. **The type unification did not merely mislabel")
print("   the data, it put it out of reach**: every content block in the")
print("   document — 458 tool uses, 458 tool results, 237 texts, 210 thinkings")
print("   — is inside those strings, and getting at them means json.loads on")
print("   1,363 cells, at which point polars has contributed the read and")
print("   nothing else.")

# ── 11. every path whose value matches ───────────────────────────────────────
print("\n11. CANNOT. No whole-document path search, and on this file most of")
print("   the document is inside a string column anyway.")

# ── 12. flattest honest table ────────────────────────────────────────────────
print(f"\n12. flattest reachable: the {df.height}-row event table, {df.width} cols.")
print("   WHAT IS LOST: every content block, re-serialised to text at Q5; the")
print("   458 tool inputs the fifth operation is about, which live inside those")
print("   blocks; and the distinction between an absent key and a null one.")
print("   polars read the file and then made most of it unreachable.")
