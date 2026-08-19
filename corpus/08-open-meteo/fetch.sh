#!/bin/sh
# 08 — Open-Meteo hourly forecast, Salt Lake City. Fetched 2026-08-09.
#
# A structural stand-in for the Synoptic Mesonet document in the Reddit thread
# that prompted this entry; Synoptic's demo token returns 403. Free, no auth.
# Committed rather than fetched at read time: 12 KB, and a forecast endpoint
# returns different numbers every hour.
curl -s 'https://api.open-meteo.com/v1/forecast?latitude=40.76&longitude=-111.89&hourly=temperature_2m,wind_speed_10m,wind_direction_10m,relative_humidity_2m&past_days=7&timezone=America%2FDenver' -o source.json
