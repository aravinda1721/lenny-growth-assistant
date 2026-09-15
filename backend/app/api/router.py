"""
backend/app/api/router.py

Main API Router defining REST endpoints for:
- /health, /readiness, /config, /config/provider
- /sessions (CRUD)
- /chat (Conversational grounding & tool execution)
- /artifacts (Generation, inspection, sandboxed raw serving)
"""

import uuid
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.db.session import get_db
from app.db.models import SessionModel, MessageModel, ArtifactModel, ChunkModel
from app.llm.factory import provider_manager
from app.agent.core import agent_orchestrator
from app.agent.skills.artifact_gen import artifact_skill
from app.core.config import settings

api_router = APIRouter()
START_TIME = datetime.now(timezone.utc)

# ------------------------------------------------------------------------------
# Pydantic Request/Response Models
# ------------------------------------------------------------------------------

class HealthResponse(BaseModel):
    status: str = "ok"
    version: str = "1.0.0"
    uptime_seconds: float
    timestamp: str

class ReadinessResponse(BaseModel):
    status: str = "ready"
    database_connected: bool
    total_indexed_chunks: int
    active_provider: str
    providers_status: List[Dict[str, Any]]

class ConfigResponse(BaseModel):
    active_provider: str
    active_model: str
    database_url_masked: str
    available_providers: List[Dict[str, Any]]

class ProviderSwitchRequest(BaseModel):
    provider: str = Field(..., description="Provider name: 'anthropic' | 'openai' | 'ollama' | 'simulated'")

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=10000, description="User prompt or inquiry")
    session_id: Optional[str] = Field(None, description="UUID of session; auto-created if empty")
    provider: Optional[str] = Field(None, description="Optional override of LLM provider")

class SessionCreateRequest(BaseModel):
    title: Optional[str] = "New Conversation"

class ArtifactCreateRequest(BaseModel):
    session_id: str
    prompt: str
    type: Optional[str] = "html"

# ------------------------------------------------------------------------------
# System & Configuration Endpoints
# ------------------------------------------------------------------------------

@api_router.get("/health", response_model=HealthResponse)
async def health_check():
    """Liveness probe returning service operational status."""
    uptime = (datetime.now(timezone.utc) - START_TIME).total_seconds()
    return HealthResponse(
        status="ok",
        uptime_seconds=round(uptime, 2),
        timestamp=datetime.now(timezone.utc).isoformat()
    )

@api_router.get("/readiness", response_model=ReadinessResponse)
async def readiness_check(db: Session = Depends(get_db)):
    """Readiness probe checking database connectivity and provider health."""
    db_connected = False
    chunk_count = 0
    try:
        db.execute(text("SELECT 1"))
        db_connected = True
        chunk_count = db.query(ChunkModel).count()
    except Exception:
        db_connected = False

    provider_statuses = await provider_manager.get_provider_status()

    return ReadinessResponse(
        status="ready" if db_connected else "degraded",
        database_connected=db_connected,
        total_indexed_chunks=chunk_count,
        active_provider=provider_manager.active_provider_name,
        providers_status=provider_statuses
    )

@api_router.get("/config", response_model=ConfigResponse)
async def get_config():
    """Returns active provider and configuration without exposing secrets."""
    provider = provider_manager.active_provider
    statuses = await provider_manager.get_provider_status()

    # Mask database URL
    db_url = settings.DATABASE_URL
    if "@" in db_url:
        parts = db_url.split("@")
        masked_url = parts[0].split(":")[0] + "://***:***@" + parts[1]
    else:
        masked_url = db_url

    return ConfigResponse(
        active_provider=provider_manager.active_provider_name,
        active_model=provider.model_name,
        database_url_masked=masked_url,
        available_providers=statuses
    )

@api_router.post("/config/provider")
async def switch_provider(payload: ProviderSwitchRequest):
    """Allows evaluator or UI to dynamically switch LLM provider at runtime."""
    success = provider_manager.set_active_provider(payload.provider)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown provider '{payload.provider}'. Must be one of: anthropic, openai, ollama, simulated"
        )
    return {
        "status": "success",
        "active_provider": provider_manager.active_provider_name,
        "model": provider_manager.active_provider.model_name
    }

# ------------------------------------------------------------------------------
# Session Endpoints
# ------------------------------------------------------------------------------

@api_router.get("/sessions")
async def list_sessions(db: Session = Depends(get_db)):
    """Lists all user chat sessions sorted by recent activity."""
    sessions = (
        db.query(SessionModel)
        .order_by(SessionModel.updated_at.desc())
        .all()
    )
    return [s.to_dict() for s in sessions]

@api_router.post("/sessions")
async def create_session(payload: SessionCreateRequest = None, db: Session = Depends(get_db)):
    """Creates a new session."""
    title = payload.title if payload and payload.title else "New Conversation"
    session_obj = SessionModel(id=str(uuid.uuid4()), title=title)
    db.add(session_obj)
    db.commit()
    db.refresh(session_obj)
    return session_obj.to_dict()

@api_router.get("/sessions/{session_id}")
async def get_session(session_id: str, db: Session = Depends(get_db)):
    """Retrieves full conversation history and attached artifacts for a session."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")

    messages = [m.to_dict() for m in session_obj.messages]
    artifacts = [a.to_dict() for a in session_obj.artifacts]

    return {
        **session_obj.to_dict(),
        "messages": messages,
        "artifacts": artifacts
    }

@api_router.delete("/sessions/{session_id}")
async def delete_session(session_id: str, db: Session = Depends(get_db)):
    """Deletes a session and all its associated messages and artifacts."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    db.delete(session_obj)
    db.commit()
    return {"status": "deleted", "session_id": session_id}

# ------------------------------------------------------------------------------
# Chat & Artifact Endpoints
# ------------------------------------------------------------------------------

@api_router.post("/chat")
async def chat_interaction(payload: ChatRequest, db: Session = Depends(get_db)):
    """
    Main conversational endpoint: accepts message, coordinates RAG retrieval,
    tool execution (grounded Q&A, Ship 30, artifacts), and persists history.
    """
    session_id = payload.session_id or str(uuid.uuid4())
    try:
        res = await agent_orchestrator.process_chat(
            db=db,
            session_id=session_id,
            user_message=payload.message,
            requested_provider=payload.provider
        )
        return res
    except Exception as e:
        # Structured error output rather than unhandled 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "AgentExecutionError",
                "message": str(e),
                "suggestion": "Check provider connectivity or switch to 'simulated' provider via /config/provider."
            }
        )

@api_router.post("/artifacts")
async def generate_artifact_endpoint(payload: ArtifactCreateRequest, db: Session = Depends(get_db)):
    """Generates a standalone artifact attached to an existing session."""
    session_obj = db.query(SessionModel).filter(SessionModel.id == payload.session_id).first()
    if not session_obj:
        raise HTTPException(status_code=404, detail=f"Session '{payload.session_id}' not found")

    provider = await provider_manager.get_healthy_provider()
    art_res = await artifact_skill.generate(
        prompt=payload.prompt,
        artifact_type=payload.type or "html",
        provider=provider
    )

    artifact_record = ArtifactModel(
        session_id=payload.session_id,
        title=art_res["title"],
        type=art_res["type"],
        content=art_res["content"]
    )
    db.add(artifact_record)
    db.commit()
    db.refresh(artifact_record)

    return artifact_record.to_dict()

@api_router.get("/artifacts/{artifact_id}")
async def get_artifact(artifact_id: str, db: Session = Depends(get_db)):
    """Returns artifact metadata and code content."""
    artifact = db.query(ArtifactModel).filter(ArtifactModel.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail=f"Artifact '{artifact_id}' not found")
    return artifact.to_dict()

@api_router.get("/artifacts/{artifact_id}/raw")
async def get_raw_artifact(artifact_id: str, db: Session = Depends(get_db)):
    """
    Serves raw HTML artifact with strict sandboxing and Content-Security-Policy headers.
    Completely prevents malicious script execution in embedded viewers.
    """
    artifact = db.query(ArtifactModel).filter(ArtifactModel.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    headers = {
        "Content-Security-Policy": "default-src 'self' 'unsafe-inline' https://fonts.googleapis.com https://fonts.gstatic.com; script-src 'none'; object-src 'none';",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "SAMEORIGIN"
    }

    media_type = "text/html; charset=utf-8" if artifact.type == "html" else "text/plain; charset=utf-8"
    return Response(content=artifact.content, media_type=media_type, headers=headers)
