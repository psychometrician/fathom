#!/usr/bin/env bash
# USGS's earthquake feed for the last month — every event they located.
#
# A static feed file regenerated on a schedule, not a query endpoint: same URL,
# whole dataset, no pagination and no parameters. Public, no auth, no key.
#
# The window slides, so the copy measured on the day is the specimen rather than
# the URL. NOTES.md records what it looked like.
set -euo pipefail
cd "$(dirname "$0")"
curl -fsSL 'https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson' -o source.json
ls -l source.json
