# ==============================================================================
# The Lenny Growth Assistant - Native Non-Docker Startup Script (PowerShell)
# ==============================================================================

Write-Host "============================================================" -ForegroundColor Cyan
Write-Host "  The Lenny Growth Assistant - Professional FDE Setup" -ForegroundColor Cyan
Write-Host "  Running 100% Natively (Zero Docker Required)" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptRoot) { $scriptRoot = Get-Location }

# 1. Environment file check
if (-not (Test-Path "$scriptRoot\.env")) {
    Write-Host "[*] Creating .env from .env.example..." -ForegroundColor Yellow
    Copy-Item "$scriptRoot\.env.example" "$scriptRoot\.env"
}

# 2. Python check
Write-Host "`n[1/4] Checking Python environment..." -ForegroundColor Green
$pythonVersion = python --version 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "[-] Python is not found. Please install Python 3.10+." -ForegroundColor Red
    Exit 1
}
Write-Host "  [+] Found: $pythonVersion"

# 3. Knowledge base check
Write-Host "`n[2/4] Verifying Grounded Transcript Knowledge Base..." -ForegroundColor Green
if (-not (Test-Path "$scriptRoot\data\tfidf_index.joblib")) {
    Write-Host "  [*] Knowledge base not initialized. Ingesting transcripts..." -ForegroundColor Yellow
    Push-Location $scriptRoot
    python ingestion/fetch_transcripts.py
    python ingestion/chunk.py
    python ingestion/embed_and_load.py
    Pop-Location
} else {
    Write-Host "  [+] Knowledge Base pre-indexed (568 transcript chunks ready)."
}

# 4. Frontend Node check
Write-Host "`n[3/4] Verifying Frontend dependencies..." -ForegroundColor Green
if (-not (Test-Path "$scriptRoot\frontend\node_modules")) {
    Write-Host "  [*] Installing frontend dependencies..." -ForegroundColor Yellow
    Push-Location "$scriptRoot\frontend"
    Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm install" -Wait -NoNewWindow
    Pop-Location
} else {
    Write-Host "  [+] Frontend node_modules ready."
}

# 5. Launch Backend and Frontend
Write-Host "`n[4/4] Launching Services..." -ForegroundColor Green

Write-Host "  [+] Starting FastAPI Backend at http://127.0.0.1:8000" -ForegroundColor Cyan
$backendProcess = Start-Process -FilePath "python" -ArgumentList "-m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000" -WorkingDirectory $scriptRoot -PassThru

Start-Sleep -Seconds 2

Write-Host "  [+] Starting Vite React Frontend at http://localhost:5173" -ForegroundColor Cyan
$frontendProcess = Start-Process -FilePath "cmd.exe" -ArgumentList "/c npm run dev" -WorkingDirectory "$scriptRoot\frontend" -PassThru

Write-Host "`n============================================================" -ForegroundColor Green
Write-Host "  Application successfully launched!" -ForegroundColor Green
Write-Host "  - Frontend UI:  http://localhost:5173" -ForegroundColor White
Write-Host "  - API Swagger:  http://localhost:8000/docs" -ForegroundColor White
Write-Host "  - Health Check: http://localhost:8000/health" -ForegroundColor White
Write-Host "============================================================" -ForegroundColor Green
Write-Host "Press Ctrl+C or close this window to stop both services."

# Keep parent script waiting and cleanup on exit
try {
    Wait-Process -Id $backendProcess.Id
} finally {
    Stop-Process -Id $backendProcess.Id -ErrorAction SilentlyContinue
    Stop-Process -Id $frontendProcess.Id -ErrorAction SilentlyContinue
}
