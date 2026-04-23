#!/usr/bin/env bash
set -euo pipefail
SNAP_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -a "$SNAP_DIR/runtime/upload-web.bin" /opt/cpgj/exports/upload-web.bin 2>/dev/null || true
cp -a "$SNAP_DIR/exports/indicator_preview.json" /opt/cpgj/exports/indicator_preview.json 2>/dev/null || true
cp -a "$SNAP_DIR/exports/indicator_detail_preview.json" /opt/cpgj/exports/indicator_detail_preview.json 2>/dev/null || true
docker cp /opt/cpgj/exports/upload-web.bin cpgj-upload-web:/upload-web
docker restart cpgj-upload-web
sleep 1
docker ps --filter name=cpgj-upload-web --format '{{.Names}}|{{.Status}}'
