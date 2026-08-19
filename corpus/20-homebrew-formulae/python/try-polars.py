"""polars — Homebrew's whole formula index

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   29.6 MB, 8,536 formulae, depth 8
  measured      2026-08-11
  run           cd corpus/20-homebrew-formulae/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               2   -                   CANNOT
   1 what is in here                            20   NO                  NO — REFUSES
   2 how deep                                    3   -                   CANNOT
   3 what is one record                          3   YES                 PARTLY
   4 always present vs sometimes                 6   YES                 NO
   5 does any field change type                  6   NO                  YES, BY REFUSING
   6 are any object keys data                    4   YES                 NO
   7 how many records                            1   NO                  yes
   8 three named fields to a table               3   YES                 yes
   9 a field missing from some rows              4   YES                 PARTLY
  10 flatten the deepest array                   8   YES                 NO — cannot reach it
  11 find every path matching something          7   YES                 PARTLY
  12 flattest honest table                       5   YES                 NO
  13 needed the shape in advance?                    YES, IN THE STRONGEST FORM IN
                                                     THE CORPUS: you must know which
                                                     fields are safe before polars will
                                                     return a frame at all
  14 survives the next file unchanged?               no — the projection is hand-picked
  15 readable a week later?                          yes, and it will not run
  16 lines, and how much is ceremony?                ~120, and 20 of them are refusals
  timing        every refusal is under 2s. The projection builds in 0.05s

  ══════════════════════════════════════════════════════════════════════════════
  POLARS REFUSES THIS DOCUMENT FIVE WAYS AND NEVER RETURNS A FRAME OF IT.
  ══════════════════════════════════════════════════════════════════════════════

  Five routes, zero DataFrames, and the error message is NOT DETERMINISTIC.
  Measured by running each call in six fresh processes — within one process it
  is fixed, which is why this needed subprocesses to see:

    read_json(default, infer_schema_length=100)      STABLE, 6/6
        extra field in struct data: vulnerabilities
        — a field on 10 of 8,536 formulae, first at index 344. The one stable
          message names the least important thing in the document.
    read_json(infer_schema_length=1000)              FOUR CAUSES IN SIX RUNS
        "String("nounzip")" as null · "String("antigravity-cli")" as null ·
        extra field: severity · extra field: test_dependencies
        — a lottery, mixing rare fields with type errors. Unusable as a diagnosis.
    read_json(infer_schema_length=None)   <- reads every record before deciding
        "Object({"bison": String("build")})" as string        (uses_from_macos[])
        "Object({"flex": String("build")})" as string         (the same site)
        "Array([String("$HOMEBREW_PREFIX/opt/activemq/…")])"  (service.run)
        — EVERY message it gives names a REAL polymorphism, and it names more
          than one. BOTH SITES ARE AMONG THE PROBE'S NINE. Which one you hear
          about is a race, and you are never told there are nine.
    pl.DataFrame(doc)
        found value of type String: "libedit" while building Struct({'bison': String})
    pl.DataFrame(doc, strict=False)
        could not append value: {":versioned_formula",""} of type: struct[2]

  So the setting that looks most careless is the only reproducible one, and the
  setting that reads the whole file tells the truth in a different order each
  time. This is entry 13's finding on a second document — *three routes, three
  answers, and the correct one is the one that fails* — with nondeterminism on
  top, and it is polars' SECOND nondeterminism in this corpus after the column
  ordering entry 14 recorded.

  Its advice is also circular at the last rung: `infer_schema_length=None` is
  already unlimited and the error still says "Try increasing infer_schema_length".

  WHAT STILL WORKS is a hand-picked projection of fields you already know to be
  scalar. That answers questions 8 and 9 in a line each and is not an answer to
  question 1, because you had to know the answer to write it.
"""
import json
import time
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))

# ── Q0. Is this what it claims to be, and is it whole? ───────────────────────
print("\nQ0  polars has its own JSON reader and no health report. CANNOT.")

# ── Q1. What is in here — FIVE REFUSALS, EACH RUN FIVE TIMES. ────────────────
# Run repeatedly BECAUSE THE MESSAGE IS NOT STABLE. Three runs of the identical
# `infer_schema_length=1000` call gave three different causes, which is how this
# was found at all.
def cause(e):
    m = " ".join(str(e).split())
    return m.split(". Try increasing")[0].split(", consider increasing")[0][:78]


routes = [
    ("read_json()                        ", lambda: pl.read_json(RAW)),
    ("read_json(infer_schema_length=1000)", lambda: pl.read_json(RAW, infer_schema_length=1000)),
    ("read_json(infer_schema_length=None)", lambda: pl.read_json(RAW, infer_schema_length=None)),
    ("pl.DataFrame(doc)                  ", lambda: pl.DataFrame(doc)),
    ("pl.DataFrame(doc, strict=False)    ", lambda: pl.DataFrame(doc, strict=False)),
]
print("\nQ1  five routes to a frame, each attempted 5 times. None returns one:")
for label, fn in routes:
    seen = {}
    for _ in range(5):
        try:
            d = fn()
            seen["OK %d x %d" % (d.height, d.width)] = seen.get("OK", 0) + 1
        except Exception as e:
            k = f"{type(e).__name__}: {cause(e)}"
            seen[k] = seen.get(k, 0) + 1
    print(f"    {label}")
    for k, n in sorted(seen.items(), key=lambda kv: -kv[1]):
        print(f"        {n}/5  {k}")
print("    Five routes, five causes, no frame. Note the 5/5s: WITHIN one process")
print("    the message is fixed. It is not fixed BETWEEN processes, which the")
print("    in-process loop above cannot show and the subprocess loop below can.")

# ── Q1b. The same call, in FRESH PROCESSES. ──────────────────────────────────
import subprocess
import sys

PROBE = ("import polars as pl\n"
         "try:\n"
         "    pl.read_json('../source.json', infer_schema_length=%s); print('OK')\n"
         "except Exception as e:\n"
         "    m=' '.join(str(e).split())\n"
         "    print(m.split('. Try increasing')[0].split(', consider increasing')[0][:78])\n")
print("\nQ1b THE SAME CALL IN SIX FRESH PROCESSES — this is the real finding:")
for n in ("100", "1000", "None"):
    seen = {}
    for _ in range(6):
        out = subprocess.run([sys.executable, "-c", PROBE % n],
                             capture_output=True, text=True).stdout.strip()
        seen[out] = seen.get(out, 0) + 1
    print(f"    infer_schema_length={n}")
    for k, c in sorted(seen.items(), key=lambda kv: -kv[1]):
        print(f"        {c}/6  {k}")
print("    ONLY THE DEFAULT IS STABLE, and what it names is the least useful")
print("    thing in the document: `vulnerabilities`, a field on 10 of 8,536.")
print("    THE MIDDLE SETTING IS A LOTTERY — four distinct causes in six runs,")
print("    mixing rare fields with type errors, so its message cannot be used as")
print("    a diagnosis at all.")
print("    THE EXHAUSTIVE SETTING VARIES TOO, and it is the interesting one:")
print("    every message it gives names a REAL polymorphism, and it names more")
print("    than one — `uses_from_macos[]` object-vs-string AND `service.run`")
print("    array-vs-string. BOTH ARE AMONG THE PROBE'S NINE. Which of the nine")
print("    you are told about is a race, and you are never told there are nine.")
print("    Entry 14 recorded polars' column ORDER changing between runs. This is")
print("    a second nondeterminism, in a different mechanism, on another document.")

# ── Q2. How deep does it go? ─────────────────────────────────────────────────
print("\nQ2  CANNOT. polars answers question 2 from a schema and there is no")
print("    schema. Where it does build one — see entry 25 — the dtype is a full")
print("    nested type and reads depth off directly. Here it never gets one.")

# ── Q1b/Q3/Q7. What CAN be read: a hand-picked scalar projection. ────────────
SCALAR = ["name", "full_name", "desc", "homepage", "license", "revision", "tap",
          "deprecated", "disabled", "outdated", "pinned", "post_install_defined"]
t = time.time()
df = pl.DataFrame([{k: r.get(k) for k in SCALAR} for r in doc])
print(f"\nQ3  a hand-picked projection: {df.height:,} x {df.width} in {time.time()-t:.2f}s")
print("    THE PROJECTION IS THE ADMISSION. Twelve fields chosen because I")
print("    already knew they were scalar — which is question 1's answer used as")
print("    question 1's input. The probe needed no such list.")
print(f"Q7  {df.height:,} formulae, and this count came from len(doc), not polars")

# ── Q4. Always present vs sometimes. ─────────────────────────────────────────
rk = [set(r) for r in doc]
allk = set().union(*rk)
absent = sorted(k for k in allk if sum(k in r for r in rk) < len(doc))
nulls = df.null_count().row(0)
print(f"\nQ4  in the projection, columns with any null: "
      f"{[c for c, n in zip(df.columns, nulls) if n]}")
print(f"Q4  the document has {len(absent)} sometimes-ABSENT fields {absent}")
print("    and 17 always-present-but-null ones. polars would conflate them as")
print("    pandas does — a unified schema cannot hold the difference — but on")
print("    THIS document it does not get far enough to conflate anything.")

# ── Q5. Does any field change type? YES, AND THE REFUSAL IS THE ANSWER. ──────
print("\nQ5  ANSWERED, AND BY FAILING. Route 3 above reads every record before")
print("    choosing a schema and then reports:")
print('      error deserializing value "Object({"bison": String("build")})" as string')
print("    That is `uses_from_macos[]`: strings on 1,163 formulae, objects on 632.")
print("    The probe reports the same site among nine. polars reports one site")
print("    and stops, because for polars a second type is not a finding, it is")
print("    an obstacle. TRUE AND UNUSABLE — the most accurate sentence any tool")
print("    in this directory prints about question 5, delivered as a crash.")

# ── Q6. Are any object keys actually data? ───────────────────────────────────
plats = sorted({k for r in doc for k in (r.get("bottle") or {}).get("stable", {}).get("files", {})})
print(f"\nQ6  NO. Where polars does build a schema it puts the keys IN the type:")
print(f"    bottle.stable.files has {len(plats)} platform keys — {plats[:4]}…")
print("    each of which would be a struct field. The probe folds them to one")
print("    path and declines to call them data. Here polars never gets to either.")

# ── Q8. Three named fields into a table. ─────────────────────────────────────
print(f"\nQ8  {df.select('name', 'desc', 'homepage').shape} — one line, on the projection")
print(df.select("name", "desc", "homepage").head(2))

# ── Q9. A field missing from some records, keeping those rows. ───────────────
ex = pl.DataFrame({"name": [r["name"] for r in doc],
                   "executables": [r.get("executables") for r in doc]})
print(f"\nQ9  executables: {ex['executables'].null_count():,} null of {ex.height:,}, rows kept")
print("    PARTLY — polars accepted this column only because I extracted it in")
print("    python first. 185 of those nulls are ABSENT keys and it cannot say so.")

# ── Q10. Flatten the deepest array into rows. ────────────────────────────────
print("\nQ10 NO. explode/unnest need a frame with the column in it, and no route")
print("    above produces one containing `patches`. Reaching patches[].resolves[]")
print("    means flattening in python and handing polars the result — at which")
print("    point python did question 10 and polars printed it.")
res = pl.DataFrame([{"name": f["name"], **rr}
                    for f in doc for p in (f.get("patches") or [])
                    for rr in (p.get("resolves") or [])])
print(f"    done in python: {res.height} x {res.width}  (the true count is 557)")

# ── Q11. Find every path whose value matches something — here, a URL. ────────
strs = [c for c in df.columns if df.schema[c] == pl.String]
naive = [c for c in strs if df[c].str.starts_with("http").any()]
strict = [c for c in strs if df[c].str.contains(r"^https?://").any()]
print(f"\nQ11 in the projection: http-prefixed {naive}, ^https?:// {strict}")
print(f"    dropped: {sorted(set(naive) - set(strict))} — the fifteen formulae")
print("    NAMED http* (httpd, httpie, http-server). Same trap as every other")
print("    tool here, because it is the predicate's fault and not the tool's.")
print("    PARTLY, and over twelve columns of 61 — the scan is as wide as the")
print("    projection, and the projection was hand-written.")

# ── Q12. The flattest honest table, and what was lost. ───────────────────────
print("\nQ12 NO. The flattest honest table is the one polars refuses to build.")
print("    What is available is the projection: 8,536 x 12 with nothing lost")
print("    because nothing nested was ever admitted. Entry 15 recorded polars")
print("    RAISING on unnest with 26 colliding names; this document does not")
print("    reach unnest, so the refusal moved one step earlier — to the read.")
