# The Lenny Growth Assistant 🎙️⚡

> **A production-grade, full-stack AI assistant grounded strictly in Lenny's Podcast transcripts.**  
> Featuring conversational Q&A with timestamped YouTube citations, a dedicated **Ship 30 for 30** essay skill with automated rubric verification, and an interactive, split-screen **Artifact Viewer** with iframe sandbox isolation.
>
> **Built for 100% Native Execution (Zero Docker Required).**

[![FastAPI](https://img.shields.io/badge/FastAPI-0.121-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18.3-61DAFB?logo=react&logoColor=black)](https://react.dev)
[![Vite](https://img.shields.io/badge/Vite-5.4-646CFF?logo=vite&logoColor=white)](https://vitejs.dev)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://python.org)
[![Tests](https://img.shields.io/badge/Tests-16%20Passing-brightgreen)](file:///tests/)

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           REACT 18 + VITE FRONTEND                          │
│                                                                             │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────────────┐ │
│  │   Sessions Sidebar    │  │     Chat & RAG Pane   │  │ Sandboxed Viewer │ │
│  │  - New session        │  │  - Grounded Q&A       │  │ - Markdown/HTML  │ │
│  │  - History & delete   │  │  - Citations drawer   │  │ - CSP / iframe   │ │
│  │  - Search & stats     │  │  - Live LLM switcher  │  │ - Copy/download  │ │
│  └───────────────────────┘  └───────────────────────┘  └──────────────────┘ │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │ REST / JSON (FastAPI)
┌──────────────────────────────────────▼──────────────────────────────────────┐
│                              FASTAPI BACKEND                                │
│                                                                             │
│  ┌───────────────────────┐  ┌───────────────────────┐  ┌──────────────────┐ │
│  │      Agent Layer      │  │     LLM Abstraction   │  │  RAG & Retrieval │ │
│  │ - answer_transcripts  │  │ - Anthropic (Claude)  │  │ - Ingestion ETL  │ │
│  │ - ship30_essay skill  │  │ - OpenAI (GPT-4o)     │  │ - Metadata chunk │ │
│  │ - generate_artifact   │  │ - Ollama (Local)      │  │ - Semantic search│ │
│  │ - Rubric verification │  │ - Offline Simulated   │  │ - YouTube source │ │
│  └───────────────────────┘  └───────────────────────┘  └──────────────────┘ │
│                                      │                                      │
│  ┌───────────────────────────────────▼───────────────────────────────────┐  │
│  │            Persistence Layer (PostgreSQL or Native SQLite)            │  │
│  │         - sessions  - messages  - citations  - artifacts  - chunks     │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## ⚡ Quickstart (Zero Docker Required)

This project is built from the ground up to run natively with **one command** on a clean developer machine.

### Prerequisites
- **Python 3.10+**
- **Node.js 18+** & **npm**

### 1-Command Startup

#### On Windows (PowerShell):
```powershell
.\run.ps1
```

#### On macOS / Linux (Bash):
```bash
chmod +x run.sh
./run.sh
```

The script automatically:
1. Verifies your Python and Node environments.
2. Initializes `.env` with safe default configurations.
3. Checks the pre-indexed knowledge base (568 chunks across Brian Chesky, Shreyas Doshi, Marty Cagan, Elena Verna, Gustaf Alstromer).
4. Installs frontend dependencies if needed.
5. Launches the **FastAPI Backend** (`http://127.0.0.1:8000`) and the **React Frontend** (`http://localhost:5173`).

---

## ⚙️ Environment Configuration (`.env`)

Copy `.env.example` to `.env`. The default settings run out-of-the-box in **Offline Demonstration Mode** with zero external API keys or background services needed:

| Variable | Description | Default | Required? |
|---|---|---|---|
| `LLM_PROVIDER` | Active engine: `simulated` \| `anthropic` \| `openai` \| `ollama` | `simulated` | **Yes** |
| `DATABASE_URL` | Database URI (PostgreSQL or SQLite) | `sqlite:///./data/lenny_assistant.db` | Optional (falls back to local SQLite) |
| `ANTHROPIC_API_KEY` | Claude API Key | *(empty)* | Only if `LLM_PROVIDER=anthropic` |
| `ANTHROPIC_MODEL` | Claude model variant | `claude-3-5-sonnet-20241022` | Optional |
| `OPENAI_API_KEY` | OpenAI API Key | *(empty)* | Only if `LLM_PROVIDER=openai` |
| `OPENAI_MODEL` | OpenAI model variant | `gpt-4o-mini` | Optional |
| `OLLAMA_BASE_URL` | Local Ollama endpoint | `http://localhost:11434` | Only if `LLM_PROVIDER=ollama` |
| `OLLAMA_MODEL` | Ollama model tag | `llama3.2` | Optional |
| `TOP_K_RETRIEVAL` | Number of chunks retrieved per query | `5` | Optional |

---

## 🤖 LLM Provider Setup & Live Switching

The Lenny Growth Assistant features a **Provider Abstraction Layer** that decouples the agent logic from the underlying model provider. Evaluators can switch models **live in the UI** (via the header model button) or via config without restarting the server:

### 1. Offline Demonstration Mode (`simulated`) — *Recommended for Instant Evaluation*
- Works immediately with **zero API keys and zero background daemons**.
- Performs deterministic, grounded synthesis over indexed chunks.
- Generates full ~1,250-word Ship 30 essays and complete interactive HTML scorecards.

### 2. Local Model via Ollama (`ollama`)
1. Download and start [Ollama](https://ollama.ai).
2. Pull your desired model:
   ```bash
   ollama pull llama3.2
   ```
3. Set `LLM_PROVIDER=ollama` in `.env` or select `OLLAMA` in the UI modal.

### 3. Cloud Models (`anthropic` / `openai`)
Add your API key to `.env` and set `LLM_PROVIDER=anthropic` or `LLM_PROVIDER=openai`. If a cloud key is missing or invalid, the backend gracefully alerts the evaluator and falls back to safe simulation rather than crashing.

---

## 📚 Transcript Knowledge Base & Ingestion

The repository includes a reproducible ingestion pipeline that pulls raw transcripts from [ChatPRD/lennys-podcast-transcripts](https://github.com/ChatPRD/lennys-podcast-transcripts):

```bash
# 1. Fetch raw transcripts from GitHub into ingestion/data/raw/
python ingestion/fetch_transcripts.py

# 2. Parse YAML frontmatter, speaker turns, timestamps, and YouTube jump-links
python ingestion/chunk.py

# 3. Fit dense semantic vectorizer and load chunks idempotently into the database
python ingestion/embed_and_load.py
```

### Ingested Episodes
- **Brian Chesky** (Airbnb CEO): *Brian Chesky’s new playbook* (Founder mode, design-led management, eliminating committee bureaucracy).
- **Elena Verna** (Amplitude, Miro, Dropbox): *10 growth tactics that never work* (Why growth cannot fix retention, product-led growth vs paid acquisition).
- **Marty Cagan** (Silicon Valley Product Group): *Product Teams vs. Feature Teams* (Empowered problem discovery, missionaries vs mercenaries).
- **Shreyas Doshi** (Stripe, Twitter): *High-Agency Product Management* (First-principles reasoning, proactive risk mitigation).
- **Gustaf Alstromer** (Y Combinator partner): *The Superhuman PMF Engine* (The Sean Ellis benchmark, cohort retention asymptotes).

---

## 🛡️ Security: Sandboxed Artifact Viewer

When the assistant generates HTML/CSS components (such as the *Product-Market Fit Scorecard* or *Cohort Retention Visualizer*), they are treated as untrusted user-supplied code. The system enforces **defense-in-depth isolation**:

1. **Server-Side Sanitization**: `backend/app/core/sanitizer.py` strips `<script>` tags, inline event handlers (`onload=`, `onerror=`), and `javascript:` URIs.
2. **Client-Side Iframe Sandboxing**: Rendered inside an `<iframe sandbox="allow-same-origin" ...>` container without `allow-scripts`, completely preventing arbitrary script execution.
3. **Content Security Policy**: Raw artifact endpoint (`GET /artifacts/{id}/raw`) enforces `default-src 'self' 'unsafe-inline'; script-src 'none'; object-src 'none';`.

---

## 🧪 Automated Testing

Run the full automated test suite using `pytest`:

```bash
pytest tests/ -v
```

### Test Coverage (16 Tests Passing):
- `tests/test_api.py`: Liveness `/health`, readiness `/readiness`, config inspection, session CRUD, and input validation (422 response on empty input).
- `tests/test_retrieval.py`: Cosine similarity accuracy, citation attribution, timestamp presence, and low-confidence fallback on out-of-domain queries.
- `tests/test_ship30.py`: Structural rubric check (target word count ~1,250 words, hook, subheadings, bullet points, selective bolding, 1-sentence takeaway).
- `tests/test_sanitization.py`: XSS prevention, script tag stripping, inline event handler neutralization, and CSP headers.

---

## 🛠️ Resilience & Troubleshooting Matrix

| Issue / Failure Mode | Root Cause | System Behavior & Mitigation |
|---|---|---|
| **Ollama Unreachable** | Ollama daemon is not running on port 11434. | The UI displays an actionable error: *"Ollama server is not responding. Ensure Ollama is running or switch to simulated provider."* |
| **Missing / Expired API Key** | `ANTHROPIC_API_KEY` is empty. | Backend catches missing key before call; `/readiness` flags status as missing, preventing unhandled 500 exceptions. |
| **Out-of-Domain Query** | Query mentions topics not in transcripts (e.g. quantum mechanics). | Retrieval confidence falls below threshold (`is_insufficient_context=True`); assistant explicitly refuses to hallucinate and suggests podcast topics. |
| **No PostgreSQL Service** | Docker/Postgres not running locally. | Persistence layer automatically falls back to native SQLite (`lenny_assistant.db`), requiring zero setup. |
| **Malicious HTML in Artifact** | Prompt attempts to inject `<script>alert(1)</script>`. | Sanitizer neutralizes the tag server-side, and client iframe sandbox blocks script execution. |

---

## 📁 Repository Structure

```
├── .env.example                     # Sample configuration template
├── .gitignore                       # Clean repository hygiene
├── run.ps1                          # 1-command startup script (PowerShell)
├── run.sh                           # 1-command startup script (Bash)
├── start_backend.ps1                # Individual backend launcher
├── start_frontend.ps1               # Individual frontend launcher
├── README.md                        # Master project documentation
├── PRD.md                           # Product Requirements Document & Discovery Brief
├── design.md                        # UI/UX design tokens & split-view rationale
├── architecture.md                  # C4 diagrams, ERD, API contracts, security
├── demo_script.md                   # Video presentation script & walkthrough
├── data/
│   ├── lenny_assistant.db           # Pre-seeded SQLite database
│   └── tfidf_index.joblib           # Pre-computed dense vector index
├── ingestion/
│   ├── fetch_transcripts.py         # GitHub API transcript loader
│   ├── chunk.py                     # Speaker-aware chunker with timestamps
│   ├── embed_and_load.py            # Dense embedding & database populator
│   └── data/raw/                    # Raw podcast markdown files
├── backend/
│   ├── main.py                      # FastAPI application entrypoint
│   ├── requirements.txt             # Backend dependencies
│   └── app/
│       ├── api/router.py            # REST endpoints (/health, /chat, /artifacts)
│       ├── agent/
│       │   ├── core.py              # Orchestrator & intent router
│       │   └── skills/
│       │       ├── answer_transcripts.py # Grounded Q&A with citations
│       │       ├── ship30.py        # Ship 30 essay skill (~1,250 words)
│       │       └── artifact_gen.py  # HTML/CSS and Markdown artifact generator
│       ├── llm/                     # Provider abstraction (Claude, OpenAI, Ollama, Simulated)
│       ├── retrieval/engine.py      # Hybrid vector search with YouTube links
│       ├── db/                      # SQLAlchemy models & dual-persistence manager
│       └── core/                    # Config, structured logging, sanitizer
├── frontend/
│   ├── index.html                   # HTML template with Google Fonts
│   ├── package.json                 # React + Vite dependencies
│   ├── vite.config.js               # Vite config with API proxy
│   └── src/
│       ├── main.jsx                 # React root
│       ├── App.jsx                  # Main application container
│       ├── index.css                # Custom Vanilla CSS design system
│       └── components/              # Sidebar, ChatPane, ArtifactViewer, CitationsDrawer, Header
├── tests/
│   ├── test_api.py                  # API contract & validation tests
│   ├── test_retrieval.py            # RAG accuracy & attribution tests
│   ├── test_ship30.py               # Ship 30 structural rubric tests
│   ├── test_sanitization.py         # XSS security & CSP tests
│   └── manual_test_plan.md          # Evaluator step-by-step checklist
└── agent-transcripts/               # Engineering logs & phase transcripts
```

---

## Youtube Video Demo:
Docs : https://youtu.be/NiWNBiHzX_o

