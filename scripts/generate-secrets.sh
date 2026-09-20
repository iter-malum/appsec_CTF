#!/bin/sh
set -eu

DIR=/secrets
mkdir -p "$DIR"

rand() {
  # portable-ish random alnum
  dd if=/dev/urandom bs=48 count=1 2>/dev/null | tr -dc 'A-Za-z0-9' | head -c "$1"
}

CREATED=0

if [ ! -f "$DIR/postgres_password" ]; then
  rand 32 > "$DIR/postgres_password"
  CREATED=1
fi

if [ ! -f "$DIR/secret_key" ]; then
  rand 64 > "$DIR/secret_key"
  CREATED=1
fi

if [ ! -f "$DIR/admin_password" ]; then
  rand 24 > "$DIR/admin_password"
  CREATED=1
fi

chmod 444 "$DIR/postgres_password" "$DIR/secret_key" "$DIR/admin_password" 2>/dev/null || true

ADMIN_USER="${ADMIN_USERNAME:-admin-ussc}"
ADMIN_PASS=$(cat "$DIR/admin_password")
DB_PASS=$(cat "$DIR/postgres_password")

{
  echo "Admin username: ${ADMIN_USER}"
  echo "Admin password: ${ADMIN_PASS}"
  echo "Postgres password: ${DB_PASS}"
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$DIR/CREDENTIALS.txt"
chmod 444 "$DIR/CREDENTIALS.txt" 2>/dev/null || true

if [ "$CREATED" = "1" ]; then
  echo ""
  echo "============================================================"
  echo " AppSec CTF — FIRST DEPLOY CREDENTIALS (save them now!)"
  echo "============================================================"
  echo " Admin login:       ${ADMIN_USER}"
  echo " Admin password:    ${ADMIN_PASS}"
  echo " Postgres password: ${DB_PASS}"
  echo "------------------------------------------------------------"
  echo " Also saved in Docker volume secrets_data:/secrets/CREDENTIALS.txt"
  echo " View later: docker compose exec api cat /secrets/CREDENTIALS.txt"
  echo "============================================================"
  echo ""
else
  echo "[init-secrets] secrets already present (not regenerated)"
fi
