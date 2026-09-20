#!/bin/sh
set -eu

mkdir -p /data/uploads /data/uploads/reports /data/uploads/sources
chown -R app:app /data/uploads

if [ ! -f /secrets/secret_key ] || [ ! -f /secrets/admin_password ] || [ ! -f /secrets/postgres_password ]; then
  echo "[api] ERROR: secrets missing under /secrets — run init-secrets first"
  ls -la /secrets || true
  exit 1
fi

export SECRET_KEY="$(cat /secrets/secret_key)"
export ADMIN_USERNAME="${ADMIN_USERNAME:-admin-ussc}"
export ADMIN_PASSWORD="$(cat /secrets/admin_password)"
export POSTGRES_PASSWORD="$(cat /secrets/postgres_password)"
export POSTGRES_USER="${POSTGRES_USER:-appsec}"
export POSTGRES_HOST="${POSTGRES_HOST:-db}"
export POSTGRES_DB="${POSTGRES_DB:-appsec_ctf}"

if [ -z "${DATABASE_URL:-}" ]; then
  export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:5432/${POSTGRES_DB}"
fi

echo "[api] waiting for database ${POSTGRES_HOST}:5432 ..."
i=0
while [ "$i" -lt 30 ]; do
  if gosu app python -c "import psycopg; psycopg.connect('host=${POSTGRES_HOST} dbname=${POSTGRES_DB} user=${POSTGRES_USER} password=${POSTGRES_PASSWORD}', connect_timeout=3).close()" 2>/tmp/db_err; then
    echo "[api] database is ready"
    break
  fi
  i=$((i + 1))
  if [ "$i" -eq 30 ]; then
    echo "[api] ERROR: cannot connect to database after 30 attempts"
    echo "[api] Often caused by OLD postgres volume + NEW secrets password."
    echo "[api] Fix: docker compose down && docker volume rm <project>_postgres_data <project>_secrets_data && docker compose up -d --build"
    cat /tmp/db_err || true
    exit 1
  fi
  sleep 2
done

echo "[api] starting uvicorn as user app (admin=${ADMIN_USERNAME})"
exec gosu app uvicorn app.main:app --host 0.0.0.0 --port 8000
