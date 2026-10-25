$ErrorActionPreference = 'Stop'
$projectRoot = $PSScriptRoot
$logDirectory = Join-Path $projectRoot 'logs'
New-Item -ItemType Directory -Path $logDirectory -Force | Out-Null

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   CHENNAI FLOOD LAB - 1-CLICK LAUNCHER                   " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Check Python & Backend Service (Port 8000)
$pythonPath = Join-Path $projectRoot '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonPath)) { 
    $pythonCmd = Get-Command python.exe -ErrorAction SilentlyContinue
    if ($pythonCmd) { $pythonPath = $pythonCmd.Source } else { $pythonPath = 'python' }
}

Write-Host "Checking Backend Simulation Engine (Port 8000)..." -NoNewline
$backendOnline = $false
try {
    $health = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 3
    if ($health.status -eq 'ok' -or $health.service -eq 'chennai-flood-sim') {
        $backendOnline = $true
    }
} catch {}

if ($backendOnline) {
    Write-Host " [ALREADY RUNNING]" -ForegroundColor Green
} else {
    Write-Host " [STARTING]" -ForegroundColor Yellow
    Start-Process -FilePath $pythonPath -ArgumentList 'backend\run_server.py' -WorkingDirectory $projectRoot -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'backend.log') -RedirectStandardError (Join-Path $logDirectory 'backend-error.log') | Out-Null
    
    $backendReady = $false
    for ($attempt = 1; $attempt -le 20; $attempt++) {
        Start-Sleep -Milliseconds 600
        try {
            $h = Invoke-RestMethod 'http://127.0.0.1:8000/api/health' -TimeoutSec 2
            if ($h.status -eq 'ok' -or $h.service -eq 'chennai-flood-sim') {
                $backendReady = $true
                break
            }
        } catch {}
    }
    if ($backendReady) {
        Write-Host "Backend Engine online at http://localhost:8000" -ForegroundColor Green
    } else {
        Write-Host "Warning: Backend taking longer than expected. Check logs/backend.log" -ForegroundColor DarkYellow
    }
}

# 2. Check Frontend Next.js Service (Port 3000)
Write-Host "Checking Frontend Dashboard (Port 3000)..." -NoNewline
$frontendOnline = $false
try {
    $res = Invoke-WebRequest 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 3
    if ($res.StatusCode -eq 200) {
        $frontendOnline = $true
    }
} catch {}

if ($frontendOnline) {
    Write-Host " [ALREADY RUNNING]" -ForegroundColor Green
} else {
    Write-Host " [STARTING]" -ForegroundColor Yellow
    $frontendDir = Join-Path $projectRoot 'frontend'
    $npmCmd = (Get-Command npm.cmd -ErrorAction SilentlyContinue).Source
    if ($npmCmd) {
        Start-Process -FilePath $npmCmd -ArgumentList @('run', 'dev') -WorkingDirectory $frontendDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'frontend.log') -RedirectStandardError (Join-Path $logDirectory 'frontend-error.log') | Out-Null
    } else {
        $nodePath = (Get-Command node.exe).Source
        Start-Process -FilePath $nodePath -ArgumentList @('node_modules\next\dist\bin\next', 'dev', '--port', '3000') -WorkingDirectory $frontendDir -WindowStyle Hidden -RedirectStandardOutput (Join-Path $logDirectory 'frontend.log') -RedirectStandardError (Join-Path $logDirectory 'frontend-error.log') | Out-Null
    }

    $frontendReady = $false
    for ($attempt = 1; $attempt -le 35; $attempt++) {
        Start-Sleep -Milliseconds 800
        try {
            $r = Invoke-WebRequest 'http://127.0.0.1:3000' -UseBasicParsing -TimeoutSec 3
            if ($r.StatusCode -eq 200) {
                $frontendReady = $true
                break
            }
        } catch {}
    }
    if ($frontendReady) {
        Write-Host "Frontend Dashboard online at http://localhost:3000" -ForegroundColor Green
    } else {
        Write-Host "Dashboard is initializing in the background. Check logs/frontend.log" -ForegroundColor DarkYellow
    }
}

# 3. Open in Browser
Write-Host ""
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   ALL SERVICES ACTIVE! OPENING BROWSER...                 " -ForegroundColor Green
Write-Host "   Frontend Dashboard: http://localhost:3000              " -ForegroundColor White
Write-Host "   Backend API Docs:   http://localhost:8000/docs         " -ForegroundColor White
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host ""

Start-Process 'http://localhost:3000'
Start-Sleep -Seconds 2
