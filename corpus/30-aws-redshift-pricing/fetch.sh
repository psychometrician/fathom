#!/bin/sh
# 30 — AWS Redshift public price list. Fetched 2026-08-18.
#
# COMMITTED, at 4.0 MB, under the corpus threshold — and this entry is the
# FIRST whose fetch is exactly reproducible. AWS publishes every price list
# under a pinned version as well as under `current`, so the URL below returns
# the same bytes tomorrow. `current/index.json` does not: it moved the day this
# was fetched and will move again.
#
# The pinned version is 20260814134227, published 2026-08-14T13:42:27Z.
# To see what has changed since, fetch `current` instead and diff.
#
# This is the file every AWS cost tool reads.
set -e
curl -sSL -o source.json \
  "https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonRedshift/20260814134227/index.json"
