# glom — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          glom (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/python && uv run try-glom.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **glom is a SPEC language: you write the shape you want and it fills it in.**
# That makes it the clearest case in the fourteen of a tool built entirely for
# question 8 and structurally unable to answer question 1 — you cannot write a
# spec for a document you have not seen.

import json
import time
import glom
from glom import glom as G, Coalesce, T

print(f"glom {glom.__version__}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

print("\nQ0  glom does not parse. CANNOT — it never sees the bytes.")

# ── Q1/Q2/Q3/Q6/Q7. ──────────────────────────────────────────────────────────
print(f"\nQ1  glom('*') is not a listing verb. list(doc) gives {len(doc)} keys,")
print("    and that is Python, not glom. CANNOT beyond one level.")
print("\nQ2  CANNOT. glom has no depth verb; a spec is written to a known depth.")
print("\nQ3  CANNOT. glom names no candidates and prices none.")
print("\nQ6  CANNOT.")

# ── Q8. THE QUESTION glom EXISTS FOR. ────────────────────────────────────────
spec = {
    "mdn_url": "api.ANGLE_instanced_arrays.__compat.mdn_url",
    "source_file": "api.ANGLE_instanced_arrays.__compat.source_file",
    "standard": "api.ANGLE_instanced_arrays.__compat.status.standard_track",
}
t0 = time.perf_counter()
got = G(doc, spec)
print(f"\nQ8  a spec of three paths -> {time.perf_counter()-t0:.4f} s")
for k, v in got.items():
    print(f"      {k:<12} {v}")
print("    YES, and this is the best answer in the fourteen for this question.")
print("    The spec IS the output shape, which nothing else here gives you.")

# ── Q9. THE MISSING FIELD, AND Coalesce. ─────────────────────────────────────
try:
    G(doc, "api.ANGLE_instanced_arrays.__compat.nope")
    print("\nQ9  a missing path returned without error — unexpected.")
except glom.PathAccessError as e:
    print(f"\nQ9  a missing path RAISES: {type(e).__name__}")
    print(f"    {str(e).splitlines()[0][:100]}")
safe = G(doc, Coalesce("api.ANGLE_instanced_arrays.__compat.nope", default=None))
print(f"    with Coalesce(default=None) -> {safe}. YES, but you must ask for it.")
print("    ** AND THE RAISE IS THE RIGHT DEFAULT. ** Compare pandas, which")
print("    writes NaN and lets a typo look like missing data. glom is the only")
print("    tool of the fourteen that treats an absent path as an ERROR first.")

# ── Q4/Q5 over a record list, which is where a spec becomes repeatable. ──────
recs = [{"feature": k, "compat": v.get("__compat")} for k, v in doc["api"].items()
        if isinstance(v, dict) and "__compat" in v]
t0 = time.perf_counter()
rows = [G(r, {"feature": "feature",
              "mdn_url": Coalesce("compat.mdn_url", default=None),
              "chrome": Coalesce("compat.support.chrome.version_added", default=None)})
        for r in recs]
s = time.perf_counter() - t0
have = sum(1 for r in rows if r["mdn_url"] is not None)
print(f"\nQ4  {len(rows):,} api records via one spec in {s:.2f} s")
print(f"    mdn_url present in {have:,}, absent in {len(rows)-have:,}. yes.")

kinds = {}
for r in rows:
    kinds[type(r["chrome"]).__name__] = kinds.get(type(r["chrome"]).__name__, 0) + 1
print(f"\nQ5  chrome.version_added types across those records: {kinds}")
print("    PARTLY — glom returns the value with its Python type intact, so the")
print("    polymorphism survives; but nothing REPORTS it. You count types")
print("    yourself, which is the same qualification pandas gets.")
print("    ** AND THE NoneType COUNT IS glom's OWN **, from the Coalesce default —")
print("    not a null in the document. jq says this field is string and boolean.")

# ── Q10/Q11/Q12. ─────────────────────────────────────────────────────────────
print("\nQ10 CANNOT without naming the array's path, and the deepest arrays sit")
print("    under a browser key that varies. `T` can reach them one at a time.")
print("\nQ11 CANNOT. glom has no search over values or paths — a spec asks for a")
print("    path you already know.")
print("\nQ12 CANNOT. There is no melt, and no way to write a spec for a shape you")
print("    have not seen.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

glom IS THE CLEANEST CASE IN THE FOURTEEN OF A TOOL BUILT FOR ONE HALF OF THIS
GRID. Questions 1, 2, 3, 6, 10, 11 and 12 are all CANNOT, and not by accident:
a glom spec IS the output shape, and you cannot write the shape of a document
you have not seen. Question 8 it answers better than anything else here — three
paths at three depths, named in the output, 0.0001 s.

AND IT IS THE ONLY ONE OF THE FOURTEEN THAT RAISES ON AN ABSENT PATH.
PathAccessError by default, `Coalesce(default=None)` when you mean it. Every
other tool here writes NaN or null and lets a typo look exactly like missing
data — jmespath returns None, pandas writes NaN, jq returns null. That is the
same distinction fathom's defect 35 was about, found on the same day: a zero
that means `nothing there` and a zero that means `you asked wrong` must not
print the same. glom is the only tool in this comparison that had it right
already.

A TRAP THIS FILE FELL INTO AND KEPT. The type census over 1,090 records reports
NoneType 103, str 938, bool 49 — and the 103 Nones are glom's OWN, written by
the Coalesce default where a record has no chrome entry. The document has no
nulls in that field at all; jq says string and boolean only. Counting types
over a filled result counts the filling, which is exactly the error the pandas
attempt makes with NaN. Two tools, same shape of mistake, and both are only
visible because jq answers the question directly.
""")
