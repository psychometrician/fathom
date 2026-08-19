"""Scrub an agent transcript to structure, keeping every graded property.

    uv run scrub.py <transcript.jsonl> source.jsonl

**Why this file exists rather than a `fetch.sh`.** `VERDICT.md` carried the
agent-trace decision open for two working days: the trace is the only specimen
available that no API has normalised, and it is also a transcript of the
author's own conversations. The author chose *"scrub the string values and keep
the structure"* on 2026-08-09, on the grounds that **every axis this corpus
grades is structural**, so the grading survives the scrub intact.

WHAT IS KEPT, AND WHY IT IS NOT A JUDGEMENT CALL
------------------------------------------------
Blanking every string would destroy the thing this file is *for*. `role`,
`type`, `stop_reason` and their kin are **discriminators** — the corpus's fourth
operation partitions on exactly these — and a document whose discriminators are
all `"xxxx"` cannot test it.

So the rule is structural rather than a list of blessed field names:

    a string value is VOCABULARY if it is <= 32 characters
    and occurs >= 20 times in the document. Everything else is CONTENT.

That is the same test `VERDICT.md` records as open defect 13 — a kind's values
recur across the document, an identifier's do not — applied here as a scrubbing
rule instead of a reporting one. Nothing is hand-picked, and the kept vocabulary
is printed on every run so it can be audited.

WHAT THE SCRUB COSTS, STATED SO IT IS NOT DISCOVERED LATER
----------------------------------------------------------
1. **Question 0's `encoded` reading is destroyed.** A string holding an encoded
   JSON document is content by the rule above, so it becomes `xxxx` and stops
   parsing. The scrubbed file cannot be used to test that health property.
2. **String CONTENT is gone**, so questions 11 (find every path whose value
   matches an email or URL) cannot be asked of it.
3. Everything else survives: keys, nesting, array lengths, types, string
   LENGTHS, numbers, booleans, nulls, and every discriminator.
"""
import json
import sys
from collections import Counter

KEEP_MAX_LEN = 32
KEEP_MIN_USES = 20


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


def scrub(o, keep):
    """Keys are structure and are never touched. Only string VALUES are."""
    if isinstance(o, str):
        return o if o in keep else "x" * len(o)
    if isinstance(o, dict):
        return {k: scrub(v, keep) for k, v in o.items()}
    if isinstance(o, list):
        return [scrub(v, keep) for v in o]
    return o


def main(src, dst):
    with open(src, encoding="utf-8") as fh:
        docs = [json.loads(line) for line in fh if line.strip()]

    counts = Counter(s for d in docs for s in strings(d))
    keep = {s for s, n in counts.items()
            if len(s) <= KEEP_MAX_LEN and n >= KEEP_MIN_USES}

    with open(dst, "w", encoding="utf-8") as fh:
        for d in docs:
            fh.write(json.dumps(scrub(d, keep), ensure_ascii=False) + "\n")

    print(f"{len(docs):,} records")
    print(f"{len(counts):,} distinct string values, {len(keep):,} kept as vocabulary")
    print(f"\nthe kept vocabulary, printed so the scrub can be audited:")
    for s, n in sorted(keep and counts.most_common() or [],
                       key=lambda kv: -kv[1]):
        if s in keep:
            print(f"    {n:7,}  {s!r}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
