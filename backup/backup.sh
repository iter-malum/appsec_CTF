#!/bin/sh
set -eu

apk add --no-cache dcron >/dev/null 2>&1 || true

BACKUP_DIR=/backups
KEEP_DAYS="${BACKUP_KEEP_DAYS:-14}"
CRON_EXPR="${BACKUP_CRON:-0 3 * * *}"

mkdir -p "$BACKUP_DIR"

run_backup() {
  STAMP=$(date -u +%Y%m%d_%H%M%S)
  FILE="$BACKUP_DIR/appsec_ctf_${STAMP}.sql.gz"
  echo "[backup] starting $FILE"
  PGPASSWORD="$POSTGRES_PASSWORD" pg_dump -h "$PGHOST" -U "$POSTGRES_USER" -d "$POSTGRES_DB" | gzip > "$FILE"
  echo "[backup] done $(du -h "$FILE" | awk '{print $1}')"
  find "$BACKUP_DIR" -name 'appsec_ctf_*.sql.gz' -mtime +"$KEEP_DAYS" -delete 2>/dev/null || true
}

# Immediate backup on start
run_backup

echo "$CRON_EXPR /bin/sh -c 'PGPASSWORD=\"$POSTGRES_PASSWORD\" pg_dump -h $PGHOST -U $POSTGRES_USER -d $POSTGRES_DB | gzip > $BACKUP_DIR/appsec_ctf_\$(date -u +\%Y\%m\%d_\%H\%M\%S).sql.gz; find $BACKUP_DIR -name \"appsec_ctf_*.sql.gz\" -mtime +$KEEP_DAYS -delete'" > /etc/crontabs/root

echo "[backup] cron installed: $CRON_EXPR"
crond -f -l 8
