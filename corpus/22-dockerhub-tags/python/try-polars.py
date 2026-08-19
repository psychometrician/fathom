"""polars — Docker Hub tags, 100 tags

Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.

  tool          polars (version printed at run time)
  file          ../source.json   476 KB, 100 tags under $.results, depth 5
  measured      2026-08-11
  run           cd corpus/22-dockerhub-tags/python && uv run try-polars.py

  question                                    lines  shape known first?  worked
   0 is this sound                               1   -                   CANNOT
   1 what is in here                            10   YES                 yes, once pointed
   2 how deep                                    6   NO                  YES — 3 + 2 = 5
   3 what is one record                          6   YES                 BOTH, priced
   4 always present vs sometimes                 8   NO                  PARTLY
   5 does any field change type                  4   NO                  yes — NONE
   6 are any object keys data                    1   -                   n/a
   7 how many records                            2   NO                  yes, both numbers
   8 three named fields to a table               2   YES                 yes
   9 a field missing from some rows              3   YES                 PARTLY
  10 flatten the deepest array                   4   YES                 yes — 1,388
  11 find every path matching something          3   NO                  NONE OF ONE
  12 flattest honest table                       4   NO                  yes
  13 needed the shape in advance?                    yes — where the records are
  14 survives the next file unchanged?               most of it
  15 readable a week later?                          yes
  16 lines, and how much is ceremony?                ~95

  THE NESTED CONTROL, AND POLARS READS IT AT THE DEFAULT SETTING. Entry 20 it
  refused five ways; entry 21 it needed `infer_schema_length=None`; here
  `pl.DataFrame(results)` just works. One key-set per shape and no polymorphism
  is exactly the condition its schema inference needs, and this document is the
  cleanest statement in the corpus of what that condition IS.

  `read_json` on the file still returns the 1-row ENVELOPE, as on entry 21.
"""
import json
import time
from importlib.metadata import version

import polars as pl

print(f"polars {version('polars')}")

RAW = "../source.json"
doc = json.load(open(RAW))
tags = doc["results"]

print("\nQ0  polars has its own reader and no health report. CANNOT.")

env = pl.read_json(RAW)
print(f"\nQ1  read_json on the file -> {env.height} x {env.width}: {env.columns}")
print("    THE ENVELOPE AGAIN, one row, not an error. Same as entry 21.")
t = time.time()
df = pl.DataFrame(tags)
print(f"Q1  pl.DataFrame(results) -> {df.height} x {df.width} in {time.time()-t:.2f}s")
print("    AT THE DEFAULT SETTING. Entry 20 refused this five ways and entry 21")
print("    needed infer_schema_length=None. The difference is that this document")
print("    has one key-set per shape and no polymorphism — the exact condition")
print("    schema inference needs, stated by a document that meets it.")


def depth(dt, d=1):
    if isinstance(dt, pl.Struct):
        return max([depth(f.dtype, d + 1) for f in dt.fields] or [d])
    if isinstance(dt, pl.List):
        return depth(dt.inner, d + 1)
    return d


dp = max(depth(df.schema[c]) for c in df.columns)
print(f"\nQ2  deepest column nests {dp} below the row; records are at $.results,")
print(f"    2 levels in, so {dp} + 2 = {dp+2} — the probe says 5.")

print(f"\nQ3  an item of results: {df.height} x {df.width}, "
      f"{sum(df.null_count().row(0))/(df.height*df.width):.0%} null")
t = time.time()
img = df.select("name", "images").explode("images").unnest("images")
print(f"Q3  an item of images:  {img.height:,} x {img.width}, "
      f"{sum(img.null_count().row(0))/(img.height*img.width):.0%} null, "
      f"{time.time()-t:.2f}s")
print("    THE PROBE SAYS 100 x 16 AT 0% AND 1,388 x 11 AT 16%. explode+unnest")
print("    is two verbs and keeps `name`, which pandas needed record_path for.")

inull = {c: n for c, n in zip(img.columns, img.null_count().row(0)) if n}
iempty = {c: int((img[c] == "").sum()) for c in img.columns
          if img.schema[c] == pl.String}
iempty = {k: v for k, v in iempty.items() if v}
print(f"\nQ4  image columns with NULL:         {inull}")
print(f"Q4  image columns with EMPTY STRING: {iempty}")
print("    polars keeps `\"\"` and null apart because String and null are")
print("    different things to it — and `null_count()` counts only the second,")
print("    so its 16% is the probe's 16% and both miss the 2,776 empty strings.")
print(f"    counting all of them: "
      f"{(sum(inull.values())+sum(iempty.values()))/(img.height*(img.width-1)):.0%}")

print(f"\nQ5  polars unified every column without complaint. dtypes:")
print(f"    {dict(list(df.schema.items())[:4])} …")
print("    The probe reports NO type change. A document polars can read at the")
print("    default is, by construction, one it found no conflict in.")
print("\nQ6  no keyed collections. n/a, and the probe agrees.")
print(f"\nQ7  {df.height} tags here; `count` says {doc['count']:,}, `next` is a URL")

print(f"\nQ8  {df.select('name', 'full_size', 'last_updated').shape}")
print(df.select("name", "full_size", "last_updated").head(2))
print(f"\nQ9  `variant` null on {img['variant'].null_count():,} of {img.height:,}, rows kept")
print("    Every image HAS the key. polars cannot say so and here nothing")
print("    depends on it — no key in this document is ever absent.")
print(f"\nQ10 explode+unnest -> {img.height:,} x {img.width}, parent kept — see Q3")
strs = [c for c in df.columns if df.schema[c] == pl.String]
u = [c for c in strs if df[c].str.contains(r"^https?://").any()]
print(f"\nQ11 of {len(strs)} String columns, {len(u)} hold a URL: {u}")
print("    NONE OF ONE. The document's single URL is `$.next`, outside the")
print("    records. Entries 17 and 18 recorded the same; this is the extreme case.")
print(f"\nQ12 {df.height} x {df.width} with `images` a List(Struct), or {img.height:,} x "
      f"{img.width} exploded.")
print("    Both honest, and polars builds either in one line. THE PROBE PRICES")
print("    BOTH AND POLARS CHOOSES NEITHER — which on this document is the only")
print("    difference left between them.")
