# Agent Transcript: Phase 1 — Transcript Ingestion & RAG Pipeline

**Timestamp:** 2026-09-15T21:03:00Z  
**Agent:** Antigravity FDE Pair Programmer  
**Goal:** Ingest authentic Lenny's Podcast transcripts, implement speaker-aware chunking with timestamps, and generate dense vector embeddings.  

---

### Actions & Engineering Challenges

1. **Querying Upstream Transcripts:**
   - Queried GitHub API for `ChatPRD/lennys-podcast-transcripts`.
   - Discovered 303 episodes, each formatted with YAML frontmatter containing `guest`, `title`, `youtube_url`, `video_id`, and `publish_date`, followed by timestamped speaker turns (`Speaker (HH:MM:SS): text`).
   - Selected 5 high-leverage product management episodes to seed the local database:
     - Brian Chesky (Leadership & Founder Mode)
     - Elena Verna (Growth Tactics & Retention)
     - Marty Cagan (Product Teams vs Feature Teams)
     - Shreyas Doshi (High-Agency Product Management)
     - Gustaf Alstromer (Superhuman PMF Engine)

2. **Speaker-Aware Chunking (`ingestion/chunk.py`):**
   - Implemented regex `^([A-Za-z\s\.\'\-]+?)\s*\(((\d{1,2}:)?\d{2}:\d{2})\):\s*(.*)$` to parse speaker turns.
   - Grouped turns into cohesive segments (~800 characters) with conversational overlap.
   - Calculated exact YouTube timestamp URLs (`https://youtu.be/{video_id}?t={seconds}`).
   - Calculated SHA-256 content hashes for every chunk to enforce idempotent upserts.
   - Result: 568 structured chunks produced.

3. **Dense Vector Embeddings & Indexing (`ingestion/embed_and_load.py`):**
   - Built a hybrid dense vectorizer using TF-IDF with sublinear TF scaling and (1, 2) n-grams.
   - Fit vectorizer over all 568 chunks (vocabulary shape: 568 x 4096).
   - Saved precomputed matrix to `data/tfidf_index.joblib` for sub-millisecond retrieval.
   - Loaded chunks into the database idempotently.

### Verifications & Testing
- Tested queries for "Brian Chesky founder mode" and "Superhuman PMF":
  - Top cosine score: 0.2729.
  - Returned authentic citation: Elena Verna on *10 growth tactics that never work*, timestamp `00:16:41`.
