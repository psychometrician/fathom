#!/usr/bin/env bash
# One page of Docker Hub's tag list for the official Python image.
#
# A container registry's own catalogue output: one object per tag, each holding
# an `images` array with one entry per architecture the tag was built for.
# Public repository, no auth, no key.
#
# The endpoint is a live catalogue and its first page changes whenever an image
# is pushed, so the copy measured on the day is the specimen rather than the
# URL. NOTES.md records what it looked like.
set -euo pipefail
cd "$(dirname "$0")"
curl -fsSL 'https://hub.docker.com/v2/repositories/library/python/tags?page_size=100' -o source.json
ls -l source.json
