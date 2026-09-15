"""
backend/app/llm/base.py

Base interface and response contracts for the LLM provider abstraction layer.
Decouples application logic from provider-specific SDK implementations.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class LLMResponse(BaseModel):
    content: str
    provider: str
    model: str
    usage: Dict[str, Any] = Field(default_factory=dict)
    finish_reason: Optional[str] = "stop"

class LLMProvider(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """Name of the provider (e.g. 'anthropic', 'openai', 'ollama', 'simulated')"""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Name of the model being used."""
        pass

    @abstractmethod
    async def is_available(self) -> bool:
        """Returns True if the provider is configured and reachable."""
        pass

    @abstractmethod
    async def complete(
        self,
        messages: List[Dict[str, str]],
        system_prompt: str = "",
        temperature: float = 0.7,
        max_tokens: int = 2500,
        **kwargs
    ) -> LLMResponse:
        """Generates a text completion for the conversation messages."""
        pass
