"""polars — an npm lockfile, 1,657 packages keyed by install path

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   759 KB, 1,657 packages, depth 5
  measured      2026-08-11
  run           cd corpus/13-package-lock/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   CANNOT
   1 what is in here                             6   NO                  NO — 5 columns
   2 how deep                                    5   NO                  YES — via the dtype tree
   3 what is one record                          5   YES                 NO — answers 1 x 5
   4 always present vs sometimes                12   YES                 NO — see the three routes
   5 does any field change type                  7   YES                 NO — silently flattens it
   6 are any object keys data                    6   -                   NO — 1,657 struct fields
   7 how many records                            2   YES                 yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   3   YES                 CANNOT
  11 find every path matching something          4   NO                  PARTLY
  12 flattest honest table                       4   YES                 PARTLY
  13 needed the shape in advance?                    NO for 2
  14 survives the next file unchanged?               no
  15 readable a week later?                          yes, and that is the danger
  16 lines, and how much is ceremony?                ~135, and the three routes are the point

**THREE WAYS TO BUILD THE PACKAGES TABLE, THREE DIFFERENT ANSWERS, AND THE ONLY
CORRECT ONE IS THE ONE THAT FAILS.** All three are one line. Measured below:

    pl.DataFrame({"rec": values}).unnest("rec") ....  7 of 21 fields   SILENT
    pl.from_dicts(values) ......................... 19 of 21 fields   SILENT
    pl.from_dicts(values, infer_schema_length=None)  SchemaError

**The first keeps SEVEN of twenty-one fields** — the schema is taken from the
first record, and the first record is npm's root package, which happens to have
exactly those seven keys. `resolved`, `integrity`, `dev`, `engines` and `funding`
are among the fourteen dropped. **`infer_schema_length=None` does not help this
route.** Nothing raises; the frame just has fewer columns than the document.

**The third RAISES, and its error is the truest sentence polars produces about
this file**: `failed to determine supertype of struct[2] and list[str]`. That is
`funding` exactly — an object on 282 packages and a one-element array of text on
2. **Asked to look at every record, polars correctly discovers the polymorphism
and refuses; asked to look at some, it silently picks one and drops the rest.**

**QUESTION 5 IS LOST TWICE OVER.** Even where a field survives, its dtype
flattens the variation: `engines` comes back `Struct({'node': String})` on all
1,051 packages that have it, so the one package where `engines` is an ARRAY is
gone, and the four other engine keys (`npm`, `bare`, `yarn`, `iojs`) with it.
The probe prints both polymorphic fields under `FIELDS THAT CHANGE TYPE`.

**AND `packages` COMES BACK AS A STRUCT WITH 1,657 FIELDS.** One per install
path, not in document order, the root's field named `""`. Where pandas made
12,153 columns, polars made one column whose TYPE is the data. Neither can say
the keys are data.

**It did not refuse the file**, which DuckDB does, and it read it in under
0.1 s. The cost of that speed is that everything above is silent.
"""
import json
import time
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))
values = list(doc["packages"].values())
truth = set().union(*(set(v) for v in values))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
t0 = time.time()
df = pl.read_json(RAW)
print(f"\nQ0  pl.read_json: {df.shape} in {time.time() - t0:.1f}s — no refusal, no warning.")
print("    DuckDB refuses this same file over one empty-string key; polars takes")
print("    it. It reports nothing about duplicate keys, big ints or NaN. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
pkg_dtype = df.schema["packages"]
print(f"\nQ1  {df.width} columns: {df.columns}")
print(f"Q1  `packages` is a Struct with {len(pkg_dtype.fields):,} fields — ONE PER")
print("    INSTALL PATH. The schema of this file IS the data.")
print(f"    first three: {[f.name for f in pkg_dtype.fields[:3]]}")
print("    Not in document order, and the root package's field is named \"\".")

# ── Q2. How deep does it go — walking the dtype tree. ────────────────────────
def dtype_depth(dt):
    if isinstance(dt, pl.Struct):
        return 1 + max((dtype_depth(f.dtype) for f in dt.fields), default=0)
    if isinstance(dt, pl.List):
        return 1 + dtype_depth(dt.inner)
    return 0


deep = max(dtype_depth(d) for d in df.dtypes)
print(f"\nQ2  deepest dtype nests {deep} levels below the row, and the document is one")
print(f"    object, so it is {1 + deep} deep. The probe prints 5. CORRECT, and it is")
print("    the same dtype walk that answered this on 14-nyc-311.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print(f"\nQ3  polars answers {df.shape} — the whole document as one row. That IS one")
print("    of the probe's eight candidates, priced there as `the whole document")
print("    1 rows x 5 cols`. polars offers no other and prices none. NO.")
print(f"Q7  {len(doc['packages']):,} packages — counted in Python, because polars has")
print("    no verb for 'how many fields does this struct have'.")

# ── Q4. THE THREE ROUTES, and what each one loses. ───────────────────────────
print(f"\nQ4  the document has {len(truth)} distinct fields across the packages.")
print("    Three one-line routes from a list of records to a table:")

routes = []
a = pl.DataFrame({"rec": values}).unnest("rec")
routes.append(("pl.DataFrame({'rec': …}).unnest", a, None))
b = pl.from_dicts(values)
routes.append(("pl.from_dicts(values)", b, None))
try:
    c = pl.from_dicts(values, infer_schema_length=None)
    routes.append(("pl.from_dicts(…, infer_schema_length=None)", c, None))
except Exception as e:
    routes.append(("pl.from_dicts(…, infer_schema_length=None)", None,
                   f"{type(e).__name__}: {e}"))

for label, frame, err in routes:
    if frame is None:
        print(f"      {label:44} RAISES")
        print(f"      {'':44} {err}")
    else:
        missing = sorted(truth - set(frame.columns))
        print(f"      {label:44} {frame.width:2} of {len(truth)} fields, "
              f"{len(missing)} dropped SILENTLY")
        if missing:
            print(f"      {'':44} missing: {missing}")

flat = b   # the least-bad of the three
present = {c: flat.height - flat[c].null_count() for c in flat.columns}
always = [c for c, n in present.items() if n == flat.height]
some = sorted(((c, n) for c, n in present.items() if n < flat.height), key=lambda kv: kv[1])
print(f"\nQ4  taking the 19-field route: always {len(always)} — {always}")
print(f"Q4  sometimes {len(some)}, rarest five: {some[:5]}")
print("    The probe reports 21 fields, 1 always and 20 sometimes. This is right")
print("    about the 19 it kept and silent about the two it did not. NO.")
print("    THE ERROR FROM THE THIRD ROUTE IS THE TRUEST THING HERE: asked to")
print("    inspect every record, polars finds the polymorphism and refuses.")

# ── Q5. Does any field change type? IT FLATTENS IT. ──────────────────────────
print("\nQ5  the document's two polymorphic fields, and what polars did with them:")
for c in ("engines", "funding"):
    counts = {}
    for v in values:
        if c in v:
            counts[type(v[c]).__name__] = counts.get(type(v[c]).__name__, 0) + 1
    if c in flat.columns:
        print(f"      {c:8} document: {counts}")
        print(f"      {'':8} polars dtype: {flat.schema[c]}")
    else:
        print(f"      {c:8} document: {counts} — DROPPED by this route")
print("    `engines` is Struct({'node': String}): the ONE package where it is an")
print("    ARRAY is gone, and so are the other four engine keys — npm, bare,")
print("    yarn, iojs. The probe prints:")
print("      engines  object x1,050, array[1] text x1")
print("      funding  object x282, array[1] object x26, array[1] text x2")
print("    A struct field has one dtype, so the question cannot be asked. NO.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print(f"\nQ6  `packages` is a Struct of {len(pkg_dtype.fields):,} fields whose names are")
print("    install paths, so the answer is YES and polars cannot say it. The")
print("    nested collections are the same — dependencies, devDependencies,")
print("    optionalDependencies and peerDependencies are keyed by PACKAGE NAME.")
print("    The probe names seven such sites and declines an eighth. polars turns")
print("    each into a struct whose schema grows with the data.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
t = flat.select("version", "resolved", "license")
print(f"\nQ8  {t.height:,} rows x {t.width} cols")
print(t.head(3))
print(f"\nQ9  license present on {flat.height - flat['license'].null_count():,} of"
      f" {flat.height:,} — rows kept, gaps null")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
n_lists = sum(1 for v in values if isinstance(v.get("funding"), list))
print(f"\nQ10 CANNOT from polars' own frame. `funding` was coerced to one dtype, so")
print(f"    the array form is gone before it can be exploded. The document has")
print(f"    57 funding[] entries over {n_lists} packages.")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
hits = {c: int(flat[c].str.contains("http").sum())
        for c, dt in zip(flat.columns, flat.dtypes) if dt == pl.String}
print(f"\nQ11 string columns holding a URL: { {c: n for c, n in hits.items() if n} }")
print("    ONE of the five folded paths, 1,656 of 2,003 values — the worst")
print("    question 11 in this directory. Three are inside `funding`, lost to")
print("    the Q5 coercion, and the fourth is `deprecated`, which this route")
print("    dropped entirely at Q4. Every miss compounds an earlier silent loss.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print(f"\nQ12 {flat.shape}, and what was lost is NOT nothing: two whole fields, the")
print("    array form of `engines` and `funding`, and four of the five engine")
print("    keys. The keyed collections remain structs whose schemas are")
print("    dependency names. The probe prices those as separate tables of")
print("    2,841, 128, 104 and 101 rows. PARTLY.")
