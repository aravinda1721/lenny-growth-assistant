"""
backend/app/agent/core.py

Agent Layer Orchestrator.
Coordinates intent classification, tool execution (answer_from_transcripts,
ship30_essay, generate_artifact), context window assembly, and persistence.
"""

from typing import Dict, Any, Optional
from sqlalchemy.orm import Session

from app.llm.factory import provider_manager
from app.db.models import SessionModel, MessageModel, ArtifactModel
from .skills.answer_transcripts import answer_skill
from .skills.ship30 import ship30_skill
from .skills.artifact_gen import artifact_skill

class AgentOrchestrator:
    async def process_chat(
        self,
        db: Session,
        session_id: str,
        user_message: str,
        requested_provider: Optional[str] = None
    ) -> Dict[str, Any]:
        # 1. Fetch or create session
        session_obj = db.query(SessionModel).filter(SessionModel.id == session_id).first()
        if not session_obj:
            session_obj = SessionModel(id=session_id, title=user_message[:50])
            db.add(session_obj)
            db.commit()

        # 2. Persist user message
        user_msg_record = MessageModel(
            session_id=session_id,
            role="user",
            content=user_message,
            citations=[]
        )
        db.add(user_msg_record)
        db.commit()

        # 3. Retrieve conversation history for context
        prior_messages = (
            db.query(MessageModel)
            .filter(MessageModel.session_id == session_id)
            .order_by(MessageModel.created_at.asc())
            .all()
        )
        history = [{"role": m.role, "content": m.content} for m in prior_messages[:-1]]

        # 4. Resolve provider
        if requested_provider:
            provider_manager.set_active_provider(requested_provider)
        provider = await provider_manager.get_healthy_provider()

        # 5. Intent routing
        msg_lower = user_message.lower()
        artifact_generated = None
        rubric_data = None

        if any(keyword in msg_lower for keyword in ["ship 30", "ship30", "essay", "1,250 words", "1250 words"]):
            # Route to Ship 30 essay skill
            res = await ship30_skill.execute(user_message, provider=provider, history=history)
            content = res["content"]
            citations = res.get("citations", [])
            rubric_data = res.get("rubric_verification")

        elif any(keyword in msg_lower for keyword in ["artifact", "one-pager", "one pager", "scorecard", "html", "dashboard", "calculator"]):
            # Route to Artifact Generation
            art_type = "markdown" if "markdown" in msg_lower else "html"
            art_res = await artifact_skill.generate(
                prompt=user_message,
                artifact_type=art_type,
                provider=provider,
                context="\n".join([m["content"] for m in history[-3:]])
            )
            
            # Answer text alongside artifact
            grounded_res = await answer_skill.execute(user_message, provider=provider, history=history)
            content = grounded_res["content"]
            citations = grounded_res.get("citations", [])

            # Create and persist artifact
            artifact_record = ArtifactModel(
                session_id=session_id,
                message_id=user_msg_record.id,
                title=art_res["title"],
                type=art_res["type"],
                content=art_res["content"]
            )
            db.add(artifact_record)
            db.commit()
            db.refresh(artifact_record)
            artifact_generated = artifact_record.to_dict()

        else:
            # Standard grounded conversational Q&A
            res = await answer_skill.execute(user_message, provider=provider, history=history)
            content = res["content"]
            citations = res.get("citations", [])

        # 6. Persist assistant message
        assistant_msg_record = MessageModel(
            session_id=session_id,
            role="assistant",
            content=content,
            citations=citations
        )
        db.add(assistant_msg_record)

        # Update session title if default
        if session_obj.title == "New Conversation" and len(user_message) > 3:
            session_obj.title = user_message[:45] + ("..." if len(user_message) > 45 else "")

        db.commit()
        db.refresh(assistant_msg_record)

        return {
            "session_id": session_id,
            "message": assistant_msg_record.to_dict(),
            "citations": citations,
            "artifact": artifact_generated,
            "rubric_verification": rubric_data,
            "provider_used": provider.name,
            "model_used": provider.model_name
        }

agent_orchestrator = AgentOrchestrator()
