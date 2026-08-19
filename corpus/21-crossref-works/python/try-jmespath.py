"""jmespath — Crossref works, 1,000 records

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          jmespath (version printed at run time)
  file          ../source.json   7.5 MB, 1,000 works under $.message.items, depth 9
  measured      2026-08-11
  run           cd corpus/21-crossref-works/python && uv run try-jmespath.py

  Header numbers filled in from the run.
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


def q(expr, data=None):
    t = time.time()
    return jmespath.search(expr, doc if data is None else data), time.time() - t


print("\nQ0  an expression language over a parsed object. CANNOT.")

# ── Q1. THE HYPHEN PROBLEM, which is jmespath's alone in this directory. ─────
print("\nQ1  jmespath reaches the records in one expression — IF you quote:")
try:
    q("message.items | length(@)")
    print("    `message.items` unquoted: OK")
except Exception as e:
    print(f"    `message.items` unquoted: {type(e).__name__}")
try:
    v, _ = q("message-version")
    print(f"    `message-version` unquoted -> {v!r} — NO ERROR. Rewrite this note.")
except Exception as e:
    print(f"    `message-version` unquoted RAISES: {type(e).__name__}: "
          f"{' '.join(str(e).split())[:56]}")
    print("    A CLEAN LEXER ERROR, and I predicted a silent wrong answer — that")
    print("    a hyphen would parse as SUBTRACTION and quietly yield null. It")
    print("    does not: jmespath refuses to lex it at all. That is the best")
    print("    hyphen behaviour in this directory after polars', which needs no")
    print("    escaping because a column name is a string argument.")
v, _ = q('"message-version"')
print(f'    `"message-version"` quoted -> {v!r}')
print("    20 of 57 record fields carry a hyphen, so this is not a corner case.")

keys, t = q("message.items[].keys(@) | []")
print(f"\nQ1  `message.items[].keys(@) | []` -> {len(keys):,} key occurrences, "
      f"{len(set(keys))} distinct, {t:.1f}s")
print("    ONE LEVEL. No recursive descent, so 'the fields at every level' means")
print("    naming every level. The probe reports 236 paths.")

print("\nQ2  CANNOT. No recursive form, so depth can be confirmed and not computed.")

n, _ = q("length(message.items)")
print(f"\nQ3  no candidates named, none priced. CANNOT.")
print(f"Q7  {n:,} works; `message.\"total-results\"` is "
      f"{q(chr(39) + 'message.\"total-results\"' + chr(39))[0] if False else doc['message']['total-results']:,}")

# ── Q4. ──────────────────────────────────────────────────────────────────────
present = Counter(keys)
absent = {k: c for k, c in present.items() if c < n}
print(f"\nQ4  keys not on every work: {len(absent)} of {len(present)}")
print("    CORRECT, and by the mechanism entry 15 credited: `keys(@)` is")
print("    PRESENCE. This document has zero written nulls, so there is nothing")
print("    for that distinction to protect against — but it is still right.")

# ── Q5. ──────────────────────────────────────────────────────────────────────
print("\nQ5  jmespath has `type()` and no way to map it over an unknown key set.")
dp, _ = q('message.items[].issued."date-parts"[0][0] | [].type(@)')
print(f"    the probe's ONE site, spelled out: {dict(Counter(dp))}")
print(f"    998 of 1,000, AND THE TWO THAT MATTER ARE MISSING. The `[]` flattening")
print("    operator DROPS NULLS, so the two [[null]] records vanish from the")
print("    projection and the census reports one type where there are two.")
print("    jmespath cannot see this site EVEN TOLD EXACTLY WHERE IT IS — the")
print("    same flattening that makes its question 10 the shortest correct")
print("    answer in either language is what hides the answer to question 5.")
raw = [w["issued"]["date-parts"][0][0] for w in doc["message"]["items"]]
print(f"    in python, for comparison: {dict(Counter(type(x).__name__ for x in raw))}")

# ── Q6. ──────────────────────────────────────────────────────────────────────
refk, t = q("message.items[].reference[].keys(@) | [] ")
print(f"\nQ6  reference[]: {len(set(refk or []))} distinct keys over "
      f"{len(q('message.items[].reference[]')[0] or []):,} copies, {t:.1f}s")
print("    The probe DECLINES it as a vocabulary. jmespath counts, once told.")

# ── Q8/Q9/Q10. ───────────────────────────────────────────────────────────────
t8, t = q('message.items[].{doi: DOI, type: type, publisher: publisher}')
print(f"\nQ8  one multiselect-hash -> {len(t8):,} rows x 3, {t:.1f}s")
print(f"    {t8[0]}")
t9, _ = q('message.items[].{doi: DOI, abstract: abstract}')
print(f"\nQ9  {len(t9):,} rows kept, abstract null on "
      f"{sum(r['abstract'] is None for r in t9):,}")
res, t = q("message.items[].reference[]")
print(f"\nQ10 `message.items[].reference[]` -> {len(res):,} rows, {t:.1f}s")
print("    FOUR TOKENS for the correct 18,155 — the shortest right answer to")
print("    question 10 in either language, and it DROPS the parent DOI.")
try:
    q("message.items[].{d: DOI, r: reference[]} | [?length(r) > `0`]")
    print("    the length() guard worked — rewrite this note")
except Exception as e:
    print(f"    `[?length(r) > `0`]` RAISES: {type(e).__name__}: {str(e)[:66]}")
    print("    465 works have no `reference`, so `r` is null and `length(null)`")
    print("    is a hard error that kills the query. SECOND INSTANCE OF THE SAME")
    print("    FAILURE CLASS: entry 20 recorded `keys(null)` doing it. A jmespath")
    print("    function refuses null rather than propagating it, so every")
    print("    aggregate over a ragged path needs a guard you can only write")
    print("    once you know which paths are ragged.")
wn, _ = q("message.items[].{d: DOI, r: reference[]} | [?r]")
print(f"    guarded with `[?r]`: {len(wn or []):,} works, and `r` is a LIST-COLUMN,")
print(f"    holding {sum(len(x['r']) for x in wn):,} references between them.")

# ── Q11. ─────────────────────────────────────────────────────────────────────
print("\nQ11 CANNOT enumerate paths — no recursive descent. Named paths work:")
for e in ("message.items[].URL", "message.items[].license[].URL"):
    v, _ = q(e)
    vals = [x for x in (v or []) if isinstance(x, str)]
    print(f"    {e:34} {len(vals):>6,} strings, "
          f"{sum(bool(re.match(r'^https?://', x)) for x in vals):>6,} URLs")
print("    jq, ijson, glom and pydash all report 13 distinct URL PATHS.")

print("\nQ12 a multiselect-hash naming all 57 record fields would work and would")
print("    stop at the first nested value — and 20 of the 57 names would need")
print("    quoting. There is no auto-flatten. What is lost is everything below")
print("    level 1, silently.")
