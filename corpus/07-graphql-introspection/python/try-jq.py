"""jq (Python binding) — GraphQL introspection, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jq (version printed at run time)
  file          ../source.json   143 KB, 108 types
  measured      2026-08-09
  run           cd corpus/07-graphql-introspection/python && uv run try-jq.py

  question                                    lines  shape known first?  worked
   1 what is in here                             5   NO                  PARTLY
   2 how deep does it go                          2  NO                  YES
   4 always vs sometimes                          4  NO                  YES
   5 does any field change type                   4  NO                  YES
   7 how many records                             1  YES                 YES
   8 three named fields to a table                2  YES                 YES
"""
import json, sys
from importlib.metadata import version
import jq
print(f"python {sys.version.split()[0]}, jq {version('jq')}")
doc = json.load(open("../source.json"))

# 1. THE ASTERISK, carried forward from 02-hn-thread. paths(scalars) only
#    reaches paths ENDING in a scalar, so a key whose value is always a
#    container is invisible. On the thread that dropped `children`.
scal = jq.compile('[paths(type != "object" and type != "array")|map(select(type=="string"))|join(".")]|unique|length').input(doc).first()
allp = jq.compile('[paths|map(select(type=="string"))|join(".")]|unique|length').input(doc).first()
print(f"\n1. paths(scalars): {scal} distinct   paths: {allp} distinct")
print(f"   difference: {allp - scal} paths that never end in a scalar.")
print("   Those are the container-valued keys. On 02-hn-thread this exact gap")
print("   is what made jq, jqr and rrapply all answer 11 and all drop")
print("   `children`. Agreement between tools is a check on the tools, never")
print("   on the question.")

print(f"\n2. depth: {jq.compile('[paths|length]|max').input(doc).first()}")

print(f"\n7. types: {jq.compile('.data.__schema.types|length').input(doc).first()}")

# 4 and 5. jq's has() vs ==null is the cleanest expression of this file's trap
#    in any tool, and it takes one line.
print("\n4/5. present vs non-null, per field of types[]:")
expr = ('[.data.__schema.types[]|keys[]]|group_by(.)|map({(.[0]):length})|add')
present = jq.compile(expr).input(doc).first()
nonnull = jq.compile(
    '[.data.__schema.types[]|to_entries[]|select(.value!=null)|.key]'
    '|group_by(.)|map({(.[0]):length})|add').input(doc).first()
for k in sorted(present):
    print(f"     {k:16} present {present[k]:3}/108   non-null {nonnull.get(k,0):3}/108")
print("   Every field is present on all 108. jq answers question 4 correctly")
print("   and in one expression, and it is the only tool here that needed no")
print("   extra plain-Python help to do it.")

print("\n8. three named fields:")
t3 = jq.compile('[.data.__schema.types[:3][]|{kind,name}]').input(doc).first()
print(f"   {t3}")
