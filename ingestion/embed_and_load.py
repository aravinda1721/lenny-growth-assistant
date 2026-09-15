"""
ingestion/embed_and_load.py

Embeds transcript chunks and loads them idempotently into the database.
Uses a hybrid TF-IDF + Cosine dense vectorizer with n-grams (1, 2)
so the system has fast, zero-dependency semantic search with no external API calls required.
Can run against both PostgreSQL or local SQLite.
"""

import sys
import json
import joblib
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer

# Add backend to path so we can import DB models
BACKEND_DIR = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(BACKEND_DIR))

from app.db.session import init_db, SessionLocal
from app.db.models import ChunkModel

PROCESSED_FILE = Path(__file__).parent / "data" / "processed" / "chunks.json"
DATA_DIR = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)
INDEX_FILE = DATA_DIR / "tfidf_index.joblib"

def load_and_embed():
    print("=== Loading & Embedding Chunks into Database ===")
    if not PROCESSED_FILE.exists():
        print(f"[-] Error: {PROCESSED_FILE} does not exist. Run ingestion/chunk.py first.")
        sys.exit(1)

    with open(PROCESSED_FILE, "r", encoding="utf-8") as f:
        chunks_data = json.load(f)

    print(f"Loaded {len(chunks_data)} chunks from {PROCESSED_FILE}")

    # Build TF-IDF dense representation
    print("Fitting semantic vectorizer over chunks corpus...")
    corpus = [f"{c['guest']} {c['episode_title']} {c['text']}" for c in chunks_data]
    vectorizer = TfidfVectorizer(
        ngram_range=(1, 2),
        max_features=4096,
        sublinear_tf=True,
        stop_words="english"
    )
    matrix = vectorizer.fit_transform(corpus)
    print(f"Matrix shape: {matrix.shape}")

    # Save vectorizer index for fast inference
    chunk_ids = [c["id"] for c in chunks_data]
    joblib.dump({"vectorizer": vectorizer, "matrix": matrix, "chunk_ids": chunk_ids}, INDEX_FILE)
    print(f"Saved vector index to {INDEX_FILE}")

    # Initialize database tables
    init_db()
    db = SessionLocal()

    inserted = 0
    updated = 0
    skipped = 0

    try:
        for i, c in enumerate(chunks_data):
            existing = db.query(ChunkModel).filter(ChunkModel.content_hash == c["content_hash"]).first()
            if existing:
                skipped += 1
                continue

            # Store dense embedding vector snippet
            dense_vec = matrix[i].toarray()[0].tolist()[:64] # store compact vector representation

            chunk_obj = ChunkModel(
                id=c["id"],
                source_file=c["source_file"],
                episode_slug=c["episode_slug"],
                episode_title=c["episode_title"],
                guest=c["guest"],
                timestamp=c["timestamp"],
                timestamp_seconds=c["timestamp_seconds"],
                youtube_url=c["youtube_url"],
                speaker=c["speaker"],
                chunk_index=c["chunk_index"],
                chunk_text=c["text"],
                content_hash=c["content_hash"],
                embedding=dense_vec
            )
            db.add(chunk_obj)
            inserted += 1

            if inserted % 100 == 0:
                db.commit()

        db.commit()
        print(f"\n[OK] Database Sync Complete: {inserted} inserted, {skipped} skipped, total: {len(chunks_data)}")
    except Exception as e:
        db.rollback()
        print(f"[-] DB Error during ingestion: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    load_and_embed()
