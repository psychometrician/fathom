#!/bin/sh
# 06 — ESPN NFL Quarterback Rating, 2019 season. Fetched 2026-08-09.
#
# The endpoint from Tom Mock, "Parsing JSON in R with jsonlite",
# themockup.blog, 2020-05-22. Committed rather than fetched at read time:
# 180 KB is well under the corpus threshold, and an endpoint that has already
# changed its row count from 30 to 28 will keep changing.
curl -s 'https://site.web.api.espn.com/apis/fitt/v3/sports/football/nfl/qbr?region=us&lang=en&qbrType=seasons&seasontype=2&isqualified=true&sort=schedAdjQBR%3Adesc&season=2019' -o source.json
