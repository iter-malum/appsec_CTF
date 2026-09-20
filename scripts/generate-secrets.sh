#!/bin/sh
set -eu

DIR=/secrets
mkdir -p "$DIR"

# Generate exactly N alphanumeric chars (need enough entropy input after filtering)
rand() {
  n="$1"
  # ~1/4 of random bytes are alnum → request 8x bytes
  dd if=/dev/urandom bs=$((n * 8)) count=1 2>/dev/null | tr -dc 'A-Za-z0-9' | head -c "$n"
  echo
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

# Re-generate if an older short key was written by the buggy generator
if [ -f "$DIR/secret_key" ]; then
  KEY_LEN=$(wc -c < "$DIR/secret_key" | tr -d ' \n')
  # strip trailing newline for length check
  KEY_LEN=$(tr -d '\n' < "$DIR/secret_key" | wc -c | tr -d ' ')
  if [ "$KEY_LEN" -lt 24 ]; then
    echo "[init-secrets] secret_key too short ($KEY_LEN) — regenerating"
    rand 64 > "$DIR/secret_key"
    CREATED=1
  fi
fi

if [ ! -f "$DIR/admin_password" ]; then
  rand 24 > "$DIR/admin_password"
  CREATED=1
fi

# Ensure admin password also long enough
if [ -f "$DIR/admin_password" ]; then
  AP_LEN=$(tr -d '\n' < "$DIR/admin_password" | wc -c | tr -d ' ')
  if [ "$AP_LEN" -lt 12 ]; then
    echo "[init-secrets] admin_password too short ($AP_LEN) — regenerating"
    rand 24 > "$DIR/admin_password"
    CREATED=1
  fi
fi

chmod 444 "$DIR/postgres_password" "$DIR/secret_key" "$DIR/admin_password" 2>/dev/null || true

ADMIN_USER="${ADMIN_USERNAME:-admin-ussc}"
ADMIN_PASS=$(tr -d '\n' < "$DIR/admin_password")
DB_PASS=$(tr -d '\n' < "$DIR/postgres_password")

{
  echo "Admin username: ${ADMIN_USER}"
  echo "Admin password: ${ADMIN_PASS}"
  echo "Postgres password: ${DB_PASS}"
  echo "Generated at: $(date -u +%Y-%m-%dT%H:%M:%SZ 2>/dev/null || date)"
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
  echo " Also saved in volume secrets_data:/secrets/CREDENTIALS.txt"
  echo " View later: docker compose exec api cat /secrets/CREDENTIALS.txt"
  echo "============================================================"
  echo ""
else
  echo "[init-secrets] secrets already present (not regenerated)"
  echo "[init-secrets] admin user: ${ADMIN_USER}"
fi
