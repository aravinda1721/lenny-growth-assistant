"""
backend/app/llm/anthropic.py

Anthropic Claude provider implementation supporting Claude 3.5 Sonnet / Haiku.
"""

import os
import httpx
from typing import List, Dict, Any
from .base import LLMProvider, LLMResponse

class AnthropicProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = model or os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.endpoint = "https://api.anthropic.com/v1/messages"

    @property
    def name(self) -> str:
        return "anthropic"

    @property
    def model_name(self) -> str:
        return self.model

    async def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key.strip()) > 10)

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2500,
        **kwargs
    ) -> LLMResponse:
        if not await self.is_available():
            raise ValueError("Anthropic API key is not configured. Set ANTHROPIC_API_KEY in .env.")

        # Format messages for Anthropic (roles: 'user' and 'assistant')
        anthropic_msgs = []
        for m in messages:
            role = "user" if m.get("role") in ["user", "system"] else "assistant"
            anthropic_msgs.append({"role": role, "content": m.get("content", "")})

        headers = {
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": anthropic_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature
        }
        if system_prompt:
            payload["system"] = system_prompt

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(f"Anthropic API error ({response.status_code}): {response.text}")
            
            data = response.json()
            content_blocks = data.get("content", [])
            text = "".join([b.get("text", "") for b in content_blocks if b.get("type") == "text"])
            usage = data.get("usage", {})

            return LLMResponse(
                content=text,
                provider="anthropic",
                model=self.model,
                usage=usage
            )
