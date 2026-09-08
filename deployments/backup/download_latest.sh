#!/bin/bash
set -eo pipefail

# ==============================================================================
# Plane Civix - Tool tai ban Backup PostgreSQL moi nhat tu VPS ve may ca nhan
# ==============================================================================

VPS_HOST="${1:-}"
DEST_DIR="${2:-./backup_downloads}"

if [ -z "$VPS_HOST" ]; then
    read -rp "Nhap dia chi SSH VPS (vi du: root@103.x.x.x): " VPS_HOST
fi

mkdir -p "$DEST_DIR"

echo "================================================================="
echo "       PLANE CIVIX - DOWNLOAD LATEST BACKUP WIZARD"
echo "================================================================="
echo "[...] Dang truy van tim ban backup moi nhat tren VPS ($VPS_HOST)..."

REMOTE_FILE=$(ssh "$VPS_HOST" "ls -t ~/plane-backups/data/plane_backup_*.sql.gz 2>/dev/null | head -n 1")

if [ -z "$REMOTE_FILE" ]; then
    echo "[x] Khong tim thay ban backup nao trong ~/plane-backups/data/ tren VPS!"
    exit 1
fi

FILE_NAME=$(basename "$REMOTE_FILE")
echo "[v] Da tim thay ban backup moi nhat: $FILE_NAME"
echo "[...] Dang tai ve: $DEST_DIR/$FILE_NAME ..."

scp "${VPS_HOST}:${REMOTE_FILE}" "$DEST_DIR/"

echo ""
echo ">>> TAI THANH CONG BAN BACKUP MOI NHAT!"
echo "- Vi tri file: $DEST_DIR/$FILE_NAME"
echo "================================================================="
