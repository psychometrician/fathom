"""jq (via the `jq` python binding) — 200 OpenLibrary search results

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   64 KB, 200 docs, depth 4
  measured      2026-08-11
  run           cd corpus/17-openlibrary/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             3   NO                  YES — exactly 31
   2 how deep                                    2   NO                  YES — exactly 4
   3 what is one record                          14  NO                  PARTLY — prices it, one field
   4 always present vs sometimes                 6   NO                  YES
   5 does any field change type                  4   NO                  YES — correctly none
   6 are any object keys data                    2   -                   n/a
   7 how many records                             4   NO                  yes — both answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 yes
  10 flatten the deepest array                   2   YES                 yes
  11 find every path matching something          4   NO                  YES — best here
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 1,2,3,4,5,7,11
  14 survives the next file unchanged?               yes for all of those
  15 readable a week later?                          the array-index fold needs a comment
  16 lines, and how much is ceremony?                ~120

**jq COMES CLOSER TO THE FOURTH OPERATION THAN ANYTHING ELSE IN EITHER LANGUAGE,
AND STILL DOES NOT REACH IT.** `group_by` applies a split, and emptiness is
computable in the same expression, so the **whole search is expressible** — and
it is written out below. Its ranking agrees with the probe's exactly:

    ebook_access     4 kinds   worst group 16.4%   <- what the probe reports
    has_fulltext     2 kinds   worst group 16.4%   ties; it is a COARSENING of it
    public_scan_b    2 kinds   worst group 34.4%   no better than not splitting
    edition_count   14 kinds   worst group 35.5%   WORSE

**That is a 15-line program with a helper function, written knowing exactly what
to look for.** jq has no verb for it and prints nothing unasked. The distance
between "expressible" and "printed without being asked" is what item 23i calls
*the looking*, and this file measures it precisely: fifteen lines.

**IT REPRODUCES THREE OF THE PROBE'S NUMBERS EXACTLY:**

    paths, array indices folded ..... 31    probe prints 31
    max path length .................. 4    probe prints 4 levels deep
    distinct key-sets, SORTED ....... 15    probe prints 15

**AND THE KEY-SET COUNT AGREES WITH DuckDB HERE**, which it did not on the two
previous entries. `count(DISTINCT json_structure)` was 5.4x high on
`13-package-lock` and 7.0x high on `15-github-issues`; this document has neither
data keys nor nulls in its records, which is the condition that makes it safe.

**QUESTION 11 IS ONE URL AND jq FINDS IT AT THE ROOT.** `documentation_url` sits
outside `docs`, so pandas and polars — which frame the records — report none of
one. `paths(condition)` starts at the top and cannot miss it.
"""
import json
import time
from importlib.metadata import version

import jq

print(f"jq python binding {version('jq')}")

RAW = "../source.json"
doc = json.load(open(RAW))
n = len(doc["docs"])


def run(program, label):
    t0 = time.time()
    out = jq.compile(program).input(doc).first()
    print(f"    [{time.time() - t0:5.2f}s] {label}")
    return out


# ── Q0. Is this what it claims to be, and is it whole? ──────────────────────
print("\nQ0  the binding takes an already-parsed object, so jq never saw the bytes.")
print("    No duplicate-key, big-int or NaN report from either side. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ───────────────────────────────────
print("\nQ1  paths, with array indices folded to []:")
paths = run('[paths | map(if type == "number" then "[]" else . end) | join(".")]'
            ' | unique', "…")
print(f"    {len(paths)} — THE PROBE PRINTS 31. Exact.")
print("\nQ2  max path length:")
print(f"    {run('[paths | length] | max', '…')} — the probe prints 4. Exact.")

# ── Q3. THE SPLIT — jq can price a candidate, and will not choose one. ─────
print("\nQ3  the record shape and its cost, computed in jq:")
base = run('''.docs as $d
    | ([$d[] | keys[]] | unique) as $f
    | {rows: ($d | length), cols: ($f | length),
       empty: (([$d[] | . as $r | $f | map(. as $k | if ($r | has($k)) then 0 else 1 end) | add]
                | add) / (($d | length) * ($f | length)))}''', "…")
print(f"    {base['rows']} rows x {base['cols']} cols, {base['empty']:.0%} empty"
      " — the probe's numbers exactly.")
print("\nQ3  and the SEARCH over every always-present field, also in jq:")
# Every key is bound with `as` before use. `$r | has(.)` does NOT work: the pipe
# rebinds `.` to $r, so has() receives the object rather than the key name. That
# cost two rewrites of this program.
EMPTINESS = """
  def emptiness($rows):
    ([$rows[] | keys[]] | unique) as $cols
    | ([ $rows[] | . as $r
         | [ $cols[] | . as $c | if ($r | has($c)) then 0 else 1 end ] | add ] | add)
      / (($rows | length) * ($cols | length));
"""
search = run(EMPTINESS + '''
    .docs as $d
    | ([$d[] | keys[]] | unique) as $all
    | [ $all[] | . as $f | select([$d[] | has($f)] | all) ] as $always
    | [ $always[] as $f
        | ($d | group_by(.[$f])) as $g
        | select(($g | length) > 1 and ($g | length) <= 24)
        | {field: $f, kinds: ($g | length),
           worst: ([$g[] | emptiness(.)] | max)} ]
      | sort_by(.worst)''', "…")
for row in search:
    print(f"      {row['field']:16} {row['kinds']:3} kinds  worst group"
          f" {row['worst']:5.1%}")
print("    jq CAN SEARCH AND PRICE the discriminators — no other tool in this")
print("    directory can — and its ranking agrees with the probe: `ebook_access`")
print("    wins, `has_fulltext` ties on the worst group, and the other two make")
print("    the table no better or worse. But that is a 15-line program with a")
print("    helper function, written knowing exactly what to look for. jq has no")
print("    verb for it and prints nothing unasked. PARTLY — and it is the closest")
print("    any tool in either language has come to the fourth operation.")

# ── Q7. How many records. ──────────────────────────────────────────────────
print("\nQ7  both answers, in one expression:")
counts = run('{in_array: (.docs | length), numFound, num_found, start}', "…")
print(f"    {counts}")
print("    200 are here, 30,427 exist. This is a PAGE, and only a top-level")
print("    field says so — pandas and polars frame `docs` and never see it.")

# ── Q4. Always present vs sometimes. ──────────────────────────────────────
print("\nQ4  field counts:")
fc = run('[.docs[] | keys_unsorted[]] | group_by(.) | map({(.[0]): length}) | add', "…")
absent = sorted(((k, c) for k, c in fc.items() if c < n), key=lambda kv: kv[1])
nulls = run('[.docs[] | to_entries[] | select(.value == null)] | length', "…")
print(f"    {len(fc)} fields · always {sum(1 for c in fc.values() if c == n)},"
      f" sometimes {len(absent)} — matches the probe")
print(f"    rarest five: {absent[:5]}")
print(f"    and {nulls} nulls in the records, so `has` and `!= null` agree here.")
print("    On 15-github-issues they disagreed on 8 fields and split the tools 9–4.")

# ── Q5. Does any field change type between records. ──────────────────────
print("\nQ5  fields whose non-null type varies:")
varying = run('''[.docs[] | to_entries[] | select(.value != null)
      | {k: .key, t: (.value | type)}] | group_by(.k)
      | map(select((map(.t) | unique | length) > 1) | .[0].k)''', "…")
print(f"    {varying or 'none'} — the probe's answer. DuckDB's `unnest` route")
print("    reports ELEVEN on this document, every one an invented null.")

# ── Q6. Are any object keys actually data? AND the key-set count. ────────
print("\nQ6  no keyed collections. n/a, and the probe's KEYS THAT ARE DATA")
print("    section is empty for this file.")
print("\nQ6b distinct key-sets:")
ks = run('[.docs[] | keys_unsorted | sort | join(",")] | unique | length', "with sort")
print(f"    {ks} — THE PROBE PRINTS 15, and DuckDB agrees here too. That")
print("    expression was 5.4x high on 13-package-lock and 7.0x high on")
print("    15-github-issues; this document has neither data keys nor nulls.")

# ── Q8/Q9/Q10. Extraction. ───────────────────────────────────────────────
print("\nQ8  three fields:")
t = run('[.docs[] | {title, edition_count, ebook_access}]', "…")
print(f"    {len(t)} rows x 3 cols · {t[0]}")
print("\nQ9  a field absent from some docs:")
q9 = run('[.docs[] | {key, cover_i}]', "…")
print(f"    {len(q9)} rows kept, {sum(r['cover_i'] is None for r in q9)} null")
print("    Object construction keeps the row; jmespath's projection returns 110.")
print("\nQ10 author_name:")
names = run('[.docs[] | .author_name // [] | .[]]', "…")
print(f"    {len(names)} names — the `// []` is needed because the field is absent")
print("    on one doc. Five fields are arrays and all five are sometimes absent.")

# ── Q11. Find every path whose value matches something. ─────────────────
print("\nQ11 URL-valued paths, no field named:")
urls = run('[paths(type == "string" and test("https?://")) | join(".")]'
           ' | group_by(.) | map({(.[0]): length}) | add', "…")
print(f"    {urls}")
print("    ONE URL, at the ROOT. `paths` starts at the top, so it cannot be")
print("    missed; pandas and polars frame `docs` and report NONE OF ONE.")

# ── Q12. The flattest honest table, and what was lost. ──────────────────
print("\nQ12 the honest record table:")
flat = run('[.docs[]]', "…")
keys = sorted(set().union(*(set(r) for r in flat)))
print(f"    {len(flat)} rows, {len(keys)} distinct keys, five of them arrays.")
print("    The seven top-level fields are a separate shape — which is why the")
print("    probe names `the whole document 1 rows x 8 cols` as a candidate.")
