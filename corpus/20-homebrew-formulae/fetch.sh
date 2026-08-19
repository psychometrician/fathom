#!/usr/bin/env bash
# Homebrew's whole formula index, as its API serves it.
#
# 29.6 MB, which is past the ~5 MB rule in CLAUDE.md, so this script is
# committed and `source.json` is not. The file changes whenever a formula is
# updated, so the copy measured on the day is the specimen rather than the
# endpoint; NOTES.md records what it looked like.
set -euo pipefail
cd "$(dirname "$0")"
curl -fsSL https://formulae.brew.sh/api/formula.json -o source.json
ls -l source.json
