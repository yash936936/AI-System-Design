# User Stories — SysDesign AI (v2)

> Personas: **IN** (Interview Candidate) · **DE** (Developer/Founder) · **SA** (Solutions Architect) · **ED** (Educator)

---

## Epic 1 — LLD / HLD Classification

### US-001 · Auto-detect design type
**As an** IN, **I want** the AI to automatically detect whether my prompt is LLD or HLD, **so that** I don't have to know the terminology before getting started.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Classification happens within 2 seconds of prompt submission
- [ ] Result is shown as a clear message: "This is a High-Level Design" or "Low-Level Design"
- [ ] A correction chip ("Switch to HLD / LLD") is shown below the classification
- [ ] Classification accuracy > 95% on a test set of 50 sample prompts
- [ ] LLD triggers depth focus on: data structures, concurrency, component internals, API contracts
- [ ] HLD triggers depth focus on: system components, capacity, data flow, trade-offs

### US-002 · Override classification
**As a** DE, **I want** to correct the AI's classification if it gets it wrong, **so that** the wrong design type doesn't cascade through all subsequent questions.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Tapping the correction chip re-classifies and restarts the MCQ flow
- [ ] A confirmation message shows the new classification
- [ ] Previous partial answers are discarded when switching type

---

## Epic 2 — MCQ Clarification Flow

### US-003 · Functional requirements MCQ
**As an** IN, **I want** to select core features from a chip list rather than typing them out, **so that** I can express requirements quickly without essay writing.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Chips cover the most common features for the detected system domain
- [ ] Multi-select is supported — user can pick 1 to all chips
- [ ] A free-text "Add your own" field appears below every MCQ set
- [ ] At least one selection (chip or free text) required before proceeding

### US-004 · Non-functional requirements MCQ
**As a** DE, **I want** to specify scale, availability, and consistency requirements using simple multiple-choice options, **so that** the generated design is actually calibrated to my system's needs.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Scale options: < 10K / 10K–1M / 1M–100M / 100M+ users
- [ ] Read/write ratio options: Read-heavy / Balanced / Write-heavy
- [ ] Availability options: 99.9% / 99.99% / 99.999%
- [ ] Consistency options: Strong / Eventual / Both (per feature)
- [ ] All selections stored in the session context object

### US-005 · Capacity estimation MCQ
**As a** DE, **I want** to input DAU and average request sizes via MCQ, **so that** the generated capacity estimates use my actual numbers, not guesses.

**Priority:** Must
**Acceptance Criteria:**
- [ ] DAU options: < 1K / 1K–100K / 100K–10M / 10M+
- [ ] Request size options with media flag for > 100KB payloads
- [ ] Back-of-envelope calculation is shown derived from these inputs in the output

### US-006 · All 9 MCQ categories accessible
**As a** SA, **I want** to be asked about all 9 design dimensions (functional, NFR, capacity, data model, API, architecture, bottlenecks, scalability, trade-offs), **so that** the output covers a complete system design review.

**Priority:** Must
**Acceptance Criteria:**
- [ ] All 9 categories are presented in sequence for HLD
- [ ] For LLD, categories 1/3/4/5/7 are asked; category 6 is simplified
- [ ] Progress indicator shows "Step N of 9" above each question turn
- [ ] User can skip a category (answer marked as "not specified")
- [ ] Summary card shown after all 9 with all answers and edit option

### US-007 · Edit answers before generating
**As an** IN, **I want** to review and edit my MCQ answers before generation starts, **so that** I can fix a wrong selection without restarting the whole flow.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Summary card shows all 9 categories with the user's selections
- [ ] Each category row has an "Edit" link that re-opens just that category's chips
- [ ] Changes to one category do not reset other categories
- [ ] "Generate" button is only active after the summary card is shown

---

## Epic 3 — RAG & Knowledge Base

### US-008 · Retrieve from GitHub design repos
**As an** IN, **I want** the AI to pull from real system design repositories when generating my design, **so that** the output is grounded in community-validated patterns, not just LLM guesswork.

**Priority:** Must
**Acceptance Criteria:**
- [ ] At least 5 GitHub system design repos are ingested at launch
- [ ] Retrieval returns the top 3–5 most relevant chunks for the session context
- [ ] Retrieved sources are listed in the "Sources" artifact tab with title + relevance score
- [ ] If no chunk scores above 0.6 cosine similarity, a web search fallback is triggered

### US-009 · Retrieve famous designs by name
**As a** SA, **I want** to ask "Show me how Netflix does X" and get the pre-stored canonical design, **so that** I can use it as a reference point in a client conversation.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Pre-loaded systems at launch: Netflix, X (Twitter), WhatsApp, Meta (Facebook), Uber, YouTube, Airbnb
- [ ] Name-match triggers direct vector store retrieval — no LLM generation call
- [ ] Design is displayed in the artifact panel with source attribution
- [ ] A comparison section shows differences from the user's current session design

### US-010 · Web search fallback
**As a** DE, **I want** the AI to search the web when its knowledge base doesn't have relevant material, **so that** I always get a grounded answer even for niche systems.

**Priority:** Should
**Acceptance Criteria:**
- [ ] Fallback is triggered when top RAG chunk similarity < 0.6
- [ ] Web search is shown as a status message in the chat ("Searching the web…")
- [ ] Web search results are cited in the output with URLs
- [ ] Web search adds < 5s to total generation time

---

## Epic 4 — Generation Output

### US-011 · Architecture diagram in artifact panel
**As an** IN, **I want** to see an interactive architecture diagram in the artifact panel while the AI explains it in the chat, **so that** I can understand the system structure visually and verbally at the same time.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Diagram renders within 5s of generation start
- [ ] Components are colour-coded by type (frontend/backend/DB/queue/CDN)
- [ ] Clicking a node shows a tooltip with responsibilities
- [ ] Pan and zoom work on mouse/touch

### US-012 · Capacity estimation output
**As a** DE, **I want** to see a back-of-envelope capacity table derived from my MCQ answers, **so that** I have concrete numbers to use in infrastructure planning.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Shows: peak QPS (read + write), daily storage generated, 5-year storage projection, bandwidth, cache dataset size
- [ ] All numbers are derivations of the DAU and request size answers from MCQ
- [ ] Formulas are shown next to each number (e.g. "10M DAU × 100 writes/day = 1B writes/day = ~11.5K QPS")

### US-013 · Data model output
**As a** DE, **I want** to see the core entity schema and SQL/NoSQL recommendation, **so that** I can start building the data layer without starting from scratch.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Shows: core entities, relationships, key columns with types
- [ ] SQL vs NoSQL decision is stated with a one-sentence rationale
- [ ] Sharding key recommendation included if scale > 10M DAU
- [ ] Access patterns listed that justify the schema choices

### US-014 · Trade-off justification
**As an** IN, **I want** the AI to justify every major decision with a trade-off statement, **so that** I can defend the design in an interview without memorising answers.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Every tech choice (DB, cache strategy, sync vs async) includes "we chose X over Y because Z"
- [ ] CAP theorem position stated for the overall system
- [ ] At least one "what would change at 10x scale" statement per design

---

## Epic 5 — Claude.ai UI

### US-015 · Sidebar chat history
**As a** DE, **I want** to see my past design sessions in a sidebar, **so that** I can return to a previous design without losing my work.

**Priority:** Should
**Acceptance Criteria:**
- [ ] Sidebar lists sessions sorted by most recent
- [ ] Each entry shows: system name (or first 40 chars of prompt) + date
- [ ] Clicking an entry restores the full session — chat history + artifact state
- [ ] "New Chat" button starts a fresh session

### US-016 · Artifact panel tabs
**As a** SA, **I want** the different output sections (Diagram, Capacity, Data Model, API, Stack) in separate tabs in the artifact panel, **so that** I can navigate to any section without scrolling through a long document.

**Priority:** Must
**Acceptance Criteria:**
- [ ] Five tabs: Diagram / Capacity / Data Model / API / Stack
- [ ] Active tab is highlighted
- [ ] Each tab renders independently — clicking a tab does not re-trigger generation
- [ ] Tabs appear progressively as each section finishes generating