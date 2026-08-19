#!/bin/sh
# 10 — Wikidata entity Q30 (United States). Fetched 2026-08-09.
#
# Chosen from four by size: 1,466,078 bytes, 469 claim properties, against
# Q145's 977 KB and Q1/Q5 at ~200 KB. Committed: under the 5 MB threshold, and
# Wikidata entities change continuously so the bytes are not reproducible.
curl -s 'https://www.wikidata.org/wiki/Special:EntityData/Q30.json' -o source.json
