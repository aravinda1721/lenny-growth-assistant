# tasks.md — Execution checklist

Granular, agent-sized tasks. Feed each phase to a coding agent (Claude Code / Agent SDK) as its own session or prompt; save the transcript of each session into `agent-transcripts/phaseN-<slug>.md` (or `.log`) as you go — don't wait until the end. Check items off as they're verified, not just written.

Legend: `[ ]` todo · acceptance criteria in *italics* under each task tell the agent (and you) when it's actually done.

---

## Phase 0 — Repo scaffolding

- [ ] Create repo structure:
  ```
  /backend        # FastAPI app
  /frontend       # React (Vite) app
  /ingestion      # transcript loading/chunking/embedding scripts
  /agent-transcripts
  /docs           # PRD.md, design.md, architecture.md live at repo root instead if preferred
  docker-compose.yml
  .env.example
  README.md
  ```
  *Acceptance: `tree -L 2` shows the layout; nothing under `/backend` or `/frontend` is committed with secrets.*
- [ ] Write `.env.example` covering: `ANTHROPIC_API_KEY`, `OPENAI_API_KEY` (optional), `LLM_PROVIDER` (`anthropic|openai|ollama`), `OLLAMA_BASE_URL`, `OLLAMA_MODEL`, `DATABASE_URL`, `APP_ENV`. Mark which are required vs optional in comments.
  *Acceptance: copying to `.env` with only `DATABASE_URL` + `LLM_PROVIDER=ollama` set is enough to boot in local-only mode.*
- [ ] Add `docker-compose.yml` skeleton with services: `postgres`, `backend`, `frontend`, `ollama` (optional profile). Backend depends_on postgres with a healthcheck.
  *Acceptance: `docker compose up` brings up postgres and an empty FastAPI app that responds on `/health`.*
- [ ] FastAPI skeleton: `/health` (liveness), `/readiness` (checks DB connection + configured provider reachability), CORS config for the frontend origin.
  *Acceptance: `curl localhost:8000/health` → `200 {"status":"ok"}`.*

## Phase 1 — Transcript ingestion

- [ ] Write a script (`ingestion/fetch_transcripts.py`) that pulls a documented subset of transcripts from `github.com/ChatPRD/lennys-podcast-transcripts` (e.g., clone/sparse-checkout, or fetch via GitHub API for N most recent files — pick one and record why in architecture.md).
  *Acceptance: running it populates `ingestion/data/raw/` with source files, each traceable to an original filename/URL.*
- [ ] Write a chunker (`ingestion/chunk.py`): split by speaker turn or paragraph with overlap, attach metadata per chunk (`source_file`, `episode_title` if derivable, `chunk_index`, `char_range`).
  *Acceptance: chunks are inspectable as JSON/JSONL with metadata; no chunk loses its source reference.*
- [ ] Write an embedding + load script (`ingestion/embed_and_load.py`) that embeds chunks and writes them into Postgres (pgvector) with a `chunks` table: `id, source_file, chunk_text, embedding, metadata jsonb, created_at`.
  *Acceptance: script is idempotent (safe to re-run — upsert on a content hash, not blind insert); `SELECT count(*) FROM chunks;` matches expectation.*
- [ ] Add a retrieval function (`backend/app/retrieval.py`) doing top-k cosine similarity search, returning chunk text + source metadata.
  *Acceptance: a quick manual query ("What is PMF?") returns plausible chunks with correct source attribution.*

## Phase 2 — Provider abstraction

- [ ] Define a `LLMProvider` interface (`backend/app/llm/base.py`) with a single method like `complete(messages, **kwargs) -> str` (or streaming variant).
  *Acceptance: interface has no provider-specific imports.*
- [ ] Implement `AnthropicProvider`, `OpenAIProvider` (optional/simple), `OllamaProvider` against that interface.
  *Acceptance: each provider can be instantiated and called independently with a trivial prompt, verified in a small script or test.*
- [ ] Add config loading (`backend/app/config.py`) reading `LLM_PROVIDER` and selecting the right implementation at startup; expose a `GET /config` endpoint returning the active provider (no secrets).
  *Acceptance: switching `LLM_PROVIDER` in `.env` and restarting changes the `/config` response and actual completions, with zero code edits.*
- [ ] Implement fallback behavior: if the configured cloud provider errors (missing key, timeout), document (README) whether it hard-fails or falls back to Ollama — pick one, implement it, and log the fallback event.
  *Acceptance: killing/omitting the cloud API key produces the documented behavior, not an unhandled exception.*

## Phase 3 — Agent layer & grounded Q&A

- [ ] Set up the Anthropic Claude Agent SDK (or Pi Coding Agent) in `backend/app/agent/`, with the provider abstraction from Phase 2 plugged in underneath.
  *Acceptance: a minimal agent round-trip works against both Claude and Ollama.*
- [ ] Implement `answer_from_transcripts` tool/skill: takes the user question + session history, retrieves top-k chunks, constructs a grounded prompt requiring citations, and returns an answer with source references.
  *Acceptance: answer text includes identifiable source markers (e.g., episode/file name) and the agent explicitly says when retrieval confidence is low / no relevant chunks found, rather than fabricating.*
- [ ] Wire session context: each session keeps its own message history; follow-up questions resolve pronouns/context correctly.
  *Acceptance: a 3-turn conversation with a pronoun-based follow-up ("what did they say about that?") retrieves correctly within the same session and is isolated from a different session ID.*
- [ ] `POST /chat` endpoint: accepts `session_id` (or creates one), `message`; returns answer + citations + `session_id`. Validate inputs (pydantic models), structured error responses.
  *Acceptance: invalid payloads return 422 with a clear error body, not a 500.*

## Phase 4 — Persistence

- [ ] Define schema: `sessions(id, created_at, metadata jsonb)`, `messages(id, session_id fk, role, content, citations jsonb, created_at)`, `artifacts(id, session_id fk, message_id fk, type, content, created_at)`.
  *Acceptance: schema exists via a migration tool (alembic or plain SQL migration files) — not ad hoc table creation in app code.*
- [ ] Wire `/chat` to persist every user/assistant message and citations.
  *Acceptance: after a chat exchange, querying Postgres directly shows the session, both messages, and citation metadata.*
- [ ] `GET /sessions`, `GET /sessions/{id}` endpoints to list sessions and fetch history (for a "start new chat" / session switcher UI).
  *Acceptance: creating two sessions and chatting in each shows fully independent histories via these endpoints.*

## Phase 5 — Ship 30 for 30 skill

- [ ] Read the Ship 30 for 30 guide and Impeccable style reference; extract a concrete rubric (hook style, structure, formatting rules, takeaway requirement) into a skill definition file (`backend/app/agent/skills/ship30.py` or a markdown prompt template file it loads).
  *Acceptance: the rubric is written down as explicit rules/checklist, not just implied in a single long prompt string.*
- [ ] Implement the skill as an agent tool: takes a topic/grounded answer, produces a ~1,250-word essay with hook, headings/bullets/bold, and a specific takeaway, grounded in retrieved transcript content (reuses Phase 3 retrieval).
  *Acceptance: generated essay word count is within a reasonable band of 1,250 (e.g., 1,100–1,400), has at least one clear takeaway sentence, and cites/reflects transcript content rather than generic filler.*
- [ ] Add a lightweight structural check (word count, heading presence) that flags/logs when output doesn't meet the rubric, rather than silently returning malformed output.
  *Acceptance: feeding a topic with no transcript support returns a graceful "insufficient grounding" response instead of a hallucinated essay.*

## Phase 6 — Artifact generation & viewer

- [ ] `POST /artifacts` (or embed in `/chat` response): given a session/message, generate a Markdown or HTML/CSS artifact; persist it via the `artifacts` table.
  *Acceptance: requesting "turn this into a one-pager" produces a stored artifact retrievable by ID.*
- [ ] `GET /artifacts/{id}` returns the artifact content + type.
- [ ] Frontend Artifact Viewer component: split-pane (chat left, artifact right), renders Markdown directly; renders HTML inside a sandboxed `<iframe sandbox="allow-same-origin">` (no `allow-scripts` unless a documented, narrow exception is made) or via DOMPurify-sanitized injection.
  *Acceptance: an artifact containing `<script>alert(1)</script>` does not execute; this is demonstrated in the manual test plan.*
- [ ] Document the sanitization/isolation strategy explicitly (what's permitted, what's blocked, why) — this goes into architecture.md's security section.

## Phase 7 — Frontend

- [ ] Chat UI: message list, input box, loading/streaming state, session switcher ("New chat" + list of past sessions).
- [ ] Provider indicator: shows active LLM provider (from `/config`), updates if changed.
- [ ] Empty/error states: no transcripts found, provider unavailable, DB error — each has a distinct, honest UI message (not a generic spinner forever).
  *Acceptance: killing Ollama mid-demo shows a clear in-UI error, not a hang.*
- [ ] Responsive layout check (narrow viewport at minimum doesn't break the split-pane) and basic accessibility pass (labels, focus states, contrast).

## Phase 8 — Resilience & observability

- [ ] Structured logging (JSON logs or consistent key=value) across: request in/out, retrieval hit/miss + latency, LLM call + latency + provider, artifact render events, DB errors.
- [ ] Explicit handling for each failure mode in plan.md's risk table: missing API key, Ollama unreachable, model timeout, empty retrieval, DB connection failure — each returns a structured error, not a stack trace to the client.
  *Acceptance: manually trigger each failure (stop the DB container, unset a key, point Ollama URL at nothing) and confirm graceful behavior + a log line.*

## Phase 9 — Tests

- [ ] Automated: retrieval returns expected chunks for a known query (unit/integration test against a small fixture set).
- [ ] Automated: `/chat` API contract test (valid + invalid payloads).
- [ ] Automated: session persistence test (messages survive and are session-isolated).
- [ ] Automated: artifact sanitization test (malicious HTML input doesn't produce executable script in the served/rendered output).
- [ ] Manual test plan (markdown checklist) covering: new chat → grounded question → citation appears; follow-up question retains context; Ship 30 skill invocation; artifact generation + viewer render; provider switch; each resilience scenario from Phase 8.

## Phase 10 — Documentation & submission deliverables

- [ ] `README.md`: architecture overview, prerequisites, install, env vars, local (Ollama) + cloud model setup, run commands, test commands, troubleshooting section (mapped to Phase 8 failure modes).
- [ ] `PRD.md`: discovery brief (user/problem, success metric, assumptions, scope in/out, risks/trade-offs — pull from plan.md §3–4), user flows, acceptance criteria, implementation plan/timeline.
- [ ] `design.md`: UI/UX principles, information architecture, key interaction states (loading/empty/error), responsive behavior, accessibility notes, and rationale for the split-pane artifact viewer.
- [ ] `architecture.md`: DB schema (with a diagram or table listing), API endpoint list, component boundaries, ingestion/retrieval flow diagram, agent routing (how the SDK decides `answer_from_transcripts` vs `ship30_essay`), model toggle mechanism, security (artifact sandboxing), deployment topology (Docker Compose diagram).
- [ ] `agent-transcripts/`: copy in raw session logs from each phase (including at least one failed attempt and how it was corrected), with secrets scrubbed.
- [ ] Record the 2–3 minute demo video (camera on): problem framing, live product demo, local Ollama demo, one technical trade-off discussion. Upload to YouTube (unlisted/public), link it in README.
- [ ] Final dry run: clone the repo fresh into a clean directory, follow only the README, confirm `docker compose up` + a sample question works end-to-end.
- [ ] Secret sweep: `git grep -i -E "sk-|api[_-]?key|password" -- ':!*.md'` (or similar) before final push; confirm `.env` is gitignored and never committed.
- [ ] Submit repo link via the submission form before **15/09/26 EOD**.
