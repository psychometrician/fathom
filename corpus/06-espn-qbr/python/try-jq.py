"""jq — ESPN quarterback rating, 2019

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   176 KB, 28 athletes
  measured      2026-08-09
  run           cd corpus/06-espn-qbr/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             1   no                  YES
   2 how deep                                    1   no                  YES
   7 how many records                            1   YES                 YES
   7a related by position, not nesting           6   no                  PARTLY
"""
import json, sys
from importlib.metadata import version
import jq
print(f"python {sys.version.split()[0]}, jq {version('jq')}")
doc = json.load(open("../source.json"))
ask = lambda e: jq.compile(e).input_value(doc).first()

print(f"\n7. athletes: {ask('.athletes|length')}")
print(f"1. distinct field names: "
      f"{ask('[paths(type != \"object\" and type != \"array\")|map(select(type==\"string\"))|last]|unique|length')}")
print(f"2. depth: {ask('[paths|length]|max')}   (axes.py grades 7)")

lens = ask('''
  [paths as $p | getpath($p) | select(type=="array" and length==10) | $p]
  | map(join(".")) | unique
''')
print(f"\n7a. every path holding an array of exactly 10, found by jq itself:")
for p in lens[:8]:
    print(f"     {p}")
print(f"     ... {max(0, len(lens) - 8)} more, {len(lens)} in total")
print("""
    jq CAN enumerate them — `paths | select(length==10)` is one expression and
    needs no prior knowledge. It is the only tool in the comparison that finds
    the aligned arrays without being told they exist.

    AND IT REPORTS 61 OF THEM WHERE THERE ARE SIX. `athletes.1...totals` and
    `athletes.10...totals` are the same structural path seen twice, and with 28
    athletes carrying two arrays each that is 56 of the 61. The distinct answer
    is `athletes[].categories[].totals`, `...ranks`, and the four under
    `categories[]`. This is the O(data) failure arriving on the one question jq
    answers better than anything else here: the enumeration is right and its
    length is proportional to the number of athletes rather than to the
    structure. Folding sibling instances is what would fix it, which is
    VERDICT.md's first operation.

    What it cannot do is say which of them holds the NAMES. `labels`, `names`,
    `displayNames` and `glossary[].abbreviation` are all ten strings, and only
    `labels` is in the order `totals` uses. jq surfaces the candidates and the
    choice between them is exactly the trap.""")
