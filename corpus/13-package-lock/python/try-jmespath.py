"""jmespath — an npm lockfile, 1,657 packages keyed by install path

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   759 KB, 1,657 packages, depth 5
  measured      2026-08-11
  run           cd corpus/13-package-lock/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             6   YES                 PARTLY
   2 how deep                                    2   -                   CANNOT
   3 what is one record                          3   YES                 CANNOT
   4 always present vs sometimes                 5   YES                 yes, with Python
   5 does any field change type                  6   YES                 PARTLY — type() helps
   6 are any object keys data                    8   -                   PARTLY — `keys()` reaches them
   7 how many records                            1   NO                  YES — keys(packages)
   8 three named fields to a table               3   YES                 yes — multiselect
   9 a field missing from some rows               5   YES                 NO — drops 923 silently
  10 flatten the deepest array                   5   YES                 PARTLY
  11 find every path matching something          4   NO                  NO
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 7
  14 survives the next file unchanged?               Q7 yes; the rest name `packages`
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~115, and the quoting is the ceremony

**jmespath REACHES THE AWKWARD KEYS HERE AND glom AND pydash DO NOT, WHICH IS
THE EXACT REVERSE OF `14-nyc-311`.** 33 package keys contain a dot —
`node_modules/@nodelib/fs.scandir` — and a quoted identifier takes them:

    packages."node_modules/@nodelib/fs.scandir"   ->  the record

glom raises `PathAccessError` on the dotted spelling; pydash returns `None`
silently. On entry 14 it was jmespath that raised, on `:@computed_region_*`,
while the other two took the same string unquoted. **Neither language is better
at odd keys. They are brittle in different places, and only a document says
which** — which is the argument for a corpus rather than a benchmark.

**`keys()` ALSO MAKES jmespath THE ONLY PATH LANGUAGE THAT ANSWERS QUESTION 7
WITHOUT BEING TOLD THE SHAPE.** `length(keys(packages))` is 1,657 — a count of a
keyed collection, which is what this document's records live in.

**QUESTION 9 IS STILL WRONG AND STILL SILENT, AND IT IS WORSE THAN ON ENTRY 14.**
`values(packages)[].license` returns **734 of 1,657** — a projection drops the
elements without the key. The multiselect hash keeps all 1,657. **Two natural
idioms, 923 rows apart, no warning.** On entry 14 the same failure cost 9,261
rows of 20,000; here it costs 56% of the document.

**AND QUESTION 11 IS A FLAT NO.** There is no recursive descent, so `every path
whose value matches` cannot be written. The truth folded is five paths and 2,003
values; unfolded it is roughly 1,700 paths, because the keys are data.
"""
import json
from collections import Counter
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")

RAW = "../source.json"
doc = json.load(open(RAW))
n = len(doc["packages"])

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  jmespath queries an object json.load already built, and has no health")
print("    vocabulary at all — no parse, no bytes, no warnings. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
top = jmespath.search("keys(@)", doc)
allkeys = Counter(jmespath.search("values(packages)[].keys(@)|[]", doc))
print(f"\nQ1  top level: {top}")
print(f"Q1  `values(packages)[].keys(@)|[]` -> {sum(allkeys.values()):,} key occurrences")
print(f"    over {len(allkeys)} distinct field names.")
print("    PARTLY: `packages` had to be named. jmespath has no way to find the")
print("    collection, and no way to enumerate paths at all.")

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
print("\nQ2  no depth function and no recursive descent operator. CANNOT.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  jmespath names no row candidates and prices none. The probe names")
print("    EIGHT with costs. CANNOT.")
print(f"Q7  `length(keys(packages))` = {jmespath.search('length(keys(packages))', doc):,}")
print("    THE ONLY PATH LANGUAGE HERE THAT COUNTS A KEYED COLLECTION IN ITS OWN")
print("    VOCABULARY. glom and pydash both hand off to Python for this.")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
always = [k for k, c in allkeys.items() if c == n]
some = sorted(((k, c) for k, c in allkeys.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  always {len(always)} — {always}")
print(f"Q4  sometimes {len(some)}, rarest five: {some[:5]}")
print("    Correct; jmespath supplied the key lists and Python counted them.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  jmespath HAS `type()`, so this is partly askable:")
for f in ("engines", "funding", "resolved"):
    kinds = Counter(jmespath.search(f"values(packages)[].{f} | [*].type(@)", doc) or [])
    print(f"      {f:9} {dict(kinds)}")
print("    engines and funding both vary, which is the probe's answer. But the")
print("    FIELD had to be named — there is no `map over every key` — so this is")
print("    three answers to a question that asks about all 21. PARTLY.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
dotted = [k for k in doc["packages"] if "." in k]
key = dotted[0]
print(f"\nQ6  YES: `packages` is keyed by install path, and 4 nested collections")
print("    are keyed by package name. jmespath cannot SAY they are data — but")
print("    `keys()` treats them as values, which is nearer than glom or pydash get.")
print(f"    {len(dotted)} keys contain a dot. Reaching one:")
quoted = f'packages."{key}".version'
print(f'    {quoted}  ->  {jmespath.search(quoted, doc)}')
try:
    jmespath.search(f"packages.{key}", doc)
    print("    ...unquoted parsed too, which contradicts the recorded claim.")
except Exception as e:
    print(f"    unquoted -> {type(e).__name__}, so quoting is mandatory")
print("    glom RAISES on this key and pydash returns None. Entry 14 was the")
print("    other way round. Neither language is safer; they break elsewhere.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = jmespath.search("values(packages)[].{version: version, resolved: resolved, "
                    "license: license}", doc)
print(f"\nQ8  {len(t):,} rows x 3 cols — multiselect hash")
print("   ", t[1])

# ── Q9. A field missing from some records, keeping those rows. IT DROPS. ─────
proj = jmespath.search("values(packages)[].license", doc)
ms = jmespath.search("values(packages)[].{v: version, l: license}", doc)
print(f"\nQ9  `values(packages)[].license`        -> {len(proj):,} values")
print(f"Q9  `values(packages)[].{{v: …, l: …}}`  -> {len(ms):,} rows, "
      f"{sum(r['l'] is None for r in ms):,} null")
print(f"    THE PROJECTION LOST {n - len(proj):,} ROWS — {100 * (n - len(proj)) / n:.0f}% of the")
print("    document — and said nothing. Both expressions are natural and the")
print("    question asked for the second. On 14-nyc-311 this same failure cost")
print("    9,261 of 20,000; the rate depends entirely on how ragged the file is.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
arrays = jmespath.search("values(packages)[?type(funding) == 'array'].funding", doc)
rows = [e for a in arrays for e in a]
print(f"\nQ10 funding arrays: {len(arrays)} packages, {len(rows)} elements")
print("   ", rows[0])
print("    The `type(funding) == 'array'` filter is required because funding is")
print("    an object on 282 packages. PARTLY: the elements are themselves")
print("    object-or-string, and jmespath cannot flatten a heterogeneous list")
print("    into one shape.")

# ── Q11. Find every path whose value matches something. ──────────────────────
named = jmespath.search("values(packages)[?resolved != null && "
                        "contains(resolved, 'http')] | length(@)", doc)
print(f"\nQ11 `resolved` holding a URL: {named:,} — but the FIELD had to be named.")
print("    jmespath has no recursive descent, so 'every path whose value matches'")
print("    is not expressible. The truth folded is five paths and 2,003 values:")
print("    resolved 1,656 · funding.url 282 · funding[].url 53 · deprecated 8 ·")
print("    funding[] 4. Unfolded it is ~1,700 paths, because the keys are data. NO.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
spec = "values(packages)[].{" + ", ".join(f'"{k}": "{k}"' for k in allkeys) + "}"
flat = jmespath.search(spec, doc)
print(f"\nQ12 {len(flat):,} x {len(allkeys)} — every field quoted, spec built in Python")
print("    The install path is LOST: `values()` discards the keys, so the row's")
print("    identity is gone. Keeping it needs a separate `keys()` call and a zip.")
print("    That is the keys-as-data cost stated precisely — the identifier is")
print("    not a field, so a value-shaped tool cannot carry it.")
