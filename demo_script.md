# 2–3 Minute Demo Video Script & Presentation Guide

**Submission Deliverable 8:** Video Walkthrough Presentation  
**Target Duration:** 2 minutes 30 seconds  
**Camera:** Enabled (Presenter in bottom corner)  
**Tone:** Authoritative, concise, forward-deployed engineering mindset  

---

## Visual & Verbal Walkthrough

### 0:00 – 0:30 | Introduction & Problem Framing
* **Screen:** Presenter camera full or picture-in-picture over the app home screen at `http://localhost:5173`.
* **Presenter Voiceover:**
  > *"Hi everyone. I'm presenting The Lenny Growth Assistant—an enterprise-grade AI system designed for product managers, growth leads, and founders who want authoritative insights strictly grounded in Lenny’s Podcast transcripts.*
  >
  > *Rather than relying on generic LLM platitudes that hallucinate, our users need verified claims with exact timestamps, instant formatting into Ship 30 for 30 essays, and rendered visual artifacts—running 100% natively without Docker friction.*
  >
  > *Let's see it in action."*

---

### 0:30 – 1:10 | Grounded Q&A & Timestamp Citations
* **Screen:** Click the suggestion card: *"What is Brian Chesky’s philosophy on founder mode vs delegation?"*
* **Screen Action:** The assistant returns a structured breakdown citing Brian Chesky on Airbnb's review rhythms.
* **Screen Action:** Click the **"5 Verified Sources"** button beneath the message. The Citations Drawer slides up from the bottom.
* **Presenter Voiceover:**
  > *"Notice how the assistant answers directly from the transcript corpus. Beneath the response, we can click to inspect our verified sources.*
  >
  > *Each citation displays the guest, episode title, exact timestamp—like 00:05:56—and a direct YouTube link with the timestamp parameter pre-filled, so an evaluator can verify the exact audio moment with one click.*
  >
  > *And if a user asks about an out-of-domain topic like quantum mechanics, our confidence thresholding immediately detects insufficient context and refuses to hallucinate."*

---

### 1:10 – 1:45 | Ship 30 for 30 Skill & Rubric Validation
* **Screen:** Type or click prompt: *"Write a Ship 30 for 30 essay on why growth tactics cannot fix a leaky retention bucket"*.
* **Screen Action:** Show the essay rendering with headline, narrative lead-in, 4 Roman numeral pillars, skimmable bullet points, and the 1-sentence takeaway.
* **Presenter Voiceover:**
  > *"Next is our dedicated Ship 30 for 30 skill. Instead of relying on an arbitrary prompt, we built a formal structural rubric directly into the agent layer.*
  >
  > *The assistant produces a full, ~1,250-word essay with a curiosity hook, four structured Roman numeral pillars, selective bold highlights, and a mandatory one-sentence takeaway—drawing on Elena Verna and Sean Ellis's frameworks.*
  >
  > *Our automated test suite continuously verifies that this output satisfies the ~1,250-word band and structural constraints."*

---

### 1:45 – 2:10 | Split-Screen Artifact Viewer & Security Isolation
* **Screen:** Type: *"Create an interactive Product Strategy & PMF Scorecard in HTML"*.
* **Screen Action:** The right split-pane opens smoothly. Show the **Product-Market Fit Scorecard** rendered in the sandboxed iframe.
* **Screen Action:** Toggle between **Preview** and **Code** view. Click the **Copy** button (shows checkmark feedback).
* **Presenter Voiceover:**
  > *"When teams need actionable deliverables, the assistant generates full Markdown or HTML/CSS artifacts, rendered in our split-screen Artifact Viewer.*
  >
  > *Because LLM-generated HTML is untrusted, we implemented defense-in-depth: server-side sanitization strips executable scripts, while the client renders inside an isolated iframe with script execution blocked.*
  >
  > *Users can toggle between live preview and raw code, copy to clipboard, or download the artifact as a standalone file."*

---

### 2:10 – 2:30 | Technical Trade-off: Non-Docker Native Dual Persistence
* **Screen:** Click the **Model Pill** in the top bar. Show the modal with `simulated`, `anthropic`, `openai`, and `ollama`.
* **Presenter Voiceover:**
  > *"Finally, let’s talk about a core forward-deployed trade-off: deployment friction.*
  >
  > *In client environments, requiring Docker or external PostgreSQL services often creates immediate setup barriers. We engineered this system with dual-engine persistence: it connects to PostgreSQL when configured, but automatically falls back to native SQLite and local vector embeddings.*
  >
  > *Together with our multi-model abstraction—supporting Claude, OpenAI, local Ollama, and an offline simulated engine—an evaluator can clone this repo, run a single PowerShell or Bash script, and have the entire product running in under 60 seconds.*
  >
  > *Thank you for your time!"*
