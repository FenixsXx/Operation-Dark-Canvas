#!/bin/sh
set -eu

BASE_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)
DB_PATH=${DARK_CANVAS_DB:-"$BASE_DIR/dark_canvas.sqlite3"}
BACKUP_DIR=${DARK_CANVAS_BACKUP_DIR:-"$BASE_DIR/backup_db"}
STAMP=$(date -u +%Y%m%dT%H%M%SZ)

mkdir -p "$BACKUP_DIR"
sqlite3 "$DB_PATH" ".backup '$BACKUP_DIR/dark_canvas_$STAMP.sqlite3'"
find "$BACKUP_DIR" -type f -name 'dark_canvas_*.sqlite3' -mtime +7 -delete