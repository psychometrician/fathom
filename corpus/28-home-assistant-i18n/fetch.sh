#!/bin/sh
# Home Assistant frontend, the English translation catalogue — fetched 2026-08-12
# from the `dev` branch. A moving target by nature: a translation file grows every
# week, so re-fetching gives a LATER file, not this one. NOTES.md records what it
# was on the day and source.json is committed because it is under 5 MB.
set -e
curl -sS -o source.json \
  "https://raw.githubusercontent.com/home-assistant/frontend/dev/src/translations/en.json"
