#!/bin/bash
set -euo pipefail

# ==============================================================================
# Plane Automated Backup Cron Installer
# Sets up a 5-minute recurring backup cron job in crontab.
# ==============================================================================

INTERVAL_MINUTES="${1:-60}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"

chmod +x "$SCRIPT_DIR/backup.sh"
chmod +x "$SCRIPT_DIR/restore.sh"
chmod +x "$SCRIPT_DIR/get_download_link.sh"

if [ "$INTERVAL_MINUTES" -ge 60 ]; then
    INTERVAL_HOURS=$((INTERVAL_MINUTES / 60))
    if [ "$INTERVAL_HOURS" -eq 1 ]; then
        CRON_SCHEDULE="0 * * * *"
    else
        CRON_SCHEDULE="0 */${INTERVAL_HOURS} * * *"
    fi
else
    CRON_SCHEDULE="*/${INTERVAL_MINUTES} * * * *"
fi

CRON_CMD="${CRON_SCHEDULE} /bin/bash ${BACKUP_SCRIPT} > /dev/null 2>&1"
CRON_COMMENT="# Plane Database Automated Hourly/Periodic Backup (30-Day Retention)"

# Remove existing Plane backup cron jobs if any
current_crontab=$(crontab -l 2>/dev/null | grep -v "backup.sh" | grep -v "Plane Database Automated" || true)

# Add new cron job
(
    echo "$current_crontab"
    echo "$CRON_COMMENT"
    echo "$CRON_CMD"
) | crontab -

echo "================================================================="
echo ">>> DA THIET LAP TU DONG SAO LUU THANH CONG!"
echo "- Tan suat sao luu: Moi ${INTERVAL_MINUTES} phut mot lan"
echo "- Vi tri luu tru du lieu: $HOME/plane-backups/data/"
echo "- Lenh sao luu thu cong: bash $SCRIPT_DIR/backup.sh"
echo "- Lenh khoi phuc du lieu: bash $SCRIPT_DIR/restore.sh"
echo "================================================================="
