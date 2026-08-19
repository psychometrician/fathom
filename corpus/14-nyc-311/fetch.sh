#!/bin/sh
# 14 — NYC 311 service requests. Fetched 2026-08-09.
#
# 29,435,797 bytes, 20,000 records, a flat JSON array. **NOT committed**: over
# the 5 MB threshold, so this script is the artifact and NOTES.md records what
# the file looked like on the day. The endpoint returns the most recent records,
# so re-running gives different rows and a different byte count.
#
# The 20,000 cap is Socrata's `$limit`, chosen to match the sampling cap in
# design/probe.py (MAX_RECORDS) so the probe reads the whole file and its
# coverage line is not doing any work.
curl -sL 'https://data.cityofnewyork.us/resource/erm2-nwe9.json?$limit=20000' -o source.json
