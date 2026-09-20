#!/bin/sh
set -eu

DIR=/secrets
mkdir -p "$DIR"

# Exactly N alphanumeric chars (need surplus entropy after filtering)
rand() {
  n="$1"
  dd if=/dev/urandom bs=$((n * 8)) count=1 2>/dev/null | tr -dc 'A-Za-z0-9' | head -c "$n"
  echo
}

ensure_secret() {
  name="$1"
  len="$2"
  min="$3"
  if [ ! -f "$DIR/$name" ]; then
    rand "$len" > "$DIR/$name"
    echo "[init-secrets] created $name"
    return 0
  fi
  cur=$(tr -d '\n' < "$DIR/$name" | wc -c | tr -d ' ')
  if [ "$cur" -lt "$min" ]; then
    rand "$len" > "$DIR/$name"
    echo "[init-secrets] regenerated short $name (was $cur)"
    return 0
  fi
  return 1
}

CREATED=0
ensure_secret postgres_password 32 16 && CREATED=1 || true
ensure_secret secret_key 64 32 && CREATED=1 || true
ensure_secret admin_password 24 16 && CREATED=1 || true

chmod 444 "$DIR/postgres_password" "$DIR/secret_key" "$DIR/admin_password" 2>/dev/null || true

ADMIN_USER="${ADMIN_USERNAME:-admin-ussc}"
ADMIN_PASS=$(tr -d '\n' < "$DIR/admin_password")
DB_PASS=$(tr -d '\n' < "$DIR/postgres_password")

{
  echo "Admin username: ${ADMIN_USER}"
  echo "Admin password: ${ADMIN_PASS}"
  echo "Postgres password: ${DB_PASS}"
  echo "UI: http://<SERVER_IP>:3000"
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date)"
} > "$DIR/CREDENTIALS.txt"
chmod 444 "$DIR/CREDENTIALS.txt" 2>/dev/null || true

if [ "$CREATED" = "1" ]; then
  echo ""
  echo "============================================================"
  echo " AppSec CTF — FIRST DEPLOY CREDENTIALS (save them!)"
  echo "============================================================"
  echo " Admin login:       ${ADMIN_USER}"
  echo " Admin password:    ${ADMIN_PASS}"
  echo " Postgres password: ${DB_PASS}"
  echo " Open UI:           http://<SERVER_IP>:3000"
  echo " Later: docker compose exec api cat /secrets/CREDENTIALS.txt"
  echo "============================================================"
  echo ""
else
  echo "[init-secrets] secrets OK (not regenerated)"
  echo "[init-secrets] admin: ${ADMIN_USER}"
fi
