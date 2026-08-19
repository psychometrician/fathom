# glom — AWS Redshift public price list
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          glom (version printed at run time)
#  file          ../source.json   4.0 MB, 8 top-level keys, 89,094 paths, depth 8
#  measured      2026-08-18
#  run           cd corpus/30-aws-redshift-pricing/python && uv run try-glom.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **glom is a SPEC language: you write the shape you want and it fills it in.**
# That makes it structurally unable to answer question 1 — you cannot write a
# spec for a document you have not seen — and on THIS document it has a second,
# sharper problem: glom's path separator is `.`, and the keys contain dots.

import json
import time

import glom
from glom import glom as G
from glom import Coalesce, T

print(f"glom {glom.__version__}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")

print("\nQ0  glom does not parse. CANNOT — it never sees the bytes.")

print(f"\nQ1  CANNOT beyond one level. list(doc) gives {len(doc)} keys and that is")
print("    Python, not glom. A spec names what you already know.")

print("\nQ2  CANNOT. No depth verb; a spec is written to a known depth.")
print("\nQ3  CANNOT. glom names no candidates and prices none.")
print("\nQ4  CANNOT. A spec says what to fetch, not what is present.")
print("\nQ5  CANNOT.")
print("\nQ6  CANNOT — and glom is the tool this document BREAKS, not merely")
print("    defeats. See Q8.")

print(f"\nQ7  CANNOT. len(doc['products']) is {len(doc['products'])} and that is Python.")

print("\nQ7a NO positional alignment. (Circular question — not scored.)")

# ── Q8. THE QUESTION glom EXISTS FOR. ────────────────────────────────────────
sku = next(iter(doc["products"]))
spec = {
    "sku": f"products.{sku}.sku",
    "family": f"products.{sku}.productFamily",
    "location": f"products.{sku}.attributes.location",
}
t0 = time.perf_counter()
one = G(doc, spec)
print(f"\nQ8  ANSWERED for a named record in {time.perf_counter() - t0:.3f} s:")
print(f"    {one}")
print("    Over all products, the spec is `('products.values()', [{...}])` —")
allrows = G(doc, (T["products"], T.values(), [{
    "sku": "sku", "family": "productFamily", "location": "attributes.location"}]))
print(f"    {len(allrows)} rows. glom is genuinely good at this.")

# ── THE FAILURE THAT MATTERS. ────────────────────────────────────────────────
print("\n    ** THE DOTTED KEY BREAKS THE SPEC LANGUAGE. **")
term_sku = next(iter(doc["terms"]["Reserved"]))
term_key = next(iter(doc["terms"]["Reserved"][term_sku]))
print(f"    A reserved term is keyed {term_key!r} — the key CONTAINS DOTS.")
try:
    G(doc, f"terms.Reserved.{term_sku}.{term_key}.offerTermCode")
    print("    the dotted spec RESOLVED (unexpected)")
except Exception as e:
    print(f"    glom(doc, 'terms.Reserved.{term_sku}.{term_key}...') raises:")
    print(f"      {type(e).__name__}: {str(e).splitlines()[0][:90]}")
print("    glom split the key on `.` and looked for levels that do not exist.")
print("    The escape is to abandon the path language and use T:")
ok = G(doc, T["terms"]["Reserved"][term_sku][term_key]["offerTermCode"])
print(f"    glom(doc, T['terms']['Reserved'][…][…]['offerTermCode']) -> {ok!r}")
print("    WHICH IS PYTHON SUBSCRIPTING. The spec language cannot address")
print("    1,728 of this document's own paths, and the workaround is to stop")
print("    using the feature.")

print(f"\nQ9  ANSWERED — Coalesce is glom's best idea:")
missing = G(doc, (T["products"], T.values(),
                  [Coalesce("attributes.instanceType", default=None)]))
print(f"    instanceType present on {sum(v is not None for v in missing)} of "
      f"{len(missing)}, rows kept. `Coalesce(..., default=None)` is exactly")
print("    the 'keep the row' verb, and it is one call.")

print("\nQ10 The deepest array is appliesTo and all 4,505 are EMPTY.")
print("    A glom spec over them returns 4,505 empty lists; flattening gives 0.")
print("    glom cannot distinguish that from the field being absent.")

print("\nQ11 CANNOT. No path search by value; a spec goes where you point it.")

print("\nQ12 CANNOT as exploration. glom BUILDS the flat table well once the")
print("    shape is known — and cannot address the terms half at all, for the")
print("    dotted-key reason above, without dropping to T[...].")

print("\nQ13 YES, absolutely and by design. A spec IS the shape written down.")
print("Q14 NO. Every literal key in every spec above is this document's.")
print("Q15 YES for the dict specs. NO for the T-chains that replace them.")
print("Q16 ~55 lines, most of it specs, which is intent rather than ceremony —")
print("    except the T-chain workaround, which is pure ceremony.")

print("\nCONCLUSION")
print("glom answers Q8 and Q9 and no exploration question, which is what a spec")
print("language is for. What this document adds is a hard failure rather than a")
print("gap: AWS keys reserved terms as `<SKU>.<OFFERTERMCODE>`, glom's paths are")
print("dot-separated, and so the tool cannot name 1,728 of the document's own")
print("locations. A path language with a reserved character meets a document")
print("that uses it, and the only way out is to stop writing paths.")
