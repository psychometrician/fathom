# polars — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          polars (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/python && uv run try-polars.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **The tool-sweep prediction was that polars cannot build the honest table
# here, as it could not on entry 28 — and that the CAUSE would be different.**
# Entry 28's failure was a name collision. This file finds out.

import json
import time
import polars as pl

print(f"polars {pl.__version__}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse (python json): {time.perf_counter() - t0:.1f} s")

print("\nQ0  polars parsed and said nothing. CANNOT.")

# ── Q1. read_json, and what polars infers. ───────────────────────────────────
t0 = time.perf_counter()
try:
    df = pl.read_json("../source.json")
    s = time.perf_counter() - t0
    print(f"\nQ1  pl.read_json -> {df.height} x {df.width} in {s:.1f} s")
    print(f"    columns: {', '.join(df.columns)}")
    print("    ONE ROW, because the root is an object. polars typed every")
    print("    top-level key as a struct and stopped there.")
    for c in df.columns[:4]:
        t = str(df.schema[c])
        print(f"      {c:<14} {t[:96]}{'…' if len(t) > 96 else ''}")
except Exception as e:
    df = None
    print(f"\nQ1  pl.read_json FAILED after {time.perf_counter()-t0:.1f} s")
    print(f"    {type(e).__name__}: {str(e)[:200]}")

# ── Q12. THE HONEST TABLE. ───────────────────────────────────────────────────
print("\nQ12 the flattest honest table, attempted three ways.")

# 1. unnest the root.
if df is not None:
    t0 = time.perf_counter()
    try:
        u = df.unnest("api")
        print(f"    unnest('api')        -> {u.height} x {u.width} "
              f"in {time.perf_counter()-t0:.1f} s")
        print(f"    ONE ROW STILL, now {u.width:,} columns wide (13 originals plus")
        print("    api's 1,090). Unnesting a struct WIDENS; it never lengthens,")
        print("    because there is one row to widen. Repeating it to the bottom")
        print("    is pandas' 427,019-column explosion by another spelling.")
    except Exception as e:
        print(f"    unnest('api')        FAILED: {type(e).__name__}: {str(e)[:120]}")

# 2. the record-shaped attempt: hand polars a list of records.
recs = [{"feature": k, **v.get("__compat", {})} for k, v in doc["api"].items()
        if isinstance(v, dict) and "__compat" in v]
t0 = time.perf_counter()
try:
    api = pl.from_dicts(recs, infer_schema_length=None)
    print(f"    from_dicts(api records) -> {api.height:,} x {api.width} "
          f"in {time.perf_counter()-t0:.1f} s")
    print(f"    columns: {', '.join(api.columns)}")
except Exception as e:
    api = None
    print(f"    from_dicts(api records) FAILED after {time.perf_counter()-t0:.1f} s")
    print(f"    ** {type(e).__name__}: {str(e)[:300]}")

# 3. the melt, which is what rrapply and json_tree do in one call.
print("\n    and the MELT — the thing rrapply does in 0.4 s and json_tree in one")
print("    query. polars has no walk over a document of unknown shape: `unnest`")
print("    needs a named struct column, `explode` needs a named list column, and")
print("    both need to be told which. There is no verb to iterate.")


def walk(x, acc, out):
    if isinstance(x, dict):
        for k, v in x.items():
            walk(v, acc + [k], out)
    elif isinstance(x, list):
        for i, v in enumerate(x):
            walk(v, acc + [str(i)], out)
    else:
        # DEPTH IS CARRIED, NOT DERIVED. A first draft joined the path and
        # counted "." — which over-counts here, because browser versions are
        # KEYS and they contain dots: `support.safari.15.4` is three steps
        # written with four separators. Same class of loss as the numeric-key
        # problem in Q10: a joined path string is not the path.
        out.append((".".join(acc), x, len(acc)))


t0 = time.perf_counter()
flat = []
walk(doc, [], flat)
s = time.perf_counter() - t0
melt = pl.DataFrame({"path": [p for p, _, _ in flat],
                     "value": [str(v) for _, v, _ in flat],
                     "depth": [d for _, _, d in flat]})
print(f"    my own walk -> {melt.height:,} x {melt.width} in {s:.1f} s")
print("    ** AND THE WALK IS MINE. ** polars holds the result well; it")
print("    contributes nothing to producing it. CANNOT.")

# ── Q5. THE QUESTION THIS DOCUMENT WAS CHOSEN FOR. ───────────────────────────
print("\nQ5  version_added, the tri-typed field.")
kinds = {}
for p, v, _ in flat:
    if p.endswith("version_added"):
        kinds[type(v).__name__] = kinds.get(type(v).__name__, 0) + 1
print(f"    from my walk, keeping python types: {kinds}")
if api is not None and "support" in api.columns:
    print(f"    polars' own dtype for `support`: {str(api.schema['support'])[:110]}…")
print("    ** THE `str(v)` IN MY MELT ABOVE IS NOT OPTIONAL AND THAT IS THE")
print("    POINT. ** A polars column is typed, so a str and a bool cannot share")
print("    one; the melt only works because I stringified first, which is the")
print("    same coercion rrapply's melt does silently. Q5 CANNOT, from the table.")

# ── Q2/Q7/Q4. ────────────────────────────────────────────────────────────────
by_dots = melt.select(pl.col("path").str.count_matches(r"\.").max()).item() + 1
dotted = sum(1 for _, _, d in flat) and melt.filter(
    pl.col("path").str.count_matches(r"\.") + 1 != pl.col("depth")).height
print(f"\nQ2  {melt['depth'].max()}, from the depth MY walk carried.")
print(f"    counting '.' in the joined path gives {by_dots} — THE SAME MAXIMUM,")
print(f"    and it is right by luck: {dotted:,} of {melt.height:,} leaves have a")
print("    key containing a dot, because browser versions are keys — `15.4`,")
print("    `5.0`. The maximum coincides; the DISTRIBUTION does not, and a first")
print("    draft of this file printed a depth histogram that disagreed with")
print("    rrapply and tidyr at every level from 4 down. Same class of loss as")
print("    Q10's: a joined path string is not the path.")
print(f"\nQ7  {melt.height:,} leaves.")
print("\nQ4  polars groups well once the table exists:")
byd = melt.group_by("depth").len().sort("depth")
print("      " + str(byd).replace("\n", "\n      ")[:400])

print("\nQ3  polars names no candidates and prices none. CANNOT.")
print("Q6  CANNOT.")

# ── Q8/Q9/Q11. ───────────────────────────────────────────────────────────────
if api is not None:
    got = api.select(["feature", "mdn_url", "source_file"]).head(2)
    print(f"\nQ8  three named fields -> {got.height} x {got.width}. yes, once the")
    print("    record list exists — and choosing it was Q3.")
    n_null = api.select(pl.col("mdn_url").is_null().sum()).item()
    print(f"\nQ9  mdn_url null in {n_null:,} of {api.height:,} rows, rows survive. YES.")

t0 = time.perf_counter()
nu = melt.filter(pl.col("value").str.contains(r"^https?://")).height
print(f"\nQ11 {nu:,} URL leaves in {time.perf_counter()-t0:.2f} s — fast, over MY table.")
loose = melt.filter(pl.col("value").str.starts_with("http")).height
up = (melt.filter(pl.col("value").str.contains(r"^https?://"))
          .select(pl.col("path").n_unique()).item())
print(f"    (loose `starts_with(\"http\")` gives {loose:,} — {loose-nu:,} more, strings")
print("     that begin `http` without being URLs. duckdb's LIKE made the same slip.)")
print(f"    distinct literal URL paths: {up:,} — one per value, no folding.")
print("\nQ10 explode() flattens a named list column. The deepest arrays here sit")
print("    under a browser key that varies, so there is no one column to name.")
print("    CANNOT without the walk.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

THE PREDICTION HELD ON BOTH HALVES: polars cannot build the honest table, and
the cause is NOT entry 28's name collision. It is a TYPE conflict —

  TypeError: unexpected value while building Series of type String;
             found value of type List(String)

— raised by from_dicts on the `tags` field, which is a list in some api records
and absent or scalar in others. polars types a column before it has seen the
column, and this document does not agree to be typed.

THE THREE ROUTES ALL END IN THE SAME PLACE. read_json gives 1 x 14 with every
top-level key a Struct; unnest widens that to 1 x 1,103 and would keep widening
to pandas' 427,019; from_dicts raises. The melt that rrapply does in 0.4 s and
json_tree does in one query has no polars spelling at all: unnest needs a named
struct column, explode needs a named list column, and neither has a form that
means "whatever is there". THERE IS NO VERB TO ITERATE, and that is the finding.

WHAT POLARS IS GOOD AT it is very good at. Given MY walk's output it filters
470,673 rows for URLs in under 0.01 s. It is a table engine handed a document,
and this corpus keeps finding the same division: the tools that win question 12
are the ones that will walk something they have not been described first.

AND THE `str(v)` IN MY MELT IS THE POINT, NOT A DETAIL. A polars column is
typed, so a str and a bool cannot share one — the melt only compiles because I
stringified first. That is exactly the coercion rrapply's melt performs
silently, arrived at from the opposite direction: here the type system forces
you to notice. Question 5 is CANNOT from the table either way.
""")
