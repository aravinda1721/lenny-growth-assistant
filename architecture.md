# System Architecture & Technical Specification: The Lenny Growth Assistant

**Deliverable 5:** Complete Technical Architecture Document  
**Target:** Production-Grade Forward Deployed AI System (Non-Docker Native & Cloud Ready)  

---

## 1. System Overview & Component Boundaries

```mermaid
graph TD
    Client["React 18 + Vite Frontend<br/>(Split-View UI, Sandboxed Iframe)"]
    
    subgraph FastAPI_Backend ["FastAPI Application (Port 8000)"]
        Router["API Router<br/>/health, /sessions, /chat, /artifacts, /config"]
        AgentCore["Agent Orchestrator<br/>(Intent Routing & Context Assembly)"]
        
        subgraph Skills ["Agent Skills Layer"]
            AnswerSkill["AnswerFromTranscriptsSkill<br/>(Grounded RAG with Citations)"]
            Ship30Skill["Ship30Skill<br/>(~1,250w Essay + Rubric Verifier)"]
            ArtifactSkill["ArtifactGeneratorSkill<br/>(HTML/CSS + Markdown Gen)"]
        end
        
        subgraph Providers ["LLM Provider Abstraction"]
            SimProvider["SimulatedProvider<br/>(Offline Grounded Synthesis)"]
            OllamaProv["OllamaProvider<br/>(Local Llama 3.2 on :11434)"]
            ClaudeProv["AnthropicProvider<br/>(Claude 3.5 Sonnet)"]
            OpenAIProv["OpenAIProvider<br/>(GPT-4o-mini)"]
        end
        
        RetrievalEngine["Retrieval Engine<br/>(Dense Vector Cosine + TF-IDF)"]
        Sanitizer["Security Sanitizer<br/>(XSS Script Stripping & CSP)"]
    end
    
    subgraph Persistence ["Dual Persistence Layer"]
        DB["SQLAlchemy ORM<br/>(PostgreSQL or Native SQLite)"]
        VectorIdx["Vector Index File<br/>(tfidf_index.joblib)"]
    end

    Client -->|REST / JSON| Router
    Router --> AgentCore
    AgentCore --> AnswerSkill
    AgentCore --> Ship30Skill
    AgentCore --> ArtifactSkill
    
    AnswerSkill --> RetrievalEngine
    Ship30Skill --> RetrievalEngine
    
    AnswerSkill --> Providers
    Ship30Skill --> Providers
    ArtifactSkill --> Providers
    
    ArtifactSkill --> Sanitizer
    RetrievalEngine --> DB
    RetrievalEngine --> VectorIdx
    AgentCore --> DB
```

---

## 2. Ingestion & Retrieval Pipeline

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant Frontend as React Client
    participant API as FastAPI Router (/chat)
    participant Agent as Agent Orchestrator
    participant RAG as Retrieval Engine
    participant LLM as LLM Provider (Active)
    participant DB as SQLite / PostgreSQL

    User->>Frontend: Enters query ("What is Brian Chesky's product playbook?")
    Frontend->>API: POST /chat { session_id, message, provider }
    API->>Agent: process_chat(db, session_id, message)
    Agent->>DB: Fetch recent messages for session context
    Agent->>RAG: search(query, top_k=5)
    RAG->>DB: Query chunks & compute cosine similarity scores
    RAG-->>Agent: Returns top chunks + citations + confidence
    
    alt Insufficient Context (score < 0.10)
        Agent-->>API: Returns "insufficient transcript context" fallback
    else Sufficient Grounding
        Agent->>LLM: complete(messages + excerpts, system_prompt)
        LLM-->>Agent: Generated grounded response
        Agent->>DB: Persist assistant message + citations JSON
        Agent-->>API: Returns { message, citations, session_id }
    end
    
    API-->>Frontend: 200 OK Response
    Frontend-->>User: Renders message + clickable citation chips
```

---

## 3. Database Schema & Data Models

The persistence layer uses **SQLAlchemy ORM**, operating identically on PostgreSQL (via `psycopg2` or Supabase) and zero-config local SQLite (`lenny_assistant.db`).

```mermaid
erDiagram
    SESSIONS ||--o{ MESSAGES : "contains"
    SESSIONS ||--o{ ARTIFACTS : "owns"
    MESSAGES ||--o{ ARTIFACTS : "produces"
    
    SESSIONS {
        string id PK "UUID"
        string title "Conversation Title"
        datetime created_at "UTC Timestamp"
        datetime updated_at "UTC Timestamp"
        json metadata_json "Session Metadata"
    }

    MESSAGES {
        string id PK "UUID"
        string session_id FK "References SESSIONS.id"
        string role "user | assistant | system"
        text content "Message Body Markdown"
        json citations "List of Citations"
        datetime created_at "UTC Timestamp"
    }

    ARTIFACTS {
        string id PK "UUID"
        string session_id FK "References SESSIONS.id"
        string message_id FK "References MESSAGES.id"
        string title "Artifact Name"
        string type "html | markdown"
        text content "HTML/CSS or Markdown Code"
        datetime created_at "UTC Timestamp"
    }

    CHUNKS {
        string id PK "e.g. brian-chesky_0001"
        string source_file "Filename"
        string episode_slug "Episode Identifier"
        string episode_title "Episode Name"
        string guest "Guest Name"
        string timestamp "HH:MM:SS"
        int timestamp_seconds "Seconds for YouTube jump"
        string youtube_url "Timestamped YouTube URL"
        string speaker "Speaker Name(s)"
        int chunk_index "Index in Episode"
        text chunk_text "Raw chunk transcript"
        string content_hash UK "SHA-256 for Idempotency"
        json embedding "Dense Vector Representation"
        datetime created_at "UTC Timestamp"
    }
```

---

## 4. API Endpoints Specification

| Method | Path | Description | Request Payload | Response Schema |
|---|---|---|---|---|
| `GET` | `/health` | Liveness health check | None | `{ status: "ok", uptime_seconds: float, timestamp: string }` |
| `GET` | `/readiness` | Readiness check for DB and providers | None | `{ status: "ready", database_connected: bool, total_indexed_chunks: int, active_provider: str, providers_status: [] }` |
| `GET` | `/config` | Returns active provider without leaking secrets | None | `{ active_provider: str, active_model: str, database_url_masked: str, available_providers: [] }` |
| `POST` | `/config/provider` | Dynamically switches LLM engine | `{ provider: "ollama" }` | `{ status: "success", active_provider: str, model: str }` |
| `GET` | `/sessions` | Lists all chat sessions | None | `[ { id, title, created_at, updated_at, message_count } ]` |
| `POST` | `/sessions` | Creates an empty session | `{ title?: string }` | `{ id, title, created_at, updated_at }` |
| `GET` | `/sessions/{id}` | Retrieves session with messages and artifacts | None | `{ id, title, messages: [], artifacts: [] }` |
| `DELETE` | `/sessions/{id}` | Deletes session and associated messages | None | `{ status: "deleted", session_id: str }` |
| `POST` | `/chat` | Main grounded conversational endpoint | `{ message: str, session_id?: str, provider?: str }` | `{ session_id, message: {}, citations: [], artifact?: {}, rubric_verification?: {} }` |
| `POST` | `/artifacts` | Generates a standalone artifact | `{ session_id: str, prompt: str, type?: "html" }` | `{ id, session_id, title, type, content }` |
| `GET` | `/artifacts/{id}` | Fetches artifact metadata and code | None | `{ id, title, type, content, created_at }` |
| `GET` | `/artifacts/{id}/raw` | Serves raw HTML with CSP sandbox headers | None | Raw HTML document (`text/html`) |

---

## 5. Security & Untrusted Artifact Isolation Model

Because generated HTML originates from language model outputs, it must be treated as **untrusted data**. The Lenny Growth Assistant enforces a three-tier defense-in-depth isolation model:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        DEFENSE-IN-DEPTH MODEL                          │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 1: SERVER-SIDE SANITIZATION                                      │
│ - Regex scanning in app/core/sanitizer.py                              │
│ - Strips <script>, <object>, <embed>, <iframe> tags                    │
│ - Neutralizes inline event handlers (onerror=, onload=, onclick=)      │
│ - Rewrites javascript: pseudo-protocol URIs                            │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 2: CLIENT-SIDE IFRAME SANDBOXING                                  │
│ - Rendered in ArtifactViewer using <iframe sandbox="allow-same-origin"> │
│ - Omission of 'allow-scripts' strictly blocks JavaScript execution    │
│ - Prevents cookie theft, localStorage access, and DOM hijacking        │
├────────────────────────────────────────────────────────────────────────┤
│ TIER 3: CONTENT SECURITY POLICY (CSP)                                  │
│ - Serves HTTP header on /artifacts/{id}/raw:                           │
│   default-src 'self' 'unsafe-inline' https://fonts.googleapis.com;    │
│   script-src 'none'; object-src 'none';                               │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Non-Docker Deployment Topology

The system is engineered for simple local execution while remaining cloud-deployable to platforms like Railway, Supabase, or AWS:

```
[Local Evaluator Machine]
  │
  ├─► PowerShell (run.ps1) / Bash (run.sh)
  │     │
  │     ├─► FastAPI (Uvicorn Worker) on http://127.0.0.1:8000
  │     │     ├─► Embedded SQLite (lenny_assistant.db)
  │     │     └─► Local Dense Vector Index (tfidf_index.joblib)
  │     │
  │     └─► Vite Dev Server on http://localhost:5173
  │           └─► Reverse proxy (/api -> http://localhost:8000)
```
