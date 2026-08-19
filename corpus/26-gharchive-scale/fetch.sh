#!/bin/sh
# 26 — one hour of public GitHub events, chosen for SIZE and nothing else.
#
# NOT COMMITTED: 118 MB gzipped, 870 MB and 286,864 records raw, far over the
# corpus threshold. GH Archive publishes one file per hour indefinitely, so any
# hour reproduces the shape even though no hour reproduces the bytes — but NOT
# any hour reproduces the SIZE, which is the whole point of this entry. Hours
# from 2024 run an order of magnitude larger than the recent ones, and
# `04-gharchive`'s is 11 MB gzipped against this one's 118 MB.
#
# THIS IS A CONTROL, DELIBERATELY. `04-gharchive` is the same source, the same
# format, the same event shape, at 50 MB and 37,883 records. The only variable
# that moves between the two entries is SIZE, which is what an axis needs if it
# is ever going to separate two files.
curl -sL https://data.gharchive.org/2024-01-15-12.json.gz -o source.json.gz
gzcat source.json.gz > source.jsonl     # 870 MB, .gitignore'd
