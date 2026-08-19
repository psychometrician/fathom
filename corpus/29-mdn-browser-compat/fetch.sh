#!/bin/sh
# 29 — MDN browser-compat-data, the whole bundle. Fetched 2026-08-12.
#
# NOT COMMITTED: 19.9 MB, over the corpus threshold. NOTES.md records what it
# was on the day. The package is versioned and published continuously, so a
# later fetch gives a LATER file — the shape reproduces, the bytes do not.
#
# This is the data behind every "can I use this yet" answer on MDN.
set -e
curl -sSL -o source.json "https://unpkg.com/@mdn/browser-compat-data/data.json"
