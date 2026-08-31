#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$ROOT_DIR/backups}"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
WORK_DIR="$BACKUP_DIR/.work-$STAMP"
ARCHIVE="$BACKUP_DIR/talleres-$STAMP.tar.gz"

mkdir -p "$WORK_DIR/db" "$WORK_DIR/media"
trap 'rm -rf "$WORK_DIR"' EXIT

if [[ "${DB_ENGINE:-django.db.backends.sqlite3}" == *postgresql* ]]; then
  : "${DB_NAME:?DB_NAME es obligatorio para PostgreSQL}"
  pg_dump --format=custom --file="$WORK_DIR/db/database.dump" "$DB_NAME"
else
  if command -v sqlite3 >/dev/null 2>&1; then
    sqlite3 "${DB_NAME:-$ROOT_DIR/db.sqlite3}" ".backup '$WORK_DIR/db/database.sqlite3'"
  else
    PYTHON_BIN="${PYTHON_BIN:-$ROOT_DIR/../env/bin/python}"
    "$PYTHON_BIN" "$ROOT_DIR/manage.py" dumpdata --natural-foreign --natural-primary \
      --exclude auth.permission --exclude contenttypes \
      --indent 2 > "$WORK_DIR/db/fixture.json"
  fi
fi

if [[ -d "$ROOT_DIR/media" ]]; then
  cp -a "$ROOT_DIR/media/." "$WORK_DIR/media/"
fi
(cd "$WORK_DIR" && find . -type f ! -name MANIFEST.sha256 -print0 | sort -z | xargs -0 sha256sum > MANIFEST.sha256)
tar -czf "$ARCHIVE" -C "$WORK_DIR" .
sha256sum "$ARCHIVE" > "$ARCHIVE.sha256"
printf 'Backup creado: %s\n' "$ARCHIVE"
