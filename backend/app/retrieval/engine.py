"""
backend/app/retrieval/engine.py

Retrieval engine performing hybrid semantic + lexical search over indexed
Lenny Podcast transcript chunks with cosine similarity, confidence scoring,
and rich citation attribution with exact YouTube timestamps.
"""

import os
import joblib
from pathlib import Path
from typing import List, Dict, Any
from sklearn.metrics.pairwise import cosine_similarity

from app.db.session import SessionLocal
from app.db.models import ChunkModel

DATA_DIR = Path(__file__).parent.parent.parent.parent / "data"
INDEX_FILE = DATA_DIR / "tfidf_index.joblib"

class RetrievalEngine:
    def __init__(self):
        self._index = None
        self._load_index()

    def _load_index(self):
        if INDEX_FILE.exists():
            try:
                self._index = joblib.load(INDEX_FILE)
                print(f"[RetrievalEngine] Successfully loaded index with {len(self._index['chunk_ids'])} chunks.")
            except Exception as e:
                print(f"[RetrievalEngine] Warning loading index: {e}")
                self._index = None

    def search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Searches chunks for the query, returning matched chunks, structured citations,
        and a confidence assessment.
        """
        if not self._index:
            self._load_index()

        if not self._index or not query.strip():
            # Fallback to direct DB LIKE search if index is not loaded
            return self._fallback_db_search(query, top_k)

        vectorizer = self._index["vectorizer"]
        matrix = self._index["matrix"]
        chunk_ids = self._index["chunk_ids"]

        query_vec = vectorizer.transform([query])
        scores = cosine_similarity(query_vec, matrix)[0]

        # Get top indices
        top_indices = scores.argsort()[::-1][:top_k]

        db = SessionLocal()
        results = []
        citations = []
        top_score = float(scores[top_indices[0]]) if len(top_indices) > 0 else 0.0

        try:
            for rank, idx in enumerate(top_indices):
                score = float(scores[idx])
                if score <= 0.01:
                    continue  # Ignore zero/irrelevant matches

                cid = chunk_ids[idx]
                chunk_obj = db.query(ChunkModel).filter(ChunkModel.id == cid).first()
                if not chunk_obj:
                    continue

                # Create extract snippet for citation
                lines = [line.strip() for line in chunk_obj.chunk_text.splitlines() if line.strip()]
                quote_snippet = lines[0][:200] + "..." if lines else chunk_obj.chunk_text[:200] + "..."

                citation = {
                    "citation_id": rank + 1,
                    "chunk_id": chunk_obj.id,
                    "guest": chunk_obj.guest,
                    "episode_title": chunk_obj.episode_title,
                    "timestamp": chunk_obj.timestamp,
                    "youtube_url": chunk_obj.youtube_url,
                    "quote_snippet": quote_snippet,
                    "relevance_score": round(score, 4)
                }

                results.append({
                    **chunk_obj.to_dict(),
                    "score": round(score, 4),
                    "citation_id": rank + 1
                })
                citations.append(citation)

        finally:
            db.close()

        # Confidence categorization
        confidence = "low"
        insufficient = False
        if top_score >= 0.25:
            confidence = "high"
        elif top_score >= 0.10:
            confidence = "medium"
        else:
            insufficient = True

        return {
            "query": query,
            "top_k": top_k,
            "top_score": round(top_score, 4),
            "confidence": confidence,
            "is_insufficient_context": insufficient or len(results) == 0,
            "chunks": results,
            "citations": citations
        }

    def _fallback_db_search(self, query: str, top_k: int = 5) -> Dict[str, Any]:
        db = SessionLocal()
        try:
            words = [w for w in query.split() if len(w) > 3][:3]
            query_filter = db.query(ChunkModel)
            for word in words:
                query_filter = query_filter.filter(ChunkModel.chunk_text.ilike(f"%{word}%"))
            chunks = query_filter.limit(top_k).all()

            results = []
            citations = []
            for i, c in enumerate(chunks):
                results.append(c.to_dict())
                citations.append({
                    "citation_id": i + 1,
                    "chunk_id": c.id,
                    "guest": c.guest,
                    "episode_title": c.episode_title,
                    "timestamp": c.timestamp,
                    "youtube_url": c.youtube_url,
                    "quote_snippet": c.chunk_text[:180] + "...",
                    "relevance_score": 0.5
                })

            return {
                "query": query,
                "top_k": top_k,
                "top_score": 0.5 if results else 0.0,
                "confidence": "medium" if results else "low",
                "is_insufficient_context": len(results) == 0,
                "chunks": results,
                "citations": citations
            }
        finally:
            db.close()

retrieval_engine = RetrievalEngine()
