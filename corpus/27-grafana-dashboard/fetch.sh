#!/bin/sh
# Grafana dashboard 1860, "Node Exporter Full", revision 37 — fetched 2026-08-12.
# One of the most-installed dashboards in existence, exported the way the
# grafana.com library serves it, which is the form a person actually receives.
set -e
curl -sS -o source.json \
  "https://grafana.com/api/dashboards/1860/revisions/37/download"
