#!/usr/bin/env bash
# One page of Crossref's works index, as its public API serves it.
#
# Crossref is the DOI registration agency for scholarly publishing; this is the
# metadata its members deposit, served back unmodified. `rows=1000` is the
# API's maximum page size.
#
# The endpoint is a live index and its first page changes constantly, so the
# copy measured on the day is the specimen rather than the URL. NOTES.md records
# what it looked like. Anonymous requests go to Crossref's public pool; no key,
# no auth, no personal identifier is sent.
set -euo pipefail
cd "$(dirname "$0")"
curl -fsSL 'https://api.crossref.org/works?rows=1000' -o source.json
ls -l source.json
