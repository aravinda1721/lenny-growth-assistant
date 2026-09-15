"""
tests/test_ship30.py

Tests for the Ship 30 for 30 essay generation skill and structural rubric verification.
"""

import sys
from pathlib import Path
import pytest

BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.agent.skills.ship30 import verify_ship30_rubric, ship30_skill
from app.llm.simulated import simulated_provider

def test_rubric_verification_valid():
    """Tests that a properly formatted Ship 30 essay passes all rubric checks."""
    full_text = simulated_provider._generate_ship30_essay("test", "")
    
    result = verify_ship30_rubric(full_text)
    assert result["has_title"] is True
    assert result["has_bullets"] is True
    assert result["has_bold"] is True
    assert result["has_takeaway"] is True
    assert result["subheading_count"] >= 3
    assert result["passed"] is True, f"Rubric issues: {result['issues']}"

def test_rubric_verification_short_fails():
    """Tests that an overly short essay fails the rubric."""
    short_text = "# Short Post\nJust a quick paragraph."
    result = verify_ship30_rubric(short_text)
    assert result["passed"] is False
    assert any("too short" in issue.lower() for issue in result["issues"])

@pytest.mark.asyncio
async def test_ship30_skill_execution():
    """Tests end-to-end execution of the Ship 30 skill."""
    res = await ship30_skill.execute("product market fit retention", provider=simulated_provider)
    assert "content" in res
    assert len(res["content"]) > 300
    assert "rubric_verification" in res
    assert res["rubric_verification"]["has_title"] is True
