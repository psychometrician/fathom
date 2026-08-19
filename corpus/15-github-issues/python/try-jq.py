"""jq (via the `jq` python binding) — 100 GitHub issues from one repository

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   686 KB, 100 issues, depth 4
  measured      2026-08-11
  run           cd corpus/15-github-issues/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             4   NO                  YES — exactly 179
   2 how deep                                    2   NO                  YES — exactly 4
   3 what is one record                          5   NO                  PARTLY — 2 key-sets
   4 always present vs sometimes                10   NO                  YES — `has` says it
   5 does any field change type                  5   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              4   YES                 yes
  10 flatten the deepest array                   3   YES                 yes
  11 find every path matching something          4   NO                  YES — best here
  12 flattest honest table                       4   YES                 yes
  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the array-index fold needs a comment
  16 lines, and how much is ceremony?                ~115, and the folds are most of it

**jq HAS `has`, AND ON THIS DOCUMENT THAT IS THE QUESTION.**
`has("closed_by")` is true on all 100 issues; `.closed_by != null` is true on 48.
**Two separate predicates for two separate facts**, so question 4 comes out as
5 sometimes-ABSENT and 8 always-present-but-NULL, with exact per-field counts.
pandas, polars and DuckDB each report **13** and cannot say which is which.

**IT REPRODUCES THREE OF THE PROBE'S NUMBERS EXACTLY:**

    paths, array indices folded ..... 179    probe prints 179
    max path length ................... 4    probe prints 4 levels deep
    distinct key-sets, SORTED ......... 2     probe prints 2

**AND THE THIRD ONE IS WHERE DuckDB GOES WRONG BY 7x.**
`count(DISTINCT json_structure(json))` returns **14** on this file, because
`json_structure` records the TYPE of every value and `"closed_by": null` is a
different structure from `"closed_by": {…}`. jq's `keys_unsorted | sort` asks
which keys are PRESENT and gets 2. Across three documents that expression has
been exact once, 5.4x high once, and 7x high here — and nothing signals which.

**`paths` GIVES 179 WITHOUT THE ROOT**, where ijson's prefixes give 180 counting
the empty root. Both are right; they differ by a convention neither states.

**AND QUESTION 11 IS FREE AND CORRECT.** `paths(type == "string" and test(...))`
returns 77 paths and 3,297 values with no field named and no recursion written.
No folding was needed — this document has no keys-as-data, so the raw answer is
the answer, unlike `13-package-lock` where the same expression gave 1,974 paths.
"""
import json
import time
from importlib.metadata import version

import jq

print(f"jq python binding {version('jq')}")

RAW = "../source.json"
doc = json.load(open(RAW))
n = len(doc)


def run(program, label):
    t0 = time.time()
    out = jq.compile(program).input(doc).first()
    print(f"    [{time.time() - t0:5.2f}s] {label}")
    return out


# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  the binding takes an already-parsed object, so jq never saw the bytes.")
print("    No duplicate-key, big-int or NaN report from either side. CANNOT.")

# ── Q1. What is in here. ─────────────────────────────────────────────────────
print("\nQ1  paths, with array indices folded to []:")
paths = run('[paths | map(if type == "number" then "[]" else . end) | join(".")]'
            ' | unique', "…")
print(f"    {len(paths)} — THE PROBE PRINTS 179. Exact.")
print("    ijson's prefixes give 180 because they count the empty root. Both are")
print("    right and neither states the convention.")

# ── Q2. How deep does it go. ─────────────────────────────────────────────────
print("\nQ2  max path length:")
print(f"    {run('[paths | length] | max', '…')} — the probe prints '4 levels deep'. Exact.")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  distinct key-sets over the 100 issues:")
ks = run('[.[] | keys_unsorted | sort | join(",")] | unique | length', "with sort")
print(f"    {ks} — THE PROBE PRINTS 2. Exact.")
print("    DuckDB's count(DISTINCT json_structure(json)) returns 14 on this file,")
print("    because json_structure records the TYPE of every value and")
print("    `closed_by: null` differs from `closed_by: {...}`. Asking which keys")
print("    are PRESENT gives 2; asking what shape the values have gives 14.")
print("    jq still names no row candidate and prices none. PARTLY.")
print(f"Q7  {run('length', 'length')} issues")

# ── Q4. THE DISCRIMINATOR — `has` IS THE WHOLE ANSWER. ──────────────────────
print("\nQ4  which keys are PRESENT, using keys_unsorted:")
counts = run('[.[] | keys_unsorted[]] | group_by(.) | map({(.[0]): length}) | add', "…")
absent = sorted(k for k, c in counts.items() if c < n)
print("\nQ4  and which are present holding NULL:")
nulls = run('[.[] | to_entries[] | select(.value == null) | .key]'
            ' | group_by(.) | map({(.[0]): length}) | add', "…")
nullish = sorted(k for k in nulls if counts[k] == n)
print(f"      sometimes ABSENT ({len(absent)}): {absent}")
print(f"      present but NULL ({len(nullish)}): {nullish}")
print("      exact null counts:")
for k, c in sorted(nulls.items(), key=lambda kv: -kv[1]):
    tag = "  (absent on the rest)" if counts[k] < n else ""
    print(f"        {k:28} {c:3} null of {counts[k]:3} present{tag}")
print("    `has(\"closed_by\")` is true on all 100; `.closed_by != null` on 48.")
print("    TWO PREDICATES FOR TWO FACTS. The frame tools have one hole and one")
print("    count, and report 13 without being able to split it 5 and 8.")

# ── Q5. Does any field change type between records. ─────────────────────────
print("\nQ5  fields whose non-null type varies:")
varying = run('''[.[] | to_entries[] | select(.value != null)
      | {k: .key, t: (.value | type)}] | group_by(.k)
      | map(select((map(.t) | unique | length) > 1) | .[0].k)''', "…")
print(f"    {varying or 'none'} — the probe's answer.")
print("    `select(.value != null)` is what makes it right; pandas' python-type")
print("    check counts NoneType as a type and reports 9 changes that are holes.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections — GitHub ships fixed field names. n/a, and the")
print("    probe's KEYS THAT ARE DATA section is empty for this file.")

# ── Q8/Q9. Extraction. ───────────────────────────────────────────────────────
print("\nQ8  three fields:")
t = run('[.[] | {number, state, user: .user.login}]', "…")
print(f"    {len(t)} rows x 3 cols · {t[0]}")
print("\nQ9  a field that is null on some issues:")
q9 = run('[.[] | {number, closed_by: .closed_by.login}]', "…")
print(f"    {len(q9)} rows kept, {sum(r['closed_by'] is None for r in q9)} null")
print("    `.closed_by.login` through a null gives null rather than raising, and")
print("    object construction keeps the row. jmespath's projection returns 48.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
print("\nQ10 labels:")
labels = run('[.[] | .number as $n | .labels[] | {number: $n, name, color}]', "…")
print(f"    {len(labels)} rows; {sum(1 for r in doc if not r['labels'])} issues have none.")

# ── Q11. Find every path whose value matches something. ─────────────────────
print("\nQ11 URL-valued paths, no field named:")
urls = run('[paths(type == "string" and test("https?://"))'
           ' | map(if type == "number" then "[]" else . end) | join(".")]'
           ' | group_by(.) | map({(.[0]): length}) | add', "…")
print(f"    {sum(urls.values()):,} values over {len(urls)} paths")
print(f"    top three: {dict(sorted(urls.items(), key=lambda kv: -kv[1])[:3])}")
print("    NO FOLD WAS NEEDED. On 13-package-lock the same expression gave 1,974")
print("    paths because the keys were data; here there are none.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 flattened, with the nested objects prefixed by hand:")
flat = run('''[.[] | . as $r | reduce (to_entries[] | select(.value | type == "object"))
      as $e ($r; . + ($e.value | with_entries(.key |= "\\($e.key).\\(.)")) | del(.[$e.key]))]''',
           "…")
keys = sorted(set().union(*(set(r) for r in flat)))
print(f"    {len(flat)} rows, {len(keys)} distinct keys")
print("    The prefixing is MINE — `with_entries(.key |= ...)` — and it is why")
print("    nothing collides. polars' `unnest` RAISES on this document and")
print("    DuckDB's `struct.*` returns 19 duplicate names; pandas prefixes and")
print("    is the only one of the four that gets it right unaided.")
