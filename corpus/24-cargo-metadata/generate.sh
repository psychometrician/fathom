#!/usr/bin/env bash
# `cargo metadata` for this workspace — a build tool's own view of itself.
#
# NOT a fetch. This is the corpus's first entry written by a tool on this
# machine rather than served by an endpoint, which is what `corpus/README.md`
# asks for and what files 21, 22 and 23 all departed from.
#
# It is therefore reproducible in a way no other entry is: same toolchain, same
# Cargo.lock, same bytes. NOTES.md records the versions it was generated with,
# because a different rustc or a changed lockfile will produce a different
# document and the specimen is the one measured on the day.
set -euo pipefail
cd "$(dirname "$0")"
cargo metadata --format-version 1 --manifest-path ../../Cargo.toml > source.json
ls -l source.json
