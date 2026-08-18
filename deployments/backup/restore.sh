#!/bin/bash
set -eo pipefail

# ==============================================================================
# Plane PostgreSQL Interactive 1-Click Restore Script
# Restores a selected snapshot into the running plane-db container.
# ==============================================================================

BACKUP_DIR="${BACKUP_DIR:-$HOME/plane-backups/data}"
CONTAINER_NAME="plane-db"
DB_USER="${POSTGRES_USER:-plane}"
DB_NAME="${POSTGRES_DB:-plane}"

if [ ! -d "$BACKUP_DIR" ]; then
    echo "[!] Thu muc backup khong ton tai: $BACKUP_DIR"
    exit 1
fi

echo "================================================================="
echo "       PLANE DATABASE RESTORE WIZARD (KHOI PHUC DU LIEU)"
echo "================================================================="

# Get last 15 backups sorted by modification time (newest first)
mapfile -t files < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name "plane_backup_*.sql.gz" -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 15 | awk '{print $2}')

if [ ${#files[@]} -eq 0 ]; then
    echo "[x] Khong tim thay ban backup nao trong: $BACKUP_DIR"
    exit 1
fi

echo "Danh sach cac ban sao luu gan nhat:"
echo ""
for i in "${!files[@]}"; do
    fname=$(basename "${files[$i]}")
    fsize=$(du -h "${files[$i]}" | cut -f1)
    # Parse timestamp from filename: plane_backup_YYYYMMDD_HHMMSS.sql.gz
    ts_str=$(echo "$fname" | sed -E 's/plane_backup_([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2})\.sql\.gz/\3\/\2\/\1 \4:\5:\6/')
    echo "  [$((i+1))]  $ts_str  ($fsize)  - $fname"
done

echo ""
read -rp "Nhap so thu tu ban sao luu ban muon phuc hoi [1-${#files[@]}] (hoac 'q' de huy): " choice

if [ "$choice" = "q" ] || [ "$choice" = "Q" ]; then
    echo "Da huy bo thao tac."
    exit 0
fi

if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#files[@]}" ]; then
    SELECTED_FILE="${files[$((choice-1))]}"
    echo ""
    echo "[!] CANH BAO: Du lieu hien tai trong Database se duoc ghi de boi ban backup nay!"
    read -rp "Ban co chac chan muon khoi phuc tu $(basename "$SELECTED_FILE")? (y/N): " confirm
    
    if [[ ! "$confirm" =~ ^[yY]$ ]]; then
        echo "Da huy thao tac."
        exit 0
    fi
    
    echo ""
    echo "[...] Dang khoi phuc du lieu vao ${CONTAINER_NAME}..."
    gunzip -c "$SELECTED_FILE" | docker exec -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" > /dev/null 2>&1
    
    echo ""
    echo "================================================================="
    echo ">>> KHOI PHUC DU LIEU THANH CONG 100%!"
    echo ">>> He thong Plane da duoc phuc hoi ve thoi diem ban sao luu."
    echo "================================================================="
else
    echo "[x] Lua chon khong hop le."
    exit 1
fi
