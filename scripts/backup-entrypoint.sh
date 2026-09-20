#!/bin/sh
set -eu
export PGPASSWORD="$(tr -d '\n' < /secrets/postgres_password)"
export POSTGRES_PASSWORD="$PGPASSWORD"
exec /bin/sh /tmp/backup.sh
