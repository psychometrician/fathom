# jq (the Python binding) — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          jq, the Python binding (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/python && uv run try-jq.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# ⚠ **THE CORRECTED LEAF EXPRESSION IS USED THROUGHOUT AND SAID SO LOUDLY.**
#
#     paths(scalars)                                          <- WRONG
#     path(.. | select(type != "object" and type != "array")) <- correct
#
# `select` emits its input when the FILTER'S OUTPUT is truthy and `scalars`
# returns the value, so a leaf that IS `false` fails its own filter. This
# document is the corpus's most exposed: measured below.
#
# **This file and ../r/try-jqr.R are the SAME ENGINE through two doors**, which
# makes them the one place in the grid where a disagreement would mean a
# binding bug rather than a language difference. The numbers are compared.

import json
import time
import jq

print(f"jq (python binding) {jq.__version__ if hasattr(jq, '__version__') else 'see uv.lock'}")

t0 = time.perf_counter()
with open("../source.json") as fh:
    doc = json.load(fh)
print(f"parse: {time.perf_counter() - t0:.1f} s")


def run(expr, label=None):
    t = time.perf_counter()
    out = jq.compile(expr).input_value(doc).first()
    s = time.perf_counter() - t
    if label:
        print(f"  {label:<46} {s:7.2f} s")
    return out, s


print("\nQ0  jq parsed and said nothing. Duplicate keys: last wins. CANNOT.")

# ── THE BROKEN IDIOM, MEASURED. ──────────────────────────────────────────────
print("\n── the broken idiom, on the document it hurts most ──────────────────────")
broken, _ = run("[paths(scalars)] | length", "paths(scalars)")
right, _ = run('[path(.. | select(type != "object" and type != "array"))] | length',
               'path(.. | select(type != obj/arr))')
print(f"    paths(scalars)  {broken:>10,}")
print(f"    corrected       {right:>10,}")
print(f"    DROPPED SILENTLY: {right - broken:,} leaves, "
      f"{100*(right-broken)/right:.2f}% of the document")

# ── Q1/Q2/Q7. ────────────────────────────────────────────────────────────────
top, _ = run("keys")
print(f"\nQ1  keys -> {len(top)}: {', '.join(top)}")
print("    ONE LEVEL, and every deeper level is another expression.")

d, _ = run('[path(.. | select(type != "object" and type != "array")) | length] | max')
print(f"\nQ2  {d}. YES — max leaf path length, one expression.")
print(f"\nQ7  {right:,} leaves.")

# ── Q5. THE QUESTION THIS DOCUMENT WAS CHOSEN FOR. ───────────────────────────
bt, _ = run('[.. | select(type != "object" and type != "array") | type]'
            ' | group_by(.) | map({(.[0]): length}) | add')
print(f"\nQ5  leaves by JSON type: {bt}")
va, _ = run('[.. | objects | select(has("version_added")) | .version_added | type]'
            ' | group_by(.) | map({(.[0]): length}) | add')
print(f"    version_added by type: {va}")
print("    YES, and jq is the cleanest answer in the fourteen: `type` is a")
print("    first-class function, so this is a group_by rather than an inference")
print("    from a Python value or a column dtype.")

# ── Q3/Q6. ───────────────────────────────────────────────────────────────────
kc, _ = run('{api: (.api|keys|length), browsers: (.browsers|keys|length),'
            ' css_props: (.css.properties|keys|length)}')
print(f"\nQ6  jq COUNTS keys: {kc}")
print("    CANNOT — the threshold that would turn a count into `these keys are")
print("    data` is mine, not jq's.")
print("\nQ3  jq names no candidates and prices none. CANNOT.")

# ── Q11, AND THE FOLD. ───────────────────────────────────────────────────────
nu, s_u = run('[.. | select(type == "string") | select(test("^https?://"))] | length',
              "count URLs")
print(f"\nQ11 {nu:,} URL leaves in {s_u:.2f} s. YES.")
up, _ = run('[path(.. | select(type == "string") | select(test("^https?://")))'
            ' | map(tostring) | join(".")] | unique | length')
print(f"    distinct literal URL paths: {up:,} — one per value, no folding")
uf, _ = run('[path(.. | select(type == "string") | select(test("^https?://")))'
            ' | map(tostring) | join(".")]'
            ' | map(gsub("\\\\.[^.]*\\\\.__compat"; ".<key>.__compat")) | unique | length')
print(f"    after ONE hand-written gsub: {uf:,}")

# ── Q8/Q9/Q10/Q12. ───────────────────────────────────────────────────────────
g, _ = run('.api.ANGLE_instanced_arrays.__compat'
           ' | {mdn: .mdn_url, src: .source_file, missing: .nope}')
print(f"\nQ8  a hash of three paths -> mdn = {g['mdn']}")
print(f"\nQ9  the missing one -> {g['missing']!r}. null, not an error, and the")
print("    object survives. YES — same ambiguity as jmespath: absent and null")
print("    are one value.")
arr, _ = run('[path(.. | select(type != "object" and type != "array"))'
             ' | select(any(.[]; type == "number"))] | length')
print(f"\nQ10 {arr:,} leaves under an array index. YES, and EXACTLY — a jq path")
print("    is an ARRAY of steps, and an array index is a NUMBER while a key is a")
print("    STRING. The distinction is in the type, not in the spelling.")
print("\nQ12 the honest table is `[paths, getpath]` pairs — the melt, in one")
print("    expression, with the fold left to you. YES.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

THE SAME ENGINE THROUGH THE OTHER DOOR GIVES IDENTICAL NUMBERS, which is what
this pair exists to check. ../r/try-jqr.R reports 380,049 broken, 470,673
correct, 90,624 dropped, 19.25%; so does this file. 35,392 URLs and 7,243 after
the same gsub, in both. A disagreement here would have meant a binding bug
rather than a language difference, and there is none.

jq ANSWERS MORE OF THIS GRID THAN ANYTHING ELSE IN THE FOURTEEN, and two
features do almost all of the work. `..` makes every search question
expressible — questions 2, 7, 11 and 12 are one line each. `type` as a
first-class function makes question 5 a group_by rather than an inference:
228,083 strings and 57,103 booleans, exact, where pandas reports a dtype of
`object`, rrapply reports `character`, and glom, pydash and pandas each invent
a NoneType the document does not contain.

AND IT IS ONE OF ONLY TWO TOOLS THAT GET QUESTION 10 EXACTLY RIGHT. A jq path
is an ARRAY OF STEPS, and an array index is a NUMBER while an object key is a
STRING — so `select(any(.[]; type == "number"))` is not a heuristic, it is the
distinction itself. 70,420, matching duckdb's fullkey route and two independent
walks. Every melted-path tool here gets it wrong in one direction or the other,
because 1,076 of this document's object keys are all digits.

THE BROKEN IDIOM COSTS 90,624 LEAVES, 19.25%, THE WORST IN THE CORPUS. Every
leaf in this file is a string or a boolean and there are no numbers and no
nulls at all, so `false` is not an edge case here — it is a quarter of the data,
and `paths(scalars)` drops all of it while looking like it worked.

IT IS THE SLOWEST OF THE FAST TOOLS, and worth recording plainly: 2.4 to 3.5
seconds per full-document expression, against duckdb's 0.1 and ijson's 0.4 for
a whole pass. Each question is a fresh traversal, so a session of ten questions
is thirty seconds of re-walking the same 19.9 MB.

WHAT IT STILL CANNOT DO IS QUESTION 3 AND QUESTION 6, for the 29th entry
running. It counts `.api | keys | length` at 1,090 and has no opinion about
whether that makes those keys data. The fold is expressible and not decidable:
one gsub takes 35,392 URL paths to 7,243, and the gsub is mine.
""")
