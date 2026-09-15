# plan.md — The Lenny Growth Assistant

Build strategy for the Forward Deployed Engineer take-home. Deadline: **Sept 15, 2026 EOD** — treat this as a ~2-day sprint. This document is the map; `tasks.md` is the turn-by-turn checklist you hand to coding agents (Claude Code / Agent SDK sessions) one phase at a time.

---

## 1. Guiding strategy

- **Ship a thin vertical slice first, then widen.** Get one grounded question → one cited answer → one rendered artifact working end-to-end on day 1, using the smallest possible stack. Everything else (auth polish, extra providers, nicer UI) is added around a working spine.
- **Optimize for evaluator trust, not feature count.** The rubric rewards clarity of judgment, reproducibility, and honest documentation of trade-offs over breadth. A smaller system that runs first-try beats a bigger one that doesn't.
- **Local model is mandatory for the demo.** Build and test against Ollama from the start, not as an afterthought — don't build only against Claude/OpenAI and bolt Ollama on at the end. The abstraction layer (Task 3 below) exists specifically so this isn't painful.
- **Write the docs as you build, not after.** PRD, design.md, and architecture.md should be updated at the end of each phase while decisions are fresh — this also naturally produces the "assumptions" and "trade-offs" content the rubric wants.
- **Keep agent transcripts as you go.** Save raw coding-agent session logs into `/agent-transcripts` incrementally; don't try to reconstruct them at the end.

## 2. Architecture at a glance

```
┌─────────────┐      REST/JSON       ┌──────────────────┐
│  Frontend   │ ───────────────────▶ │  FastAPI backend  │
│ (chat + AV) │ ◀─────────────────── │                    │
└─────────────┘                      │  ┌──────────────┐  │
                                      │  │ Agent layer   │  │──▶ LLM provider
                                      │  │ (Claude Agent │  │    (Anthropic / OpenAI / Ollama)
                                      │  │  SDK, skills) │  │
                                      │  └──────┬───────┘  │
                                      │         │          │
                                      │  ┌──────▼───────┐  │
                                      │  │ Retrieval     │  │──▶ Vector store (pgvector
                                      │  │ (RAG)         │  │    or local Chroma)
                                      │  └──────────────┘  │
                                      │                    │
                                      │  ┌──────────────┐  │
                                      │  │ Persistence   │  │──▶ PostgreSQL (Supabase/Railway)
                                      │  └──────────────┘  │
                                      └──────────────────┘
```

**Frontend:** React (Vite) chat UI + Artifact Viewer pane, split-screen like Claude.ai.
**Backend:** FastAPI, one process, clear routers: `/chat`, `/sessions`, `/artifacts`, `/health`, `/config`.
**Agent layer:** Anthropic Claude Agent SDK, with two explicit skills/tools: `answer_from_transcripts` (RAG) and `ship30_essay` (content generation skill). Model calls go through a provider abstraction so Claude / OpenAI / Ollama are interchangeable via config.
**Retrieval:** Chunk transcripts → embed → store in pgvector (simplest: one Postgres doing double duty as both app DB and vector store — avoids standing up a second service). Fallback: local Chroma if pgvector setup is a blocker under time pressure — document the trade-off either way.
**Persistence:** Postgres tables for sessions, messages, artifacts.
**Deployment:** Docker Compose (postgres + backend + frontend + optional ollama container), `.env.example`, one-command `docker compose up`.

## 3. Scope decisions (make these explicit in the PRD)

**In scope:**
- RAG over the Lenny's Podcast transcript repo (subset is fine — document how many transcripts / what selection criteria, e.g. most recent N or a curated topical set, given time constraints).
- Session-based chat with persisted history.
- Ship 30 for 30 essay-generation skill.
- Markdown + HTML/CSS artifact generation with a sandboxed viewer (iframe + sandbox attribute + CSP, no script execution unless explicitly and narrowly allowed).
- Cloud provider (Anthropic) + local provider (Ollama) both wired through one config toggle.
- Docker Compose startup, structured logging, graceful degradation on missing keys/timeouts/empty retrieval.
- Basic automated tests: retrieval, one API contract test, session persistence, artifact sanitization.

**Explicitly out of scope (state why in PRD):**
- Full auth/user accounts (single implicit user or lightweight API-key/header identity is enough — say so).
- Ingesting the *entire* transcript corpus if it's large — pick a representative subset and document the ingestion story as if it scaled (make ingestion idempotent and re-runnable rather than a one-off script, so "how it would scale" is credible).
- Streaming token-by-token UI (nice-to-have, not core to grading — add only if time remains).
- Multi-user auth, rate limiting, billing.
- Fine-tuning or evaluation harnesses beyond basic tests.

## 4. Risk register (feed into PRD §Risks)

| Risk | Mitigation to implement |
|---|---|
| Hallucination / ungrounded answers | RAG with explicit "insufficient context" fallback path; citations required in prompt template |
| Local model quality (Ollama) is much weaker | Smaller, tightly scoped prompts for the local path; document expected quality gap honestly in README |
| Latency (agent + retrieval + generation) | Show a loading/streaming state in UI; keep retrieval top-k small; cache embeddings |
| Unsafe artifact rendering (XSS in generated HTML) | Sandboxed `<iframe sandbox="allow-same-origin">` with no `allow-scripts` by default, or DOMPurify if scripts are needed; strip `<script>`/event handlers server-side too (defense in depth) |
| Data leakage across sessions | Session-scoped context only; never mix retrieval/history across session IDs |
| DB/Ollama unavailable at runtime | Health checks + friendly degraded-mode responses, not crashes |
| Time overrun before deadline | Thin-slice-first strategy (§1); cut nice-to-haves, never cut docs/tests/security note |

## 5. Build phases (see tasks.md for the checklist form)

1. **Phase 0 — Scaffolding & repo hygiene** (30–60 min): repo structure, `.env.example`, Docker Compose skeleton, health endpoint.
2. **Phase 1 — Data ingestion** (transcripts → chunks → embeddings → pgvector), with a re-runnable ingestion script and provenance metadata (source file/episode/timestamp) kept per chunk.
3. **Phase 2 — Provider abstraction** for Claude / OpenAI / Ollama, config-driven, with a `/config` endpoint exposing the active provider.
4. **Phase 3 — Agent layer**: Claude Agent SDK setup, `answer_from_transcripts` tool wired to retrieval + citation formatting, session/context management.
5. **Phase 4 — Persistence**: Postgres schema for sessions/messages/artifacts, wired into chat flow.
6. **Phase 5 — Ship 30 for 30 skill**: dedicated skill definition (read the guide, encode the rules as an explicit rubric/prompt template + word-count/structure checks), callable from the agent.
7. **Phase 6 — Artifact generation + viewer**: backend endpoint that returns Markdown/HTML artifacts tied to a message; frontend split-pane viewer with sandboxing.
8. **Phase 7 — Frontend polish**: chat UI, session switcher, provider indicator, artifact viewer states (loading/error/empty).
9. **Phase 8 — Resilience & observability**: structured logging, error handling for all the failure modes in the risk table, health/readiness checks.
10. **Phase 9 — Tests**: automated tests per rubric + manual UI test plan.
11. **Phase 10 — Docs & deliverables**: README, PRD, design.md, architecture.md, agent transcripts folder, demo video, final run-through as a "fresh evaluator."

## 6. Definition of done (before submission)

- [ ] `docker compose up` from a clean clone works with only `.env.example` → `.env` copy.
- [ ] A fresh question against the transcripts returns a cited, grounded answer (or an honest "not enough context" response).
- [ ] Switching provider (Claude/OpenAI ↔ Ollama) via config works without code changes and is visible in the UI.
- [ ] Ship 30 for 30 skill produces a ~1,250-word structured essay grounded in transcript content.
- [ ] Artifact viewer renders a generated Markdown/HTML artifact safely, beside the chat.
- [ ] All 8 required deliverables exist in the repo (README, PRD, design.md, architecture.md, agent-transcripts/, tests + manual test plan, demo video link, and the repo itself is public with no secrets committed).
- [ ] Ran `git log`/`grep` sweep for secrets before final push.
