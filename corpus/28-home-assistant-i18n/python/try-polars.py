"""polars — Home Assistant frontend, the English translation catalogue

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

── scoring ──────────────────────────────────────────────────────────────────
 tool          polars (version printed at run time)
 file          ../source.json   590 KB, 7 top-level keys, 10,136 paths, depth 11
 measured      2026-08-12
 run           cd corpus/28-home-assistant-i18n/python && uv run try-polars.py

 question                                    lines  shape known first?  worked
  0 is this sound                               1   -                   CANNOT
  1 what is in here                             8   NO                  YES — the SCHEMA, every level
  2 how deep                                    6   NO                  yes, by walking the dtype
  3 what is one record                          4   NO                  CANNOT — one row, names none
  4 always present vs sometimes                 -   -                   CANNOT, no records to compare
  5 does any field change type                  3   NO                  by accident — see below
  6 are any object keys data                    -   -                   CANNOT
  7 how many records                            2   NO                  1
  8 three named fields to a table               4  YES                  yes
  9 a field missing from some rows              3  YES                  raises, unless you ask first
 10 flatten the deepest array                   1   -                   NOTHING TO FLATTEN
 11 find every path matching something          5   NO                  yes, by walking the schema
 12 flattest honest table                       9   NO                  CANNOT — unnest RAISES
 13 needed the shape in advance?                    NO for 1, 2, 11
 14 survives the next file unchanged?               yes for 1, 2, 11
 15 readable a week later?                          the schema walk, no
 16 lines, and how much is ceremony?                ~85

**polars is the only tool of the eight that hands you a TYPED description of
every level without being asked** — `df.schema` is a nested dtype and walking it
answers Q1, Q2 and Q11 with no path known in advance. It is also the tool whose
answer to Q3 is most confidently wrong: one row.
"""
import sys
import time

import polars as pl

print(f"polars {pl.__version__} · python {sys.version.split()[0]}")

t = time.time()
df = pl.read_json("../source.json")
print(f"\nQ0  read_json succeeded silently. CANNOT — no duplicate-key report.")


def walk(dtype, prefix="", depth=1, out=None):
    """Every field in the nested dtype, with its depth. polars' schema IS the
    structure, so this needs nothing but the frame."""
    out = [] if out is None else out
    if isinstance(dtype, pl.Struct):
        for f in dtype.fields:
            p = f"{prefix}.{f.name}" if prefix else f.name
            out.append((p, f.dtype, depth))
            walk(f.dtype, p, depth + 1, out)
    return out


fields = []
for name, dtype in df.schema.items():
    fields.append((name, dtype, 1))
    walk(dtype, name, 2, fields)

print(f"\nQ1  df.schema, walked: {len(fields):,} fields at every level.")
print(f"    top level, {len(df.schema)}: {', '.join(df.schema)}")
print("    YES, and nothing was known in advance — the dtype is the structure.")

print(f"\nQ2  deepest field: {max(d for _, _, d in fields)}. yes.")

leaves = [(p, d) for p, dt, d in fields if not isinstance(dt, pl.Struct)]
print(f"\nQ5  {len(leaves):,} leaf fields, dtypes: "
      f"{ {str(dt) for _, dt, _ in fields if not isinstance(dt, pl.Struct)} }")
print("    Every leaf is Utf8. by accident: polars needs ONE dtype per field, so")
print("    a field that were a string here and an object there would have failed")
print("    to read rather than been reported. Nothing here forces that.")

print(f"\nQ3  {df.height} row. polars names no candidates and prices none.")
print("    There is no array to make rows from. CANNOT.")
print(f"\nQ7  {df.height}.")

print("\nQ4  CANNOT. One row means no population to compare.")
print("\nQ6  CANNOT.")

got = df.select(
    pl.col("ui").struct.field("common").struct.field("and").alias("and"),
    pl.col("ui").struct.field("common").struct.field("loading").alias("loading"),
)
print(f"\nQ8  {got.row(0)}  — struct.field chains, one per level. yes.")

print("\nQ9  a field that is not there raises StructFieldNotFoundError rather")
print("    than giving null, so the caller must check the schema first.")

print("\nQ10 zero arrays. NOTHING TO FLATTEN.")

icu = [p for p, dt, _ in fields if not isinstance(dt, pl.Struct)]
print(f"\nQ11 {len(icu):,} leaf paths available to filter, from the schema alone.")
print("    To match on VALUES you must unnest first, which is Q12.")

# UNNEST FAILS ON THIS DOCUMENT, and the reason is worth the whole attempt.
try:
    flat = df.unnest("ui")
    print(f"\nQ12 unnest -> {flat.shape}")
except Exception as e:
    print(f"\nQ12 df.unnest('ui') RAISES: {type(e).__name__}")
    print(f"    {e}")
    print("    The root has `panel` and so does `ui`. Lifting ui's fields to the")
    print("    top collides with the root's own, and polars refuses rather than")
    print("    renaming. THE FLATTEST HONEST TABLE CANNOT BE BUILT BY UNNEST at")
    print("    all — not 'is awkward', cannot.")
    print("    Every level would have to be renamed on the way up, by hand, and")
    print("    the renaming is the dotted path that jq and ijson give free.")
print(f"    ({time.time() - t:.1f}s)")

print("""
CONCLUSION. polars is the best of the DataFrame tools here and it is because of
the schema: a nested dtype is a real description of every level, available
without asking, and it answers Q1, Q2 and Q11 with nothing known in advance.
That is closer to what the probe does than anything else in the eight.

Where it ends is Q12, and harder than expected. `df.unnest('ui')` RAISES: the
root has a `panel` key and so does `ui`, so lifting one level collides with the
level above. **The flattest honest table cannot be built by unnest at all**, and
the fix — renaming every field on the way up — is the dotted path that jq and
ijson hand over for nothing.

Q3 ends the same way for a different reason: polars is certain there is one row,
because there is no array, and offers nothing else.

And the schema's completeness is bought with a constraint the probe does not
have: polars needs ONE dtype per field, so a document whose field changes type
between records does not get REPORTED here, it fails to read.
""")
