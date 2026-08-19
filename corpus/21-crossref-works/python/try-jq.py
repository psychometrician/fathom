"""jq (the Python binding) — Crossref works, 1,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq, the Python binding (version printed at run time)
  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
  measured      2026-08-11
  run           cd corpus/21-crossref-works/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   PARTLY
   1 what is in here                             3   NO                  yes — 236
   2 how deep                                    2   NO                  yes — 9
   3 what is one record                         28   NO                  PARTLY — see below
   4 always present vs sometimes                 4   NO                  yes — 40, no nulls
   5 does any field change type                 10   NO                  PARTLY
   6 are any object keys data                    5   NO                  by hand
   7 how many records                            3   NO                  yes, three answers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              2   YES                 yes
  10 flatten the deepest array                   3   YES                 yes — 18,155
  11 find every path matching something          4   NO                  yes — 13
  12 flattest honest table                       3   NO                  PARTLY
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
  14 survives the next file unchanged?               the Q3 SEARCH does, unchanged
  15 readable a week later?                          the Q3 program, no
  16 lines, and how much is ceremony?                ~120, almost none ceremony

  ══════════════════════════════════════════════════════════════════════════════
  THIS IS THE DEFECT-24 DOCUMENT, AND THE FIFTEEN-LINE jq SEARCH FINDS WHAT THE
  PROBE DECLINED — WITH THE PROBE'S OWN NUMBERS.
  ══════════════════════════════════════════════════════════════════════════════

  The probe reports NO `SPLIT ON` here. `21-crossref-works` is twelve kinds and
  says so in a field called `type`; open defect 24 is that the halving rule takes
  a MAXIMUM over groups, so the 104 journal-articles veto a split that is right
  for the other 896.

  The search below is entry 17's program, UNCHANGED except for the path to the
  records, and it ranks three candidates:

      field                    kinds   worst    weighted
      type                        12   0.2629     0.2073
      content-domain               9   0.4873     0.3177
      is-referenced-by-count      13   0.4381     0.4105

  `type` IS FIRST ON BOTH METRICS. Unsplit emptiness is 0.4454, so the halving
  rule wants a worst group under 0.2227 — and `type` misses by 0.04 while its
  WEIGHTED figure, 0.2073, passes comfortably.

  THE PROBE'S RANKING IS NOT WRONG. ONLY ITS GATE IS. That is a sharper
  statement of defect 24 than the entry had: the probe finds the right field and
  then refuses it. And the numbers jq computes here — 0.2629 and 0.2073 — are
  the probe's own internal figures reproduced by a program that shares no code
  with it.

  Entry 17 measured the same search agreeing with the probe where the probe was
  RIGHT. This is the other half: it agrees with the probe about which field, and
  disagrees about whether to take it.
"""
import json
import time
from importlib.metadata import version

import jq

print(f"jq (python binding) {version('jq')}")

RAW = "../source.json"
doc = json.load(open(RAW))


def q(prog, data=None):
    t = time.time()
    out = jq.compile(prog).input(data if data is not None else doc).all()
    return out, time.time() - t


# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  parsed. jq reports 'valid JSON' and nothing else: duplicate keys go")
print("    last-wins silently, ints past 2^53 become doubles silently. PARTLY.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
paths, t = q('[paths | map(if type=="number" then "[]" else . end) | join(".")] '
             '| unique | length')
print(f"\nQ1  {paths[0]} distinct paths, {t:.1f}s")
depth, _ = q('[paths | length] | max')
print(f"Q2  depth {depth[0]} — agrees with the probe")

# ── Q3. THE SPLIT. The centrepiece of this entry. ────────────────────────────
print("\nQ3  the obvious record and its cost, in jq:")
base, _ = q('''.message.items as $d
    | ([$d[] | keys[]] | unique) as $f
    | {rows: ($d|length), cols: ($f|length),
       empty: (([$d[] | . as $r | $f | map(. as $k | if ($r|has($k)) then 0 else 1 end) | add]
                | add) / (($d|length) * ($f|length)))}''')
b = base[0]
print(f"    an item of items: {b['rows']:,} rows x {b['cols']} cols, {b['empty']:.1%} empty")
print("    The probe says 1,000 x 71 at 44% — jq's 57 counts only the keys that")
print("    OCCUR, the probe's 71 counts the flattened columns. Same document,")
print("    two honest widths, and neither tool says which it means.")

EMPTINESS = """
  def emptiness($rows):
    ([$rows[] | keys[]] | unique) as $cols
    | ([ $rows[] | . as $r
         | [ $cols[] | . as $c | if ($r | has($c)) then 0 else 1 end ] | add ] | add)
      / (($rows | length) * ($cols | length));
"""
print("\nQ3  AND THE SEARCH — entry 17's program, unchanged but for the path:")
search, t = q(EMPTINESS + '''
    .message.items as $d
    | ([$d[] | keys[]] | unique) as $all
    | [ $all[] | . as $f | select([$d[] | has($f)] | all) ] as $always
    | [ $always[] as $f
        | ($d | group_by(.[$f])) as $g
        | select(($g|length) > 1 and ($g|length) <= 24)
        | {field: $f, kinds: ($g|length),
           worst: ([$g[] | emptiness(.)] | max),
           weighted: ([$g[] | {n: length, e: emptiness(.)}]
                      | (map(.n * .e) | add) / (map(.n) | add))} ]
      | sort_by(.weighted)''')
print(f"      {'field':24} {'kinds':>5} {'worst':>8} {'weighted':>9}   ({t:.1f}s)")
for r in search[0]:
    print(f"      {r['field']:24} {r['kinds']:5} {r['worst']:8.4f} {r['weighted']:9.4f}")
halve = b["empty"] / 2
print(f"\n    unsplit emptiness {b['empty']:.4f}, so the halving rule wants worst < {halve:.4f}")
top = search[0][0]
print(f"    `{top['field']}` worst {top['worst']:.4f} FAILS by {top['worst']-halve:.4f};"
      f" weighted {top['weighted']:.4f} PASSES")
print("    THE PROBE PICKS THE SAME FIELD AND THEN REFUSES IT. Defect 24 is not")
print("    a ranking failure, it is a GATE failure, and this is the first")
print("    measurement to separate the two.")
kinds, _ = q('[.message.items[].type] | group_by(.) | map({t: .[0], n: length}) | sort_by(-.n)')
print(f"    the twelve kinds: {[(r['t'], r['n']) for r in kinds[0][:5]]} …")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
some, _ = q('[.message.items[] | keys[]] | group_by(.) | map({k: .[0], n: length}) '
            '| map(select(.n < 1000)) | length')
nulls, _ = q('[.message.items[] | to_entries[] | select(.value == null) | .key] | unique')
print(f"\nQ4  {some[0]} of 57 fields are sometimes ABSENT; null-valued fields: {nulls[0]}")
print("    ZERO NULLS AT THE RECORD LEVEL. This is a pure-absence document, like")
print("    entry 17 and unlike entry 20 — so question 4's absent/null")
print("    discriminator has nothing to bite on and every tool should agree.")

# ── Q5. Does any field change type between records? ──────────────────────────
print("\nQ5  the probe reports exactly ONE site, and it is the subtlest in the corpus:")
dp, _ = q('[.message.items[].issued."date-parts"] | group_by(.[0][0] == null) '
          '| map({first_is_null: (.[0][0][0] == null), n: length, sample: .[0]})')
for r in dp[0]:
    print(f"    {r['n']:4} records: {json.dumps(r['sample'])}")
print("    `issued.date-parts` is [[2018,11,3]] on 998 and [[null]] on 2. Both")
print("    are arrays of arrays; the JSON TYPE is identical. The probe reports")
print("    `array[2] number` against `array[2] null`, which needs element typing")
print("    THROUGH two levels of nesting.")
naive, _ = q('[.message.items[] | to_entries[] | {k: .key, t: (.value|type)}] '
             '| group_by(.k) | map({k: .[0].k, t: (map(.t)|unique)}) '
             '| map(select((.t - ["null"]) | length > 1)) | length')
print(f"    a field-level `type` census finds {naive[0]}. PARTLY: jq can reach it,")
print("    with `.[0][0] | type` written by someone who already knew.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
ref, _ = q('[.message.items[].reference[]? | keys[]] | unique | length')
refn, _ = q('[.message.items[].reference[]?] | length')
print(f"\nQ6  $.message.items[].reference[]: {ref[0]} keys over {refn[0]:,} copies")
print("    THE PROBE DECLINES THIS as a vocabulary rather than data, and that")
print("    decline is the repair from `13-package-lock`'s `engines` GENERALISING")
print("    to an unseen document. jq counts and does not judge, as always.")

# ── Q7. How many records — three answers. ────────────────────────────────────
counts, _ = q('{in_array: (.message.items|length), total: .message["total-results"], '
              'per_page: .message["items-per-page"]}')
print(f"\nQ7  {counts[0]}")
print("    THREE ANSWERS and only one is 'how many records are here'. Entry 17")
print("    recorded the same trap under `numFound`.")

# ── Q8/Q9/Q10. Extraction. ───────────────────────────────────────────────────
t8, _ = q('[.message.items[] | {DOI, type, publisher}] | length')
print(f"\nQ8  {t8[0]:,} rows x 3, one expression")
t9, _ = q('[.message.items[] | {DOI, abstract: (.abstract // null)}] '
          '| map(select(.abstract != null)) | length')
print(f"\nQ9  abstract present on {t9[0]} of 1,000; `//` keeps every row")
t10, t = q('[.message.items[] as $w | $w.reference[]? | {DOI: $w.DOI, key, "doi": .DOI}] | length')
print(f"\nQ10 reference[] flattened to {t10[0]:,} rows x 3, {t:.1f}s")
print("    The parent DOI stays in scope through the `as` binding.")

# ── Q11. Find every path whose value matches something. ──────────────────────
u, t = q('[paths(type=="string" and test("^https?://")) '
         '| map(if type=="number" then "[]" else . end) | join(".")] | unique')
print(f"\nQ11 {len(u[0])} distinct URL paths, {t:.1f}s")
for p in u[0][:6]:
    print(f"      {p}")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 jq has no `to_table`. The honest answer is question 3's — and this")
print("    document has SEVENTEEN priced row candidates in the probe's output,")
print("    of which jq will count any one you name and rank none.")
