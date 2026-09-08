#!/bin/bash
set -eo pipefail

# ==============================================================================
# Plane Civix - Menu Chon Ban Backup De Lay Link Tai (Tu Dong Huy Sau 1 Gio)
# ==============================================================================

BACKUP_DIR="${BACKUP_DIR:-$HOME/plane-backups/data}"
mkdir -p "$BACKUP_DIR"

echo "================================================================="
echo "       PLANE DATABASE BACKUP DOWNLOAD LINK WIZARD"
echo "================================================================="

# Get last 15 backups sorted by modification time (newest first)
mapfile -t files < <(find "$BACKUP_DIR" -maxdepth 1 -type f -name "plane_backup_*.sql.gz" -printf "%T@ %p\n" 2>/dev/null | sort -nr | head -n 15 | awk '{print $2}')

if [ ${#files[@]} -eq 0 ]; then
    echo "[x] Chua tim thay ban sao luu nao trong: $BACKUP_DIR"
    echo "    (Moi ban chay 'bash deployments/backup/backup.sh' de tao ban sao luu dau tien)."
    exit 1
fi

echo "Danh sach cac ban sao luu san co tren he thong:"
echo ""
for i in "${!files[@]}"; do
    fname=$(basename "${files[$i]}")
    fsize=$(du -h "${files[$i]}" | cut -f1)
    # Parse timestamp from filename: plane_backup_YYYYMMDD_HHMMSS.sql.gz
    ts_str=$(echo "$fname" | sed -E 's/plane_backup_([0-9]{4})([0-9]{2})([0-9]{2})_([0-9]{2})([0-9]{2})([0-9]{2})\.sql\.gz/\3\/\2\/\1 \4:\5:\6/')
    if [ "$i" -eq 0 ]; then
        echo "  [$((i+1))]  $ts_str  ($fsize)  - $fname  [MOI NHAT]"
    else
        echo "  [$((i+1))]  $ts_str  ($fsize)  - $fname"
    fi
done

echo ""
read -rp "Nhap so thu tu ban muon lay link tai [1-${#files[@]}] (Mac dinh: [1] - Moi nhat, 'q' de huy): " choice

choice="${choice:-1}"

if [ "$choice" = "q" ] || [ "$choice" = "Q" ]; then
    echo "Da huy thao tac."
    exit 0
fi

if [[ "$choice" =~ ^[0-9]+$ ]] && [ "$choice" -ge 1 ] && [ "$choice" -le "${#files[@]}" ]; then
    SELECTED_FILE="${files[$((choice-1))]}"
    SELECTED_NAME=$(basename "$SELECTED_FILE")
    SELECTED_SIZE=$(du -h "$SELECTED_FILE" | cut -f1)

    echo ""
    echo "- Da chon: $SELECTED_NAME ($SELECTED_SIZE)"
    echo "- Che do: Tu dong huy link sau 1 gio de bao mat du lieu"
    echo "[...] Dang tao link tai an toan..."

    # Upload to Litterbox with 1 hour expiration and strip trailing newlines/percent
    UPLOAD_URL=$(curl -s -F "reqtype=fileupload" -F "time=1h" -F "fileToUpload=@$SELECTED_FILE" https://litterbox.catbox.moe/resources/internals/api.php | tr -d '\r\n% ')

    if [[ "$UPLOAD_URL" =~ ^https://litter\.catbox\.moe/ ]]; then
        echo ""
        echo "================================================================="
        echo ">>> LINK TAI CUA BAN (Copy dan thang vao trinh duyet tren may):"
        echo ""
        echo "    $UPLOAD_URL"
        echo ""
        echo "- Link nay se tu dong het han va bi xoa vinh vien sau 60 phut."
        echo "================================================================="
    else
        echo "[x] Co loi khi tao link tai. Vui long thu lai."
        exit 1
    fi
else
    echo "[x] Lua chon khong hop le: $choice"
    exit 1
fi
