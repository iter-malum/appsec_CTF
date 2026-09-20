#!/bin/sh
set -eu

export PGPASSWORD="$(cat /secrets/postgres_password)"
export POSTGRES_PASSWORD="$PGPASSWORD"

exec /bin/sh /tmp/backup.sh
