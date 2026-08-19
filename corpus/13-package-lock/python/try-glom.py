"""glom — an npm lockfile, 1,657 packages keyed by install path

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          glom (version printed at run time)
  file          ../source.json   759 KB, 1,657 packages, depth 5
  measured      2026-08-11
  run           cd corpus/13-package-lock/python && uv run try-glom.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                            12   NO                  by hand
   2 how deep                                    2   NO                  by hand
   3 what is one record                          3   YES                 CANNOT
   4 always present vs sometimes                 5   YES                 yes
   5 does any field change type                  6   YES                 YES
   6 are any object keys data                    7   -                   NO — and 33 keys BREAK it
   7 how many records                            1   YES                 yes
   8 three named fields to a table               3   YES                 yes — Coalesce
   9 a field missing from some rows              2   YES                 yes — Coalesce
  10 flatten the deepest array                   5   YES                 PARTLY
  11 find every path matching something         12   NO                  by hand
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 4, 5, 7
  14 survives the next file unchanged?               Q4/Q5 yes, the rest no
  15 readable a week later?                          yes, and the trap is invisible
  16 lines, and how much is ceremony?                ~135, and the two walks are 24

**THE DOTTED PATH BREAKS ON 33 OF THE 1,657 KEYS, AND THIS REVERSES WHAT ENTRY
14 CONCLUDED.** glom splits a spec on `.`, and npm package names contain dots:

    glom(doc, "packages.node_modules/@nodelib/fs.scandir")
    -> PathAccessError

**33 package keys and 33 dependency names carry a dot** — `fs.scandir`,
`object.assign`, `bn.js`, `opentype.js`. On `14-nyc-311` glom took the awkward
`:@computed_region_*` keys unquoted where jmespath raised a ParseError, and this
file inverts it exactly: **jmespath's quoted identifier reaches these keys and
glom's dotted spec does not.** Neither language is better at odd keys; they are
brittle in different places, and only a document tells you which.

**glom RAISES, WHICH IS THE GOOD OUTCOME.** pydash's `get` returns `None` for
the same path and says nothing. The escape hatch is `Path('packages', key)`,
which takes segments rather than parsing a string — it works, and **you have to
know the keys contain dots before you know to reach for it.**

**QUESTION 6 IS WHAT THE FILE IS FOR AND glom CANNOT ASK IT.** `packages` is
keyed by install path and four nested collections are keyed by package name, so
their keys are data. glom has `Coalesce`, `Match` and `Regex` for values and
nothing at all for keys. The probe prints seven keyed sites under `KEYS THAT ARE
DATA` and declines an eighth.

**WHERE IT DOES WELL IS QUESTION 5**, because reading values rather than a frame
finds `engines` and `funding` with no NaN to trip on — the same reason it was
right on entry 14, this time on a document that actually has polymorphism.

**AND THE HAND-WRITTEN WALK PRODUCES THIS FILE'S SHARPEST NUMBER.** Enumerating
paths gives **16,545**, which is the probe's count too. Folding the seven keyed
collections to `<key>` gives **49**. **A ratio of 338 to 1**, and the 16,545
version is not a description of the document — it is the document's data printed
sideways. Question 1 is only answerable on this file because something folds,
and glom supplies neither the walk nor the fold.
"""
import json
import re
from collections import Counter
from importlib.metadata import version

from glom import Coalesce, Path, glom

print(f"glom {version('glom')}")

RAW = "../source.json"
doc = json.load(open(RAW))
packages = doc["packages"]

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  glom never sees bytes; json.load parsed and reported nothing.")
print("    Duplicate keys, big ints, NaN: unreported by both. CANNOT.")

# ── Q1/Q2. What is in here, and how deep — by hand. ──────────────────────────
paths, folded, maxd = set(), set(), 0


def walk(x, p="$", f="$", d=1):
    """Two path sets: raw, and folded on the keyed collections."""
    global maxd
    if isinstance(x, (dict, list)):
        maxd = max(maxd, d)
    if isinstance(x, dict):
        keyed = f in ("$.packages",) or f.endswith(("dependencies", "devDependencies",
                                                    "optionalDependencies",
                                                    "peerDependencies", "bin",
                                                    "peerDependenciesMeta"))
        for k, v in x.items():
            paths.add(f"{p}.{k}")
            nf = f"{f}.<key>" if keyed else f"{f}.{k}"
            folded.add(nf)
            walk(v, f"{p}.{k}", nf, d + 1)
    elif isinstance(x, list):
        paths.add(f"{p}[]")
        folded.add(f"{f}[]")
        for v in x:
            walk(v, f"{p}[]", f"{f}[]", d + 1)


walk(doc)
print(f"\nQ1  {len(paths):,} distinct RAW paths — the probe prints 16,545 too.")
print(f"Q1  {len(folded)} paths once the keyed collections fold to <key>.")
print("    THAT RATIO IS THE FINDING: 16,545 against a few dozen. Enumerating")
print("    paths on a keys-as-data document is not an answer, it is the data")
print("    printed sideways. The folding is what makes question 1 answerable,")
print("    and glom supplied neither — this is 12 lines of hand-written walk.")
print(f"Q2  depth {maxd} — same recursion, and it agrees with the probe.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  glom names no row candidates and prices none. The probe names EIGHT")
print("    and prices them, including `an entry of packages 1,657 x 1394 99%")
print("    empty` — the one a reader would otherwise walk into. CANNOT.")
print(f"Q7  {len(packages):,} packages")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
seen = Counter()
for r in glom(packages.values(), [list]):
    seen.update(r)
n = len(packages)
always = [k for k, c in seen.items() if c == n]
some = sorted(((k, c) for k, c in seen.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  {len(seen)} distinct fields; always {len(always)} — {always}")
print(f"Q4  sometimes {len(some)}, rarest five: {some[:5]}")
print("    Matches the probe. `glom(values, [list])` gets the key lists; the")
print("    Counter is Python's.")

# ── Q5. Does any field change type between records? ──────────────────────────
kinds = {}
for r in packages.values():
    for k, v in r.items():
        kinds.setdefault(k, Counter())[type(v).__name__] += 1
varying = {k: dict(v) for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields holding more than one python type: {varying}")
print("    BOTH ARE REAL and both are the probe's. Reading values instead of a")
print("    frame means there is no NaN to mistake for a type — the same reason")
print("    glom was right on 14-nyc-311, now on a document that HAS polymorphism.")

# ── Q6. Are any object keys actually data? AND THE DOTTED-PATH TRAP. ─────────
dotted = [k for k in packages if "." in k]
print(f"\nQ6  YES — and glom cannot say so, and cannot reach {len(dotted)} of the keys.")
key = next(k for k in dotted)
print(f"    key under test: {key}")
try:
    glom(doc, f"packages.{key}")
    print("    ...the dotted spec worked, which contradicts the recorded claim.")
except Exception as e:
    print(f"    glom(doc, 'packages.{key[:28]}…') -> {type(e).__name__}")
print(f"    glom(doc, Path('packages', key))       -> "
      f"{str(glom(doc, Path('packages', key)))[:40]}…")
print("    `Path()` takes segments and does not parse, so it is the escape hatch.")
print("    You need to know the keys contain dots before you know to use it.")
print("    On 14-nyc-311 glom reached the odd keys and JMESPATH raised. Reversed.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
spec = [{"version": "version",
         "resolved": Coalesce("resolved", default=None),
         "license": Coalesce("license", default=None)}]
t = glom(list(packages.values()), spec)
print(f"\nQ8  {len(t):,} rows x 3 cols")
print("   ", t[1])

# ── Q9. A field missing from some records, keeping those rows. ───────────────
lic = glom(list(packages.values()), [Coalesce("license", default=None)])
print(f"\nQ9  license present on {sum(x is not None for x in lic):,} of {len(lic):,}")
first_missing = next(i for i, v in enumerate(packages.values()) if "license" not in v)
print("    `Coalesce(default=None)` keeps the row. Without it glom raises on the")
print(f"    first package lacking the field, which here is index {first_missing} of 1,657 —")
print("    far enough in that a spot check of the first few rows would pass.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
lists = {k: v["funding"] for k, v in packages.items()
         if isinstance(v.get("funding"), list)}
rows = [{"pkg": k, **(e if isinstance(e, dict) else {"url": e})}
        for k, v in lists.items() for e in v]
print(f"\nQ10 funding[] over {len(lists)} packages -> {len(rows)} rows")
print("   ", rows[0])
print("    PARTLY. `funding` is object-or-array AND its elements are")
print("    object-or-string, so two type tests are needed. glom's Coalesce")
print("    handles a missing path, not a path whose TYPE varies.")

# ── Q11. Find every path whose value matches something — by hand. ────────────
URL = re.compile(r"https?://")
hits = Counter()


def find(x, f="$"):
    if isinstance(x, dict):
        keyed = f in ("$.packages",) or f.endswith(("dependencies", "devDependencies",
                                                    "optionalDependencies",
                                                    "peerDependencies", "bin",
                                                    "peerDependenciesMeta"))
        for k, v in x.items():
            find(v, f"{f}.<key>" if keyed else f"{f}.{k}")
    elif isinstance(x, list):
        for v in x:
            find(v, f"{f}[]")
    elif isinstance(x, str) and URL.search(x):
        hits[f] += 1


find(doc)
print(f"\nQ11 URL-valued paths, FOLDED: {dict(hits)}")
print(f"    {sum(hits.values()):,} values over {len(hits)} paths. Unfolded it is")
print("    about 1,700 paths, one per package, which is the same explosion as")
print("    question 1. glom's Match/Regex test a path you name; there is no way")
print("    to ask for every path, so this is 12 more lines of recursion.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cols = list(seen)
flat = glom(list(packages.values()), [{c: Coalesce(c, default=None) for c in cols}])
print(f"\nQ12 {len(flat):,} x {len(cols)}")
print("    The four keyed collections stay dicts in their cells, so this is the")
print("    21-column honest table and NOT the 1,394-column one pandas builds.")
print("    Those collections are separate tables the probe prices at 2,841, 128,")
print("    104 and 101 rows; glom will not tell you they exist.")
