#!/bin/sh
# 15 — GitHub issues and pull requests for pandas-dev/pandas. Fetched 2026-08-09.
#
# 702,018 bytes, 100 records, a flat JSON array. Committed: under the 5 MB rule.
# The endpoint returns the most recent 100 in whatever state they are in, so
# re-running gives different records and NOTES.md records the file as it was.
#
# `state=all` on purpose: the default is open-only, and the mix of open and
# closed is part of what makes this an ordinary document rather than a curated
# one. No authentication — this is the unauthenticated public endpoint, which is
# what anybody reaching for it first would use.
curl -sL 'https://api.github.com/repos/pandas-dev/pandas/issues?per_page=100&state=all' -o source.json
