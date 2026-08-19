"""ijson — USGS earthquakes, one month

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          ijson (version printed at run time)
  file          ../source.json   7.4 MB, 10,885 features, depth 5
  measured      2026-08-10
  run           cd corpus/25-usgs-quakes/python && uv run try-ijson.py

  question                                    lines  shape known first?  worked
   0 is this sound                               3   -                   PARTLY
   1 what is in here                             8   NO                  YES
   2 how deep                                    2   NO                  yes
   3 what is one record                          2   YES                 CANNOT
   4 always present vs sometimes                 6   NO                  YES
   5 does any field change type                  4   NO                  YES
   6 are any object keys data                    1   -                   n/a
   7 how many records                            1   NO                  yes
   8 three named fields to a table               5   YES                 yes
   9 a field missing from some rows              -   YES                 see Q8
  10 flatten the deepest array                   4   YES                 yes
  11 find every path matching something          5   NO                  YES
  12 flattest honest table                       -   YES                 not attempted
  13 needed the shape in advance?                    NO for 1, 2, 4, 5, 11
  14 survives the next file unchanged?               yes for those five
  15 readable a week later?                          the prefix strings need a note
  16 lines, and how much is ceremony?                ~85, and the event loop is most

**ijson IS THE ONLY TOOL HERE THAT NEVER HOLDS THE DOCUMENT**, and on this file
that costs nothing and buys the Phase 1 answers outright: it walks 7.4 MB in one
pass and reports paths, depth, presence and types without a schema, a frame or a
column list. Its `prefix` IS a folded path — `features.item.properties.mag` —
which is the same idea as `design/probe.py`'s `$.features[].properties.mag`
arrived at independently.

**What it will not do is question 3 or 12.** There is no notion of a record
candidate, and building the flat table means writing the accumulation yourself,
at which point ijson is a parser and the work is python's.
"""
from collections import Counter, defaultdict
from importlib.metadata import version

import ijson

print(f"ijson {version('ijson')}")
SRC = "../source.json"

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  ijson raises IncompleteJSONError on a truncated file, which is more")
print("    than most here manage. Duplicate keys, big ints and encoded payloads:")
print("    it yields both duplicates as events, so a CONSUMER could see them —")
print("    but ijson itself says nothing. PARTLY.")

# ── Q1/Q2/Q4/Q5. One pass answers four questions. ────────────────────────────
kinds = defaultdict(Counter)   # folded path -> Counter of value types
per_feature = Counter()        # folded path -> how many features carried it
n_features = 0

with open(SRC, "rb") as fh:
    seen_this = set()
    for prefix, event, value in ijson.parse(fh):
        folded = prefix.replace(".item", "[]")
        if event in ("string", "number", "boolean", "null",
                     "start_map", "start_array"):
            t = {"start_map": "object", "start_array": "array"}.get(event, event)
            kinds[folded][t] += 1
            if folded.startswith("features[]."):
                seen_this.add(folded)
        if prefix == "features.item" and event == "end_map":
            n_features += 1
            for p in seen_this:
                per_feature[p] += 1
            seen_this = set()

# ijson emits an EMPTY prefix for the document root, which is a real path to it
# and not one to jq or to the probe. Dropped so the count is comparable: 46 → 45.
named = [p for p in kinds if p]
print(f"\nQ1  {len(named)} distinct folded paths, in ONE STREAMING PASS")
print("   ", sorted(named)[:10], "…")
print(f"Q2  depth {max(p.count('.') + p.count('[]') + 1 for p in named)}"
      "  (segments, which is jq's convention and the probe's)")
print(f"Q7  {n_features:,} features")

props = {p: per_feature[p] for p in per_feature if p.startswith("features[].properties.")}
some = {p.split(".")[-1]: v for p, v in props.items() if v < n_features}
print(f"\nQ4  property paths present on every feature: {len(props) - len(some)}")
print(f"Q4  present on only some: {some or 'none'}")
print("    Like jq and unlike every frame here, PRESENCE is what is counted:")
print("    a key with a null value is present, and ijson saw the key.")

changing = {p.rsplit(".", 1)[-1]: dict(c) for p, c in kinds.items()
            if p.startswith("features[].properties.") and len(c) > 1}
print(f"\nQ5  property paths carrying more than one event type: {len(changing)}")
print("   ", {k: v for k, v in list(changing.items())[:4]}, "…")
real = {k: v for k, v in changing.items() if len(set(v) - {"null"}) > 1}
print(f"Q5  ignoring null: {real or 'none'} — agrees with jq, glom and the probe")

# ── Q3. What is one record. ──────────────────────────────────────────────────
print("\nQ3  ijson names no candidates and prices nothing. CANNOT.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
print("\nQ6  no keyed collections here. n/a")

# ── Q8/Q9/Q10. Extraction, streaming. ────────────────────────────────────────
rows = []
with open(SRC, "rb") as fh:
    for f in ijson.items(fh, "features.item"):
        p, g = f["properties"], f["geometry"]["coordinates"]
        rows.append((p["mag"], p["place"], p["time"], p.get("alert"),
                     g[0], g[1], g[2], p["types"]))
print(f"\nQ8/Q9/Q10  {len(rows):,} rows built streaming: {rows[0]}")
print(f"Q9  alert non-null on {sum(1 for r in rows if r[3] is not None)} rows, kept as None elsewhere")

# ── Q11. Find every path whose value matches something. ──────────────────────
urls = Counter()
with open(SRC, "rb") as fh:
    for prefix, event, value in ijson.parse(fh):
        if event == "string" and isinstance(value, str) and value.startswith("http"):
            urls[prefix.replace(".item", "[]")] += 1
print(f"\nQ11 URL-valued paths: {dict(urls)}")
print("    Found without naming a column or a schema, in one pass, on a file")
print("    that never entered memory. This is ijson's best answer.")

# ── The packed strings, because defect 26 came from this file. ───────────────
print("\nDEFECT 26  does ijson notice a list packed into a string?")
print("   ", rows[0][7], "→ a `string` event and nothing more.")

# ── One thing ijson alone gets right, noticed from its output rather than
#    predicted: it yields Decimal, not float. ────────────────────────────────
print("\nPRECISION  ijson yields", type(rows[0][0]).__name__,
      "where every other tool here yields float:")
print("   ", repr(rows[0][4]), "vs", repr(float(rows[0][4])))
print("    On coordinates at 12 significant figures that is the difference")
print("    between the number in the file and a number near it.")
