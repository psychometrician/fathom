#!/bin/sh
# 04 — one hour of public GitHub events. Fetched 2026-08-08 for 2026-08-07 15:00 UTC.
#
# NOT COMMITTED: 10.6 MB gzipped, 50 MB and 37,883 records raw, over the corpus
# threshold. GH Archive publishes one file per hour, indefinitely, so any hour
# reproduces the shape even though no hour reproduces the bytes.
#
# It arrives GZIPPED, which is the point of the specimen as much as the size is.
curl -sL https://data.gharchive.org/2026-08-07-15.json.gz -o source.json.gz
gzcat source.json.gz > source.jsonl     # 50 MB, .gitignore'd
