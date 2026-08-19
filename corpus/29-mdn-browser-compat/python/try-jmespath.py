# jmespath — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jmespath (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/python && uv run try-jmespath.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **jmespath is a query language with no descent operator.** jq has `..`, which
# is what makes every search question answerable there. This file measures what
# that absence costs on a document 12 levels deep.

import json
import time
import jmespath

print(f"jmespath {jmespath.__version__ if hasattr(jmespath,'__version__') else 'see uv.lock'}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

print("\nQ0  jmespath does not parse. CANNOT.")

# ── Q1. keys() exists, one level. ────────────────────────────────────────────
t0 = time.perf_counter()
top = jmespath.search("keys(@)", doc)
print(f"\nQ1  keys(@) -> {len(top)} keys in {time.perf_counter()-t0:.3f} s")
print(f"    {', '.join(top)}")
print("    ONE LEVEL. keys() does not recurse and there is no operator that does.")

print("\nQ2  CANNOT. No descent operator, so depth is not expressible.")
print("Q3  CANNOT. Names no candidates, prices none.")
print("Q6  CANNOT.")

# ── Q8/Q9. THE QUESTION IT EXISTS FOR. ───────────────────────────────────────
t0 = time.perf_counter()
got = jmespath.search(
    "{mdn: api.ANGLE_instanced_arrays.\"__compat\".mdn_url, "
    " src: api.ANGLE_instanced_arrays.\"__compat\".source_file, "
    " missing: api.ANGLE_instanced_arrays.\"__compat\".nope}", doc)
print(f"\nQ8  a multiselect hash of three paths -> {time.perf_counter()-t0:.4f} s")
for k, v in got.items():
    print(f"      {k:<8} {v}")
print("    YES. The hash literal names the output keys, like glom's spec.")
print(f"\nQ9  the missing one -> {got['missing']!r}. NULL rather than an error, and")
print("    the row survives. YES — and note this is the OPPOSITE default to")
print("    glom, which raises. A typo here is indistinguishable from absence.")

# ── Q4/Q7. Projections over the record list. ─────────────────────────────────
# THE FIRST DRAFT WROTE THIS AND IT IS A SILENT WRONG SHAPE:
#     api.*."__compat".{mdn: mdn_url, src: source_file}
# The multiselect-hash binds to the WHOLE projection, not to each element, so
# it returns ONE dict of two keys instead of 1,090 records. No error; the next
# line failed with `'str' object has no attribute 'get'` several steps away.
wrong = jmespath.search("api.*.\"__compat\".{mdn: mdn_url, src: source_file}", doc)
print(f"\nQ4  the natural expression returns a {type(wrong).__name__} of "
      f"{len(wrong)} — NOT 1,090 records.")
print("    A multiselect after a projection binds once, to the projection's")
print("    result. It does not raise; it returns a plausible smaller thing.")
t0 = time.perf_counter()
rows = jmespath.search("api.*.{mdn: \"__compat\".mdn_url, src: \"__compat\".source_file}", doc)
s = time.perf_counter() - t0
have = sum(1 for r in rows if r and r.get("mdn"))
print(f"    written so the hash is INSIDE the projection -> {len(rows):,} records "
      f"in {s:.2f} s")
print(f"    mdn_url present in {have:,}, absent in {len(rows)-have:,}. yes,")
print("    and `api.*` IS a real contribution — a wildcard over an object's")
print("    values, which is exactly the keys-as-data traversal.")
print(f"\nQ7  {len(rows):,} under that reading. yes.")

# ── Q5. ──────────────────────────────────────────────────────────────────────
# SAME TRAP AGAIN: the long dotted form after `api.*` returns None here, not a
# list of 1,090. The multiselect form is the one that projects per element.
naive = jmespath.search("api.*.\"__compat\".support.chrome.version_added", doc)
print(f"\n    (the dotted form returns {naive!r} — the projection trap, twice.)")
va = [r["va"] for r in
      jmespath.search("api.*.{va: \"__compat\".support.chrome.version_added}", doc)]
kinds = {}
for v in va:
    kinds[type(v).__name__] = kinds.get(type(v).__name__, 0) + 1
print(f"\nQ5  chrome.version_added types: {kinds}")
print("    PARTLY. The values keep their Python types, but jmespath has no")
print("    `type` function to group by — you count them in Python afterwards.")
print("    jq does this in the query; that is the difference between the two.")

# ── Q10/Q11/Q12. ─────────────────────────────────────────────────────────────
# THE TRAP A THIRD TIME. `api.*."__compat".support.*` returns None; a second
# wildcard after a projection does not nest, it replaces.
t0 = time.perf_counter()
naive10 = jmespath.search("api.*.\"__compat\".support.*", doc)
flat = jmespath.search("api.*.{s: \"__compat\".support}", doc)
flat = [r["s"] for r in flat if r.get("s")]
print(f"\nQ10 `api.*.\"__compat\".support.*` -> {naive10!r}  (the trap, a THIRD time)")
print(f"    the multiselect form -> {len(flat):,} support groups in "
      f"{time.perf_counter()-t0:.2f} s")
print("    PARTLY — one level per star, the path written out by hand, and every")
print("    star after the first needs the multiselect workaround. There is no `**`.")
print("\nQ11 CANNOT. No descent operator, so `every path whose value matches`")
print("    has no expression. This is the single largest gap against jq.")
print("\nQ12 CANNOT. Same reason.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

NO DESCENT OPERATOR IS THE WHOLE STORY. jq has `..`, and that single operator
is why jq answers questions 2, 11 and 12 and jmespath answers none of them.
They are otherwise close relatives — both are query languages over parsed JSON,
both express question 8 well — and the gap between them on this grid is almost
entirely one piece of syntax.

`api.*` IS A REAL CONTRIBUTION and deserves saying. A wildcard over an OBJECT's
values is precisely the keys-as-data traversal, and it is spelled the same as
the array wildcard — which is the idea fathom's fold is built on, available here
as ordinary syntax. What is missing is any way to discover that `api` is the
container you want.

AND IT HAS THE OPPOSITE MISSING-PATH DEFAULT TO glom, WHICH IS THE SHARPER
COMPARISON. A path that does not exist returns None, exactly like a path that
exists and holds null. glom raises. Both files were written the same day fathom
repaired defect 35, which is the same distinction in a third place.

ONE TRAP, HIT THREE TIMES IN THIS FILE ALONE. `api.*."__compat".{mdn: …}` returns a
single two-key dict rather than 1,090 records, because a multiselect after a
projection binds to the projection's RESULT. It does not raise. The failure
surfaced three lines later as an AttributeError about a str, which names
neither the expression nor the cause — the same shape of error as `python/
pandas.py` shadowing its library, and as duckdb's `path`-versus-`fullkey`
above. A query language that answers the wrong question quietly is worse on
this grid than one that cannot answer it.

IT HAPPENED AGAIN AT Q5 AND AT Q10, with the dotted form returning None both
times. Three occurrences in one attempt file, each needing the multiselect
workaround, is not a slip by the author — it is what using this tool on a
document of unknown shape actually costs.
""")
