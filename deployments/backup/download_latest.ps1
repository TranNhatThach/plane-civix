# ==============================================================================
# Plane Civix - Tool tai ban Backup PostgreSQL moi nhat tu VPS ve may ca nhan
# ==============================================================================
param(
    [string]$VpsHost = "",
    [string]$DestDir = $(if (Test-Path "D:\") { "D:\Backup" } else { ".\backups" })
)

if (-not $VpsHost) {
    $VpsHost = Read-Host "Nhap dia chi SSH VPS (vi du: root@103.x.x.x)"
}

if (-not (Test-Path $DestDir)) {
    New-Item -ItemType Directory -Force -Path $DestDir | Out-Null
}

Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "       PLANE CIVIX - DOWNLOAD LATEST BACKUP WIZARD" -ForegroundColor Cyan
Write-Host "=================================================================" -ForegroundColor Cyan
Write-Host "[...] Dang truy van tim ban backup moi nhat tren VPS ($VpsHost)..."

# Run ssh with quiet flag and filter strictly for the backup filename to ignore any VPS login banners/MOTD
$rawOutput = ssh -q $VpsHost "ls -t ~/plane-backups/data/plane_backup_*.sql.gz 2>/dev/null | grep 'plane_backup_.*\.sql\.gz' | head -n 1"
$remoteFile = if ($rawOutput) { $rawOutput.ToString().Trim() } else { "" }

if (-not $remoteFile -or -not ($remoteFile -match "plane_backup_.*\.sql\.gz")) {
    Write-Host "[x] Khong tim thay ban backup nao trong ~/plane-backups/data/ tren VPS!" -ForegroundColor Red
    Write-Host "    (Hay chac chan rang VPS da tao it nhat 1 ban backup trong ~/plane-backups/data/)." -ForegroundColor Yellow
    exit 1
}

$fileName = Split-Path $remoteFile -Leaf
Write-Host "[v] Da tim thay ban backup moi nhat: $fileName" -ForegroundColor Green
Write-Host "[...] Dang tai ve thu muc: $DestDir\$fileName ..." -ForegroundColor Yellow

scp "${VpsHost}:${remoteFile}" "$DestDir\"

if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Write-Host ">>> TAI THANH CONG BAN BACKUP MOI NHAT!" -ForegroundColor Green
    Write-Host "- Vi tri file: $DestDir\$fileName" -ForegroundColor Green
    Write-Host "=================================================================" -ForegroundColor Cyan
} else {
    Write-Host "[x] Tai that bai. Vui long kiem tra lai ket noi SSH den VPS." -ForegroundColor Red
}
