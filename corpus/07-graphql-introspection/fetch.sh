#!/bin/sh
# 07 — a GraphQL introspection result. Fetched 2026-08-09.
#
# The SpaceX public GraphQL API describing its own schema. Chosen from three
# public endpoints as the richest (108 types against 23 and 25).
# Committed rather than fetched at read time: well under the 5 MB threshold,
# and a public demo endpoint will not be stable.
curl -s -X POST -H 'Content-Type: application/json' \
  -d @query.graphql.json \
  https://spacex-production.up.railway.app/ -o source.json
