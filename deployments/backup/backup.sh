#!/bin/bash
set -euo pipefail

# ==============================================================================
# Plane PostgreSQL Automated Backup Script
# Creates compressed timestamped snapshots and prunes old backups.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${BACKUP_DIR:-$HOME/plane-backups/data}"
mkdir -p "$BACKUP_DIR"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/plane_backup_${TIMESTAMP}.sql.gz"

CONTAINER_NAME="plane-db"
DB_USER="${POSTGRES_USER:-plane}"
DB_PASS="${POSTGRES_PASSWORD:-plane}"
DB_NAME="${POSTGRES_DB:-plane}"

# 1. Verify container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[$(date)] ERROR: Docker container '${CONTAINER_NAME}' is not running!" >&2
    exit 1
fi

# 2. Perform Database Dump with Gzip Compression
echo "[$(date)] Starting backup for database '${DB_NAME}'..."
if docker exec -e PGPASSWORD="$DB_PASS" "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$BACKUP_FILE"; then
    FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
    echo "[$(date)] Backup SUCCESS: ${BACKUP_FILE} (${FILE_SIZE})"
else
    echo "[$(date)] ERROR: Backup failed!" >&2
    rm -f "$BACKUP_FILE"
    exit 1
fi

# 3. Retention Policy: Remove backups older than 3 days to protect VPS disk space
find "$BACKUP_DIR" -type f -name "plane_backup_*.sql.gz" -mtime +3 -delete
