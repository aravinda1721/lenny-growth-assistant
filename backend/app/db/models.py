"""
backend/app/db/models.py

SQLAlchemy ORM models for Sessions, Messages, Citations, Artifacts, and Chunks.
Designed to work seamlessly on PostgreSQL (pgvector/JSONB) and native SQLite (JSON).
"""

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Column,
    String,
    Text,
    Integer,
    DateTime,
    ForeignKey,
    JSON,
    Index
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

def utcnow():
    return datetime.now(timezone.utc)

class SessionModel(Base):
    __tablename__ = "sessions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="New Conversation")
    created_at = Column(DateTime, default=utcnow, nullable=False)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow, nullable=False)
    metadata_json = Column(JSON, default=dict, nullable=False)

    # Relationships
    messages = relationship("MessageModel", back_populates="session", cascade="all, delete-orphan", order_by="MessageModel.created_at")
    artifacts = relationship("ArtifactModel", back_populates="session", cascade="all, delete-orphan", order_by="ArtifactModel.created_at")

    def to_dict(self):
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "metadata": self.metadata_json or {},
            "message_count": len(self.messages) if self.messages else 0
        }

class MessageModel(Base):
    __tablename__ = "messages"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    content = Column(Text, nullable=False)
    citations = Column(JSON, default=list, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    session = relationship("SessionModel", back_populates="messages")
    artifacts = relationship("ArtifactModel", back_populates="message")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "citations": self.citations or [],
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ArtifactModel(Base):
    __tablename__ = "artifacts"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    session_id = Column(String(36), ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    message_id = Column(String(36), ForeignKey("messages.id", ondelete="SET NULL"), nullable=True)
    title = Column(String(255), nullable=False, default="Generated Artifact")
    type = Column(String(50), nullable=False, default="markdown")  # 'markdown' or 'html'
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=utcnow, nullable=False)

    session = relationship("SessionModel", back_populates="artifacts")
    message = relationship("MessageModel", back_populates="artifacts")

    def to_dict(self):
        return {
            "id": self.id,
            "session_id": self.session_id,
            "message_id": self.message_id,
            "title": self.title,
            "type": self.type,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }

class ChunkModel(Base):
    __tablename__ = "chunks"

    id = Column(String(100), primary_key=True)
    source_file = Column(String(255), nullable=False)
    episode_slug = Column(String(100), nullable=False, index=True)
    episode_title = Column(String(255), nullable=False)
    guest = Column(String(100), nullable=False, index=True)
    timestamp = Column(String(20), nullable=False)
    timestamp_seconds = Column(Integer, nullable=False, default=0)
    youtube_url = Column(String(500), nullable=False)
    speaker = Column(String(255), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    chunk_text = Column(Text, nullable=False)
    content_hash = Column(String(64), nullable=False, unique=True, index=True)
    embedding = Column(JSON, nullable=True)  # List of floats for dense vector
    created_at = Column(DateTime, default=utcnow, nullable=False)

    __table_args__ = (
        Index("idx_chunk_search", "episode_slug", "guest"),
    )

    def to_dict(self, include_embedding=False):
        d = {
            "id": self.id,
            "source_file": self.source_file,
            "episode_slug": self.episode_slug,
            "episode_title": self.episode_title,
            "guest": self.guest,
            "timestamp": self.timestamp,
            "timestamp_seconds": self.timestamp_seconds,
            "youtube_url": self.youtube_url,
            "speaker": self.speaker,
            "chunk_index": self.chunk_index,
            "text": self.chunk_text,
            "content_hash": self.content_hash,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        if include_embedding:
            d["embedding"] = self.embedding
        return d
