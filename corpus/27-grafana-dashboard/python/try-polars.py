"""polars — Grafana "Node Exporter Full", dashboard 1860

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

 ── scoring ──────────────────────────────────────────────────────────────────
  tool          polars (version printed at run time)
  file          ../source.json   667 KB, 25 root keys, 231 distinct paths
  measured      2026-08-13
  run           cd corpus/27-grafana-dashboard/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             8   NO                  CANNOT — the read fails
   2 how deep                                    -   -                   CANNOT
   3 what is one record                          5   -                   CANNOT
   4 always present vs sometimes                 4  YES                  PARTLY, on a hand-built frame
   5 does any field change type                  4   NO                  CANNOT — see below
   6 are any object keys data                    -   -                   CANNOT
   7 how many records                            6  YES                  132, after pre-flattening by hand
   8 three named fields to a table               3  YES                  yes, on a hand-built frame
   9 a field missing from some rows              2  YES                  yes — null
  10 flatten the deepest array                   3  YES                  yes — explode
  11 find every path matching something          -   -                   CANNOT
  12 flattest honest table                       -   -                   CANNOT
  13 needed the shape in advance?                    YES — enough to avoid the bad fields
  14 survives the next file unchanged?               NO
  15 readable a week later?                          yes, what there is of it
  16 lines, and how much is ceremony?                ~55

**polars CANNOT READ THIS DOCUMENT, by any of four routes**, and that is the
result. `pl.read_json` on the file, `pl.DataFrame` on the panel list,
`strict=False` as the error message itself suggests, and `infer_schema_length=None`
all raise. This is the second entry running where polars is the one tool of the
fourteen that cannot get started — it failed on a name collision on entry 28 and
on type unification here.

**The cause is one genuinely polymorphic field.**
`fieldConfig.overrides[].properties[].value` holds an integer, a string and an
object at different sites, and polars' type system has no supertype for those.
Every other tool in the comparison either reports the variation (jq, ijson,
pydash, duckdb) or ignores it (pandas, glom, jmespath); polars is the only one
for which it is fatal.
"""
import json
import sys

import polars as pl

print(f"polars {pl.__version__} · python {sys.version.split()[0]}")

doc = json.load(open("../source.json"))
panels = doc["panels"] + [q for p in doc["panels"] for q in p.get("panels", [])]

# ── Q0. Soundness. ────────────────────────────────────────────────────────
print("\nQ0  CANNOT. Nothing is reported about duplicates, 2^53 or NaN.")

# ── Q1. FOUR ROUTES IN, FOUR FAILURES. ───────────────────────────────────
print("\nQ1  CANNOT — and it is worth showing all four attempts, because rule 6")
print("    says a competing tool gets as many tries as the probe got.")
attempts = [
    ("pl.read_json('../source.json')",
     lambda: pl.read_json("../source.json")),
    ("pl.DataFrame(doc['panels'])",
     lambda: pl.DataFrame(doc["panels"])),
    ("pl.DataFrame(doc['panels'], strict=False)",
     lambda: pl.DataFrame(doc["panels"], strict=False)),
    ("pl.DataFrame(..., infer_schema_length=None, strict=False)",
     lambda: pl.DataFrame(doc["panels"], infer_schema_length=None, strict=False)),
]
for label, fn in attempts:
    try:
        print(f"      {label:<56} -> {fn().shape}")
    except Exception as e:
        print(f"      {label:<56} -> {type(e).__name__}")
        print(f"        {str(e).splitlines()[0][:96]}")
print("    The third is the one the second one's own error message recommends.")

# ── Q5, ANSWERED BY THE FAILURE. ─────────────────────────────────────────
vals = [pr.get("value") for p in panels
        for ov in p.get("fieldConfig", {}).get("overrides", [])
        for pr in ov.get("properties", [])]
kinds = {type(v).__name__ for v in vals}
print(f"\nQ5  CANNOT, and the reason IS the Q1 failure. The field that breaks the")
print(f"    read is `fieldConfig.overrides[].properties[].value`, which holds")
print(f"    {len(vals)} values of types {sorted(kinds)}.")
print("    polars cannot REPORT type variation because type variation stops it")
print("    from building the frame at all. That is a categorically different")
print("    answer from 'no' and it is why the grade is CANNOT rather than PARTLY.")

# ── Q2/Q6/Q11/Q12. ───────────────────────────────────────────────────────
print("\nQ2  CANNOT. Depth would come from the inferred schema and there is none.")
print("\nQ6  CANNOT. Keys become columns unconditionally, when they become anything.")
print("\nQ11 CANNOT. No path enumeration, and no frame to enumerate over.")
print("\nQ12 CANNOT. `unnest` lifts one NAMED level at a time and needs a struct")
print("    column to lift; entry 28 hit a DuplicateError trying, and here the")
print("    frame never exists. Two entries, two hard failures, same grade.")

# ── What DOES work: a frame built by dropping every nested field by hand. ─
flat = [{k: v for k, v in p.items() if not isinstance(v, (dict, list))}
        for p in panels]
df = pl.DataFrame(flat)
print(f"\n    ── from here on, everything runs on a frame I pre-flattened in Python:")
print(f"       [{{k: v for k, v in p.items() if not isinstance(v, (dict, list))}} …]")
print(f"       {df.shape[0]} rows x {df.shape[1]} cols. The nested fields are simply gone.")

# ── Q7. THE CENTRAL QUESTION. ────────────────────────────────────────────
print("\nQ7  THE CENTRAL QUESTION.")
print(f"      len(doc['panels'])                        -> {len(doc['panels'])}")
print(f"      the nested panels, gathered in Python     -> {len(panels) - len(doc['panels'])}")
print(f"      the hand-built frame's height             -> {df.height}")
print("    132, but polars contributed nothing to reaching it. The list")
print("    comprehension that finds the nested panels is plain Python, and it")
print("    names `panels` inside `panels` as a literal.")

# ── Q3. What is one record. ──────────────────────────────────────────────
print("\nQ3  CANNOT — nothing proposed, nothing priced:")
tg = [t for p in panels for t in p.get("targets", [])]
for label, n in [("one panel per row (all depths)", len(panels)),
                 ("one TOP-LEVEL panel per row", len(doc["panels"])),
                 ("one target per row", len(tg)),
                 ("one template variable per row", len(doc["templating"]["list"]))]:
    print(f"      {label:<32} {n:>6,}")

# ── Q4. Always vs sometimes. ─────────────────────────────────────────────
print("\nQ4  PARTLY, and read the caveat. On the hand-built frame:")
nulls = dict(zip(df.columns, df.null_count().row(0)))
for c, n in sorted(nulls.items(), key=lambda kv: kv[1])[:5]:
    print(f"      {c:<18} {df.height - n:>4} present  {'always' if n == 0 else ''}")
print("    The caveat is structural: a polars column must exist on every row, so")
print("    an ABSENT field is materialised as null and is now indistinguishable")
print("    from a field that is present and null. The ragged edge this project")
print("    measures is exactly what the type system erases.")

# ── Q8/Q9. Three named fields; a field missing from some rows. ───────────
sel = pl.DataFrame([{k: p.get(k) for k in ("title", "type", "id", "description")}
                    for p in panels])
print(f"\nQ8  {sel.height} rows x 4. yes — once the columns are chosen to be scalars.")
print(sel.head(3))
print(f"\nQ9  `description` is null in {sel['description'].null_count()} of {sel.height}; rows survive.")
print("    yes, and it agrees with jq, ijson and pandas at 84 — but per Q4 that")
print("    null is asserting two different things at once.")

# ── Q10. Flatten the deepest array. ──────────────────────────────────────
tgf = pl.DataFrame({"t": [p.get("targets", []) for p in panels]}).explode("t").drop_nulls()
print(f"\nQ10 `explode` -> {tgf.height} targets. yes, and `explode` is the right verb:")
print("    it is polars' `unnest_longer` and it is clean. It flattens the level you")
print("    hand it, and finding that level was Q7's problem rather than explode's.")

print("""
CONCLUSION. polars cannot read this document. Four routes in — `read_json`,
`DataFrame`, `strict=False`, `infer_schema_length=None` — and all four raise
before any question can be asked. One field, `overrides[].properties[].value`,
is an object at 614 sites, a string at 33 and an integer at 18, and polars' type
system has no supertype for that. Everything scored below CANNOT was
measured on a frame I built by deleting every nested field in plain Python
first, which is the tool not being the tool.

Two structural findings, both worth more than the failure itself.

Type variation is FATAL here rather than reportable. Every other tool either
names the varying field or quietly ignores it; polars is the only one where the
answer to "does any field change type" is that the question cannot be reached.

And where it does build a frame, it erases the ragged edge. A column must exist
on every row, so a field 15 of 132 panels carry becomes a column all 132 carry,
117 of them null, and absent is now spelled the same as present-and-null.

This is the second consecutive entry where polars is the one tool of fourteen
that cannot get started, having failed a completely different way on entry 28.
""")
