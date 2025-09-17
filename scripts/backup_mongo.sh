#!/usr/bin/env bash
set -euo pipefail
STAMP="$(date +%Y%m%d_%H%M%S)"
OUT="~/Projects/ProPlus/backups/mongodump_$STAMP"
mongodump --host 127.0.0.1 --port 27017 --out "$OUT"
# Սեղմում (ըստ ցանկության)
tar -C "$(dirname "$OUT")" -czf "${OUT}.tar.gz" "$(basename "$OUT")"
rm -rf "$OUT"
