# Manual Test Plan & Evaluator Verification Checklist

A step-by-step verification plan for evaluating **The Lenny Growth Assistant** without Docker.

---

## 1. Startup & Initialization

- [ ] **Step 1.1**: Run `.\run.ps1` (Windows PowerShell) or `./run.sh` (macOS/Linux).
- [ ] **Step 1.2**: Confirm backend starts at `http://localhost:8000` and displays:
  ```
  The Lenny Growth Assistant Backend is ready.
  ```
- [ ] **Step 1.3**: Confirm frontend opens at `http://localhost:5173`.
- [ ] **Step 1.4**: Check knowledge base counter in the bottom left of the sidebar shows **568 Chunks**.

---

## 2. Grounded Conversational Q&A

- [ ] **Step 2.1**: Click the suggestion card: *"What is Brian Chesky’s philosophy on founder mode vs delegation?"*
- [ ] **Step 2.2**: Confirm the assistant responds with a structured synthesis referencing Airbnb's operating rhythm.
- [ ] **Step 2.3**: Click the **"5 Verified Sources"** button beneath the message.
- [ ] **Step 2.4**: Confirm the Citations Drawer slides up from the bottom showing:
  - Guest: **Brian Chesky**
  - Episode: *Brian Chesky’s new playbook*
  - Timestamp (e.g. `00:00:00` or `00:05:56`)
  - Red **"▶ Watch"** button linking directly to YouTube with timestamp parameter (`&t=...`).

---

## 3. Ship 30 for 30 Essay Generation

- [ ] **Step 3.1**: Enter the prompt: *"Write a Ship 30 for 30 essay on why growth tactics cannot fix a leaky retention bucket"*.
- [ ] **Step 3.2**: Confirm the assistant produces a long-form (~1,250 words), skimmable essay containing:
  - Curiosity-inducing `# Headline`
  - Punchy narrative lead-in
  - Roman numeral subheadings (`### I.`, `### II.`, `### III.`, `### IV.`)
  - Skimmable bullet points with selective **bold** emphasis
  - Explicit section: `### The 1-Sentence Takeaway`
- [ ] **Step 3.3**: Confirm the essay is grounded in quotes/ideas from Elena Verna and Sean Ellis.

---

## 4. Sandboxed Artifact Generation & Split-Screen Viewer

- [ ] **Step 4.1**: Enter prompt: *"Create an interactive Product Strategy & PMF Scorecard in HTML"*.
- [ ] **Step 4.2**: Confirm the right split-pane opens automatically displaying the **Artifact Viewer**.
- [ ] **Step 4.3**: In the Artifact Viewer:
  - Toggle between **Preview** (interactive rendered card) and **Code** (source code syntax).
  - Click **Copy** (`📋`) and verify clipboard receives source code.
  - Click **Download** (`⬇`) and confirm an `.html` file is downloaded.
  - Click **Fullscreen** (`⤢`) to expand the viewer across the viewport, then exit.
- [ ] **Step 4.4**: Security verification: Inspect the DOM to confirm the artifact renders inside `<iframe sandbox="allow-same-origin">` with script execution blocked.

---

## 5. Dynamic LLM Provider Switching

- [ ] **Step 5.1**: Click the **Model Pill** in the top header (currently showing `Offline Demo Mode`).
- [ ] **Step 5.2**: Confirm the **Configure LLM Provider** modal appears, displaying:
  - `SIMULATED` (Available)
  - `ANTHROPIC` (Shows availability status based on `.env`)
  - `OPENAI` (Shows availability status based on `.env`)
  - `OLLAMA` (Shows availability status based on local daemon)
- [ ] **Step 5.3**: Select a different provider (e.g. `anthropic` or `ollama`) and verify the active badge updates instantly without restarting the server.

---

## 6. Session Persistence & Isolation

- [ ] **Step 6.1**: Click **"+ New Conversation"** in the sidebar.
- [ ] **Step 6.2**: Confirm chat clears and a new session ID is generated.
- [ ] **Step 6.3**: Ask a new question (e.g. *"What did Marty Cagan say about feature teams?"*).
- [ ] **Step 6.4**: Click back to the previous session in the sidebar and verify the prior conversation and artifact are fully preserved.
- [ ] **Step 6.5**: Click the `✕` delete icon next to a session in the sidebar and verify it is removed from the list and database.

---

## 7. Resilience & Failure Handling

- [ ] **Step 7.1**: Ask an out-of-domain question: *"Explain quantum mechanics Schrödinger wave equation"*.
- [ ] **Step 7.2**: Verify the assistant acknowledges that Lenny's Podcast transcripts do not cover this topic rather than fabricating hallucinations.
- [ ] **Step 7.3**: Submit an empty message or invalid payload via API and verify the system returns a friendly `422 Unprocessable Entity` rather than an unhandled server crash.
