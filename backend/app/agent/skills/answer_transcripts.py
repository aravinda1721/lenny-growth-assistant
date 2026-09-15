"""
backend/app/agent/skills/answer_transcripts.py

Grounded conversational skill: answers product and growth questions strictly
from Lenny's Podcast transcripts with explicit source citations and low-confidence fallbacks.
"""

from typing import List, Dict, Any
from app.retrieval.engine import retrieval_engine
from app.llm.base import LLMProvider

SYSTEM_PROMPT = """You are 'The Lenny Growth Assistant', an expert product and growth advisor.
Your knowledge is strictly grounded in transcripts from Lenny's Podcast.

CRITICAL INSTRUCTIONS:
1. Answer the user's question using ONLY the provided transcript excerpts.
2. Cite your sources directly using the format: [Source: Episode Title - Speaker (Timestamp)].
3. If the provided excerpts do not contain enough information to answer the question faithfully, state clearly and honestly that the transcripts do not contain sufficient context, rather than fabricating an answer.
4. Format your response cleanly with markdown headings, bullet points, and concise takeaways.
"""

class AnswerFromTranscriptsSkill:
    def __init__(self, retrieval=None):
        self.retrieval = retrieval or retrieval_engine

    async def execute(
        self,
        query: str,
        provider: LLMProvider,
        history: List[Dict[str, str]] = None,
        top_k: int = 5
    ) -> Dict[str, Any]:
        """
        Executes grounded retrieval and answers the question.
        """
        # Step 1: Retrieval
        search_res = self.retrieval.search(query, top_k=top_k)
        chunks = search_res["chunks"]
        citations = search_res["citations"]
        is_insufficient = search_res["is_insufficient_context"]

        # Step 2: Handle insufficient context immediately without hallucinating
        if is_insufficient:
            fallback_text = (
                "I searched the transcripts from Lenny's Podcast, but there is not enough "
                f"grounded material discussing '{query}'.\n\n"
                "To ensure accuracy and prevent hallucination, I only answer questions supported by "
                "recorded episodes (such as discussions on Product-Market Fit, Founder Mode, "
                "B2B Growth, Feature Teams vs. Empowered Teams, and Retention Loops). "
                "Could you please reframe or ask about one of those topics?"
            )
            return {
                "content": fallback_text,
                "citations": [],
                "confidence": search_res["confidence"],
                "is_grounded": False,
                "insufficient_context": True
            }

        # Step 3: Format retrieved context for prompt
        context_blocks = []
        for i, c in enumerate(chunks):
            context_blocks.append(
                f"--- Excerpt {i+1} ---\n"
                f"Episode: {c['episode_title']}\n"
                f"Guest: {c['guest']}\n"
                f"Timestamp: {c['timestamp']}\n"
                f"YouTube Link: {c['youtube_url']}\n"
                f"Content:\n{c['text']}\n"
            )
        context_str = "\n".join(context_blocks)

        prompt_message = (
            f"User Question: {query}\n\n"
            f"Here are the relevant transcript excerpts:\n\n{context_str}\n\n"
            f"Provide a thorough, grounded answer with clear citations."
        )

        messages = list(history or [])
        messages.append({"role": "user", "content": prompt_message})

        # Step 4: Generate completion
        llm_response = await provider.complete(
            messages=messages,
            system_prompt=SYSTEM_PROMPT,
            temperature=0.3
        )

        return {
            "content": llm_response.content,
            "citations": citations,
            "confidence": search_res["confidence"],
            "is_grounded": True,
            "insufficient_context": False,
            "provider": llm_response.provider,
            "model": llm_response.model
        }

answer_skill = AnswerFromTranscriptsSkill()
