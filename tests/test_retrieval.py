"""
tests/test_retrieval.py

Unit and integration tests for the RAG Retrieval Engine.
Validates cosine similarity search, citation attribution, and low-confidence fallbacks.
"""

import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.retrieval.engine import retrieval_engine

def test_retrieval_known_entity():
    """Verifies that querying for Brian Chesky returns relevant chunks from his episode."""
    res = retrieval_engine.search("Brian Chesky founder mode and leadership", top_k=5)
    assert res["top_k"] == 5
    assert len(res["chunks"]) > 0
    assert len(res["citations"]) > 0

    # Verify that at least one citation matches Brian Chesky
    guests = [c["guest"] for c in res["citations"]]
    assert "Brian Chesky" in guests

    first_cit = res["citations"][0]
    assert "citation_id" in first_cit
    assert "timestamp" in first_cit
    assert "youtube_url" in first_cit
    assert len(first_cit["quote_snippet"]) > 10

def test_retrieval_pmf_query():
    """Verifies that querying for PMF returns relevant chunks."""
    res = retrieval_engine.search("How to measure product market fit and retention loops", top_k=5)
    assert len(res["chunks"]) > 0
    assert res["confidence"] in ["high", "medium"]

def test_retrieval_insufficient_context():
    """Verifies that an out-of-domain query triggers the low confidence fallback."""
    gibberish_query = "quantum mechanics Schrödinger equation quantum entanglement"
    res = retrieval_engine.search(gibberish_query, top_k=3)
    # The score should be low or flagged as insufficient
    assert res["is_insufficient_context"] is True or res["confidence"] == "low"
