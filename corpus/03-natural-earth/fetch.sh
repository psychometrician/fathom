#!/bin/sh
# 03 — Natural Earth 1:50m admin-0 countries, as GeoJSON. Fetched 2026-08-08.
#
# Natural Earth is public domain. This copy is served by geojson.xyz, which
# republishes the 3.3.0 shapefiles as GeoJSON so that no conversion step stands
# between the endpoint and the document — the file is what somebody downloads.
curl -sL https://d2ad6b4ur7yvpq.cloudfront.net/naturalearth-3.3.0/ne_50m_admin_0_countries.geojson \
     -o source.json
