"""jq (Python binding) — Open-Meteo hourly forecast, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   12 KB, 336 hours x 5 variables, stored COLUMN-WISE
  measured      2026-08-09
  run           cd corpus/08-open-meteo/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             3   NO                  YES
   2 how deep does it go                          1  NO                  YES
   7 how many records                             1  YES                 YES
  7a related by position, not nesting             5  NO                  YES
  12 flattest honest table                        5  YES                 YES
"""
import json, sys
from importlib.metadata import version
import jq
print(f"python {sys.version.split()[0]}, jq {version('jq')}")
doc = json.load(open("../source.json"))

n = jq.compile('[paths|map(select(type=="string"))|join(".")]|unique|length').input(doc).first()
print(f"\n1. {n} distinct paths")
print(f"2. depth: {jq.compile('[paths|length]|max').input(doc).first()}")
print(f"\n7. hours: {jq.compile('.hourly.time|length').input(doc).first()}")

# 7a. THE ONE QUESTION THAT MATTERS ON THIS FILE, and jq answers it in one
#     expression without being told what the document is. Note the question is
#     marked CIRCULAR in QUESTIONS.md — added the same day the probe gained the
#     feature — so this is not scored as a win against a question that predates
#     the design. It is recorded because rule 3 requires every file to be asked.
expr = '[paths(type=="array") as $p|{path:($p|join(".")),len:(getpath($p)|length)}]'
arrays = jq.compile(expr).input(doc).first()
print("\n7a. every array and its length, one expression, no prior knowledge:")
for a in arrays:
    print(f"     {a['path']:32} {a['len']}")
print("   Five arrays, all 336, all under `hourly`. jq lays the evidence out")
print("   and draws no conclusion — which is the honest half of what a reader")
print("   needs, and not the half that says 'this file is 336 rows'.")

# 12. jq CAN transpose, and this is the shortest correct expression in any of
#     the eight Python tools.
out = jq.compile(
    '.hourly as $h|($h|keys_unsorted) as $k'
    '|[range(0;($h[$k[0]]|length))|. as $i|reduce $k[] as $c ({};.[$c]=$h[$c][$i])]'
).input(doc).first()
print(f"\n12. transposed: {len(out)} rows x {len(out[0])} cols")
for r in out[:2]:
    print(f"      {r}")
print("    One expression, correct, and it names `.hourly` — so it needed")
print("    question 3 answered before it could be written.")
