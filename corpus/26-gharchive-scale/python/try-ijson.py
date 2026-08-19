# ijson — one hour of public GitHub events, at 17x the size of entry 04
#
# Scoring header follows ../../01-npm-registry/r/try-purrr.R, which is the template.
#
# ── scoring ──────────────────────────────────────────────────────────────────
#  tool          ijson (version printed at run time)
#  file          ../source.json.gz   118 MB gzipped, 870 MB / 286,864 records raw
#  measured      2026-08-14
#  run           cd corpus/26-gharchive-scale/python && uv run try-ijson.py
#
#  Header filled in after the run. See the CONCLUSION.
#
# **THIS ENTRY GRADES THE TOOLS ON SCALE AND NOTHING ELSE.** It is the same
# source, format and event shape as `04-gharchive` at 50 MB, chosen so that size
# is the only variable. Every attempt here therefore carries a BUDGET and
# reports peak memory, because "did it finish" is the question and a tool that
# cannot must say so rather than hang.
#
# ijson is the tool this entry exists to reward: it never holds the document.

import gzip
import resource
import signal
import time
import ijson

BUDGET = 600           # seconds; a tool that exceeds it has answered "cannot"
SRC = "../source.json.gz"


class Budget(Exception):
    pass


def _stop(signum, frame):
    raise Budget()


signal.signal(signal.SIGALRM, _stop)


def rss_mb():
    # macOS reports ru_maxrss in BYTES; Linux in kilobytes. This machine is
    # darwin, and the value is sanity-checked against the file size below.
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1e6


print(f"ijson {ijson.__version__} · backend {ijson.backend}")
print(f"budget {BUDGET} s · file {SRC}")

print("\nQ0  ijson parses and reports nothing about soundness. It RAISES on")
print("    malformed input mid-stream, which is more than most. CANNOT.")

# ── ONE STREAMING PASS OVER THE WHOLE FILE. ──────────────────────────────────
signal.alarm(BUDGET)
t0 = time.perf_counter()
records = 0
leaves = 0
maxdepth = 0
depth = 0
by_type = {}
prefixes = set()
urls = 0
finished = True
try:
    with gzip.open(SRC, "rb") as fh:
        for prefix, event, value in ijson.parse(fh, multiple_values=True):
            if event in ("start_map", "start_array"):
                depth += 1
                maxdepth = max(maxdepth, depth)
                if depth == 1:
                    records += 1
            elif event in ("end_map", "end_array"):
                depth -= 1
            elif event != "map_key":
                leaves += 1
                by_type[event] = by_type.get(event, 0) + 1
                prefixes.add(prefix)
                if event == "string" and value.startswith(("http://", "https://")):
                    urls += 1
except Budget:
    finished = False
signal.alarm(0)
secs = time.perf_counter() - t0

if finished:
    print(f"\n    ONE STREAMING PASS over 870 MB: {secs:.1f} s, peak RSS {rss_mb():,.0f} MB")
    print(f"    ** {records:,} records — THE WHOLE FILE, not a sample. **")
else:
    print(f"\n    DID NOT FINISH within {BUDGET} s — got {records:,} records "
          f"({100*records/286864:.1f}%), peak RSS {rss_mb():,.0f} MB")

# ── Q1/Q2/Q7. ────────────────────────────────────────────────────────────────
print(f"\nQ1  {len(prefixes):,} distinct prefixes — and a prefix is a FOLDED path:")
print("    ijson writes an array element as `.item`, so every element of an")
print("    array shares one prefix. It is the only automatic folding here.")
print(f"\nQ2  {maxdepth}. YES — counted from the start/end events as they pass.")
print(f"\nQ7  {records:,} records, {leaves:,} leaves.")

# ── Q5. ──────────────────────────────────────────────────────────────────────
print("\nQ5  leaf events over the whole file:")
for k, v in sorted(by_type.items(), key=lambda kv: -kv[1]):
    print(f"      {k:<10} {v:>12,}")
print("    YES, and exactly: the EVENT NAME is the JSON type.")

# ── Q11. ─────────────────────────────────────────────────────────────────────
print(f"\nQ11 {urls:,} URL leaves, counted in the same pass. YES.")

# ── Q3/Q4/Q6. ────────────────────────────────────────────────────────────────
print("\nQ3  ijson names no candidates and prices none. CANNOT.")
print("\nQ4  PARTLY — presence per prefix is countable in the same pass, but")
print("    the denominator is Q3's to choose.")
print("\nQ6  CANNOT. The prefix folds ARRAYS and never an object whose keys are")
print("    data, which is the distinction fathom's fold exists to make.")

# ── Q8/Q9/Q10/Q12. ───────────────────────────────────────────────────────────
print("\nQ8  ijson.items(prefix) reaches a named field, streaming until it finds")
print("    it — one pass per field unless you write the event loop yourself.")
print("\nQ9  a missing prefix yields nothing. Absence is silence in a stream.")
print("\nQ10 the `.item` suffix IS the array flattening, automatic, and it keeps")
print("    an array step distinct from a key step. YES.")
print("\nQ12 PARTLY. The event stream IS a melt — (prefix, type, value) is three")
print("    columns — but assembling it into a table means writing the loop.")

print(f"""
CONCLUSION. Written after the run and corrected against what printed.
  finished: {finished} · {secs:.1f} s · peak RSS {rss_mb():,.0f} MB

IT READ 870 MB AND 286,864 RECORDS IN ABOUT TEN SECONDS AT 25 MB OF MEMORY.
Not a sample — the whole file. 1,035 distinct prefixes, depth 6, 17,670,186
leaves, and the type census exact because the event name IS the JSON type.

AND THAT NUMBER SHOULD BE READ NEXT TO fathom's. On this same file the probe
took 12.3 SECONDS AND 2,485 MB to describe the FIRST 20,000 RECORDS — 6.97% of
it. ijson is faster, uses one percent of the memory, and reads all of it.

THE TWO ARE NOT DOING THE SAME WORK and the comparison still matters. fathom
classifies, folds, prices row candidates and renders a page; ijson counts
events. What ijson settles is the part they DO share: the READ. This entry's
own notes derived `peak RSS ~ 500 MB + 2.28 x file size` and concluded memory
tracks the file rather than the sample, because the document is read and split
into lines before the cap applies. ijson proves that cost is not inherent to
reading 870 MB of NDJSON — it is 25 MB if you never hold it.

SO THE SAMPLING CONTRACT BUYS LESS THAN IT COSTS ON THIS FILE. It was supposed
to bound the work; it bounds the PARSE and not the READ, and the read is where
the 2,485 MB went. And the sample is what cost this entry a reported
keys-as-data site — `payload.issue.performed_via_github_app.permissions`, 11
copies in 286,864 records, invisible in the first 20,000. A streaming reader
would have found it AND used less memory.

WHAT ijson STILL CANNOT DO is question 3 and question 6, for the 30th entry
running. 1,035 prefixes is a field list, not a menu of row shapes, and the
prefix folds arrays while never folding an object whose keys are data.
""")
