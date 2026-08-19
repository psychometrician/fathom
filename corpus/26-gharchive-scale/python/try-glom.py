# glom — one hour of public GitHub events, at 17x the size of entry 04
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          glom (version printed at run time)
#  file          ../source.json.gz   118 MB gzipped, 870 MB / 286,864 records raw
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/python && uv run try-glom.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# glom operates on an ALREADY-PARSED value, so the whole document must be in
# memory before it can be asked anything. That cost is measured in its own
# process by `_needs_doc.py` and reported here.
import time, glom
from glom import glom as G, Coalesce
from _budget import in_subprocess
from _needs_doc import load

print(f"glom {glom.__version__}")
out, rc = in_subprocess("_needs_doc.py", "all")
fin, secs, rss, n, _, why = (out.split("\t") + [""])[:6]
print(f"\nparse the whole document first: finished={fin} {float(secs):.1f} s "
      f"peak RSS {float(rss):,.0f} MB, {int(n):,} records")

print("\nQ0  glom never sees the bytes. CANNOT.")
print("Q1  CANNOT beyond one level — no listing verb.")
print("Q2  CANNOT. A spec is written to a depth you already know.")
print("Q3  CANNOT. Names no candidates, prices none.")
print("Q6  CANNOT.")

docs = load(50_000)          # enough to answer 4/5/8/9 honestly, in seconds
t0 = time.perf_counter()
rows = [G(d, {"type": "type", "actor": "actor.login",
              "repo": Coalesce("repo.name", default=None),
              "org": Coalesce("org.login", default=None)}) for d in docs]
s = time.perf_counter() - t0
print(f"\nQ8  one spec over {len(rows):,} records in {s:.1f} s "
      f"({1e6*s/len(rows):.1f} us each)")
print(f"      {rows[0]}")
print("    YES, and it is the best-SHAPED answer to Q8 in the Python half — the")
print("    spec IS the output shape. It is also the SLOWEST of the three path")
print("    libraries here by about 8x: pydash and compiled jmespath both do the")
print("    identical work over these 50,000 records in 0.3 s.")
miss = sum(1 for r in rows if r["org"] is None)
print(f"\nQ9  `org` absent in {miss:,} of {len(rows):,}; Coalesce keeps the row. YES.")
print("    And glom RAISES on an absent path by default, alone among the")
print("    fourteen. On a file this size that is worth more, not less: a typo")
print("    in a spec run over 286,864 records fails loudly on the first one.")
print("\nQ4  yes, from the table above — once Q3 has been answered by hand.")
print("Q5  PARTLY. Values keep their Python types; nothing reports them, and a")
print("    Coalesce default invents a NoneType the document may not have.")
print("Q10 CANNOT without naming the array's path.")
print("Q11 CANNOT. glom has no search over values or paths.")
print("Q12 CANNOT. No melt, and no spec can be written for an unseen shape.")
print(f"""
CONCLUSION. Written after the run and corrected against what printed.

IT COMPLETES, AND THE PREDICTION SAID IT WOULD NOT. Parsing all 286,864 records
costs about 5 seconds and 2.9 GB, which this machine has.

WHAT SCALE DID EXPOSE IS THE PRICE OF THE SPEC. glom applies its four-path spec
at about 50 microseconds per record — 2.5 s over 50,000 — where pydash's dotted
`get` and a compiled jmespath expression each take 0.3 s for the same work.
That is roughly 8x, invisible on any smaller corpus document and worth about
four minutes over the whole file. The spec buys a named output shape and this
is what it costs.

WHAT IS DEFEATED IS THE OTHER HALF OF THE GRID, exactly as at 50 MB and 19.9 MB.
Questions 1, 2, 3, 6, 10, 11 and 12 are CANNOT, because a glom spec IS the
output shape and you cannot write the shape of a document you have not seen.
Scale changed the cost of the answer and not which questions have one.
""")
