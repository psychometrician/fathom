"""pydash — an npm lockfile, 1,657 packages keyed by install path

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          pydash (version printed at run time)
  file          ../source.json   759 KB, 1,657 packages, depth 5
  measured      2026-08-11
  run           cd corpus/13-package-lock/python && uv run try-pydash.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                             8   NO                  YES — in its own words
   2 how deep                                    3   NO                  YES — in its own words
   3 what is one record                          3   YES                 CANNOT
   4 always present vs sometimes                 5   YES                 YES — no Python needed
   5 does any field change type                  5   YES                 YES
   6 are any object keys data                    9   -                   NO — and 33 keys FAIL SILENTLY
   7 how many records                            1   YES                 yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              2   YES                 YES — keeps the rows
  10 flatten the deepest array                   4   YES                 PARTLY
  11 find every path matching something          7   NO                  YES — but unfolded
  12 flattest honest table                       3   YES                 yes
  13 needed the shape in advance?                    NO for 1, 2, 11
  14 survives the next file unchanged?               Q1/Q2/Q11 yes
  15 readable a week later?                          NO — two silent traps
  16 lines, and how much is ceremony?                ~130, and the deep walks are 15

**pydash IS THE ONLY ONE OF THE THREE PATH LANGUAGES THAT FAILS SILENTLY ON THIS
DOCUMENT'S KEYS, AND IT IS THE WORST OF THE THREE OUTCOMES.** 33 package keys
contain a dot, because npm package names do:

    pydash.get(doc, "packages.node_modules/@nodelib/fs.scandir")   ->  None

**None. Not an error, not a warning — the same value a genuinely absent key
returns.** glom raises `PathAccessError` on the identical spelling and jmespath
reaches it with a quoted identifier. `pydash.get(doc, ["packages", key])` — a
LIST path rather than a parsed string — works, and you must know the keys
contain dots before you know to write it.

**On `14-nyc-311` pydash took the awkward keys unquoted and jmespath raised.
Here it is pydash that breaks and jmespath that works.** Two documents, opposite
verdicts, and the failure mode that matters is not which tool broke but that
this one broke *by returning a plausible value*.

**THE MUTATION TRAP FROM ENTRY 14 IS STILL HERE AND THE FIX TRANSFERRED.**
`map_values_deep` is a mapper, not a walker: a survey callback that returns
`None` overwrites every leaf. This file returns `value` from both callbacks, and
proves the document survived rather than assuming it.

**WHERE IT WINS IS QUESTION 11 — AND THE WIN COMES OUT WRONG-SHAPED.**
`map_values_deep` finds every URL without a field being named, which glom and
jmespath cannot do. But the paths it reports are the RAW ones, so the answer is
**about 1,700 lines, one per package**, where the folded truth is five. Being
able to enumerate paths is not the same as being able to describe a document,
and this file is where those two come apart.
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
packages = doc["packages"]
n = len(packages)

KEYED = ("dependencies", "devDependencies", "optionalDependencies",
         "peerDependencies", "peerDependenciesMeta", "bin")


def fold(path):
    """Raw path segments -> a path with the keyed collections folded to <key>."""
    out, i = ["$"], 0
    while i < len(path):
        seg = path[i]
        if isinstance(seg, int):
            out.append("[]")
            i += 1
            continue
        out.append(f".{seg}")
        if seg == "packages" or seg in KEYED:
            if i + 1 < len(path):
                out.append(".<key>")
                i += 1
        i += 1
    return "".join(out)


# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  pydash is a collection library; json.load parsed and said nothing.")
print("    No health vocabulary on either side. CANNOT.")

# ── Q1/Q2. What is in here, and how deep. ────────────────────────────────────
raw_paths, folded_paths, maxlen = set(), set(), 0


def survey(value, path):
    global maxlen
    maxlen = max(maxlen, len(path))
    raw_paths.add("$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path))
    folded_paths.add(fold(path))
    return value            # REQUIRED — see the header. Entry 14 learned this.


t0 = time.time()
pydash.map_values_deep(doc, survey)
walk_s = time.time() - t0
print(f"\nQ1  map_values_deep visited every leaf in {walk_s:.1f}s")
print(f"    {len(raw_paths):,} distinct RAW leaf paths")
print(f"    {len(folded_paths)} once the keyed collections fold to <key>")
print(f"    A RATIO OF {len(raw_paths) // len(folded_paths)} TO 1. The raw list is not a")
print("    description of this document; it is the document's keys printed as")
print("    paths. pydash gives the walk and no way to fold it.")
print(f"Q2  deepest leaf path is {maxlen} segments; the probe prints 5 levels deep.")
print(f"    document intact after the walk: doc['lockfileVersion'] = "
      f"{doc['lockfileVersion']}")

# ── Q3/Q7. What is one record, and how many. ─────────────────────────────────
print("\nQ3  pydash names no row candidates and prices none. The probe names")
print("    EIGHT with costs, including 1,657 x 1394 at 99% empty. CANNOT.")
print(f"Q7  {pydash.size(packages):,} packages")

# ── Q4. Always present vs sometimes — NO collections.Counter. ────────────────
keys = pydash.flatten([list(v) for v in packages.values()])
counts = pydash.count_by(keys)
always = [k for k, c in counts.items() if c == n]
some = sorted(((k, c) for k, c in counts.items() if c < n), key=lambda kv: kv[1])
print(f"\nQ4  {len(keys):,} key occurrences over {len(counts)} names")
print(f"Q4  always {len(always)} — {always}")
print(f"Q4  sometimes {len(some)}, rarest five: {some[:5]}")
print("    `flatten` + `count_by` are pydash's own; glom and jmespath both")
print("    borrow collections.Counter for this line.")

# ── Q5. Does any field change type between records? ──────────────────────────
kinds = {}
for v in packages.values():
    for k, x in v.items():
        kinds.setdefault(k, {})
        kinds[k][type(x).__name__] = kinds[k].get(type(x).__name__, 0) + 1
varying = {k: v for k, v in kinds.items() if len(v) > 1}
print(f"\nQ5  fields holding more than one python type: {varying}")
print("    BOTH ARE REAL and both are the probe's. No frame, so no NaN to")
print("    mistake for a type — the same reason this worked on 14-nyc-311.")

# ── Q6. Are any object keys actually data? AND THE SILENT TRAP. ─────────────
dotted = [k for k in packages if "." in k]
key = dotted[0]
print(f"\nQ6  YES, and pydash cannot say so — and {len(dotted)} of the keys cannot be")
print("    reached by the dotted spelling AT ALL:")
print(f"    key: {key}")
print(f"    pydash.get(doc, 'packages.{key[:22]}…')")
print(f"      -> {pydash.get(doc, f'packages.{key}')}   <- SILENT. Same as absent.")
print(f"    pydash.get(doc, ['packages', key])")
print(f"      -> {str(pydash.get(doc, ['packages', key]))[:44]}…")
print("    glom RAISES on this spelling; jmespath reaches it quoted. pydash is")
print("    the only one that answers a wrong question with a plausible value.")
print("    On 14-nyc-311 the verdict was the other way round.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
t = [pydash.pick(v, "version", "resolved", "license") for v in packages.values()]
print(f"\nQ8  {len(t):,} rows x 3 cols via `pick`")
print("   ", t[1])

# ── Q9. A field missing from some records, keeping those rows. ───────────────
lic = pydash.map_(list(packages.values()), "license")
print(f"\nQ9  `map_(values, 'license')` -> {len(lic):,} values, "
      f"{sum(x is None for x in lic):,} None")
print("    ALL 1,657 ROWS KEPT. jmespath's projection returns 734 for the same")
print("    question and does not say it dropped 923.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
lists = {k: v["funding"] for k, v in packages.items()
         if isinstance(v.get("funding"), list)}
rows = [{"pkg": k, **(e if isinstance(e, dict) else {"url": e})}
        for k, v in lists.items() for e in v]
print(f"\nQ10 funding[] over {len(lists)} packages -> {len(rows)} rows")
print("   ", rows[0])
print("    PARTLY: `funding` is object-or-array and its elements are")
print("    object-or-string, so two type tests are needed and neither is pydash's.")

# ── Q11. Find every path whose value matches something. ──────────────────────
URL = re.compile(r"https?://")
raw_hits, folded_hits = {}, {}


def find(value, path):
    if isinstance(value, str) and URL.search(value):
        raw = "$" + "".join("[]" if isinstance(s, int) else f".{s}" for s in path)
        raw_hits[raw] = raw_hits.get(raw, 0) + 1
        f = fold(path)
        folded_hits[f] = folded_hits.get(f, 0) + 1
    return value


pydash.map_values_deep(copy.deepcopy(doc), find)
print(f"\nQ11 {sum(raw_hits.values()):,} URL values.")
print(f"    as pydash reports them: {len(raw_hits):,} distinct paths")
print(f"    folded by hand:         {len(folded_hits)} paths — {folded_hits}")
print("    THE WALK IS pydash'S AND THE FOLD IS NOT. It is the only path language")
print("    here that answers question 11 unprompted, and the answer it gives is")
print(f"    {len(raw_hits):,} lines long. Being able to enumerate paths and being able")
print("    to describe a document are different things, and this file separates them.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
cols = list(counts)
flat = [pydash.pick(v, *cols) for v in packages.values()]
print(f"\nQ12 {len(flat):,} x {len(cols)}")
print("    The keyed collections stay dicts in their cells, so this is the")
print("    21-column honest table rather than pandas' 1,394-column one. The")
print("    install path is lost unless it is zipped back in — `values()` has no")
print("    room for the key, which is the keys-as-data cost exactly.")
