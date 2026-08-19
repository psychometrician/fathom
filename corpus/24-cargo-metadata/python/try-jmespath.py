"""jmespath — cargo metadata for this repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   27 KB, 8 packages, depth 8
  measured      2026-08-11
  run           cd corpus/24-cargo-metadata/python && uv run try-jmespath.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                             5   YES                 PARTLY — one level
   2 how deep                                    1   -                   CANNOT
   3 what is one record                          4   YES                 counts, prices none
   4 always present vs sometimes                 6   NO                  YES for presence
   5 does any field change type                  4   YES                 PARTLY
   6 are any object keys data                   12   YES                 keys(@), and see below
   7 how many records                             2  NO                  yes
   8 three named fields to a table                2 YES                 yes
   9 a field missing from some rows                3 YES                 yes
  10 flatten the deepest array                     4 YES                 YES — its best answer
  11 find every path matching something            4 YES                 CANNOT
  12 flattest honest table                         3 YES                 CANNOT
  13 needed the shape in advance?                    YES for 5, 6, 10, 11
  14 survives the next file unchanged?               YES for everything except a query
                                                     that names a FEATURE
  15 readable a week later?                          YES
  16 lines, and how much is ceremony?                ~85

  jmespath GETS QUESTION 6's INGREDIENTS IN ONE EXPRESSION and cannot escape a
  hyphen. `packages[].features.zlib-ng-compat` is a LexerError — it refuses to
  lex the minus — and `packages[].features."zlib-ng-compat"` works. So on this
  document the escaping problem is about the DATA, and jmespath is the tool
  where naming an individual feature is hardest and enumerating them all is
  easiest.

  `packages[].keys(features) | []` gives all 28 names in one line and does not
  raise, because every package HAS a `features` object — even the two of this
  repository's own crates, whose objects are empty.
"""
import json
import re
import time
from collections import Counter
from importlib.metadata import version

import jmespath

print(f"jmespath {version('jmespath')}")

RAW = "../source.json"
doc = json.load(open(RAW))


def q(e):
    t = time.time()
    return jmespath.search(e, doc), time.time() - t


print("\nQ0  an expression language over a parsed object. CANNOT.")

keys, t = q("packages[].keys(@) | []")
print(f"\nQ1  `packages[].keys(@) | []` -> {len(keys)} occurrences, "
      f"{len(set(keys))} distinct, {t:.3f}s")
print(f"Q1  the root has {len(doc)} keys, reached by `keys(@)`")
print("\nQ2  CANNOT. No recursive descent; the probe says 8.")

n, _ = q("length(packages)")
print(f"\nQ3  jmespath counts and prices nothing. CANNOT.")
print(f"Q7  {n} packages, {len(doc['workspace_members'])} workspace members,"
      f" {len(doc['resolve']['nodes'])} resolve nodes")

# ── Q6. THE CENTREPIECE. ────────────────────────────────────────────────────
fk, t = q("packages[].keys(features) | []")
c = Counter(fk)
once = [k for k, v in c.items() if v == 1]
hy = [k for k in c if "-" in k]
print(f"\nQ6  `packages[].keys(features) | []` -> {len(c)} distinct feature names")
print(f"    over {len(fk)} occurrences, {len(once)} appearing ONCE, {t:.3f}s")
print("    NO RAISE, because every package HAS a `features` object — even the")
print("    two whose objects are empty. Entries 20 and 21 both lost a query to")
print("    `keys(null)`; this document has no absent parent to trip it.")
print("    ONE LINE FOR THE WHOLE VOCABULARY — the ingredient `classify()`")
print("    judges on, and jmespath states no verdict as usual.")
print(f"\nQ6  AND {len(hy)} OF THE {len(c)} NAMES CONTAIN A HYPHEN:")
try:
    q("packages[].features.zlib-ng-compat")
    print("    `packages[].features.zlib-ng-compat` parsed — rewrite this note")
except Exception as e:
    print(f"    `features.zlib-ng-compat` unquoted: {type(e).__name__}: "
          f"{' '.join(str(e).split())[:48]}")
v, _ = q('packages[].features."zlib-ng-compat"')
print(f'    `features."zlib-ng-compat"` quoted -> {v}')
print("    SO NAMING ONE FEATURE IS THE HARDEST THING HERE AND ENUMERATING ALL")
print("    28 IS THE EASIEST. On entries 21 and 23 the hyphens were FIELD names")
print("    and quoting them was a schema chore; here they are VALUES, so the")
print("    quoting is a property of the data — question 6 from the other end.")

# ── Q4/Q5. ──────────────────────────────────────────────────────────────────
present = Counter(keys)
print(f"\nQ4  package keys not on every package: "
      f"{[k for k, v in present.items() if v < n]}")
nul = {k: sum(1 for p in doc["packages"] if p[k] is None) for k in present}
print(f"Q4  written NULL: {len([k for k, v in nul.items() if v])}; NULL ON ALL {n}: "
      f"{sorted(k for k, v in nul.items() if v == n)}")
print("    `keys(@)` counts PRESENCE and gets the first line right. The null")
print("    counts needed python — jmespath tests ONE named key at a time.")
print("\nQ5  `type()` on a named path, and no census:")
for f in ("name", "edition", "targets"):
    ts, _ = q(f"packages[].{f} | [].type(@)")
    print(f"    packages[].{f:10} -> {dict(Counter(ts))}")
print("    The probe reports NO type change, and jq confirms zero once `an empty")
print("    array is not a type` is applied. jmespath can confirm one field at a")
print("    time, 24 times, and never discover it.")

# ── Q8/Q9/Q10/Q11/Q12. ──────────────────────────────────────────────────────
t8, t = q("packages[].{name: name, version: version, edition: edition}")
print(f"\nQ8  one multiselect-hash -> {len(t8)} rows x 3, {t:.3f}s")
d, _ = q("packages[].{n: name, d: description}")
print(f"\nQ9  {len(d)} rows kept, `description` null on {sum(x['d'] is None for x in d)}")
tg, t = q("packages[].targets[]")
dk, _ = q("resolve.nodes[].deps[].dep_kinds[]")
print(f"\nQ10 `packages[].targets[]` -> {len(tg)} rows, {t:.3f}s")
print(f"Q10 `resolve.nodes[].deps[].dep_kinds[]` -> {len(dk)} rows at depth 6 —")
print("    THREE FLATTENING OPERATORS AND NOTHING ELSE, on the deepest array in")
print("    the document. jmespath's best answer again, and it drops the parent")
print("    again: neither the package nor the node id survives.")
print("\nQ11 CANNOT enumerate paths — no recursive descent. Named paths work:")
for e in ("packages[].repository", "packages[].homepage"):
    v, _ = q(e)
    vals = [x for x in v if isinstance(x, str)]
    print(f"    {e:28} {len(vals)} strings, "
          f"{sum(bool(re.match(r'^https?://', x)) for x in vals)} URLs")
print("    jq reports 5 distinct URL PATHS; two are under")
print("    `metadata.release.pre-release-replacements[]`.")
print("\nQ12 a multiselect-hash naming all 24 package fields would work and stop")
print("    at `features`, `targets` and `dependencies`. No auto-flatten. And a")
print("    hash that named the 28 features would need every one of them quoted.")
