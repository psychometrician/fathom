"""pydash — 100 GitHub issues from one repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   686 KB, 100 issues, depth 4
  measured      2026-08-11
  run           cd corpus/15-github-issues/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             7   NO                  YES — in its own words
   2 how deep                                    3   NO                  YES
   3 what is one record                          3   YES                 CANNOT
   4 always present vs sometimes                 8   NO                  YES — separates both
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              10   YES                 YES — and the DEFAULT TRAP
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          6   NO                  YES — in its own words
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 7, 11
  14 survives the next file unchanged?               yes for those
  15 readable a week later?                          NO — the default trap is invisible
  16 lines, and how much is ceremony?                ~125, and the deep walk is 8

**`pydash.get(record, "closed_by", "DEFAULT")` RETURNS `None`, NOT `"DEFAULT"`,
AND THAT REPRODUCES ENTRY 25's FINDING ON A SECOND DOCUMENT.** `FINDINGS.md`
records it there as *"pydash proved it by accident"*: the default fires only
when the key is **absent**, and `closed_by` is **present holding null** on 52 of
these 100 issues. The value you get back is the null, and it looks exactly like
a lookup that fell through.

**AND THE SAME CALL ONE LEVEL DEEPER BEHAVES THE OPPOSITE WAY.**
`pydash.get(record, "closed_by.login", "DEFAULT")` returns `"DEFAULT"`, because
traversal *through* a null fails and the default does fire. **Same function, same
record, two different answers depending on how deep you reach** — and the shallow
one is the one that lies.

**WITH THAT KNOWN, pydash SEPARATES ABSENT FROM NULL CORRECTLY.** 5 sometimes-
absent, 8 always-present-but-null, which is the truth and which pandas, polars
and DuckDB all collapse into a single 13.

**`map_values_deep` IS STILL A MAPPER, NOT A WALKER** — the entry-14 trap. Both
callbacks here return `value`, and the file proves the document survived rather
than assuming it.

**AND ON THIS DOCUMENT ITS PATH ENUMERATION IS ACTUALLY USEFUL.** 77 URL paths
and 3,297 values, reported straight. On `13-package-lock` the same walk gave
1,974 paths because the keys were data; here there are none, so the raw answer
IS the answer. **The tool did not improve — the document stopped fighting it.**
"""
import copy
import json
import re
import time
from importlib.metadata import version

import pydash

print(f"pydash {version('pydash')}")

RAW = "../source.json"
doc = json.load(open(RAW))
n = len(doc)

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pydash is a collection library; json.load parsed and said nothing. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
paths, maxlen = set(), 0


def survey(value, path):
    global maxlen
    maxlen = max(maxlen, len(path))
    paths.add("$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path))
    return value            # REQUIRED — map_values_deep MUTATES otherwise.


t0 = time.time()
pydash.map_values_deep(doc, survey)
print(f"\nQ1  map_values_deep visited every leaf in {time.time() - t0:.1f}s:"
      f" {len(paths)} distinct LEAF paths")
print("    The probe prints 179 paths; this is leaves only, so the container")
print("    paths — $[], $[].user, $[].labels[] — are never named.")
print(f"Q2  deepest leaf path is {maxlen} segments; the probe prints 4 levels deep.")
print(f"    document intact after the walk: doc[0]['number'] = {doc[0]['number']}")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  pydash names no row candidates and prices none. The probe names three")
print("    and prices them, including `100 rows x 144 cols 53% empty`. CANNOT.")
print(f"Q7  {pydash.size(doc)} issues")

# ── Q4. THE DISCRIMINATOR, and pydash passes it. ────────────────────────────
keys = pydash.flatten([list(r) for r in doc])
counts = pydash.count_by(keys)
nonnull = pydash.count_by(pydash.flatten(
    [[k for k, v in r.items() if v is not None] for r in doc]))
absent = sorted(k for k, c in counts.items() if c < n)
nullish = sorted(k for k in counts if counts[k] == n and nonnull.get(k, 0) < n)
print(f"\nQ4  {len(keys):,} key occurrences over {len(counts)} names")
print(f"      sometimes ABSENT ({len(absent)}): {absent}")
print(f"      present but NULL ({len(nullish)}): {nullish}")
print("    BOTH KINDS, SEPARATELY, and `count_by` is pydash's own. pandas, polars")
print("    and DuckDB each report 13 and cannot say which is which.")

# ── Q5. Does any field change type between records? ──────────────────────────
kinds = {}
for r in doc:
    for k, v in r.items():
        if v is not None:
            kinds.setdefault(k, set()).add(type(v).__name__)
varying = {k: v for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields with more than one python type, nulls excluded: {varying or 'none'}")
print("    NONE — the probe's answer. Excluding null is the trick pandas cannot")
print("    perform on a frame, where it reports 9 changes that are all holes.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — GitHub ships fixed field names. n/a")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = [{"number": r["number"], "state": r["state"],
      "user": pydash.get(r, "user.login")} for r in doc]
print(f"\nQ8  {len(t)} rows x 3 cols")
print("   ", t[0])

# ── Q9. THE DEFAULT TRAP. ───────────────────────────────────────────────────
r_null = next(r for r in doc if r["closed_by"] is None)
r_absent = next(r for r in doc if "pull_request" not in r)
print("\nQ9  `pydash.get(record, key, 'DEFAULT')` on this document:")
print(f"      closed_by  PRESENT holding null -> {pydash.get(r_null, 'closed_by', 'DEFAULT')!r}")
print(f"      closed_by.login through a null  -> {pydash.get(r_null, 'closed_by.login', 'DEFAULT')!r}")
print(f"      pull_request ABSENT             -> {pydash.get(r_absent, 'pull_request', 'DEFAULT')!r}")
print("    THE FIRST ONE IS THE TRAP. The default fires when the key is ABSENT;")
print("    a key present holding null returns the null, which looks identical to")
print("    a lookup that fell through. FINDINGS.md records exactly this on")
print("    25-usgs-quakes — `pydash proved it by accident` — and here it is on a")
print("    second document.")
print("    AND ONE LEVEL DEEPER IT REVERSES: traversal THROUGH a null fails, so")
print("    the default does fire. Same function, same record, opposite answers.")
lic = pydash.map_(doc, "closed_by.login")
print(f"\nQ9  `map_(doc, 'closed_by.login')` -> {len(lic)} values,"
      f" {sum(x is None for x in lic)} None — all 100 rows kept.")
print("    jmespath's projection returns 48 for the same question.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
labels = [{"number": r["number"], **lab} for r in doc for lab in r["labels"]]
print(f"\nQ10 labels flattened to {len(labels)} rows;"
      f" {sum(1 for r in doc if not r['labels'])} issues have none and vanish.")

# ── Q11. Find every path whose value matches something. ─────────────────────
URL = re.compile(r"https?://")
hits = {}


def find(value, path):
    if isinstance(value, str) and URL.search(value):
        key = "$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path)
        hits[key] = hits.get(key, 0) + 1
    return value


pydash.map_values_deep(copy.deepcopy(doc), find)
print(f"\nQ11 {sum(hits.values()):,} URL values over {len(hits)} paths")
print(f"    top three: {dict(sorted(hits.items(), key=lambda kv: -kv[1])[:3])}")
print("    NO FOLD WAS NEEDED. On 13-package-lock this same walk produced 1,974")
print("    paths because the keys were data; here there are none, so the raw")
print("    answer is the answer. The tool did not change — the document did.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
flat = [pydash.pick(r, *counts) for r in doc]
print(f"\nQ12 {len(flat)} x {len(counts)}")
print("    The nested objects stay dicts. Nothing collides, because nothing was")
print("    flattened — polars RAISES on this document and DuckDB returns 19")
print("    duplicate column names for attempting the same thing.")
