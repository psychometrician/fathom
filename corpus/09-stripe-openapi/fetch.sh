#!/bin/sh
# 09 — the Stripe OpenAPI specification. Fetched 2026-08-09.
#
# NOT COMMITTED: 7,967,776 bytes, over the corpus threshold. Stripe publishes
# this continuously, so any pull reproduces the shape though not the bytes.
curl -sL https://raw.githubusercontent.com/stripe/openapi/master/openapi/spec3.json -o source.json
