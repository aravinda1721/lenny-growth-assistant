"""
backend/app/agent/skills/ship30.py

Ship 30 for 30 essay generation skill.
Encodes strict editorial and structural principles:
- Target: ~1,250 words (1,000 - 1,400 acceptable range)
- 1 Compelling Hook / Headline
- 1 Punchy Narrative Lead-in
- 3 to 5 Structured Subheadings
- Skimmable bullet points with bold emphasis
- 1 Specific, Memorable 1-Sentence Takeaway
- Strict grounding in transcript knowledge base
Includes automated rubric verification.
"""

import re
from typing import Dict, Any, List
from app.retrieval.engine import retrieval_engine
from app.llm.base import LLMProvider

SHIP30_SYSTEM_PROMPT = """You are a master digital writer trained in the Ship 30 for 30 framework and Impeccable writing style.
You transform raw product and growth insights from Lenny's Podcast into an authoritative, highly skimmable, ~1,250-word essay.

EDITORIAL RULES:
1. WORD COUNT: Aim for approximately 1,250 words (between 1,100 and 1,350 words). Do not write a 300-word summary.
2. HOOK: Start with a provocative, curiosity-inducing # Headline followed by 2-3 short, rhythmic opening paragraphs identifying a common failure or counter-intuitive truth.
3. STRUCTURE: Divide the core argument into 3 to 5 distinct subheads using Roman numerals (e.g. '### I. ...', '### II. ...').
4. FORMATTING: Use skimmable bullet points, numbered lists, and bold lead-in phrases for every main idea. Never write walls of text.
5. GROUNDING: Ground the core ideas in quotes, frameworks, and stories from the provided Lenny's Podcast excerpts (e.g. Brian Chesky, Shreyas Doshi, Marty Cagan, Elena Verna).
6. TAKEAWAY: End with an explicit section titled: '### The 1-Sentence Takeaway' containing a bold, actionable summary statement.
"""

def verify_ship30_rubric(text: str) -> Dict[str, Any]:
    """
    Validates that the generated text adheres to the Ship 30 for 30 structural rubric.
    """
    words = text.split()
    word_count = len(words)
    
    # Check for title/hook
    has_title = text.strip().startswith("#")
    
    # Check for subheadings
    subheadings = re.findall(r"^###?\s+.*$", text, re.MULTILINE)
    has_subheadings = len(subheadings) >= 3
    
    # Check for bullet points or lists
    has_bullets = bool(re.search(r"^\s*[-*•]\s+", text, re.MULTILINE))
    
    # Check for bold emphasis
    has_bold = bool(re.search(r"\*\*[^*]+\*\*", text))
    
    # Check for 1-sentence takeaway
    has_takeaway = "takeaway" in text.lower()
    
    issues = []
    if word_count < 800:
        issues.append(f"Word count too short ({word_count} words; target ~1,250)")
    elif word_count > 1600:
        issues.append(f"Word count too long ({word_count} words; target ~1,250)")
        
    if not has_title:
        issues.append("Missing top-level # Title/Hook")
    if not has_subheadings:
        issues.append(f"Insufficient subheadings ({len(subheadings)} found; target >= 3)")
    if not has_bullets:
        issues.append("Missing bullet points for skimmability")
    if not has_bold:
        issues.append("Missing selective bold emphasis")
    if not has_takeaway:
        issues.append("Missing '1-Sentence Takeaway' conclusion")

    return {
        "passed": len(issues) == 0,
        "word_count": word_count,
        "subheading_count": len(subheadings),
        "has_title": has_title,
        "has_bullets": has_bullets,
        "has_bold": has_bold,
        "has_takeaway": has_takeaway,
        "issues": issues
    }

class Ship30Skill:
    def __init__(self, retrieval=None):
        self.retrieval = retrieval or retrieval_engine

    async def execute(
        self,
        topic: str,
        provider: LLMProvider,
        history: List[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        # Step 1: Retrieve relevant grounded material
        search_res = self.retrieval.search(topic, top_k=6)
        chunks = search_res["chunks"]
        citations = search_res["citations"]

        if search_res["is_insufficient_context"] or not chunks:
            return {
                "content": (
                    f"Unable to generate a grounded Ship 30 for 30 essay on '{topic}'.\n\n"
                    "The transcripts from Lenny's Podcast do not contain sufficient source material on this subject. "
                    "Per the editorial guidelines, all essays must be directly backed by podcast interview transcripts."
                ),
                "citations": [],
                "rubric_verification": {"passed": False, "issues": ["Insufficient source grounding"]},
                "word_count": 0
            }

        # Step 2: Assemble grounding context
        context_str = "\n\n".join([f"[{c['guest']} - {c['episode_title']}]:\n{c['text']}" for c in chunks])

        user_prompt = (
            f"Topic: {topic}\n\n"
            f"Grounding transcript material from Lenny's Podcast:\n{context_str}\n\n"
            f"Write a full ~1,250-word Ship 30 for 30 essay following all editorial rules."
        )

        messages = [{"role": "user", "content": user_prompt}]

        # Step 3: Generate
        llm_response = await provider.complete(
            messages=messages,
            system_prompt=SHIP30_SYSTEM_PROMPT,
            temperature=0.7,
            max_tokens=3000
        )

        essay = llm_response.content
        rubric_check = verify_ship30_rubric(essay)

        return {
            "content": essay,
            "citations": citations,
            "rubric_verification": rubric_check,
            "word_count": rubric_check["word_count"],
            "provider": llm_response.provider,
            "model": llm_response.model
        }

ship30_skill = Ship30Skill()
