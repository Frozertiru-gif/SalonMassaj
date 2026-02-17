#!/usr/bin/env bash
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/app/backups}"
RETENTION_KEEP="${RETENTION_KEEP:-7}"
DATABASE_URL="${DATABASE_URL:-}"
BACKUP_PASSPHRASE="${BACKUP_PASSPHRASE:-}"

if [[ -z "$DATABASE_URL" ]]; then
  echo "DATABASE_URL is required" >&2
  exit 1
fi

if [[ -z "$BACKUP_PASSPHRASE" ]]; then
  echo "BACKUP_PASSPHRASE is required" >&2
  exit 1
fi

mkdir -p "$BACKUP_DIR"

readarray -t DB_PARTS < <(python - <<'PY'
import os
from urllib.parse import unquote, urlparse

url = os.environ["DATABASE_URL"]
parsed = urlparse(url)
if parsed.scheme.startswith("postgresql+"):
    parsed = parsed._replace(scheme=parsed.scheme.split("+", 1)[0])

host = parsed.hostname or "localhost"
port = str(parsed.port or 5432)
user = unquote(parsed.username or "postgres")
password = unquote(parsed.password or "")
name = (parsed.path or "/").lstrip("/")
if not name:
    raise SystemExit("Database name is missing in DATABASE_URL")
print(host)
print(port)
print(name)
print(user)
print(password)
PY
)

DB_HOST="${DB_PARTS[0]}"
DB_PORT="${DB_PARTS[1]}"
DB_NAME="${DB_PARTS[2]}"
DB_USER="${DB_PARTS[3]}"
DB_PASSWORD="${DB_PARTS[4]}"

TIMESTAMP="$(date -u +%Y%m%d_%H%M%S)"
BASENAME="${DB_NAME}_${TIMESTAMP}.dump.gpg"
TARGET_PATH="$BACKUP_DIR/$BASENAME"

export PGPASSWORD="$DB_PASSWORD"
pg_dump \
  -h "$DB_HOST" \
  -p "$DB_PORT" \
  -U "$DB_USER" \
  -d "$DB_NAME" \
  -Fc \
| gpg --batch --yes --symmetric --cipher-algo AES256 --pinentry-mode loopback --passphrase "$BACKUP_PASSPHRASE" -o "$TARGET_PATH"
unset PGPASSWORD

SIZE_BYTES="$(wc -c < "$TARGET_PATH" | tr -d ' ')"
CREATED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"

cat > "$BACKUP_DIR/last_backup.json" <<JSON
{
  "filename": "$BASENAME",
  "path": "$TARGET_PATH",
  "created_at": "$CREATED_AT",
  "size_bytes": $SIZE_BYTES
}
JSON

if [[ "$RETENTION_KEEP" =~ ^[0-9]+$ ]] && (( RETENTION_KEEP > 0 )); then
  mapfile -t FILES < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name '*.dump.gpg' -printf '%f\n' | sort -r)
  if (( ${#FILES[@]} > RETENTION_KEEP )); then
    for old_file in "${FILES[@]:RETENTION_KEEP}"; do
      rm -f "$BACKUP_DIR/$old_file"
    done
  fi
fi

echo "$TARGET_PATH"
