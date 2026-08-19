"""polars — Natural Earth country geometry

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   3.9 MB, 241 features, GeoJSON
  measured      2026-08-09
  run           cd corpus/03-natural-earth/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is it sound                                 4   no                  see below
   1 what is in here                             3   no                  PARTLY
   5 does any field change type                  4   no                  WRONG
   7 how many records                            2   YES                 YES

WHY THIS FILE. polars could not open 05-fhir-bundle at all, defeated by a field
that is an object on some records and a list on others. Here the conflict is
subtler: `coordinates` is a list either way and only the DEPTH differs. Does a
type system that refused the coarse conflict notice the fine one?
"""
import json, sys
from importlib.metadata import version
import polars as pl

print(f"python {sys.version.split()[0]}, polars {version('polars')}")

print("\n0. polars on the GeoJSON:")
df = None
for label, kw in [("default", {}), ("infer_schema_length=None", {"infer_schema_length": None})]:
    try:
        d = pl.read_json("../source.json", **kw)
        if df is None:
            df = d
        print(f"     {label:<26} OK, {d.height} row(s)")
    except Exception as e:
        print(f"     {label:<26} FAILED — {type(e).__name__}: {str(e).splitlines()[0][:40]}")

doc = json.load(open("../source.json"))
print(f"\n7. features inside: {len(doc['features'])}")

if df is not None:
    s = str(df.schema)
    print(f"\n1. schema: {len(s):,} characters "
          f"({len(s)/len(open('../source.json','rb').read()):.3%} of the file)")
    coord = [t for t in s.split(",") if "coordinates" in t]
    print(f"   the coordinates entry: {coord[0].strip()[:70] if coord else 'n/a'}")
    depth = coord[0].count("List(") if coord else 0
    print(f"\n5. polars gave `coordinates` {depth} levels of List, and the 122")
    print("   Polygons only have 3. It did not refuse and it did not report:")
    print("   it PROMOTED every Polygon to the deeper shape so one type covers")
    print("   both. 122 features were silently rewrapped.")
    # `.unnest("features").unnest("geometry")` raises DuplicateError here:
    # GeoJSON puts `type` on the Feature AND on the geometry, and flattening
    # collides them. Reaching the field directly instead.
    got = df.explode("features").select(
        pl.col("features").struct.field("geometry")
          .struct.field("coordinates").alias("c"))
    import collections
    def dep(x): return 1 + dep(x[0]) if isinstance(x, (list, tuple)) else 0
    c = collections.Counter(dep(v) for v in got["c"].to_list())
    print(f"   nesting depths AFTER the read: {dict(c)}")
    print("   against {3: 122, 4: 119} in the file. The distinction the document")
    print("   was chosen for does not survive being loaded.")
    print("   DuckDB typed the same field `JSON[][][]` — three levels and then")
    print("   an admission, which is the more honest of the two.")
