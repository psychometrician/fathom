#!/bin/sh
# 13 — Visual Studio Code's package-lock.json. Fetched 2026-08-09.
#
# 777,210 bytes, lockfileVersion 3, 1,657 entries under `packages`. Chosen from
# four candidates; the other three repos do not commit a package-lock.json at
# that path and returned 404, so this was the only real lockfile available from
# a project of the size wanted.
#
# Committed: under the 5 MB threshold. `main` moves, so the bytes are not
# reproducible and NOTES.md records the file as it was on the day.
curl -s 'https://raw.githubusercontent.com/microsoft/vscode/main/package-lock.json' -o source.json
