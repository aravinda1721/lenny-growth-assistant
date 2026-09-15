"""
backend/app/core/config.py

Application settings and configuration management using Pydantic Settings.
Reads from environment variables and .env file.
"""

from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).parent.parent.parent.parent
ENV_FILE = ROOT_DIR / ".env"

class Settings(BaseSettings):
    APP_ENV: str = "development"
    APP_PORT: int = 8000
    FRONTEND_PORT: int = 5173
    
    # LLM Settings
    LLM_PROVIDER: str = "simulated"
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-3-5-sonnet-20241022"
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "llama3.2"
    
    # Persistence & Retrieval
    DATABASE_URL: str = f"sqlite:///{ROOT_DIR / 'data' / 'lenny_assistant.db'}"
    TOP_K_RETRIEVAL: int = 5
    
    # CORS
    CORS_ORIGINS: List[str] = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:8000",
        "http://localhost:3000"
    ]

    model_config = SettingsConfigDict(
        env_file=str(ENV_FILE) if ENV_FILE.exists() else None,
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
