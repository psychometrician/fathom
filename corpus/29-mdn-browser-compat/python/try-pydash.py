# pydash — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          pydash (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/python && uv run try-pydash.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **pydash is lodash for Python: a large library of collection utilities.**
# Its JSON-shaped verb is `get` with a dotted path, and `deep_map_values`.
# The question is whether a utility belt reaches a document 12 levels deep.

import json
import time
import pydash

print(f"pydash {pydash.__version__}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

print("\nQ0  pydash does not parse. CANNOT.")
print(f"\nQ1  pydash.keys(doc) -> {len(pydash.keys(doc))} keys. ONE LEVEL.")
print("    There is no recursive listing verb.")

# ── Q8/Q9. `get`, which is the whole reason to reach for it. ─────────────────
t0 = time.perf_counter()
u = pydash.get(doc, "api.ANGLE_instanced_arrays.__compat.mdn_url")
missing = pydash.get(doc, "api.ANGLE_instanced_arrays.__compat.nope")
dflt = pydash.get(doc, "api.ANGLE_instanced_arrays.__compat.nope", "ABSENT")
print(f"\nQ8  pydash.get(dotted path) -> {time.perf_counter()-t0:.5f} s")
print(f"      {u}")
print("    YES. A dotted string, no ceremony, and it is the friendliest")
print("    spelling of question 8 in the Python half.")
print(f"\nQ9  a missing path -> {missing!r}; with a default -> {dflt!r}.")
print("    YES, the row survives — and like jmespath and unlike glom, an absent")
print("    path and a null are the same None unless you pass a sentinel.")

# ── Q4/Q7 over the record list. ──────────────────────────────────────────────
recs = list(doc["api"].items())
t0 = time.perf_counter()
rows = [{"feature": k,
         "mdn": pydash.get(v, "__compat.mdn_url"),
         "chrome": pydash.get(v, "__compat.support.chrome.version_added")}
        for k, v in recs]
s = time.perf_counter() - t0
have = sum(1 for r in rows if r["mdn"])
print(f"\nQ4  {len(rows):,} api records, one get() each, in {s:.2f} s")
print(f"    mdn present {have:,}, absent {len(rows)-have:,}. yes.")
print(f"\nQ7  {len(rows):,} under that reading. yes — and the reading was mine.")

kinds = {}
for r in rows:
    kinds[type(r["chrome"]).__name__] = kinds.get(type(r["chrome"]).__name__, 0) + 1
print(f"\nQ5  chrome.version_added types: {kinds}")
print("    PARTLY, with the same qualification as glom and pandas: the types")
print("    survive, nothing reports them, and the NoneType count is pydash's")
print("    own — the default for an absent path, not a null in the document.")

# ── Q12. The melt, via deep_map_values. ──────────────────────────────────────
print("\nQ12 pydash has no melt. `deep_map_values` transforms leaves IN PLACE and")
print("    returns the same shape, so it cannot flatten. The nearest thing is a")
print("    walk I write myself, which is what every other utility library here")
print("    also requires. CANNOT.")

t0 = time.perf_counter()
leaves = []


def walk(x, acc):
    if isinstance(x, dict):
        for k, v in x.items():
            walk(v, acc + [k])
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, acc + [str(i)])
    else:
        leaves.append((acc, x))


walk(doc, [])
print(f"    (my own walk, for the counts below: {len(leaves):,} leaves in "
      f"{time.perf_counter()-t0:.1f} s)")

d = max(len(a) for a, _ in leaves)
print(f"\nQ2  {d}, from MY walk. pydash contributed nothing.")
print("\nQ3  CANNOT. Names no candidates, prices none.")
print("Q6  CANNOT.")
nu = sum(1 for _, v in leaves if isinstance(v, str) and v.startswith(("http://", "https://")))
print(f"\nQ11 {nu:,} URL leaves — from MY walk, filtered with a Python")
print("    comprehension. pydash has no search over paths. CANNOT.")
arr = sum(1 for a, _ in leaves if any(seg.isdigit() for seg in a))
print(f"\nQ10 {arr:,} leaves whose path holds an all-digit segment — and that is")
print("    the WRONG number for the same reason as rrapply's: 1,076 object keys")
print("    here are all digits. The true count is 70,420, which needs a walk")
print("    that remembers whether the parent was a list. CANNOT from a path.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

pydash IS A UTILITY BELT AND THIS IS A DOCUMENT, and the two never quite meet.
`get` with a dotted path is the friendliest spelling of question 8 anywhere in
the Python half — no spec object, no compile step, just a string. Everything
else on this grid it answers with a walk I wrote: questions 2, 10, 11 and 12
are all my recursion with pydash holding the coat.

`deep_map_values` IS THE VERB THAT LOOKS LIKE IT SHOULD WORK AND DOES NOT. It
maps over leaves and returns the SAME SHAPE, so it can transform a document but
never flatten one. There is no melt in the library.

ITS Q10 NUMBER MATCHES rrapply's EXACTLY, 75,791, AND BOTH ARE WRONG. Two
tools in two languages, the same path-string reasoning, the same over-count
against the true 70,420 — because 1,076 object keys in this document are all
digits. Agreement between two tools is not correctness when both make the same
assumption, which is worth remembering every time this corpus cites two
independent tools agreeing.

AND THE NoneType COUNT IS ITS OWN, for the third time in the Python half. glom
writes it from Coalesce, pandas from NaN, pydash from get's default. All three
report a type the document does not contain, and only jq — which has `type` as
a function over the real value — gets version_added right at string and boolean.
""")
