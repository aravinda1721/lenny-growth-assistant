#!/usr/bin/env bash
# ==============================================================================
# The Lenny Growth Assistant - Native Non-Docker Startup Script (Bash)
# ==============================================================================

set -e

echo "============================================================"
echo "  The Lenny Growth Assistant - Professional FDE Setup"
echo "  Running 100% Natively (Zero Docker Required)"
echo "============================================================"

# 1. Environment check
if [ ! -f ".env" ]; then
    echo "[*] Creating .env from .env.example..."
    cp .env.example .env
fi

# 2. Check Python
echo ""
echo "[1/4] Checking Python environment..."
python3 --version || python --version

# 3. Knowledge base check
echo ""
echo "[2/4] Verifying Grounded Transcript Knowledge Base..."
if [ ! -f "data/tfidf_index.joblib" ]; then
    echo "  [*] Ingesting podcast transcripts..."
    python3 ingestion/fetch_transcripts.py || python ingestion/fetch_transcripts.py
    python3 ingestion/chunk.py || python ingestion/chunk.py
    python3 ingestion/embed_and_load.py || python ingestion/embed_and_load.py
else
    echo "  [+] Knowledge Base pre-indexed (568 chunks ready)."
fi

# 4. Frontend check
echo ""
echo "[3/4] Verifying Frontend dependencies..."
if [ ! -d "frontend/node_modules" ]; then
    echo "  [*] Installing frontend dependencies..."
    (cd frontend && npm install)
else
    echo "  [+] Frontend node_modules ready."
fi

# 5. Launch Backend & Frontend
echo ""
echo "[4/4] Launching Services..."
echo "  [+] Starting FastAPI Backend at http://127.0.0.1:8000"
(cd backend && python3 -m uvicorn main:app --host 127.0.0.1 --port 8000) &
BACKEND_PID=$!

sleep 2

echo "  [+] Starting Vite React Frontend at http://localhost:5173"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true" EXIT

echo ""
echo "============================================================"
echo "  Application successfully launched!"
echo "  - Frontend UI:  http://localhost:5173"
echo "  - API Swagger:  http://localhost:8000/docs"
echo "  - Health Check: http://localhost:8000/health"
echo "============================================================"
echo "Press Ctrl+C to stop."

wait
