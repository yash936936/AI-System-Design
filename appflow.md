# App Flow — SysDesign AI (v2)

## Layout Model — Claude.ai Identical

Every screen shares the same three-panel shell. No navigation between pages — the state changes within panels.

```
┌──────────────┬──────────────────────────────┬──────────────────────────┐
│  SIDEBAR     │  CHAT PANEL                  │  ARTIFACT PANEL          │
│  (260px)     │  (flex-grow)                 │  (420px)                 │
│              │                              │                          │
│  New chat    │  Message bubbles             │  Diagram / Capacity /    │
│  ──────────  │  MCQ chips                   │  Data Model / API /      │
│  History     │  AI responses                │  Stack tabs              │
│  list        │  ──────────────              │                          │
│              │  [ prompt input bar ]        │  Rendered output         │
└──────────────┴──────────────────────────────┴──────────────────────────┘
```

---

## Screen 1 — Empty State (New Chat)

**Sidebar:** "New Chat" button at top. Empty history list below. User avatar + settings at bottom.

**Chat panel:** Centred welcome message: *"Describe the system you want to design."* Four example prompt chips below it:
- "Design Twitter's timeline feed"
- "Design the auth service for my SaaS"
- "How would you design WhatsApp's messaging layer?"
- "LLD for a rate limiter"

No artifact panel visible yet — right panel is collapsed or shows a placeholder.

**Prompt input bar:** Identical to Claude.ai — full-width bar at bottom of chat panel, auto-expanding textarea, send button, model label ("Gemini Flash").

---

## Screen 2 — LLD / HLD Detection

**Trigger:** User submits a prompt.

**Chat panel:** AI immediately replies (< 2s) with a classification message:

> "This looks like a **High-Level Design** question. I'll walk you through the full HLD process — architecture, capacity, data model, API, and trade-offs."

Or for LLD:

> "This is a **Low-Level Design** question — I'll focus on the component internals, data structures, concurrency model, and API contracts."

Below the message, a small correction chip:
- `[ Switch to HLD ]` or `[ Switch to LLD ]`

User can confirm or correct. The context object is initialised with the design type.

**Artifact panel:** Still empty or shows a subtle "Building your design context…" skeleton.

---

## Screen 3 — MCQ Clarification (9 Categories)

**Trigger:** Design type confirmed.

**Chat panel:** AI sends clarification questions one category at a time, rendered as interactive chips inside the chat bubble. Each category is a separate message turn.

**Category order and MCQ format example:**

**Turn 1 — Functional Requirements**
> "What are the core features you need? Select all that apply:"
> `[ Post content ]` `[ Follow users ]` `[ Timeline feed ]` `[ Notifications ]` `[ Search ]` `[ DMs ]`
> `+ Add your own: [ text field ]`

**Turn 2 — Non-Functional Requirements**
> "What's the scale? Pick the closest:"
> `[ < 10K users ]` `[ 10K–1M users ]` `[ 1M–100M users ]` `[ 100M+ users ]`
>
> "Read/write ratio?"
> `[ Read-heavy (10:1+) ]` `[ Balanced ]` `[ Write-heavy ]`
>
> "Availability requirement?"
> `[ 99.9% (8.7hr downtime/yr) ]` `[ 99.99% (52min/yr) ]` `[ 99.999% (5min/yr) ]`

**Turn 3 — Capacity**
> "Daily active users?"
> `[ < 1K ]` `[ 1K–100K ]` `[ 100K–10M ]` `[ 10M+ ]`
> "Average request size?"
> `[ < 1KB ]` `[ 1KB–100KB ]` `[ 100KB–10MB ]` `[ > 10MB (media) ]`

**Turns 4–9** cover: Data Model preferences, API style, Architecture approach, Bottleneck focus, Scalability priority, Trade-off priorities.

Each turn waits for the user to tap chips or type before moving to the next. A progress indicator shows "Step 3 of 9" above the message.

**After all 9 turns:** A summary card is shown with all answers. A `[ Looks good — Generate ]` button and `[ Edit answers ]` button.

---

## Screen 4 — RAG Retrieval & Analysis (Streaming)

**Trigger:** User confirms answers.

**Chat panel:** AI streams a brief analysis message:

> "Analysing your requirements… Searching knowledge base for relevant patterns…"
> *(live dot animation)*
>
> "Found 4 relevant references: Redis Sorted Sets for timeline, Cassandra fan-out patterns, Twitter's original architecture (2013 vs 2022 evolution), and a rate-limiting deep dive."

If RAG confidence is low:
> "Searching the web for additional context on [topic]…"

**Artifact panel:** A "Sources" tab appears showing the retrieved chunks with titles and relevance scores. User can expand any source to read the excerpt.

---

## Screen 5 — Architecture Diagram (Primary Output)

**Trigger:** RAG complete. Generation starts.

**Artifact panel — Diagram tab (active):**
- Interactive Mermaid/React Flow diagram rendering the full system architecture
- Component nodes: colour-coded by type (frontend=blue, backend=green, DB=orange, queue=purple, CDN=grey)
- Edges labelled with protocol (HTTP, gRPC, async/queue)
- Click any node → tooltip shows: name, type, responsibilities, scaling notes
- Pan + zoom. Minimap bottom-right.

**Chat panel:** AI streams a narrative explanation of the architecture alongside the diagram rendering:
> "Here's the high-level architecture. The system uses a fan-out-on-write approach for the timeline feed, which optimises read latency at the cost of write amplification…"

---

## Screen 6 — Capacity / Data Model / API / Stack Tabs

**Artifact panel tabs (rendered after architecture):**

**Capacity tab:** Back-of-envelope table — QPS (read/write), storage per day/year, bandwidth, cache hit rate estimate. All numbers derived from the MCQ answers.

**Data Model tab:** Entity-relationship summary. Schema tables with columns, types, and indexes. SQL vs NoSQL decision with rationale. Sharding key if applicable.

**API tab:** Key endpoints listed — method, path, request body shape, response shape, auth method, pagination strategy.

**Stack tab:** Layer cards (Frontend / Backend / Database / Cache / Queue / CDN / Auth / Monitoring). Each card: primary pick + 1–2 alternatives + one-sentence rationale tied to the specific NFRs the user selected.

**Chat panel:** Each tab completion is narrated inline — user can ask follow-up questions ("Why Cassandra over DynamoDB?") and the AI responds in context, referencing the RAG sources.

---

## Screen 7 — Famous Design Retrieval

**Trigger:** User asks "Show me how Netflix does CDN" or "Design WhatsApp" (matching a pre-loaded system).

**Chat panel:** AI responds:
> "I have Netflix's CDN architecture (Open Connect) pre-loaded. Here's the canonical design and how your requirements compare."

**Artifact panel:** Switches to the stored famous design diagram. A comparison section below shows: "Your design vs Netflix — key differences."

The famous design is pulled directly from the vector store — no LLM generation needed, so zero API cost for the retrieval itself.

---

## Screen 8 — Export & Share

**Trigger:** User clicks "Export" button (top-right of artifact panel).

**Options:**
- Export as **PDF** — full design: diagram image + capacity table + data model + API spec + stack
- Export as **Markdown** — all sections as `.md` file
- Export as **JSON** — raw structured data (component graph + all section payloads)
- **Copy shareable link** — generates a read-only URL for the session

Sidebar history: completed sessions show a `↗ share` icon. Clicking opens the same export modal.