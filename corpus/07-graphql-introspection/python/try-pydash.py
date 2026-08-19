"""pydash — GraphQL introspection, 2026

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   143 KB, 108 types
  measured      2026-08-09
  run           cd corpus/07-graphql-introspection/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   1 what is in here                             6   NO                  YES
   2 how deep does it go                          4  NO                  YES
   4 always vs sometimes                          4  YES                 YES
   7 how many records                             1  YES                 YES
   8 three named fields to a table                3  YES                 YES
"""
import json, sys
from importlib.metadata import version
import pydash
print(f"python {sys.version.split()[0]}, pydash {version('pydash')}")
doc = json.load(open("../source.json"))

# 1. pydash counts KEY NAMES, which is why it answered 13 on the hn thread
#    where jq's paths(scalars) answered 11. Walking to scalars drops any key
#    whose value is a container, and on this file that would drop `fields`.
def paths(o, p=""):
    if isinstance(o, dict):
        for k, v in o.items():
            yield f"{p}.{k}"
            yield from paths(v, f"{p}.{k}")
    elif isinstance(o, list):
        for v in o:
            yield from paths(v, p + "[]")

allp = list(paths(doc))
distinct = sorted(set(allp))
print(f"\n1. {len(allp)} paths, {len(distinct)} distinct")
print(f"   listing them costs {len(str(distinct))} chars for a 143,376-byte file")
print("   Compare npm, where the same count was 3,126 distinct paths for a truth")
print("   of about 40 fields. Here the number is small, and the reason is that")
print("   this document has NO keys-as-data. The listing is honest for once.")

print("\n2. depth:")
def depth(o):
    if isinstance(o, dict) and o:
        return 1 + max(depth(v) for v in o.values())
    if isinstance(o, list) and o:
        return 1 + max(depth(v) for v in o)
    return 0
print(f"   {depth(doc)} levels. The recursion is `type.ofType.ofType…`, which")
print("   is how GraphQL spells a non-null list of a non-null String, so depth")
print("   here is a property of the TYPE SYSTEM rather than of the data.")

types = pydash.get(doc, "data.__schema.types")
print(f"\n7. types: {len(types)}")

print("\n4. pydash.get with a default, over all 108:")
for f in ["fields", "enumValues", "possibleTypes"]:
    n = sum(1 for t in types if pydash.get(t, f) is not None)
    k = sum(1 for t in types if f in t)
    print(f"     {f:16} key present {k:3}/108, non-null {n:3}/108")
print("   pydash.get() returns None for BOTH, so the two columns above cannot")
print("   be produced by pydash alone — the `in` test is plain Python.")

print("\n8. three named fields:")
for t in types[:3]:
    print(f"     {pydash.get(t,'kind'):14} {pydash.get(t,'name'):22} "
          f"{str(pydash.get(t,'description'))[:30]}")
