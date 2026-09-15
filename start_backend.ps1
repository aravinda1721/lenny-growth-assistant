# Quick start script for FastAPI Backend
Write-Host "Starting FastAPI Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
python -m uvicorn main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
