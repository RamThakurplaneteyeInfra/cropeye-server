# PowerShell script to help configure PostgreSQL for TCP/IP connections
# Run this script as Administrator

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "PostgreSQL Connection Configuration Helper" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if running as Administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "[WARNING] This script should be run as Administrator" -ForegroundColor Yellow
    Write-Host "Right-click PowerShell and select 'Run as Administrator'" -ForegroundColor Yellow
    Write-Host ""
}

# Find PostgreSQL installation
$pgPath = "C:\Program Files\PostgreSQL\17\data"
if (-not (Test-Path $pgPath)) {
    Write-Host "[ERROR] PostgreSQL data directory not found at: $pgPath" -ForegroundColor Red
    Write-Host "Searching for PostgreSQL installation..." -ForegroundColor Yellow
    
    $possiblePaths = @(
        "C:\Program Files\PostgreSQL",
        "C:\Program Files (x86)\PostgreSQL"
    )
    
    foreach ($basePath in $possiblePaths) {
        if (Test-Path $basePath) {
            $versions = Get-ChildItem $basePath -Directory | Where-Object { $_.Name -match "^\d+$" }
            if ($versions) {
                $latest = $versions | Sort-Object Name -Descending | Select-Object -First 1
                $pgPath = Join-Path $latest.FullName "data"
                Write-Host "[INFO] Found PostgreSQL at: $pgPath" -ForegroundColor Green
                break
            }
        }
    }
}

if (-not (Test-Path $pgPath)) {
    Write-Host "[ERROR] Could not find PostgreSQL data directory" -ForegroundColor Red
    Write-Host "Please install PostgreSQL or specify the path manually" -ForegroundColor Yellow
    exit 1
}

Write-Host "[INFO] PostgreSQL data directory: $pgPath" -ForegroundColor Green
Write-Host ""

# Check PostgreSQL service
Write-Host "Checking PostgreSQL service..." -ForegroundColor Cyan
$service = Get-Service -Name "*postgres*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($service) {
    Write-Host "[OK] PostgreSQL service found: $($service.Name)" -ForegroundColor Green
    Write-Host "     Status: $($service.Status)" -ForegroundColor $(if ($service.Status -eq 'Running') { 'Green' } else { 'Yellow' })
} else {
    Write-Host "[WARNING] PostgreSQL service not found" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Configuration Files" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$pg_hba_conf = Join-Path $pgPath "pg_hba.conf"
$postgresql_conf = Join-Path $pgPath "postgresql.conf"

# Check pg_hba.conf
if (Test-Path $pg_hba_conf) {
    Write-Host "[OK] Found pg_hba.conf" -ForegroundColor Green
    Write-Host "     Location: $pg_hba_conf" -ForegroundColor Gray
    
    $content = Get-Content $pg_hba_conf -Raw
    if ($content -match "127\.0\.0\.1|localhost") {
        Write-Host "[OK] pg_hba.conf contains localhost/127.0.0.1 rules" -ForegroundColor Green
    } else {
        Write-Host "[WARNING] pg_hba.conf may not allow localhost connections" -ForegroundColor Yellow
        Write-Host "          You may need to add: host    all    all    127.0.0.1/32    md5" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] pg_hba.conf not found" -ForegroundColor Red
}

Write-Host ""

# Check postgresql.conf
if (Test-Path $postgresql_conf) {
    Write-Host "[OK] Found postgresql.conf" -ForegroundColor Green
    Write-Host "     Location: $postgresql_conf" -ForegroundColor Gray
    
    $content = Get-Content $postgresql_conf
    $listen_line = $content | Select-String "listen_addresses"
    if ($listen_line) {
        if ($listen_line.Line -match "#listen_addresses|#\s*listen_addresses") {
            Write-Host "[WARNING] listen_addresses is commented out" -ForegroundColor Yellow
            Write-Host "          You need to uncomment it and set to 'localhost'" -ForegroundColor Yellow
        } else {
            Write-Host "[OK] listen_addresses configuration found" -ForegroundColor Green
        }
    } else {
        Write-Host "[WARNING] listen_addresses not found in postgresql.conf" -ForegroundColor Yellow
    }
} else {
    Write-Host "[ERROR] postgresql.conf not found" -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Next Steps" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "1. Edit pg_hba.conf and add (if not present):" -ForegroundColor Yellow
Write-Host "   host    all    all    127.0.0.1/32    md5" -ForegroundColor White
Write-Host ""
Write-Host "2. Edit postgresql.conf and ensure:" -ForegroundColor Yellow
Write-Host "   listen_addresses = 'localhost'" -ForegroundColor White
Write-Host "   port = 5432" -ForegroundColor White
Write-Host ""
Write-Host "3. Restart PostgreSQL service:" -ForegroundColor Yellow
Write-Host "   Restart-Service postgresql-x64-17" -ForegroundColor White
Write-Host ""
Write-Host "4. Test connection:" -ForegroundColor Yellow
Write-Host "   python test_postgres_connection.py" -ForegroundColor White
Write-Host ""
Write-Host "Files location:" -ForegroundColor Cyan
Write-Host "  pg_hba.conf: $pg_hba_conf" -ForegroundColor Gray
Write-Host "  postgresql.conf: $postgresql_conf" -ForegroundColor Gray
Write-Host ""

# Offer to open files
$open = Read-Host "Do you want to open these files now? (Y/N)"
if ($open -eq 'Y' -or $open -eq 'y') {
    if (Test-Path $pg_hba_conf) {
        notepad $pg_hba_conf
    }
    if (Test-Path $postgresql_conf) {
        Start-Sleep -Seconds 2
        notepad $postgresql_conf
    }
}

