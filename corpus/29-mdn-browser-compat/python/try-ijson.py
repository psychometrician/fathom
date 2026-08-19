# ijson — MDN browser-compat-data, the whole bundle
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          ijson (version printed at run time)
#  file          ../source.json   19.9 MB, 14 top-level keys, 838,880 paths, depth 12
#  measured      2026-08-14
#  run           cd corpus/29-mdn-browser-compat/python && uv run try-ijson.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **ijson is the only one of the fourteen that never holds the document.** It
# emits events — (prefix, event, value) — as bytes arrive. That makes it the
# natural answer to "what is in here" for a file too big to load, and this is
# the largest file in the corpus that still fits in memory, so both readings
# are available and comparable.

import time
import ijson

print(f"ijson {ijson.__version__} · backend {ijson.backend}")

print("\nQ0  ijson parses and reports nothing about soundness. It will RAISE on")
print("    malformed input mid-stream, which is more than most, but duplicate")
print("    keys pass through as two events and nothing says so. CANNOT.")

# ── THE ONE PASS. Everything below comes from it. ────────────────────────────
t0 = time.perf_counter()
depth = 0
maxdepth = 0
leaves = 0
by_type = {}
prefixes = set()
top = []
urls = 0
va_types = {}
in_stack = []
with open("../source.json", "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if event in ("start_map", "start_array"):
            depth += 1
            maxdepth = max(maxdepth, depth)
        elif event in ("end_map", "end_array"):
            depth -= 1
        elif event != "map_key":
            leaves += 1
            by_type[event] = by_type.get(event, 0) + 1
            if depth == 1 and prefix and "." not in prefix:
                top.append(prefix)
            if event == "string" and value.startswith(("http://", "https://")):
                urls += 1
            if prefix.endswith("version_added"):
                va_types[event] = va_types.get(event, 0) + 1
            prefixes.add(prefix)
s = time.perf_counter() - t0
print(f"\n    ONE STREAMING PASS over 19.9 MB: {s:.1f} s, constant memory")

# ── Q1/Q2/Q7. ────────────────────────────────────────────────────────────────
print(f"\nQ1  {len(prefixes):,} distinct prefixes seen — and a PREFIX IS A FOLDED")
print("    PATH: ijson writes an array element as `.item`, so every element of")
print("    an array shares one prefix. That is the only automatic folding any")
print("    of the fourteen performs, and nobody asked for it.")
print(f"    the top-level scalars among them: {', '.join(sorted(top)) or '(none)'}")

print(f"\nQ2  {maxdepth}. YES — from the start/end events, counted as they pass.")
print(f"\nQ7  {leaves:,} leaves.")

# ── Q5. ──────────────────────────────────────────────────────────────────────
print("\nQ5  leaf events over the whole document:")
for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]):
    print(f"      {k:<10} {v:>10,}")
print("    version_added by event type:")
for k, v in sorted(va_types.items(), key=lambda kv: -kv[1]):
    print(f"      {k:<10} {v:>10,}")
print("    YES, and it is exact: the EVENT NAME is the JSON type, so a boolean")
print("    arrives as `boolean` and never as the string 'False'. rrapply's melt")
print("    loses precisely this.")

# ── Q11. ─────────────────────────────────────────────────────────────────────
print(f"\nQ11 {urls:,} URL leaves, counted in the same pass. YES.")

# ── Q3/Q4/Q6. ────────────────────────────────────────────────────────────────
print("\nQ3  ijson names no candidates and prices none. The prefix set is a")
print("    field list, not a menu of row shapes. CANNOT.")
print("\nQ4  PARTLY — presence per prefix is countable in the same pass, but")
print("    `always vs sometimes` needs a denominator, and choosing it is Q3.")
print("\nQ6  CANNOT. A prefix folds ARRAYS automatically and never folds an")
print("    object whose keys are data — `api.ANGLE_instanced_arrays` and")
print("    `api.Document` stay separate prefixes. That is the exact distinction")
print("    fathom's fold exists to make, and ijson makes half of it for free")
print("    and the other half not at all.")

# ── Q8/Q9/Q10/Q12. ───────────────────────────────────────────────────────────
t0 = time.perf_counter()
with open("../source.json", "rb") as fh:
    got = next(ijson.items(fh, "api.ANGLE_instanced_arrays.__compat.mdn_url"), None)
print(f"\nQ8  ijson.items(prefix) -> {got}")
print(f"    {time.perf_counter()-t0:.1f} s, because it streams until it finds it.")
print("    yes, but the cost is a pass per field unless you write the event loop.")
with open("../source.json", "rb") as fh:
    miss = next(ijson.items(fh, "api.ANGLE_instanced_arrays.__compat.nope"), "ABSENT")
print(f"\nQ9  a missing prefix -> {miss!r}. No error, no row. YES-ish: absence is")
print("    silence in a stream, which is the same ambiguity as jmespath's None.")
print("\nQ10 the `.item` suffix IS the array flattening, and it is automatic.")
print("    YES — and uniquely, ijson distinguishes an array step from a key step")
print("    in the prefix itself, as duckdb's fullkey does.")
print("\nQ12 PARTLY. The event stream IS a melt — (prefix, type, value) is three")
print("    columns — but assembling it into a table means writing the loop, and")
print("    the prefix has already folded arrays whether you wanted that or not.")

print("""
CONCLUSION. Written after the run and corrected against what printed.

ONE STREAMING PASS OVER 19.9 MB IN 0.4 SECONDS, IN CONSTANT MEMORY, and every
structural answer in this file comes out of that single pass: depth, leaf
count, the type census, the URL count, the version_added split. Nothing else
in the fourteen gives that much for one traversal, and nothing else would still
work if the file were 20 GB.

ITS TYPE ANSWER IS THE MOST EXACT OF ALL FOURTEEN, and for a reason worth
stating: the EVENT NAME is the JSON type. A boolean arrives as the event
`boolean`, so 228,083 strings and 57,103 booleans is not an inference from a
Python value or a column dtype — it is the parser reporting what it read.
rrapply's melt turns those same booleans into the strings "TRUE" and "FALSE";
pandas, glom and pydash each report a NoneType the document does not contain.

AND IT FOLDS ARRAYS AUTOMATICALLY, WHICH NOBODY ASKED FOR AND WHICH PLACES IT
ON A SPECTRUM THIS DOCUMENT MAKES VISIBLE. `.item` means every element of an
array shares one prefix. On this file that takes 470,673 leaves to 452,862
distinct prefixes — a 3.8% reduction, because MDN's nesting is overwhelmingly
objects whose keys are data, and those never fold. Lay the four answers to
`where do the URLs live` side by side:

    no folding at all (rrapply, tidyr, duckdb, jq)     35,392 paths
    ijson, arrays folded automatically                  ~ the same
    fathom, keys-as-data folded                         11,320   <- defect 36
    one hand-written rule over rrapply's columns           176

THE SPECTRUM IS THE FINDING. Folding arrays is free and buys almost nothing
here; folding keys-as-data is the whole game on this document, and it is the
thing only fathom attempts and only fathom gets wrong. 176 is what a person
gets in one line once somebody hands them the levels as columns.

WHERE ijson STOPS is question 3 and question 6, for the 29th entry running. A
prefix set is a field list, not a menu of row shapes; and the prefix folds
arrays while never folding an object whose keys are data, so
`api.ANGLE_instanced_arrays` and `api.Document` remain separate forever. ijson
makes half of fathom's fold for free and has no opinion about the other half.
""")
