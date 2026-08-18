#!/bin/bash
set -euo pipefail

# ==============================================================================
# Plane Automated Backup Cron Installer
# Sets up a 5-minute recurring backup cron job in crontab.
# ==============================================================================

INTERVAL_MINUTES="${1:-5}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_SCRIPT="$SCRIPT_DIR/backup.sh"

chmod +x "$SCRIPT_DIR/backup.sh"
chmod +x "$SCRIPT_DIR/restore.sh"

CRON_CMD="*/${INTERVAL_MINUTES} * * * * /bin/bash ${BACKUP_SCRIPT} > /dev/null 2>&1"
CRON_COMMENT="# Plane Database Automated 5-Min Backup"

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
