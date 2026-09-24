# ==============================================================================
# SRM AI Camera Attendance System — One-Click Master Campus Launcher
# Runs: AI Camera Vision Engine (8000) + Spring Boot (8080) + React Frontend (5173)
# ==============================================================================
param (
    [switch]$NoBrowser = $false,
    [switch]$UseVite = $false,
    [string]$CameraUrl = "http://192.168.1.3:8080/video"
)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$env:CAMERA_URL = $CameraUrl

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " SRM AI CAMERA ATTENDANCE SYSTEM — UNIFIED PLATFORM LAUNCHER" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

# 0. Gracefully free ports 8000, 8080, 5173, 3000 if lingering
function Free-Port($port) {
    try {
        $pids = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
        foreach ($pidToKill in $pids) {
            if ($pidToKill -and $pidToKill -ne $PID) {
                Write-Host "[Launcher] Freeing port $port (PID: $pidToKill)..." -ForegroundColor Yellow
                Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
            }
        }
    } catch {}
}

Free-Port 8000
Free-Port 8080
Free-Port 5173
Free-Port 3000
Start-Sleep -Milliseconds 500

# 1. Configure Java 17 Runtime for Spring Boot Backend
$jdkPath = "C:\Program Files\Microsoft\jdk-17.0.20.101-hotspot"
if (Test-Path $jdkPath) {
    $env:JAVA_HOME = $jdkPath
    $env:PATH = "$env:JAVA_HOME\bin;$env:PATH"
    Write-Host "[Launcher] Configured OpenJDK 17 runtime: $jdkPath" -ForegroundColor Green
} else {
    Write-Host "[Launcher] Warning: JDK 17 path not found, using default Java." -ForegroundColor Yellow
}

$env:PYTHONPATH = "$PSScriptRoot\ai-service;$env:PYTHONPATH"

# 2. Start AI Camera Vision Engine (FastAPI on Port 8000)
Write-Host "[Launcher] Starting AI Camera Vision Engine (:8000)..." -ForegroundColor Cyan
$aiCwd = Join-Path $PSScriptRoot "ai-service"
$aiProcess = Start-Process -FilePath "python" `
    -ArgumentList "-m", "uvicorn", "app.backend.api:app", "--host", "0.0.0.0", "--port", "8000" `
    -WorkingDirectory $aiCwd -PassThru

# 3. Start Spring Boot Backend (Port 8080)
Write-Host "[Launcher] Starting Spring Boot Attendance Backend (PostgreSQL on :8080)..." -ForegroundColor Cyan
$jarPath = Join-Path $PSScriptRoot "attendance-backend\target\attendance-backend-0.0.1-SNAPSHOT.jar"
$backendCwd = Join-Path $PSScriptRoot "attendance-backend"
$backendProcess = $null
if (Test-Path $jarPath) {
    $javaBin = if (Test-Path "$env:JAVA_HOME\bin\java.exe") { "$env:JAVA_HOME\bin\java.exe" } else { "java" }
    $backendProcess = Start-Process -FilePath $javaBin -ArgumentList "-jar", $jarPath -WorkingDirectory $backendCwd -PassThru
} else {
    Write-Host "[Launcher] Warning: JAR not found, running backend via mvnw..." -ForegroundColor Yellow
    $backendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c", "mvnw.cmd spring-boot:run" -WorkingDirectory $backendCwd -PassThru
}

# 4. Start Frontend (Next.js by default on :3000 or Vite on :5173)
$frontendProcess = $null
$frontendUrl = ""
if ($UseVite) {
    Write-Host "[Launcher] Starting React Vite Frontend (:5173)..." -ForegroundColor Cyan
    $frontendCwd = Join-Path $PSScriptRoot "attendance-frontend"
    $frontendProcess = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "npm run dev -- --host 0.0.0.0 --port 5173" `
        -WorkingDirectory $frontendCwd -PassThru
    $frontendUrl = "http://localhost:5173/live"
} else {
    Write-Host "[Launcher] Starting Next.js Production Frontend (:3000)..." -ForegroundColor Cyan
    $frontendCwd = Join-Path $PSScriptRoot "attendance-next"
    $frontendProcess = Start-Process -FilePath "cmd.exe" `
        -ArgumentList "/c", "npm run dev" `
        -WorkingDirectory $frontendCwd -PassThru
    $frontendUrl = "http://localhost:3000/live"
}

# 5. Readiness health check
Write-Host "[Launcher] Waiting for services to become responsive..." -ForegroundColor Gray
$maxWait = 20
$ready = $false
for ($i = 0; $i -lt $maxWait; $i++) {
    Start-Sleep -Seconds 1
    try {
        $aiCheck = (Invoke-WebRequest -Uri "http://localhost:8000/api/campus/summary" -UseBasicParsing -TimeoutSec 1).StatusCode
        $backendCheck = (Invoke-WebRequest -Uri "http://localhost:8080/api/dashboard/summary" -UseBasicParsing -TimeoutSec 1).StatusCode
        if ($aiCheck -eq 200 -and $backendCheck -eq 200) {
            $ready = $true
            break
        }
    } catch {}
}

Write-Host "`n======================================================================" -ForegroundColor Green
Write-Host " ALL 3 CORE SERVICES ACTIVE & CONNECTED!" -ForegroundColor Green
Write-Host "  • Live Camera Feed Source         : $CameraUrl" -ForegroundColor Cyan
Write-Host "  • AI Camera Engine & Video Stream : http://localhost:8000/api/camera/stream/CAM01" -ForegroundColor Gray
Write-Host "  • Spring Boot REST Backend        : http://localhost:8080/api/dashboard/summary" -ForegroundColor Gray
Write-Host "  • Attendance Portal ($($UseVite ? 'Vite' : 'Next.js'))  : $frontendUrl" -ForegroundColor White
Write-Host "======================================================================" -ForegroundColor Green

# 6. Launch Browser
if (-not $NoBrowser) {
    Write-Host "[Launcher] Opening browser to Live Monitoring CCTV Dashboard..." -ForegroundColor Green
    Start-Process $frontendUrl
}

Write-Host "`nPress ENTER or CTRL+C in this terminal window to stop all services..." -ForegroundColor Yellow
try {
    [Console]::ReadLine()
} finally {
    Write-Host "`n[Launcher] Stopping all services..." -ForegroundColor Red
    if ($aiProcess -and -not $aiProcess.HasExited) { Stop-Process -Id $aiProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($backendProcess -and -not $backendProcess.HasExited) { Stop-Process -Id $backendProcess.Id -Force -ErrorAction SilentlyContinue }
    if ($frontendProcess -and -not $frontendProcess.HasExited) { Stop-Process -Id $frontendProcess.Id -Force -ErrorAction SilentlyContinue }
    Free-Port 8000
    Free-Port 8080
    Free-Port 5173
    Free-Port 3000
    Write-Host "[Launcher] Clean shutdown complete." -ForegroundColor Green
}
