"""
backend/app/llm/openai.py

OpenAI provider implementation supporting GPT-4o / GPT-4o-mini.
"""

import os
import httpx
from typing import List, Dict, Any
from .base import LLMProvider, LLMResponse

class OpenAIProvider(LLMProvider):
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.endpoint = "https://api.openai.com/v1/chat/completions"

    @property
    def name(self) -> str:
        return "openai"

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
            raise ValueError("OpenAI API key is not configured. Set OPENAI_API_KEY in .env.")

        formatted_msgs = []
        if system_prompt:
            formatted_msgs.append({"role": "system", "content": system_prompt})
        formatted_msgs.extend([{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages])

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.model,
            "messages": formatted_msgs,
            "max_tokens": max_tokens,
            "temperature": temperature
        }

        async with httpx.AsyncClient(timeout=45.0) as client:
            response = await client.post(self.endpoint, json=payload, headers=headers)
            if response.status_code != 200:
                raise RuntimeError(f"OpenAI API error ({response.status_code}): {response.text}")

            data = response.json()
            content = data["choices"][0]["message"]["content"]
            usage = data.get("usage", {})

            return LLMResponse(
                content=content,
                provider="openai",
                model=self.model,
                usage=usage
            )
