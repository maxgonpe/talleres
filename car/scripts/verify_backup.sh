#!/usr/bin/env bash
set -euo pipefail

ARCHIVE="${1:?Uso: verify_backup.sh backup.tar.gz}"
CHECKSUM="$ARCHIVE.sha256"
sha256sum -c "$CHECKSUM"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT
tar -xzf "$ARCHIVE" -C "$TMP_DIR"
(cd "$TMP_DIR" && sha256sum -c MANIFEST.sha256)
printf 'Backup verificado correctamente: %s\n' "$ARCHIVE"
