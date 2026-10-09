#!/bin/bash
set -eo pipefail

# ==============================================================================
# Plane PostgreSQL Interactive Restore Script (Enterprise Hardened)
# Restores a selected snapshot with pre-backup safety and integrity verification.
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

CONTAINER_NAME="plane-db"
DB_USER="${POSTGRES_USER:-plane}"
DB_PASS="${POSTGRES_PASSWORD:-plane}"
DB_NAME="${POSTGRES_DB:-plane}"

echo "================================================================="
echo "       PLANE DATABASE RESTORE WIZARD (KHOI PHUC DU LIEU)"
echo "================================================================="

# Check container running
if ! docker ps --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "[x] LOI: Container '${CONTAINER_NAME}' khong hoat dong!" >&2
    exit 1
fi

# Get last 15 backups sorted by modification time (newest first)
mapfile -t files < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name "plane_backup_*.sql.gz" -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 15 | awk '{print $2}')

if [ ${#files[@]} -eq 0 ]; then
    echo "[x] Chua tim thay ban sao luu nao trong: $BACKUP_DIR"
    echo "    (Moi ban chay 'bash deployments/backup/backup.sh' de tao ban sao luu dau tien)."
    exit 1
fi

echo "Danh sach cac ban sao luu gan nhat:"
echo ""
for i in "${!files[@]}"; do
    fname=$(basename "${files[$i]}")
    fsize=$(du -h "${files[$i]}" | cut -f1)
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
    echo "    (Dung luong: $(du -h "$SELECTED_FILE" | cut -f1) - File: $(basename "$SELECTED_FILE"))"
    read -rp "Ban co chac chan muon khoi phuc? (y/N): " confirm
    
    if [[ ! "$confirm" =~ ^[yY]$ ]]; then
        echo "Da huy thao tac."
        exit 0
    fi

    # Verify backup archive integrity first
    echo "[...] Kiem tra tinh toan ven cua file backup..."
    if ! gzip -t "$SELECTED_FILE"; then
        echo "[x] LOI NGHIEP TRONG: File backup bi loi hoac khong hoan chinh! Khong the khoi phuc." >&2
        exit 1
    fi

    # Create safety pre-restore backup
    echo "[...] Dang tao ban sao luu an toan phong ngua truoc khi restore..."
    bash "$SCRIPT_DIR/backup.sh" || echo "[!] Canh bao: Khong the tao snapshot an toan, tiep tuc restore..."

    echo ""
    echo "[...] Dang khoi phuc du lieu vao database '${DB_NAME}'..."

    # Recreate public schema to ensure clean slate without duplicate key conflicts
    docker exec -e PGPASSWORD="$DB_PASS" "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA IF EXISTS public CASCADE; CREATE SCHEMA public; GRANT ALL ON SCHEMA public TO ${DB_USER};" >/dev/null 2>&1 || true

    # Execute restore with ON_ERROR_STOP=1
    if gunzip -c "$SELECTED_FILE" | docker exec -e PGPASSWORD="$DB_PASS" -i "$CONTAINER_NAME" psql -U "$DB_USER" -d "$DB_NAME" -v ON_ERROR_STOP=1 > /tmp/plane_restore.log 2>&1; then
        echo ""
        echo "================================================================="
        echo ">>> KHOI PHUC DU LIEU THANH CONG 100%!"
        echo ">>> He thong Plane da duoc phuc hoi ve thoi diem ban sao luu."
        echo "================================================================="
    else
        echo ""
        echo "[x] LOI: Qua trinh khoi phuc database gap su co!" >&2
        echo "    Chi tiet loi xem tai /tmp/plane_restore.log hoac log duoi day:" >&2
        tail -n 20 /tmp/plane_restore.log >&2 || true
        exit 1
    fi
else
    echo "[x] Lua chon khong hop le."
    exit 1
fi
