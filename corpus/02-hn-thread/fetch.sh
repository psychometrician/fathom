#!/bin/sh
# 02 — one Hacker News comment thread, fetched 2026-08-08.
#
# HN's own API at hacker-news.firebaseio.com returns FLAT items whose `kids` are
# id references, so a thread has to be assembled from hundreds of requests.
# Assembling it would make the document ours rather than one somebody was handed,
# which the corpus rule forbids. Algolia's HN API returns the whole nested tree in
# one GET, so that is what is used.
curl -s https://hn.algolia.com/api/v1/items/49220339 -o source.json
