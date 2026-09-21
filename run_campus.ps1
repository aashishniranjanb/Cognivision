# ==============================================================================
# SRM AI Attendance System — One-Click Campus Production Runner (PowerShell)
# ==============================================================================
param (
    [switch]$Demo = $true,
    [int]$Port = 8000,
    [string]$HostIp = "0.0.0.0"
)

Write-Host "======================================================================" -ForegroundColor Cyan
Write-Host " SRM AI MULTI-CAMERA ATTENDANCE SYSTEM — ONE-CLICK CAMPUS STARTUP" -ForegroundColor Cyan
Write-Host "======================================================================" -ForegroundColor Cyan

$env:PYTHONPATH = "ai-service;$env:PYTHONPATH"

$argsList = @("--host", $HostIp, "--port", $Port)
if ($Demo) {
    $argsList += "--demo"
}

python ai-service/app/system_runner.py @argsList
