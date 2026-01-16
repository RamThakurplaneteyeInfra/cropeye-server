# PowerShell script to set up Docker database for the project
# This script will start Docker Desktop, wait for it, then start the database container

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Docker Database Setup" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if Docker is installed
$dockerVersion = docker --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[ERROR] Docker is not installed!" -ForegroundColor Red
    Write-Host "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host "[OK] Docker is installed: $dockerVersion" -ForegroundColor Green
Write-Host ""

# Check if Docker Desktop is running
Write-Host "Checking if Docker Desktop is running..." -ForegroundColor Cyan
$dockerRunning = $false

try {
    $null = docker ps 2>&1
    if ($LASTEXITCODE -eq 0) {
        $dockerRunning = $true
        Write-Host "[OK] Docker Desktop is running!" -ForegroundColor Green
    }
} catch {
    $dockerRunning = $false
}

if (-not $dockerRunning) {
    Write-Host "[INFO] Docker Desktop is not running" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Starting Docker Desktop..." -ForegroundColor Cyan
    
    # Try to start Docker Desktop
    $dockerPath = @(
        "$env:ProgramFiles\Docker\Docker\Docker Desktop.exe",
        "${env:ProgramFiles(x86)}\Docker\Docker\Docker Desktop.exe",
        "$env:LOCALAPPDATA\Programs\Docker\Docker\Docker Desktop.exe"
    )
    
    $dockerExe = $null
    foreach ($path in $dockerPath) {
        if (Test-Path $path) {
            $dockerExe = $path
            break
        }
    }
    
    if ($dockerExe) {
        Write-Host "[INFO] Found Docker Desktop at: $dockerExe" -ForegroundColor Green
        Write-Host "[INFO] Starting Docker Desktop..." -ForegroundColor Yellow
        Start-Process -FilePath $dockerExe -WindowStyle Minimized
        
        Write-Host "[INFO] Waiting for Docker Desktop to start (this may take 30-60 seconds)..." -ForegroundColor Yellow
        Write-Host ""
        
        # Wait for Docker to be ready (max 2 minutes)
        $maxWait = 120
        $waited = 0
        $ready = $false
        
        while ($waited -lt $maxWait) {
            Start-Sleep -Seconds 5
            $waited += 5
            
            try {
                $null = docker ps 2>&1
                if ($LASTEXITCODE -eq 0) {
                    $ready = $true
                    break
                }
            } catch {
                # Continue waiting
            }
            
            if (($waited % 15) -eq 0) {
                Write-Host "  Still waiting... ($waited seconds)" -ForegroundColor Gray
            }
        }
        
        if ($ready) {
            Write-Host "[OK] Docker Desktop is now running!" -ForegroundColor Green
        } else {
            Write-Host "[ERROR] Docker Desktop did not start within 2 minutes" -ForegroundColor Red
            Write-Host "[INFO] Please start Docker Desktop manually and run this script again" -ForegroundColor Yellow
            exit 1
        }
    } else {
        Write-Host "[ERROR] Could not find Docker Desktop executable" -ForegroundColor Red
        Write-Host "[INFO] Please start Docker Desktop manually:" -ForegroundColor Yellow
        Write-Host "  1. Open Docker Desktop from Start menu" -ForegroundColor White
        Write-Host "  2. Wait for it to start" -ForegroundColor White
        Write-Host "  3. Run this script again" -ForegroundColor White
        exit 1
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Starting Database Container" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

# Check if database container already exists
Write-Host "Checking for existing database container..." -ForegroundColor Cyan
$existingContainer = docker ps -a --filter "name=cropeye_postgres" --format "{{.Names}}" 2>&1

if ($existingContainer -and $existingContainer -ne "") {
    Write-Host "[INFO] Found existing database container: $existingContainer" -ForegroundColor Yellow
    
    # Check if it's running
    $runningContainer = docker ps --filter "name=cropeye_postgres" --format "{{.Names}}" 2>&1
    if ($runningContainer -and $runningContainer -ne "") {
        Write-Host "[OK] Database container is already running!" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Starting existing container..." -ForegroundColor Yellow
        docker start cropeye_postgres 2>&1 | Out-Null
        Start-Sleep -Seconds 5
        Write-Host "[OK] Database container started!" -ForegroundColor Green
    }
} else {
    Write-Host "[INFO] No existing container found. Creating new database container..." -ForegroundColor Yellow
    Write-Host ""
    
    # Start only the database service
    Write-Host "Starting PostgreSQL database container..." -ForegroundColor Cyan
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
Write-Host "Verifying database container..." -ForegroundColor Cyan
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

# Test database connection
Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Testing Database Connection" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Waiting a few more seconds for PostgreSQL to be fully ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

Write-Host "[INFO] Testing connection to database..." -ForegroundColor Cyan

# Test connection using docker exec
$testResult = docker exec cropeye_postgres pg_isready -U postgres 2>&1

if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] PostgreSQL is ready to accept connections!" -ForegroundColor Green
} else {
    Write-Host "[WARNING] PostgreSQL may still be starting up" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "Setup Complete!" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "[SUCCESS] Docker database is set up and running!" -ForegroundColor Green
Write-Host ""
Write-Host "Database Configuration:" -ForegroundColor Cyan
Write-Host "  Container: cropeye_postgres" -ForegroundColor White
Write-Host "  Database: neoce" -ForegroundColor White
Write-Host "  User: postgres" -ForegroundColor White
Write-Host "  Password: admin" -ForegroundColor White
Write-Host "  Host: localhost" -ForegroundColor White
Write-Host "  Port: 5432" -ForegroundColor White
Write-Host ""
Write-Host "Next Steps:" -ForegroundColor Cyan
Write-Host "  1. Run: python complete_database_setup.py" -ForegroundColor Yellow
Write-Host "     This will create the database and install PostGIS" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Run migrations: python manage.py migrate" -ForegroundColor Yellow
Write-Host ""
Write-Host "  3. Start server: python manage.py runserver" -ForegroundColor Yellow
Write-Host ""
Write-Host "Useful Commands:" -ForegroundColor Cyan
Write-Host "  View logs: docker logs cropeye_postgres" -ForegroundColor Gray
Write-Host "  Stop: docker stop cropeye_postgres" -ForegroundColor Gray
Write-Host "  Start: docker start cropeye_postgres" -ForegroundColor Gray
Write-Host "  Remove: docker compose down" -ForegroundColor Gray
Write-Host ""

