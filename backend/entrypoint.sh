#!/bin/sh
set -eu

mkdir -p /data/uploads /data/uploads/reports /data/uploads/sources
chown -R app:app /data/uploads

for f in secret_key admin_password postgres_password; do
  if [ ! -f "/secrets/$f" ]; then
    echo "[api] ERROR: missing /secrets/$f — start init-secrets first"
    exit 1
  fi
done

export SECRET_KEY="$(tr -d '\n' < /secrets/secret_key)"
export ADMIN_USERNAME="${ADMIN_USERNAME:-admin-ussc}"
export ADMIN_PASSWORD="$(tr -d '\n' < /secrets/admin_password)"
export POSTGRES_PASSWORD="$(tr -d '\n' < /secrets/postgres_password)"
export POSTGRES_USER="${POSTGRES_USER:-appsec}"
export POSTGRES_HOST="${POSTGRES_HOST:-db}"
export POSTGRES_DB="${POSTGRES_DB:-appsec_ctf}"
export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}"

echo "[api] waiting for database..."
i=0
while [ "$i" -lt 30 ]; do
  if gosu app python -c "import psycopg; psycopg.connect(host='${POSTGRES_HOST}', dbname='${POSTGRES_DB}', user='${POSTGRES_USER}', password='${POSTGRES_PASSWORD}', connect_timeout=3).close()" 2>/tmp/db_err; then
    echo "[api] database ready"
    break
  fi
  i=$((i + 1))
  if [ "$i" -eq 30 ]; then
    echo "[api] DB connect failed. If you rotated secrets, reset postgres volume:"
    echo "  docker compose down && docker volume rm \$(docker volume ls -q | grep postgres_data)"
    cat /tmp/db_err || true
    exit 1
  fi
  sleep 2
done

echo "[api] starting (admin=${ADMIN_USERNAME})"
exec gosu app uvicorn app.main:app --host 0.0.0.0 --port 8000
