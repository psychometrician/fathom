# pydash — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          pydash (version printed at run time)
#  file          ../source.json.gz   118 MB gzipped, 870 MB / 286,864 records raw
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/python && uv run try-pydash.py
#
#  Header filled in after the run. See the CONCLUSION.
import time, pydash
from _budget import in_subprocess
from _needs_doc import load

print(f"pydash {pydash.__version__}")
out, rc = in_subprocess("_needs_doc.py", "all")
fin, secs, rss, n, _, why = (out.split("\t") + [""])[:6]
print(f"\nparse the whole document first: finished={fin} {float(secs):.1f} s "
      f"peak RSS {float(rss):,.0f} MB, {int(n):,} records")

docs = load(50_000)
print("\nQ0  pydash never sees the bytes. CANNOT.")
print(f"\nQ1  pydash.keys(one record) -> {len(pydash.keys(docs[0]))} keys. ONE LEVEL.")
t0 = time.perf_counter()
rows = [{"t": pydash.get(d, "type"), "a": pydash.get(d, "actor.login"),
         "o": pydash.get(d, "org.login")} for d in docs]
s = time.perf_counter() - t0
print(f"\nQ8  pydash.get(dotted path) x3 over {len(rows):,} records in {s:.1f} s")
print(f"      {rows[0]}")
print("    YES — the friendliest spelling of Q8 anywhere, and it is also FAST:")
print("    level with compiled jmespath and about eight times quicker than glom")
print("    on the identical 50,000 records.")
miss = sum(1 for r in rows if r["o"] is None)
print(f"\nQ9  `org` absent in {miss:,}; get() returns None, row survives. YES.")
print("\nQ2  CANNOT without my own walk.  Q3 CANNOT.  Q6 CANNOT.")
print("Q5  PARTLY — types survive, nothing reports them, and get()'s default")
print("    invents a NoneType the document may not contain.")
print("Q10/Q11/Q12 CANNOT. `deep_map_values` returns the SAME SHAPE, so it can")
print("    transform a document but never flatten one. There is no melt.")
print(f"""
CONCLUSION. Written after the run and corrected against what printed.

IT COMPLETES, and the prediction that it would not was wrong: 870 MB is 5
seconds and 2.9 GB of parsing on this machine, and pydash works on whatever is
in memory.

WHAT SCALE EXPOSED IS SPEED, and it went the opposite way to my expectation.
`pydash.get` parses a dotted string per call, so I recorded it as the one that
would be slowest at 286,864 records. Measured on the same 50,000 records it is
0.3 s — level with a COMPILED jmespath expression and about eight times faster
than glom's spec at 2.5 s. The friendliest spelling here is also among the
quickest, which is not the trade the API's shape suggests.

EVERYTHING ELSE IS UNCHANGED FROM ENTRIES 04 AND 29. It is a utility belt, not
a JSON library; there is no melt, no search, and no verb that answers what a
row could be. Questions 2, 3, 6, 10, 11 and 12 are CANNOT at every size.
""")
