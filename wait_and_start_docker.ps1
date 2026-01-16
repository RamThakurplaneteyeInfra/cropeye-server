# Script to wait for Docker Desktop and start containers
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Waiting for Docker Desktop to be ready..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

$maxAttempts = 24  # 2 minutes total (24 * 5 seconds)
$attempt = 0
$dockerReady = $false

while ($attempt -lt $maxAttempts) {
    $attempt++
    Write-Host "Attempt $attempt of $maxAttempts - Checking Docker..." -ForegroundColor Yellow
    
    try {
        $null = docker ps 2>&1
        if ($LASTEXITCODE -eq 0) {
            $dockerReady = $true
            Write-Host "✅ Docker Desktop is ready!" -ForegroundColor Green
            break
        }
    } catch {
        # Continue waiting
    }
    
    if (-not $dockerReady) {
        Write-Host "⏳ Docker Desktop is still starting... waiting 5 seconds" -ForegroundColor Gray
        Start-Sleep -Seconds 5
    }
}

if (-not $dockerReady) {
    Write-Host "" -ForegroundColor Red
    Write-Host "❌ Docker Desktop did not become ready after 2 minutes" -ForegroundColor Red
    Write-Host "Please ensure Docker Desktop is running and try again" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "You can:" -ForegroundColor Cyan
    Write-Host "  1. Open Docker Desktop from Start menu" -ForegroundColor White
    Write-Host "  2. Wait for it to fully start (check system tray)" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Docker containers..." -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if container already exists
$existingContainer = docker ps -a --filter "name=cropeye_postgres" --format "{{.Names}}" 2>&1

if ($existingContainer -and $existingContainer -ne "") {
    Write-Host "[INFO] Found existing container: $existingContainer" -ForegroundColor Yellow
    
    $runningContainer = docker ps --filter "name=cropeye_postgres" --format "{{.Names}}" 2>&1
    if ($runningContainer -and $runningContainer -ne "") {
        Write-Host "[OK] Database container is already running!" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Starting existing container..." -ForegroundColor Yellow
        docker start cropeye_postgres
        Start-Sleep -Seconds 5
        Write-Host "[OK] Database container started!" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] Creating and starting database container..." -ForegroundColor Yellow
    docker compose up db -d
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Database container is starting..." -ForegroundColor Green
        Write-Host "[INFO] Waiting for database to be ready (30 seconds)..." -ForegroundColor Yellow
        Start-Sleep -Seconds 30
    } else {
        Write-Host "[ERROR] Failed to start database container" -ForegroundColor Red
        exit 1
    }
}

# Verify container is running
Write-Host ""
Write-Host "Verifying container status..." -ForegroundColor Cyan
$containerStatus = docker ps --filter "name=cropeye_postgres" --format "{{.Status}}" 2>&1

if ($containerStatus -and $containerStatus -ne "") {
    Write-Host "[OK] Database container is running!" -ForegroundColor Green
    Write-Host "     Status: $containerStatus" -ForegroundColor Gray
} else {
    Write-Host "[ERROR] Database container is not running" -ForegroundColor Red
    Write-Host "[INFO] Checking container logs..." -ForegroundColor Yellow
    docker logs cropeye_postgres --tail 20
    exit 1
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "✅ Docker Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Database Configuration:" -ForegroundColor Cyan
Write-Host "  Container: cropeye_postgres" -ForegroundColor White
Write-Host "  Database: neoce" -ForegroundColor White
Write-Host "  User: postgres" -ForegroundColor White
Write-Host "  Password: admin" -ForegroundColor White
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5432" -ForegroundColor White
Write-Host ""

