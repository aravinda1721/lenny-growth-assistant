"""
tests/test_api.py

API Contract and Integration Tests for FastAPI Endpoints.
Covers health, readiness, configuration, session management, and chat execution.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add backend directory to path
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from main import app

client = TestClient(app)

def test_health_endpoint():
    """Verifies liveness health check."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "uptime_seconds" in data
    assert "timestamp" in data

def test_readiness_endpoint():
    """Verifies readiness check, DB connectivity, and chunk count."""
    response = client.get("/readiness")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ready"
    assert data["database_connected"] is True
    assert data["total_indexed_chunks"] > 0
    assert "active_provider" in data
    assert isinstance(data["providers_status"], list)

def test_config_endpoint():
    """Verifies configuration inspection without leaking secrets."""
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "active_provider" in data
    assert "active_model" in data
    assert "available_providers" in data
    # Ensure no raw passwords in DB URL
    assert "password" not in data["database_url_masked"].lower()

def test_provider_switch_endpoint():
    """Verifies runtime switching of active LLM provider."""
    # Switch to simulated
    res = client.post("/config/provider", json={"provider": "simulated"})
    assert res.status_code == 200
    assert res.json()["active_provider"] == "simulated"

    # Try invalid provider
    bad_res = client.post("/config/provider", json={"provider": "invalid_provider_xyz"})
    assert bad_res.status_code == 400

def test_session_lifecycle():
    """Tests session creation, retrieval, and deletion."""
    # 1. Create session
    create_res = client.post("/sessions", json={"title": "Test Integration Session"})
    assert create_res.status_code == 200
    session_data = create_res.json()
    session_id = session_data["id"]
    assert session_data["title"] == "Test Integration Session"

    # 2. Get session
    get_res = client.get(f"/sessions/{session_id}")
    assert get_res.status_code == 200
    assert get_res.json()["id"] == session_id

    # 3. List sessions contains new session
    list_res = client.get("/sessions")
    assert list_res.status_code == 200
    session_ids = [s["id"] for s in list_res.json()]
    assert session_id in session_ids

    # 4. Delete session
    del_res = client.delete(f"/sessions/{session_id}")
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "deleted"

    # 5. Confirm deletion
    confirm_res = client.get(f"/sessions/{session_id}")
    assert confirm_res.status_code == 404

def test_chat_endpoint_valid():
    """Tests /chat interaction with citation generation and persistence."""
    chat_payload = {
        "message": "What did Brian Chesky say about founder mode?",
        "provider": "simulated"
    }
    response = client.post("/chat", json=chat_payload)
    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert "message" in data
    assert data["message"]["role"] == "assistant"
    assert len(data["message"]["content"]) > 50
    assert isinstance(data["citations"], list)
    assert len(data["citations"]) > 0

def test_chat_endpoint_validation_error():
    """Tests that invalid payloads return structured 422 errors instead of 500 crashes."""
    bad_payload = {"message": ""}  # Empty message violates min_length=1
    response = client.post("/chat", json=bad_payload)
    assert response.status_code == 422
