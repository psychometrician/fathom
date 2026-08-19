# jmespath — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jmespath (see uv.lock)
#  file          ../source.json.gz   118 MB gzipped, 870 MB / 286,864 records raw
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/python && uv run try-jmespath.py
#
#  Header filled in after the run. See the CONCLUSION.
import time, jmespath
from _budget import in_subprocess
from _needs_doc import load

print("jmespath (version in uv.lock)")
out, rc = in_subprocess("_needs_doc.py", "all")
fin, secs, rss, n, _, why = (out.split("\t") + [""])[:6]
print(f"\nparse the whole document first: finished={fin} {float(secs):.1f} s "
      f"peak RSS {float(rss):,.0f} MB, {int(n):,} records")

docs = load(50_000)
print("\nQ0  jmespath never sees the bytes. CANNOT.")
top = jmespath.search("keys(@)", docs[0])
print(f"\nQ1  keys(@) on one record -> {', '.join(top)}")
print("    ONE LEVEL, and there is no descent operator to go further.")
print("\nQ2  CANNOT. No `..`, so depth is not expressible.")
print("Q3  CANNOT.  Q6  CANNOT.")

expr = jmespath.compile("{t: type, a: actor.login, o: org.login}")
t0 = time.perf_counter()
rows = [expr.search(d) for d in docs]
s = time.perf_counter() - t0
print(f"\nQ8  a compiled multiselect over {len(rows):,} records in {s:.1f} s")
print(f"      {rows[0]}")
print("    YES — and compiling once matters at this scale, which is the only")
print("    thing 286,864 records changed about this tool.")
miss = sum(1 for r in rows if r["o"] is None)
print(f"\nQ9  `org` absent in {miss:,}; returns None and the row survives. YES —")
print("    and absent is indistinguishable from null, unlike glom.")
print("\nQ4  yes, from the table. Q5 PARTLY — no `type` function to group by.")
print("Q7  286,864 records, from the parse above.")
print("Q10 PARTLY — one level per star, written out by hand. No `**`.")
print("Q11 CANNOT. No descent operator. Q12 CANNOT, same reason.")
print(f"""
CONCLUSION. Written after the run and corrected against what printed.

IT COMPLETES. 870 MB is 5 seconds and 2.9 GB of parsing, and jmespath is then
fast — a compiled expression over 50,000 records runs in well under a second.
The prediction that it would fail was wrong.

THE MISSING DESCENT OPERATOR IS STILL THE WHOLE STORY, unchanged from entry 29.
jq has `..`; jmespath does not, and that single absence is why questions 2, 11
and 12 are CANNOT here as they were at 19.9 MB. Scale did not add a limitation
or remove one.

ONE THING SCALE DID CHANGE: `jmespath.compile` stops being a nicety. Re-parsing
the expression per record is the difference between seconds and minutes at
286,864 records, and nothing in the API makes that obvious.
""")
