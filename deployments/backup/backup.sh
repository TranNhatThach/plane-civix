#!/bin/bash
set -euo pipefail

# ==============================================================================
# Plane PostgreSQL Automated Backup Script (Enterprise Hardened)
# Creates compressed timestamped snapshots and prunes old backups.
# ==============================================================================

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Load environment configuration if available
if [ -f "$REPO_ROOT/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    source <(grep -v '^#' "$REPO_ROOT/.env" | grep '=' | sed -e 's/\r$//') 2>/dev/null || true
    set +a
fi
if [ -f "$REPO_ROOT/apps/api/.env" ]; then
    set -a
    # shellcheck disable=SC1090
    source <(grep -v '^#' "$REPO_ROOT/apps/api/.env" | grep '=' | sed -e 's/\r$//') 2>/dev/null || true
    set +a
fi

BACKUP_DIR="${BACKUP_DIR:-$HOME/plane-backups/data}"
mkdir -p "$BACKUP_DIR"

# Prevent concurrent backup execution
LOCK_FILE="/tmp/plane_backup.lock"
exec 200>"$LOCK_FILE"
if command -v flock >/dev/null 2>&1; then
    if ! flock -n 200; then
        echo "[$(date)] INFO: Another backup process is currently running. Exiting."
        exit 0
    fi
fi

SHARE_LINK=false
for arg in "$@"; do
    case $arg in
        --link|-l|--share|-s)
            SHARE_LINK=true
            ;;
    esac
done

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/plane_backup_${TIMESTAMP}.sql.gz"
TEMP_BACKUP_FILE="${BACKUP_FILE}.tmp"

CONTAINER_NAME="plane-db"
DB_USER="${POSTGRES_USER:-plane}"
DB_PASS="${POSTGRES_PASSWORD:-plane}"
DB_NAME="${POSTGRES_DB:-plane}"
RETENTION_DAYS="${RETENTION_DAYS:-30}"

# 1. Verify container is running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[$(date)] ERROR: Docker container '${CONTAINER_NAME}' is not running!" >&2
    exit 1
fi

# 2. Perform Database Dump with Gzip Compression to temporary file
echo "[$(date)] Starting backup for database '${DB_NAME}'..."
if docker exec -e PGPASSWORD="$DB_PASS" "$CONTAINER_NAME" pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$TEMP_BACKUP_FILE"; then
    # Verify archive integrity
    if gzip -t "$TEMP_BACKUP_FILE" 2>/dev/null; then
        mv "$TEMP_BACKUP_FILE" "$BACKUP_FILE"
        FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
        echo "[$(date)] Backup SUCCESS: ${BACKUP_FILE} (${FILE_SIZE})"
    else
        echo "[$(date)] ERROR: Backup file failed gzip verification!" >&2
        rm -f "$TEMP_BACKUP_FILE"
        exit 1
    fi
else
    echo "[$(date)] ERROR: Database dump failed!" >&2
    rm -f "$TEMP_BACKUP_FILE"
    exit 1
fi

# 3. Retention Policy: Remove backups older than RETENTION_DAYS to protect VPS disk space
echo "[$(date)] Pruning backups older than ${RETENTION_DAYS} days..."
find "$BACKUP_DIR" -type f -name "plane_backup_*.sql.gz" -mtime +"$RETENTION_DAYS" -delete

if [ "$SHARE_LINK" = true ]; then
    echo ""
    bash "$SCRIPT_DIR/get_download_link.sh"
fi
