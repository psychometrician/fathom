#!/usr/bin/env bash
# crates.io's front-page summary.
#
# Chosen for a shape the corpus does not have: ONE object holding SEVERAL
# DIFFERENT collections, rather than one array of records, a wrapper around one
# array, or a map keyed by name. Public, no auth, no key.
#
# The endpoint is a live summary and changes whenever a crate is published, so
# the copy measured on the day is the specimen rather than the URL. NOTES.md
# records what it looked like.
set -euo pipefail
cd "$(dirname "$0")"
curl -fsSL -H 'User-Agent: fathom-corpus/1.0 (research)' \
  'https://crates.io/api/v1/summary' -o source.json
ls -l source.json
