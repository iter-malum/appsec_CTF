#!/bin/sh
set -eu

mkdir -p /data/uploads /data/uploads/reports /data/uploads/sources
chown -R app:app /data/uploads

export SECRET_KEY="$(cat /secrets/secret_key)"
export ADMIN_USERNAME="${ADMIN_USERNAME:-admin-ussc}"
export ADMIN_PASSWORD="$(cat /secrets/admin_password)"
export POSTGRES_PASSWORD="$(cat /secrets/postgres_password)"

if [ -z "${DATABASE_URL:-}" ]; then
  export DATABASE_URL="postgresql+psycopg://${POSTGRES_USER:-appsec}:${POSTGRES_PASSWORD}@${POSTGRES_HOST:-db}:5432/${POSTGRES_DB:-appsec_ctf}"
fi

echo "[api] starting uvicorn as user app (admin=${ADMIN_USERNAME})"
exec gosu app uvicorn app.main:app --host 0.0.0.0 --port 8000
