"""
tests/test_sanitization.py

Security and Sanitization Tests for Artifact Rendering.
Validates defense-in-depth protection against Cross-Site Scripting (XSS),
malicious script tag removal, event handler stripping, and CSP headers.
"""

import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from main import app
from app.core.sanitizer import sanitize_html_artifact
from app.db.session import SessionLocal
from app.db.models import SessionModel, ArtifactModel

client = TestClient(app)

def test_sanitizer_removes_script_tags():
    """Verifies that executable <script> tags are neutralized."""
    malicious_input = "<div><h1>Title</h1><script>alert('XSS-ATTACK');</script><p>Clean content</p></div>"
    sanitized = sanitize_html_artifact(malicious_input)
    assert "<script>" not in sanitized
    assert "alert('XSS-ATTACK')" not in sanitized
    assert "Title" in sanitized
    assert "Clean content" in sanitized

def test_sanitizer_removes_inline_event_handlers():
    """Verifies that inline JS event handlers (onload, onerror, onclick) are stripped."""
    malicious_input = "<img src='invalid.jpg' onerror='alert(1)' onload='doEvil()' /><a href='javascript:stealCookie()'>Link</a>"
    sanitized = sanitize_html_artifact(malicious_input)
    assert "onerror=" not in sanitized
    assert "onload=" not in sanitized
    assert "javascript:" not in sanitized

def test_raw_artifact_endpoint_csp_headers():
    """Verifies that the /artifacts/{id}/raw endpoint serves strict Content-Security-Policy headers."""
    db = SessionLocal()
    try:
        session_obj = SessionModel(id="test-sec-session", title="Security Test")
        db.add(session_obj)
        
        artifact_obj = ArtifactModel(
            id="test-art-sec",
            session_id="test-sec-session",
            title="Secured Scorecard",
            type="html",
            content="<html><body><h3>Safe Artifact</h3></body></html>"
        )
        db.add(artifact_obj)
        db.commit()

        # Fetch via endpoint
        response = client.get(f"/artifacts/test-art-sec/raw")
        assert response.status_code == 200
        csp = response.headers.get("Content-Security-Policy", "")
        assert "script-src 'none'" in csp
        assert "Safe Artifact" in response.text
    finally:
        # Cleanup
        db.query(ArtifactModel).filter(ArtifactModel.id == "test-art-sec").delete()
        db.query(SessionModel).filter(SessionModel.id == "test-sec-session").delete()
        db.commit()
        db.close()
