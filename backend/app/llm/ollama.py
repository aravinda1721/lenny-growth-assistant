"""
backend/app/llm/ollama.py

Local Ollama provider implementation supporting llama3.2, mistral, deepseek, etc.
Direct HTTP client to localhost:11434 with health checks.
"""

import os
import httpx
from typing import List, Dict, Any
from .base import LLMProvider, LLMResponse

class OllamaProvider(LLMProvider):
    def __init__(self, base_url: str = None, model: str = None):
        self.base_url = (base_url or os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")).rstrip("/")
        self.model = model or os.getenv("OLLAMA_MODEL", "llama3.2")
        self.endpoint = f"{self.base_url}/api/chat"

    @property
    def name(self) -> str:
        return "ollama"

    @property
    def model_name(self) -> str:
        return self.model

    async def is_available(self) -> bool:
        """Checks if Ollama daemon is reachable and responding."""
        try:
            async with httpx.AsyncClient(timeout=2.0) as client:
                res = await client.get(f"{self.base_url}/api/tags")
                return res.status_code == 200
        except Exception:
            return False

    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2500,
        **kwargs
    ) -> LLMResponse:
        available = await self.is_available()
        if not available:
            raise ConnectionError(
                f"Ollama server is not responding at {self.base_url}. "
                "Ensure the Ollama application is running or switch to 'simulated' or cloud provider."
            )

        formatted_msgs = []
        if system_prompt:
            formatted_msgs.append({"role": "system", "content": system_prompt})
        formatted_msgs.extend([{"role": m.get("role", "user"), "content": m.get("content", "")} for m in messages])

        payload = {
            "model": self.model,
            "messages": formatted_msgs,
            "stream": False,
            "options": {
                "temperature": temperature,
                "num_predict": max_tokens
            }
        }

        async with httpx.AsyncClient(timeout=90.0) as client:
            response = await client.post(self.endpoint, json=payload)
            if response.status_code != 200:
                raise RuntimeError(f"Ollama error ({response.status_code}): {response.text}")

            data = response.json()
            content = data.get("message", {}).get("content", "")
            
            return LLMResponse(
                content=content,
                provider="ollama",
                model=self.model,
                usage={"eval_count": data.get("eval_count", 0), "prompt_eval_count": data.get("prompt_eval_count", 0)}
            )
