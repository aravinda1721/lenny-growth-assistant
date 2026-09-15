"""
backend/app/llm/factory.py

Factory and manager for LLM providers.
Supports dynamic switching, status inspection, and graceful fallbacks.
"""

import os
from typing import Dict, List, Optional, Any
from .base import LLMProvider
from .anthropic import AnthropicProvider
from .openai import OpenAIProvider
from .ollama import OllamaProvider
from .simulated import SimulatedProvider

class ProviderManager:
    def __init__(self):
        self._providers: Dict[str, LLMProvider] = {
            "anthropic": AnthropicProvider(),
            "openai": OpenAIProvider(),
            "ollama": OllamaProvider(),
            "simulated": SimulatedProvider()
        }
        # Read default from env or fallback to simulated
        env_provider = os.getenv("LLM_PROVIDER", "simulated").strip().lower()
        self._active_provider_name = env_provider if env_provider in self._providers else "simulated"

    @property
    def active_provider(self) -> LLMProvider:
        return self._providers.get(self._active_provider_name, self._providers["simulated"])

    @property
    def active_provider_name(self) -> str:
        return self._active_provider_name

    def set_active_provider(self, name: str) -> bool:
        name = name.strip().lower()
        if name in self._providers:
            self._active_provider_name = name
            return True
        return False

    async def get_provider_status(self) -> List[Dict[str, Any]]:
        status_list = []
        for name, provider in self._providers.items():
            avail = await provider.is_available()
            status_list.append({
                "name": name,
                "model": provider.model_name,
                "available": avail,
                "is_active": (name == self._active_provider_name)
            })
        return status_list

    async def get_healthy_provider(self) -> LLMProvider:
        """Returns active provider if available, otherwise falls back to simulated."""
        active = self.active_provider
        if await active.is_available():
            return active
        print(f"[ProviderManager] Warning: '{self._active_provider_name}' unavailable. Falling back to 'simulated'.")
        return self._providers["simulated"]

provider_manager = ProviderManager()
